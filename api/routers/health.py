"""
Health / hello-world router.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def hello():
    """Hello world and health check."""
    return {"status": "ok", "message": "CV AI Pipeline API"}
