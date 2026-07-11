from abc import ABC, abstractmethod
from fastapi import UploadFile

from vms_models.dtos.image_features.image_feature_dashboard_response_dto import (
    ImageFeatureDashboardResponseDto,
)
from vms_models.dtos.image_features.image_feature_response_dto import ImageFeatureResponseDto


class IImageFeatureService(ABC):
    """
    Contract for image feature operations.
    Controller depends on this interface, not implementation.
    """

    @abstractmethod
    async def test_crops(
        self,
        file: UploadFile,
        crop_padding_pixels: int,
        detector_model: str = "yolo",
    ) -> ImageFeatureResponseDto:
        pass

    @abstractmethod
    async def test_detections(
        self,
        file: UploadFile,
        confidence_threshold: float,
        iou_threshold: float,
        detector_model: str = "yolo",
    ) -> ImageFeatureResponseDto:
        pass

    @abstractmethod
    async def test_detection_crops(
        self,
        file: UploadFile,
        confidence_threshold: float,
        iou_threshold: float,
        crop_padding_pixels: int,
        detector_model: str = "yolo",
    ) -> ImageFeatureResponseDto:
        pass

    @abstractmethod
    async def ingest_image_to_memory(
        self,
        file: UploadFile,
        confidence_threshold: float,
        iou_threshold: float,
        crop_padding_pixels: int,
        detector_model: str = "yolo",
    ) -> ImageFeatureResponseDto:
        pass

    @abstractmethod
    async def search_image_memory(
        self,
        file: UploadFile,
        top_k: int,
        detector_model: str = "yolo",
    ) -> ImageFeatureResponseDto:
        pass

    @abstractmethod
    def list_dashboard_images(
        self,
        limit: int,
    ) -> ImageFeatureDashboardResponseDto:
        pass
