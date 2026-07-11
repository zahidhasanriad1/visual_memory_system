from fastapi import APIRouter
from vms_utils.common.api_response import ApiResponse

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
async def health():
    return ApiResponse(success=True, message="VMS-X backend is healthy.", data={"system": "VMS-X", "status": "healthy"}).to_response()
