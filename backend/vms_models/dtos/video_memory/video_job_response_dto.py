from pydantic import BaseModel
class VideoJobResponseDto(BaseModel):
    job_id: str
    status: str
    message: str
    source_video_path: str | None = None
