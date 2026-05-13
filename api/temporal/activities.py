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
from utils.ai_client import AIClient
import structlog
import json

logger = structlog.get_logger()

# Initialize AIClient
ai_client = AIClient()


@activity.defn
async def set_execution_state(execution_id: int, state: str) -> None:
    """Updates the state of a CV execution."""
    logger.info("setting_execution_state", execution_id=execution_id, state=state)
    
    # Convert string to enum
    try:
        enum_state = ExecutionState(state)
    except ValueError:
        logger.error("invalid_execution_state", state=state)
        return
    
    async with async_session() as db:
        execution = await db.get(CvExecution, execution_id)
        if execution:
            execution.state = enum_state
            await db.commit()
        else:
            logger.warning("execution_not_found", execution_id=execution_id)


@activity.defn
async def extract_cv_text(execution_id: int) -> int:
    """
    Extracts raw text from the CV PDF and saves it as an artifact.

    Args:
        execution_id: ID of the CvExecution.

    Returns:
        The ID of the created CvExecutionArtifact.
    """
    logger.info("extraction_started", execution_id=execution_id)

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


@activity.defn
async def extract_structured_information(execution_id: int, artifact_id: int) -> int:
    """
    Calls an LLM to extract structured information from the CV text.

    Args:
        execution_id: ID of the CvExecution.
        artifact_id: ID of the EXTRACTED_INPUT artifact.

    Returns:
        The ID of the created CvExecutionArtifact (LLM_STRUCTURED_RAW).
    """
    logger.info("llm_extraction_started", execution_id=execution_id, artifact_id=artifact_id)

    # 1. Get the artifact from DB to find the file_hash
    async with async_session() as db:
        artifact = await db.get(CvExecutionArtifact, artifact_id)
        if not artifact:
            raise ApplicationError(f"Artifact {artifact_id} not found", non_retryable=True)
        file_hash = artifact.file_hash

    # 2. Download raw text from file server
    file_url = f"{settings.file_server_url}/files/{file_hash}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(file_url)
            response.raise_for_status()
            raw_text = response.text
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ApplicationError(f"File {file_hash} not found on server", non_retryable=True)
            raise # Transient error, will retry
        except httpx.RequestError:
            raise # Transient error, will retry

    # 3. Call AIClient
    try:
        # Prompt for extraction (just a test as requested)
        system_prompt = "You are a professional HR assistant. Extract structured information from the following CV text in JSON format."
        user_prompt = f"Please extract key details (name, experience, skills) from this CV:\n\n{raw_text}"
        
        structured_data = await ai_client.get_structured_response(user_prompt, system_prompt)
    except Exception as e:
        # Check if it's a transient error (like connection or timeout) or a permanent one
        # For now, let's assume OpenAI SDK errors are retryable unless we know otherwise.
        # But if it's an AuthenticationError or similar, it should be non-retryable.
        # For simplicity, we let it retry on most errors.
        logger.error("llm_call_failed", error=str(e))
        raise

    # 4. Upload structured result to file server
    async with httpx.AsyncClient() as client:
        result_json = json.dumps(structured_data, indent=2)
        files = {"file": ("structured_cv.json", result_json.encode("utf-8"), "application/json")}
        upload_response = await client.post(f"{settings.file_server_url}/files/upload", files=files)
        upload_response.raise_for_status()
        result_file_hash = upload_response.json()["id"]

    # 5. Create Artifact in Database
    async with async_session() as db:
        new_artifact = CvExecutionArtifact(
            cv_execution_id=execution_id,
            type=ArtifactType.LLM_STRUCTURED_RAW,
            file_hash=result_file_hash
        )
        db.add(new_artifact)
        await db.commit()
        await db.refresh(new_artifact)
        
        logger.info("llm_extraction_completed", artifact_id=new_artifact.id)
        return new_artifact.id
