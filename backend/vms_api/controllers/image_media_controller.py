from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from vms_api.appsettings import get_settings

router = APIRouter(prefix="/media", tags=["Image Media"])


STORAGE_ROOT = get_settings().storage_root.resolve()

IMAGE_UPLOAD_DIR = STORAGE_ROOT / "uploads" / "images"
IMAGE_OUTPUT_DIR = STORAGE_ROOT / "outputs" / "image_features"
IMAGE_CROP_DIR = STORAGE_ROOT / "crops" / "images"

ALLOWED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
    ".tif",
    ".tiff",
}

IMMUTABLE_IMAGE_HEADERS = {
    "Cache-Control": "public, max-age=31536000, immutable",
}


def safe_resolve_file(base_dir: Path, *parts: str) -> Path:
    file_path = base_dir.joinpath(*parts).resolve()
    base_dir_resolved = base_dir.resolve()

    try:
        file_path.relative_to(base_dir_resolved)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid file path.",
            },
        )

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail={
                "message": "File not found.",
            },
        )

    if file_path.suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Unsupported image file extension.",
            },
        )

    return file_path


def image_file_response(file_path: Path) -> FileResponse:
    # Let Starlette infer image/jpeg, image/png, etc. from the real extension.
    # Inline disposition preserves browser and <img> rendering behavior.
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        content_disposition_type="inline",
        headers=IMMUTABLE_IMAGE_HEADERS,
    )


@router.get("/image-upload/{filename}")
async def get_uploaded_image(filename: str):
    file_path = safe_resolve_file(IMAGE_UPLOAD_DIR, filename)

    return image_file_response(file_path)


@router.get("/image-output/{filename}")
async def get_image_output(filename: str):
    file_path = safe_resolve_file(IMAGE_OUTPUT_DIR, filename)

    return image_file_response(file_path)


@router.get("/image-crop/{request_id}/{filename}")
async def get_image_crop(request_id: str, filename: str):
    file_path = safe_resolve_file(IMAGE_CROP_DIR, request_id, filename)

    return image_file_response(file_path)
