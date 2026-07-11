from vms_api.controllers.image_feature_controller import _public_image_data
from vms_utils.common.api_response import _remove_internal_locations


def test_public_responses_remove_nested_filesystem_locations() -> None:
    payload = {
        "source_image_path": "/app/storage/private.jpg",
        "source_image_url": "/api/v1/media/image-upload/id.jpg",
        "detections": [
            {
                "annotated_image_path": r"E:\VMS-X\private.jpg",
                "annotated_image_url": "/api/v1/media/image-output/id.jpg",
            }
        ],
        "crop_image_paths": ["secret"],
    }

    for sanitizer in (_public_image_data, _remove_internal_locations):
        public = sanitizer(payload)
        serialized = str(public)
        assert "_path" not in serialized
        assert "/app/storage" not in serialized
        assert "E:\\VMS-X" not in serialized
        assert public["source_image_url"].startswith("/api/v1/media/")
