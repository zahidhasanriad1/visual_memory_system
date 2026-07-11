from sqlalchemy.ext.asyncio import AsyncSession
from vms_data_access.repositories.base_repository import BaseRepository
from vms_domain.entities.annotation_task_entity import AnnotationTaskEntity

class AnnotationTaskRepository(BaseRepository[AnnotationTaskEntity]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AnnotationTaskEntity)
