from __future__ import annotations

from threading import Lock
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession
from vms_services.interfaces.i_image_feature_service import IImageFeatureService
from vms_services.interfaces.i_cloud_ai_agent_service import ICloudAiAgentService
from vms_data_access.repositories.user_repository import UserRepository
from vms_services.interfaces.i_auth_service import IAuthService

if TYPE_CHECKING:
    from vms_services.services.adaptive_learning_service import AdaptiveLearningService
    from vms_services.services.annotation_service import AnnotationService
    from vms_services.services.auth_service import AuthService
    from vms_services.services.cloud_ai_agent_service import CloudAiAgentService
    from vms_services.services.image_feature_service import ImageFeatureService
    from vms_services.services.media_service import MediaService
    from vms_services.services.model_registry_service import ModelRegistryService
    from vms_services.services.training_service import TrainingService
    from vms_services.services.video_memory_service import VideoMemoryService


_user_repository_singleton: UserRepository | None = None
_auth_service_singleton: AuthService | None = None
_cloud_ai_agent_service_singleton: CloudAiAgentService | None = None
_image_feature_service_singleton: ImageFeatureService | None = None
_user_repository_lock = Lock()
_auth_service_lock = Lock()
_cloud_ai_agent_service_lock = Lock()
_image_feature_service_lock = Lock()


def get_cloud_ai_agent_service() -> ICloudAiAgentService:
    global _cloud_ai_agent_service_singleton

    if _cloud_ai_agent_service_singleton is None:
        with _cloud_ai_agent_service_lock:
            if _cloud_ai_agent_service_singleton is None:
                from vms_services.services.cloud_ai_agent_service import (
                    CloudAiAgentService,
                )

                _cloud_ai_agent_service_singleton = CloudAiAgentService()

    return _cloud_ai_agent_service_singleton


class ServiceProvider:
    """Request-scoped, lazy service factory."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._auth = None
        self._video_memory = None
        self._adaptive_learning = None
        self._annotation = None
        self._model_registry = None
        self._training = None
        self._media = None

    @property
    def auth(self) -> AuthService:
        if self._auth is None:
            from vms_services.services.auth_service import AuthService

            self._auth = AuthService(user_repository=UserRepository())
        return self._auth

    @property
    def video_memory(self) -> VideoMemoryService:
        if self._video_memory is None:
            # This service imports detector/Torch stacks. Only video routes pay
            # that cost; annotation/model/training routes stay lightweight.
            from vms_services.services.video_memory_service import VideoMemoryService

            self._video_memory = VideoMemoryService(self._session)
        return self._video_memory

    @property
    def adaptive_learning(self) -> AdaptiveLearningService:
        if self._adaptive_learning is None:
            from vms_services.services.adaptive_learning_service import (
                AdaptiveLearningService,
            )

            self._adaptive_learning = AdaptiveLearningService(self._session)
        return self._adaptive_learning

    @property
    def annotation(self) -> AnnotationService:
        if self._annotation is None:
            from vms_services.services.annotation_service import AnnotationService

            self._annotation = AnnotationService(self._session)
        return self._annotation

    @property
    def model_registry(self) -> ModelRegistryService:
        if self._model_registry is None:
            from vms_services.services.model_registry_service import ModelRegistryService

            self._model_registry = ModelRegistryService(self._session)
        return self._model_registry

    @property
    def training(self) -> TrainingService:
        if self._training is None:
            from vms_services.services.training_service import TrainingService

            self._training = TrainingService(self._session)
        return self._training

    @property
    def media(self) -> MediaService:
        if self._media is None:
            from vms_services.services.media_service import MediaService

            self._media = MediaService()
        return self._media


def get_user_repository() -> UserRepository:
    global _user_repository_singleton

    if _user_repository_singleton is None:
        with _user_repository_lock:
            if _user_repository_singleton is None:
                _user_repository_singleton = UserRepository()

    return _user_repository_singleton


def get_auth_service() -> IAuthService:
    global _auth_service_singleton

    if _auth_service_singleton is None:
        with _auth_service_lock:
            if _auth_service_singleton is None:
                from vms_services.services.auth_service import AuthService

                _auth_service_singleton = AuthService(
                    user_repository=get_user_repository(),
                )

    return _auth_service_singleton

def get_image_feature_service() -> IImageFeatureService:
    """
    Provides singleton image feature service through dependency injection.
    """

    global _image_feature_service_singleton

    if _image_feature_service_singleton is None:
        with _image_feature_service_lock:
            if _image_feature_service_singleton is None:
                # ImageFeatureService imports both detector stacks (including
                # Torch). The lock prevents concurrent cold requests from
                # constructing independent models and independent JSON locks.
                from vms_services.services.image_feature_service import (
                    ImageFeatureService,
                )

                _image_feature_service_singleton = ImageFeatureService()

    return _image_feature_service_singleton
