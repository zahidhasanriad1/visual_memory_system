# Test And Runbook

## Verified Commands

Backend source compile excluding `.venv`:

```powershell
backend\.venv\Scripts\python.exe -m compileall -q backend\vms_api backend\vms_data_access backend\vms_domain backend\vms_models backend\vms_services backend\vms_utils backend\tests
```

Result: passed.

Backend tests:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Workdir: `E:\VMS-X\backend`.
Result: `29 passed in 19.37s`.

Frontend build:

```powershell
npm.cmd run build
```

Workdir: `E:\VMS-X\frontend`.
Result: passed, initial bundle `570.65 kB`, generation `20.880 seconds`.

Docker Compose validation:

```powershell
docker compose config
```

Result: config rendered. Warnings: Docker config file access denied for `C:\Users\Riad\.docker\config.json`.

OpenAPI generation:

```powershell
backend\.venv\Scripts\python.exe -c "import sys,json; sys.path.insert(0,'backend'); from vms_api.main import app; print(len(app.openapi()['paths']))"
```

Result: 38 paths.

Health smoke:

```powershell
backend\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'backend'); from fastapi.testclient import TestClient; from vms_api.main import app; r=TestClient(app).get('/api/v1/health'); print(r.status_code); print(r.text)"
```

Result: HTTP 200 with healthy envelope.

## Local Backend

```powershell
cd E:\VMS-X\backend
.\.venv\Scripts\python.exe -m uvicorn vms_api.main:app --host 0.0.0.0 --port 8000 --reload
```

Expected health: `GET http://localhost:8000/api/v1/health` returns success envelope.

## Local Frontend

```powershell
cd E:\VMS-X\frontend
npm.cmd start
```

Expected: Angular dev server on port 4200 with proxy config.

## Docker Compose

```powershell
cd E:\VMS-X
docker compose up --build
```

Expected: backend on 8000, frontend on 4200, backend healthcheck queries `/api/v1/health`.

## Database Initialization

Database schema is created on backend startup by `create_database_schema()`. No migrations are available.

## Redis

Redis is not configured or used.

## Ollama

Ollama is not implemented in active source.

## Provider Health

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/cloud-ai/connectivity
```

Expected: list of provider statuses. With blank keys, providers report unconfigured.

## Smoke Tests

Image detection:

```powershell
curl.exe -X POST http://localhost:8000/api/v1/detections/test-image -F "file=@sample.jpg"
```

Video job:

```powershell
curl.exe -X POST http://localhost:8000/api/v1/video-memory/jobs/ingest-video -F "file=@sample.mp4"
```

Annotation:

```powershell
Invoke-RestMethod -Method Get -Uri http://localhost:8000/api/v1/annotation/projects
```

Training list:

```powershell
Invoke-RestMethod -Uri http://localhost:8000/api/v1/training-jobs
```

Cleanup tests: none implemented.
