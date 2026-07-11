from fastapi import APIRouter
from vms_services.services.media_service import MediaService

router = APIRouter(prefix="/media", tags=["Media"])
service = MediaService()

@router.get("/video/{filename}")
async def get_video(filename: str):
    return service.get_video_file(filename)

@router.get("/report/{filename}")
async def get_report(filename: str):
    return service.get_report_file(filename)
