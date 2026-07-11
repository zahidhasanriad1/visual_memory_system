import uuid
from sqlalchemy import String, Float, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from vms_domain.database.base import Base
from vms_utils.base.base_entity import BaseEntity

class AdaptiveLearningItemEntity(BaseEntity, Base):
    __tablename__ = "adaptive_learning_items"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_video_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    stored_image_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    yolo_class_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    yolo_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    vlm_object_name: Mapped[str] = mapped_column(String(120), default="unknown_object", nullable=False)
    vlm_confidence_level: Mapped[str] = mapped_column(String(50), default="low", nullable=False)
    vlm_confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    final_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    admin_review_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    admin_corrected_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
