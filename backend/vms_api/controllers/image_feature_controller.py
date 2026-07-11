from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from vms_services.interfaces.i_image_feature_service import IImageFeatureService
from vms_services.service_injection import get_image_feature_service

router = APIRouter(tags=["Image Features"])


def _public_image_data(value):
    """Remove server/host filesystem locations from every public image response."""

    if isinstance(value, dict):
        return {
            key: _public_image_data(item)
            for key, item in value.items()
            if not key.endswith("_path") and not key.endswith("_paths")
        }
    if isinstance(value, list):
        return [_public_image_data(item) for item in value]
    return value


@router.get("/image-features/dashboard-images")
def get_dashboard_images(
    limit: int = Query(default=50, ge=1, le=200),
    image_feature_service: IImageFeatureService = Depends(get_image_feature_service),
):
    result = image_feature_service.list_dashboard_images(limit=limit)

    return {
        "success": True,
        "message": "Image feature dashboard images loaded successfully.",
        "data": _public_image_data(result.model_dump()),
    }


@router.post("/crops/test-image")
async def test_image_crop(
    file: UploadFile = File(...),
    detector_model: str = Form("yolo"),
    crop_padding_pixels: int = Form(8),
    image_feature_service: IImageFeatureService = Depends(get_image_feature_service),
):
    result = await image_feature_service.test_crops(
        file=file,
        crop_padding_pixels=crop_padding_pixels,
        detector_model=detector_model,
    )

    return {
        "success": True,
        "message": result.message,
        "data": _public_image_data(result.model_dump()),
    }


@router.post("/detections/test-image")
async def test_image_detection(
    file: UploadFile = File(...),
    confidence_threshold: float = Form(0.25),
    iou_threshold: float = Form(0.45),
    detector_model: str = Form("yolo"),
    image_feature_service: IImageFeatureService = Depends(get_image_feature_service),
):
    result = await image_feature_service.test_detections(
        file=file,
        confidence_threshold=confidence_threshold,
        iou_threshold=iou_threshold,
        detector_model=detector_model,
    )

    return {
        "success": True,
        "message": result.message,
        "data": _public_image_data(result.model_dump()),
    }


@router.post("/detection-crops/test-image")
async def test_image_detection_crops(
    file: UploadFile = File(...),
    confidence_threshold: float = Form(0.25),
    iou_threshold: float = Form(0.45),
    detector_model: str = Form("yolo"),
    crop_padding_pixels: int = Form(8),
    image_feature_service: IImageFeatureService = Depends(get_image_feature_service),
):
    result = await image_feature_service.test_detection_crops(
        file=file,
        confidence_threshold=confidence_threshold,
        iou_threshold=iou_threshold,
        crop_padding_pixels=crop_padding_pixels,
        detector_model=detector_model,
    )

    return {
        "success": True,
        "message": result.message,
        "data": _public_image_data(result.model_dump()),
    }


@router.post("/object-memory/ingest-image")
async def ingest_image_to_object_memory(
    file: UploadFile = File(...),
    confidence_threshold: float = Form(0.25),
    iou_threshold: float = Form(0.45),
    detector_model: str = Form("yolo"),
    crop_padding_pixels: int = Form(8),
    image_feature_service: IImageFeatureService = Depends(get_image_feature_service),
):
    result = await image_feature_service.ingest_image_to_memory(
        file=file,
        confidence_threshold=confidence_threshold,
        iou_threshold=iou_threshold,
        crop_padding_pixels=crop_padding_pixels,
        detector_model=detector_model,
    )

    return {
        "success": True,
        "message": result.message,
        "data": _public_image_data(result.model_dump()),
    }


@router.post("/object-memory/search-image")
async def search_object_memory_by_image(
    file: UploadFile = File(...),
    detector_model: str = Form("yolo"),
    top_k: int = Form(5),
    image_feature_service: IImageFeatureService = Depends(get_image_feature_service),
):
    result = await image_feature_service.search_image_memory(
        file=file,
        top_k=top_k,
        detector_model=detector_model,
    )

    return {
        "success": True,
        "message": result.message,
        "data": _public_image_data(result.model_dump()),
    }
