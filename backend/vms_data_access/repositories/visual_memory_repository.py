from sqlalchemy.ext.asyncio import AsyncSession
from vms_data_access.repositories.base_repository import BaseRepository
from vms_domain.entities.visual_memory_entity import VisualMemoryEntity

class VisualMemoryRepository(BaseRepository[VisualMemoryEntity]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, VisualMemoryEntity)
