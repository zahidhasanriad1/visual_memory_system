# Visual Memory

## Image Visual Memory

Status: IMPLEMENTED AND VERIFIED BY TESTS.

File: `backend/vms_services/services/image_feature_service.py`.

Implementation:

- Embedding provider: local deterministic OpenCV histogram, not ML embedding model.
- Dimensions: 96 floats: 32-bin HSV H, 32-bin HSV S, 32-bin HSV V.
- Normalization: L2 norm.
- Persistence path: `storage/object_memory/image_memory.json`.
- ID generation: `uuid.uuid4()`.
- Stored metadata: `memory_id`, `source_request_id`, source filename/path/URL, crop path/URL, detector model, class name, confidence, bbox, embedding.
- Similarity metric: cosine similarity.
- Top-k: `max(1, top_k)`, sorted descending.
- Filtering: no class/date/source filters implemented.
- Cleanup/retention: none implemented.
- Public response: embedding removed by `_public_memory_item`.

## Video Visual Memory

Status: PARTIALLY IMPLEMENTED.

`VideoMemoryService` creates crop files and per-object `memory_id` values in report JSON when `enable_memory_storage=true`, but no ChromaDB, vector index, SQL `VisualMemoryEntity` insert, or searchable video memory endpoint was found.

## ChromaDB

Status: MISSING.

No `chromadb` dependency, collection creation, persistence path, or query API was found.

## Linkage

- Image memory links to source request ID, source image URL, crop URL, detector class, confidence, and bbox.
- Video report objects link track ID, frame number, timestamp, crop path, and bbox, but not into the image memory JSON or SQL visual memory table.
- VLM metadata is not joined into image memory ingestion; cloud AI analysis is a separate endpoint.
