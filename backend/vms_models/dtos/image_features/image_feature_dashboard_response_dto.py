from pydantic import BaseModel, Field

from vms_models.dtos.image_features.image_feature_dashboard_item_dto import (
    ImageFeatureDashboardItemDto,
)


class ImageFeatureDashboardResponseDto(BaseModel):
    total_count: int = 0
    source_image_count: int = 0
    annotated_image_count: int = 0
    crop_image_count: int = 0
    detection_count: int = 0
    memory_item_count: int = 0
    items: list[ImageFeatureDashboardItemDto] = Field(default_factory=list)
