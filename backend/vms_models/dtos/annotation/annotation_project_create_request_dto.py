from pydantic import BaseModel, Field
class AnnotationProjectCreateRequestDto(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None
