from sqlalchemy.ext.asyncio import AsyncSession
from vms_data_access.repositories.user_repository import UserRepository
from vms_data_access.repositories.video_repository import VideoRepository
from vms_data_access.repositories.video_job_repository import VideoJobRepository
from vms_data_access.repositories.video_frame_repository import VideoFrameRepository
from vms_data_access.repositories.tracked_object_repository import TrackedObjectRepository
from vms_data_access.repositories.visual_memory_repository import VisualMemoryRepository
from vms_data_access.repositories.adaptive_learning_item_repository import AdaptiveLearningItemRepository
from vms_data_access.repositories.annotation_project_repository import AnnotationProjectRepository
from vms_data_access.repositories.annotation_task_repository import AnnotationTaskRepository
from vms_data_access.repositories.annotation_object_repository import AnnotationObjectRepository
from vms_data_access.repositories.model_version_repository import ModelVersionRepository
from vms_data_access.repositories.training_job_repository import TrainingJobRepository
from vms_data_access.repositories.dataset_version_repository import DatasetVersionRepository

class RepositoryProvider:
    """Repository factory scoped to one SQLAlchemy session."""

    def __init__(self, session: AsyncSession) -> None:
        self.users = UserRepository()
        self.videos = VideoRepository(session)
        self.video_jobs = VideoJobRepository(session)
        self.video_frames = VideoFrameRepository(session)
        self.tracked_objects = TrackedObjectRepository(session)
        self.visual_memory = VisualMemoryRepository(session)
        self.adaptive_items = AdaptiveLearningItemRepository(session)
        self.annotation_projects = AnnotationProjectRepository(session)
        self.annotation_tasks = AnnotationTaskRepository(session)
        self.annotation_objects = AnnotationObjectRepository(session)
        self.model_versions = ModelVersionRepository(session)
        self.training_jobs = TrainingJobRepository(session)
        self.dataset_versions = DatasetVersionRepository(session)
