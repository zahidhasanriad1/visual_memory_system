from pydantic import BaseModel
from vms_models.dtos.adaptive_learning.vlm_object_naming_response_dto import VlmObjectNamingResponseDto
class AdaptiveLearningResponseDto(BaseModel):
    item_id: str
    status: str
    stored_image_path: str
    yolo_class_name: str | None
    yolo_confidence: float | None
    vlm_result: VlmObjectNamingResponseDto
    final_label: str | None
    admin_review_required: bool
    decision_reason: str
