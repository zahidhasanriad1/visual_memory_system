export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export interface RegisterRequest {
  full_name: string;
  email: string;
  password: string;
  role: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  full_name: string;
  email: string;
  role: string;
}

export interface UserProfile {
  user_id: string;
  full_name: string;
  email: string;
  role: string;
  is_active: boolean;
}
