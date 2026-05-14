from datetime import datetime, timezone
from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

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
