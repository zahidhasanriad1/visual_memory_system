import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { finalize } from 'rxjs';
import { ApiClientService } from '../../../../core/services/api-client.service';

interface TrainingJob {
  job_id: string;
  detector_model: 'yolo' | 'skydet' | string;
  status: string;
  progress_percent: number;
  message: string;
  metrics: Record<string, number | string | null>;
}

interface DetectorModelOption {
  value: 'yolo' | 'skydet';
  label: string;
}

@Component({
  selector: 'app-training-orchestrator',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <section class="vms-page training-page">
      <div class="vms-heading">
        <div>
          <p>Admin Module</p>
          <h1>Training Orchestrator</h1>
          <span>
            Queue managed YOLO or SkyDet training jobs with dataset, base model, epochs, image size, and batch controls.
          </span>
        </div>
        <button class="vms-button" type="button" (click)="startTraining()" [disabled]="isSubmitting">
          {{ isSubmitting ? 'Queueing...' : 'Start Training' }}
        </button>
      </div>

      <div class="workspace">
        <form class="vms-card form-panel" [formGroup]="form" (ngSubmit)="startTraining()">
          <label class="vms-label">
            Dataset version ID
            <input class="vms-input" formControlName="dataset_version_id" placeholder="Required dataset version ID" />
          </label>

          <label class="vms-label">
            Base model ID
            <input class="vms-input" formControlName="base_model_id" placeholder="Optional model ID" />
          </label>

          <div class="detector-selector" role="radiogroup" aria-label="Detector model">
            @for (option of detectorOptions; track option.value) {
              <label [class.active]="form.controls.detector_model.value === option.value">
                <input type="radio" formControlName="detector_model" [value]="option.value" />
                <span>{{ option.label }}</span>
              </label>
            }
          </div>

          <div class="settings">
            <label class="vms-label">
              Epochs
              <input class="vms-input" type="number" min="1" formControlName="epochs" />
            </label>

            <label class="vms-label">
              Image size
              <input class="vms-input" type="number" min="128" step="32" formControlName="image_size" />
            </label>

            <label class="vms-label">
              Batch size
              <input class="vms-input" type="number" min="1" formControlName="batch_size" />
            </label>
          </div>

          <button class="vms-button" type="submit" [disabled]="isSubmitting">
            Queue Backend Job
          </button>
        </form>

        <section class="vms-card result-panel">
          <div class="panel-title">
            <span>Latest Training Job</span>
            <h2>{{ job?.job_id || 'No job queued yet' }}</h2>
          </div>

          <div class="empty" *ngIf="!job && !errorMessage">
            Submit the form to create a backend training job.
          </div>

          <div class="error" *ngIf="errorMessage">{{ errorMessage }}</div>

          <ng-container *ngIf="job">
            <div class="vms-stat-grid">
              <article class="vms-stat">
                <span>Detector</span>
                <strong>{{ job.detector_model }}</strong>
              </article>
              <article class="vms-stat">
                <span>Status</span>
                <strong>{{ job.status }}</strong>
              </article>
              <article class="vms-stat">
                <span>Progress</span>
                <strong>{{ job.progress_percent }}%</strong>
              </article>
              <article class="vms-stat">
                <span>Epochs</span>
                <strong>{{ job.metrics['epochs'] }}</strong>
              </article>
              <article class="vms-stat">
                <span>Batch</span>
                <strong>{{ job.metrics['batch_size'] }}</strong>
              </article>
            </div>

            <div class="message">
              {{ job.message }}
            </div>
          </ng-container>
        </section>
      </div>
    </section>
  `,
  styles: [
    `
      .workspace {
        display: grid;
        grid-template-columns: minmax(360px, 0.85fr) minmax(0, 1.15fr);
        gap: 22px;
        align-items: start;
      }

      .form-panel,
      .result-panel {
        display: grid;
        gap: 16px;
        padding: 22px;
      }

      .settings {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 14px;
      }

      .detector-selector {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
      }

      .detector-selector label {
        min-height: 46px;
        display: grid;
        place-items: center;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        background: #ffffff;
        color: #334155;
        font-size: 13px;
        font-weight: 900;
        cursor: pointer;
      }

      .detector-selector label.active {
        border-color: #2563eb;
        background: #eff6ff;
        color: #1d4ed8;
      }

      .detector-selector input {
        position: absolute;
        opacity: 0;
        pointer-events: none;
      }

      .panel-title span {
        color: #2563eb;
        font-size: 12px;
        font-weight: 900;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      .panel-title h2 {
        margin: 7px 0 0;
        font-size: 24px;
        overflow-wrap: anywhere;
      }

      .message,
      .empty,
      .error {
        padding: 14px 16px;
        border-radius: 8px;
        background: #f8fafc;
        color: #475569;
        font-weight: 750;
      }

      .error {
        background: #fef2f2;
        color: #991b1b;
      }

      @media (max-width: 1100px) {
        .workspace {
          grid-template-columns: 1fr;
        }
      }

      @media (max-width: 720px) {
        .detector-selector,
        .settings {
          grid-template-columns: 1fr;
        }
      }
    `,
  ],
})
export class TrainingOrchestratorComponent {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ApiClientService);

  isSubmitting = false;
  errorMessage: string | null = null;
  job: TrainingJob | null = null;

  readonly detectorOptions: DetectorModelOption[] = [
    { value: 'yolo', label: 'YOLO' },
    { value: 'skydet', label: 'SkyDet' },
  ];

  readonly form = this.fb.nonNullable.group({
    detector_model: 'yolo' as const,
    dataset_version_id: ['', Validators.required],
    base_model_id: '',
    epochs: 50,
    image_size: 640,
    batch_size: 8,
  });

  startTraining(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.errorMessage = 'Dataset version ID is required.';
      return;
    }
    this.isSubmitting = true;
    this.errorMessage = null;

    const raw = this.form.getRawValue();
    const payload = {
      detector_model: raw.detector_model,
      dataset_version_id: raw.dataset_version_id.trim(),
      base_model_id: raw.base_model_id.trim() || null,
      epochs: Number(raw.epochs),
      image_size: Number(raw.image_size),
      batch_size: Number(raw.batch_size),
    };

    this.api
      .post<TrainingJob>('/training-jobs/start', payload)
      .pipe(finalize(() => (this.isSubmitting = false)))
      .subscribe({
        next: (response) => {
          this.job = response.data;
        },
        error: (error) => {
          this.errorMessage =
            error?.error?.detail?.message ||
            error?.error?.message ||
            error?.message ||
            'Unable to queue training job.';
        },
      });
  }
}
