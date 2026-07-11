from enum import StrEnum


class ModelStatus(StrEnum):
    DRAFT = "draft"
    TRAINING = "training"
    VALIDATED = "validated"
    ACTIVE = "active"
    ARCHIVED = "archived"
    FAILED = "failed"
