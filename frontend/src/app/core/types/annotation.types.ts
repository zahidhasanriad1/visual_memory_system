export interface AnnotationProject {
  id: string;
  name: string;
  description: string | null;
  status: string;
}

export interface AnnotationTask {
  id: string;
  project_id: string;
  source_type: string;
  source_path?: string | null;
  source_url: string | null;
  status: string;
  frame_number: number | null;
}

export interface AnnotationObject {
  id: string;
  task_id: string;
  label: string;
  x_min: number;
  y_min: number;
  x_max: number;
  y_max: number;
  geometry_type: 'box' | 'polygon';
  points: number[][];
  status: string;
}

export interface AnnotationObjectCreateRequest {
  task_id: string;
  label: string;
  geometry_type: 'box' | 'polygon';
  x_min: number;
  y_min: number;
  x_max: number;
  y_max: number;
  points: number[][];
}
