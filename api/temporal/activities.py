"""
Temporal activity definitions for CV processing.
"""

import httpx
from pydantic import ValidationError
from temporalio import activity
from temporalio.exceptions import ApplicationError

from config import settings
from database import (
    async_session,
    ArtifactType,
    CvExecution,
    CvExecutionArtifact,
    CvRecord,
    ExecutionState,
)
from domain.software_engineering.analysis_outputs import AnalysisOutputs
from domain.software_engineering.improvements_recommendation.improvements_recommender import (
    SoftwareEngineerHeuristicImprovementsRecommender,
)
from domain.software_engineering.salary_estimation.salary_estimator import (
    SoftwareEngineerHeuristicSalaryEstimator,
)
from domain.software_engineering.seniority_scoring.seniority_scorer import (
    SoftwareEngineerHeuristicAnalyzer,
)
from domain.software_engineering.structure_extraction.models.models import CVExtraction
from temporal.extractors.pdf_extractor import PDFExtractor
from utils.ai_client import AIClient
from shared.file_server_client import FileServerClient, NotFoundError, FileServerError
from domain.software_engineering.structure_extraction.structured_extractractor import SoftwareEngineerStructuredExtractor
import structlog

logger = structlog.get_logger()

# Initialize AIClient and FileServerClient
ai_client = AIClient()
file_client = FileServerClient(settings.file_server_url)
extractor = SoftwareEngineerStructuredExtractor(ai_client)
seniority_analyzer = SoftwareEngineerHeuristicAnalyzer()
salary_estimator = SoftwareEngineerHeuristicSalaryEstimator()
improvements_recommender = SoftwareEngineerHeuristicImprovementsRecommender()


async def persist_artifact(artifact: CvExecutionArtifact) -> int:
    """Helper to persist a CvExecutionArtifact to the database."""
    async with async_session() as db:
        db.add(artifact)
        await db.commit()
        await db.refresh(artifact)
        return artifact.id


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
    try:
        pdf_bytes = await file_client.download(file_hash)
    except NotFoundError:
        raise ApplicationError(f"File {file_hash} not found on server", non_retryable=True)
    except FileServerError as e:
        logger.error("file_server_download_error", error=str(e), file_hash=file_hash)
        raise
            
    # 2. Extract text using PDFExtractor
    extractor = PDFExtractor()
    try:
        extracted_text = extractor.extract(pdf_bytes)
    except ValueError as e:
        raise ApplicationError(str(e), non_retryable=True)

    # 3. Upload extracted text to file server
    try:
        upload_data = await file_client.upload("extracted.txt", extracted_text.encode("utf-8"), "text/plain")
        text_file_hash = upload_data.id
    except FileServerError as e:
        logger.error("file_server_upload_error", error=str(e))
        raise

    # 4. Create Artifact in Database
    artifact = CvExecutionArtifact(
        cv_execution_id=execution_id,
        type=ArtifactType.EXTRACTED_INPUT,
        file_hash=text_file_hash
    )
    return await persist_artifact(artifact)


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
    try:
        raw_text = await file_client.download_text(file_hash)
    except NotFoundError:
        raise ApplicationError(f"File {file_hash} not found on server", non_retryable=True)
    except FileServerError as e:
        logger.error("file_server_download_error", error=str(e), file_hash=file_hash)
        raise # Transient error, will retry

    # 3. Call AIClient via the specialized extractor
    try:
        # The extractor builds the prompt with the JSON schema and handles validation
        extraction_result = await extractor.extract(raw_text)
        # Convert the Pydantic object to a dict for uploading
        structured_data = extraction_result.model_dump()
    except Exception as e:
        # Check if it's a transient error (like connection or timeout) or a permanent one
        # For now, let's assume OpenAI SDK errors are retryable unless we know otherwise.
        # But if it's an AuthenticationError or similar, it should be non-retryable.
        # For simplicity, we let it retry on most errors.
        logger.error("llm_call_failed", error=str(e))
        raise

    # 4. Upload structured result to file server
    try:
        upload_data = await file_client.upload_json("structured_cv.json", structured_data)
        result_file_hash = upload_data.id
    except FileServerError as e:
        logger.error("file_server_upload_error", error=str(e))
        raise

    # 5. Create Artifact in Database
    new_artifact = CvExecutionArtifact(
        cv_execution_id=execution_id,
        type=ArtifactType.LLM_STRUCTURED_RAW,
        file_hash=result_file_hash
    )
    artifact_id = await persist_artifact(new_artifact)
    logger.info("llm_extraction_completed", artifact_id=artifact_id)
    return artifact_id


@activity.defn
async def generate_analysis_outputs(
    cv_execution_id: int,
    structured_artifact_id: int,
) -> int:
    """
    Generates deterministic analysis outputs from structured CV extraction.

    Args:
        cv_execution_id: ID of the CvExecution.
        structured_artifact_id: ID of the LLM_STRUCTURED_RAW artifact.

    Returns:
        The ID of the created CvExecutionArtifact (ANALYSIS_OUTPUTS).
    """
    logger.info(
        "analysis_outputs_started",
        execution_id=cv_execution_id,
        artifact_id=structured_artifact_id,
    )

    async with async_session() as db:
        artifact = await db.get(CvExecutionArtifact, structured_artifact_id)
        if not artifact:
            raise ApplicationError(
                f"Artifact {structured_artifact_id} not found",
                non_retryable=True,
            )

        if artifact.cv_execution_id != cv_execution_id:
            raise ApplicationError(
                (
                    f"Artifact {structured_artifact_id} does not belong to "
                    f"execution {cv_execution_id}"
                ),
                non_retryable=True,
            )

        if artifact.type != ArtifactType.LLM_STRUCTURED_RAW:
            raise ApplicationError(
                (
                    f"Artifact {structured_artifact_id} has type "
                    f"{artifact.type.value}; expected "
                    f"{ArtifactType.LLM_STRUCTURED_RAW.value}"
                ),
                non_retryable=True,
            )

        file_hash = artifact.file_hash

    try:
        structured_json = await file_client.download_text(file_hash)
    except NotFoundError:
        raise ApplicationError(
            f"File {file_hash} not found on server",
            non_retryable=True,
        )
    except FileServerError as e:
        logger.error("file_server_download_error", error=str(e), file_hash=file_hash)
        raise

    try:
        extraction = CVExtraction.model_validate_json(structured_json)
        seniority_scoring = seniority_analyzer.createSeniorityScoring(extraction)
        salary_estimation = salary_estimator.createSalaryEstimation(
            extraction=extraction,
            seniority_scoring=seniority_scoring,
        )
        improvement_recommendation = (
            improvements_recommender.createSalaryImprovementRecommendation(
                extraction=extraction,
                seniority=seniority_scoring,
                salary_estimation=salary_estimation,
            )
        )
        analysis_outputs = AnalysisOutputs(
            seniority_scoring=seniority_scoring,
            salary_estimation=salary_estimation,
            improvement_recommendation=improvement_recommendation,
        )
        analysis_outputs_json = analysis_outputs.model_dump_json()
    except ValidationError as e:
        logger.error("analysis_outputs_validation_failed", error=str(e))
        raise ApplicationError(str(e), non_retryable=True)

    try:
        upload_data = await file_client.upload(
            "analysis_outputs.json",
            analysis_outputs_json.encode("utf-8"),
            "application/json",
        )
        result_file_hash = upload_data.id
    except FileServerError as e:
        logger.error("file_server_upload_error", error=str(e))
        raise

    new_artifact = CvExecutionArtifact(
        cv_execution_id=cv_execution_id,
        type=ArtifactType.ANALYSIS_OUTPUTS,
        file_hash=result_file_hash,
    )
    artifact_id = await persist_artifact(new_artifact)
    logger.info("analysis_outputs_completed", artifact_id=artifact_id)
    return artifact_id
