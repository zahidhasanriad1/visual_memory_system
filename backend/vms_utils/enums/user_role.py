from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    ANNOTATOR = "annotator"
    USER = "user"
    VIEWER = "viewer"
