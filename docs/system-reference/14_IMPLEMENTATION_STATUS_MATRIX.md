# Implementation Status Matrix

| Capability | Backend route | Backend service | Frontend page | Test coverage | Runtime verified | Status | Missing work | Evidence file |
|---|---|---|---|---|---|---|---|---|
| Health | `/health` | inline controller | Docker health | no direct test | yes | IMPLEMENTED AND VERIFIED | none | `health_controller.py` |
| Auth register/login/me | `/auth/*` | `AuthService` | login/register | indirect no | no | PARTIALLY IMPLEMENTED | backend-wide auth/roles | `auth_service.py` |
| Image validation | image routes | `ImageFileValidator` | image page | yes | tests | IMPLEMENTED AND VERIFIED | none | `image_file_validator.py` |
| TIFF/large image preview | image routes | `_decode_saved_image` | image page | partial | no | IMPLEMENTED BUT NOT RUNTIME-VERIFIED | smoke test | `image_feature_service.py` |
| YOLO ONNX image detection | `/detections/test-image` | OpenCV DNN | image page | partial | no | IMPLEMENTED BUT NOT RUNTIME-VERIFIED | model smoke/metrics | `image_feature_service.py` |
| SkyDet detection | image/video routes | `SkyDetDetector` | image/video pages | no full inference | no | IMPLEMENTED BUT NOT RUNTIME-VERIFIED | model smoke/metrics | `skydet_detector.py` |
| NMS/postprocessing | image/model code | OpenCV/Torch NMS | n/a | partial | no | IMPLEMENTED | edge tests | service/detector |
| Crops | `/crops`, `/detection-crops` | crop helpers | image page | yes | tests | IMPLEMENTED AND VERIFIED | cleanup | `image_feature_service.py` |
| Image memory ingest/search | `/object-memory/*` | JSON histogram memory | image page | yes | tests | IMPLEMENTED AND VERIFIED | vector DB/filtering | `image_feature_service.py` |
| ChromaDB | none | none | none | none | no | MISSING | implement Chroma | n/a |
| Video upload/job | `/video-memory/jobs/ingest-video` | `VideoMemoryService` | video page | no | no | IMPLEMENTED BUT NOT RUNTIME-VERIFIED | upload streaming/auth | `video_memory_service.py` |
| Video frame detection/tracking | job background | `VideoMemoryService` + tracker | video page | no | no | IMPLEMENTED BUT NOT RUNTIME-VERIFIED | smoke tests | `video_memory_service.py` |
| Annotated video reconstruction | media video route | OpenCV writer | video page | no | no | IMPLEMENTED BUT NOT RUNTIME-VERIFIED | codec/audio tests | `video_memory_service.py` |
| Audio preservation | none | none | none | none | no | MISSING | ffmpeg audio mux | n/a |
| Video list/delete/retry/timeline endpoints | none | partial report only | none | none | no | MISSING/PARTIAL | add routes/services | n/a |
| Cloud AI health/agents | `/cloud-ai/health`, `/agents` | `CloudAiAgentService` | cloud page | yes for config/provider utilities | no live | IMPLEMENTED BUT NOT PROVIDER-VERIFIED | live provider tests | cloud files |
| Hugging Face/Gemini/OpenAI | `/cloud-ai/*` | provider classes | cloud page | unit/provider mocks | no live | IMPLEMENTED BUT NOT PROVIDER-VERIFIED | secrets/connectivity verification | providers |
| Ollama | none | none | none | stale pycache only | no | MISSING | source provider | n/a |
| Annotation | `/annotation/*` | `AnnotationService` | annotation page | no full route tests | no | IMPLEMENTED BUT NOT RUNTIME-VERIFIED | auth, project/task CRUD | annotation files |
| Dataset export | `/training-jobs/datasets/from-annotations` | `TrainingService` | custom training | partial | no | IMPLEMENTED BUT NOT RUNTIME-VERIFIED | export smoke | training service |
| Training jobs | `/training-jobs/*` | `TrainingService` | training pages | partial | no full training | IMPLEMENTED BUT NOT RUNTIME-VERIFIED | worker/progress tests | training service |
| Model registry | `/model-registry/*` | `ModelRegistryService` | registry page | no | no | PARTIALLY IMPLEMENTED | file validation/reload on manual activation | registry service |
| Docker deployment | compose | Dockerfiles | Nginx frontend | config only | config rendered | IMPLEMENTED BUT NOT RUNTIME-VERIFIED | build/run in Docker | compose |
| Migrations | none | metadata startup | n/a | no | no | MISSING | Alembic scripts | migrations folder |
| Cleanup/retention | none | none | none | no | no | MISSING | cleanup worker/policy | storage evidence |
