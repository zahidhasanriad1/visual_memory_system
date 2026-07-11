import uuid
from sqlalchemy import String, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column
from vms_domain.database.base import Base
from vms_utils.base.base_entity import BaseEntity

class TrackedObjectEntity(BaseEntity, Base):
    __tablename__ = "tracked_objects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    track_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    frame_number: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    class_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    class_name: Mapped[str] = mapped_column(String(120), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    crop_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    x_min: Mapped[float] = mapped_column(Float, nullable=False)
    y_min: Mapped[float] = mapped_column(Float, nullable=False)
    x_max: Mapped[float] = mapped_column(Float, nullable=False)
    y_max: Mapped[float] = mapped_column(Float, nullable=False)
