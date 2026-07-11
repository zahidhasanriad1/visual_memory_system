# Configuration Reference

Real secret values are intentionally omitted.

| Variable | Purpose | Required | Default | Secret | Source |
|---|---|---|---|---|---|
| `APP_NAME` | FastAPI title | optional | VMS-X Adaptive Visual Memory Intelligence Platform | no | `appsettings.py` |
| `APP_ENV` | environment label | optional | development | no | `appsettings.py` |
| `APP_DEBUG` | include exception reasons | optional | true | no | `appsettings.py`, middleware |
| `API_PREFIX` | API prefix | optional | `/api/v1` | no | `appsettings.py` |
| `DATABASE_URL` | SQLAlchemy async DB URL | optional | SQLite in storage | sensitive-ish | `appsettings.py` |
| `JWT_SECRET_KEY` | JWT signing key | required in production | insecure placeholder | yes | `appsettings.py`, `jwt_token_service.py` |
| `JWT_ALGORITHM` | declared algorithm setting | optional | HS256 | no | `appsettings.py` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | token lifetime | optional | 120 in settings, 1440 in direct JWT service | no | both settings/JWT service |
| `CORS_ALLOWED_ORIGINS` | allowed CORS origins | optional | localhost Angular | no | `appsettings.py` |
| `MAX_UPLOAD_SIZE_MB` | global content-length limit | optional | 1024 | no | upload middleware |
| `STORAGE_ROOT` | backend storage root | optional | `backend/storage` | no | `appsettings.py` |
| `VMS_STORAGE_ROOT` | image service storage override | optional | settings storage root | no | image service |
| `VMS_HOST_STORAGE_ROOT` | host-display path mapping | optional | blank | no | settings/image service |
| `YOLO_MODEL_PATH` | YOLO ONNX/Ultralytics artifact | optional | `storage/models/skysealand_yolo12m_best.onnx` | no | settings/image/video |
| `SKYDET_MODEL_PATH` | SkyDet checkpoint | optional | `storage/models/skydet_skysealand_best.pt` | no | settings/SkyDet |
| `USE_HUGGINGFACE` | enable HF provider | optional | true | no | settings/cloud config |
| `HF_TOKEN` | Hugging Face API key | required for HF | blank | yes | settings/cloud config |
| `HUGGINGFACE_API_BASE_URL` | HF base URL | optional | `https://router.huggingface.co/v1` | no | cloud config |
| `HUGGINGFACE_VISION_MODEL` | HF vision model | optional | `zai-org/GLM-4.5V:zai-org` | no | cloud config |
| `HUGGINGFACE_TEXT_MODEL` | HF text model | optional | `Qwen/Qwen2.5-7B-Instruct` | no | cloud config |
| `HUGGINGFACE_VLM_MODEL` | legacy/additional VLM model setting | optional | null / compose value | no | settings/compose |
| `VLM_TIMEOUT_SECONDS` | settings VLM timeout | optional | 120 | no | appsettings |
| `AI_PROVIDER` | default cloud provider | optional | hybrid | no | cloud config |
| `CLOUD_AI_HYBRID_ORDER` | hybrid order | optional | huggingface,gemini,openai | no | cloud config |
| `CLOUD_AI_TIMEOUT_SECONDS` | provider timeout | optional | 60 | no | cloud config |
| `CLOUD_AI_MAX_RETRIES` | HF retry count | optional | 2 | no | cloud config |
| `USE_OPENAI` | enable OpenAI | optional | false | no | cloud config |
| `OPENAI_API_KEY` | OpenAI API key | required for OpenAI | blank | yes | cloud config |
| `OPENAI_VISION_MODEL` | OpenAI model | optional | `gpt-5.5` | no | cloud config |
| `OPENAI_API_BASE_URL` | OpenAI base URL | optional | `https://api.openai.com/v1` | no | cloud config |
| `USE_GEMINI` | enable Gemini | optional | false | no | cloud config |
| `GEMINI_API_KEY` | Gemini API key | required for Gemini | blank | yes | cloud config |
| `GEMINI_VISION_MODEL` | Gemini model | optional | `gemini-2.5-flash` | no | cloud config |
| `GEMINI_API_BASE_URL` | Gemini base URL | optional | `https://generativelanguage.googleapis.com` | no | cloud config |
| `IMAGE_TILED_DETECTION_ENABLED` | image tiling toggle | optional | true | no | image service |
| `IMAGE_TILE_SIZE` | tile size | optional | 1024 | no | image service |
| `IMAGE_TILE_OVERLAP_RATIO` | tile overlap | optional | 0.25 | no | image service |
| `IMAGE_TILED_MIN_SIDE` | min side for tiling | optional | 1400 | no | image service |
| `IMAGE_MAX_INFERENCE_SIDE` | bounded preview/inference max side | optional | 2560 | no | image service |
| `IMAGE_MAX_SOURCE_PIXELS` | source pixel cap | optional | 300000000 | no | image service |
| `IMAGE_OUTPUT_JPEG_QUALITY` | annotated/preview quality | optional | 90 | no | image service |
| `IMAGE_CROP_JPEG_QUALITY` | crop quality | optional | 90 | no | image service |
| `YOLO_INPUT_SIZE` | YOLO DNN input size | optional | 640 | no | image service |
| `YOLO_CLASS_NAMES` | class label list | optional | airplane,boat,car,ship | no | image service |
| `SKYDET_BOX_EXPANSION_RATIO` | SkyDet bbox expansion | optional | 0.08 | no | SkyDet |
| `YOLO_TRAIN_BASE_MODEL` | Ultralytics base model | optional | yolo11n.pt | no | training service |

Local example: put secrets in `backend/.env` or `backend/.env.docker` as `<API_KEY>` placeholders.

Docker example: compose maps `STORAGE_ROOT=/app/storage` and model paths under `/app/storage/models`.

Hugging Face Space example: set `STORAGE_ROOT=/data`, `DATABASE_URL=sqlite+aiosqlite:////data/database/vmsx.db`, and provider keys as Space secrets.
