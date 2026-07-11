import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { finalize } from 'rxjs';
import { API_CONFIG } from '../../../../core/config/api.config';
import { ApiResponse } from '../../../../core/types/api-response.type';

@Component({
  selector: 'app-adaptive-review',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <section class="vms-page adaptive-page">
      <div class="vms-heading">
        <div>
          <p>Human Review</p>
          <h1>Adaptive Learning Review</h1>
          <span>
            Analyze uncertain crops with VLM assistance and prepare admin or annotator review decisions.
          </span>
        </div>
        <button class="vms-button" type="button" (click)="analyze()" [disabled]="isLoading">
          {{ isLoading ? 'Analyzing...' : 'Analyze Crop' }}
        </button>
      </div>

      <div class="workspace">
        <form class="vms-card form-panel" [formGroup]="form" (ngSubmit)="analyze()">
          <label class="drop">
            <input type="file" accept="image/*,.jpg,.jpeg,.png,.webp,.bmp" (change)="pick($event)" />
            <strong>{{ fileName }}</strong>
            <span>Upload uncertain crop or frame region</span>
          </label>

          <label class="vms-label">
            YOLO class name
            <input class="vms-input" formControlName="yolo_class_name" placeholder="unknown_object" />
          </label>

          <label class="vms-label">
            YOLO confidence
            <input class="vms-input" type="number" min="0" max="1" step="0.01" formControlName="yolo_confidence" />
          </label>
        </form>

        <section class="vms-card result-panel">
          <div class="result-title">
            <span>Backend Analysis</span>
            <h2>{{ result ? 'Review result ready' : 'Waiting for crop' }}</h2>
          </div>

          <div class="empty" *ngIf="!result && !errorMessage">
            Upload a crop and run analysis. The backend response will appear as review fields.
          </div>

          <div class="error" *ngIf="errorMessage">{{ errorMessage }}</div>

          <div class="result-list" *ngIf="result">
            <article *ngFor="let item of resultEntries">
              <span>{{ item.key }}</span>
              <strong>{{ item.value }}</strong>
            </article>
          </div>
        </section>
      </div>
    </section>
  `,
  styles: [
    `
      .workspace {
        display: grid;
        grid-template-columns: minmax(360px, 0.8fr) minmax(0, 1.2fr);
        gap: 22px;
        align-items: start;
      }

      .form-panel,
      .result-panel {
        display: grid;
        gap: 16px;
        padding: 22px;
      }

      .drop {
        min-height: 156px;
        display: grid;
        place-items: center;
        text-align: center;
        border: 2px dashed #93c5fd;
        border-radius: 8px;
        background: #f8fbff;
        padding: 18px;
        cursor: pointer;
      }

      .drop input {
        display: none;
      }

      .drop strong {
        max-width: 100%;
        font-size: 22px;
        font-weight: 950;
        overflow-wrap: anywhere;
      }

      .drop span,
      .result-title span {
        color: #64748b;
        font-weight: 800;
      }

      .result-title h2 {
        margin: 7px 0 0;
        font-size: 24px;
      }

      .result-list {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
      }

      .result-list article,
      .empty,
      .error {
        padding: 14px;
        border-radius: 8px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
      }

      .result-list span {
        display: block;
        color: #64748b;
        font-size: 12px;
        font-weight: 900;
        text-transform: uppercase;
      }

      .result-list strong {
        display: block;
        margin-top: 7px;
        overflow-wrap: anywhere;
      }

      .error {
        background: #fef2f2;
        color: #991b1b;
        font-weight: 800;
      }

      @media (max-width: 1000px) {
        .workspace,
        .result-list {
          grid-template-columns: 1fr;
        }
      }
    `,
  ],
})
export class AdaptiveReviewComponent {
  private readonly fb = inject(FormBuilder);
  private readonly http = inject(HttpClient);

  file: File | null = null;
  fileName = 'Choose crop image';
  isLoading = false;
  errorMessage: string | null = null;
  result: Record<string, unknown> | null = null;

  readonly form = this.fb.nonNullable.group({
    yolo_class_name: '',
    yolo_confidence: 0,
  });

  get resultEntries(): Array<{ key: string; value: string }> {
    return Object.entries(this.result ?? {}).map(([key, value]) => ({
      key,
      value: typeof value === 'object' ? JSON.stringify(value) : String(value),
    }));
  }

  pick(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.file = input.files?.item(0) ?? null;
    this.fileName = this.file?.name ?? 'Choose crop image';
    this.result = null;
    this.errorMessage = null;
  }

  analyze(): void {
    if (!this.file) {
      this.errorMessage = 'Choose a crop image first.';
      return;
    }

    const formData = new FormData();
    formData.append('image_file', this.file);

    const raw = this.form.getRawValue();

    if (raw.yolo_class_name.trim()) {
      formData.append('yolo_class_name', raw.yolo_class_name.trim());
    }

    if (raw.yolo_confidence > 0) {
      formData.append('yolo_confidence', String(raw.yolo_confidence));
    }

    this.isLoading = true;
    this.errorMessage = null;

    this.http
      .post<ApiResponse<Record<string, unknown>>>(`${API_CONFIG.baseUrl}/adaptive-learning/crop/analyze`, formData)
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: (response) => {
          this.result = response.data;
        },
        error: (error) => {
          this.errorMessage =
            error?.error?.detail?.message ||
            error?.error?.message ||
            error?.message ||
            'Unable to analyze crop.';
        },
      });
  }
}
