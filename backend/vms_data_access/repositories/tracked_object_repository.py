from sqlalchemy.ext.asyncio import AsyncSession
from vms_data_access.repositories.base_repository import BaseRepository
from vms_domain.entities.tracked_object_entity import TrackedObjectEntity

class TrackedObjectRepository(BaseRepository[TrackedObjectEntity]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, TrackedObjectEntity)
