from pydantic import BaseModel
from vms_models.dtos.video_memory.video_frame_response_dto import VideoFrameResponseDto
from vms_models.dtos.video_memory.tracked_object_response_dto import TrackedObjectResponseDto
from vms_models.dtos.video_memory.track_summary_response_dto import TrackSummaryResponseDto

class VideoMemoryResultResponseDto(BaseModel):
    video_id: str
    source_video_path: str
    original_filename: str
    processing_mode: str
    fps: float
    total_video_frames: int
    duration_seconds: float
    processed_frame_count: int
    total_detection_count: int
    total_tracked_object_count: int
    total_stored_object_count: int
    collection_name: str
    video_report_path: str | None
    annotated_video_path: str | None
    frames: list[VideoFrameResponseDto]
    objects: list[TrackedObjectResponseDto]
    tracks: list[TrackSummaryResponseDto]
