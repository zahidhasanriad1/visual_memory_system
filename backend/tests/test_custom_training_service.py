from pathlib import Path

import cv2
import numpy as np
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from vms_domain.database.base import Base
from vms_domain.entities.annotation_object_entity import AnnotationObjectEntity
from vms_domain.entities.annotation_project_entity import AnnotationProjectEntity
from vms_domain.entities.annotation_task_entity import AnnotationTaskEntity
from vms_models.dtos.training.custom_dataset_create_request_dto import (
    CustomDatasetCreateRequestDto,
)
from vms_services.services.training_service import TrainingService


@pytest.mark.asyncio
async def test_approved_annotations_create_dynamic_class_dataset(tmp_path: Path) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    source_path = tmp_path / "source.jpg"
    assert cv2.imwrite(str(source_path), np.zeros((200, 300, 3), dtype=np.uint8))

    async with session_factory() as session:
        project = AnnotationProjectEntity(name="Custom vessels")
        session.add(project)
        await session.flush()
        task = AnnotationTaskEntity(
            project_id=project.id,
            source_type="image",
            source_path=str(source_path),
        )
        session.add(task)
        await session.flush()
        session.add_all(
            [
                AnnotationObjectEntity(
                    task_id=task.id,
                    label="fishing_vessel",
                    x_min=20,
                    y_min=30,
                    x_max=140,
                    y_max=120,
                    geometry_type="box",
                    points=[],
                    status="approved",
                ),
                AnnotationObjectEntity(
                    task_id=task.id,
                    label="harbor_crane",
                    x_min=160,
                    y_min=40,
                    x_max=260,
                    y_max=180,
                    geometry_type="polygon",
                    points=[[160, 40], [260, 40], [240, 180], [170, 160]],
                    status="approved",
                ),
            ]
        )
        await session.commit()

        service = TrainingService(session)
        service._custom_dataset_root = tmp_path / "datasets"
        result = await service.create_dataset_from_annotations_async(
            CustomDatasetCreateRequestDto(
                project_id=project.id,
                name="Port assets",
                version="v1",
            )
        )

        assert result.ready_for_training is True
        assert result.image_count == 1
        assert result.annotation_count == 2
        assert result.class_names == ["fishing_vessel", "harbor_crane"]
        dataset_root = service._custom_dataset_root / result.id
        assert (dataset_root / "data.yaml").is_file()
        assert (dataset_root / "annotations.json").is_file()
        label_text = next((dataset_root / "labels" / "train").glob("*.txt")).read_text()
        assert len(label_text.splitlines()) == 2

    await engine.dispose()
