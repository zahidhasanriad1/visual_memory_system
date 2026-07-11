import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { API_CONFIG } from '../config/api.config';
import { ApiResponse } from '../types/api-response.type';
import {
  AnnotationObject,
  AnnotationObjectCreateRequest,
  AnnotationProject,
  AnnotationTask,
} from '../types/annotation.types';

@Injectable({
  providedIn: 'root',
})
export class AnnotationApiService {
  private readonly apiBaseUrl = API_CONFIG.baseUrl;

  constructor(private readonly http: HttpClient) {}

  listProjects(): Observable<ApiResponse<AnnotationProject[]>> {
    return this.http.get<ApiResponse<AnnotationProject[]>>(`${this.apiBaseUrl}/annotation/projects`);
  }

  listTasks(projectId?: string): Observable<ApiResponse<AnnotationTask[]>> {
    const params = projectId ? new HttpParams().set('project_id', projectId) : undefined;

    return this.http.get<ApiResponse<AnnotationTask[]>>(`${this.apiBaseUrl}/annotation/tasks`, {
      params,
    });
  }

  listObjects(taskId?: string): Observable<ApiResponse<AnnotationObject[]>> {
    const params = taskId ? new HttpParams().set('task_id', taskId) : undefined;

    return this.http.get<ApiResponse<AnnotationObject[]>>(`${this.apiBaseUrl}/annotation/objects`, {
      params,
    });
  }

  listLabels(): Observable<ApiResponse<string[]>> {
    return this.http.get<ApiResponse<string[]>>(`${this.apiBaseUrl}/annotation/labels`);
  }

  createObject(
    request: AnnotationObjectCreateRequest
  ): Observable<ApiResponse<AnnotationObject>> {
    return this.http.post<ApiResponse<AnnotationObject>>(
      `${this.apiBaseUrl}/annotation/objects`,
      request
    );
  }

  updateObjectStatus(
    objectId: string,
    status: 'pending' | 'approved' | 'rejected'
  ): Observable<ApiResponse<AnnotationObject>> {
    return this.http.patch<ApiResponse<AnnotationObject>>(
      `${this.apiBaseUrl}/annotation/objects/${objectId}/status`,
      { status }
    );
  }

  deleteObject(objectId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiBaseUrl}/annotation/objects/${objectId}`);
  }
}
