import uuid
from sqlalchemy import String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from vms_domain.database.base import Base
from vms_utils.base.base_entity import BaseEntity

class DatasetVersionEntity(BaseEntity, Base):
    __tablename__ = "dataset_versions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(80), nullable=False)
    export_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    class_names: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    image_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    annotation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quality_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
