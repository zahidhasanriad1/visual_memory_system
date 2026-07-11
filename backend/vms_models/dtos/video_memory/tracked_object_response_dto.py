from pydantic import BaseModel
class TrackedObjectResponseDto(BaseModel):
    track_id: str
    detection_id: str
    memory_id: str | None
    memory_action: str
    frame_number: int
    frame_timestamp_seconds: float
    class_id: int | None
    class_name: str
    confidence: float
    crop_path: str | None
    x_min: float
    y_min: float
    x_max: float
    y_max: float
