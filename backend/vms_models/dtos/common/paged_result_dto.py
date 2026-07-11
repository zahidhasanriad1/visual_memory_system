from pydantic import BaseModel
from typing import Generic, TypeVar
T = TypeVar("T")
class PagedResultDto(BaseModel, Generic[T]):
    total_count: int
    limit: int
    offset: int
    items: list[T]
