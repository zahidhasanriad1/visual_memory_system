import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { finalize } from 'rxjs';
import { ApiClientService } from '../../../../core/services/api-client.service';

interface ModelVersion {
  id: string;
  model_name: string;
  model_type: string;
  version: string;
  model_path: string;
  onnx_path: string | null;
  class_names: string[];
  metrics: Record<string, unknown>;
  status: string;
}

@Component({
  selector: 'app-model-registry',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <section class="vms-page registry-page">
      <div class="vms-heading">
        <div>
          <p>Admin Module</p>
          <h1>Model Registry</h1>
          <span>
            Register validated model versions, inspect lifecycle state, and activate models safely from the backend registry.
          </span>
        </div>
        <button class="vms-button" type="button" (click)="loadModels()" [disabled]="isLoading">
          {{ isLoading ? 'Refreshing...' : 'Refresh' }}
        </button>
      </div>

      <div class="workspace">
        <form class="vms-card form-panel" [formGroup]="form" (ngSubmit)="registerModel()">
          <label class="vms-label">
            Model name
            <input class="vms-input" formControlName="model_name" placeholder="skysealand-yolo" />
          </label>

          <div class="settings">
            <label class="vms-label">
              Model type
              <input class="vms-input" formControlName="model_type" placeholder="detector" />
            </label>

            <label class="vms-label">
              Version
              <input class="vms-input" formControlName="version" placeholder="v1.0.0" />
            </label>
          </div>

          <label class="vms-label">
            Model path
            <input class="vms-input" formControlName="model_path" placeholder="storage/models/model.pt" />
          </label>

          <label class="vms-label">
            ONNX path
            <input class="vms-input" formControlName="onnx_path" placeholder="storage/models/model.onnx" />
          </label>

          <label class="vms-label">
            Class names
            <input class="vms-input" formControlName="class_names" placeholder="airplane, boat, car, ship" />
          </label>

          <button class="vms-button" type="submit" [disabled]="isSubmitting">
            {{ isSubmitting ? 'Registering...' : 'Register Model' }}
          </button>

          <div class="error" *ngIf="errorMessage">{{ errorMessage }}</div>
        </form>

        <section class="vms-card table-panel">
          <div class="table-heading">
            <div>
              <span>Registered Versions</span>
              <h2>{{ models.length }} models</h2>
            </div>
          </div>

          <div class="empty" *ngIf="!models.length && !isLoading">
            No model versions registered yet.
          </div>

          <div class="model-list" *ngIf="models.length">
            <article *ngFor="let model of models">
              <div>
                <strong>{{ model.model_name }}</strong>
                <span>{{ model.model_type }} / {{ model.version }}</span>
              </div>
              <div class="classes">
                <small *ngFor="let name of model.class_names">{{ name }}</small>
              </div>
              <b [class.active]="model.status === 'active'">{{ model.status }}</b>
              <button
                class="vms-button secondary"
                type="button"
                (click)="activateModel(model.id)"
                [disabled]="model.status === 'active' || activatingId === model.id"
              >
                {{ activatingId === model.id ? 'Activating...' : 'Activate' }}
              </button>
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
        grid-template-columns: minmax(360px, 0.78fr) minmax(0, 1.22fr);
        gap: 22px;
        align-items: start;
      }

      .form-panel,
      .table-panel {
        padding: 22px;
      }

      .form-panel {
        display: grid;
        gap: 15px;
      }

      .settings {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 14px;
      }

      .table-heading span {
        color: #2563eb;
        font-size: 12px;
        font-weight: 900;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      .table-heading h2 {
        margin: 7px 0 18px;
        font-size: 24px;
      }

      .model-list {
        display: grid;
        gap: 10px;
      }

      .model-list article {
        display: grid;
        grid-template-columns: minmax(0, 1.2fr) minmax(120px, 0.8fr) auto auto;
        align-items: center;
        gap: 12px;
        padding: 14px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        background: #f8fafc;
      }

      .model-list strong,
      .model-list span {
        display: block;
        overflow-wrap: anywhere;
      }

      .model-list strong {
        font-size: 16px;
        font-weight: 950;
      }

      .model-list span {
        margin-top: 4px;
        color: #64748b;
        font-size: 13px;
        font-weight: 750;
      }

      .classes {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
      }

      .classes small,
      .model-list b {
        padding: 6px 8px;
        border-radius: 999px;
        background: #e0f2fe;
        color: #0369a1;
        font-size: 12px;
        font-weight: 900;
      }

      .model-list b {
        background: #f1f5f9;
        color: #475569;
        text-transform: uppercase;
      }

      .model-list b.active {
        background: #dcfce7;
        color: #166534;
      }

      .empty,
      .error {
        padding: 14px;
        border-radius: 8px;
        background: #f8fafc;
        color: #64748b;
        font-weight: 750;
      }

      .error {
        background: #fef2f2;
        color: #991b1b;
      }

      @media (max-width: 1180px) {
        .workspace,
        .model-list article {
          grid-template-columns: 1fr;
        }
      }

      @media (max-width: 720px) {
        .settings {
          grid-template-columns: 1fr;
        }
      }
    `,
  ],
})
export class ModelRegistryComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ApiClientService);

  models: ModelVersion[] = [];
  isLoading = false;
  isSubmitting = false;
  activatingId: string | null = null;
  errorMessage: string | null = null;

  readonly form = this.fb.nonNullable.group({
    model_name: '',
    model_type: 'detector',
    version: '',
    model_path: '',
    onnx_path: '',
    class_names: 'airplane, boat, car, ship',
  });

  ngOnInit(): void {
    this.loadModels();
  }

  loadModels(): void {
    this.isLoading = true;
    this.errorMessage = null;

    this.api
      .get<ModelVersion[]>('/model-registry/models')
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: (response) => {
          this.models = response.data;
        },
        error: (error) => {
          this.errorMessage =
            error?.error?.detail?.message ||
            error?.error?.message ||
            error?.message ||
            'Unable to load model registry.';
        },
      });
  }

  registerModel(): void {
    this.isSubmitting = true;
    this.errorMessage = null;

    const raw = this.form.getRawValue();
    const payload = {
      model_name: raw.model_name.trim(),
      model_type: raw.model_type.trim(),
      version: raw.version.trim(),
      model_path: raw.model_path.trim(),
      onnx_path: raw.onnx_path.trim() || null,
      class_names: raw.class_names
        .split(',')
        .map((name) => name.trim())
        .filter(Boolean),
      metrics: {},
    };

    this.api
      .post<ModelVersion>('/model-registry/models', payload)
      .pipe(finalize(() => (this.isSubmitting = false)))
      .subscribe({
        next: () => this.loadModels(),
        error: (error) => {
          this.errorMessage =
            error?.error?.detail?.message ||
            error?.error?.message ||
            error?.message ||
            'Unable to register model.';
        },
      });
  }

  activateModel(modelId: string): void {
    this.activatingId = modelId;
    this.errorMessage = null;

    this.api
      .post<ModelVersion>(`/model-registry/models/${modelId}/activate`, {})
      .pipe(finalize(() => (this.activatingId = null)))
      .subscribe({
        next: () => this.loadModels(),
        error: (error) => {
          this.errorMessage =
            error?.error?.detail?.message ||
            error?.error?.message ||
            error?.message ||
            'Unable to activate model.';
        },
      });
  }
}
