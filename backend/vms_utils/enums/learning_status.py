from enum import StrEnum


class LearningStatus(StrEnum):
    AUTO_LABELED = "auto_labeled"
    REVIEW_REQUIRED = "review_required"
    ADMIN_APPROVED = "admin_approved"
    REJECTED = "rejected"
    EXPORTED = "exported"
    USED_FOR_TRAINING = "used_for_training"
