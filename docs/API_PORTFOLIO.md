# VMS-X API Portfolio Reference

VMS-X is an end-to-end visual intelligence platform built with FastAPI, Angular, SQLAlchemy, OpenCV, PyTorch, ONNX, YOLO, SkyDet, and Hugging Face/Gemini provider adapters. It supports secure image/video inference, visual memory, human-in-the-loop annotation, versioned dataset generation, custom object training, and model activation.

## CV-ready project summary

> Engineered VMS-X, an industry-oriented computer-vision platform that unifies YOLO/ONNX and a custom PyTorch SkyDet detector behind a consistent FastAPI API. Built large-TIFF inference, tiled detection, secure media delivery, image/video pipelines, CVAT-style box and polygon annotation, approval workflows, dynamic class datasets, custom model training, model versioning, and an Angular operations console. Integrated Hugging Face, Gemini, and OpenAI through provider adapters without exposing API keys or server filesystem paths.

## Strong CV bullet points

- Designed a modular FastAPI and Angular visual-intelligence platform supporting interchangeable YOLO and custom SkyDet detection pipelines.
- Implemented bounded large-image decoding and tiled inference for 180 MB TIFF imagery while preserving original image metadata and returning browser-safe previews.
- Verified a `11185 x 13760` TIFF end to end: SkyDet completed in `17.38 s` with 21 detections and YOLO completed in `19.43 s` with 69 detections on the local test environment.
- Developed a CVAT/Roboflow-style annotation workspace with bounding boxes, polygons, dynamic labels, object review, approval, rejection, and deletion.
- Built an annotation-to-training lifecycle that generates versioned YOLO and COCO datasets, trains YOLO or SkyDet models, registers artifacts, and activates validated versions.
- Added recursive response sanitization so API payloads expose browser-safe media URLs but never host or container filesystem locations.
- Integrated Hugging Face, Gemini, and OpenAI behind a provider-routing layer with health checks, safe error normalization, timeout handling, and no frontend key exposure.
- Improved inference responsiveness with streamed uploads, bounded decoding, background work, tiled NMS, lazy service initialization, batched storage updates, and Angular request-state controls.

## Representative API surface

| Capability | Method and endpoint | Purpose |
|---|---|---|
| Image detection | `POST /api/v1/detections/test-image` | Run YOLO or SkyDet on PNG, JPEG, or TIFF |
| Detection and crops | `POST /api/v1/detection-crops/test-image` | Detect objects and create secured crop URLs |
| Visual-memory ingest | `POST /api/v1/object-memory/ingest-image` | Store detected-object metadata |
| Visual-memory search | `POST /api/v1/object-memory/search-image` | Retrieve visually similar objects |
| Annotation labels | `GET /api/v1/annotation/labels` | Return default and learned dynamic classes |
| Annotation object | `POST /api/v1/annotation/objects` | Create a box or polygon annotation |
| Approval review | `PATCH /api/v1/annotation/objects/{id}/status` | Approve or reject an annotation |
| Dataset builder | `POST /api/v1/training-jobs/datasets/from-annotations` | Build versioned YOLO and COCO datasets |
| Custom training | `POST /api/v1/training-jobs/start` | Queue YOLO or SkyDet training |
| Training status | `GET /api/v1/training-jobs/{job_id}` | Return progress and metrics |
| AI connectivity | `POST /api/v1/cloud-ai/connectivity` | Safely verify configured provider inference |

## 1. Large-TIFF SkyDet detection

### Request

```bash
curl -X POST "http://localhost:8000/api/v1/detections/test-image" \
  -F "file=@port_satellite_scene.tif;type=image/tiff" \
  -F "detector_model=skydet" \
  -F "confidence_threshold=0.25" \
  -F "iou_threshold=0.45"
```

### Sanitized response

```json
{
  "success": true,
  "message": "Image detection test completed successfully.",
  "data": {
    "request_id": "e6764f8f-3673-476e-b3ba-0a0f83da52f1",
    "image_id": "e6764f8f-3673-476e-b3ba-0a0f83da52f1",
    "status": "completed",
    "source_filename": "port_satellite_scene.tif",
    "source_image_url": "/api/v1/media/image-output/e6764f8f-3673-476e-b3ba-0a0f83da52f1_source_preview.jpg",
    "annotated_image_url": "/api/v1/media/image-output/e6764f8f-3673-476e-b3ba-0a0f83da52f1_annotated.jpg",
    "file_size_bytes": 180459048,
    "content_type": "image/tiff",
    "detector_model": "skydet",
    "source_width": 11185,
    "source_height": 13760,
    "width": 2081,
    "height": 2560,
    "inference_scaled": true,
    "processed_image_count": 1,
    "total_detection_count": 21,
    "model_loaded": true,
    "detector_warning": null,
    "detections": [
      {
        "detection_id": "detection-uuid",
        "class_id": 3,
        "class_name": "ship",
        "confidence": 0.536885,
        "bbox": {"x_min": 1410, "y_min": 428, "x_max": 1654, "y_max": 618},
        "annotated_image_url": "/api/v1/media/image-output/e6764f8f-3673-476e-b3ba-0a0f83da52f1_annotated.jpg"
      }
    ],
    "crops": [],
    "memory_items": [],
    "matches": []
  }
}
```

The detection list is shortened here for presentation. Public responses contain URLs only; fields such as `source_image_path`, `annotated_image_path`, and `crop_path` are recursively removed.

## 2. Polygon annotation

### Request

```http
POST /api/v1/annotation/objects
Content-Type: application/json

{
  "task_id": "task-7c1240",
  "label": "fishing_vessel",
  "geometry_type": "polygon",
  "points": [[164.0, 82.0], [431.0, 91.0], [452.0, 188.0], [179.0, 207.0]]
}
```

### Response

```json
{
  "success": true,
  "message": "Annotation object created successfully.",
  "data": {
    "id": "annotation-c2a95f",
    "task_id": "task-7c1240",
    "label": "fishing_vessel",
    "geometry_type": "polygon",
    "points": [[164.0, 82.0], [431.0, 91.0], [452.0, 188.0], [179.0, 207.0]],
    "x_min": 164.0,
    "y_min": 82.0,
    "x_max": 452.0,
    "y_max": 207.0,
    "status": "pending"
  }
}
```

## 3. Annotation approval

```http
PATCH /api/v1/annotation/objects/annotation-c2a95f/status
Content-Type: application/json

{"status": "approved"}
```

```json
{
  "success": true,
  "message": "Annotation review status updated.",
  "data": {
    "id": "annotation-c2a95f",
    "task_id": "task-7c1240",
    "label": "fishing_vessel",
    "geometry_type": "polygon",
    "points": [[164.0, 82.0], [431.0, 91.0], [452.0, 188.0], [179.0, 207.0]],
    "x_min": 164.0,
    "y_min": 82.0,
    "x_max": 452.0,
    "y_max": 207.0,
    "status": "approved"
  }
}
```

## 4. Versioned dataset creation

```http
POST /api/v1/training-jobs/datasets/from-annotations
Content-Type: application/json

{
  "project_id": "project-port-assets",
  "name": "Port Assets",
  "version": "v2",
  "train_split": 0.8,
  "include_pending": false
}
```

```json
{
  "success": true,
  "message": "Versioned training dataset created from approved annotations.",
  "data": {
    "id": "dataset-9bd35f",
    "name": "Port Assets",
    "version": "v2",
    "class_names": ["ship", "boat", "car", "airplane", "fishing_vessel", "harbor_crane"],
    "image_count": 1840,
    "annotation_count": 12763,
    "quality_score": 94,
    "ready_for_training": true
  }
}
```

## 5. Custom SkyDet training

```http
POST /api/v1/training-jobs/start
Content-Type: application/json

{
  "detector_model": "skydet",
  "dataset_version_id": "dataset-9bd35f",
  "base_model_id": null,
  "epochs": 50,
  "image_size": 640,
  "batch_size": 8
}
```

```json
{
  "success": true,
  "message": "Training job created successfully.",
  "data": {
    "job_id": "train-f45809",
    "detector_model": "skydet",
    "status": "queued",
    "progress_percent": 0.0,
    "message": "Training job queued.",
    "metrics": {
      "epochs": 50,
      "image_size": 640,
      "batch_size": 8,
      "dataset_version_id": "dataset-9bd35f"
    }
  }
}
```

Completed training status:

```json
{
  "success": true,
  "message": "Training job loaded successfully.",
  "data": {
    "job_id": "train-f45809",
    "detector_model": "skydet",
    "status": "completed",
    "progress_percent": 100.0,
    "message": "Training completed and validated model activated.",
    "metrics": {
      "epochs": 50,
      "class_count": 6,
      "best_validation_loss": 0.184,
      "model_activated": true
    }
  }
}
```

## 6. Cloud AI provider connectivity

Successful-state example after valid provider permissions and outbound network access:

```http
POST /api/v1/cloud-ai/connectivity
```

```json
{
  "success": true,
  "message": "Cloud provider connectivity check completed.",
  "data": [
    {
      "provider": "huggingface",
      "configured": true,
      "connected": true,
      "message": "Provider authentication and inference are working.",
      "latency_ms": 842
    },
    {
      "provider": "gemini",
      "configured": true,
      "connected": true,
      "message": "Provider authentication and inference are working.",
      "latency_ms": 611
    },
    {
      "provider": "openai",
      "configured": false,
      "connected": false,
      "message": "API key or provider configuration is missing.",
      "latency_ms": null
    }
  ]
}
```

The connectivity endpoint never returns tokens, provider exception bodies, or secret configuration values.

## Security and engineering decisions

- API keys exist only in backend environment configuration.
- Public DTOs return media URLs, IDs, dimensions, status, metrics, and model attribution.
- Recursive sanitizers remove all keys ending in `_path` or `_paths` before serialization.
- Uploads are streamed in chunks and validated by file signature, MIME type, extension, and size.
- TIFF and oversized images use a browser-safe JPEG preview and a bounded inference representation.
- Detector identity is preserved end to end: a SkyDet request reports `detector_model: "skydet"`, not `yolo`.
- Training classes are read from approved annotations/checkpoint metadata, so the model can grow beyond the original four classes.

## Interview explanation

> The central design decision was to keep the existing layered architecture while putting YOLO and SkyDet behind the same detector contract. This made image, video, crop, memory, annotation, and training pipelines model-agnostic. Large TIFF files were solved with streamed persistence, bounded Pillow decoding, tiled inference, and global NMS. The annotation layer produces reviewed, versioned datasets, and the training layer updates the registry and live detector only after a successful run. API responses deliberately expose media URLs instead of infrastructure paths.
