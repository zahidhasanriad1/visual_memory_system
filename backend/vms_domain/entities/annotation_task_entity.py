import uuid
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from vms_domain.database.base import Base
from vms_utils.base.base_entity import BaseEntity

class AnnotationTaskEntity(BaseEntity, Base):
    __tablename__ = "annotation_tasks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(String(80), default="pending", nullable=False)
    frame_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
