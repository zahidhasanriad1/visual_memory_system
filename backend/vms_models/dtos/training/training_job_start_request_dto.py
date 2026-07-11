from pydantic import BaseModel, Field
class TrainingJobStartRequestDto(BaseModel):
    detector_model: str = "yolo"
    dataset_version_id: str
    base_model_id: str | None = None
    epochs: int = Field(default=50, ge=1, le=1000)
    image_size: int = Field(default=640, ge=320, le=1536)
    batch_size: int = Field(default=8, ge=1, le=128)
