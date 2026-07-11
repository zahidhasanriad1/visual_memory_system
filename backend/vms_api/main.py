import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from vms_api.appsettings import get_settings
from vms_domain.database.session import create_database_schema
from vms_utils.middleware.exception_middleware import ExceptionMiddleware
from vms_utils.middleware.request_logging_middleware import RequestLoggingMiddleware
from vms_utils.middleware.upload_size_middleware import UploadSizeMiddleware
from vms_api.controllers import auth_controller, video_memory_controller, adaptive_learning_controller, annotation_controller, model_registry_controller, training_controller, media_controller, health_controller
from vms_api.controllers.image_feature_controller import router as image_feature_router
from vms_api.controllers.cloud_ai_controller import router as cloud_ai_router
from vms_api.controllers.image_media_controller import router as image_media_router

settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0")
local_dev_origin_regex = (
    r"https?://("
    r"localhost|127\.0\.0\.1|0\.0\.0\.0|"
    r"192\.168\.\d{1,3}\.\d{1,3}|"
    r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}"
    r")(:\d+)?"
)

app.add_middleware(ExceptionMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(UploadSizeMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=local_dev_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_controller.router, prefix=settings.api_prefix)
app.include_router(auth_controller.router, prefix=settings.api_prefix)
app.include_router(video_memory_controller.router, prefix=settings.api_prefix)
app.include_router(adaptive_learning_controller.router, prefix=settings.api_prefix)
app.include_router(annotation_controller.router, prefix=settings.api_prefix)
app.include_router(model_registry_controller.router, prefix=settings.api_prefix)
app.include_router(training_controller.router, prefix=settings.api_prefix)
app.include_router(media_controller.router, prefix=settings.api_prefix)
app.include_router(image_feature_router, prefix=settings.api_prefix)
app.include_router(cloud_ai_router, prefix=settings.api_prefix)
app.include_router(image_media_router, prefix=settings.api_prefix)

@app.on_event("startup")
async def on_startup() -> None:
    await create_database_schema()

if __name__ == "__main__":
    uvicorn.run("vms_api.main:app", host="0.0.0.0", port=8000, reload=True)
