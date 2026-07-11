import uuid
from sqlalchemy import String, Float, Text
from sqlalchemy.orm import Mapped, mapped_column
from vms_domain.database.base import Base
from vms_utils.base.base_entity import BaseEntity

class VideoJobEntity(BaseEntity, Base):
    __tablename__ = "video_jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default="queued", nullable=False)
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    message: Mapped[str] = mapped_column(String(1000), default="Queued.", nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_report_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
