# VMS-X Docker

## Run the full app

```bash
cp backend/.env.docker.example backend/.env.docker
docker compose up --build
```

Open:

- Frontend: `http://localhost:4200`
- Backend health: `http://localhost:8000/api/v1/health`

## Persistent data

The backend stores uploads, SQLite database, crops, outputs, and models in:

```text
backend/storage
```

That folder is bind-mounted into the backend container as `/app/storage`.

To return readable Windows paths alongside the canonical media URLs, set this
display-only mapping in `backend/.env.docker`:

```text
VMS_HOST_STORAGE_ROOT=E:/VMS-X/backend/storage
```

This setting never changes container file I/O; the backend continues to use
`/app/storage` internally.

## Detector models

Place detector models here before running detections:

```text
backend/storage/models/skysealand_yolo12m_best.onnx
backend/storage/models/skydet_skysealand_best.pt
```

The frontend Video Timeline Processor has a YOLO/SkyDet selector. Both options use the same backend processing pipeline after detection.

The `backend/storage` folder is bind-mounted into Docker as `/app/storage`, so the compose defaults are:

```text
YOLO_MODEL_PATH=/app/storage/models/skysealand_yolo12m_best.onnx
SKYDET_MODEL_PATH=/app/storage/models/skydet_skysealand_best.pt
```

## Cloud AI

The backend uses Hugging Face Inference Providers for the default vision-language and text models. Copy `backend/.env.docker.example` to the git-ignored `backend/.env.docker`, replace `JWT_SECRET_KEY`, then add a Hugging Face token with Inference Providers permission:

```text
USE_HUGGINGFACE=true
HF_TOKEN=hf_your_token_here
HUGGINGFACE_API_BASE_URL=https://router.huggingface.co/v1
HUGGINGFACE_VISION_MODEL=zai-org/GLM-4.5V:zai-org
HUGGINGFACE_TEXT_MODEL=Qwen/Qwen2.5-7B-Instruct
HUGGINGFACE_VLM_MODEL=zai-org/GLM-4.5V:zai-org
```

The token stays in the git-ignored backend environment file and is never exposed to Angular or copied into the backend image. OpenAI and Gemini remain disabled by default; enable them and add keys only in your local `backend/.env.docker`. Hybrid mode falls back in this order: `huggingface,gemini,openai`.

## Local dev without Docker

Run the backend on port `8000`:

```bash
cd backend
python -m uvicorn vms_api.main:app --host 0.0.0.0 --port 8000
```

Run the frontend with the package script so Angular uses `proxy.conf.json`:

```bash
cd frontend
npm start
```

Open `http://localhost:4200`. The frontend calls `/api/v1/...`; Angular proxies `/api` to `http://127.0.0.1:8000`.

## Useful commands

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
docker compose down
```
