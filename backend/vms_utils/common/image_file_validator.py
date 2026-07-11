from pathlib import Path
from fastapi import UploadFile

from vms_utils.exceptions.app_exception import AppException


class ImageFileValidator:
    """
    Validates image uploads for the image feature pipeline.
    Supports common web, scientific, and dataset image formats.
    """

    ALLOWED_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".webp",
        ".tif",
        ".tiff",
    }

    ALLOWED_CONTENT_TYPES = {
        "image/jpeg",
        "image/png",
        "image/bmp",
        "image/webp",
        "image/tiff",
        "application/octet-stream",
    }

    MAX_IMAGE_SIZE_MB = 200

    FORMAT_EXTENSIONS = {
        "jpeg": {".jpg", ".jpeg"},
        "png": {".png"},
        "bmp": {".bmp"},
        "webp": {".webp"},
        "tiff": {".tif", ".tiff"},
    }

    FORMAT_CONTENT_TYPES = {
        "jpeg": "image/jpeg",
        "png": "image/png",
        "bmp": "image/bmp",
        "webp": "image/webp",
        "tiff": "image/tiff",
    }

    @classmethod
    def validate_upload(cls, file: UploadFile) -> str:
        if not file.filename:
            raise AppException(
                message="Image filename is missing.",
                status_code=400,
            )

        extension = Path(file.filename).suffix.lower()

        if extension not in cls.ALLOWED_EXTENSIONS:
            raise AppException(
                message=f"Unsupported image type: {extension}. Supported: jpg, jpeg, png, bmp, webp, tif, tiff.",
                status_code=400,
            )

        if file.content_type and file.content_type not in cls.ALLOWED_CONTENT_TYPES:
            raise AppException(
                message=f"Unsupported image content type: {file.content_type}.",
                status_code=400,
            )

        return extension

    @classmethod
    def validate_size(cls, file_bytes: bytes) -> None:
        size_mb = len(file_bytes) / (1024 * 1024)

        if size_mb > cls.MAX_IMAGE_SIZE_MB:
            raise AppException(
                message=f"Image is too large. Maximum allowed size is {cls.MAX_IMAGE_SIZE_MB} MB.",
                status_code=413,
            )

    @classmethod
    def validate_signature(
        cls,
        file_bytes: bytes,
        extension: str,
        declared_content_type: str | None,
    ) -> str:
        """Return the verified MIME type and reject misleading extensions/MIME."""

        image_format = cls._detect_format(file_bytes)
        if image_format is None:
            raise AppException(
                message="Image bytes do not match a supported image format.",
                status_code=400,
            )

        allowed_extensions = cls.FORMAT_EXTENSIONS[image_format]
        if extension not in allowed_extensions:
            raise AppException(
                message=(
                    f"Image content is {image_format.upper()}, but the filename "
                    f"extension is {extension}."
                ),
                status_code=400,
            )

        actual_content_type = cls.FORMAT_CONTENT_TYPES[image_format]
        if declared_content_type not in {
            None,
            "",
            "application/octet-stream",
            actual_content_type,
        }:
            raise AppException(
                message=(
                    f"Image content type is {actual_content_type}, but the upload "
                    f"declared {declared_content_type}."
                ),
                status_code=400,
            )

        return actual_content_type

    @staticmethod
    def _detect_format(file_bytes: bytes) -> str | None:
        if file_bytes.startswith(b"\xff\xd8\xff"):
            return "jpeg"
        if file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            return "png"
        if file_bytes.startswith(b"BM"):
            return "bmp"
        if (
            len(file_bytes) >= 12
            and file_bytes.startswith(b"RIFF")
            and file_bytes[8:12] == b"WEBP"
        ):
            return "webp"
        if file_bytes.startswith(
            (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+")
        ):
            return "tiff"
        return None
