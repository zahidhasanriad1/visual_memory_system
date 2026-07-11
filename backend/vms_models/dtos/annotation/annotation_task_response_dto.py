from pydantic import BaseModel
class AnnotationTaskResponseDto(BaseModel):
    id: str
    project_id: str
    source_type: str
    source_path: str | None = None
    source_url: str | None = None
    status: str
    frame_number: int | None = None
