from pydantic import BaseModel
class AdaptiveReviewRequestDto(BaseModel):
    decision: str
    corrected_label: str | None = None
    notes: str | None = None
