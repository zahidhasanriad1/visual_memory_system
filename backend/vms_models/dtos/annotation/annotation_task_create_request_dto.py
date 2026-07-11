from pydantic import BaseModel
class AnnotationTaskCreateRequestDto(BaseModel):
    project_id: str
    source_type: str
    source_path: str
    frame_number: int | None = None
