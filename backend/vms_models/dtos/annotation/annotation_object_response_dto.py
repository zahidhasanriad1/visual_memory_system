from pydantic import BaseModel, Field
class AnnotationObjectResponseDto(BaseModel):
    id: str
    task_id: str
    label: str
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    geometry_type: str = "box"
    points: list[list[float]] = Field(default_factory=list)
    status: str
