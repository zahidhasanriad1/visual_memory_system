from typing import Literal

from pydantic import BaseModel, Field


class AnnotationObjectCreateRequestDto(BaseModel):
    task_id: str
    label: str = Field(min_length=1, max_length=120)
    geometry_type: Literal["box", "polygon"] = "box"
    x_min: float = 0
    y_min: float = 0
    x_max: float = 0
    y_max: float = 0
    points: list[list[float]] = Field(default_factory=list)
