import json
import shutil
import uuid
from collections import defaultdict
from pathlib import Path
import cv2
from sqlalchemy.ext.asyncio import AsyncSession
from vms_api.appsettings import get_settings
from vms_domain.entities.video_entity import VideoEntity
from vms_domain.entities.video_job_entity import VideoJobEntity
from vms_models.dtos.video_memory.video_processing_settings_dto import VideoProcessingSettingsDto
from vms_utils.ai.skydet_detector import SkyDetDetector
from vms_utils.ai.yolo_detector import YoloDetector
from vms_utils.ai.byte_track_tracker import ByteTrackTracker
from vms_utils.exceptions.app_exception import AppException

class VideoMemoryService:
    """Full-timeline video memory orchestration service."""

    _ALLOWED_VIDEO_SUFFIXES = {".mp4", ".m4v", ".avi", ".mov", ".mkv", ".webm"}

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._settings = get_settings()
        self._detectors = {
            "yolo": YoloDetector(self._settings.yolo_model_path),
            "skydet": SkyDetDetector(self._settings.skydet_model_path),
        }

    async def create_job_async(self, file_bytes: bytes, filename: str, settings: VideoProcessingSettingsDto) -> dict:
        suffix = Path(filename).suffix.lower()
        if suffix not in self._ALLOWED_VIDEO_SUFFIXES:
            raise AppException("Unsupported video format.", data={"suffix": suffix})
        job_id = uuid.uuid4().hex
        source_dir = self._settings.upload_dir / "video_memory_sources"
        source_dir.mkdir(parents=True, exist_ok=True)
        source_path = source_dir / f"video_memory_source_{job_id}{suffix}"
        source_path.write_bytes(file_bytes)
        job = VideoJobEntity(id=job_id, status="queued", message="Video processing job created.")
        self._session.add(job)
        await self._session.commit()
        return {"job_id": job_id, "status": job.status, "message": job.message, "source_video_path": str(source_path), "settings": settings.model_dump(mode="json")}

    async def process_job_async(self, job_id: str, source_video_path: str, original_filename: str, settings: VideoProcessingSettingsDto) -> None:
        job = await self._session.get(VideoJobEntity, job_id)
        if not job:
            return
        try:
            job.status = "running"; job.message = "Processing video."; job.progress_percent = 1.0
            await self._session.commit()
            result = await self.ingest_video_from_path_async(Path(source_video_path), original_filename, settings, job_id)
            job.status = "completed"; job.progress_percent = 100.0; job.message = "Video processing completed."; job.video_id = result["video_id"]; job.result_report_path = result.get("video_report_path")
            await self._session.commit()
        except Exception as error:
            job.status = "failed"; job.error = str(error); job.message = "Video processing failed."
            await self._session.commit()

    async def get_job_status_async(self, job_id: str) -> dict:
        job = await self._session.get(VideoJobEntity, job_id)
        if not job:
            raise AppException("Video job not found.", status_code=404)
        return {"job_id": job.id, "status": job.status, "progress_percent": job.progress_percent, "message": job.message, "result_available": bool(job.result_report_path), "error": job.error}

    async def get_job_result_async(self, job_id: str) -> dict:
        job = await self._session.get(VideoJobEntity, job_id)
        if not job or not job.result_report_path:
            raise AppException("Video job result not available.", status_code=404)
        return json.loads(Path(job.result_report_path).read_text(encoding="utf-8"))

    async def ingest_video_from_path_async(self, source_video_path: Path, original_filename: str, settings: VideoProcessingSettingsDto, forced_video_id: str | None = None) -> dict:
        if not source_video_path.exists():
            raise AppException("Video source file not found.", status_code=404)
        video_id = forced_video_id or uuid.uuid4().hex
        cap = cv2.VideoCapture(str(source_video_path))
        if not cap.isOpened():
            raise AppException("Could not open video file.")
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        duration = total_frames / fps if fps > 0 else 0.0

        video = VideoEntity(id=video_id, original_filename=original_filename, source_video_path=str(source_video_path), fps=fps, total_video_frames=total_frames, duration_seconds=duration, width=width, height=height)
        self._session.add(video)
        await self._session.commit()

        frame_dir = self._settings.frame_dir / "video_memory" / video_id
        tracked_frame_dir = self._settings.output_dir / "video_memory_tracked_frames" / video_id
        crop_dir = self._settings.crop_dir / "video_memory_objects" / video_id
        video_out_dir = self._settings.output_dir / "video_memory_videos"
        report_dir = self._settings.output_dir / "video_memory_reports"
        for d in [frame_dir, tracked_frame_dir, crop_dir, video_out_dir, report_dir]:
            d.mkdir(parents=True, exist_ok=True)

        output_fps = fps if settings.output_video_fps == 0.0 else settings.output_video_fps
        annotated_video_path = video_out_dir / f"annotated_{settings.detector_model}_{settings.processing_mode}_video_{video_id}.mp4"
        writer = None
        if settings.create_annotated_video and width > 0 and height > 0:
            writer = cv2.VideoWriter(str(annotated_video_path), cv2.VideoWriter_fourcc(*"mp4v"), output_fps, (width, height))

        tracker = ByteTrackTracker(iou_threshold=settings.tracker_iou_threshold)
        frames: list[dict] = []
        objects: list[dict] = []
        track_stats: dict[str, dict] = {}
        processed_count = 0
        total_detection_count = 0
        total_stored = 0
        frame_number = 0
        next_sample_time = 0.0

        while True:
            ok, frame = cap.read()
            if not ok:
                break
            timestamp = frame_number / fps if fps else 0.0
            should_process = self._should_process_frame(settings, frame_number, timestamp, next_sample_time)
            if should_process and settings.processing_mode in {"timeline_sampled", "fast_sampled"}:
                next_sample_time = timestamp + settings.sample_every_seconds
            tracked_frame = frame.copy()
            frame_detection_count = 0
            frame_tracked_count = 0
            frame_stored_count = 0
            if should_process:
                detector = self._detectors.get(settings.detector_model, self._detectors["yolo"])
                detections = detector.detect(frame, settings.confidence_threshold, settings.iou_threshold, settings.max_detections_per_frame)
                tracked = tracker.update(detections)
                frame_detection_count = len(detections)
                frame_tracked_count = len(tracked)
                total_detection_count += len(detections)
                for item in tracked:
                    det = item.detection
                    color = (0, 255, 0)
                    cv2.rectangle(tracked_frame, (int(det.x_min), int(det.y_min)), (int(det.x_max), int(det.y_max)), color, 2)
                    cv2.putText(tracked_frame, f"{item.track_id} {det.class_name} {det.confidence:.2f}", (int(det.x_min), max(20, int(det.y_min)-8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
                    crop_path = None
                    memory_id = None
                    memory_action = "not_stored"
                    if settings.enable_memory_storage:
                        crop = frame[max(0,int(det.y_min)-settings.crop_padding_pixels):min(height,int(det.y_max)+settings.crop_padding_pixels), max(0,int(det.x_min)-settings.crop_padding_pixels):min(width,int(det.x_max)+settings.crop_padding_pixels)]
                        if crop.size:
                            crop_path = crop_dir / f"{item.track_id}_frame_{frame_number:08d}_{det.class_name}_{det.confidence:.3f}_{det.detection_id}.jpg"
                            cv2.imwrite(str(crop_path), crop)
                            memory_id = uuid.uuid4().hex
                            memory_action = "stored"
                            frame_stored_count += 1
                            total_stored += 1
                    obj = {"track_id": item.track_id, "detection_id": det.detection_id, "memory_id": memory_id, "memory_action": memory_action, "frame_number": frame_number, "frame_timestamp_seconds": round(timestamp, 4), "frame_image_path": "", "class_id": det.class_id, "class_name": det.class_name, "confidence": round(det.confidence, 6), "crop_path": str(crop_path) if crop_path else None, "x_min": det.x_min, "y_min": det.y_min, "x_max": det.x_max, "y_max": det.y_max}
                    objects.append(obj)
                    self._update_track_stats(track_stats, item.track_id, det, frame_number, timestamp)
                frame_image_path = frame_dir / f"frame_{frame_number:08d}_{timestamp:.2f}s.jpg"
                tracked_image_path = tracked_frame_dir / f"tracked_frame_{video_id}_{frame_number:08d}.jpg"
                cv2.imwrite(str(frame_image_path), frame)
                cv2.imwrite(str(tracked_image_path), tracked_frame)
                for obj in objects[-frame_tracked_count:]:
                    obj["frame_image_path"] = str(frame_image_path)
                frames.append({"frame_number": frame_number, "frame_timestamp_seconds": round(timestamp, 4), "frame_image_path": str(frame_image_path), "tracked_annotated_image_path": str(tracked_image_path), "detection_count": frame_detection_count, "tracked_object_count": frame_tracked_count, "stored_object_count": frame_stored_count})
                processed_count += 1
            if writer is not None:
                writer.write(tracked_frame)
            frame_number += 1
            if settings.max_frames > 0 and processed_count >= settings.max_frames:
                break
            if frame_number % 30 == 0:
                await self._update_running_job_progress(video_id, frame_number, total_frames)

        cap.release()
        if writer is not None:
            writer.release()
        tracks = self._finalize_tracks(track_stats)
        result = {"video_id": video_id, "source_video_path": str(source_video_path), "original_filename": original_filename, "detector_model": settings.detector_model, "processing_mode": settings.processing_mode, "fps": round(fps, 4), "total_video_frames": total_frames, "duration_seconds": round(duration, 4), "processed_frame_count": processed_count, "total_detection_count": total_detection_count, "total_tracked_object_count": len(objects), "total_stored_object_count": total_stored, "collection_name": "visual_object_memory", "video_report_path": None, "annotated_video_path": str(annotated_video_path) if writer is not None else None, "frames": frames, "objects": objects, "tracks": tracks}
        report_path = report_dir / f"video_memory_report_{video_id}.json"
        result["video_report_path"] = str(report_path)
        report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result

    def _should_process_frame(self, settings: VideoProcessingSettingsDto, frame_number: int, timestamp: float, next_sample_time: float) -> bool:
        if settings.processing_mode == "full_video":
            return True
        if settings.processing_mode == "timeline_sampled":
            return timestamp + 1e-6 >= next_sample_time
        if settings.processing_mode == "fast_sampled":
            return timestamp + 1e-6 >= next_sample_time
        return True

    async def _update_running_job_progress(self, video_id: str, frame_number: int, total_frames: int) -> None:
        job = await self._session.get(VideoJobEntity, video_id)
        if job and total_frames:
            job.progress_percent = min(99.0, (frame_number / total_frames) * 100.0)
            job.message = f"Processing frame {frame_number}/{total_frames}."
            await self._session.commit()

    def _update_track_stats(self, stats: dict, track_id: str, det, frame_number: int, timestamp: float) -> None:
        if track_id not in stats:
            stats[track_id] = {"track_id": track_id, "class_id": det.class_id, "class_name": det.class_name, "first_seen_frame": frame_number, "last_seen_frame": frame_number, "first_seen_seconds": timestamp, "last_seen_seconds": timestamp, "seen_frame_count": 0, "confidence_sum": 0.0, "best_confidence": 0.0, "last_box": {}}
        s = stats[track_id]
        s["last_seen_frame"] = frame_number; s["last_seen_seconds"] = timestamp; s["seen_frame_count"] += 1; s["confidence_sum"] += det.confidence; s["best_confidence"] = max(s["best_confidence"], det.confidence); s["last_box"] = {"x_min": det.x_min, "y_min": det.y_min, "x_max": det.x_max, "y_max": det.y_max}

    def _finalize_tracks(self, stats: dict) -> list[dict]:
        tracks = []
        for s in stats.values():
            avg = s["confidence_sum"] / max(1, s["seen_frame_count"])
            tracks.append({"track_id": s["track_id"], "class_id": s["class_id"], "class_name": s["class_name"], "first_seen_frame": s["first_seen_frame"], "last_seen_frame": s["last_seen_frame"], "first_seen_seconds": round(s["first_seen_seconds"], 4), "last_seen_seconds": round(s["last_seen_seconds"], 4), "seen_frame_count": s["seen_frame_count"], "average_confidence": round(avg, 6), "best_confidence": round(s["best_confidence"], 6), "last_box": s["last_box"]})
        return sorted(tracks, key=lambda x: x["track_id"])
