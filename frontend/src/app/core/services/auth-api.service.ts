import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Router } from '@angular/router';
import {
  ApiResponse,
  AuthResponse,
  RegisterRequest,
  UserProfile,
} from '../types/auth/auth.types';
import { Observable, tap } from 'rxjs';
import { API_CONFIG } from '../config/api.config';

@Injectable({
  providedIn: 'root',
})
export class AuthApiService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  private readonly apiBaseUrl = API_CONFIG.baseUrl;
  private readonly tokenKey = 'vms_x_access_token';
  private readonly userKey = 'vms_x_user';

  register(request: RegisterRequest): Observable<ApiResponse<AuthResponse>> {
    return this.http
      .post<ApiResponse<AuthResponse>>(`${this.apiBaseUrl}/auth/register`, request)
      .pipe(tap((response) => this.saveAuthResponse(response)));
  }

  loginForm(email: string, password: string): Observable<ApiResponse<AuthResponse>> {
    const body = new HttpParams()
      .set('username', email)
      .set('password', password);

    return this.http
      .post<ApiResponse<AuthResponse>>(
        `${this.apiBaseUrl}/auth/login/form`,
        body.toString(),
        {
          headers: new HttpHeaders({
            'Content-Type': 'application/x-www-form-urlencoded',
          }),
        }
      )
      .pipe(tap((response) => this.saveAuthResponse(response)));
  }

  me(): Observable<ApiResponse<UserProfile>> {
    return this.http.get<ApiResponse<UserProfile>>(`${this.apiBaseUrl}/auth/me`);
  }

  logout(): void {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.userKey);
    this.router.navigateByUrl('/login');
  }

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  isLoggedIn(): boolean {
    return !!this.getToken();
  }

  getStoredRole(): string {
    return this.getStoredUser()?.role?.toLowerCase() || 'viewer';
  }

  hasAnyRole(roles: string[] | undefined): boolean {
    if (!roles?.length) {
      return true;
    }

    return roles.map((role) => role.toLowerCase()).includes(this.getStoredRole());
  }

  getStoredUser(): AuthResponse | null {
    const raw = localStorage.getItem(this.userKey);

    if (!raw) {
      return null;
    }

    try {
      return JSON.parse(raw) as AuthResponse;
    } catch {
      return null;
    }
  }

  private saveAuthResponse(response: ApiResponse<AuthResponse>): void {
    if (!response.success || !response.data?.access_token) {
      return;
    }

    localStorage.setItem(this.tokenKey, response.data.access_token);
    localStorage.setItem(this.userKey, JSON.stringify(response.data));
  }
}
