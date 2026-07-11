from typing import Annotated
from fastapi import APIRouter, Depends
from vms_api.dependency_services.service_dependencies import get_service_provider
from vms_models.dtos.model_registry.model_register_request_dto import ModelRegisterRequestDto
from vms_services.service_injection import ServiceProvider
from vms_utils.common.api_response import ApiResponse

router = APIRouter(prefix="/model-registry", tags=["Model Registry"])

@router.post("/models")
async def register_model(request: ModelRegisterRequestDto, services: Annotated[ServiceProvider, Depends(get_service_provider)]):
    data = await services.model_registry.register_model_async(request)
    return ApiResponse(success=True, message="Model registered successfully.", data=data).to_response()

@router.get("/models")
async def list_models(services: Annotated[ServiceProvider, Depends(get_service_provider)]):
    data = await services.model_registry.list_models_async()
    return ApiResponse(success=True, message="Models retrieved successfully.", data=data).to_response()

@router.post("/models/{model_id}/activate")
async def activate_model(model_id: str, services: Annotated[ServiceProvider, Depends(get_service_provider)]):
    data = await services.model_registry.activate_model_async(model_id)
    return ApiResponse(success=True, message="Model activated successfully.", data=data).to_response()
