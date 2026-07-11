from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from vms_api.appsettings import get_settings
from vms_utils.common.api_response import ApiResponse


class UploadSizeMiddleware(BaseHTTPMiddleware):
    """Rejects oversized uploads before they reach expensive services."""

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        content_length = request.headers.get("content-length")
        if content_length:
            max_bytes = settings.max_upload_size_mb * 1024 * 1024
            if int(content_length) > max_bytes:
                return ApiResponse(success=False, message="Uploaded payload is too large.", data={"max_mb": settings.max_upload_size_mb}).to_response(413)
        return await call_next(request)
