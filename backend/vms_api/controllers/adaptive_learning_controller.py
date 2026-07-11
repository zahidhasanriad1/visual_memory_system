from typing import Annotated
from fastapi import APIRouter, Depends, File, Form, UploadFile
from vms_api.dependency_services.service_dependencies import get_service_provider
from vms_services.service_injection import ServiceProvider
from vms_utils.common.api_response import ApiResponse

router = APIRouter(prefix="/adaptive-learning", tags=["Adaptive Learning"])

@router.post("/crop/analyze")
async def analyze_crop(image_file: UploadFile = File(...), yolo_class_name: str | None = Form(None), yolo_confidence: float | None = Form(None), services: Annotated[ServiceProvider, Depends(get_service_provider)] = None):
    data = await services.adaptive_learning.analyze_crop_async(await image_file.read(), image_file.filename or "crop.jpg", yolo_class_name, yolo_confidence)
    return ApiResponse(success=True, message="Adaptive learning crop analysis completed successfully.", data=data).to_response()
