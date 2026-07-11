from pydantic import BaseModel
class VideoFrameResponseDto(BaseModel):
    frame_number: int
    frame_timestamp_seconds: float
    frame_image_path: str
    tracked_annotated_image_path: str | None
    detection_count: int
    tracked_object_count: int
    stored_object_count: int
