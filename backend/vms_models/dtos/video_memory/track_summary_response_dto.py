from pydantic import BaseModel
class TrackSummaryResponseDto(BaseModel):
    track_id: str
    class_id: int | None
    class_name: str
    first_seen_frame: int
    last_seen_frame: int
    first_seen_seconds: float
    last_seen_seconds: float
    seen_frame_count: int
    average_confidence: float
    best_confidence: float
    last_box: dict[str, float]
