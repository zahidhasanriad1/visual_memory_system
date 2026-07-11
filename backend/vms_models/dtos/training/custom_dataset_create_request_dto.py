from pydantic import BaseModel, Field


class CustomDatasetCreateRequestDto(BaseModel):
    project_id: str
    name: str = Field(min_length=2, max_length=255)
    version: str = Field(default="v1", min_length=1, max_length=80)
    train_split: float = Field(default=0.8, ge=0.5, le=0.95)
    include_pending: bool = False
