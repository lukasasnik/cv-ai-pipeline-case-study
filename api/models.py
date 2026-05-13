"""
SQLAlchemy ORM models.
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ExecutionState(enum.Enum):
    SUCCESS = "success"
    ERROR = "error"
    PROGRESS = "progress"
    NEW = "new"


class ArtifactType(enum.Enum):
    EXTRACTED_INPUT = "extracted_input"
    LLM_STRUCTURED_RAW = "llm_structured_raw"


class CvRecord(Base):
    """Tracks a CV that has been uploaded and processed through the pipeline."""

    __tablename__ = "cv_record"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )
    filename: Mapped[str] = mapped_column(String(512))
    file_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(
        String(50), default="uploaded"
    )  # uploaded | processing | completed | failed
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    executions: Mapped[list["CvExecution"]] = relationship(
        "CvExecution", back_populates="cv_record", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CvRecord {self.id} status={self.status}>"


class CvExecution(Base):
    """Captures the executions/processing of a CV."""

    __tablename__ = "cv_execution"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cv_id: Mapped[int] = mapped_column(ForeignKey("cv_record.id"), index=True)
    workflow_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state: Mapped[ExecutionState] = mapped_column(
        Enum(ExecutionState, name="execution_state"), default=ExecutionState.NEW
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    cv_record: Mapped["CvRecord"] = relationship("CvRecord", back_populates="executions")
    artifacts: Mapped[list["CvExecutionArtifact"]] = relationship(
        "CvExecutionArtifact", back_populates="execution", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CvExecution {self.id} cv_id={self.cv_id} state={self.state}>"


class CvExecutionArtifact(Base):
    """Stores records of artifacts generated during execution."""

    __tablename__ = "cv_execution_artifact"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cv_execution_id: Mapped[int] = mapped_column(
        ForeignKey("cv_execution.id"), index=True
    )
    type: Mapped[ArtifactType] = mapped_column(Enum(ArtifactType, name="artifact_type"))
    file_hash: Mapped[str] = mapped_column(String(64))

    execution: Mapped["CvExecution"] = relationship("CvExecution", back_populates="artifacts")

    def __repr__(self) -> str:
        return f"<CvExecutionArtifact {self.id} type={self.type}>"
