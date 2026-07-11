from pydantic import BaseModel, Field, model_validator

class VideoProcessingSettingsDto(BaseModel):
    detector_model: str = Field(default="yolo")
    processing_mode: str = Field(default="full_video")
    sample_every_seconds: float = Field(default=1.0, ge=0.1)
    max_frames: int = Field(default=0, ge=0)
    confidence_threshold: float = Field(default=0.25, ge=0.0, le=1.0)
    iou_threshold: float = Field(default=0.45, ge=0.0, le=1.0)
    max_detections_per_frame: int = Field(default=50, ge=1, le=500)
    tracker_iou_threshold: float = Field(default=0.30, ge=0.05, le=0.95)
    crop_padding_pixels: int = Field(default=8, ge=0, le=128)
    enable_memory_storage: bool = True
    enable_duplicate_pruning: bool = True
    create_annotated_video: bool = True
    output_video_fps: float = Field(default=0.0, ge=0.0)
    save_detector_annotated_image: bool = False

    @model_validator(mode="after")
    def preserve_original_timeline_by_default(self):
        if self.detector_model not in {"yolo", "skydet"}:
            self.detector_model = "yolo"
        # Full video mode is the production default because output must match the input timeline.
        if self.processing_mode not in {"full_video", "timeline_sampled", "fast_sampled"}:
            self.processing_mode = "full_video"
        if self.processing_mode == "full_video":
            self.max_frames = 0
            self.output_video_fps = 0.0
            self.sample_every_seconds = 1.0
        return self
