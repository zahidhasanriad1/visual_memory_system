import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { Subject, finalize, switchMap, takeUntil, timer } from 'rxjs';

import { AnnotationApiService } from '../../../../core/services/annotation-api.service';
import { ApiClientService } from '../../../../core/services/api-client.service';
import { AnnotationProject } from '../../../../core/types/annotation.types';

interface CustomDataset {
  id: string;
  name: string;
  version: string;
  class_names: string[];
  image_count: number;
  annotation_count: number;
  quality_score: number;
  ready_for_training: boolean;
}

interface TrainingJob {
  job_id: string;
  detector_model: string;
  status: string;
  progress_percent: number;
  message: string;
  metrics: Record<string, unknown>;
}

@Component({
  selector: 'app-custom-training',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <section class="custom-training-page">
      <header>
        <div><p>Continuous learning</p><h1>Custom Object Training</h1>
          <span>Approved box/polygon annotations become a versioned dataset, then a new YOLO or SkyDet model.</span>
        </div>
        <button type="button" (click)="reload()" [disabled]="isLoading">Refresh</button>
      </header>

      <div class="pipeline">
        <article><b>1</b><span>Annotate</span><small>Box or polygon</small></article>
        <article><b>2</b><span>Approve</span><small>Quality gate</small></article>
        <article><b>3</b><span>Build dataset</span><small>YOLO + COCO</small></article>
        <article><b>4</b><span>Train & version</span><small>Registry activation</small></article>
      </div>

      <div class="workspace">
        <form class="card" [formGroup]="datasetForm" (ngSubmit)="createDataset()">
          <div class="card-title"><div><span>Dataset builder</span><h2>From approved annotations</h2></div></div>
          <label>Annotation project
            <select formControlName="project_id"><option value="">Select project</option>
              @for (project of projects; track project.id) { <option [value]="project.id">{{ project.name }}</option> }
            </select>
          </label>
          <div class="two-columns">
            <label>Dataset name<input formControlName="name" placeholder="Harbor objects" /></label>
            <label>Version<input formControlName="version" placeholder="v1" /></label>
          </div>
          <label class="check"><input type="checkbox" formControlName="include_pending" /> Include pending annotations (not recommended)</label>
          <button class="primary" type="submit" [disabled]="isBuildingDataset">
            {{ isBuildingDataset ? 'Building dataset…' : 'Create versioned dataset' }}
          </button>
        </form>

        <form class="card" [formGroup]="trainingForm" (ngSubmit)="startTraining()">
          <div class="card-title"><div><span>Managed training</span><h2>Train model</h2></div></div>
          <label>Dataset version
            <select formControlName="dataset_version_id"><option value="">Select dataset</option>
              @for (dataset of datasets; track dataset.id) {
                <option [value]="dataset.id">{{ dataset.name }} · {{ dataset.version }} · {{ dataset.class_names.length }} classes</option>
              }
            </select>
          </label>
          <div class="detectors">
            @for (model of ['yolo', 'skydet']; track model) {
              <label [class.active]="trainingForm.controls.detector_model.value === model">
                <input type="radio" formControlName="detector_model" [value]="model" />{{ model }}
              </label>
            }
          </div>
          <div class="three-columns">
            <label>Epochs<input type="number" min="1" formControlName="epochs" /></label>
            <label>Image size<input type="number" min="320" step="32" formControlName="image_size" /></label>
            <label>Batch<input type="number" min="1" formControlName="batch_size" /></label>
          </div>
          <button class="primary" type="submit" [disabled]="isStartingTraining">
            {{ isStartingTraining ? 'Starting worker…' : 'Start custom training' }}
          </button>
        </form>
      </div>

      <section class="card dataset-list">
        <div class="card-title"><div><span>Dataset registry</span><h2>Available versions</h2></div><strong>{{ datasets.length }}</strong></div>
        <div class="table-head"><span>Dataset</span><span>Classes</span><span>Images</span><span>Annotations</span><span>Quality</span></div>
        @for (dataset of datasets; track dataset.id) {
          <article class="dataset-row">
            <div><strong>{{ dataset.name }}</strong><small>{{ dataset.version }}</small></div>
            <div class="chips">@for (name of dataset.class_names; track name) { <i>{{ name }}</i> }</div>
            <b>{{ dataset.image_count }}</b><b>{{ dataset.annotation_count }}</b><b>{{ dataset.quality_score }}%</b>
          </article>
        } @empty { <div class="empty">Create a dataset from an annotation project to begin.</div> }
      </section>

      <section class="card jobs">
        <div class="card-title"><div><span>Training runs</span><h2>Worker status</h2></div><strong>{{ jobs.length }}</strong></div>
        @for (job of jobs; track job.job_id) {
          <article>
            <div><strong>{{ job.detector_model | uppercase }}</strong><small>{{ job.job_id }}</small></div>
            <div class="progress"><i [style.width.%]="job.progress_percent"></i></div>
            <b [class]="job.status">{{ job.status }}</b><span>{{ job.message }}</span>
          </article>
        } @empty { <div class="empty">No training job has been started.</div> }
      </section>
      <p class="error" *ngIf="errorMessage">{{ errorMessage }}</p>
      <p class="success" *ngIf="successMessage">{{ successMessage }}</p>
    </section>
  `,
  styles: [`
    .custom-training-page{display:grid;gap:18px;color:#0f172a} header,.card-title,.pipeline,.table-head,.dataset-row,.jobs article{display:flex;align-items:center} header{justify-content:space-between;gap:18px} header p,.card-title span{margin:0;color:#2563eb;font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase} h1{margin:3px 0;font-size:34px;font-weight:800} header span{color:#64748b} button,input,select{min-height:42px;border:1px solid #d8e1ee;border-radius:8px;background:#fff;color:#0f172a;font:inherit} button{padding:0 16px;font-weight:700;cursor:pointer} input,select{width:100%;padding:0 11px}.pipeline{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.pipeline article{display:grid;grid-template-columns:auto 1fr;column-gap:10px;padding:14px;border:1px solid #dbe4ef;border-radius:10px;background:#f8fafc}.pipeline b{grid-row:1/3;width:32px;height:32px;display:grid;place-items:center;border-radius:9px;background:#2563eb;color:#fff}.pipeline span{font-weight:800}.pipeline small{color:#64748b}.workspace{display:grid;grid-template-columns:1fr 1fr;gap:18px}.card{display:grid;gap:14px;padding:20px;border:1px solid #d8e1ee;border-radius:12px;background:#fff;box-shadow:0 10px 30px rgba(15,23,42,.05)}.card-title{justify-content:space-between}.card-title h2{margin:4px 0 0;font-size:20px}.card-title>strong{padding:5px 10px;border-radius:999px;background:#eff6ff;color:#1d4ed8}label{display:grid;gap:6px;color:#475569;font-size:12px;font-weight:700}.two-columns,.three-columns{display:grid;gap:10px}.two-columns{grid-template-columns:1fr 120px}.three-columns{grid-template-columns:repeat(3,1fr)}.check{display:flex;align-items:center}.check input{width:17px;min-height:17px}.primary{border-color:#2563eb;background:#2563eb;color:#fff}.detectors{display:grid;grid-template-columns:1fr 1fr;gap:8px}.detectors label{min-height:42px;display:grid;place-items:center;border:1px solid #d8e1ee;border-radius:8px;text-transform:uppercase;cursor:pointer}.detectors label.active{border-color:#2563eb;background:#eff6ff;color:#1d4ed8}.detectors input{position:absolute;opacity:0}.table-head,.dataset-row{display:grid;grid-template-columns:1.1fr 2fr .5fr .7fr .5fr;gap:12px}.table-head{padding:0 10px;color:#64748b;font-size:11px;font-weight:700;text-transform:uppercase}.dataset-row{padding:12px 10px;border-top:1px solid #eef2f7}.dataset-row>div:first-child,.jobs article>div:first-child{display:grid}.dataset-row small,.jobs small{color:#64748b}.chips{display:flex;flex-wrap:wrap;gap:5px}.chips i{padding:3px 7px;border-radius:999px;background:#eff6ff;color:#1d4ed8;font-size:10px;font-style:normal;font-weight:700}.jobs article{display:grid;grid-template-columns:1fr 1.4fr .6fr 2fr;gap:12px;padding:11px 0;border-top:1px solid #eef2f7}.progress{height:8px;border-radius:999px;background:#e2e8f0;overflow:hidden}.progress i{display:block;height:100%;background:#2563eb}.completed{color:#15803d}.failed{color:#b91c1c}.running{color:#1d4ed8}.empty,.error,.success{padding:13px;border-radius:8px;background:#f8fafc;color:#64748b}.error{background:#fef2f2;color:#991b1b}.success{background:#ecfdf5;color:#047857}@media(max-width:950px){.workspace,.pipeline{grid-template-columns:1fr}.table-head{display:none}.dataset-row,.jobs article{grid-template-columns:1fr}.three-columns{grid-template-columns:1fr}}
  `],
})
export class CustomTrainingComponent implements OnInit, OnDestroy {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ApiClientService);
  private readonly annotationApi = inject(AnnotationApiService);
  private readonly destroy$ = new Subject<void>();

  projects: AnnotationProject[] = [];
  datasets: CustomDataset[] = [];
  jobs: TrainingJob[] = [];
  isLoading = false;
  isBuildingDataset = false;
  isStartingTraining = false;
  errorMessage: string | null = null;
  successMessage: string | null = null;

  readonly datasetForm = this.fb.nonNullable.group({ project_id: '', name: '', version: 'v1', include_pending: false });
  readonly trainingForm = this.fb.nonNullable.group({ detector_model: 'skydet', dataset_version_id: '', epochs: 30, image_size: 640, batch_size: 4 });

  ngOnInit(): void { this.reload(); timer(3000, 5000).pipe(takeUntil(this.destroy$), switchMap(() => this.api.get<TrainingJob[]>('/training-jobs'))).subscribe({next:r=>this.jobs=r.data??[]}); }
  ngOnDestroy(): void { this.destroy$.next(); this.destroy$.complete(); }

  reload(): void {
    this.isLoading = true; this.errorMessage = null;
    this.annotationApi.listProjects().subscribe({next:r=>this.projects=r.data??[]});
    this.api.get<CustomDataset[]>('/training-jobs/datasets').pipe(finalize(()=>this.isLoading=false)).subscribe({next:r=>this.datasets=r.data??[],error:e=>this.errorMessage=this.errorText(e)});
    this.api.get<TrainingJob[]>('/training-jobs').subscribe({next:r=>this.jobs=r.data??[]});
  }

  createDataset(): void {
    const raw=this.datasetForm.getRawValue(); if(!raw.project_id||!raw.name.trim()){this.errorMessage='Select a project and enter a dataset name.';return}
    this.isBuildingDataset=true;this.errorMessage=null;this.successMessage=null;
    this.api.post<CustomDataset>('/training-jobs/datasets/from-annotations',{...raw,name:raw.name.trim(),version:raw.version.trim()||'v1',train_split:.8})
      .pipe(finalize(()=>this.isBuildingDataset=false)).subscribe({next:r=>{this.datasets=[r.data,...this.datasets.filter(x=>x.id!==r.data.id)];this.trainingForm.controls.dataset_version_id.setValue(r.data.id);this.successMessage=`Dataset ${r.data.name} is ready with ${r.data.class_names.length} classes.`},error:e=>this.errorMessage=this.errorText(e)});
  }

  startTraining(): void {
    const raw=this.trainingForm.getRawValue(); if(!raw.dataset_version_id){this.errorMessage='Select a dataset version first.';return}
    this.isStartingTraining=true;this.errorMessage=null;this.successMessage=null;
    this.api.post<TrainingJob>('/training-jobs/start',{...raw,epochs:Number(raw.epochs),image_size:Number(raw.image_size),batch_size:Number(raw.batch_size),base_model_id:null})
      .pipe(finalize(()=>this.isStartingTraining=false)).subscribe({next:r=>{this.jobs=[r.data,...this.jobs];this.successMessage='Training worker started. The active model registry will update after validation.'},error:e=>this.errorMessage=this.errorText(e)});
  }
  private errorText(error:any):string{return error?.error?.detail?.message||error?.error?.message||error?.message||'Request failed.'}
}
