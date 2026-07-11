import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { finalize, forkJoin } from 'rxjs';

import { API_CONFIG } from '../../../../core/config/api.config';
import { AnnotationApiService } from '../../../../core/services/annotation-api.service';
import {
  AnnotationObject,
  AnnotationProject,
  AnnotationTask,
} from '../../../../core/types/annotation.types';

type AnnotationTool = 'select' | 'box' | 'polygon' | 'pan';
type Point = [number, number];

@Component({
  selector: 'app-annotation-workspace',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './annotation-workspace.component.html',
  styleUrl: './annotation-workspace.component.scss',
})
export class AnnotationWorkspaceComponent implements OnInit {
  private readonly api = inject(AnnotationApiService);

  projects: AnnotationProject[] = [];
  tasks: AnnotationTask[] = [];
  objects: AnnotationObject[] = [];
  dynamicLabels: string[] = [];
  selectedProjectId = '';
  activeTask: AnnotationTask | null = null;
  selectedObject: AnnotationObject | null = null;
  queueFilter: 'all' | 'pending' | 'approved' = 'all';
  activeTool: AnnotationTool = 'select';
  zoom = 1;
  imageWidth = 1000;
  imageHeight = 1000;
  isLoading = false;
  isSaving = false;
  errorMessage: string | null = null;
  selectedLabel = 'ship';
  newLabel = '';
  polygonPoints: Point[] = [];
  isDrawingBox = false;
  private boxStart: Point | null = null;

  draftBox = {
    x_min: 0,
    y_min: 0,
    x_max: 0,
    y_max: 0,
  };

  ngOnInit(): void {
    this.reload();
  }

  get activeProject(): AnnotationProject | null {
    return this.projects.find((project) => project.id === this.selectedProjectId) ?? null;
  }

  get filteredTasks(): AnnotationTask[] {
    return this.tasks.filter((task) => {
      const projectMatches = !this.selectedProjectId || task.project_id === this.selectedProjectId;
      return projectMatches && (this.queueFilter === 'all' || task.status === this.queueFilter);
    });
  }

  get activeObjects(): AnnotationObject[] {
    return this.activeTask
      ? this.objects.filter((object) => object.task_id === this.activeTask?.id)
      : [];
  }

  get labels(): string[] {
    return [...new Set(['airplane', 'boat', 'car', 'ship', ...this.dynamicLabels])].sort();
  }

  get activeImageUrl(): string | null {
    return this.activeTask?.source_url
      ? `${API_CONFIG.mediaBaseUrl}${this.activeTask.source_url}`
      : null;
  }

  get zoomPercent(): string {
    return `${Math.round(this.zoom * 100)}%`;
  }

  get imageAspectRatio(): string {
    return `${this.imageWidth} / ${this.imageHeight}`;
  }

  get draftPolygonPoints(): string {
    return this.polygonPoints.map(([x, y]) => `${x},${y}`).join(' ');
  }

  reload(): void {
    this.isLoading = true;
    this.errorMessage = null;
    forkJoin({ projects: this.api.listProjects(), labels: this.api.listLabels() })
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: ({ projects, labels }) => {
          this.projects = projects.data ?? [];
          this.dynamicLabels = labels.data ?? [];
          if (!this.selectedLabel && this.labels.length) {
            this.selectedLabel = this.labels[0];
          }
          this.loadTasks();
        },
        error: (error) => {
          this.errorMessage = this.errorText(error, 'Unable to load annotation workspace.');
        },
      });
  }

  selectProject(projectId: string): void {
    this.selectedProjectId = projectId;
    this.activeTask = null;
    this.selectedObject = null;
    this.loadTasks();
  }

  selectTask(task: AnnotationTask): void {
    this.activeTask = task;
    this.selectedObject = null;
    this.resetDraft();
    this.loadObjects(task.id);
  }

  setTool(tool: AnnotationTool): void {
    this.activeTool = tool;
    this.isDrawingBox = false;
    this.boxStart = null;
    if (tool !== 'polygon') {
      this.polygonPoints = [];
    }
  }

  onImageLoad(event: Event): void {
    const image = event.target as HTMLImageElement;
    this.imageWidth = image.naturalWidth || 1000;
    this.imageHeight = image.naturalHeight || 1000;
  }

  onCanvasPointerDown(event: PointerEvent): void {
    if (!this.activeTask || !this.activeImageUrl) {
      return;
    }
    const point = this.eventPoint(event);
    if (this.activeTool === 'box') {
      this.boxStart = point;
      this.isDrawingBox = true;
      this.draftBox = { x_min: point[0], y_min: point[1], x_max: point[0], y_max: point[1] };
      (event.currentTarget as SVGSVGElement).setPointerCapture(event.pointerId);
    } else if (this.activeTool === 'polygon') {
      this.polygonPoints = [...this.polygonPoints, point];
    }
  }

  onCanvasPointerMove(event: PointerEvent): void {
    if (!this.isDrawingBox || !this.boxStart || this.activeTool !== 'box') {
      return;
    }
    const [x, y] = this.eventPoint(event);
    this.draftBox = {
      x_min: Math.min(this.boxStart[0], x),
      y_min: Math.min(this.boxStart[1], y),
      x_max: Math.max(this.boxStart[0], x),
      y_max: Math.max(this.boxStart[1], y),
    };
  }

  onCanvasPointerUp(event: PointerEvent): void {
    if (!this.isDrawingBox) {
      return;
    }
    this.onCanvasPointerMove(event);
    this.isDrawingBox = false;
    this.boxStart = null;
  }

  finishPolygon(): void {
    if (this.polygonPoints.length < 3) {
      this.errorMessage = 'Polygon requires at least three points.';
      return;
    }
    this.errorMessage = null;
  }

  undoPolygonPoint(): void {
    this.polygonPoints = this.polygonPoints.slice(0, -1);
  }

  addLabel(): void {
    const label = this.normalizeLabel(this.newLabel);
    if (!label) {
      return;
    }
    this.dynamicLabels = [...new Set([...this.dynamicLabels, label])];
    this.selectedLabel = label;
    this.newLabel = '';
  }

  saveObject(): void {
    if (!this.activeTask) {
      this.errorMessage = 'Select a task first.';
      return;
    }
    const geometryType = this.activeTool === 'polygon' ? 'polygon' : 'box';
    if (geometryType === 'polygon' && this.polygonPoints.length < 3) {
      this.errorMessage = 'Add at least three polygon points before saving.';
      return;
    }
    if (
      geometryType === 'box' &&
      (this.draftBox.x_max - this.draftBox.x_min < 2 ||
        this.draftBox.y_max - this.draftBox.y_min < 2)
    ) {
      this.errorMessage = 'Draw a bounding box on the image before saving.';
      return;
    }

    this.isSaving = true;
    this.errorMessage = null;
    this.api
      .createObject({
        task_id: this.activeTask.id,
        label: this.normalizeLabel(this.selectedLabel) || 'unknown_object',
        geometry_type: geometryType,
        x_min: this.draftBox.x_min,
        y_min: this.draftBox.y_min,
        x_max: this.draftBox.x_max,
        y_max: this.draftBox.y_max,
        points: geometryType === 'polygon' ? this.polygonPoints : [],
      })
      .pipe(finalize(() => (this.isSaving = false)))
      .subscribe({
        next: (response) => {
          this.objects = [...this.objects, response.data];
          this.dynamicLabels = [...new Set([...this.dynamicLabels, response.data.label])];
          this.selectedObject = response.data;
          this.resetDraft();
        },
        error: (error) => {
          this.errorMessage = this.errorText(error, 'Unable to save annotation.');
        },
      });
  }

  reviewSelected(status: 'approved' | 'rejected'): void {
    if (!this.selectedObject) {
      return;
    }
    this.api.updateObjectStatus(this.selectedObject.id, status).subscribe({
      next: (response) => {
        this.objects = this.objects.map((item) =>
          item.id === response.data.id ? response.data : item
        );
        this.selectedObject = response.data;
      },
      error: (error) => {
        this.errorMessage = this.errorText(error, 'Unable to update review status.');
      },
    });
  }

  deleteSelected(): void {
    if (!this.selectedObject) {
      return;
    }
    const objectId = this.selectedObject.id;
    this.api.deleteObject(objectId).subscribe({
      next: () => {
        this.objects = this.objects.filter((item) => item.id !== objectId);
        this.selectedObject = null;
      },
      error: (error) => {
        this.errorMessage = this.errorText(error, 'Unable to delete annotation.');
      },
    });
  }

  selectObject(object: AnnotationObject, event?: Event): void {
    event?.stopPropagation();
    if (this.activeTool === 'select') {
      this.selectedObject = object;
    }
  }

  objectPolygonPoints(object: AnnotationObject): string {
    return (object.points ?? []).map((point) => `${point[0]},${point[1]}`).join(' ');
  }

  boxX(object: AnnotationObject): number {
    return this.normalizedCoord(Math.min(object.x_min, object.x_max), this.imageWidth);
  }

  boxY(object: AnnotationObject): number {
    return this.normalizedCoord(Math.min(object.y_min, object.y_max), this.imageHeight);
  }

  boxWidth(object: AnnotationObject): number {
    return Math.max(2, Math.abs(this.boxX(object) - this.normalizedCoord(object.x_max, this.imageWidth)));
  }

  boxHeight(object: AnnotationObject): number {
    return Math.max(2, Math.abs(this.boxY(object) - this.normalizedCoord(object.y_max, this.imageHeight)));
  }

  shortId(value: string): string {
    return value.slice(0, 8);
  }

  labelColor(label: string): string {
    const palette = ['#2563eb', '#06b6d4', '#f59e0b', '#7c3aed', '#16a34a', '#db2777', '#dc2626'];
    const hash = [...label].reduce((total, character) => total + character.charCodeAt(0), 0);
    return palette[hash % palette.length];
  }

  private resetDraft(): void {
    this.draftBox = { x_min: 0, y_min: 0, x_max: 0, y_max: 0 };
    this.polygonPoints = [];
    this.isDrawingBox = false;
    this.boxStart = null;
  }

  private eventPoint(event: PointerEvent): Point {
    const svg = event.currentTarget as SVGSVGElement;
    const bounds = svg.getBoundingClientRect();
    const x = ((event.clientX - bounds.left) / Math.max(1, bounds.width)) * this.imageWidth;
    const y = ((event.clientY - bounds.top) / Math.max(1, bounds.height)) * this.imageHeight;
    return [
      Math.max(0, Math.min(this.imageWidth, Math.round(x * 10) / 10)),
      Math.max(0, Math.min(this.imageHeight, Math.round(y * 10) / 10)),
    ];
  }

  private normalizedCoord(value: number, axisSize: number): number {
    return value <= 1 ? value * axisSize : Math.max(0, Math.min(axisSize, value));
  }

  private normalizeLabel(value: string): string {
    return value.trim().toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
  }

  private loadTasks(): void {
    this.api.listTasks(this.selectedProjectId || undefined).subscribe({
      next: (response) => {
        this.tasks = response.data ?? [];
        this.activeTask = this.filteredTasks[0] ?? null;
        if (this.activeTask) {
          this.loadObjects(this.activeTask.id);
        } else {
          this.objects = [];
        }
      },
      error: (error) => {
        this.errorMessage = this.errorText(error, 'Unable to load annotation tasks.');
      },
    });
  }

  private loadObjects(taskId: string): void {
    this.api.listObjects(taskId).subscribe({
      next: (response) => {
        const otherObjects = this.objects.filter((object) => object.task_id !== taskId);
        this.objects = [...otherObjects, ...(response.data ?? [])];
        this.selectedObject = response.data?.[0] ?? null;
      },
      error: (error) => {
        this.errorMessage = this.errorText(error, 'Unable to load annotation objects.');
      },
    });
  }

  private errorText(error: any, fallback: string): string {
    return error?.error?.detail?.message || error?.error?.message || error?.message || fallback;
  }
}
