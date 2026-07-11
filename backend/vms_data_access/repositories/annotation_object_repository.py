from sqlalchemy.ext.asyncio import AsyncSession
from vms_data_access.repositories.base_repository import BaseRepository
from vms_domain.entities.annotation_object_entity import AnnotationObjectEntity

class AnnotationObjectRepository(BaseRepository[AnnotationObjectEntity]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AnnotationObjectEntity)
