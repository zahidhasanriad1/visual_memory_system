import asyncio
import json
import os
import random
import shutil
import uuid
from pathlib import Path

import cv2
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from vms_api.appsettings import get_settings
from vms_domain.entities.annotation_object_entity import AnnotationObjectEntity
from vms_domain.entities.annotation_project_entity import AnnotationProjectEntity
from vms_domain.entities.annotation_task_entity import AnnotationTaskEntity
from vms_domain.entities.dataset_version_entity import DatasetVersionEntity
from vms_domain.entities.model_version_entity import ModelVersionEntity
from vms_domain.entities.training_job_entity import TrainingJobEntity
from vms_models.dtos.training.custom_dataset_create_request_dto import (
    CustomDatasetCreateRequestDto,
)
from vms_models.dtos.training.custom_dataset_response_dto import (
    CustomDatasetResponseDto,
)
from vms_models.dtos.training.training_job_response_dto import TrainingJobResponseDto
from vms_models.dtos.training.training_job_start_request_dto import (
    TrainingJobStartRequestDto,
)
from vms_utils.exceptions.app_exception import AppException


async def run_training_job_background(job_id: str) -> None:
    """Run a long-lived job with its own database session.

    Request-scoped sessions may be closed as soon as the HTTP response is sent,
    so background training must never retain the controller's session.
    """

    from vms_domain.database.session import AsyncSessionFactory

    async with AsyncSessionFactory() as session:
        await TrainingService(session).run_training_job_async(job_id)


class TrainingService:
    """Annotation-to-dataset-to-versioned-model training orchestration."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._settings = get_settings()
        self._custom_dataset_root = self._settings.dataset_dir / "custom_training"
        self._training_root = self._settings.output_dir / "training_runs"
        self._custom_dataset_root.mkdir(parents=True, exist_ok=True)
        self._training_root.mkdir(parents=True, exist_ok=True)

    async def create_dataset_from_annotations_async(
        self,
        request: CustomDatasetCreateRequestDto,
    ) -> CustomDatasetResponseDto:
        project = await self._session.get(AnnotationProjectEntity, request.project_id)
        if not project:
            raise AppException("Annotation project not found.", status_code=404)

        task_result = await self._session.execute(
            select(AnnotationTaskEntity).where(
                AnnotationTaskEntity.project_id == request.project_id
            )
        )
        tasks = list(task_result.scalars().all())
        if not tasks:
            raise AppException("The project has no annotation tasks.", status_code=422)

        task_ids = [task.id for task in tasks]
        object_statement = select(AnnotationObjectEntity).where(
            AnnotationObjectEntity.task_id.in_(task_ids)
        )
        if not request.include_pending:
            object_statement = object_statement.where(
                AnnotationObjectEntity.status == "approved"
            )
        object_result = await self._session.execute(object_statement)
        objects = list(object_result.scalars().all())
        if not objects:
            raise AppException(
                "No approved annotations are available for training.",
                status_code=422,
            )

        objects_by_task: dict[str, list[AnnotationObjectEntity]] = {}
        for item in objects:
            objects_by_task.setdefault(item.task_id, []).append(item)
        usable_tasks = [task for task in tasks if objects_by_task.get(task.id)]
        class_names = sorted({item.label for item in objects})

        dataset_id = str(uuid.uuid4())
        dataset_root = self._custom_dataset_root / dataset_id
        random.Random(dataset_id).shuffle(usable_tasks)
        train_count = max(1, int(len(usable_tasks) * request.train_split))
        if len(usable_tasks) > 1:
            train_count = min(train_count, len(usable_tasks) - 1)

        exported_images = 0
        exported_annotations = 0
        coco_annotations: list[dict] = []
        coco_images: list[dict] = []

        for index, task in enumerate(usable_tasks):
            split = "train" if index < train_count else "val"
            source_path = self._training_source_path(Path(task.source_path))
            image = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
            if image is None:
                continue
            height, width = image.shape[:2]
            image_dir = dataset_root / "images" / split
            label_dir = dataset_root / "labels" / split
            image_dir.mkdir(parents=True, exist_ok=True)
            label_dir.mkdir(parents=True, exist_ok=True)
            image_name = f"{task.id}.jpg"
            target_image = image_dir / image_name
            if not cv2.imwrite(str(target_image), image, [int(cv2.IMWRITE_JPEG_QUALITY), 92]):
                continue

            label_lines: list[str] = []
            image_objects = objects_by_task[task.id]
            for annotation in image_objects:
                class_id = class_names.index(annotation.label)
                x_min = max(0.0, min(float(width), annotation.x_min))
                y_min = max(0.0, min(float(height), annotation.y_min))
                x_max = max(0.0, min(float(width), annotation.x_max))
                y_max = max(0.0, min(float(height), annotation.y_max))
                box_width = max(1.0, x_max - x_min)
                box_height = max(1.0, y_max - y_min)
                center_x = x_min + (box_width / 2)
                center_y = y_min + (box_height / 2)
                label_lines.append(
                    f"{class_id} {center_x / width:.8f} {center_y / height:.8f} "
                    f"{box_width / width:.8f} {box_height / height:.8f}"
                )
                coco_annotations.append(
                    {
                        "id": annotation.id,
                        "image_id": task.id,
                        "category_id": class_id,
                        "bbox": [x_min, y_min, box_width, box_height],
                        "segmentation": [
                            [coordinate for point in (annotation.points or []) for coordinate in point]
                        ] if annotation.geometry_type == "polygon" else [],
                        "area": box_width * box_height,
                        "iscrowd": 0,
                    }
                )
            (label_dir / f"{task.id}.txt").write_text(
                "\n".join(label_lines),
                encoding="utf-8",
            )
            coco_images.append(
                {"id": task.id, "file_name": f"images/{split}/{image_name}", "width": width, "height": height}
            )
            exported_images += 1
            exported_annotations += len(label_lines)

        if not exported_images:
            raise AppException("No readable task images could be exported.", status_code=422)

        data_yaml = dataset_root / "data.yaml"
        yaml_lines = [
            f"path: {dataset_root.as_posix()}",
            "train: images/train",
            "val: images/val" if (dataset_root / "images" / "val").exists() else "val: images/train",
            "names:",
            *[f"  {index}: {json.dumps(name)}" for index, name in enumerate(class_names)],
        ]
        data_yaml.write_text("\n".join(yaml_lines) + "\n", encoding="utf-8")
        (dataset_root / "annotations.json").write_text(
            json.dumps(
                {
                    "images": coco_images,
                    "annotations": coco_annotations,
                    "categories": [
                        {"id": index, "name": name}
                        for index, name in enumerate(class_names)
                    ],
                },
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )

        quality_score = min(100, round((exported_annotations / max(1, len(objects))) * 100))
        entity = DatasetVersionEntity(
            id=dataset_id,
            name=request.name.strip(),
            version=request.version.strip(),
            export_path=str(dataset_root),
            class_names=class_names,
            image_count=exported_images,
            annotation_count=exported_annotations,
            quality_score=quality_score,
        )
        self._session.add(entity)
        await self._session.commit()
        return self._dataset_response(entity)

    async def list_datasets_async(self) -> list[CustomDatasetResponseDto]:
        result = await self._session.execute(
            select(DatasetVersionEntity).order_by(DatasetVersionEntity.created_at.desc())
        )
        return [self._dataset_response(item) for item in result.scalars().all()]

    async def start_training_async(
        self,
        request: TrainingJobStartRequestDto,
    ) -> TrainingJobResponseDto:
        detector_model = request.detector_model.strip().lower()
        if detector_model not in {"yolo", "skydet"}:
            raise AppException("Detector must be 'yolo' or 'skydet'.", status_code=422)
        dataset = await self._session.get(DatasetVersionEntity, request.dataset_version_id)
        if not dataset or not dataset.export_path:
            raise AppException("Training dataset was not found.", status_code=404)

        entity = TrainingJobEntity(
            id=uuid.uuid4().hex,
            dataset_version_id=request.dataset_version_id,
            status="queued",
            progress_percent=0.0,
            metrics={
                "detector_model": detector_model,
                "epochs": request.epochs,
                "image_size": request.image_size,
                "batch_size": request.batch_size,
                "base_model_id": request.base_model_id,
                "class_names": dataset.class_names,
            },
        )
        self._session.add(entity)
        await self._session.commit()
        return self._job_response(entity, "Training job queued for the managed worker.")

    async def list_training_jobs_async(self) -> list[TrainingJobResponseDto]:
        result = await self._session.execute(
            select(TrainingJobEntity).order_by(TrainingJobEntity.created_at.desc()).limit(50)
        )
        return [self._job_response(item) for item in result.scalars().all()]

    async def get_training_job_async(self, job_id: str) -> TrainingJobResponseDto:
        entity = await self._session.get(TrainingJobEntity, job_id)
        if not entity:
            raise AppException("Training job not found.", status_code=404)
        return self._job_response(entity)

    async def run_training_job_async(self, job_id: str) -> None:
        entity = await self._session.get(TrainingJobEntity, job_id)
        if not entity or entity.status not in {"queued", "failed"}:
            return
        dataset = await self._session.get(DatasetVersionEntity, entity.dataset_version_id)
        if not dataset or not dataset.export_path:
            entity.status = "failed"
            entity.error = "Training dataset is unavailable."
            await self._session.commit()
            return

        entity.status = "running"
        entity.progress_percent = 5.0
        await self._session.commit()
        detector_model = str(entity.metrics.get("detector_model", "yolo"))
        run_dir = self._training_root / entity.id
        run_dir.mkdir(parents=True, exist_ok=True)

        try:
            if detector_model == "yolo":
                artifact, metrics = await asyncio.to_thread(
                    self._execute_yolo_training,
                    entity,
                    dataset,
                    run_dir,
                )
                onnx_path = metrics.pop("onnx_path", None)
            else:
                artifact, metrics = await asyncio.to_thread(
                    self._execute_skydet_training,
                    entity,
                    dataset,
                    run_dir,
                )
                onnx_path = None

            entity.output_model_path = str(artifact)
            entity.status = "completed"
            entity.progress_percent = 100.0
            entity.metrics = {**entity.metrics, **metrics}
            await self._register_trained_model(entity, dataset, artifact, onnx_path)
            await self._session.commit()
        except Exception as error:
            entity.status = "failed"
            entity.error = str(error)
            entity.progress_percent = 100.0
            await self._session.commit()

    def _execute_yolo_training(
        self,
        entity: TrainingJobEntity,
        dataset: DatasetVersionEntity,
        run_dir: Path,
    ) -> tuple[Path, dict]:
        from ultralytics import YOLO

        base_model = os.getenv("YOLO_TRAIN_BASE_MODEL", "yolo11n.pt")
        model = YOLO(base_model)
        results = model.train(
            data=str(Path(dataset.export_path) / "data.yaml"),
            epochs=int(entity.metrics["epochs"]),
            imgsz=int(entity.metrics["image_size"]),
            batch=int(entity.metrics["batch_size"]),
            project=str(run_dir.parent),
            name=run_dir.name,
            exist_ok=True,
            verbose=False,
        )
        best_path = Path(results.save_dir) / "weights" / "best.pt"
        if not best_path.exists():
            raise RuntimeError("YOLO training completed without a best.pt artifact.")
        trained = YOLO(str(best_path))
        exported = trained.export(format="onnx", imgsz=int(entity.metrics["image_size"]))
        metrics = {"onnx_path": str(exported), "training_backend": "ultralytics"}
        return best_path, metrics

    def _execute_skydet_training(
        self,
        entity: TrainingJobEntity,
        dataset: DatasetVersionEntity,
        run_dir: Path,
    ) -> tuple[Path, dict]:
        from vms_utils.ai.skydet_training import train_skydet

        return train_skydet(
            data_yaml=Path(dataset.export_path) / "data.yaml",
            output_dir=run_dir,
            class_names=list(dataset.class_names),
            epochs=int(entity.metrics["epochs"]),
            image_size=int(entity.metrics["image_size"]),
            batch_size=int(entity.metrics["batch_size"]),
            base_checkpoint=self._settings.skydet_model_path,
        )

    async def _register_trained_model(
        self,
        job: TrainingJobEntity,
        dataset: DatasetVersionEntity,
        artifact: Path,
        onnx_path: str | None,
    ) -> None:
        detector_model = str(job.metrics["detector_model"])
        await self._session.execute(
            update(ModelVersionEntity)
            .where(ModelVersionEntity.model_type == detector_model)
            .values(status="archived")
        )
        model = ModelVersionEntity(
            model_name=f"custom-{detector_model}-{dataset.name}",
            model_type=detector_model,
            version=f"{dataset.version}-{job.id[:8]}",
            model_path=str(artifact),
            onnx_path=onnx_path,
            class_names=dataset.class_names,
            metrics=job.metrics,
            status="active",
        )
        self._session.add(model)

        activated_path = self._activate_artifact(
            detector_model=detector_model,
            artifact=artifact,
            onnx_path=onnx_path,
        )
        from vms_services import service_injection

        image_service = service_injection._image_feature_service_singleton
        if image_service is not None:
            image_service.reload_detector(
                detector_model=detector_model,
                model_path=activated_path,
                class_names=list(dataset.class_names),
            )

    def _activate_artifact(
        self,
        detector_model: str,
        artifact: Path,
        onnx_path: str | None,
    ) -> Path:
        configured_path = (
            Path(self._settings.skydet_model_path)
            if detector_model == "skydet"
            else Path(self._settings.yolo_model_path)
        )
        if not configured_path.is_absolute():
            configured_path = (Path.cwd() / configured_path).resolve()
        source_path = artifact if detector_model == "skydet" else Path(onnx_path or "")
        if not source_path.exists():
            raise RuntimeError(f"Activated {detector_model} artifact is missing.")
        configured_path.parent.mkdir(parents=True, exist_ok=True)
        if source_path.resolve() != configured_path.resolve():
            shutil.copy2(source_path, configured_path)
        return configured_path

    def _training_source_path(self, source_path: Path) -> Path:
        preview = self._settings.output_dir / "image_features" / f"{source_path.stem}_source_preview.jpg"
        return preview if preview.exists() else source_path

    def _dataset_response(self, entity: DatasetVersionEntity) -> CustomDatasetResponseDto:
        return CustomDatasetResponseDto(
            id=entity.id,
            name=entity.name,
            version=entity.version,
            class_names=entity.class_names or [],
            image_count=entity.image_count,
            annotation_count=entity.annotation_count,
            quality_score=entity.quality_score,
            ready_for_training=bool(entity.image_count and entity.annotation_count and entity.class_names),
        )

    def _job_response(
        self,
        entity: TrainingJobEntity,
        message: str | None = None,
    ) -> TrainingJobResponseDto:
        return TrainingJobResponseDto(
            job_id=entity.id,
            detector_model=str(entity.metrics.get("detector_model", "yolo")),
            status=entity.status,
            progress_percent=entity.progress_percent,
            message=message or entity.error or f"Training job is {entity.status}.",
            metrics=entity.metrics,
            output_model_path=entity.output_model_path,
        )
