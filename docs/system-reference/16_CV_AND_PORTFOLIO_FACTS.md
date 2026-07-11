# CV And Portfolio Facts

## Verified Facts

- Built a FastAPI and Angular visual memory prototype with image detection/cropping, video detection/tracking jobs, annotation, training orchestration, model registry, and cloud AI provider routing.
- Implemented robust image upload validation with extension, declared MIME, byte signature, size, and pixel checks.
- Implemented large-image/TIFF bounded preview handling in code.
- Integrated YOLO ONNX inference for image routes using OpenCV DNN.
- Implemented a custom SkyDet PyTorch detector architecture and adapter.
- Implemented deterministic local visual memory search using 96-dimensional HSV histogram embeddings stored in JSON.
- Implemented human annotation with bounding boxes and polygons, approval/rejection, dynamic labels, YOLO labels, and COCO-like `annotations.json` export.
- Implemented cloud AI provider adapters for Hugging Face, Gemini, OpenAI Responses API, and hybrid fallback routing.
- Implemented frontend pages for dashboard, image features, video memory, cloud AI, annotation, adaptive review, training, and model registry.
- Backend tests pass: 29/29.
- Angular production build succeeds.

## Example Values

- Default classes: `airplane`, `boat`, `car`, `ship`.
- Default image threshold values: confidence `0.25`, IoU `0.45`.
- Default YOLO input size: `640`.
- Default image tile size: `1024`, overlap `0.25`.
- Default cloud hybrid order: `huggingface,gemini,openai`.

## Unverified Claims

- Any mAP, precision, recall, or accuracy number.
- Real-time video FPS.
- GPU acceleration in the audited environment.
- Live Hugging Face/Gemini/OpenAI provider success.
- Successful end-to-end custom training completion in this audit.
- Production security readiness.

## Planned Or Missing Features

- Ollama local VLM integration.
- ChromaDB/vector database memory.
- Original audio preservation in reconstructed videos.
- Video list/get/delete/retry/timeline endpoints.
- Backend-wide role authorization.
- Retention cleanup.
- Alembic migrations.

## Safe CV Wording

"Developed VMS-X, a FastAPI + Angular visual-memory prototype with validated image ingestion, YOLO/SkyDet detection adapters, object cropping, local similarity search, video tracking jobs, annotation and dataset export workflows, custom training orchestration, model registry records, and hybrid cloud-AI agent routing. Verified 29 backend tests passing and a successful Angular production build."
