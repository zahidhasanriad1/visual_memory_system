from sqlalchemy.ext.asyncio import AsyncSession
from vms_data_access.repositories.base_repository import BaseRepository
from vms_domain.entities.object_identity_entity import ObjectIdentityEntity

class ObjectIdentityRepository(BaseRepository[ObjectIdentityEntity]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ObjectIdentityEntity)
