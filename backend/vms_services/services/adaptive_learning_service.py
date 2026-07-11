import uuid
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from vms_api.appsettings import get_settings
from vms_domain.entities.adaptive_learning_item_entity import AdaptiveLearningItemEntity
from vms_models.dtos.adaptive_learning.adaptive_learning_response_dto import AdaptiveLearningResponseDto
from vms_models.dtos.adaptive_learning.vlm_object_naming_response_dto import VlmObjectNamingResponseDto
from vms_utils.ai.huggingface_vlm_client import HuggingFaceVlmClient
from vms_utils.exceptions.app_exception import AppException

class AdaptiveLearningService:
    """VLM-assisted object naming and human review workflow."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._settings = get_settings()
        self._vlm = HuggingFaceVlmClient()

    async def analyze_crop_async(self, image_bytes: bytes, filename: str, yolo_class_name: str | None, yolo_confidence: float | None, auto_threshold: float = 0.82) -> AdaptiveLearningResponseDto:
        if not image_bytes:
            raise AppException("Image file is empty.")
        item_id = uuid.uuid4().hex
        result = await self._vlm.name_object(image_bytes, filename)
        object_name = self._normalize_label(result.get("object_name", "unknown_object")) or "unknown_object"
        score = float(result.get("confidence_score", 0.0) or 0.0)
        level = str(result.get("confidence_level", "low"))
        is_unknown = bool(result.get("is_unknown", object_name == "unknown_object"))
        auto = not is_unknown and level == "high" and score >= auto_threshold
        status = "auto_labeled" if auto else "review_required"
        final_label = object_name if auto else None
        target_root = self._settings.dataset_dir / "adaptive_learning" / status / (final_label or "unknown")
        target_root.mkdir(parents=True, exist_ok=True)
        ext = Path(filename).suffix.lower() or ".jpg"
        path = target_root / f"{item_id}{ext}"
        path.write_bytes(image_bytes)
        entity = AdaptiveLearningItemEntity(id=item_id, status=status, source_type="uploaded_crop", stored_image_path=str(path), yolo_class_name=yolo_class_name, yolo_confidence=yolo_confidence, vlm_object_name=object_name, vlm_confidence_level=level, vlm_confidence_score=score, final_label=final_label, admin_review_required=not auto)
        self._session.add(entity)
        await self._session.commit()
        vlm_dto = VlmObjectNamingResponseDto(object_name=object_name, confidence_level=level, confidence_score=score, is_unknown=is_unknown, short_explanation=result.get("short_explanation"), vlm_status=result.get("vlm_status", "completed"), vlm_error=result.get("vlm_error"))
        reason = "Auto-labeled because VLM confidence is high." if auto else "Sent to admin review because VLM was unsure or below threshold."
        return AdaptiveLearningResponseDto(item_id=item_id, status=status, stored_image_path=str(path), yolo_class_name=yolo_class_name, yolo_confidence=yolo_confidence, vlm_result=vlm_dto, final_label=final_label, admin_review_required=not auto, decision_reason=reason)

    def _normalize_label(self, label: str | None) -> str:
        if not label:
            return ""
        return "_".join(label.lower().strip().replace("-", "_").split())
