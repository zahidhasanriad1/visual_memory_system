# Annotation, Dataset, And Training

## Annotation Flow

Endpoints:

- `GET /api/v1/annotation/projects`
- `POST /api/v1/annotation/projects`
- `GET /api/v1/annotation/tasks?project_id=...`
- `POST /api/v1/annotation/tasks`
- `GET /api/v1/annotation/objects?task_id=...`
- `POST /api/v1/annotation/objects`
- `GET /api/v1/annotation/labels`
- `PATCH /api/v1/annotation/objects/{object_id}/status`
- `DELETE /api/v1/annotation/objects/{object_id}`

Service: `backend/vms_services/services/annotation_service.py`.

Capabilities:

- Project create/list.
- Task create/list.
- Box and polygon annotation object create/list.
- Label normalization: lowercase words joined by `_`.
- Polygon requires at least 3 points.
- Box must have positive area.
- Status review values: `pending`, `approved`, `rejected`.
- Delete object.
- Dynamic label list combines defaults `airplane, boat, car, ship` with learned distinct labels.

Missing:

- No project/task update/delete endpoints.
- No backend auth/role enforcement for annotation routes.
- No optimistic versioning or audit trail writes.

## Dataset Export

Endpoint: `POST /api/v1/training-jobs/datasets/from-annotations`.
Service: `TrainingService.create_dataset_from_annotations_async`.

Input: `project_id`, `name`, `version`, `train_split`, `include_pending`.

Processing:

- Loads annotation project and tasks.
- Selects approved objects unless `include_pending=true`.
- Shuffles usable tasks with deterministic seed `dataset_id`.
- Writes train/val images as JPEG.
- Writes YOLO label txt files.
- Writes `data.yaml`.
- Writes `annotations.json` in COCO-like format with images, annotations, categories.
- Creates `DatasetVersionEntity`.

Output DTO: `id`, `name`, `version`, `class_names`, `image_count`, `annotation_count`, `quality_score`, `ready_for_training`.

Status: IMPLEMENTED BUT NOT RUNTIME-VERIFIED.

## Training Jobs

Endpoints:

- `GET /api/v1/training-jobs/datasets`
- `POST /api/v1/training-jobs/start`
- `GET /api/v1/training-jobs`
- `GET /api/v1/training-jobs/{job_id}`

Status transitions:

- `queued` at creation.
- `running` in background worker.
- `completed` after artifact and registry update.
- `failed` on exception.

YOLO training:

- Uses Ultralytics `YOLO`.
- Base model env: `YOLO_TRAIN_BASE_MODEL`, default `yolo11n.pt`.
- Exports ONNX after training.

SkyDet training:

- Calls `vms_utils.ai.skydet_training.train_skydet`.
- Uses custom Torch training loop.

Model registration:

- Completed training archives prior same-type models, inserts active `ModelVersionEntity`, copies artifact to configured active path, and reloads the singleton image service if present.

Status: IMPLEMENTED BUT NOT RUNTIME-VERIFIED.

Mocking:

- Training code is not mocked; it starts real Ultralytics/SkyDet training in background. Tests cover parts of custom training service behavior, not full training runs.
