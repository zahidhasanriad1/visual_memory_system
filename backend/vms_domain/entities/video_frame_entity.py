import uuid
from sqlalchemy import String, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column
from vms_domain.database.base import Base
from vms_utils.base.base_entity import BaseEntity

class VideoFrameEntity(BaseEntity, Base):
    __tablename__ = "video_frames"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    frame_number: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    frame_image_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    tracked_annotated_image_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
