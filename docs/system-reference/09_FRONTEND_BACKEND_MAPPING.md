# Frontend Backend Mapping

API base URL is `'/api/v1'` in `frontend/src/app/core/config/api.config.ts`; production code is not hardcoded to localhost.

## Routes And Pages

| Frontend route | Component | Backend calls | Loading/error state | Auth behavior | Status |
|---|---|---|---|---|---|
| `/login` | `features/auth/pages/login/login-page.ts` | `POST /auth/login/form` | form submit errors | public | IMPLEMENTED |
| `/register` | `features/auth/pages/register/register-page.ts` | `POST /auth/register` | form submit errors | public | IMPLEMENTED |
| `/dashboard` | `DashboardComponent` | local/cards, auth role | role-filtered cards | guarded | IMPLEMENTED |
| `/image-features` | `ImageFeaturesPageComponent` | image feature service endpoints | loading/error in component | frontend guard roles admin/annotator/user/viewer | IMPLEMENTED |
| `/video-memory` | `VideoMemoryComponent` | create/status/result video job | polling/status UI | frontend guard admin/user | IMPLEMENTED |
| `/cloud-ai` | `CloudAiPageComponent` | health/agents/connectivity/analyze/summarize | page states | frontend guard admin/user | IMPLEMENTED |
| `/annotation` | `AnnotationWorkspaceComponent` | annotation project/task/object/label endpoints | explicit error messages | frontend guard admin/annotator/user | IMPLEMENTED |
| `/adaptive-learning` | `AdaptiveReviewComponent` | direct HTTP to `/adaptive-learning/crop/analyze` | component states | frontend guard admin/annotator/user | PARTIAL |
| `/approval` | `AdaptiveReviewComponent` | same as above | component states | frontend guard admin/annotator/user | PARTIAL |
| `/custom-training` | `CustomTrainingComponent` | training dataset/job endpoints, annotation projects | loading/error | frontend guard admin/user | IMPLEMENTED |
| `/training` | `TrainingOrchestratorComponent` | `POST /training-jobs/start` | component states | frontend guard admin | PARTIAL |
| `/model-registry` | `ModelRegistryComponent` | model registry endpoints | loading/error | frontend guard admin | IMPLEMENTED |

## Service Method Mapping

| Angular service/method | Backend endpoint | Backend service |
|---|---|---|
| `AuthApiService.register` | `POST /api/v1/auth/register` | `AuthService.register` |
| `AuthApiService.loginForm` | `POST /api/v1/auth/login/form` | `AuthService.login` |
| `AuthApiService.me` | `GET /api/v1/auth/me` | `AuthService.get_current_user` |
| `ImageFeatureApiService.getDashboardImages` | `GET /api/v1/image-features/dashboard-images` | `ImageFeatureService.list_dashboard_images` |
| `testImageCrop` | `POST /api/v1/crops/test-image` | `ImageFeatureService.test_crops` |
| `testImageDetection` | `POST /api/v1/detections/test-image` | `ImageFeatureService.test_detections` |
| `testImageDetectionCrops` | `POST /api/v1/detection-crops/test-image` | `ImageFeatureService.test_detection_crops` |
| `ingestImageToMemory` | `POST /api/v1/object-memory/ingest-image` | `ImageFeatureService.ingest_image_to_memory` |
| `searchImageMemory` | `POST /api/v1/object-memory/search-image` | `ImageFeatureService.search_image_memory` |
| `VideoMemoryService.createJob` | `POST /api/v1/video-memory/jobs/ingest-video` | `VideoMemoryService.create_job_async` |
| `VideoMemoryService.status` | `GET /api/v1/video-memory/jobs/{job_id}` | `get_job_status_async` |
| `VideoMemoryService.result` | `GET /api/v1/video-memory/jobs/{job_id}/result` | `get_job_result_async` |
| `CloudAiApiService.getHealth` | `GET /api/v1/cloud-ai/health` | `CloudAiAgentService.get_health` |
| `CloudAiApiService.getAgents` | `GET /api/v1/cloud-ai/agents` | `get_agents` |
| `CloudAiApiService.checkConnectivity` | `POST /api/v1/cloud-ai/connectivity` | `check_connectivity` |
| `CloudAiApiService.analyzeImage` | `POST /api/v1/cloud-ai/analyze-image` | `analyze_uploaded_image` |
| `CloudAiApiService.summarizeReport` | `POST /api/v1/cloud-ai/summarize-report` | `summarize_report` |
| `AnnotationApiService.*` | annotation endpoints | `AnnotationService` |
| `ApiClientService` from training pages | training endpoints | `TrainingService` |
| `ApiClientService` from registry page | model registry endpoints | `ModelRegistryService` |

## Auth Note

The frontend stores tokens in localStorage and sends `Authorization: Bearer <JWT_TOKEN>` via interceptor. The frontend route guard enforces roles locally. Backend routes generally do not enforce these roles; only `/auth/me` explicitly requires a bearer token.
