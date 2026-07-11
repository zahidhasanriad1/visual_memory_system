from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends

from vms_api.dependency_services.service_dependencies import get_service_provider
from vms_models.dtos.training.custom_dataset_create_request_dto import (
    CustomDatasetCreateRequestDto,
)
from vms_models.dtos.training.training_job_start_request_dto import (
    TrainingJobStartRequestDto,
)
from vms_services.service_injection import ServiceProvider
from vms_services.services.training_service import run_training_job_background
from vms_utils.common.api_response import ApiResponse

router = APIRouter(prefix="/training-jobs", tags=["Custom Training"])


def _public_training_data(value):
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    if isinstance(value, dict):
        return {
            key: _public_training_data(item)
            for key, item in value.items()
            if not key.endswith("_path") and not key.endswith("_paths")
        }
    if isinstance(value, list):
        return [_public_training_data(item) for item in value]
    return value


@router.post("/datasets/from-annotations")
async def create_dataset_from_annotations(
    request: CustomDatasetCreateRequestDto,
    services: Annotated[ServiceProvider, Depends(get_service_provider)],
):
    data = await services.training.create_dataset_from_annotations_async(request)
    return ApiResponse(
        success=True,
        message="Versioned training dataset created from approved annotations.",
        data=_public_training_data(data),
    ).to_response()


@router.get("/datasets")
async def list_training_datasets(
    services: Annotated[ServiceProvider, Depends(get_service_provider)],
):
    data = await services.training.list_datasets_async()
    return ApiResponse(
        success=True,
        message="Training datasets loaded successfully.",
        data=_public_training_data(data),
    ).to_response()


@router.post("/start")
async def start_training(
    request: TrainingJobStartRequestDto,
    background_tasks: BackgroundTasks,
    services: Annotated[ServiceProvider, Depends(get_service_provider)],
):
    data = await services.training.start_training_async(request)
    background_tasks.add_task(run_training_job_background, data.job_id)
    return ApiResponse(
        success=True,
        message="Training job created successfully.",
        data=_public_training_data(data),
    ).to_response()


@router.get("")
async def list_training_jobs(
    services: Annotated[ServiceProvider, Depends(get_service_provider)],
):
    data = await services.training.list_training_jobs_async()
    return ApiResponse(
        success=True,
        message="Training jobs loaded successfully.",
        data=_public_training_data(data),
    ).to_response()


@router.get("/{job_id}")
async def get_training_job(
    job_id: str,
    services: Annotated[ServiceProvider, Depends(get_service_provider)],
):
    data = await services.training.get_training_job_async(job_id)
    return ApiResponse(
        success=True,
        message="Training job loaded successfully.",
        data=_public_training_data(data),
    ).to_response()
