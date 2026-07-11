# VMS-X: Adaptive Visual Memory Intelligence Platform

VMS-X is an industry-grade FastAPI + Angular platform for full-timeline video intelligence, object tracking, visual memory, VLM-assisted open-world object naming, human-in-the-loop annotation, dataset versioning, training orchestration, and safe model registry activation.



## Visual Documentation

- [Project Owner](#project-owner)
- [Professional Skills](#professional-skills)
- [Tech Stack](#tech-stack)
- [System Architecture](#system-architecture)
- [Main User Workflow](#main-user-workflow)
- [Runtime Request Lifecycle](#runtime-request-lifecycle)
- [Image and Video Ingest Workflow](#image-and-video-ingest-workflow)
- [Database Model Diagram](#database-model-diagram)
- [CI Workflow](#ci-workflow)

## Tech Stack

| Layer | Technology | Role |
| --- | --- | --- |
| Frontend | Angular 21, TypeScript, RxJS | Standalone feature UI, routing, API clients, dashboard workflows |
| Backend API | FastAPI, Pydantic DTOs | REST API, request validation, response shaping, OpenAPI docs |
| Service Layer | Python services, dependency injection | Video intelligence, image features, cloud AI, training, registry logic |
| AI / CV | YOLO/ONNX, SkyDet/PT, ByteTrack-style tracking | Detection, tracking, crops, timeline-preserving video memory |
| Cloud AI | Hugging Face, Gemini, OpenAI adapters | VLM object naming, image analysis, report summarization |
| Data Layer | SQLAlchemy, repository pattern | Domain persistence, query boundaries, async database access |
| Storage | Local/Docker volume storage | Uploaded media, crops, reports, generated videos, model artifacts |
| DevOps | Docker, Docker Compose, pytest, Angular build | Reproducible local runtime and verification pipeline |

## System Architecture

```mermaid
flowchart TB
    subgraph Client["Client Layer"]
        Angular["Angular 21 Frontend"]
        Routes["Feature Routes"]
        ApiClient["Typed API Services"]
    end

    subgraph API["FastAPI Backend"]
        Controllers["Controllers"]
        Middleware["CORS / Logging / Error Middleware"]
        DI["Dependency Services"]
    end

    subgraph Domain["Application Core"]
        Services["Business Services"]
        AIProviders["AI Provider Adapters"]
        Repositories["Repositories"]
        DTOs["Request / Response DTOs"]
    end

    subgraph Intelligence["Vision Intelligence"]
        Detector["YOLO / SkyDet Detector"]
        Tracker["ByteTrack-style Tracker"]
        VLM["VLM Providers"]
        Trainer["Training Orchestrator"]
    end

    subgraph Persistence["Persistence and Storage"]
        Database["SQLAlchemy Database"]
        MediaStore["Media / Crop / Report Storage"]
        Registry["Model Registry"]
    end

    Angular --> Routes --> ApiClient
    ApiClient --> Controllers
    Controllers --> Middleware
    Controllers --> DI
    DI --> Services
    Services --> DTOs
    Services --> AIProviders
    Services --> Repositories
    AIProviders --> Detector
    AIProviders --> VLM
    Detector --> Tracker
    Services --> Trainer
    Repositories --> Database
    Services --> MediaStore
    Trainer --> Registry
    Registry --> Detector
```

### Backend Package Map

| Package | Responsibility |
| --- | --- |
| `vms_api` | FastAPI app, controllers, middleware, dependency services, configuration |
| `vms_services` | Business logic, AI providers, image/video processing, training orchestration |
| `vms_data_access` | Repository implementations and persistence boundaries |
| `vms_domain` | SQLAlchemy entities, database session setup, migration boundary |
| `vms_models` | Request and response DTOs used by API and frontend contracts |
| `vms_utils` | Security, validation, enums, middleware helpers, shared exceptions |

## Main User Workflow

```mermaid
flowchart LR
    Login["Login / Register"] --> Dashboard["Dashboard"]
    Dashboard --> Image["Image Features"]
    Dashboard --> Video["Video Memory"]
    Dashboard --> Cloud["Cloud AI"]
    Dashboard --> Review["Adaptive Review"]
    Dashboard --> Annotate["Annotation Workspace"]
    Dashboard --> Train["Custom Training"]
    Dashboard --> Models["Model Registry"]

    Image --> Results["Detections / Crops / Memory Search"]
    Video --> Tracks["Jobs / Tracks / Annotated Output"]
    Cloud --> Summary["AI Analysis / Report Summary"]
    Review --> Annotate
    Annotate --> Dataset["Dataset Version"]
    Dataset --> Train
    Train --> Models
    Models --> Image
    Models --> Video
```

1. The operator signs in and lands on the dashboard.
2. Image and video workflows create detections, crops, tracks, and visual memory records.
3. Uncertain objects move into adaptive review where VLM suggestions can be accepted or corrected.
4. Human-reviewed labels flow into annotation, dataset versioning, and training.
5. Approved model versions are activated through the registry and reused by future detection runs.

## Runtime Request Lifecycle

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant A as Angular UI
    participant C as API Client
    participant F as FastAPI Controller
    participant S as Service Layer
    participant R as Repository
    participant DB as Database
    participant ST as Storage
    participant AI as AI Provider

    U->>A: Submit action or upload media
    A->>C: Build typed request
    C->>F: HTTP request to /api/v1/*
    F->>F: Validate request DTO and auth context
    F->>S: Resolve service via dependency injection
    S->>ST: Store uploaded media when needed
    S->>AI: Run detector, tracker, or VLM provider
    S->>R: Persist domain results
    R->>DB: Insert or query records
    DB-->>R: Return entities
    R-->>S: Return domain data
    S-->>F: Return sanitized response DTO
    F-->>C: API response with public URLs
    C-->>A: Update UI state
    A-->>U: Render result, job status, or review task
```

## Image and Video Ingest Workflow

```mermaid
flowchart TD
    Upload["Upload Image or Video"] --> Validate["Validate file, size, mode, and settings"]
    Validate --> Type{"Media Type"}

    Type -->|Image| ImageStore["Store source image"]
    ImageStore --> ImageDetect["Run image detection or cloud AI analysis"]
    ImageDetect --> ImageCrops["Generate crops and normalized detections"]
    ImageCrops --> ImageMemory["Ingest or search object memory"]
    ImageMemory --> ImageResponse["Return feature results and safe media URLs"]

    Type -->|Video| VideoJob["Create background video job"]
    VideoJob --> FrameLoop["Read frames while preserving timeline"]
    FrameLoop --> VideoDetect["Run YOLO/ONNX or SkyDet/PT detector"]
    VideoDetect --> Track["Track objects across frames"]
    Track --> VideoMemory["Persist tracks and visual memory"]
    VideoMemory --> Output["Generate report and annotated video"]
    Output --> JobResult["Return job status, result report, and media URLs"]

    ImageResponse --> Review{"Needs human review?"}
    JobResult --> Review
    Review -->|Yes| Adaptive["Adaptive learning queue"]
    Review -->|No| Done["Completed result"]
    Adaptive --> Annotation["Annotation workspace"]
    Annotation --> Dataset["Dataset versioning"]
    Dataset --> Training["Training orchestration"]
    Training --> Registry["Model registry activation"]
```

## Database Model Diagram

The current persistence model uses UUID-style string identifiers and several logical relationships through `*_id` fields.

```mermaid
erDiagram
    USER {
        string user_id PK
        string full_name
        string email
        string role
        bool is_active
    }

    VIDEO {
        string id PK
        string original_filename
        string source_video_path
        float fps
        int total_video_frames
        float duration_seconds
    }

    VIDEO_JOB {
        string id PK
        string video_id
        string status
        float progress_percent
        string result_report_path
    }

    VIDEO_FRAME {
        string id PK
        string video_id
        int frame_number
        float timestamp_seconds
        string frame_image_path
    }

    TRACKED_OBJECT {
        string id PK
        string video_id
        string track_id
        string class_name
        float confidence
        string crop_path
    }

    VISUAL_MEMORY {
        string id PK
        string video_id
        string track_id
        string class_name
        float confidence
        string crop_path
    }

    OBJECT_IDENTITY {
        string id PK
        string canonical_label
        string representative_memory_id
        json memory_ids
    }

    ADAPTIVE_LEARNING_ITEM {
        string id PK
        string source_type
        string source_video_id
        string vlm_object_name
        string final_label
        string status
    }

    ANNOTATION_PROJECT {
        string id PK
        string name
        string status
    }

    ANNOTATION_TASK {
        string id PK
        string project_id
        string source_type
        string source_path
        string status
    }

    ANNOTATION_OBJECT {
        string id PK
        string task_id
        string label
        float x_min
        float y_min
        float x_max
        float y_max
    }

    DATASET_VERSION {
        string id PK
        string name
        string version
        string export_path
        int image_count
        int annotation_count
    }

    TRAINING_JOB {
        string id PK
        string dataset_version_id
        string status
        float progress_percent
        string output_model_path
    }

    MODEL_VERSION {
        string id PK
        string model_name
        string model_type
        string version
        string model_path
        string status
    }

    AUDIT_LOG {
        string id PK
        string actor_user_id
        string action
        string entity_type
        string entity_id
    }

    USER ||--o{ AUDIT_LOG : performs
    VIDEO ||--o{ VIDEO_JOB : has
    VIDEO ||--o{ VIDEO_FRAME : contains
    VIDEO ||--o{ TRACKED_OBJECT : produces
    VIDEO ||--o{ VISUAL_MEMORY : stores
    VIDEO ||--o{ ADAPTIVE_LEARNING_ITEM : may_create
    VISUAL_MEMORY ||--o{ OBJECT_IDENTITY : clusters_into
    ANNOTATION_PROJECT ||--o{ ANNOTATION_TASK : owns
    ANNOTATION_TASK ||--o{ ANNOTATION_OBJECT : contains
    DATASET_VERSION ||--o{ TRAINING_JOB : trains
    TRAINING_JOB ||--o{ MODEL_VERSION : outputs
```

## CI Workflow

```mermaid
flowchart LR
    Push["Push / Pull Request"] --> Checkout["Checkout source"]
    Checkout --> BackendSetup["Set up Python"]
    Checkout --> FrontendSetup["Set up Node"]
    BackendSetup --> BackendInstall["Install backend dependencies"]
    FrontendSetup --> FrontendInstall["npm install / npm ci"]
    BackendInstall --> BackendTests["Run pytest"]
    FrontendInstall --> FrontendBuild["Run Angular build"]
    BackendTests --> DockerBuild["Build backend Docker image"]
    FrontendBuild --> DockerBuild
    DockerBuild --> ComposeSmoke["Docker Compose smoke check"]
    ComposeSmoke --> Artifact["Ready for release or deployment"]
```

Recommended checks:

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q

cd ../frontend
npm install
npm run build

cd ..
docker compose up --build
```

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


