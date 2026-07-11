from sqlalchemy.ext.asyncio import AsyncSession
from vms_data_access.repositories.base_repository import BaseRepository
from vms_domain.entities.video_entity import VideoEntity

class VideoRepository(BaseRepository[VideoEntity]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, VideoEntity)
