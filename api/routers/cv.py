from typing import Any

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import settings
from database import get_db
from models import CvExecution, CvExecutionArtifact, CvRecord, ExecutionState
from schemas import CvListResponse, CvResponse, ExecutionResponse
from temporalio.client import Client
from temporal.workflows import CvProcessingWorkflow
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/cvs", tags=["cvs"])


@router.get("", response_model=CvListResponse)
async def list_cvs(
    skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(CvRecord)
        .options(selectinload(CvRecord.executions).selectinload(CvExecution.artifacts))
        .order_by(desc(CvRecord.id))
        .offset(skip)
        .limit(limit)
    )
    cvs = result.scalars().all()
    count_result = await db.execute(select(func.count(CvRecord.id)))
    total = count_result.scalar_one()
    return {"items": cvs, "total": total, "skip": skip, "limit": limit}


@router.get("/{cv_id}", response_model=CvResponse)
async def get_cv(cv_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CvRecord)
        .options(selectinload(CvRecord.executions).selectinload(CvExecution.artifacts))
        .where(CvRecord.id == cv_id)
    )
    cv = result.scalars().first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    return cv


@router.post("/upload", response_model=CvResponse)
async def upload_cv(
    file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
):
    if file.content_type != "application/pdf" and not file.filename.lower().endswith(
        ".pdf"
    ):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    logger.info("cv_upload_start", filename=file.filename)

    async with httpx.AsyncClient() as client:
        content = await file.read()
        files = {"file": (file.filename, content, file.content_type)}
        try:
            response = await client.post(
                f"{settings.file_server_url}/files/upload", files=files
            )
            response.raise_for_status()
            file_data = response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"File server error: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail="File server returned error",
            )

    # Note: If the file hash already exists, the file-server will return it and not create a duplicate.
    # We should still create a CV record, or check if one exists. For now, creating a new DB record
    # pointing to the same file_hash might fail due to unique constraint on file_hash in DB.
    # Wait! Models has: file_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    # If the file exists, file_hash is the same. Thus, DB will throw an IntegrityError if a record with this hash exists.
    # Let's handle this.
    try:
        cv_record = CvRecord(
            filename=file.filename, file_hash=file_data["id"], status="uploaded"
        )
        db.add(cv_record)
        await db.commit()
        
        # Refetch to ensure relationships are loaded for Pydantic, avoiding identity map cache issues with db.get
        result = await db.execute(
            select(CvRecord)
            .options(selectinload(CvRecord.executions).selectinload(CvExecution.artifacts))
            .where(CvRecord.id == cv_record.id)
        )
        cv_record = result.scalar_one()
        return cv_record
    except Exception as e:
        await db.rollback()
        # Check if it already exists
        existing_cv = await db.execute(
            select(CvRecord)
            .options(selectinload(CvRecord.executions).selectinload(CvExecution.artifacts))
            .where(CvRecord.file_hash == file_data["id"])
        )
        existing = existing_cv.scalars().first()
        if existing:
            logger.info("cv_upload_duplicate", file_hash=file_data["id"])
            return existing
        logger.error("cv_upload_failed", error=str(e), filename=file.filename)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{cv_id}", status_code=204)
async def delete_cv(cv_id: int, db: AsyncSession = Depends(get_db)):
    cv = await db.get(CvRecord, cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"{settings.file_server_url}/files/{cv.file_hash}"
            )
            if response.status_code not in (200, 204, 404):
                response.raise_for_status()
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=502, detail=f"File server error during deletion: {exc}"
            )

    await db.delete(cv)
    await db.commit()
    logger.info("cv_deleted", cv_id=cv_id, file_hash=cv.file_hash)


@router.post("/{cv_id}/process", response_model=ExecutionResponse)
async def process_cv(cv_id: int, db: AsyncSession = Depends(get_db)):
    cv = await db.get(CvRecord, cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    execution = CvExecution(
        cv_id=cv_id,
        state=ExecutionState.NEW
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    try:
        client = await Client.connect(settings.temporal_host)
        
        handle = await client.start_workflow(
            CvProcessingWorkflow.run,
            execution.id,
            id=f"cv-processing-{execution.id}",
            task_queue=settings.temporal_task_queue,
        )
        
        execution.workflow_id = handle.id
        await db.commit()
        
        logger.info("cv_processing_started", cv_id=cv_id, execution_id=execution.id, workflow_id=handle.id)

        # Refetch to ensure relationships are loaded for Pydantic, avoiding identity map cache
        result = await db.execute(
            select(CvExecution)
            .options(selectinload(CvExecution.artifacts))
            .where(CvExecution.id == execution.id)
        )
        execution = result.scalar_one()
        
        return execution
    except Exception as e:
        execution.state = ExecutionState.ERROR
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {e}")


@router.get("/executions/{execution_id}", response_model=ExecutionResponse)
async def get_execution(execution_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CvExecution)
        .options(selectinload(CvExecution.artifacts))
        .where(CvExecution.id == execution_id)
    )
    execution = result.scalars().first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


@router.get("/artifacts/{artifact_id}/download")
async def download_artifact(artifact_id: int, db: AsyncSession = Depends(get_db)):
    artifact = await db.get(CvExecutionArtifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    logger.info("artifact_download_start", artifact_id=artifact_id, file_hash=artifact.file_hash)

    async def stream_file():
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "GET", f"{settings.file_server_url}/files/{artifact.file_hash}"
            ) as response:
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code, detail="File server error"
                    )
                async for chunk in response.aiter_bytes():
                    yield chunk

    # We don't have the original filename here easily without another call to file-server
    # but the file-server response might have it in headers.
    # For now, let's just proxy the stream.
    return StreamingResponse(
        stream_file(),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="artifact_{artifact.id}_{artifact.file_hash[:8]}"'
        },
    )
