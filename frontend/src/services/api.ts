import { ApiResponse } from '@/types';

type ApiRequestOptions = RequestInit & {
  params?: URLSearchParams | Record<string, string>;
};

async function fetchApi<T>(
  endpoint: string,
  options: ApiRequestOptions = {}
): Promise<ApiResponse<T>> {
  const cleanEndpoint = endpoint
    .replace(/^\/+/, '')
    .replace(/^api\//, '');

  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://dev.agentframework.ai:8001';

  // Construct URL with query parameters if they exist
  const url = new URL(`${baseUrl}/api/${cleanEndpoint}`);
  if (options.params) {
    const params = options.params instanceof URLSearchParams 
      ? options.params 
      : new URLSearchParams(options.params);
    
    params.forEach((value, key) => {
      url.searchParams.append(key, value);
    });
  }

  try {
    const response = await fetch(url.toString(), {
      ...options,
      headers: {
	...(!(options.body instanceof FormData) && { 'Content-Type': 'application/json' }),
        ...options.headers,
      },
    });

    // Handle 204 No Content
    if (response.status === 204) {
      return { data: null } as ApiResponse<T>;
    }

    const data = await response.json() as T | { detail: string };

    if (!response.ok) {
      throw new Error(
        typeof data === 'object' && data !== null && 'detail' in data
          ? (data as { detail: string }).detail
          : (typeof data === 'object' ? JSON.stringify(data, null, 2) : String(data)) ||
       'An error occurred'
    );
  }

    return { data: data as T };
  } catch (err) {
    console.error('Fetch Error:', err);
    throw err;
  }
}

export const api = {
  get: <T>(endpoint: string, options: RequestInit & { params?: URLSearchParams | Record<string, string> } = {}) => {
    const { params, ...fetchOptions } = options;
    const queryParams = params instanceof URLSearchParams 
      ? params 
      : params 
        ? new URLSearchParams(params) 
        : undefined;

    const url = queryParams 
      ? `${endpoint}?${queryParams.toString()}` 
      : endpoint;

    return fetchApi<T>(url, {
      ...fetchOptions,
      method: 'GET'
    });
  },
    
  post: <T>(endpoint: string, data?: unknown, options?: RequestInit) =>
    fetchApi<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data instanceof FormData || data instanceof URLSearchParams ? data : JSON.stringify(data),
    }),

  login: (username: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    return api.post<{
      access_token: string;
      token_type: string;
      user_id: string;
      username: string;
      email: string;
    }>('/auth/token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      }
    });
  },
    
  put: <T>(endpoint: string, data?: unknown, options?: RequestInit) =>
    fetchApi<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  patch: <T>(endpoint: string, data?: unknown, options?: RequestInit) =>
    fetchApi<T>(endpoint, {
      ...options,
      method: 'PATCH', 
      body: JSON.stringify(data),
    }),
    
  delete: <T>(endpoint: string, options?: RequestInit) =>
    fetchApi<T>(endpoint, { ...options, method: 'DELETE' }),

  createCheckoutSession: (productKey: string) => 
    api.post<{ checkout_url: string }>('billing/create-checkout-session', { product_key: productKey }),

  // Admin endpoints
  admin: {
    getHealth: (options?: RequestInit) =>
      fetchApi<{
        status: string;
        version: string;
        uptime: string;
        memory_usage: string;
      }>('/admin/health', {
        ...options,
        method: 'GET',
      }),
    getStatus: (options?: RequestInit) =>
      fetchApi<{
        api_status: {
          status: 'healthy' | 'degraded' | 'down';
          response_time: string;
          last_checked: string;
        };
        database_status: {
          status: 'healthy' | 'degraded' | 'down';
          connections: number;
          last_checked: string;
        };
        cache_status: {
          status: 'healthy' | 'degraded' | 'down';
          hit_rate: string;
          last_checked: string;
        };
        message_queue_status: {
          status: 'healthy' | 'degraded' | 'down';
          queue_size: number;
          last_checked: string;
        };
      }>('/admin/status', {
        ...options, 
        method: 'GET',
      }), 
    getMetrics: (options?: RequestInit) =>
      fetchApi<{
        total_users: number;
        active_conversations: number;
        api_calls_24h: number;
      }>('/admin/metrics', {
        ...options,
        method: 'GET',
      }),
  },
};

export function getAuthHeaders(token: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
  };
}
