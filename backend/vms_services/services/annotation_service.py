from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from vms_domain.entities.annotation_project_entity import AnnotationProjectEntity
from vms_domain.entities.annotation_task_entity import AnnotationTaskEntity
from vms_domain.entities.annotation_object_entity import AnnotationObjectEntity
from vms_models.dtos.annotation.annotation_project_create_request_dto import AnnotationProjectCreateRequestDto
from vms_models.dtos.annotation.annotation_project_response_dto import AnnotationProjectResponseDto
from vms_models.dtos.annotation.annotation_task_create_request_dto import AnnotationTaskCreateRequestDto
from vms_models.dtos.annotation.annotation_task_response_dto import AnnotationTaskResponseDto
from vms_models.dtos.annotation.annotation_object_create_request_dto import AnnotationObjectCreateRequestDto
from vms_models.dtos.annotation.annotation_object_response_dto import AnnotationObjectResponseDto
from vms_api.appsettings import get_settings
from vms_utils.exceptions.app_exception import AppException

class AnnotationService:
    """CVAT/Roboflow-style annotation workflow service."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._storage_root = get_settings().storage_root.resolve()

    async def create_project_async(self, request: AnnotationProjectCreateRequestDto) -> AnnotationProjectResponseDto:
        entity = AnnotationProjectEntity(name=request.name, description=request.description)
        self._session.add(entity); await self._session.commit(); await self._session.refresh(entity)
        return self._project_response(entity)

    async def create_task_async(self, request: AnnotationTaskCreateRequestDto) -> AnnotationTaskResponseDto:
        entity = AnnotationTaskEntity(project_id=request.project_id, source_type=request.source_type, source_path=request.source_path, frame_number=request.frame_number)
        self._session.add(entity); await self._session.commit(); await self._session.refresh(entity)
        return self._task_response(entity)

    async def create_object_async(self, request: AnnotationObjectCreateRequestDto) -> AnnotationObjectResponseDto:
        task = await self._session.get(AnnotationTaskEntity, request.task_id)
        if not task:
            raise AppException("Annotation task not found.", status_code=404)

        label = "_".join(request.label.strip().lower().split())
        points = [[float(point[0]), float(point[1])] for point in request.points if len(point) >= 2]
        if request.geometry_type == "polygon":
            if len(points) < 3:
                raise AppException("Polygon requires at least three points.", status_code=422)
            xs = [point[0] for point in points]
            ys = [point[1] for point in points]
            x_min, y_min, x_max, y_max = min(xs), min(ys), max(xs), max(ys)
        else:
            x_min = min(request.x_min, request.x_max)
            y_min = min(request.y_min, request.y_max)
            x_max = max(request.x_min, request.x_max)
            y_max = max(request.y_min, request.y_max)
            if x_max <= x_min or y_max <= y_min:
                raise AppException("Bounding box must have a positive area.", status_code=422)
            points = []

        entity = AnnotationObjectEntity(
            task_id=request.task_id,
            label=label,
            x_min=max(0.0, x_min),
            y_min=max(0.0, y_min),
            x_max=max(0.0, x_max),
            y_max=max(0.0, y_max),
            geometry_type=request.geometry_type,
            points=points,
            status="pending",
        )
        self._session.add(entity); await self._session.commit(); await self._session.refresh(entity)
        return self._object_response(entity)

    async def list_labels_async(self) -> list[str]:
        result = await self._session.execute(
            select(AnnotationObjectEntity.label).distinct().order_by(AnnotationObjectEntity.label)
        )
        learned = [str(label) for label in result.scalars().all() if label]
        return list(dict.fromkeys(["airplane", "boat", "car", "ship", *learned]))

    async def update_object_status_async(
        self,
        object_id: str,
        status: str,
    ) -> AnnotationObjectResponseDto:
        entity = await self._session.get(AnnotationObjectEntity, object_id)
        if not entity:
            raise AppException("Annotation object not found.", status_code=404)
        entity.status = status
        await self._session.commit()
        await self._session.refresh(entity)
        return self._object_response(entity)

    async def delete_object_async(self, object_id: str) -> None:
        result = await self._session.execute(
            delete(AnnotationObjectEntity).where(AnnotationObjectEntity.id == object_id)
        )
        if not result.rowcount:
            raise AppException("Annotation object not found.", status_code=404)
        await self._session.commit()

    async def list_projects_async(self) -> list[AnnotationProjectResponseDto]:
        result = await self._session.execute(select(AnnotationProjectEntity))
        projects = result.scalars().all()
        return [self._project_response(project) for project in projects]

    async def list_tasks_async(self, project_id: str | None = None) -> list[AnnotationTaskResponseDto]:
        statement = select(AnnotationTaskEntity)

        if project_id:
            statement = statement.where(AnnotationTaskEntity.project_id == project_id)

        result = await self._session.execute(statement)
        tasks = result.scalars().all()
        return [self._task_response(task) for task in tasks]

    async def list_objects_async(self, task_id: str | None = None) -> list[AnnotationObjectResponseDto]:
        statement = select(AnnotationObjectEntity)

        if task_id:
            statement = statement.where(AnnotationObjectEntity.task_id == task_id)

        result = await self._session.execute(statement)
        objects = result.scalars().all()
        return [self._object_response(item) for item in objects]

    def _project_response(self, entity: AnnotationProjectEntity) -> AnnotationProjectResponseDto:
        return AnnotationProjectResponseDto(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            status=entity.status,
        )

    def _task_response(self, entity: AnnotationTaskEntity) -> AnnotationTaskResponseDto:
        return AnnotationTaskResponseDto(
            id=entity.id,
            project_id=entity.project_id,
            source_type=entity.source_type,
            source_path=None,
            source_url=self._source_url(entity.source_path),
            status=entity.status,
            frame_number=entity.frame_number,
        )

    def _object_response(self, entity: AnnotationObjectEntity) -> AnnotationObjectResponseDto:
        return AnnotationObjectResponseDto(
            id=entity.id,
            task_id=entity.task_id,
            label=entity.label,
            x_min=entity.x_min,
            y_min=entity.y_min,
            x_max=entity.x_max,
            y_max=entity.y_max,
            geometry_type=entity.geometry_type or "box",
            points=entity.points or [],
            status=entity.status,
        )

    def _source_url(self, source_path: str) -> str | None:
        try:
            path = Path(source_path).resolve()
        except Exception:
            return None

        upload_dir = self._storage_root / "uploads" / "images"
        output_dir = self._storage_root / "outputs" / "image_features"
        crop_dir = self._storage_root / "crops" / "images"

        if path.is_file() and str(path).startswith(str(upload_dir)):
            preview_path = output_dir / f"{path.stem}_source_preview.jpg"
            if preview_path.exists():
                return f"/api/v1/media/image-output/{preview_path.name}"
            return f"/api/v1/media/image-upload/{path.name}"

        if path.is_file() and str(path).startswith(str(output_dir)):
            return f"/api/v1/media/image-output/{path.name}"

        if path.is_file() and str(path).startswith(str(crop_dir)) and path.parent != crop_dir:
            return f"/api/v1/media/image-crop/{path.parent.name}/{path.name}"

        return None
