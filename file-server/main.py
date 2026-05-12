"""
File Server — FastAPI microservice for file storage.

Files are deduplicated using SHA-256 content hashing.
Each file is stored as <sha256>.<ext> with a <sha256>.meta.json sidecar.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from shared.logging_utils import setup_logging

logger = setup_logging("file-server")
logger.info("File server starting up")

STORAGE_DIR = Path("/data/files")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 1024 * 1024  # 1 MB

app = FastAPI(
    title="CV Pipeline — File Server",
    description="Standalone file storage with SHA-256 content-hash deduplication.",
    version="0.1.0",
)


def _find_file_by_id(file_id: str) -> Path | None:
    """Find the stored file matching the given hash ID."""
    matches = list(STORAGE_DIR.glob(f"{file_id}.*"))
    # Filter out .meta.json sidecar files
    matches = [m for m in matches if not m.name.endswith(".meta.json")]
    return matches[0] if matches else None


def _meta_path(file_id: str) -> Path:
    return STORAGE_DIR / f"{file_id}.meta.json"


# ── Upload ────────────────────────────────────────────────────────────────────


@app.post("/files/upload")
async def upload_file(file: UploadFile):
    """
    Upload a file.

    The file content is hashed with SHA-256 to produce a unique ID.
    If a file with the same hash already exists, the upload is a no-op
    and the existing file metadata is returned (idempotent).
    """
    sha256 = hashlib.sha256()
    chunks: list[bytes] = []

    # Stream and hash incrementally
    while True:
        chunk = await file.read(CHUNK_SIZE)
        if not chunk:
            break
        sha256.update(chunk)
        chunks.append(chunk)

    file_hash = sha256.hexdigest()
    original_name = file.filename or "unknown"
    extension = Path(original_name).suffix.lower() or ".bin"

    # Check for existing file (idempotent)
    existing = _find_file_by_id(file_hash)
    if existing:
        logger.info("file_upload_duplicate", file_id=file_hash, filename=original_name)
        meta = json.loads(_meta_path(file_hash).read_text())
        return JSONResponse(
            content={
                "id": file_hash,
                "filename": meta.get("original_filename", original_name),
                "size": existing.stat().st_size,
                "created": False,
            }
        )

    # Store file
    stored_path = STORAGE_DIR / f"{file_hash}{extension}"
    with open(stored_path, "wb") as f:
        for chunk in chunks:
            f.write(chunk)

    file_size = stored_path.stat().st_size

    # Store metadata sidecar
    meta = {
        "original_filename": original_name,
        "extension": extension,
        "size": file_size,
        "content_type": file.content_type,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    _meta_path(file_hash).write_text(json.dumps(meta, indent=2))

    logger.info("file_uploaded", file_id=file_hash, filename=original_name, size=file_size)

    return JSONResponse(
        status_code=201,
        content={
            "id": file_hash,
            "filename": original_name,
            "size": file_size,
            "created": True,
        },
    )


# ── Get / Serve ───────────────────────────────────────────────────────────────


@app.get("/files/{file_id}")
async def get_file(file_id: str):
    """Serve a stored file by its hash ID."""
    stored_path = _find_file_by_id(file_id)
    if not stored_path:
        raise HTTPException(status_code=404, detail="File not found")

    # Read original filename from metadata for Content-Disposition
    meta_file = _meta_path(file_id)
    original_name = file_id
    if meta_file.exists():
        meta = json.loads(meta_file.read_text())
        original_name = meta.get("original_filename", file_id)

    logger.info("file_served", file_id=file_id, filename=original_name)

    return FileResponse(
        path=stored_path,
        filename=original_name,
        media_type="application/octet-stream",
    )


# ── Delete ────────────────────────────────────────────────────────────────────


@app.delete("/files/{file_id}", status_code=204)
async def delete_file(file_id: str):
    """Delete a stored file and its metadata by hash ID."""
    stored_path = _find_file_by_id(file_id)
    if not stored_path:
        raise HTTPException(status_code=404, detail="File not found")

    stored_path.unlink()

    meta_file = _meta_path(file_id)
    if meta_file.exists():
        meta_file.unlink()

    logger.info("file_deleted", file_id=file_id)

    return None


# ── Health ────────────────────────────────────────────────────────────────────


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "file-server"}
