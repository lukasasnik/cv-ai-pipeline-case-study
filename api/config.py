"""
Application configuration loaded from environment variables.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with sensible defaults for Docker Compose."""

    # Database
    database_url: str = (
        "postgresql+asyncpg://cvpipeline:cvpipeline@database:5432/cvpipeline"
    )

    # File Server
    file_server_url: str = "http://file-server:8000"

    # Temporal
    temporal_host: str = "temporal:7233"
    temporal_task_queue: str = "cv-pipeline-queue"

    model_config = {"env_prefix": "APP_"}


settings = Settings()
