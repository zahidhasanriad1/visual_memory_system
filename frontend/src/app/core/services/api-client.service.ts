import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_CONFIG } from '../config/api.config';
import { ApiResponse } from '../types/api-response.type';

@Injectable({ providedIn: 'root' })
export class ApiClientService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = API_CONFIG.baseUrl;

  get<T>(path: string, params?: Record<string, string | number | boolean | null | undefined>): Observable<ApiResponse<T>> {
    let httpParams = new HttpParams();
    Object.entries(params ?? {}).forEach(([key, value]) => { if (value !== null && value !== undefined && value !== '') httpParams = httpParams.set(key, String(value)); });
    return this.http.get<ApiResponse<T>>(`${this.baseUrl}${path}`, { params: httpParams });
  }
  post<T>(path: string, body: unknown): Observable<ApiResponse<T>> { return this.http.post<ApiResponse<T>>(`${this.baseUrl}${path}`, body); }
  postForm<T>(path: string, formData: FormData): Observable<ApiResponse<T>> { return this.http.post<ApiResponse<T>>(`${this.baseUrl}${path}`, formData); }
}
