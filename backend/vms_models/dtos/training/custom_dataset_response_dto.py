from pydantic import BaseModel, Field


class CustomDatasetResponseDto(BaseModel):
    id: str
    name: str
    version: str
    class_names: list[str] = Field(default_factory=list)
    image_count: int
    annotation_count: int
    quality_score: int
    ready_for_training: bool
