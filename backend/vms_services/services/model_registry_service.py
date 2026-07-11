from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from vms_domain.entities.model_version_entity import ModelVersionEntity
from vms_models.dtos.model_registry.model_register_request_dto import ModelRegisterRequestDto
from vms_models.dtos.model_registry.model_version_response_dto import ModelVersionResponseDto
from vms_utils.exceptions.app_exception import AppException

class ModelRegistryService:
    """Safe model lifecycle registry with activation and rollback support."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def register_model_async(self, request: ModelRegisterRequestDto) -> ModelVersionResponseDto:
        entity = ModelVersionEntity(model_name=request.model_name, model_type=request.model_type, version=request.version, model_path=request.model_path, onnx_path=request.onnx_path, class_names=request.class_names, metrics=request.metrics, status="validated")
        self._session.add(entity); await self._session.commit(); await self._session.refresh(entity)
        return self._to_dto(entity)

    async def list_models_async(self) -> list[ModelVersionResponseDto]:
        result = await self._session.execute(select(ModelVersionEntity).order_by(ModelVersionEntity.created_at.desc()))
        return [self._to_dto(item) for item in result.scalars().all()]

    async def activate_model_async(self, model_id: str) -> ModelVersionResponseDto:
        entity = await self._session.get(ModelVersionEntity, model_id)
        if not entity:
            raise AppException("Model not found.", status_code=404)
        await self._session.execute(update(ModelVersionEntity).where(ModelVersionEntity.model_type == entity.model_type).values(status="archived"))
        entity.status = "active"
        await self._session.commit(); await self._session.refresh(entity)
        return self._to_dto(entity)

    def _to_dto(self, entity: ModelVersionEntity) -> ModelVersionResponseDto:
        return ModelVersionResponseDto(id=entity.id, model_name=entity.model_name, model_type=entity.model_type, version=entity.version, model_path=entity.model_path, onnx_path=entity.onnx_path, class_names=entity.class_names, metrics=entity.metrics, status=entity.status)
