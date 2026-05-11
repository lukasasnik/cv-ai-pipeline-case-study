from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict
from models import ExecutionState, ArtifactType

class ArtifactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: ArtifactType
    file_hash: str

class ExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_id: str | None = None
    state: ExecutionState
    created_at: datetime
    artifacts: list[ArtifactResponse] = []

class CvResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    file_hash: str
    status: str
    result: str | None = None
    created_at: datetime
    updated_at: datetime
    executions: list[ExecutionResponse] = []

class CvListResponse(BaseModel):
    items: list[CvResponse]
    total: int
    skip: int
    limit: int
