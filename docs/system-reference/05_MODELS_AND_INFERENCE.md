# Models And Inference

## Model Artifacts Found

`backend/storage/models` contains:

- `skysealand_yolo12m_best.onnx` - 80,611,413 bytes
- `skydet_skysealand_best.pt` - 5,095,373 bytes
- `skydet_best.pt` - 5,095,373 bytes
- `skydet_skysealand_run_metrics.json` - 14,830 bytes

Presence was verified by filesystem listing. Loading/inference accuracy was not smoke-tested during this audit.

## YOLO Image Path

File: `backend/vms_services/services/image_feature_service.py`.

- Uses OpenCV DNN `cv2.dnn.readNetFromONNX`.
- Default path: `storage/models/skysealand_yolo12m_best.onnx` or `YOLO_MODEL_PATH`.
- Input size: `YOLO_INPUT_SIZE`, default 640.
- Class names: `YOLO_CLASS_NAMES`, default `airplane,boat,car,ship`.
- Preprocess: letterbox, `blobFromImage`, scale `1/255`, RGB swap.
- Postprocess: confidence threshold, IOU threshold, `cv2.dnn.NMSBoxes`.
- Tiling: enabled by default for max side >= 1400, tile size 1024, overlap 25%.
- Missing artifact behavior: returns empty detections with detector warning.

Status: IMPLEMENTED BUT NOT RUNTIME-VERIFIED.

## YOLO Video Path

File: `backend/vms_utils/ai/yolo_detector.py`.

- Uses Ultralytics `YOLO`.
- Lazy loads model from `settings.yolo_model_path`.
- Calls `.predict(frame, conf, iou, max_det)`.
- Returns `DetectedObject` dataclasses.
- Missing artifact behavior: returns empty detections and sets `load_error`.

Status: IMPLEMENTED BUT NOT RUNTIME-VERIFIED.

## SkyDet

File: `backend/vms_utils/ai/skydet_detector.py`.

- Custom PyTorch model: MobileNetV3 small backbone, PANet neck, FCOS-style head.
- Config class names: `airplane, boat, car, ship`.
- Image size: 640.
- Device: `cuda` if available, else `cpu`.
- Loads checkpoint from `SKYDET_MODEL_PATH`.
- Uses AMP only on CUDA.
- Decode: sigmoid class scores times centerness, pre-NMS top-k 3000, per-class NMS.
- Box expansion: `SKYDET_BOX_EXPANSION_RATIO`, default 0.08, capped at 0.25.
- Missing artifact behavior: returns empty detections and sets `load_error`.

Status: IMPLEMENTED BUT NOT RUNTIME-VERIFIED.

## Model Registry

Endpoints:

- `POST /api/v1/model-registry/models`
- `GET /api/v1/model-registry/models`
- `POST /api/v1/model-registry/models/{model_id}/activate`

The registry stores rows in `model_versions`. Activation archives other rows of the same `model_type` and marks the selected row active. It does not copy files or reload detectors in `ModelRegistryService`; detector reloading/copying happens only after training completion in `TrainingService._register_trained_model`.

Status: PARTIALLY IMPLEMENTED.

## Training Integration

- YOLO training uses Ultralytics base model from `YOLO_TRAIN_BASE_MODEL`, default `yolo11n.pt`, then exports ONNX.
- SkyDet training calls `train_skydet`.
- Completed training registers active `ModelVersionEntity`, archives prior same-type models, copies active artifact to configured path, and reloads singleton image service if already instantiated.

Status: IMPLEMENTED BUT NOT RUNTIME-VERIFIED.

## Performance Measurements

No runtime latency, FPS, throughput, mAP, precision, recall, or hardware performance was measured in this audit. Existing SkyDet metrics JSON was found, but its contents were not treated as current verified benchmark results.
