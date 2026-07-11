from sqlalchemy.ext.asyncio import AsyncSession
from vms_data_access.repositories.base_repository import BaseRepository
from vms_domain.entities.video_frame_entity import VideoFrameEntity

class VideoFrameRepository(BaseRepository[VideoFrameEntity]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, VideoFrameEntity)
