import uuid
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from vms_domain.database.base import Base
from vms_utils.base.base_entity import BaseEntity

class AnnotationProjectEntity(BaseEntity, Base):
    __tablename__ = "annotation_projects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(80), default="active", nullable=False)
