# VMS-X: Adaptive Visual Memory Intelligence Platform

VMS-X is an industry-grade FastAPI + Angular platform for full-timeline video intelligence, object tracking, visual memory, VLM-assisted open-world object naming, human-in-the-loop annotation, dataset versioning, training orchestration, and safe model registry activation.

## Core pipeline

```text
Video/Image Upload
→ Full-frame timeline-preserving processing
→ YOLO/ONNX or SkyDet/PT detector adapter
→ ByteTrack-style tracker
→ Object crop + visual memory metadata
→ Video report + annotated output video
→ VLM-assisted adaptive learning
→ CVAT/Roboflow-style annotation workspace
→ Dataset versioning
→ Training orchestration
→ Model registry activation/rollback
```

## Architecture

Backend uses Python package names mapped from the requested architecture:

- `vms_data_access` = DataAccess interfaces/repositories/injection
- `vms_domain` = database/entities/migrations
- `vms_models` = all request/response DTOs, one DTO per file
- `vms_services` = interfaces/services/injection
- `vms_utils` = base, exceptions, auth policy, enums, middleware, security
- `vms_api` = controllers, configuration, middleware, dependency services, appsettings, main

Frontend uses Angular 21 standalone, feature-based architecture.

## Run with Docker

```bash
cp backend/.env.docker.example backend/.env.docker
# Set HF_TOKEN and replace JWT_SECRET_KEY in backend/.env.docker, then:
docker compose up --build
```

Backend: http://localhost:8000/docs  
Frontend: http://localhost:4200

## Local backend run

```bash
cd backend
cp .env.example .env
# Set HF_TOKEN in .env
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
python -m vms_api.main
```

Run backend tests with the development dependencies:

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

## Local frontend run

```bash
cd frontend
npm install
npm start
```

## Notes

- Default video processing is `full_video` with `max_frames=0` and `output_video_fps=0.0`, preserving original video timeline.
- Detection adapter is modular. The Video Timeline Processor lets users choose `YOLO` or `SkyDet` for the same tracking, crop, memory, report, and annotated-video pipeline. Set `YOLO_MODEL_PATH` and `SKYDET_MODEL_PATH` in `backend/.env` or Docker env to override the default model files.
- Image APIs return browser-safe media URLs. Public API responses and the Angular console never expose host or container filesystem locations.
- Cloud AI and adaptive-learning VLM requests use Hugging Face Inference Providers through the backend. Set `HF_TOKEN`, `HUGGINGFACE_VISION_MODEL`, and `HUGGINGFACE_TEXT_MODEL`; the token is never sent to the frontend.
- OpenAI and Gemini remain optional providers. Hybrid mode tries `huggingface,gemini,openai` by default.
- If Hugging Face is unavailable or unconfigured, adaptive learning safely routes the item to human review.

