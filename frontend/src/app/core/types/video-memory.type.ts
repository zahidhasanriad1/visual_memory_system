export interface VideoProcessingSettings {
  detector_model: 'yolo' | 'skydet';
  processing_mode: 'full_video' | 'timeline_sampled' | 'fast_sampled';
  sample_every_seconds: number;
  max_frames: number;
  confidence_threshold: number;
  iou_threshold: number;
  max_detections_per_frame: number;
  tracker_iou_threshold: number;
  crop_padding_pixels: number;
  enable_memory_storage: boolean;
  enable_duplicate_pruning: boolean;
  create_annotated_video: boolean;
  output_video_fps: number;
  save_detector_annotated_image: boolean;
}
export interface VideoJobResponse { job_id: string; status: string; message: string; source_video_path?: string; }
export interface VideoJobStatus { job_id: string; status: string; progress_percent: number; message: string; result_available: boolean; error?: string | null; }
export interface VideoMemoryResult { video_id: string; original_filename: string; detector_model: string; processing_mode: string; fps: number; total_video_frames: number; duration_seconds: number; processed_frame_count: number; total_detection_count: number; total_tracked_object_count: number; total_stored_object_count: number; annotated_video_path?: string | null; }
