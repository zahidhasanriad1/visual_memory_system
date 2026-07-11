from pydantic import BaseModel
class VideoJobStatusResponseDto(BaseModel):
    job_id: str
    status: str
    progress_percent: float
    message: str
    result_available: bool
    error: str | None = None
