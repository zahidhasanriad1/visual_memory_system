import { ImageFeatureDashboardItem } from '../../../../core/types/image-features/image-feature.types';

export type ImageHistoryFilter = 'all' | 'source' | 'detection' | 'crop' | 'memory';

export interface DashboardCard {
  title: string;
  value: string;
  roles: string[];
}

export interface DashboardModule {
  path: string;
  title: string;
  status: string;
  roles: string[];
}

export interface ImageHistoryFilterOption {
  label: string;
  value: ImageHistoryFilter;
}

export interface ImageDashboardState {
  total_count: number;
  source_image_count: number;
  annotated_image_count: number;
  crop_image_count: number;
  detection_count: number;
  memory_item_count: number;
  items: ImageFeatureDashboardItem[];
}
