# Video Pipeline

Controller: `backend/vms_api/controllers/video_memory_controller.py`.
Service: `backend/vms_services/services/video_memory_service.py`.

## Registered Endpoints

| Requested capability | Implemented endpoint | Status |
|---|---|---|
| upload video | `POST /api/v1/video-memory/jobs/ingest-video` | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| list videos | none | MISSING |
| get video record | none | MISSING |
| process video | background task after upload | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| get processing status | `GET /api/v1/video-memory/jobs/{job_id}` | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| get timeline | no dedicated endpoint; tracks/frames in result report | PARTIALLY IMPLEMENTED |
| get output video | `GET /api/v1/media/video/{filename}` | IMPLEMENTED BUT NOT RUNTIME-VERIFIED |
| retry processing | none | MISSING |
| delete video | none | MISSING |

## Pipeline Trace

1. `create_video_job` reads entire upload bytes into memory.
2. `VideoMemoryService.create_job_async` validates suffix in `.mp4,.m4v,.avi,.mov,.mkv,.webm`.
3. Source file is written to `settings.upload_dir / "video_memory_sources" / f"video_memory_source_{job_id}{suffix}"`.
4. A `VideoJobEntity` row is created with `status="queued"`.
5. FastAPI `BackgroundTasks` calls `process_job_async`.
6. Job status changes to `running`, progress `1.0`.
7. `ingest_video_from_path_async` opens OpenCV `VideoCapture`.
8. Metadata extracted: FPS, frame count, width, height, duration.
9. `VideoEntity` is inserted.
10. Frame/crop/output/report folders are created.
11. `VideoWriter` writes `mp4v` annotated video when enabled and dimensions are available.
12. For each frame, `_should_process_frame` decides full or sampled processing.
13. Detector selected by `settings.detector_model` (`YoloDetector` or `SkyDetDetector`).
14. `ByteTrackTracker` assigns stable track IDs like `{class}_track_001`.
15. Crops are written when `enable_memory_storage=true`.
16. Original frames and tracked frames are saved.
17. Per-object dictionaries and per-track stats are accumulated.
18. Progress is committed every 30 frames.
19. Writer/capture are released.
20. Result JSON is written to `storage/outputs/video_memory_reports/video_memory_report_{video_id}.json`.
21. Job status becomes `completed`, result path recorded.

## Naming Formats

- Source video: `video_memory_source_{job_id}{suffix}`
- Frame image: `frame_{frame_number:08d}_{timestamp:.2f}s.jpg`
- Tracked frame: `tracked_frame_{video_id}_{frame_number:08d}.jpg`
- Crop: `{track_id}_frame_{frame_number:08d}_{class_name}_{confidence:.3f}_{detection_id}.jpg`
- Annotated video: `annotated_{detector_model}_{processing_mode}_video_{video_id}.mp4`
- Report: `video_memory_report_{video_id}.json`

## FPS, Dimensions, Codec

- Source FPS read from OpenCV, default fallback 25.0.
- Output FPS is source FPS unless `output_video_fps` is nonzero.
- Output width/height match `CAP_PROP_FRAME_WIDTH/HEIGHT`.
- Output codec is OpenCV fourcc `mp4v`.
- Original audio is not preserved; no ffmpeg/moviepy/audio pipeline exists.

## Status Transitions

- `queued`: created in `create_job_async`.
- `running`: set by `process_job_async`.
- `completed`: set after report generation.
- `failed`: set on exception, with `error=str(error)`.

## Result Fields

`get_job_status_async` returns `job_id`, `status`, `progress_percent`, `message`, `result_available`, `error`.

Result report contains `video_id`, `source_video_path`, `original_filename`, `detector_model`, `processing_mode`, `fps`, `total_video_frames`, `duration_seconds`, `processed_frame_count`, detection/tracking/storage counts, `collection_name`, `video_report_path`, `annotated_video_path`, `frames`, `objects`, `tracks`.

## Failure Recovery

Failures set job status to `failed`; there is no retry endpoint. Partial files are not cleaned up. If a job is missing, status returns 404. If no result path exists, result returns 404.

## Visual Memory And Cleanup

Video crops are stored, and `memory_id` values are generated in report objects, but no ChromaDB/vector store or SQL `VisualMemoryEntity` write was found in `VideoMemoryService`. Temporary frames/crops are retained; cleanup is missing.
