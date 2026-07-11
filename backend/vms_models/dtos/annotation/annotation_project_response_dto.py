from pydantic import BaseModel
class AnnotationProjectResponseDto(BaseModel):
    id: str
    name: str
    description: str | None
    status: str
