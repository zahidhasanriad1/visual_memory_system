from typing import Any, Generic, TypeVar
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel

T = TypeVar("T")


def _remove_internal_locations(value):
    if isinstance(value, dict):
        return {
            key: _remove_internal_locations(item)
            for key, item in value.items()
            if not key.endswith("_path") and not key.endswith("_paths")
        }
    if isinstance(value, list):
        return [_remove_internal_locations(item) for item in value]
    return value


class ApiResponse(BaseModel, Generic[T]):
    """Unified API response envelope."""

    success: bool
    message: str
    data: T | None = None

    def to_response(self, status_code: int = 200) -> ORJSONResponse:
        content = _remove_internal_locations(self.model_dump(mode="json"))
        return ORJSONResponse(status_code=status_code, content=content)
