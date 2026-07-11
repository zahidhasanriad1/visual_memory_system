from pathlib import Path

import pytest
from fastapi import HTTPException

from vms_api.controllers.image_media_controller import (
    image_file_response,
    safe_resolve_file,
)


def test_image_response_uses_specific_mime_and_inline_disposition(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "annotated.jpg"
    image_path.write_bytes(b"jpeg-test")

    response = image_file_response(image_path)

    assert response.media_type == "image/jpeg"
    assert response.headers["content-disposition"].startswith("inline;")
    assert response.headers["cache-control"] == "public, max-age=31536000, immutable"


def test_safe_resolve_rejects_sibling_prefix_traversal(tmp_path: Path) -> None:
    base_dir = tmp_path / "images"
    base_dir.mkdir()
    sibling_dir = tmp_path / "images-escape"
    sibling_dir.mkdir()
    (sibling_dir / "hidden.jpg").write_bytes(b"not-public")

    with pytest.raises(HTTPException) as error:
        safe_resolve_file(base_dir, "..", sibling_dir.name, "hidden.jpg")

    assert error.value.status_code == 400
