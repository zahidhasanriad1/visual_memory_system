from pydantic import BaseModel
class VlmObjectNamingResponseDto(BaseModel):
    object_name: str
    confidence_level: str
    confidence_score: float
    is_unknown: bool
    short_explanation: str | None = None
    vlm_status: str
    vlm_error: str | None = None
