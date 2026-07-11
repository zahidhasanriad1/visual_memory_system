from sqlalchemy.ext.asyncio import AsyncSession
from vms_data_access.repositories.base_repository import BaseRepository
from vms_domain.entities.dataset_version_entity import DatasetVersionEntity

class DatasetVersionRepository(BaseRepository[DatasetVersionEntity]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, DatasetVersionEntity)
