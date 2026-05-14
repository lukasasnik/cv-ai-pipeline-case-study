from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from .artifact_type import ArtifactType

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
