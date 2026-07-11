import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiClientService } from './api-client.service';
import { VideoJobResponse, VideoJobStatus, VideoMemoryResult, VideoProcessingSettings } from '../types/video-memory.type';
import { ApiResponse } from '../types/api-response.type';

@Injectable({ providedIn: 'root' })
export class VideoMemoryService {
  private readonly api = inject(ApiClientService);
  createJob(file: File, settings: VideoProcessingSettings): Observable<ApiResponse<VideoJobResponse>> {
    const formData = new FormData();
    formData.append('file', file);
    Object.entries(settings).forEach(([key, value]) => formData.append(key, String(value)));
    return this.api.postForm<VideoJobResponse>('/video-memory/jobs/ingest-video', formData);
  }
  status(jobId: string): Observable<ApiResponse<VideoJobStatus>> { return this.api.get<VideoJobStatus>(`/video-memory/jobs/${jobId}`); }
  result(jobId: string): Observable<ApiResponse<VideoMemoryResult>> { return this.api.get<VideoMemoryResult>(`/video-memory/jobs/${jobId}/result`); }
}
