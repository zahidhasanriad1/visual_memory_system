import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
  inject,
} from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { finalize, Subscription, timeout } from 'rxjs';

import { API_CONFIG } from '../../../core/config/api.config';
import { ImageFeatureApiService } from '../../../core/services/image-feature-api.service';
import {
  ImageFeatureBBox,
  ImageFeatureDetection,
  ImageFeatureRequestSettings,
  ImageFeatureResult,
} from '../../../core/types/image-features/image-feature.types';

type ImageFeatureAction =
  | 'crop'
  | 'detection'
  | 'detection-crop'
  | 'ingest-memory'
  | 'search-memory';

interface ResultInfoItem {
  label: string;
  value: string | number;
}

interface DetectorModelOption {
  value: ImageFeatureRequestSettings['detectorModel'];
  label: string;
}

@Component({
  selector: 'app-image-features-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './image-features-page.html',
  styleUrl: './image-features-page.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ImageFeaturesPageComponent implements OnInit, OnDestroy {
  private readonly fb = inject(FormBuilder);
  private readonly changeDetectorRef = inject(ChangeDetectorRef);
  private readonly imageFeatureApi = inject(ImageFeatureApiService);
  private readonly requestTimeoutMs = 180000;
  private readonly cachedResultKey = 'vms_x_last_image_feature_result';
  private activeRequestSubscription: Subscription | null = null;
  private pendingCacheHandle: number | null = null;
  private pendingCacheUsesIdleCallback = false;

  selectedFile: File | null = null;
  selectedFileName = 'No image selected';
  previewUrl: string | null = null;

  isLoading = false;
  activeAction: ImageFeatureAction | null = null;
  errorMessage: string | null = null;
  result: ImageFeatureResult | null = null;
  resultImageUrl: string | null = null;
  resultDetectorKey: ImageFeatureRequestSettings['detectorModel'] = 'yolo';
  resultDetectorLabel = 'YOLO';
  requestedDetectorLabel = 'YOLO';
  detectorMismatch = false;
  resultInfoItems: ResultInfoItem[] = [];
  topDetectionItems: ImageFeatureDetection[] = [];
  visibleCropItems: ImageFeatureResult['crops'] = [];
  visibleMemoryItemList: ImageFeatureResult['memory_items'] = [];
  visibleMatchItems: ImageFeatureResult['matches'] = [];

  readonly actionLabels: Record<ImageFeatureAction, string> = {
    crop: 'Test Crop',
    detection: 'Test Detection',
    'detection-crop': 'Detection Crops',
    'ingest-memory': 'Ingest Memory',
    'search-memory': 'Search Memory',
  };

  readonly detectorOptions: DetectorModelOption[] = [
    { value: 'yolo', label: 'YOLO' },
    { value: 'skydet', label: 'SkyDet' },
  ];

  readonly form = this.fb.nonNullable.group({
    detectorModel:
      this.fb.nonNullable.control<ImageFeatureRequestSettings['detectorModel']>('yolo'),
    confidenceThreshold: 0.25,
    iouThreshold: 0.45,
    cropPaddingPixels: 8,
    topK: 5,
  });

  ngOnInit(): void {
    this.restoreCachedResult();
  }

  ngOnDestroy(): void {
    this.cancelActiveRequest();
    this.cancelScheduledResultCache();
    this.revokeBlobPreviewUrl();
  }

  onFileSelected(event: Event): void {
    this.cancelActiveRequest();
    const input = event.target as HTMLInputElement;
    const file = input.files?.item(0);

    if (!file) {
      this.revokeBlobPreviewUrl();
      this.selectedFile = null;
      this.selectedFileName = 'No image selected';
      this.previewUrl = null;
      return;
    }

    this.selectedFile = file;
    this.selectedFileName = file.name;
    this.clearResult();
    this.errorMessage = null;
    sessionStorage.removeItem(this.cachedResultKey);

    this.revokeBlobPreviewUrl();

    this.previewUrl = URL.createObjectURL(file);
  }

  runAction(action: ImageFeatureAction): void {
    if (!this.selectedFile) {
      this.errorMessage = 'Please select an image first.';
      return;
    }

    this.cancelActiveRequest();
    this.isLoading = true;
    this.activeAction = action;
    this.errorMessage = null;
    this.clearResult();

    const settings = this.buildSettings();

    const request$ =
      action === 'crop'
        ? this.imageFeatureApi.testImageCrop(this.selectedFile, settings)
        : action === 'detection'
          ? this.imageFeatureApi.testImageDetection(this.selectedFile, settings)
          : action === 'detection-crop'
            ? this.imageFeatureApi.testImageDetectionCrops(this.selectedFile, settings)
            : action === 'ingest-memory'
              ? this.imageFeatureApi.ingestImageToMemory(this.selectedFile, settings)
              : this.imageFeatureApi.searchImageMemory(this.selectedFile, settings);

    this.activeRequestSubscription = request$
      .pipe(
        timeout({ first: this.requestTimeoutMs }),
        finalize(() => {
          this.activeRequestSubscription = null;
          this.isLoading = false;
          this.changeDetectorRef.markForCheck();
        })
      )
      .subscribe({
        next: (response) => {
          if (!response.success) {
            this.errorMessage = response.message;
            return;
          }

          const normalizedResult = this.applyResult(response.data, settings.detectorModel);
          this.scheduleResultCache(normalizedResult);
          this.changeDetectorRef.markForCheck();
        },
        error: (error) => {
          this.errorMessage =
            error?.name === 'TimeoutError'
              ? 'The backend is still taking too long. Try a smaller image or lower processing settings.'
              : error?.error?.detail?.message ||
                error?.error?.detail ||
                error?.error?.message ||
                error?.message ||
                'Image feature request failed.';
          this.changeDetectorRef.markForCheck();
        },
      });
  }

  private cancelActiveRequest(): void {
    const activeRequest = this.activeRequestSubscription;
    this.activeRequestSubscription = null;
    activeRequest?.unsubscribe();
    this.isLoading = false;
    this.activeAction = null;
  }

  get activeActionLabel(): string {
    return this.activeAction ? this.actionLabels[this.activeAction] : 'Processing';
  }

  mediaUrl(url: string | null | undefined): string | null {
    if (!url) {
      return null;
    }

    if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('blob:')) {
      return url;
    }

    if (url.startsWith('/')) {
      return `${API_CONFIG.mediaBaseUrl}${url}`;
    }

    return url;
  }

  confidencePercent(value: number | null | undefined): string {
    return `${Math.round((value ?? 0) * 100)}%`;
  }

  formatBytes(value: number | null | undefined): string {
    if (!value) {
      return 'n/a';
    }

    if (value < 1024) {
      return `${value} B`;
    }

    if (value < 1024 * 1024) {
      return `${(value / 1024).toFixed(1)} KB`;
    }

    return `${(value / 1024 / 1024).toFixed(1)} MB`;
  }

  bboxText(bbox: ImageFeatureBBox | null | undefined): string {
    if (!bbox) {
      return 'No bbox';
    }

    return `${bbox.x_min},${bbox.y_min} - ${bbox.x_max},${bbox.y_max}`;
  }

  bboxSizeText(bbox: ImageFeatureBBox | null | undefined): string {
    if (!bbox) {
      return 'Unknown size';
    }

    return `${Math.max(0, bbox.x_max - bbox.x_min)} x ${Math.max(0, bbox.y_max - bbox.y_min)} px`;
  }

  detectorLabel(model: string | null | undefined): string {
    return this.normalizeDetectorModel(model) === 'skydet' ? 'SkyDet' : 'YOLO';
  }

  private buildSettings(): ImageFeatureRequestSettings {
    return {
      detectorModel: this.form.controls['detectorModel'].value,
      confidenceThreshold: Number(this.form.controls['confidenceThreshold'].value),
      iouThreshold: Number(this.form.controls['iouThreshold'].value),
      cropPaddingPixels: Number(this.form.controls['cropPaddingPixels'].value),
      topK: Number(this.form.controls['topK'].value),
    };
  }

  private get totalOutputCount(): number {
    if (!this.result) {
      return 0;
    }

    return (
      this.result.detections.length +
      this.result.crops.length +
      this.result.memory_items.length +
      this.result.matches.length
    );
  }

  private cacheResult(result: ImageFeatureResult): void {
    try {
      sessionStorage.setItem(this.cachedResultKey, JSON.stringify(this.compactResult(result)));
    } catch {
      sessionStorage.removeItem(this.cachedResultKey);
    }
  }

  private scheduleResultCache(result: ImageFeatureResult): void {
    this.cancelScheduledResultCache();

    const save = () => {
      this.pendingCacheHandle = null;
      this.cacheResult(result);
    };

    if (typeof window.requestIdleCallback === 'function') {
      this.pendingCacheUsesIdleCallback = true;
      this.pendingCacheHandle = window.requestIdleCallback(save, { timeout: 1000 });
      return;
    }

    this.pendingCacheUsesIdleCallback = false;
    this.pendingCacheHandle = window.setTimeout(save, 0);
  }

  private cancelScheduledResultCache(): void {
    if (this.pendingCacheHandle === null) {
      return;
    }

    if (
      this.pendingCacheUsesIdleCallback &&
      typeof window.cancelIdleCallback === 'function'
    ) {
      window.cancelIdleCallback(this.pendingCacheHandle);
    } else {
      window.clearTimeout(this.pendingCacheHandle);
    }

    this.pendingCacheHandle = null;
  }

  private restoreCachedResult(): void {
    const cachedResult = sessionStorage.getItem(this.cachedResultKey);

    if (!cachedResult) {
      return;
    }

    try {
      const restoredResult = JSON.parse(cachedResult) as ImageFeatureResult;
      const normalizedResult = this.applyResult(restoredResult);
      this.selectedFileName = restoredResult.source_filename;
      this.previewUrl = this.mediaUrl(restoredResult.source_image_url);
      this.form.controls.detectorModel.setValue(
        this.normalizeDetectorModel(
          normalizedResult.requested_detector_model || normalizedResult.detector_model
        ),
        { emitEvent: false }
      );
    } catch {
      sessionStorage.removeItem(this.cachedResultKey);
    }
  }

  private revokeBlobPreviewUrl(): void {
    if (this.previewUrl?.startsWith('blob:')) {
      URL.revokeObjectURL(this.previewUrl);
    }
  }

  private compactResult(result: ImageFeatureResult): ImageFeatureResult {
    return {
      ...result,
      detections: result.detections.slice(0, 50),
      crops: result.crops.slice(0, 24),
      memory_items: result.memory_items.slice(0, 20),
      matches: result.matches.slice(0, 20),
    };
  }

  private applyResult(
    result: ImageFeatureResult,
    requestedDetector?: ImageFeatureRequestSettings['detectorModel']
  ): ImageFeatureResult {
    const normalizedResult = this.normalizeResult(result, requestedDetector);
    const firstAnnotatedDetection = normalizedResult.detections.find(
      (item) => item.annotated_image_url
    );
    const annotatedImageUrl =
      normalizedResult.annotated_image_url || firstAnnotatedDetection?.annotated_image_url;
    const requestedDetectorKey =
      normalizedResult.requested_detector_model ||
      this.normalizeDetectorModel(normalizedResult.detector_model);
    const reportedDetectorKey = this.normalizeDetectorModel(normalizedResult.detector_model);

    this.result = normalizedResult;
    this.resultDetectorKey = reportedDetectorKey;
    this.resultDetectorLabel = this.detectorLabel(reportedDetectorKey);
    this.requestedDetectorLabel = this.detectorLabel(requestedDetectorKey);
    this.detectorMismatch = requestedDetectorKey !== reportedDetectorKey;
    this.resultImageUrl =
      this.mediaUrl(annotatedImageUrl) || this.mediaUrl(normalizedResult.source_image_url);
    this.topDetectionItems = [...normalizedResult.detections]
      .sort((a, b) => b.confidence - a.confidence)
      .slice(0, 12);
    this.visibleCropItems = normalizedResult.crops.slice(0, 24);
    this.visibleMemoryItemList = normalizedResult.memory_items.slice(0, 20);
    this.visibleMatchItems = normalizedResult.matches.slice(0, 20);
    this.resultInfoItems = this.buildResultInfo(normalizedResult);

    return normalizedResult;
  }

  private clearResult(): void {
    this.cancelScheduledResultCache();
    this.result = null;
    this.resultImageUrl = null;
    this.resultInfoItems = [];
    this.topDetectionItems = [];
    this.visibleCropItems = [];
    this.visibleMemoryItemList = [];
    this.visibleMatchItems = [];
  }

  private buildResultInfo(result: ImageFeatureResult): ResultInfoItem[] {
    return [
      { label: 'Request ID', value: result.request_id },
      { label: 'Image ID', value: result.image_id || result.request_id },
      {
        label: 'Requested detector',
        value: this.detectorLabel(result.requested_detector_model || result.detector_model),
      },
      { label: 'Backend detector', value: this.detectorLabel(result.detector_model) },
      { label: 'Model state', value: result.model_loaded ? 'Loaded' : 'Not loaded' },
      { label: 'Processed', value: result.processed_image_count ?? 1 },
      { label: 'Detections', value: result.total_detection_count ?? result.detections.length },
      { label: 'Crops', value: result.total_crop_count ?? result.crops.length },
      {
        label: 'Memory',
        value: result.total_memory_item_count ?? result.memory_items.length,
      },
      { label: 'Matches', value: result.total_match_count ?? result.matches.length },
      { label: 'Outputs', value: result.total_output_count ?? this.totalOutputCount },
      { label: 'Size', value: `${result.width} x ${result.height}` },
      {
        label: 'Source size',
        value: `${result.source_width ?? result.width} x ${result.source_height ?? result.height}`,
      },
      { label: 'Large-image mode', value: result.inference_scaled ? 'Optimized preview' : 'Native' },
      { label: 'File', value: result.source_filename },
      { label: 'Type', value: result.content_type || 'n/a' },
      { label: 'Bytes', value: this.formatBytes(result.file_size_bytes) },
    ];
  }

  private normalizeResult(
    result: ImageFeatureResult,
    requestedDetector?: ImageFeatureRequestSettings['detectorModel']
  ): ImageFeatureResult {
    return {
      ...result,
      detector_model: this.normalizeDetectorModel(result.detector_model),
      // Keep the submitted value separately so the UI can identify a backend
      // attribution mismatch without rewriting what the backend reported.
      requested_detector_model:
        requestedDetector ||
        result.requested_detector_model ||
        this.normalizeDetectorModel(result.detector_model),
      detections: Array.isArray(result.detections) ? result.detections : [],
      crops: Array.isArray(result.crops) ? result.crops : [],
      memory_items: Array.isArray(result.memory_items) ? result.memory_items : [],
      matches: Array.isArray(result.matches) ? result.matches : [],
    };
  }

  private normalizeDetectorModel(
    model: string | null | undefined
  ): ImageFeatureRequestSettings['detectorModel'] {
    const normalized = (model || '').trim().toLowerCase().replace(/[_\s-]+/g, '');
    return normalized === 'skydet' ? 'skydet' : 'yolo';
  }

}
