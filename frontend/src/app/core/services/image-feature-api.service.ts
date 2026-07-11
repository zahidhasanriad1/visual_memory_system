import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import {
  ApiResponse,
  ImageFeatureDashboardResult,
  ImageFeatureRequestSettings,
  ImageFeatureResult,
} from '../types/image-features/image-feature.types';
import { Observable } from 'rxjs';
import { API_CONFIG } from '../config/api.config';

@Injectable({
  providedIn: 'root',
})
export class ImageFeatureApiService {
  private readonly apiBaseUrl = API_CONFIG.baseUrl;

  constructor(private readonly http: HttpClient) {}

  getDashboardImages(limit = 50): Observable<ApiResponse<ImageFeatureDashboardResult>> {
    return this.http.get<ApiResponse<ImageFeatureDashboardResult>>(
      `${this.apiBaseUrl}/image-features/dashboard-images`,
      {
        params: {
          limit,
        },
      }
    );
  }

  testImageCrop(
    file: File,
    settings: ImageFeatureRequestSettings
  ): Observable<ApiResponse<ImageFeatureResult>> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('detector_model', settings.detectorModel);
    formData.append('crop_padding_pixels', String(settings.cropPaddingPixels));

    return this.http.post<ApiResponse<ImageFeatureResult>>(
      `${this.apiBaseUrl}/crops/test-image`,
      formData
    );
  }

  testImageDetection(
    file: File,
    settings: ImageFeatureRequestSettings
  ): Observable<ApiResponse<ImageFeatureResult>> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('detector_model', settings.detectorModel);
    formData.append('confidence_threshold', String(settings.confidenceThreshold));
    formData.append('iou_threshold', String(settings.iouThreshold));

    return this.http.post<ApiResponse<ImageFeatureResult>>(
      `${this.apiBaseUrl}/detections/test-image`,
      formData
    );
  }

  testImageDetectionCrops(
    file: File,
    settings: ImageFeatureRequestSettings
  ): Observable<ApiResponse<ImageFeatureResult>> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('detector_model', settings.detectorModel);
    formData.append('confidence_threshold', String(settings.confidenceThreshold));
    formData.append('iou_threshold', String(settings.iouThreshold));
    formData.append('crop_padding_pixels', String(settings.cropPaddingPixels));

    return this.http.post<ApiResponse<ImageFeatureResult>>(
      `${this.apiBaseUrl}/detection-crops/test-image`,
      formData
    );
  }

  ingestImageToMemory(
    file: File,
    settings: ImageFeatureRequestSettings
  ): Observable<ApiResponse<ImageFeatureResult>> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('detector_model', settings.detectorModel);
    formData.append('confidence_threshold', String(settings.confidenceThreshold));
    formData.append('iou_threshold', String(settings.iouThreshold));
    formData.append('crop_padding_pixels', String(settings.cropPaddingPixels));

    return this.http.post<ApiResponse<ImageFeatureResult>>(
      `${this.apiBaseUrl}/object-memory/ingest-image`,
      formData
    );
  }

  searchImageMemory(
    file: File,
    settings: ImageFeatureRequestSettings
  ): Observable<ApiResponse<ImageFeatureResult>> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('detector_model', settings.detectorModel);
    formData.append('top_k', String(settings.topK));

    return this.http.post<ApiResponse<ImageFeatureResult>>(
      `${this.apiBaseUrl}/object-memory/search-image`,
      formData
    );
  }
}
