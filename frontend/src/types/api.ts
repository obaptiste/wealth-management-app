// types/api.ts
export interface User {
    id: number;
    username: string;
    email: string;
    is_active: boolean;
    is_superuser: boolean;
    created_at: string;
    updated_at: string;
}

export interface ApiResponse<T> {
  data: T;
  status: number;
  message: string;
  error?: string;
}
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// API client types

/**
 * ApiClientResponse<T> is used in the following scenarios:
 * 
 * 1. When defining API client function return types:
 *    - API functions should return Promise<ApiClientResponse<T>>
 * 
 * 2. When consuming API responses:
 *    - Helps with type safety when destructuring the data property
 *    - Example: const { data } = await apiClient.get<User>('/auth/me');
 * 
 * 3. When implementing mock API responses for testing:
 *    - Ensures test data matches the expected API response format
 */
export interface ApiClientResponse<T> {
  data: T;
  // Add other common response properties if needed
  // status?: number;
  // message?: string;
}

export interface ApiClientOptions {
  headers?: Record<string, string>;
  [key: string]: unknown;
}

export interface ApiClient {
  get<T>(url: string, options?: ApiClientOptions): Promise<ApiClientResponse<T>>;
  post<T, D = unknown>(url: string, data: D, options?: ApiClientOptions): Promise<ApiClientResponse<T>>;
}

/**
 * Authentication response from login endpoint
 */
export interface AuthResponse {
  access_token: string;
  token_type: string;
}

/**
 * User response containing user data
 */
export interface UserResponse {
  user: User;
}

