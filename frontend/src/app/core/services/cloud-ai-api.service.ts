import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import {
  ApiResponse,
  CloudAiAgent,
  CloudAiAgentName,
  CloudAiConnectivity,
  CloudAiHealth,
  CloudAiImageAnalysisResult,
  CloudAiProviderName,
  CloudAiTextSummaryResult,
} from '../types/cloud-ai/cloud-ai.types';
import { Observable } from 'rxjs';
import { API_CONFIG } from '../config/api.config';

@Injectable({
  providedIn: 'root',
})
export class CloudAiApiService {
  private readonly apiBaseUrl = API_CONFIG.baseUrl;

  constructor(private readonly http: HttpClient) {}

  getHealth(): Observable<ApiResponse<CloudAiHealth>> {
    return this.http.get<ApiResponse<CloudAiHealth>>(
      `${this.apiBaseUrl}/cloud-ai/health`
    );
  }

  getAgents(): Observable<ApiResponse<CloudAiAgent[]>> {
    return this.http.get<ApiResponse<CloudAiAgent[]>>(
      `${this.apiBaseUrl}/cloud-ai/agents`
    );
  }

  checkConnectivity(): Observable<ApiResponse<CloudAiConnectivity[]>> {
    return this.http.post<ApiResponse<CloudAiConnectivity[]>>(
      `${this.apiBaseUrl}/cloud-ai/connectivity`,
      {}
    );
  }

  analyzeImage(
    file: File,
    provider: CloudAiProviderName,
    agentName: CloudAiAgentName,
    context: string,
    detail: string
  ): Observable<ApiResponse<CloudAiImageAnalysisResult>> {
    const formData = new FormData();

    formData.append('file', file);
    formData.append('provider', provider);
    formData.append('agent_name', agentName);
    formData.append('detail', detail);

    if (context.trim()) {
      formData.append('context', context.trim());
    }

    return this.http.post<ApiResponse<CloudAiImageAnalysisResult>>(
      `${this.apiBaseUrl}/cloud-ai/analyze-image`,
      formData
    );
  }

  summarizeReport(
    reportText: string,
    provider: CloudAiProviderName,
    agentName: CloudAiAgentName,
    context: string
  ): Observable<ApiResponse<CloudAiTextSummaryResult>> {
    const formData = new FormData();

    formData.append('report_text', reportText);
    formData.append('provider', provider);
    formData.append('agent_name', agentName);

    if (context.trim()) {
      formData.append('context', context.trim());
    }

    return this.http.post<ApiResponse<CloudAiTextSummaryResult>>(
      `${this.apiBaseUrl}/cloud-ai/summarize-report`,
      formData
    );
  }
}
