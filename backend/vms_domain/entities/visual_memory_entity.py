import uuid
from sqlalchemy import String, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column
from vms_domain.database.base import Base
from vms_utils.base.base_entity import BaseEntity

class VisualMemoryEntity(BaseEntity, Base):
    __tablename__ = "visual_memory_items"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    track_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    class_name: Mapped[str] = mapped_column(String(120), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    crop_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
