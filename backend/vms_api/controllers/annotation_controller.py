from typing import Annotated
from fastapi import APIRouter, Depends, Query, Response, status
from vms_api.dependency_services.service_dependencies import get_service_provider
from vms_models.dtos.annotation.annotation_project_create_request_dto import AnnotationProjectCreateRequestDto
from vms_models.dtos.annotation.annotation_task_create_request_dto import AnnotationTaskCreateRequestDto
from vms_models.dtos.annotation.annotation_object_create_request_dto import AnnotationObjectCreateRequestDto
from vms_models.dtos.annotation.annotation_status_update_request_dto import AnnotationStatusUpdateRequestDto
from vms_services.service_injection import ServiceProvider
from vms_utils.common.api_response import ApiResponse

router = APIRouter(prefix="/annotation", tags=["Annotation"])

@router.get("/projects")
async def list_projects(services: Annotated[ServiceProvider, Depends(get_service_provider)]):
    data = await services.annotation.list_projects_async()
    return ApiResponse(success=True, message="Annotation projects loaded successfully.", data=data).to_response()

@router.post("/projects")
async def create_project(request: AnnotationProjectCreateRequestDto, services: Annotated[ServiceProvider, Depends(get_service_provider)]):
    data = await services.annotation.create_project_async(request)
    return ApiResponse(success=True, message="Annotation project created successfully.", data=data).to_response()

@router.get("/tasks")
async def list_tasks(
    services: Annotated[ServiceProvider, Depends(get_service_provider)],
    project_id: str | None = Query(default=None),
):
    data = await services.annotation.list_tasks_async(project_id)
    return ApiResponse(success=True, message="Annotation tasks loaded successfully.", data=data).to_response()

@router.post("/tasks")
async def create_task(request: AnnotationTaskCreateRequestDto, services: Annotated[ServiceProvider, Depends(get_service_provider)]):
    data = await services.annotation.create_task_async(request)
    return ApiResponse(success=True, message="Annotation task created successfully.", data=data).to_response()

@router.get("/objects")
async def list_objects(
    services: Annotated[ServiceProvider, Depends(get_service_provider)],
    task_id: str | None = Query(default=None),
):
    data = await services.annotation.list_objects_async(task_id)
    return ApiResponse(success=True, message="Annotation objects loaded successfully.", data=data).to_response()

@router.post("/objects")
async def create_object(request: AnnotationObjectCreateRequestDto, services: Annotated[ServiceProvider, Depends(get_service_provider)]):
    data = await services.annotation.create_object_async(request)
    return ApiResponse(success=True, message="Annotation object created successfully.", data=data).to_response()


@router.get("/labels")
async def list_labels(services: Annotated[ServiceProvider, Depends(get_service_provider)]):
    data = await services.annotation.list_labels_async()
    return ApiResponse(success=True, message="Annotation labels loaded successfully.", data=data).to_response()


@router.patch("/objects/{object_id}/status")
async def update_object_status(
    object_id: str,
    request: AnnotationStatusUpdateRequestDto,
    services: Annotated[ServiceProvider, Depends(get_service_provider)],
):
    data = await services.annotation.update_object_status_async(object_id, request.status)
    return ApiResponse(success=True, message="Annotation review status updated.", data=data).to_response()


@router.delete("/objects/{object_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_object(
    object_id: str,
    services: Annotated[ServiceProvider, Depends(get_service_provider)],
):
    await services.annotation.delete_object_async(object_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
