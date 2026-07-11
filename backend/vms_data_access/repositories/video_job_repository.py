from sqlalchemy.ext.asyncio import AsyncSession
from vms_data_access.repositories.base_repository import BaseRepository
from vms_domain.entities.video_job_entity import VideoJobEntity

class VideoJobRepository(BaseRepository[VideoJobEntity]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, VideoJobEntity)
