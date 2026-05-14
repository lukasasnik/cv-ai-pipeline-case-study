"""
CV AI Pipeline — Main API application.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.logging_utils import setup_logging

# Initialize logging as early as possible
logger = setup_logging("cv-api")

from database import engine, Base
from routers import cv, health
logger.info("API service starting up")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="CV AI Pipeline API",
    description="REST API for the CV processing pipeline. Upload CVs, trigger processing, and retrieve results.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(cv.router)
