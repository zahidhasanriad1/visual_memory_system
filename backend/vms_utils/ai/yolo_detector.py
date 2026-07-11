from pathlib import Path
from typing import Any
import cv2
import os
from vms_api.appsettings import get_settings
from vms_utils.ai.detected_object import DetectedObject

class YoloDetector:
    """YOLO adapter. If model is unavailable, returns no detections safely."""

    def __init__(self, model_path: Path | None = None) -> None:
        self._settings = get_settings()
        self._model_path = Path(model_path or self._settings.yolo_model_path)
        self._model: Any | None = None
        self._load_attempted = False
        self.load_error: str | None = None

    def _load_model(self) -> None:
        if self._load_attempted:
            return
        self._load_attempted = True
        model_path = self._model_path
        if not model_path.exists():
            self._model = None
            self.load_error = f"YOLO model not found: {model_path}"
            return
        try:
            ultralytics_config_dir = self._settings.log_dir / "ultralytics"
            ultralytics_config_dir.mkdir(parents=True, exist_ok=True)
            os.environ.setdefault("YOLO_CONFIG_DIR", str(ultralytics_config_dir))
            from ultralytics import YOLO
            self._model = YOLO(str(model_path))
            self.load_error = None
        except Exception as error:
            self._model = None
            self.load_error = str(error)

    def detect(self, frame, confidence_threshold: float, iou_threshold: float, max_detections: int) -> list[DetectedObject]:
        self._load_model()
        if self._model is None:
            return []
        results = self._model.predict(frame, conf=confidence_threshold, iou=iou_threshold, verbose=False, max_det=max_detections)
        detections: list[DetectedObject] = []
        for result in results:
            names = getattr(result, "names", {})
            for box in result.boxes:
                xyxy = box.xyxy[0].tolist()
                class_id = int(box.cls[0].item()) if box.cls is not None else None
                class_name = str(names.get(class_id, class_id or "object"))
                confidence = float(box.conf[0].item())
                detections.append(DetectedObject.create(class_id, class_name, confidence, *map(float, xyxy)))
        return detections
