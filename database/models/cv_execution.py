from datetime import datetime, timezone
from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from .execution_state import ExecutionState

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
