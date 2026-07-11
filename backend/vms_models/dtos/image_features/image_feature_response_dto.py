from pydantic import BaseModel, Field


class ImageFeatureResponseDto(BaseModel):
    """
    Response DTO for image feature endpoints.
    One DTO class per file, following the VMS-X architecture rule.
    """

    request_id: str
    image_id: str
    status: str
    message: str

    source_filename: str
    source_image_path: str
    source_image_url: str | None = None
    file_size_bytes: int | None = None
    content_type: str | None = None
    detector_model: str
    annotated_image_path: str | None = None
    annotated_image_url: str | None = None

    width: int
    height: int
    source_width: int | None = None
    source_height: int | None = None
    inference_scaled: bool = False
    processed_image_count: int = 1
    total_detection_count: int = 0
    total_crop_count: int = 0
    total_memory_item_count: int = 0
    total_match_count: int = 0
    total_output_count: int = 0

    model_loaded: bool = False
    detector_warning: str | None = None

    detections: list[dict] = Field(default_factory=list)
    crops: list[dict] = Field(default_factory=list)
    memory_items: list[dict] = Field(default_factory=list)
    matches: list[dict] = Field(default_factory=list)
