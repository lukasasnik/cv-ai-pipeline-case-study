"""
Temporal activity definitions for CV processing.
"""

import httpx
from temporalio import activity
from temporalio.exceptions import ApplicationError

from config import settings
from database import async_session
from models import ArtifactType, CvExecution, CvExecutionArtifact, CvRecord, ExecutionState
from temporal.extractors.pdf_extractor import PDFExtractor


@activity.defn
async def set_execution_state(execution_id: int, state: str) -> None:
    """Updates the state of a CV execution."""
    activity.logger.info(f"Setting execution {execution_id} state to {state}")
    
    # Convert string to enum
    try:
        enum_state = ExecutionState(state)
    except ValueError:
        activity.logger.error(f"Invalid execution state: {state}")
        return
    
    async with async_session() as db:
        execution = await db.get(CvExecution, execution_id)
        if execution:
            execution.state = enum_state
            await db.commit()
        else:
            activity.logger.warning(f"Execution {execution_id} not found.")


@activity.defn
async def extract_cv_text(execution_id: int) -> int:
    """
    Extracts raw text from the CV PDF and saves it as an artifact.

    Args:
        execution_id: ID of the CvExecution.

    Returns:
        The ID of the created CvExecutionArtifact.
    """
    activity.logger.info(f"Starting extraction for execution {execution_id}")

    async with async_session() as db:
        execution = await db.get(CvExecution, execution_id)
        if not execution:
            raise ApplicationError(f"Execution {execution_id} not found", non_retryable=True)
            
        cv_record = await db.get(CvRecord, execution.cv_id)
        if not cv_record:
            raise ApplicationError(f"CV Record {execution.cv_id} not found", non_retryable=True)
            
        file_hash = cv_record.file_hash

    # 1. Download PDF from file server
    file_url = f"{settings.file_server_url}/files/{file_hash}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(file_url)
            response.raise_for_status()
            pdf_bytes = response.content
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ApplicationError(f"File {file_hash} not found on server", non_retryable=True)
            raise
            
    # 2. Extract text using PDFExtractor
    extractor = PDFExtractor()
    try:
        extracted_text = extractor.extract(pdf_bytes)
    except ValueError as e:
        raise ApplicationError(str(e), non_retryable=True)

    # 3. Upload extracted text to file server
    async with httpx.AsyncClient() as client:
        files = {"file": ("extracted.txt", extracted_text.encode("utf-8"), "text/plain")}
        upload_response = await client.post(f"{settings.file_server_url}/files/upload", files=files)
        upload_response.raise_for_status()
        text_file_hash = upload_response.json()["id"]

    # 4. Create Artifact in Database
    async with async_session() as db:
        artifact = CvExecutionArtifact(
            cv_execution_id=execution_id,
            type=ArtifactType.EXTRACTED_INPUT,
            file_hash=text_file_hash
        )
        db.add(artifact)
        await db.commit()
        await db.refresh(artifact)
        
        return artifact.id
