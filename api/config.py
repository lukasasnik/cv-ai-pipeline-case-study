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
    
    # AI API
    ai_api_url: str = "http://host.docker.internal:1234/v1"
    ai_api_token: str = "YOUR_TOKEN"
    ai_model: str = "google/gemma-4-26b-a4b"

    model_config = {"env_prefix": ""}


settings = Settings()
