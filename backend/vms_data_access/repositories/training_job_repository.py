from sqlalchemy.ext.asyncio import AsyncSession
from vms_data_access.repositories.base_repository import BaseRepository
from vms_domain.entities.training_job_entity import TrainingJobEntity

class TrainingJobRepository(BaseRepository[TrainingJobEntity]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, TrainingJobEntity)
