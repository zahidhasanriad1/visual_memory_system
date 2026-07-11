import cv2
import numpy as np
import pytest

from vms_utils.common.image_file_validator import ImageFileValidator
from vms_utils.exceptions.app_exception import AppException


def _encoded_png() -> bytes:
    image = np.zeros((8, 8, 3), dtype=np.uint8)
    ok, encoded = cv2.imencode(".png", image)
    assert ok
    return encoded.tobytes()


def test_signature_returns_verified_content_type() -> None:
    content_type = ImageFileValidator.validate_signature(
        file_bytes=_encoded_png(),
        extension=".png",
        declared_content_type="application/octet-stream",
    )

    assert content_type == "image/png"


def test_signature_rejects_filename_extension_mismatch() -> None:
    with pytest.raises(AppException) as error:
        ImageFileValidator.validate_signature(
            file_bytes=_encoded_png(),
            extension=".jpg",
            declared_content_type="image/jpeg",
        )

    assert error.value.status_code == 400


def test_signature_rejects_declared_mime_mismatch() -> None:
    with pytest.raises(AppException) as error:
        ImageFileValidator.validate_signature(
            file_bytes=_encoded_png(),
            extension=".png",
            declared_content_type="image/jpeg",
        )

    assert error.value.status_code == 400
