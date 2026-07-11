from pydantic import BaseModel, Field


class ImageFeatureDashboardItemDto(BaseModel):
    request_id: str
    operation: str | None = None
    detector_model: str | None = None
    source_filename: str
    source_image_path: str
    source_image_url: str
    file_size_bytes: int = 0
    updated_at: str

    annotated_image_path: str | None = None
    annotated_image_url: str | None = None
    crop_image_urls: list[str] = Field(default_factory=list)
    crop_image_paths: list[str] = Field(default_factory=list)

    image_kinds: list[str] = Field(default_factory=list)
    class_names: list[str] = Field(default_factory=list)
    crop_count: int = 0
    detection_count: int = 0
    memory_item_count: int = 0
    best_confidence: float | None = None
