import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { finalize, timeout } from 'rxjs';

import { CloudAiApiService } from '../../../core/services/cloud-ai-api.service';
import {
  CloudAiAgent,
  CloudAiAgentName,
  CloudAiConnectivity,
  CloudAiHealth,
  CloudAiImageAnalysisResult,
  CloudAiProviderName,
  CloudAiTextSummaryResult,
} from '../../../core/types/cloud-ai/cloud-ai.types';

@Component({
  selector: 'app-cloud-ai-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './cloud-ai-page.html',
  styleUrl: './cloud-ai-page.scss',
})
export class CloudAiPageComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly cloudAiApi = inject(CloudAiApiService);
  private readonly requestTimeoutMs = 300000;

  selectedFile: File | null = null;
  selectedFileName = 'No image selected';
  previewUrl: string | null = null;

  health: CloudAiHealth | null = null;
  agents: CloudAiAgent[] = [];
  connectivity: CloudAiConnectivity[] = [];
  isConnectivityLoading = false;

  imageResult: CloudAiImageAnalysisResult | null = null;
  reportResult: CloudAiTextSummaryResult | null = null;

  isImageLoading = false;
  isReportLoading = false;
  errorMessage: string | null = null;

  readonly form = this.fb.nonNullable.group({
    provider: 'hybrid' as CloudAiProviderName,
    imageAgentName: 'scene_understanding' as CloudAiAgentName,
    reportAgentName: 'video_timeline_summary' as CloudAiAgentName,
    detail: 'auto',
    context: '',
    reportText: '',
  });

  ngOnInit(): void {
    this.loadHealth();
    this.loadAgents();
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.item(0);

    if (!file) {
      this.selectedFile = null;
      this.selectedFileName = 'No image selected';
      this.previewUrl = null;
      return;
    }

    this.selectedFile = file;
    this.selectedFileName = file.name;
    this.imageResult = null;
    this.errorMessage = null;

    if (this.previewUrl) {
      URL.revokeObjectURL(this.previewUrl);
    }

    this.previewUrl = URL.createObjectURL(file);
  }

  analyzeImage(): void {
    if (!this.selectedFile) {
      this.errorMessage = 'Please select an image first.';
      return;
    }

    this.isImageLoading = true;
    this.imageResult = null;
    this.errorMessage = null;

    this.cloudAiApi
      .analyzeImage(
        this.selectedFile,
        this.form.controls.provider.value,
        this.form.controls.imageAgentName.value,
        this.form.controls.context.value,
        this.form.controls.detail.value
      )
      .pipe(
        timeout({ first: this.requestTimeoutMs }),
        finalize(() => {
          this.isImageLoading = false;
        })
      )
      .subscribe({
        next: (response) => {
          if (!response.success) {
            this.errorMessage = response.message;
            return;
          }

          this.imageResult = response.data;
        },
        error: (error) => {
          this.errorMessage =
            error?.name === 'TimeoutError'
              ? 'The AI provider is still taking too long. Try another provider or a smaller image.'
              : error?.error?.detail?.message ||
                error?.error?.message ||
                error?.message ||
                'Cloud AI image analysis failed.';
        },
      });
  }

  summarizeReport(): void {
    const reportText = this.form.controls.reportText.value.trim();

    if (!reportText) {
      this.errorMessage = 'Please paste a video report or text first.';
      return;
    }

    this.isReportLoading = true;
    this.reportResult = null;
    this.errorMessage = null;

    this.cloudAiApi
      .summarizeReport(
        reportText,
        this.form.controls.provider.value,
        this.form.controls.reportAgentName.value,
        this.form.controls.context.value
      )
      .pipe(
        timeout({ first: this.requestTimeoutMs }),
        finalize(() => {
          this.isReportLoading = false;
        })
      )
      .subscribe({
        next: (response) => {
          if (!response.success) {
            this.errorMessage = response.message;
            return;
          }

          this.reportResult = response.data;
        },
        error: (error) => {
          this.errorMessage =
            error?.name === 'TimeoutError'
              ? 'The AI provider is still taking too long. Try another provider or shorter report text.'
              : error?.error?.detail?.message ||
                error?.error?.message ||
                error?.message ||
                'Cloud AI report summary failed.';
        },
      });
  }

  checkConnectivity(): void {
    this.isConnectivityLoading = true;
    this.errorMessage = null;
    this.cloudAiApi
      .checkConnectivity()
      .pipe(finalize(() => (this.isConnectivityLoading = false)))
      .subscribe({
        next: (response) => (this.connectivity = response.data ?? []),
        error: (error) => {
          this.errorMessage =
            error?.error?.detail?.message || error?.message || 'Provider check failed.';
        },
      });
  }

  private loadHealth(): void {
    this.cloudAiApi.getHealth().subscribe({
      next: (response) => {
        if (response.success) {
          this.health = response.data;
        }
      },
    });
  }

  parsedEntries(value: Record<string, unknown> | null | undefined): Array<{ key: string; value: string }> {
    if (!value) {
      return [];
    }

    return Object.entries(value).map(([key, item]) => ({
      key,
      value: this.formatValue(item),
    }));
  }

  formatValue(value: unknown): string {
    if (value === null || value === undefined) {
      return 'None';
    }

    if (Array.isArray(value)) {
      return value.map((item) => this.formatValue(item)).join(', ');
    }

    if (typeof value === 'object') {
      return JSON.stringify(value);
    }

    return String(value);
  }

  textValue(
    value: Record<string, unknown> | null | undefined,
    keys: string[],
    fallback = 'Not available'
  ): string {
    if (!value) {
      return fallback;
    }

    for (const key of keys) {
      const item = value[key];

      if (typeof item === 'string' && item.trim()) {
        return item.trim();
      }
    }

    return fallback;
  }

  listValue(value: Record<string, unknown> | null | undefined, key: string): string[] {
    const item = value?.[key];

    if (Array.isArray(item)) {
      return item.map((entry) => this.formatValue(entry)).filter(Boolean);
    }

    if (typeof item === 'string' && item.trim()) {
      return [item.trim()];
    }

    return [];
  }

  riskValue(value: Record<string, unknown> | null | undefined): string {
    return this.textValue(value, ['risk_level'], 'unknown');
  }

  riskClass(value: Record<string, unknown> | null | undefined): string {
    const risk = this.riskValue(value).toLowerCase();

    if (risk === 'critical') {
      return 'critical';
    }

    if (risk === 'attention') {
      return 'attention';
    }

    if (risk === 'normal') {
      return 'normal';
    }

    return 'unknown';
  }

  objectSummary(value: Record<string, unknown> | null | undefined): string {
    const visibleObjects = this.listValue(value, 'visible_objects');
    const supportedClasses = this.listValue(value, 'supported_detection_classes_seen');
    const likelyClasses = this.listValue(value, 'likely_classes');

    return [...new Set([...visibleObjects, ...supportedClasses, ...likelyClasses])].join(', ') || 'None';
  }

  resultHasParsedJson(value: Record<string, unknown> | null | undefined): boolean {
    return !!value && Object.keys(value).length > 0;
  }

  private loadAgents(): void {
    this.cloudAiApi.getAgents().subscribe({
      next: (response) => {
        if (response.success) {
          this.agents = response.data;
        }
      },
    });
  }
}
