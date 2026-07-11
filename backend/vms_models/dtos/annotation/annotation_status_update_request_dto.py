from typing import Literal

from pydantic import BaseModel


class AnnotationStatusUpdateRequestDto(BaseModel):
    status: Literal["pending", "approved", "rejected"]
