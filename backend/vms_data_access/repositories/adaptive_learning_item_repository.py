from sqlalchemy.ext.asyncio import AsyncSession
from vms_data_access.repositories.base_repository import BaseRepository
from vms_domain.entities.adaptive_learning_item_entity import AdaptiveLearningItemEntity

class AdaptiveLearningItemRepository(BaseRepository[AdaptiveLearningItemEntity]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AdaptiveLearningItemEntity)
