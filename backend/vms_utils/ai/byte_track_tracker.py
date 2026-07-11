from dataclasses import dataclass
from vms_utils.ai.detected_object import DetectedObject

@dataclass
class TrackedDetection:
    track_id: str
    detection: DetectedObject

class ByteTrackTracker:
    """Lightweight ByteTrack-style two-stage IoU tracker."""

    def __init__(self, iou_threshold: float = 0.30, high_threshold: float = 0.50, low_threshold: float = 0.10, max_lost_frames: int = 30) -> None:
        self.iou_threshold = iou_threshold
        self.high_threshold = high_threshold
        self.low_threshold = low_threshold
        self.max_lost_frames = max_lost_frames
        self._tracks: dict[str, dict] = {}
        self._class_counters: dict[str, int] = {}

    def update(self, detections: list[DetectedObject]) -> list[TrackedDetection]:
        detections = [d for d in detections if d.confidence >= self.low_threshold]
        matches: list[TrackedDetection] = []
        used_track_ids: set[str] = set()
        used_detection_ids: set[str] = set()

        for stage in [lambda d: d.confidence >= self.high_threshold, lambda d: d.confidence < self.high_threshold]:
            candidates = [d for d in detections if stage(d) and d.detection_id not in used_detection_ids]
            pairs: list[tuple[float, str, DetectedObject]] = []
            for detection in candidates:
                for track_id, track in self._tracks.items():
                    if track_id in used_track_ids or track["class_name"] != detection.class_name:
                        continue
                    iou = self._iou(track["box"], [detection.x_min, detection.y_min, detection.x_max, detection.y_max])
                    if iou >= self.iou_threshold:
                        pairs.append((iou, track_id, detection))
            pairs.sort(reverse=True, key=lambda p: p[0])
            for _, track_id, detection in pairs:
                if track_id in used_track_ids or detection.detection_id in used_detection_ids:
                    continue
                self._tracks[track_id]["box"] = [detection.x_min, detection.y_min, detection.x_max, detection.y_max]
                self._tracks[track_id]["lost"] = 0
                self._tracks[track_id]["hits"] += 1
                used_track_ids.add(track_id)
                used_detection_ids.add(detection.detection_id)
                matches.append(TrackedDetection(track_id, detection))

        for detection in detections:
            if detection.confidence >= self.high_threshold and detection.detection_id not in used_detection_ids:
                track_id = self._new_track_id(detection.class_name)
                self._tracks[track_id] = {"class_name": detection.class_name, "box": [detection.x_min, detection.y_min, detection.x_max, detection.y_max], "lost": 0, "hits": 1}
                used_track_ids.add(track_id)
                matches.append(TrackedDetection(track_id, detection))

        for track_id in list(self._tracks.keys()):
            if track_id not in used_track_ids:
                self._tracks[track_id]["lost"] += 1
                if self._tracks[track_id]["lost"] > self.max_lost_frames:
                    self._tracks.pop(track_id, None)
        return matches

    def _new_track_id(self, class_name: str) -> str:
        key = class_name.lower().replace(" ", "_") or "object"
        self._class_counters[key] = self._class_counters.get(key, 0) + 1
        return f"{key}_track_{self._class_counters[key]:03d}"

    @staticmethod
    def _iou(a: list[float], b: list[float]) -> float:
        x1 = max(a[0], b[0]); y1 = max(a[1], b[1]); x2 = min(a[2], b[2]); y2 = min(a[3], b[3])
        inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
        area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
        area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
        union = area_a + area_b - inter
        return inter / union if union else 0.0
