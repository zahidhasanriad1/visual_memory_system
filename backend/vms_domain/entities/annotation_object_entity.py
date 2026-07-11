import uuid
from sqlalchemy import String, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column
from vms_domain.database.base import Base
from vms_utils.base.base_entity import BaseEntity

class AnnotationObjectEntity(BaseEntity, Base):
    __tablename__ = "annotation_objects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    x_min: Mapped[float] = mapped_column(Float, nullable=False)
    y_min: Mapped[float] = mapped_column(Float, nullable=False)
    x_max: Mapped[float] = mapped_column(Float, nullable=False)
    y_max: Mapped[float] = mapped_column(Float, nullable=False)
    geometry_type: Mapped[str] = mapped_column(String(40), default="box", nullable=False)
    points: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(80), default="pending", nullable=False)
