# API Request/Response Catalog

All registered endpoints are mounted under `API_PREFIX`, default `/api/v1`. Most endpoints return either an explicit dict or `ApiResponse(success, message, data).to_response()`. `ApiResponse.to_response()` removes public response keys ending in `_path` or `_paths`.

FastAPI OpenAPI generation succeeded. Registered path count: 38.

## Common Response Shapes

Application success envelope:

```json
{
  "success": true,
  "message": "Operation message.",
  "data": {}
}
```

Application error envelope from `ExceptionMiddleware` for `AppException`:

```json
{
  "success": false,
  "message": "Error message.",
  "data": {}
}
```

FastAPI `HTTPException` handlers are not normalized by the custom middleware and return:

```json
{
  "detail": {
    "message": "Error message."
  }
}
```

Validation error shape is FastAPI's `HTTPValidationError`.

## Endpoint Table

| Method | Path | Tag | Auth | Request | Success Data | Handler | Frontend caller | Status |
|---|---|---|---|---|---|---|---|---|
| GET | `/api/v1/health` | Health | none | none | `{system,status}` | `health_controller.health` | Docker healthcheck | IMPLEMENTED AND VERIFIED |
| POST | `/api/v1/auth/register` | Authentication | none | JSON `RegisterRequestDto` | `AuthResponseDto` | `auth_controller.register` | `AuthApiService.register` | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| POST | `/api/v1/auth/login/form` | Authentication | none | form `username`, `password` | `AuthResponseDto` | `auth_controller.login_form` | `AuthApiService.loginForm` | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| POST | `/api/v1/auth/logout` | Authentication | none | none | `null` | `auth_controller.logout` | `AuthApiService.logout` local only | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| GET | `/api/v1/auth/me` | Authentication | bearer header | header `authorization` | `UserProfileResponseDto` | `auth_controller.get_me` | `AuthApiService.me` | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| POST | `/api/v1/video-memory/jobs/ingest-video` | Video Memory | none | multipart video + settings | job id/status/message | `video_memory_controller.create_video_job` | `VideoMemoryService.createJob` | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| GET | `/api/v1/video-memory/jobs/{job_id}` | Video Memory | none | path `job_id` | job status | `get_job_status` | `VideoMemoryService.status` | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| GET | `/api/v1/video-memory/jobs/{job_id}/result` | Video Memory | none | path `job_id` | report JSON | `get_job_result` | `VideoMemoryService.result` | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| POST | `/api/v1/adaptive-learning/crop/analyze` | Adaptive Learning | none | multipart `image_file`, optional YOLO fields | `AdaptiveLearningResponseDto` | `adaptive_learning_controller.analyze_crop` | `AdaptiveReviewComponent` direct HTTP | PARTIALLY IMPLEMENTED |
| GET | `/api/v1/annotation/projects` | Annotation | none | none | list project DTOs | `annotation_controller.list_projects` | `AnnotationApiService.listProjects` | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| POST | `/api/v1/annotation/projects` | Annotation | none | JSON `AnnotationProjectCreateRequestDto` | project DTO | `create_project` | no core service method | IMPLEMENTED BUT FRONTEND GAP |
| GET | `/api/v1/annotation/tasks` | Annotation | none | query `project_id?` | list task DTOs | `list_tasks` | `AnnotationApiService.listTasks` | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| POST | `/api/v1/annotation/tasks` | Annotation | none | JSON `AnnotationTaskCreateRequestDto` | task DTO | `create_task` | no core service method | IMPLEMENTED BUT FRONTEND GAP |
| GET | `/api/v1/annotation/objects` | Annotation | none | query `task_id?` | list object DTOs | `list_objects` | `AnnotationApiService.listObjects` | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| POST | `/api/v1/annotation/objects` | Annotation | none | JSON `AnnotationObjectCreateRequestDto` | object DTO | `create_object` | `AnnotationApiService.createObject` | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| GET | `/api/v1/annotation/labels` | Annotation | none | none | string list | `list_labels` | `AnnotationApiService.listLabels` | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| PATCH | `/api/v1/annotation/objects/{object_id}/status` | Annotation | none | path + JSON `{status}` | object DTO | `update_object_status` | `AnnotationApiService.updateObjectStatus` | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| DELETE | `/api/v1/annotation/objects/{object_id}` | Annotation | none | path | 204 no body | `delete_object` | `AnnotationApiService.deleteObject` | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| POST | `/api/v1/model-registry/models` | Model Registry | none | JSON `ModelRegisterRequestDto` | model DTO | `register_model` | `ModelRegistryComponent` | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| GET | `/api/v1/model-registry/models` | Model Registry | none | none | model DTO list | `list_models` | `ModelRegistryComponent` | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| POST | `/api/v1/model-registry/models/{model_id}/activate` | Model Registry | none | path | model DTO | `activate_model` | `ModelRegistryComponent` | PARTIALLY IMPLEMENTED |
| POST | `/api/v1/training-jobs/datasets/from-annotations` | Custom Training | none | JSON `CustomDatasetCreateRequestDto` | dataset DTO | `create_dataset_from_annotations` | `CustomTrainingComponent` | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| GET | `/api/v1/training-jobs/datasets` | Custom Training | none | none | dataset DTO list | `list_training_datasets` | `CustomTrainingComponent` | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| POST | `/api/v1/training-jobs/start` | Custom Training | none | JSON `TrainingJobStartRequestDto` | job DTO | `start_training` | `CustomTrainingComponent`, `TrainingOrchestratorComponent` | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| GET | `/api/v1/training-jobs` | Custom Training | none | none | job DTO list | `list_training_jobs` | training pages | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| GET | `/api/v1/training-jobs/{job_id}` | Custom Training | none | path | job DTO | `get_training_job` | no direct service method found | IMPLEMENTED BUT FRONTEND GAP |
| GET | `/api/v1/media/video/{filename}` | Media | none | path filename | `FileResponse` | `media_controller.get_video` | report links | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| GET | `/api/v1/media/report/{filename}` | Media | none | path filename | `FileResponse` JSON | `media_controller.get_report` | report links | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| GET | `/api/v1/image-features/dashboard-images` | Image Features | none | query `limit=50`, 1..200 | dashboard DTO | `get_dashboard_images` | `ImageFeatureApiService.getDashboardImages` | IMPLEMENTED AND VERIFIED BY TESTS |
| POST | `/api/v1/crops/test-image` | Image Features | none | multipart `file`, `detector_model`, `crop_padding_pixels` | image feature DTO | `test_image_crop` | `ImageFeatureApiService.testImageCrop` | IMPLEMENTED AND VERIFIED BY TESTS |
| POST | `/api/v1/detections/test-image` | Image Features | none | multipart file + thresholds | image feature DTO | `test_image_detection` | `ImageFeatureApiService.testImageDetection` | IMPLEMENTED BUT MODEL RUNTIME NOT VERIFIED |
| POST | `/api/v1/detection-crops/test-image` | Image Features | none | multipart file + thresholds + padding | image feature DTO | `test_image_detection_crops` | `ImageFeatureApiService.testImageDetectionCrops` | IMPLEMENTED AND VERIFIED BY TESTS |
| POST | `/api/v1/object-memory/ingest-image` | Image Features | none | multipart file + thresholds + padding | memory items | `ingest_image_to_object_memory` | `ImageFeatureApiService.ingestImageToMemory` | IMPLEMENTED AND VERIFIED BY TESTS |
| POST | `/api/v1/object-memory/search-image` | Image Features | none | multipart `file`, `detector_model`, `top_k` | matches | `search_object_memory_by_image` | `ImageFeatureApiService.searchImageMemory` | IMPLEMENTED AND VERIFIED BY TESTS |
| GET | `/api/v1/cloud-ai/health` | Cloud AI Agents | none | none | cloud health DTO | `cloud_ai_health` | `CloudAiApiService.getHealth` | IMPLEMENTED BUT NOT PROVIDER-VERIFIED |
| GET | `/api/v1/cloud-ai/agents` | Cloud AI Agents | none | none | agent list | `list_cloud_ai_agents` | `CloudAiApiService.getAgents` | IMPLEMENTED BUT NOT PROVIDER-VERIFIED |
| POST | `/api/v1/cloud-ai/connectivity` | Cloud AI Agents | none | none | provider connectivity list | `check_cloud_ai_connectivity` | `CloudAiApiService.checkConnectivity` | IMPLEMENTED BUT NOT PROVIDER-VERIFIED |
| POST | `/api/v1/cloud-ai/analyze-image` | Cloud AI Agents | none | multipart file/provider/agent/context/detail | cloud image result | `analyze_image_with_cloud_ai` | `CloudAiApiService.analyzeImage` | IMPLEMENTED BUT NOT PROVIDER-VERIFIED |
| POST | `/api/v1/cloud-ai/summarize-report` | Cloud AI Agents | none | form report/provider/agent/context | text summary result | `summarize_report_with_cloud_ai` | `CloudAiApiService.summarizeReport` | IMPLEMENTED BUT NOT PROVIDER-VERIFIED |
| GET | `/api/v1/media/image-upload/{filename}` | Image Media | none | path filename | `FileResponse` | `image_media_controller.get_uploaded_image` | image URLs | IMPLEMENTED AND VERIFIED BY TESTS |
| GET | `/api/v1/media/image-output/{filename}` | Image Media | none | path filename | `FileResponse` | `get_image_output` | image URLs | IMPLEMENTED AND VERIFIED BY TESTS |
| GET | `/api/v1/media/image-crop/{request_id}/{filename}` | Image Media | none | path request/filename | `FileResponse` | `get_image_crop` | image URLs | IMPLEMENTED AND VERIFIED BY TESTS |

## DTO Field Catalog

- `RegisterRequestDto`: `full_name` 2..120, `email`, `password` 6..128, `role` one of `admin|annotator|user|viewer`, default `user`.
- `LoginRequestDto`: `email`, `password` 1..128.
- `AuthResponseDto`: `access_token`, `token_type= bearer`, `user_id`, `full_name`, `email`, `role`.
- `UserProfileResponseDto`: `user_id`, `full_name`, `email`, `role`, `is_active`.
- `ImageFeatureResponseDto`: `request_id`, `image_id`, `status`, `message`, `source_filename`, `source_image_path`, `source_image_url`, `file_size_bytes`, `content_type`, `detector_model`, `annotated_image_path`, `annotated_image_url`, `width`, `height`, `source_width`, `source_height`, `inference_scaled`, counts, `model_loaded`, `detector_warning`, `detections`, `crops`, `memory_items`, `matches`.
- `VideoProcessingSettingsDto`: `detector_model=yolo`, `processing_mode=full_video`, `sample_every_seconds>=0.1`, `max_frames>=0`, `confidence_threshold 0..1`, `iou_threshold 0..1`, `max_detections_per_frame 1..500`, `tracker_iou_threshold 0.05..0.95`, `crop_padding_pixels 0..128`, `enable_memory_storage=true`, `enable_duplicate_pruning=true`, `create_annotated_video=true`, `output_video_fps>=0`, `save_detector_annotated_image=false`.
- `AnnotationObjectCreateRequestDto`: `task_id`, `label` 1..120, `geometry_type=box|polygon`, `x_min`, `y_min`, `x_max`, `y_max`, `points`.
- `AnnotationStatusUpdateRequestDto`: `status=pending|approved|rejected`.
- `CustomDatasetCreateRequestDto`: `project_id`, `name` 2..255, `version` 1..80 default `v1`, `train_split` 0.5..0.95 default 0.8, `include_pending=false`.
- `TrainingJobStartRequestDto`: `detector_model=yolo`, `dataset_version_id`, `base_model_id`, `epochs` 1..1000 default 50, `image_size` 320..1536 default 640, `batch_size` 1..128 default 8.
- `ModelRegisterRequestDto`: `model_name`, `model_type`, `version`, `model_path`, `onnx_path`, `class_names`, `metrics`.
- `CloudAiImageAnalysisRequestDto`: `provider=huggingface|openai|gemini|hybrid`, `agent_name=scene_understanding|object_metadata|video_timeline_summary|safety_review|memory_query`, `context`, `detail=auto`.

## Examples

Health:

```bash
curl http://localhost:8000/api/v1/health
```

```powershell
Invoke-RestMethod -Uri http://localhost:8000/api/v1/health
```

Image detection:

```bash
curl -X POST http://localhost:8000/api/v1/detections/test-image \
  -F "file=@sample.jpg" \
  -F "detector_model=yolo" \
  -F "confidence_threshold=0.25" \
  -F "iou_threshold=0.45"
```

Auth error:

```json
{
  "detail": {
    "message": "Authorization bearer token is missing."
  }
}
```

Validation error: FastAPI returns `detail: [{type, loc, msg, input}]` for bad fields.

Provider/model error: cloud AI wraps provider errors as HTTP 502 with `detail.message` and `detail.reason`; the reason may include provider exception text and should be sanitized before production exposure.
