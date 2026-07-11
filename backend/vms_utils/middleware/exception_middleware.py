from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from vms_api.appsettings import get_settings
from vms_utils.common.api_response import ApiResponse
from vms_utils.exceptions.app_exception import AppException


class ExceptionMiddleware(BaseHTTPMiddleware):
    """Central safe exception handler."""

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except AppException as error:
            return ApiResponse(success=False, message=error.message, data=error.data).to_response(error.status_code)
        except Exception as error:
            settings = get_settings()
            data = {"reason": str(error)} if settings.app_debug else {}

            return ApiResponse(success=False, message="Internal server error.", data=data).to_response(500)
