from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from vms_api.dependency_services.service_dependencies import get_service_provider
from vms_models.dtos.video_memory.video_processing_settings_dto import VideoProcessingSettingsDto
from vms_services.service_injection import ServiceProvider
from vms_utils.common.api_response import ApiResponse

router = APIRouter(prefix="/video-memory", tags=["Video Memory"])

async def _build_settings(
    detector_model: str = Form("yolo"),
    processing_mode: str = Form("full_video"),
    sample_every_seconds: float = Form(1.0),
    max_frames: int = Form(0),
    confidence_threshold: float = Form(0.25),
    iou_threshold: float = Form(0.45),
    max_detections_per_frame: int = Form(50),
    tracker_iou_threshold: float = Form(0.30),
    crop_padding_pixels: int = Form(8),
    enable_memory_storage: bool = Form(True),
    enable_duplicate_pruning: bool = Form(True),
    create_annotated_video: bool = Form(True),
    output_video_fps: float = Form(0.0),
    save_detector_annotated_image: bool = Form(False),
) -> VideoProcessingSettingsDto:
    return VideoProcessingSettingsDto(
        detector_model=detector_model,
        processing_mode=processing_mode,
        sample_every_seconds=sample_every_seconds,
        max_frames=max_frames,
        confidence_threshold=confidence_threshold,
        iou_threshold=iou_threshold,
        max_detections_per_frame=max_detections_per_frame,
        tracker_iou_threshold=tracker_iou_threshold,
        crop_padding_pixels=crop_padding_pixels,
        enable_memory_storage=enable_memory_storage,
        enable_duplicate_pruning=enable_duplicate_pruning,
        create_annotated_video=create_annotated_video,
        output_video_fps=output_video_fps,
        save_detector_annotated_image=save_detector_annotated_image,
    )

@router.post("/jobs/ingest-video")
async def create_video_job(background_tasks: BackgroundTasks, file: UploadFile = File(...), settings: Annotated[VideoProcessingSettingsDto, Depends(_build_settings)] = None, services: Annotated[ServiceProvider, Depends(get_service_provider)] = None):
    file_bytes = await file.read()
    data = await services.video_memory.create_job_async(file_bytes=file_bytes, filename=file.filename or "video.mp4", settings=settings)
    background_tasks.add_task(services.video_memory.process_job_async, data["job_id"], data["source_video_path"], file.filename or "video.mp4", settings)
    return ApiResponse(success=True, message="Video processing job created successfully.", data={k:v for k,v in data.items() if k != "settings"}).to_response()

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str, services: Annotated[ServiceProvider, Depends(get_service_provider)]):
    data = await services.video_memory.get_job_status_async(job_id)
    return ApiResponse(success=True, message="Video job status retrieved successfully.", data=data).to_response()

@router.get("/jobs/{job_id}/result")
async def get_job_result(job_id: str, services: Annotated[ServiceProvider, Depends(get_service_provider)]):
    data = await services.video_memory.get_job_result_async(job_id)
    return ApiResponse(success=True, message="Video job result retrieved successfully.", data=data).to_response()
