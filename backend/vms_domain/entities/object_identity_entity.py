import uuid
from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column
from vms_domain.database.base import Base
from vms_utils.base.base_entity import BaseEntity

class ObjectIdentityEntity(BaseEntity, Base):
    __tablename__ = "object_identities"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    canonical_label: Mapped[str] = mapped_column(String(120), nullable=False)
    representative_memory_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    memory_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
