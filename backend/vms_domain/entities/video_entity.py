import uuid
from sqlalchemy import String, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column
from vms_domain.database.base import Base
from vms_utils.base.base_entity import BaseEntity

class VideoEntity(BaseEntity, Base):
    __tablename__ = "videos"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    source_video_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    fps: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_video_frames: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    width: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    height: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
