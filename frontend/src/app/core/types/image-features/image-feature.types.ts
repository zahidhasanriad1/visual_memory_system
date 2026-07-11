export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export interface ImageFeatureBBox {
  x_min: number;
  y_min: number;
  x_max: number;
  y_max: number;
}

export interface ImageFeatureDetection {
  detection_id: string;
  class_id: number | null;
  class_name: string;
  confidence: number;
  bbox: ImageFeatureBBox;
  annotated_image_url?: string | null;
}

export interface ImageFeatureCrop {
  crop_id: string;
  detection_id: string | null;
  class_id: number | null;
  class_name: string;
  confidence: number;
  bbox: ImageFeatureBBox;
  crop_url: string | null;
  crop_padding_pixels?: number;
}

export interface ImageFeatureMemoryItem {
  memory_id: string;
  source_request_id: string;
  source_filename: string;
  source_image_url?: string | null;
  crop_url?: string | null;
  class_name: string;
  confidence: number;
  bbox: ImageFeatureBBox | null;
  similarity_score?: number;
}

export interface ImageFeatureResult {
  request_id: string;
  image_id?: string;
  status: string;
  message: string;

  source_filename: string;
  source_image_url: string | null;
  annotated_image_url?: string | null;
  file_size_bytes?: number | null;
  content_type?: string | null;
  detector_model: 'yolo' | 'skydet' | string;
  requested_detector_model?: 'yolo' | 'skydet';

  width: number;
  height: number;
  source_width?: number | null;
  source_height?: number | null;
  inference_scaled?: boolean;
  processed_image_count?: number;
  total_detection_count?: number;
  total_crop_count?: number;
  total_memory_item_count?: number;
  total_match_count?: number;
  total_output_count?: number;

  model_loaded: boolean;
  detector_warning: string | null;

  detections: ImageFeatureDetection[];
  crops: ImageFeatureCrop[];
  memory_items: ImageFeatureMemoryItem[];
  matches: ImageFeatureMemoryItem[];
}

export interface ImageFeatureDashboardItem {
  request_id: string;
  operation: string | null;
  source_filename: string;
  source_image_url: string;
  file_size_bytes: number;
  updated_at: string;
  annotated_image_url: string | null;
  crop_image_urls: string[];
  image_kinds: string[];
  class_names: string[];
  crop_count: number;
  detection_count: number;
  memory_item_count: number;
  best_confidence: number | null;
}

export interface ImageFeatureDashboardResult {
  total_count: number;
  source_image_count: number;
  annotated_image_count: number;
  crop_image_count: number;
  detection_count: number;
  memory_item_count: number;
  items: ImageFeatureDashboardItem[];
}

export interface ImageFeatureRequestSettings {
  detectorModel: 'yolo' | 'skydet';
  confidenceThreshold: number;
  iouThreshold: number;
  cropPaddingPixels: number;
  topK: number;
}
