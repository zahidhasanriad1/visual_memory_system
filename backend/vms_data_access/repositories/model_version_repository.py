from sqlalchemy.ext.asyncio import AsyncSession
from vms_data_access.repositories.base_repository import BaseRepository
from vms_domain.entities.model_version_entity import ModelVersionEntity

class ModelVersionRepository(BaseRepository[ModelVersionEntity]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ModelVersionEntity)
