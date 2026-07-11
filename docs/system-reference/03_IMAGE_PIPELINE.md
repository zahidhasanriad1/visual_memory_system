# Image Pipeline

## Pipeline Trace

Upload route:

- Crop test: `POST /api/v1/crops/test-image`
- Detection: `POST /api/v1/detections/test-image`
- Detection + crops: `POST /api/v1/detection-crops/test-image`
- Memory ingest: `POST /api/v1/object-memory/ingest-image`
- Memory search: `POST /api/v1/object-memory/search-image`
- Dashboard: `GET /api/v1/image-features/dashboard-images`
- Media: `/api/v1/media/image-upload/{filename}`, `/image-output/{filename}`, `/image-crop/{request_id}/{filename}`

Controller file: `backend/vms_api/controllers/image_feature_controller.py`.
Service file: `backend/vms_services/services/image_feature_service.py`.

## Stage Details

| Stage | Input | Processing | Output | File | Failure cases | Status |
|---|---|---|---|---|---|---|
| Upload bind | multipart `file` | FastAPI `UploadFile` | stream handle | controller | validation 422 if missing | IMPLEMENTED |
| Extension/content type | `UploadFile` | `ImageFileValidator.validate_upload` | extension | `image_file_validator.py` | 400 unsupported extension/type | IMPLEMENTED AND VERIFIED |
| Stream persistence | file stream | 1 MB chunks, max 200 MB | `storage/uploads/images/{uuid}{ext}` | `_persist_upload_stream` | 413 over limit | IMPLEMENTED |
| Signature validation | first 16 bytes | checks JPEG/PNG/BMP/WEBP/TIFF magic, extension and declared type | verified MIME | `validate_signature` | 400 spoof/corrupt | IMPLEMENTED AND VERIFIED |
| Decode/large/TIFF | saved path | Pillow reads dimensions; TIFF or large image converted to bounded RGB thumbnail | BGR image, optional source preview JPEG | `_decode_saved_image` | 413 pixel cap, 500 preview write | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| Tiled inference | BGR image | if enabled and side >= `IMAGE_TILED_MIN_SIDE`, tiles with overlap | merged detections | `_detect_objects_tiled`, `_detect_adapter_tiled` | detector unavailable warning | IMPLEMENTED |
| YOLO ONNX | BGR image/tile | OpenCV DNN `readNetFromONNX`, letterbox, blob, forward | detections | `_detect_yolo_with_opencv` | model missing/unreadable warning | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| SkyDet | BGR image/tile | PyTorch checkpoint, MobileNetV3/PANet/FCOS decode | detections | `SkyDetDetector.detect` | model missing/unreadable warning | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| NMS | raw boxes | OpenCV `NMSBoxes` for YOLO/image; class-wise torch NMS in SkyDet | filtered detections | `_apply_global_nms`, `_postprocess_yolo_output`, `_nms_xyxy` | none explicit | IMPLEMENTED |
| Annotation | BGR image + boxes | OpenCV drawing, labels | `storage/outputs/image_features/{request_id}_detections.jpg` | `_save_annotated_image` | 500 write failure | IMPLEMENTED |
| Crops | detections/whole image | padding, JPEG quality | `storage/crops/images/{request_id}/...jpg` | `_save_crops`, `_save_whole_image_crop` | 500 write failure | IMPLEMENTED |
| Visual embedding | crop/query BGR | HSV histograms: 32 H + 32 S + 32 V, L2-normalized | 96-float embedding | `_generate_embedding` | none explicit | IMPLEMENTED |
| Memory persistence | crop embeddings | append JSON atomically | `storage/object_memory/image_memory.json` | `_append_memory_items` | JSON read errors ignored | IMPLEMENTED |
| Similar search | query embedding | cosine similarity, top-k | matches with `similarity_score` | `_search_memory_items` | empty memory => [] | IMPLEMENTED |
| VLM enrichment | image | not part of image feature service; cloud route can analyze uploaded images separately | cloud result | `cloud_ai_controller.py` | provider 502 | PARTIALLY CONNECTED |
| Cleanup | temp files | source/crop/history retained | none | N/A | storage growth | MISSING |

## Configurable Values

- `VMS_STORAGE_ROOT`, `VMS_HOST_STORAGE_ROOT`
- `IMAGE_TILED_DETECTION_ENABLED=true`
- `IMAGE_TILE_SIZE=1024`
- `IMAGE_TILE_OVERLAP_RATIO=0.25`
- `IMAGE_TILED_MIN_SIDE=1400`
- `IMAGE_MAX_INFERENCE_SIDE=2560`
- `IMAGE_MAX_SOURCE_PIXELS=300000000`
- `IMAGE_OUTPUT_JPEG_QUALITY=90`
- `IMAGE_CROP_JPEG_QUALITY=90`
- `YOLO_MODEL_PATH`
- `YOLO_INPUT_SIZE=640`
- `YOLO_CLASS_NAMES=airplane,boat,car,ship`
- `SKYDET_MODEL_PATH`

## Public Response Fields

Image feature responses expose `request_id`, `image_id`, `status`, `message`, source filename/URL, file size/type, detector model, annotated URL, dimensions, counts, model load status, detector warning, `detections`, `crops`, `memory_items`, and `matches`. Controllers remove keys ending in `_path`/`_paths`; service DTOs still contain path fields internally.

Detection item shape includes `detection_id`, `detector_model`, `class_id`, `class_name`, `confidence`, `bbox`, and optionally `annotated_image_url`.

Crop item shape includes crop filename/URL, class name, confidence, bbox, and detector metadata.

Memory item shape excludes `embedding` publicly.

## Request Examples

Crop test:

```bash
curl -X POST http://localhost:8000/api/v1/crops/test-image \
  -F "file=@sample.jpg" \
  -F "detector_model=yolo" \
  -F "crop_padding_pixels=8"
```

Detection and crop:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/detection-crops/test-image -Form @{
  file = Get-Item .\sample.jpg
  detector_model = "skydet"
  confidence_threshold = "0.25"
  iou_threshold = "0.45"
  crop_padding_pixels = "8"
}
```

Object-memory ingestion:

```bash
curl -X POST http://localhost:8000/api/v1/object-memory/ingest-image \
  -F "file=@sample.jpg" \
  -F "detector_model=yolo"
```

Similar-object search:

```bash
curl -X POST http://localhost:8000/api/v1/object-memory/search-image \
  -F "file=@query.jpg" \
  -F "top_k=5"
```

Cloud VLM image analysis:

```bash
curl -X POST http://localhost:8000/api/v1/cloud-ai/analyze-image \
  -F "file=@sample.jpg" \
  -F "provider=hybrid" \
  -F "agent_name=scene_understanding" \
  -F "detail=auto"
```

Large TIFF inference uses the same image endpoints; TIFF upload is accepted when extension/content/signature agree and dimensions are within `IMAGE_MAX_SOURCE_PIXELS`.

## Accuracy Notes

- ChromaDB is not used.
- Object memory is JSON, deterministic histogram embeddings, cosine similarity.
- Large/TIFF support is implemented in code and there are TIFF files in storage, but this audit did not run a fresh large-TIFF smoke request.
