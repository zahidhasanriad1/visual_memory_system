import { CommonModule, DecimalPipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { finalize, switchMap, takeWhile, timer } from 'rxjs';

import { VideoMemoryService } from '../../../../core/services/video-memory.service';
import { ToasterService } from '../../../../core/services/toaster.service';
import {
  VideoJobStatus,
  VideoMemoryResult,
  VideoProcessingSettings,
} from '../../../../core/types/video-memory.type';

interface VideoModeOption {
  value: VideoProcessingSettings['processing_mode'];
  label: string;
}

interface DetectorModelOption {
  value: VideoProcessingSettings['detector_model'];
  label: string;
}

@Component({
  selector: 'app-video-memory',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, DecimalPipe],
  templateUrl: './video-memory.component.html',
  styleUrl: './video-memory.component.scss',
})
export class VideoMemoryComponent {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(VideoMemoryService);
  private readonly toast = inject(ToasterService);

  file: File | null = null;
  fileName = 'No video selected';
  status: VideoJobStatus | null = null;
  result: VideoMemoryResult | null = null;
  isStarting = false;

  readonly modeOptions: VideoModeOption[] = [
    { value: 'full_video', label: 'Full video' },
    { value: 'timeline_sampled', label: 'Timeline sampled' },
    { value: 'fast_sampled', label: 'Fast preview' },
  ];

  readonly detectorOptions: DetectorModelOption[] = [
    { value: 'yolo', label: 'YOLO' },
    { value: 'skydet', label: 'SkyDet' },
  ];

  readonly form = this.fb.nonNullable.group({
    detector_model: 'yolo' as const,
    processing_mode: 'full_video' as const,
    sample_every_seconds: 1,
    max_frames: 0,
    confidence_threshold: 0.25,
    iou_threshold: 0.45,
    max_detections_per_frame: 50,
    tracker_iou_threshold: 0.3,
    crop_padding_pixels: 8,
    enable_memory_storage: true,
    enable_duplicate_pruning: true,
    create_annotated_video: true,
    output_video_fps: 0,
    save_detector_annotated_image: false,
  });

  pick(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.file = input.files?.item(0) ?? null;
    this.fileName = this.file?.name ?? 'No video selected';
    this.status = null;
    this.result = null;
  }

  start(): void {
    if (!this.file) {
      this.toast.show('error', 'Choose a video first.');
      return;
    }

    this.isStarting = true;
    this.status = null;
    this.result = null;

    const settings = this.form.getRawValue() as VideoProcessingSettings;

    this.api
      .createJob(this.file, settings)
      .pipe(finalize(() => (this.isStarting = false)))
      .subscribe({
        next: (response) => {
          this.toast.show('success', 'Video memory job started.');
          this.watchJob(response.data.job_id);
        },
        error: (error) => {
          this.toast.show('error', error?.error?.message || 'Video memory job failed.');
        },
      });
  }

  private watchJob(jobId: string): void {
    timer(0, 1000)
      .pipe(
        switchMap(() => this.api.status(jobId)),
        takeWhile(
          (statusResponse) =>
            statusResponse.data.status !== 'completed' &&
            statusResponse.data.status !== 'failed',
          true
        )
      )
      .subscribe((statusResponse) => {
        this.status = statusResponse.data;

        if (statusResponse.data.status === 'completed') {
          this.loadResult(jobId);
        }
      });
  }

  private loadResult(jobId: string): void {
    this.api.result(jobId).subscribe({
      next: (response) => {
        this.result = response.data;
      },
      error: (error) => {
        this.toast.show('error', error?.error?.message || 'Unable to load video result.');
      },
    });
  }
}
