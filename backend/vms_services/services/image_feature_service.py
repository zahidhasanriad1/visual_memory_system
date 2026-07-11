import asyncio
import json
import math
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from threading import Lock, RLock
from typing import Any

import cv2
import numpy as np
from fastapi import UploadFile
from PIL import Image

from vms_api.appsettings import get_settings
from vms_models.dtos.image_features.image_feature_dashboard_item_dto import (
    ImageFeatureDashboardItemDto,
)
from vms_models.dtos.image_features.image_feature_dashboard_response_dto import (
    ImageFeatureDashboardResponseDto,
)
from vms_models.dtos.image_features.image_feature_response_dto import ImageFeatureResponseDto
from vms_services.interfaces.i_image_feature_service import IImageFeatureService
from vms_utils.ai.skydet_detector import SkyDetDetector
from vms_utils.ai.yolo_detector import YoloDetector
from vms_utils.common.image_file_validator import ImageFileValidator
from vms_utils.exceptions.app_exception import AppException

class ImageFeatureService(IImageFeatureService):
    """
    Industry-grade image feature pipeline:
    - upload validation
    - image decoding
    - YOLO/ONNX detection
    - detection crop generation
    - lightweight visual memory ingestion
    - image-to-memory similarity search
    - browser-accessible media URLs
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.storage_root = Path(os.getenv("VMS_STORAGE_ROOT") or settings.storage_root).resolve()
        # Container paths are correct for I/O but not useful to a host-side user.
        # When configured, response DTOs are mapped to this display-only root while
        # all reads and writes continue to use ``storage_root``.
        self.host_storage_root = (
            os.getenv("VMS_HOST_STORAGE_ROOT", "").strip()
            or settings.host_storage_root.strip()
            or str(self.storage_root)
        )

        self.upload_dir = self.storage_root / "uploads" / "images"
        self.crop_dir = self.storage_root / "crops" / "images"
        self.output_dir = self.storage_root / "outputs" / "image_features"
        self.memory_dir = self.storage_root / "object_memory"
        self.tiled_detection_enabled = os.getenv("IMAGE_TILED_DETECTION_ENABLED", "true").lower() == "true"
        self.tile_size = int(os.getenv("IMAGE_TILE_SIZE", "1024"))
        self.tile_overlap_ratio = float(os.getenv("IMAGE_TILE_OVERLAP_RATIO", "0.25"))
        self.tiled_min_side = int(os.getenv("IMAGE_TILED_MIN_SIDE", "1400"))
        self.max_inference_side = max(
            640,
            int(os.getenv("IMAGE_MAX_INFERENCE_SIDE", "2560")),
        )
        self.max_source_pixels = max(
            10_000_000,
            int(os.getenv("IMAGE_MAX_SOURCE_PIXELS", "300000000")),
        )
        Image.MAX_IMAGE_PIXELS = self.max_source_pixels
        self.output_jpeg_quality = min(
            100,
            max(70, int(os.getenv("IMAGE_OUTPUT_JPEG_QUALITY", "90"))),
        )
        self.crop_jpeg_quality = min(
            100,
            max(70, int(os.getenv("IMAGE_CROP_JPEG_QUALITY", "90"))),
        )
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.crop_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self.memory_file = self.memory_dir / "image_memory.json"
        self.history_file = self.output_dir / "image_feature_history.json"

        self.yolo_model_path = os.getenv(
            "YOLO_MODEL_PATH",
            "storage/models/skysealand_yolo12m_best.onnx",
        )

        self.yolo_input_size = int(os.getenv("YOLO_INPUT_SIZE", "640"))

        class_names_from_env = os.getenv("YOLO_CLASS_NAMES", "airplane,boat,car,ship")
        self.class_names = [
            item.strip()
            for item in class_names_from_env.split(",")
            if item.strip()
        ]

        self._detector_net: cv2.dnn_Net | None = None
        self._detectors = {
            "yolo": YoloDetector(settings.yolo_model_path),
            "skydet": SkyDetDetector(settings.skydet_model_path),
        }
        self._detector_locks = {name: Lock() for name in self._detectors}
        self._history_lock = RLock()
        self._memory_lock = RLock()
        self.last_detector_warning: str | None = None

    async def test_crops(
        self,
        file: UploadFile,
        crop_padding_pixels: int,
        detector_model: str = "yolo",
    ) -> ImageFeatureResponseDto:
        normalized_detector = self._normalize_detector_model(detector_model)
        context = await self._save_and_decode_image(file)
        context["detector_model"] = normalized_detector
        whole_crop = await asyncio.to_thread(
            self._save_whole_image_crop,
            context,
            crop_padding_pixels,
        )

        response = self._build_response(
            context=context,
            message="Image crop test completed successfully.",
            crops=[whole_crop],
        )

        await asyncio.to_thread(self._record_dashboard_result, "crop_test", response)

        return response

    async def test_detections(
        self,
        file: UploadFile,
        confidence_threshold: float,
        iou_threshold: float,
        detector_model: str = "yolo",
    ) -> ImageFeatureResponseDto:
        normalized_detector = self._normalize_detector_model(detector_model)
        context = await self._save_and_decode_image(file)
        context["detector_model"] = normalized_detector

        detections, detector_warning = await asyncio.to_thread(
            self._detect_objects_with_status,
            context["image_bgr"],
            confidence_threshold,
            iou_threshold,
            context["detector_model"],
        )
        context["detector_warning"] = detector_warning

        await asyncio.to_thread(
            self._attach_annotated_image_if_needed,
            context["request_id"],
            context["image_bgr"],
            detections,
            context["detector_model"],
        )

        response = self._build_response(
            context=context,
            message="Image detection test completed successfully.",
            detections=detections,
        )

        await asyncio.to_thread(self._record_dashboard_result, "detection_test", response)

        return response

    async def test_detection_crops(
        self,
        file: UploadFile,
        confidence_threshold: float,
        iou_threshold: float,
        crop_padding_pixels: int,
        detector_model: str = "yolo",
    ) -> ImageFeatureResponseDto:
        normalized_detector = self._normalize_detector_model(detector_model)
        context = await self._save_and_decode_image(file)
        context["detector_model"] = normalized_detector

        detections, detector_warning = await asyncio.to_thread(
            self._detect_objects_with_status,
            context["image_bgr"],
            confidence_threshold,
            iou_threshold,
            context["detector_model"],
        )
        context["detector_warning"] = detector_warning

        await asyncio.to_thread(
            self._attach_annotated_image_if_needed,
            context["request_id"],
            context["image_bgr"],
            detections,
            context["detector_model"],
        )

        crops = await asyncio.to_thread(
            self._crop_detections,
            context["request_id"],
            context["image_bgr"],
            detections,
            crop_padding_pixels,
        )

        response = self._build_response(
            context=context,
            message="Detection crop test completed successfully.",
            detections=detections,
            crops=crops,
        )

        await asyncio.to_thread(
            self._record_dashboard_result,
            "detection_crop_test",
            response,
        )

        return response

    async def ingest_image_to_memory(
        self,
        file: UploadFile,
        confidence_threshold: float,
        iou_threshold: float,
        crop_padding_pixels: int,
        detector_model: str = "yolo",
    ) -> ImageFeatureResponseDto:
        normalized_detector = self._normalize_detector_model(detector_model)
        context = await self._save_and_decode_image(file)
        context["detector_model"] = normalized_detector

        detections, detector_warning = await asyncio.to_thread(
            self._detect_objects_with_status,
            context["image_bgr"],
            confidence_threshold,
            iou_threshold,
            context["detector_model"],
        )
        context["detector_warning"] = detector_warning

        await asyncio.to_thread(
            self._attach_annotated_image_if_needed,
            context["request_id"],
            context["image_bgr"],
            detections,
            context["detector_model"],
        )

        crops = await asyncio.to_thread(
            self._crop_detections,
            context["request_id"],
            context["image_bgr"],
            detections,
            crop_padding_pixels,
        )

        if not crops:
            crops = [
                await asyncio.to_thread(
                    self._save_whole_image_crop,
                    context,
                    crop_padding_pixels,
                )
            ]

        memory_items = await asyncio.to_thread(
            self._ingest_crops_into_memory,
            context,
            crops,
        )

        response = self._build_response(
            context=context,
            message="Image objects ingested into visual memory successfully.",
            detections=detections,
            crops=crops,
            memory_items=memory_items,
        )

        await asyncio.to_thread(self._record_dashboard_result, "memory_ingest", response)

        return response

    async def search_image_memory(
        self,
        file: UploadFile,
        top_k: int,
        detector_model: str = "yolo",
    ) -> ImageFeatureResponseDto:
        normalized_detector = self._normalize_detector_model(detector_model)
        context = await self._save_and_decode_image(file)
        context["detector_model"] = normalized_detector

        matches = await asyncio.to_thread(
            self._search_memory_items,
            context["image_bgr"],
            top_k,
        )

        response = self._build_response(
            context=context,
            message="Image memory search completed successfully.",
            matches=matches,
        )

        await asyncio.to_thread(self._record_dashboard_result, "memory_search", response)

        return response

    def list_dashboard_images(
        self,
        limit: int,
    ) -> ImageFeatureDashboardResponseDto:
        safe_limit = min(max(1, limit), 200)
        items_by_request: dict[str, ImageFeatureDashboardItemDto] = {}

        for source_path in self._iter_image_files(self.upload_dir, limit=safe_limit):
            item = self._build_lightweight_dashboard_item_from_source(source_path)
            items_by_request[item.request_id] = item

        for history_item in self._load_dashboard_history_items():
            existing_item = items_by_request.get(history_item.request_id)
            items_by_request[history_item.request_id] = self._merge_dashboard_items(
                existing_item=existing_item,
                history_item=history_item,
            )

        all_items = sorted(
            items_by_request.values(),
            key=lambda item: item.updated_at,
            reverse=True,
        )

        total_items = len(all_items)
        source_image_count = len(
            [item for item in all_items if "source" in item.image_kinds]
        )
        annotated_image_count = len(
            [item for item in all_items if "detection" in item.image_kinds]
        )
        crop_image_count = sum(item.crop_count for item in all_items)
        detection_count = sum(item.detection_count for item in all_items)
        memory_item_count = sum(item.memory_item_count for item in all_items)

        visible_items = [
            self._compact_dashboard_item_for_list(item)
            for item in all_items[:safe_limit]
        ]

        return ImageFeatureDashboardResponseDto(
            total_count=total_items,
            source_image_count=source_image_count,
            annotated_image_count=annotated_image_count,
            crop_image_count=crop_image_count,
            detection_count=detection_count,
            memory_item_count=memory_item_count,
            items=visible_items,
        )

    async def _save_and_decode_image(self, file: UploadFile) -> dict:
        extension = ImageFileValidator.validate_upload(file)
        request_id = str(uuid.uuid4())
        safe_filename = f"{request_id}{extension}"
        saved_path = self.upload_dir / safe_filename

        await file.seek(0)
        try:
            header, file_size_bytes = await asyncio.to_thread(
                self._persist_upload_stream,
                file.file,
                saved_path,
            )
            verified_content_type = ImageFileValidator.validate_signature(
                file_bytes=header,
                extension=extension,
                declared_content_type=file.content_type,
            )
            decoded = await asyncio.to_thread(
                self._decode_saved_image,
                saved_path,
                request_id,
            )
        except Exception:
            saved_path.unlink(missing_ok=True)
            raise

        if decoded is None:
            saved_path.unlink(missing_ok=True)
            raise AppException(
                message="Unable to decode image. File may be corrupted.",
                status_code=400,
            )

        image_bgr = decoded["image_bgr"]
        height, width = image_bgr.shape[:2]
        preview_path = decoded.get("preview_path")
        source_image_url = (
            self._build_output_url(str(preview_path))
            if preview_path
            else self._build_upload_url(str(saved_path))
        )

        return {
            "request_id": request_id,
            "source_filename": file.filename or safe_filename,
            "source_image_path": str(saved_path),
            "source_image_url": source_image_url,
            "file_size_bytes": file_size_bytes,
            "content_type": verified_content_type,
            "image_bgr": image_bgr,
            "width": width,
            "height": height,
            "source_width": decoded["source_width"],
            "source_height": decoded["source_height"],
            "inference_scaled": bool(decoded["inference_scaled"]),
        }

    def _persist_upload_stream(
        self,
        source_file,
        saved_path: Path,
    ) -> tuple[bytes, int]:
        max_bytes = ImageFileValidator.MAX_IMAGE_SIZE_MB * 1024 * 1024
        total_bytes = 0
        header = b""
        source_file.seek(0)

        with saved_path.open("wb") as target:
            while True:
                chunk = source_file.read(1024 * 1024)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    raise AppException(
                        message=(
                            "Image is too large. Maximum allowed size is "
                            f"{ImageFileValidator.MAX_IMAGE_SIZE_MB} MB."
                        ),
                        status_code=413,
                    )
                if len(header) < 16:
                    header = (header + chunk)[:16]
                target.write(chunk)

        return header, total_bytes

    def _decode_saved_image(
        self,
        saved_path: Path,
        request_id: str,
    ) -> dict | None:
        try:
            with Image.open(saved_path) as pil_image:
                source_width, source_height = pil_image.size
                source_pixels = source_width * source_height
                if source_pixels > self.max_source_pixels:
                    raise AppException(
                        message=(
                            "Image dimensions are too large for safe processing. "
                            f"Maximum is {self.max_source_pixels:,} pixels."
                        ),
                        status_code=413,
                    )

                requires_preview = (
                    pil_image.format == "TIFF"
                    or max(source_width, source_height) > self.max_inference_side
                )

                if requires_preview:
                    bounded = pil_image.convert("RGB")
                    bounded.thumbnail(
                        (self.max_inference_side, self.max_inference_side),
                        Image.Resampling.LANCZOS,
                        reducing_gap=3.0,
                    )
                    image_rgb = np.asarray(bounded)
                    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
                else:
                    image_bgr = cv2.imread(str(saved_path), cv2.IMREAD_COLOR)

            if image_bgr is None:
                return None

            inference_scaled = (
                image_bgr.shape[1] != source_width
                or image_bgr.shape[0] != source_height
            )
            preview_path = None
            if requires_preview:
                preview_path = self.output_dir / f"{request_id}_source_preview.jpg"
                if not cv2.imwrite(
                    str(preview_path),
                    image_bgr,
                    [int(cv2.IMWRITE_JPEG_QUALITY), 86],
                ):
                    raise AppException(
                        message="Unable to save browser-safe image preview.",
                        status_code=500,
                    )

            return {
                "image_bgr": image_bgr,
                "source_width": source_width,
                "source_height": source_height,
                "inference_scaled": inference_scaled,
                "preview_path": preview_path,
            }
        except AppException:
            raise
        except Exception:
            return None

    def _detect_objects(
        self,
        image_bgr: np.ndarray,
        confidence_threshold: float,
        iou_threshold: float,
        detector_model: str = "yolo",
    ) -> list[dict]:
        detections, warning = self._detect_objects_with_status(
            image_bgr=image_bgr,
            confidence_threshold=confidence_threshold,
            iou_threshold=iou_threshold,
            detector_model=detector_model,
        )
        # Kept for compatibility with existing diagnostics. Request responses use
        # the local warning returned above and cannot be overwritten by another
        # concurrent request on this singleton service.
        self.last_detector_warning = warning
        return detections

    def _detect_objects_with_status(
        self,
        image_bgr: np.ndarray,
        confidence_threshold: float,
        iou_threshold: float,
        detector_model: str = "yolo",
    ) -> tuple[list[dict], str | None]:
        normalized_model = self._normalize_detector_model(detector_model)

        if normalized_model == "yolo":
            return self._detect_yolo_with_opencv(
                image_bgr=image_bgr,
                confidence_threshold=confidence_threshold,
                iou_threshold=iou_threshold,
            )

        detector = self._detectors[normalized_model]

        try:
            # Most detector runtimes and CUDA model objects are not safe to invoke
            # concurrently. Serialize per model (YOLO and SkyDet can still run in
            # parallel with one another) while the FastAPI event loop stays free.
            with self._detector_locks[normalized_model]:
                if (
                    self.tiled_detection_enabled
                    and max(image_bgr.shape[:2]) >= self.tiled_min_side
                ):
                    normalized_detections = self._detect_adapter_tiled(
                        detector=detector,
                        image_bgr=image_bgr,
                        confidence_threshold=confidence_threshold,
                        iou_threshold=iou_threshold,
                        detector_model=normalized_model,
                    )
                else:
                    detections = detector.detect(
                        image_bgr,
                        confidence_threshold,
                        iou_threshold,
                        max_detections=500,
                    )
                    normalized_detections = [
                        self._detected_object_to_dict(item, normalized_model)
                        for item in detections
                    ]
            load_error = getattr(detector, "load_error", None)
            warning = (
                f"{normalized_model.upper()} detection warning: {load_error}"
                if load_error
                else None
            )
            return normalized_detections, warning
        except Exception as exc:
            return (
                [],
                f"{normalized_model.upper()} detection unavailable: {exc}",
            )

    def _detect_yolo_with_opencv(
        self,
        image_bgr: np.ndarray,
        confidence_threshold: float,
        iou_threshold: float,
    ) -> tuple[list[dict], str | None]:
        """Run the existing ONNX/tiled YOLO path without Ultralytics overhead."""

        detector = self._detectors["yolo"]
        model_path = Path(getattr(detector, "_model_path", self.yolo_model_path))
        if not model_path.is_absolute():
            model_path = (Path.cwd() / model_path).resolve()

        if not model_path.exists():
            return [], f"YOLO detection warning: model not found: {model_path}"

        try:
            with self._detector_locks["yolo"]:
                self.last_detector_warning = None
                net = self._load_detector_net(model_path)
                height, width = image_bgr.shape[:2]
                if (
                    self.tiled_detection_enabled
                    and max(height, width) >= self.tiled_min_side
                ):
                    detections = self._detect_objects_tiled(
                        net=net,
                        image_bgr=image_bgr,
                        confidence_threshold=confidence_threshold,
                        iou_threshold=iou_threshold,
                    )
                else:
                    detections = self._detect_objects_single_pass(
                        net=net,
                        image_bgr=image_bgr,
                        confidence_threshold=confidence_threshold,
                        iou_threshold=iou_threshold,
                    )
                warning = self.last_detector_warning

            for detection in detections:
                detection["detector_model"] = "yolo"
            return detections, warning
        except Exception as exc:
            return [], f"YOLO detection unavailable: {exc}"

    def _detect_adapter_tiled(
        self,
        detector,
        image_bgr: np.ndarray,
        confidence_threshold: float,
        iou_threshold: float,
        detector_model: str,
    ) -> list[dict]:
        """Run adapter-backed detectors on bounded tiles and merge globally."""

        height, width = image_bgr.shape[:2]
        tile_size = max(self.yolo_input_size, self.tile_size)
        overlap_pixels = int(tile_size * self.tile_overlap_ratio)
        stride = max(1, tile_size - overlap_pixels)
        x_starts = self._build_tile_starts(width, tile_size, stride)
        y_starts = self._build_tile_starts(height, tile_size, stride)
        all_detections: list[dict] = []

        for y_start in y_starts:
            for x_start in x_starts:
                x_end = min(width, x_start + tile_size)
                y_end = min(height, y_start + tile_size)
                tile_image = image_bgr[y_start:y_end, x_start:x_end]
                if tile_image.size == 0:
                    continue

                tile_detections = detector.detect(
                    tile_image,
                    confidence_threshold,
                    iou_threshold,
                    max_detections=100,
                )
                for item in tile_detections:
                    detection = self._detected_object_to_dict(item, detector_model)
                    bbox = detection["bbox"]
                    detection["bbox"] = {
                        "x_min": max(0, min(width - 1, bbox["x_min"] + x_start)),
                        "y_min": max(0, min(height - 1, bbox["y_min"] + y_start)),
                        "x_max": max(0, min(width - 1, bbox["x_max"] + x_start)),
                        "y_max": max(0, min(height - 1, bbox["y_max"] + y_start)),
                    }
                    all_detections.append(detection)

        return self._apply_global_nms(
            detections=all_detections,
            confidence_threshold=confidence_threshold,
            iou_threshold=iou_threshold,
        )

    def _normalize_detector_model(self, detector_model: str | None) -> str:
        normalized = (detector_model or "").strip().lower().replace("-", "").replace("_", "")
        aliases = {
            "yolo": "yolo",
            "skydet": "skydet",
        }
        if normalized not in aliases:
            raise AppException(
                message="Unsupported detector model. Use 'yolo' or 'skydet'.",
                status_code=422,
                data={"detector_model": detector_model},
            )
        return aliases[normalized]

    def reload_detector(
        self,
        detector_model: str,
        model_path: Path,
        class_names: list[str] | None = None,
    ) -> None:
        """Atomically reload an activated model without restarting the API."""

        normalized_model = self._normalize_detector_model(detector_model)
        with self._detector_locks[normalized_model]:
            if normalized_model == "skydet":
                self._detectors["skydet"] = SkyDetDetector(model_path)
            else:
                self._detectors["yolo"] = YoloDetector(model_path)
                self._detector_net = None
                if class_names:
                    self.class_names = list(class_names)

    def _detected_object_to_dict(self, detection, detector_model: str) -> dict:
        return {
            "detection_id": detection.detection_id,
            "detector_model": detector_model,
            "class_id": detection.class_id,
            "class_name": detection.class_name,
            "confidence": round(float(detection.confidence), 6),
            "bbox": {
                "x_min": int(round(detection.x_min)),
                "y_min": int(round(detection.y_min)),
                "x_max": int(round(detection.x_max)),
                "y_max": int(round(detection.y_max)),
            },
        }

    def _detect_objects_single_pass(
        self,
        net: cv2.dnn_Net,
        image_bgr: np.ndarray,
        confidence_threshold: float,
        iou_threshold: float,
    ) -> list[dict]:
        input_size = self.yolo_input_size

        letterboxed, scale, pad_x, pad_y = self._letterbox(image_bgr, input_size)

        blob = cv2.dnn.blobFromImage(
            letterboxed,
            scalefactor=1 / 255.0,
            size=(input_size, input_size),
            mean=(0, 0, 0),
            swapRB=True,
            crop=False,
        )

        net.setInput(blob)
        outputs = net.forward()

        return self._postprocess_yolo_output(
            output=outputs,
            original_shape=image_bgr.shape,
            input_size=input_size,
            scale=scale,
            pad_x=pad_x,
            pad_y=pad_y,
            confidence_threshold=confidence_threshold,
            iou_threshold=iou_threshold,
        )


    def _detect_objects_tiled(
        self,
        net: cv2.dnn_Net,
        image_bgr: np.ndarray,
        confidence_threshold: float,
        iou_threshold: float,
    ) -> list[dict]:
        height, width = image_bgr.shape[:2]

        tile_size = max(self.yolo_input_size, self.tile_size)
        overlap_pixels = int(tile_size * self.tile_overlap_ratio)
        stride = max(1, tile_size - overlap_pixels)

        x_starts = self._build_tile_starts(
            full_length=width,
            tile_size=tile_size,
            stride=stride,
        )

        y_starts = self._build_tile_starts(
            full_length=height,
            tile_size=tile_size,
            stride=stride,
        )

        all_detections: list[dict] = []

        for y_start in y_starts:
            for x_start in x_starts:
                x_end = min(width, x_start + tile_size)
                y_end = min(height, y_start + tile_size)

                tile_image = image_bgr[y_start:y_end, x_start:x_end]

                if tile_image.size == 0:
                    continue

                tile_detections = self._detect_objects_single_pass(
                    net=net,
                    image_bgr=tile_image,
                    confidence_threshold=confidence_threshold,
                    iou_threshold=iou_threshold,
                )

                for detection in tile_detections:
                    bbox = detection["bbox"]

                    x_min = int(bbox["x_min"]) + x_start
                    y_min = int(bbox["y_min"]) + y_start
                    x_max = int(bbox["x_max"]) + x_start
                    y_max = int(bbox["y_max"]) + y_start

                    detection["bbox"] = {
                        "x_min": max(0, min(width - 1, x_min)),
                        "y_min": max(0, min(height - 1, y_min)),
                        "x_max": max(0, min(width - 1, x_max)),
                        "y_max": max(0, min(height - 1, y_max)),
                    }

                    detection["tile"] = {
                        "x_min": x_start,
                        "y_min": y_start,
                        "x_max": x_end,
                        "y_max": y_end,
                    }

                    all_detections.append(detection)

        return self._apply_global_nms(
            detections=all_detections,
            confidence_threshold=confidence_threshold,
            iou_threshold=iou_threshold,
        )


    def _build_tile_starts(
        self,
        full_length: int,
        tile_size: int,
        stride: int,
    ) -> list[int]:
        if full_length <= tile_size:
            return [0]

        starts = list(range(0, full_length - tile_size + 1, stride))

        last_start = full_length - tile_size

        if starts[-1] != last_start:
            starts.append(last_start)

        return starts


    def _apply_global_nms(
        self,
        detections: list[dict],
        confidence_threshold: float,
        iou_threshold: float,
    ) -> list[dict]:
        if not detections:
            return []

        boxes: list[list[int]] = []
        confidences: list[float] = []

        for detection in detections:
            bbox = detection["bbox"]

            x_min = int(bbox["x_min"])
            y_min = int(bbox["y_min"])
            x_max = int(bbox["x_max"])
            y_max = int(bbox["y_max"])

            boxes.append(
                [
                    x_min,
                    y_min,
                    max(1, x_max - x_min),
                    max(1, y_max - y_min),
                ]
            )

            confidences.append(float(detection["confidence"]))

        nms_indices = cv2.dnn.NMSBoxes(
            bboxes=boxes,
            scores=confidences,
            score_threshold=confidence_threshold,
            nms_threshold=iou_threshold,
        )

        if len(nms_indices) == 0:
            return []

        final_detections: list[dict] = []

        for raw_index in nms_indices:
            index = (
                int(raw_index[0])
                if isinstance(raw_index, (list, tuple, np.ndarray))
                else int(raw_index)
            )

            final_detections.append(detections[index])

        final_detections = sorted(
            final_detections,
            key=lambda item: float(item.get("confidence", 0.0)),
            reverse=True,
        )

        return final_detections

    def _load_detector_net(self, model_path: Path) -> cv2.dnn_Net:
        if self._detector_net is None:
            self._detector_net = cv2.dnn.readNetFromONNX(str(model_path))

        return self._detector_net

    def _letterbox(
        self,
        image_bgr: np.ndarray,
        input_size: int,
    ) -> tuple[np.ndarray, float, int, int]:
        height, width = image_bgr.shape[:2]

        scale = min(input_size / width, input_size / height)

        new_width = int(round(width * scale))
        new_height = int(round(height * scale))

        resized = cv2.resize(image_bgr, (new_width, new_height))

        canvas = np.full(
            shape=(input_size, input_size, 3),
            fill_value=114,
            dtype=np.uint8,
        )

        pad_x = (input_size - new_width) // 2
        pad_y = (input_size - new_height) // 2

        canvas[
            pad_y : pad_y + new_height,
            pad_x : pad_x + new_width,
        ] = resized

        return canvas, scale, pad_x, pad_y

    def _postprocess_yolo_output(
        self,
        output: Any,
        original_shape: tuple,
        input_size: int,
        scale: float,
        pad_x: int,
        pad_y: int,
        confidence_threshold: float,
        iou_threshold: float,
    ) -> list[dict]:
        original_height, original_width = original_shape[:2]

        predictions = output

        if isinstance(predictions, tuple):
            predictions = predictions[0]

        predictions = np.array(predictions)

        if predictions.ndim == 3:
            predictions = predictions[0]

        if predictions.ndim != 2:
            self.last_detector_warning = (
                f"Unsupported YOLO output shape: {predictions.shape}"
            )
            return []

        if predictions.shape[0] < predictions.shape[1]:
            predictions = predictions.T

        boxes: list[list[int]] = []
        confidences: list[float] = []
        class_ids: list[int] = []

        for row in predictions:
            if len(row) < 6:
                continue

            box_values = row[:4]

            if np.max(box_values) <= 2.0:
                cx = float(box_values[0] * input_size)
                cy = float(box_values[1] * input_size)
                box_width = float(box_values[2] * input_size)
                box_height = float(box_values[3] * input_size)
            else:
                cx = float(box_values[0])
                cy = float(box_values[1])
                box_width = float(box_values[2])
                box_height = float(box_values[3])

            scores = row[4:]

            if len(scores) == len(self.class_names) + 1:
                objectness = float(scores[0])
                class_scores = scores[1:]
                class_id = int(np.argmax(class_scores))
                confidence = objectness * float(class_scores[class_id])
            else:
                class_scores = scores
                class_id = int(np.argmax(class_scores))
                confidence = float(class_scores[class_id])

            if confidence < confidence_threshold:
                continue

            x_min = int((cx - box_width / 2 - pad_x) / scale)
            y_min = int((cy - box_height / 2 - pad_y) / scale)
            x_max = int((cx + box_width / 2 - pad_x) / scale)
            y_max = int((cy + box_height / 2 - pad_y) / scale)

            x_min = max(0, min(original_width - 1, x_min))
            y_min = max(0, min(original_height - 1, y_min))
            x_max = max(0, min(original_width - 1, x_max))
            y_max = max(0, min(original_height - 1, y_max))

            if x_max <= x_min or y_max <= y_min:
                continue

            boxes.append([x_min, y_min, x_max - x_min, y_max - y_min])
            confidences.append(confidence)
            class_ids.append(class_id)

        if not boxes:
            return []

        nms_indices = cv2.dnn.NMSBoxes(
            bboxes=boxes,
            scores=confidences,
            score_threshold=confidence_threshold,
            nms_threshold=iou_threshold,
        )

        detections: list[dict] = []

        if len(nms_indices) == 0:
            return detections

        for raw_index in nms_indices:
            index = (
                int(raw_index[0])
                if isinstance(raw_index, (list, tuple, np.ndarray))
                else int(raw_index)
            )

            x, y, w, h = boxes[index]
            class_id = class_ids[index]

            class_name = (
                self.class_names[class_id]
                if class_id < len(self.class_names)
                else f"class_{class_id}"
            )

            detections.append(
                {
                    "detection_id": str(uuid.uuid4()),
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": round(float(confidences[index]), 6),
                    "bbox": {
                        "x_min": int(x),
                        "y_min": int(y),
                        "x_max": int(x + w),
                        "y_max": int(y + h),
                    },
                }
            )

        return detections

    def _crop_detections(
        self,
        request_id: str,
        image_bgr: np.ndarray,
        detections: list[dict],
        crop_padding_pixels: int,
    ) -> list[dict]:
        crops: list[dict] = []
        height, width = image_bgr.shape[:2]

        crop_folder = self.crop_dir / request_id
        crop_folder.mkdir(parents=True, exist_ok=True)

        for index, detection in enumerate(detections):
            bbox = detection["bbox"]

            x_min = max(0, int(bbox["x_min"]) - crop_padding_pixels)
            y_min = max(0, int(bbox["y_min"]) - crop_padding_pixels)
            # x_max/y_max are exclusive crop bounds, matching NumPy slicing and
            # the whole-image crop contract (width/height at the far edge).
            x_max = min(width, int(bbox["x_max"]) + crop_padding_pixels)
            y_max = min(height, int(bbox["y_max"]) + crop_padding_pixels)

            if x_max <= x_min or y_max <= y_min:
                continue

            crop_image = image_bgr[y_min:y_max, x_min:x_max]
            crop_filename = f"crop_{index + 1:04d}_{detection['class_name']}.jpg"
            crop_path = crop_folder / crop_filename

            crop_saved = cv2.imwrite(
                str(crop_path),
                crop_image,
                [int(cv2.IMWRITE_JPEG_QUALITY), self.crop_jpeg_quality],
            )
            if not crop_saved:
                raise AppException(
                    message=f"Unable to save detection crop: {crop_filename}",
                    status_code=500,
                )

            crops.append(
                {
                    "crop_id": str(uuid.uuid4()),
                    "detection_id": detection["detection_id"],
                    "detector_model": detection.get("detector_model", "yolo"),
                    "class_id": detection["class_id"],
                    "class_name": detection["class_name"],
                    "confidence": detection["confidence"],
                    "bbox": {
                        "x_min": x_min,
                        "y_min": y_min,
                        "x_max": x_max,
                        "y_max": y_max,
                    },
                    "crop_path": str(crop_path),
                    "crop_url": self._build_crop_url(str(crop_path), request_id),
                }
            )

        return crops

    def _save_whole_image_crop(
        self,
        context: dict,
        crop_padding_pixels: int,
    ) -> dict:
        crop_folder = self.crop_dir / context["request_id"]
        crop_folder.mkdir(parents=True, exist_ok=True)

        crop_path = crop_folder / "whole_image.jpg"
        crop_saved = cv2.imwrite(
            str(crop_path),
            context["image_bgr"],
            [int(cv2.IMWRITE_JPEG_QUALITY), self.crop_jpeg_quality],
        )
        if not crop_saved:
            raise AppException(
                message="Unable to save whole-image crop.",
                status_code=500,
            )

        return {
            "crop_id": str(uuid.uuid4()),
            "detection_id": None,
            "detector_model": context["detector_model"],
            "class_id": None,
            "class_name": "whole_image",
            "confidence": 1.0,
            "bbox": {
                "x_min": 0,
                "y_min": 0,
                "x_max": context["width"],
                "y_max": context["height"],
            },
            "crop_path": str(crop_path),
            "crop_url": self._build_crop_url(
                str(crop_path),
                context["request_id"],
            ),
            "crop_padding_pixels": crop_padding_pixels,
        }
    
    def _get_class_color(self, class_name: str) -> tuple[int, int, int]:
        """
        Returns high-contrast, satellite-friendly BGR colors for each class.
        OpenCV uses BGR, not RGB.
        """

        class_colors = {
            "airplane": (0, 140, 255),
            "boat": (255, 120, 0),
            "ship": (190, 60, 255),
            "car": (55, 210, 55),
            "unknown_object": (185, 185, 185),
        }

        return class_colors.get(class_name.lower(), (0, 215, 255))

    def _format_detection_class_name(self, class_name: str) -> str:
        return class_name.replace("_", " ").strip().title() or "Unknown Object"

    def _draw_filled_rounded_panel(
        self,
        image: np.ndarray,
        x_min: int,
        y_min: int,
        x_max: int,
        y_max: int,
        fill_color: tuple[int, int, int],
        alpha: float = 0.72,
    ) -> None:
        """
        Draws a semi-transparent panel.
        This keeps text readable without fully hiding the image.
        """

        height, width = image.shape[:2]
        clipped_x_min = max(0, min(width, int(x_min)))
        clipped_y_min = max(0, min(height, int(y_min)))
        clipped_x_max = max(0, min(width, int(x_max) + 1))
        clipped_y_max = max(0, min(height, int(y_max) + 1))
        if clipped_x_max <= clipped_x_min or clipped_y_max <= clipped_y_min:
            return

        # Blend only the requested region. Copying a 20+ megapixel image once per
        # label used hundreds of MB and dominated annotation time.
        region = image[clipped_y_min:clipped_y_max, clipped_x_min:clipped_x_max]
        overlay = np.empty_like(region)
        overlay[:] = fill_color
        cv2.addWeighted(overlay, alpha, region, 1 - alpha, 0, dst=region)

    def _annotation_scale(self, image: np.ndarray) -> float:
        height, width = image.shape[:2]
        return max(1.0, min(2.5, max(height, width) / 1600.0))

    def _draw_detection_label(
        self,
        image: np.ndarray,
        x_min: int,
        y_min: int,
        label: str,
        color: tuple[int, int, int],
    ) -> None:
        """
        Draws a modern label badge above the detection box.
        """

        font = cv2.FONT_HERSHEY_DUPLEX
        scale = self._annotation_scale(image)
        font_scale = 0.52 * scale
        thickness = max(2, int(round(1.35 * scale)))
        horizontal_padding = int(round(9 * scale))
        vertical_padding = int(round(7 * scale))

        text_size, _ = cv2.getTextSize(
            label,
            font,
            font_scale,
            thickness,
        )

        text_width, text_height = text_size
        _, image_width = image.shape[:2]

        label_x_min = max(0, min(image_width - 1, x_min))
        label_y_min = max(0, y_min - text_height - (vertical_padding * 2))
        label_x_max = min(
            image_width - 1,
            label_x_min + text_width + (horizontal_padding * 2),
        )
        label_y_max = label_y_min + text_height + (vertical_padding * 2)

        self._draw_filled_rounded_panel(
            image=image,
            x_min=label_x_min,
            y_min=label_y_min,
            x_max=label_x_max,
            y_max=label_y_max,
            fill_color=color,
            alpha=0.88,
        )

        cv2.putText(
            image,
            label,
            (label_x_min + horizontal_padding, label_y_max - vertical_padding),
            font,
            font_scale,
            (255, 255, 255),
            thickness,
            cv2.LINE_AA,
        )

    def _draw_detection_summary_panel(
        self,
        image: np.ndarray,
        detections: list[dict],
        detector_model: str,
    ) -> None:
        """Draw a compact, non-obstructive result badge."""

        if not detections:
            return

        height, width = image.shape[:2]
        ui_scale = self._annotation_scale(image)

        class_counts: dict[str, int] = {}
        for detection in detections:
            class_name = str(detection.get("class_name", "unknown_object"))
            class_counts[class_name] = class_counts.get(class_name, 0) + 1

        total_objects = len(detections)

        margin_x = int(round(14 * ui_scale))
        margin_y = int(round(12 * ui_scale))
        panel_width = min(int(round(270 * ui_scale)), width - (margin_x * 2))
        panel_height = int(round((52 + (len(class_counts) * 20)) * ui_scale))

        x_max = width - margin_x
        y_min = margin_y
        x_min = max(margin_x, x_max - panel_width)
        y_max = min(height - margin_y, y_min + panel_height)

        self._draw_filled_rounded_panel(
            image=image,
            x_min=x_min,
            y_min=y_min,
            x_max=x_max,
            y_max=y_max,
            fill_color=(15, 23, 42),
            alpha=0.84,
        )

        cv2.rectangle(
            image,
            (x_min, y_min),
            (x_max, y_max),
            (100, 116, 139),
            thickness=max(1, int(round(ui_scale))),
            lineType=cv2.LINE_AA,
        )

        body_font = cv2.FONT_HERSHEY_SIMPLEX
        text_thickness = max(1, int(round(ui_scale)))
        left_padding = int(round(12 * ui_scale))

        detector_name = "SkyDet" if detector_model == "skydet" else "YOLO"

        cv2.putText(
            image,
            f"{detector_name}  |  {total_objects} objects",
            (x_min + left_padding, y_min + int(round(23 * ui_scale))),
            cv2.FONT_HERSHEY_DUPLEX,
            0.52 * ui_scale,
            (255, 255, 255),
            text_thickness,
            cv2.LINE_AA,
        )

        y_cursor = y_min + int(round(46 * ui_scale))

        for class_name, count in sorted(class_counts.items()):
            color = self._get_class_color(class_name)

            cv2.circle(
                image,
                (
                    x_min + int(round(15 * ui_scale)),
                    y_cursor - int(round(4 * ui_scale)),
                ),
                max(4, int(round(4 * ui_scale))),
                color,
                thickness=-1,
                lineType=cv2.LINE_AA,
            )

            cv2.putText(
                image,
                f"{self._format_detection_class_name(class_name)}: {count}",
                (x_min + int(round(26 * ui_scale)), y_cursor),
                body_font,
                0.42 * ui_scale,
                (255, 255, 255),
                text_thickness,
                cv2.LINE_AA,
            )

            y_cursor += int(round(20 * ui_scale))

    def _draw_bottom_status_bar(
        self,
        image: np.ndarray,
        detections: list[dict],
        detector_model: str,
    ) -> None:
        """
        Draws a clean bottom bar with project branding and processing status.
        """

        height, width = image.shape[:2]
        ui_scale = self._annotation_scale(image)

        bar_height = int(round(42 * ui_scale))
        y_min = height - bar_height

        self._draw_filled_rounded_panel(
            image=image,
            x_min=0,
            y_min=y_min,
            x_max=width,
            y_max=height,
            fill_color=(2, 6, 23),
            alpha=0.72,
        )

        detector_name = "SkyDet" if detector_model == "skydet" else "YOLO"
        text = (
            f"VMS-X Adaptive Visual Memory Intelligence | "
            f"Detector: {detector_name} | Objects: {len(detections)}"
        )

        cv2.putText(
            image,
            text,
            (int(round(18 * ui_scale)), height - int(round(13 * ui_scale))),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55 * ui_scale,
            (226, 232, 240),
            max(2, int(round(1.25 * ui_scale))),
            cv2.LINE_AA,
        )
    
    def _save_annotated_image(
        self,
        request_id: str,
        image_bgr: np.ndarray,
        detections: list[dict],
        detector_model: str,
    ) -> Path:
        """
        Saves a professional annotated image with:
        - class-wise colors
        - semi-transparent boxes
        - clean label badges
        - detection summary panel
        - VMS-X status bar
        """

        annotated = image_bgr.copy()

        for detection in detections:
            bbox = detection["bbox"]

            x_min = int(bbox["x_min"])
            y_min = int(bbox["y_min"])
            x_max = int(bbox["x_max"])
            y_max = int(bbox["y_max"])

            class_name = str(detection.get("class_name", "unknown_object"))
            color = self._get_class_color(class_name)
            self._draw_filled_rounded_panel(
                image=annotated,
                x_min=x_min,
                y_min=y_min,
                x_max=x_max,
                y_max=y_max,
                fill_color=color,
                alpha=0.14,
            )

        box_thickness = max(2, int(round(self._annotation_scale(annotated) * 2)))
        for detection in detections:
            bbox = detection["bbox"]

            x_min = int(bbox["x_min"])
            y_min = int(bbox["y_min"])
            x_max = int(bbox["x_max"])
            y_max = int(bbox["y_max"])

            class_name = str(detection.get("class_name", "unknown_object"))
            confidence = float(detection.get("confidence", 0.0))
            color = self._get_class_color(class_name)

            label = (
                f"{self._format_detection_class_name(class_name)} "
                f"{confidence * 100:.1f}%"
            )

            cv2.rectangle(
                annotated,
                (x_min, y_min),
                (x_max, y_max),
                color,
                thickness=box_thickness,
                lineType=cv2.LINE_AA,
            )

            self._draw_detection_label(
                image=annotated,
                x_min=x_min,
                y_min=y_min,
                label=label,
                color=color,
            )

        self._draw_detection_summary_panel(
            image=annotated,
            detections=detections,
            detector_model=detector_model,
        )

        annotated_path = self.output_dir / f"{request_id}_annotated.jpg"

        annotated_saved = cv2.imwrite(
            str(annotated_path),
            annotated,
            [
                int(cv2.IMWRITE_JPEG_QUALITY),
                self.output_jpeg_quality,
            ],
        )
        if not annotated_saved:
            raise AppException(
                message="Unable to save annotated detection image.",
                status_code=500,
            )

        return annotated_path

    def _attach_annotated_image_if_needed(
        self,
        request_id: str,
        image_bgr: np.ndarray,
        detections: list[dict],
        detector_model: str,
    ) -> None:
        if not detections:
            return

        annotated_path = self._save_annotated_image(
            request_id=request_id,
            image_bgr=image_bgr,
            detections=detections,
            detector_model=detector_model,
        )

        annotated_url = self._build_output_url(str(annotated_path))

        for item in detections:
            item["detector_model"] = detector_model
            item["annotated_image_path"] = str(annotated_path)
            item["annotated_image_url"] = annotated_url

    def _generate_embedding(self, image_bgr: np.ndarray) -> list[float]:
        """
        Lightweight deterministic visual embedding.
        This keeps memory search functional without forcing heavy GPU dependencies.
        """

        resized = cv2.resize(image_bgr, (128, 128))
        hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)

        hist_h = cv2.calcHist([hsv], [0], None, [32], [0, 180])
        hist_s = cv2.calcHist([hsv], [1], None, [32], [0, 256])
        hist_v = cv2.calcHist([hsv], [2], None, [32], [0, 256])

        embedding = np.concatenate([hist_h, hist_s, hist_v]).flatten()
        norm = np.linalg.norm(embedding)

        if norm == 0:
            return embedding.astype(float).tolist()

        return (embedding / norm).astype(float).tolist()

    def _ingest_crops_into_memory(self, context: dict, crops: list[dict]) -> list[dict]:
        new_items: list[dict] = []
        for crop in crops:
            crop_image = cv2.imread(crop["crop_path"])
            if crop_image is None:
                continue

            new_items.append(
                {
                    "memory_id": str(uuid.uuid4()),
                    "source_request_id": context["request_id"],
                    "source_filename": context["source_filename"],
                    "source_image_path": context["source_image_path"],
                    "source_image_url": self._build_upload_url(context["source_image_path"]),
                    "crop_path": crop["crop_path"],
                    "crop_url": crop.get("crop_url"),
                    "detector_model": context["detector_model"],
                    "class_name": crop.get("class_name", "unknown_object"),
                    "confidence": crop.get("confidence", 0.0),
                    "bbox": crop.get("bbox"),
                    "embedding": self._generate_embedding(crop_image),
                }
            )

        # Persist once per request instead of loading and rewriting the entire JSON
        # file once for every crop.
        self._append_memory_items(new_items)
        return [self._public_memory_item(item) for item in new_items]

    def _search_memory_items(self, image_bgr: np.ndarray, top_k: int) -> list[dict]:
        query_embedding = self._generate_embedding(image_bgr)
        matches: list[dict] = []
        for item in self._load_memory_items():
            item_embedding = item.get("embedding")
            if not item_embedding:
                continue
            public_item = self._public_memory_item(item)
            public_item["similarity_score"] = self._cosine_similarity(
                query_embedding,
                item_embedding,
            )
            matches.append(public_item)

        return sorted(
            matches,
            key=lambda item: item["similarity_score"],
            reverse=True,
        )[: max(1, top_k)]

    def _append_memory_item(self, memory_item: dict) -> None:
        self._append_memory_items([memory_item])

    def _append_memory_items(self, new_items: list[dict]) -> None:
        if not new_items:
            return
        with self._memory_lock:
            memory_items = self._load_memory_items()
            memory_items.extend(new_items)
            self._write_json_atomic(self.memory_file, memory_items)

    def _load_memory_items(self) -> list[dict]:
        with self._memory_lock:
            if not self.memory_file.exists():
                return []

            try:
                with self.memory_file.open("r", encoding="utf-8") as file:
                    data = json.load(file)

                return data if isinstance(data, list) else []
            except (json.JSONDecodeError, OSError):
                return []

    def _public_memory_item(self, memory_item: dict) -> dict:
        public_item = dict(memory_item)
        public_item.pop("embedding", None)

        source_image_path = public_item.get("source_image_path")
        crop_path = public_item.get("crop_path")
        source_request_id = public_item.get("source_request_id")

        if source_image_path and not public_item.get("source_image_url"):
            public_item["source_image_url"] = self._build_upload_url(source_image_path)

        if crop_path and source_request_id and not public_item.get("crop_url"):
            public_item["crop_url"] = self._build_crop_url(crop_path, source_request_id)

        if source_image_path:
            public_item["source_image_path"] = self._to_host_storage_path(source_image_path)
        if crop_path:
            public_item["crop_path"] = self._to_host_storage_path(crop_path)

        return public_item

    def _record_dashboard_result(
        self,
        operation: str,
        response: ImageFeatureResponseDto,
    ) -> None:
        with self._history_lock:
            history_items = self._load_dashboard_history_items()
            history_items = [
                item for item in history_items if item.request_id != response.request_id
            ]
            history_items.append(
                self._build_dashboard_item_from_response(
                    operation=operation,
                    response=response,
                )
            )

            history_items = sorted(
                history_items,
                key=lambda item: item.updated_at,
                reverse=True,
            )[:1000]

            self._write_json_atomic(
                self.history_file,
                [item.model_dump() for item in history_items],
            )

    def _write_json_atomic(self, path: Path, data: Any) -> None:
        temporary_path = path.with_suffix(f"{path.suffix}.tmp")
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, separators=(",", ":"))
        os.replace(temporary_path, path)

    def _build_dashboard_item_from_response(
        self,
        operation: str,
        response: ImageFeatureResponseDto,
    ) -> ImageFeatureDashboardItemDto:
        annotated_image_path = None
        annotated_image_url = None

        for detection in response.detections:
            annotated_image_path = detection.get("annotated_image_path")
            annotated_image_url = detection.get("annotated_image_url")

            if annotated_image_url:
                break

        crop_image_paths = [
            str(crop.get("crop_path"))
            for crop in response.crops
            if crop.get("crop_path")
        ]
        crop_image_urls = [
            str(crop.get("crop_url"))
            for crop in response.crops
            if crop.get("crop_url")
        ]

        class_names = self._extract_dashboard_class_names(
            response.detections,
            response.crops,
            response.memory_items,
            response.matches,
        )

        image_kinds = ["source"]

        if response.detections or annotated_image_url:
            image_kinds.append("detection")

        if response.crops:
            image_kinds.append("crop")

        if response.memory_items:
            image_kinds.append("memory")

        if response.matches:
            image_kinds.append("memory_match")

        return ImageFeatureDashboardItemDto(
            request_id=response.request_id,
            operation=operation,
            detector_model=response.detector_model,
            source_filename=response.source_filename,
            source_image_path=response.source_image_path,
            source_image_url=response.source_image_url
            or self._build_upload_url(response.source_image_path),
            file_size_bytes=response.file_size_bytes or 0,
            updated_at=self._utc_now_iso(),
            annotated_image_path=annotated_image_path,
            annotated_image_url=annotated_image_url,
            crop_image_urls=crop_image_urls,
            crop_image_paths=crop_image_paths,
            image_kinds=image_kinds,
            class_names=class_names,
            crop_count=response.total_crop_count or len(response.crops),
            detection_count=response.total_detection_count or len(response.detections),
            memory_item_count=response.total_memory_item_count or len(response.memory_items),
            best_confidence=self._best_confidence_from_items(
                response.detections,
                response.crops,
                response.memory_items,
            ),
        )

    def _build_lightweight_dashboard_item_from_source(
        self,
        source_path: Path,
    ) -> ImageFeatureDashboardItemDto:
        request_id = source_path.stem
        source_stat = source_path.stat()
        annotated_path = self.output_dir / f"{request_id}_annotated.jpg"
        preview_path = self.output_dir / f"{request_id}_source_preview.jpg"
        has_annotated_image = annotated_path.exists()
        image_kinds = ["source"]

        if has_annotated_image:
            image_kinds.append("detection")

        return ImageFeatureDashboardItemDto(
            request_id=request_id,
            source_filename=source_path.name,
            source_image_path=self._to_host_storage_path(source_path),
            source_image_url=(
                self._build_output_url(str(preview_path))
                if preview_path.exists()
                else self._build_upload_url(str(source_path))
            ),
            file_size_bytes=source_stat.st_size,
            updated_at=self._timestamp_to_iso(source_stat.st_mtime),
            annotated_image_path=(
                self._to_host_storage_path(annotated_path)
                if has_annotated_image
                else None
            ),
            annotated_image_url=(
                self._build_output_url(str(annotated_path))
                if has_annotated_image
                else None
            ),
            crop_image_urls=[],
            crop_image_paths=[],
            image_kinds=image_kinds,
            class_names=[],
            crop_count=0,
            detection_count=1 if has_annotated_image else 0,
            memory_item_count=0,
            best_confidence=None,
        )

    def _build_dashboard_item_from_source(
        self,
        source_path: Path,
        memory_summary: dict,
    ) -> ImageFeatureDashboardItemDto:
        request_id = source_path.stem
        source_stat = source_path.stat()
        annotated_path = self.output_dir / f"{request_id}_annotated.jpg"
        preview_path = self.output_dir / f"{request_id}_source_preview.jpg"
        crop_paths = list(self._iter_image_files(self.crop_dir / request_id, limit=200))
        non_whole_crop_paths = [
            path for path in crop_paths if path.stem.lower() != "whole_image"
        ]

        class_names = set(memory_summary.get("class_names", []))

        for crop_path in non_whole_crop_paths:
            class_name = self._class_name_from_crop_path(crop_path)

            if class_name:
                class_names.add(self._format_detection_class_name(class_name))

        memory_item_count = int(memory_summary.get("count", 0))
        detection_count = max(len(non_whole_crop_paths), memory_item_count)
        image_kinds = ["source"]

        if annotated_path.exists() or detection_count > 0:
            image_kinds.append("detection")

        if crop_paths:
            image_kinds.append("crop")

        if memory_item_count > 0:
            image_kinds.append("memory")

        return ImageFeatureDashboardItemDto(
            request_id=request_id,
            source_filename=source_path.name,
            source_image_path=self._to_host_storage_path(source_path),
            source_image_url=(
                self._build_output_url(str(preview_path))
                if preview_path.exists()
                else self._build_upload_url(str(source_path))
            ),
            file_size_bytes=source_stat.st_size,
            updated_at=self._timestamp_to_iso(source_stat.st_mtime),
            annotated_image_path=(
                self._to_host_storage_path(annotated_path)
                if annotated_path.exists()
                else None
            ),
            annotated_image_url=(
                self._build_output_url(str(annotated_path))
                if annotated_path.exists()
                else None
            ),
            crop_image_urls=[
                self._build_crop_url(str(crop_path), request_id)
                for crop_path in crop_paths
            ],
            crop_image_paths=[
                self._to_host_storage_path(crop_path) for crop_path in crop_paths
            ],
            image_kinds=image_kinds,
            class_names=sorted(class_names),
            crop_count=len(crop_paths),
            detection_count=detection_count,
            memory_item_count=memory_item_count,
            best_confidence=memory_summary.get("best_confidence"),
        )

    def _load_dashboard_history_items(self) -> list[ImageFeatureDashboardItemDto]:
        with self._history_lock:
            if not self.history_file.exists():
                return []

            try:
                with self.history_file.open("r", encoding="utf-8") as file:
                    data = json.load(file)
            except (json.JSONDecodeError, OSError):
                return []

        if not isinstance(data, list):
            return []

        items: list[ImageFeatureDashboardItemDto] = []

        for item in data:
            if not isinstance(item, dict):
                continue

            try:
                public_item = dict(item)
                if public_item.get("source_image_path"):
                    public_item["source_image_path"] = self._to_host_storage_path(
                        public_item["source_image_path"]
                    )
                if public_item.get("annotated_image_path"):
                    public_item["annotated_image_path"] = self._to_host_storage_path(
                        public_item["annotated_image_path"]
                    )
                public_item["crop_image_paths"] = [
                    self._to_host_storage_path(path)
                    for path in public_item.get("crop_image_paths", [])
                ]
                items.append(ImageFeatureDashboardItemDto(**public_item))
            except ValueError:
                continue

        return items

    def _merge_dashboard_items(
        self,
        existing_item: ImageFeatureDashboardItemDto | None,
        history_item: ImageFeatureDashboardItemDto,
    ) -> ImageFeatureDashboardItemDto:
        if existing_item is None:
            return history_item

        class_names = sorted(set(existing_item.class_names) | set(history_item.class_names))
        image_kinds = sorted(set(existing_item.image_kinds) | set(history_item.image_kinds))
        crop_image_urls = sorted(
            set(existing_item.crop_image_urls) | set(history_item.crop_image_urls)
        )
        crop_image_paths = sorted(
            set(existing_item.crop_image_paths) | set(history_item.crop_image_paths)
        )
        confidence_values = [
            value
            for value in [existing_item.best_confidence, history_item.best_confidence]
            if value is not None
        ]

        return ImageFeatureDashboardItemDto(
            request_id=history_item.request_id,
            operation=history_item.operation or existing_item.operation,
            detector_model=history_item.detector_model or existing_item.detector_model,
            source_filename=history_item.source_filename or existing_item.source_filename,
            source_image_path=existing_item.source_image_path or history_item.source_image_path,
            source_image_url=existing_item.source_image_url or history_item.source_image_url,
            file_size_bytes=max(
                existing_item.file_size_bytes,
                history_item.file_size_bytes,
            ),
            updated_at=max(existing_item.updated_at, history_item.updated_at),
            annotated_image_path=(
                existing_item.annotated_image_path
                or history_item.annotated_image_path
            ),
            annotated_image_url=(
                existing_item.annotated_image_url
                or history_item.annotated_image_url
            ),
            crop_image_urls=crop_image_urls,
            crop_image_paths=crop_image_paths,
            image_kinds=image_kinds,
            class_names=class_names,
            crop_count=max(existing_item.crop_count, history_item.crop_count),
            detection_count=max(
                existing_item.detection_count,
                history_item.detection_count,
            ),
            memory_item_count=max(
                existing_item.memory_item_count,
                history_item.memory_item_count,
            ),
            best_confidence=max(confidence_values) if confidence_values else None,
        )

    def _compact_dashboard_item_for_list(
        self,
        item: ImageFeatureDashboardItemDto,
    ) -> ImageFeatureDashboardItemDto:
        data = item.model_dump()
        data["crop_image_urls"] = []
        data["crop_image_paths"] = []
        return ImageFeatureDashboardItemDto(**data)

    def _build_memory_summary_by_request(self) -> dict[str, dict]:
        summary_by_request: dict[str, dict] = {}

        for item in self._load_memory_items():
            request_id = item.get("source_request_id")

            if not request_id:
                continue

            summary = summary_by_request.setdefault(
                str(request_id),
                {
                    "class_names": set(),
                    "count": 0,
                    "best_confidence": None,
                },
            )
            summary["count"] += 1

            class_name = item.get("class_name")

            if class_name:
                summary["class_names"].add(self._format_detection_class_name(str(class_name)))

            confidence = item.get("confidence")

            if isinstance(confidence, (int, float)):
                best_confidence = summary["best_confidence"]
                summary["best_confidence"] = (
                    float(confidence)
                    if best_confidence is None
                    else max(float(confidence), float(best_confidence))
                )

        for summary in summary_by_request.values():
            summary["class_names"] = sorted(summary["class_names"])

        return summary_by_request

    def _extract_dashboard_class_names(self, *item_groups: list[dict]) -> list[str]:
        class_names: set[str] = set()

        for items in item_groups:
            for item in items:
                class_name = item.get("class_name")

                if class_name:
                    class_names.add(self._format_detection_class_name(str(class_name)))

        return sorted(class_names)

    def _best_confidence_from_items(self, *item_groups: list[dict]) -> float | None:
        confidences: list[float] = []

        for items in item_groups:
            for item in items:
                confidence = item.get("confidence")

                if isinstance(confidence, (int, float)):
                    confidences.append(float(confidence))

        return max(confidences) if confidences else None

    def _iter_image_files(self, directory: Path, limit: int | None = None) -> list[Path]:
        if not directory.exists() or not directory.is_dir():
            return []

        image_paths = sorted(
            [
                path
                for path in directory.iterdir()
                if path.is_file()
                and path.suffix.lower() in ImageFileValidator.ALLOWED_EXTENSIONS
            ],
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

        if limit is None:
            return image_paths

        return image_paths[: max(1, limit)]

    def _class_name_from_crop_path(self, crop_path: Path) -> str | None:
        parts = crop_path.stem.split("_", 2)

        if len(parts) < 3:
            return None

        return parts[2]

    def _utc_now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _timestamp_to_iso(self, timestamp: float) -> str:
        return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()

    def _cosine_similarity(
        self,
        vector_a: list[float],
        vector_b: list[float],
    ) -> float:
        a = np.array(vector_a, dtype=np.float32)
        b = np.array(vector_b, dtype=np.float32)

        denominator = float(np.linalg.norm(a) * np.linalg.norm(b))

        if denominator == 0:
            return 0.0

        value = float(np.dot(a, b) / denominator)

        if math.isnan(value):
            return 0.0

        return round(value, 6)

    def _build_upload_url(self, path: str) -> str:
        filename = self._filename_from_path(path)
        return f"/api/v1/media/image-upload/{filename}"

    def _build_output_url(self, path: str) -> str:
        filename = self._filename_from_path(path)
        return f"/api/v1/media/image-output/{filename}"

    def _build_crop_url(self, path: str, request_id: str) -> str:
        filename = self._filename_from_path(path)
        return f"/api/v1/media/image-crop/{request_id}/{filename}"

    def _filename_from_path(self, path: str) -> str:
        # PureWindowsPath also works when the API itself runs in a Linux container.
        normalized = str(path)
        if "\\" in normalized or (len(normalized) > 1 and normalized[1] == ":"):
            return PureWindowsPath(normalized).name
        return Path(normalized).name

    def _to_host_storage_path(self, path: str | Path) -> str:
        raw_path = str(path)
        if os.name != "nt" and (
            "\\" in raw_path or (len(raw_path) > 1 and raw_path[1] == ":")
        ):
            return raw_path
        path_value = Path(path)
        try:
            internal_path = (
                path_value.resolve()
                if path_value.is_absolute()
                else (self.storage_root / path_value).resolve()
            )
            relative_path = internal_path.relative_to(self.storage_root)
        except (OSError, ValueError):
            # Already-public/legacy paths are returned untouched.
            return str(path)

        host_root = self.host_storage_root
        if "\\" in host_root or (len(host_root) > 1 and host_root[1] == ":"):
            return str(PureWindowsPath(host_root).joinpath(*relative_path.parts))
        return str(Path(host_root).joinpath(*relative_path.parts))

    def _publicize_result_item(self, item: dict) -> dict:
        public_item = dict(item)
        for key in (
            "source_image_path",
            "crop_path",
            "annotated_image_path",
            "output_path",
        ):
            if public_item.get(key):
                public_item[key] = self._to_host_storage_path(public_item[key])
        return public_item

    def _is_model_loaded(self, detector_model: str = "yolo") -> bool:
        detector_model = self._normalize_detector_model(detector_model)
        detector = self._detectors[detector_model]
        if detector_model == "skydet" and getattr(detector, "_load_attempted", False):
            return getattr(detector, "_model", None) is not None
        if detector_model == "yolo" and self._detector_net is not None:
            return True

        model_path = Path(getattr(detector, "_model_path", self.yolo_model_path))

        if not model_path.is_absolute():
            model_path = Path.cwd() / model_path

        return model_path.resolve().exists()

    def _build_response(
        self,
        context: dict,
        message: str,
        detections: list[dict] | None = None,
        crops: list[dict] | None = None,
        memory_items: list[dict] | None = None,
        matches: list[dict] | None = None,
    ) -> ImageFeatureResponseDto:
        detections = detections or []
        crops = crops or []
        memory_items = memory_items or []
        matches = matches or []
        total_output_count = len(detections) + len(crops) + len(memory_items) + len(matches)
        detector_model = context["detector_model"]
        detector_warning = context.get("detector_warning")
        annotated_image_path = next(
            (
                item.get("annotated_image_path")
                for item in detections
                if item.get("annotated_image_path")
            ),
            None,
        )
        annotated_image_url = next(
            (
                item.get("annotated_image_url")
                for item in detections
                if item.get("annotated_image_url")
            ),
            None,
        )
        public_detections = [self._publicize_result_item(item) for item in detections]
        public_crops = [self._publicize_result_item(item) for item in crops]
        public_memory_items = [self._publicize_result_item(item) for item in memory_items]
        public_matches = [self._publicize_result_item(item) for item in matches]

        return ImageFeatureResponseDto(
            request_id=context["request_id"],
            image_id=context["request_id"],
            status="completed",
            message=message,
            source_filename=context["source_filename"],
            source_image_path=self._to_host_storage_path(context["source_image_path"]),
            source_image_url=context.get("source_image_url")
            or self._build_upload_url(context["source_image_path"]),
            file_size_bytes=context.get("file_size_bytes"),
            content_type=context.get("content_type"),
            detector_model=detector_model,
            annotated_image_path=(
                self._to_host_storage_path(annotated_image_path)
                if annotated_image_path
                else None
            ),
            annotated_image_url=annotated_image_url,
            width=context["width"],
            height=context["height"],
            source_width=context.get("source_width", context["width"]),
            source_height=context.get("source_height", context["height"]),
            inference_scaled=bool(context.get("inference_scaled", False)),
            processed_image_count=1,
            total_detection_count=len(detections),
            total_crop_count=len(crops),
            total_memory_item_count=len(memory_items),
            total_match_count=len(matches),
            total_output_count=total_output_count,
            model_loaded=(
                self._is_model_loaded(detector_model)
                and not bool(detector_warning)
            ),
            detector_warning=detector_warning,
            detections=public_detections,
            crops=public_crops,
            memory_items=public_memory_items,
            matches=public_matches,
        )
