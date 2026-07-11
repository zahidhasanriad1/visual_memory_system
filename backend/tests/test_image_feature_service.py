from io import BytesIO
from pathlib import Path, PureWindowsPath

import cv2
import numpy as np
import pytest
from fastapi import UploadFile
from PIL import Image
from starlette.datastructures import Headers

from vms_services.services.image_feature_service import ImageFeatureService
from vms_utils.ai.detected_object import DetectedObject
from vms_utils.exceptions.app_exception import AppException


class _FakeSkyDetDetector:
    def __init__(self, model_path: Path) -> None:
        self._model_path = model_path
        self._load_attempted = True
        self._model = object()
        self.load_error = None

    def detect(
        self,
        frame: np.ndarray,
        confidence_threshold: float,
        iou_threshold: float,
        max_detections: int,
    ) -> list[DetectedObject]:
        assert frame.shape[:2] == (120, 200)
        assert confidence_threshold == 0.25
        assert iou_threshold == 0.45
        assert max_detections == 500
        return [
            DetectedObject.create(
                class_id=3,
                class_name="ship",
                confidence=0.87654321,
                x_min=20,
                y_min=40,
                x_max=150,
                y_max=90,
            )
        ]


class _BrokenSkyDetDetector(_FakeSkyDetDetector):
    def detect(self, *args, **kwargs) -> list[DetectedObject]:
        self.load_error = "checkpoint shape mismatch"
        return []


def _make_service(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ImageFeatureService:
    storage_root = tmp_path / "storage"
    monkeypatch.setenv("VMS_STORAGE_ROOT", str(storage_root))
    monkeypatch.setenv("VMS_HOST_STORAGE_ROOT", r"E:\VMS-X\backend\storage")
    monkeypatch.setenv("IMAGE_OUTPUT_JPEG_QUALITY", "80")
    monkeypatch.setenv("IMAGE_CROP_JPEG_QUALITY", "80")
    return ImageFeatureService()


def _make_upload() -> UploadFile:
    image = np.full((120, 200, 3), (30, 60, 90), dtype=np.uint8)
    ok, encoded = cv2.imencode(".png", image)
    assert ok
    return UploadFile(
        BytesIO(encoded.tobytes()),
        filename="sky scene.png",
        headers=Headers({"content-type": "image/png"}),
    )


def _make_tiff_upload() -> UploadFile:
    buffer = BytesIO()
    Image.fromarray(np.zeros((900, 1400, 3), dtype=np.uint8)).save(
        buffer,
        format="TIFF",
        compression="tiff_adobe_deflate",
    )
    buffer.seek(0)
    return UploadFile(
        buffer,
        filename="large-scene.tif",
        headers=Headers({"content-type": "image/tiff"}),
    )


@pytest.mark.asyncio
async def test_skydet_selection_and_detailed_paths_are_preserved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _make_service(tmp_path, monkeypatch)
    fake_model_path = tmp_path / "skydet.pt"
    fake_model_path.touch()
    service._detectors["skydet"] = _FakeSkyDetDetector(fake_model_path)

    response = await service.test_detections(
        file=_make_upload(),
        confidence_threshold=0.25,
        iou_threshold=0.45,
        detector_model=" Sky-Det ",
    )

    expected_output = PureWindowsPath(
        r"E:\VMS-X\backend\storage\outputs\image_features"
    ) / f"{response.request_id}_annotated.jpg"
    internal_output = (
        service.output_dir / f"{response.request_id}_annotated.jpg"
    )

    assert response.detector_model == "skydet"
    assert response.model_loaded is True
    assert response.detector_warning is None
    assert response.total_detection_count == 1
    assert response.annotated_image_path == str(expected_output)
    assert response.annotated_image_url == (
        f"/api/v1/media/image-output/{response.request_id}_annotated.jpg"
    )
    assert response.detections[0]["detector_model"] == "skydet"
    assert response.detections[0]["class_name"] == "ship"
    assert response.detections[0]["confidence"] == 0.876543
    assert response.detections[0]["annotated_image_path"] == str(expected_output)
    assert response.source_image_path.startswith(r"E:\VMS-X\backend\storage\uploads")
    assert internal_output.is_file()


def test_detector_normalization_does_not_silently_run_yolo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _make_service(tmp_path, monkeypatch)

    assert service._normalize_detector_model("SkyDet") == "skydet"
    assert service._normalize_detector_model("sky_det") == "skydet"
    assert service._normalize_detector_model(" YOLO ") == "yolo"

    with pytest.raises(AppException) as error:
        service._normalize_detector_model("unknown")

    assert error.value.status_code == 422


def test_detection_crop_uses_full_image_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _make_service(tmp_path, monkeypatch)
    image = np.zeros((10, 10, 3), dtype=np.uint8)
    detections = [
        {
            "detection_id": "detection-1",
            "detector_model": "skydet",
            "class_id": 2,
            "class_name": "car",
            "confidence": 0.9,
            "bbox": {"x_min": 8, "y_min": 8, "x_max": 10, "y_max": 10},
        }
    ]

    crops = service._crop_detections(
        request_id="request-1",
        image_bgr=image,
        detections=detections,
        crop_padding_pixels=4,
    )

    assert len(crops) == 1
    assert crops[0]["detector_model"] == "skydet"
    assert crops[0]["bbox"] == {
        "x_min": 4,
        "y_min": 4,
        "x_max": 10,
        "y_max": 10,
    }
    saved_crop = cv2.imread(crops[0]["crop_path"])
    assert saved_crop.shape[:2] == (6, 6)


def test_windows_host_path_still_builds_valid_media_url(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _make_service(tmp_path, monkeypatch)
    windows_path = r"E:\VMS-X\backend\storage\outputs\image_features\abc_annotated.jpg"

    assert service._build_output_url(windows_path) == (
        "/api/v1/media/image-output/abc_annotated.jpg"
    )


@pytest.mark.asyncio
async def test_failed_skydet_inference_is_not_reported_as_loaded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _make_service(tmp_path, monkeypatch)
    fake_model_path = tmp_path / "broken-skydet.pt"
    fake_model_path.touch()
    service._detectors["skydet"] = _BrokenSkyDetDetector(fake_model_path)

    response = await service.test_detections(
        file=_make_upload(),
        confidence_threshold=0.25,
        iou_threshold=0.45,
        detector_model="skydet",
    )

    assert response.detector_model == "skydet"
    assert response.model_loaded is False
    assert response.detector_warning == (
        "SKYDET detection warning: checkpoint shape mismatch"
    )


@pytest.mark.asyncio
async def test_tiff_uses_bounded_browser_preview(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("IMAGE_MAX_INFERENCE_SIDE", "640")
    service = _make_service(tmp_path, monkeypatch)

    response = await service.test_crops(
        file=_make_tiff_upload(),
        crop_padding_pixels=8,
        detector_model="skydet",
    )

    assert response.content_type == "image/tiff"
    assert response.source_width == 1400
    assert response.source_height == 900
    assert response.width == 640
    assert response.height < 640
    assert response.inference_scaled is True
    assert response.source_image_url.endswith("_source_preview.jpg")
