from dataclasses import dataclass
import uuid

@dataclass
class DetectedObject:
    detection_id: str
    class_id: int | None
    class_name: str
    confidence: float
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @classmethod
    def create(cls, class_id: int | None, class_name: str, confidence: float, x_min: float, y_min: float, x_max: float, y_max: float):
        return cls(uuid.uuid4().hex, class_id, class_name, confidence, x_min, y_min, x_max, y_max)
