import axios from 'axios';

// Create axios instance with base URL from environment variable
export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token to requests
api.interceptors.request.use(
  (config) => {
    // Get token from localStorage (in browser context only)
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle token expiration
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    // Handle 401 errors (unauthorized)
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      // Redirect to login page
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auth_token');
        window.location.href = '/auth/login';
      }
      
      return Promise.reject(error);
    }
    
    return Promise.reject(error);
  }
);

// Generic API functions

// GET request
export const get = async<T>(url: string, params?: any): Promise<T> => {
  const response = await api.get<T>(url, { params });
  return response.data;
};

// POST request
export const post = async<T>(url: string, data?: any): Promise<T> => {
  const response = await api.post<T>(url, data);
  return response.data;
};

// PUT request
export const put = async<T>(url: string, data?: any): Promise<T> => {
  const response = await api.put<T>(url, data);
  return response.data;
};

// DELETE request
export const del = async<T>(url: string): Promise<T> => {
  const response = await api.delete<T>(url);
  return response.data;
};

// Upload file
export const uploadFile = async<T>(url: string, file: File, additionalData?: Record<string, any>): Promise<T> => {
  const formData = new FormData();
  formData.append('file', file);
  
  if (additionalData) {
    Object.entries(additionalData).forEach(([key, value]) => {
      formData.append(key, value);
    });
  }
  
  const response = await api.post<T>(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
};

// Conversation-specific API calls

// Get all conversations for the current user
export interface ConversationsResponse {
  conversations: Conversation[];
}

export const getConversations = async (): Promise<ConversationsResponse> => {
  return get<ConversationsResponse>('/conversations');
};

// Get a specific conversation by ID
export const getConversation = async (id: string) => {
  return get(`/conversations/${id}`);
};

// Get all messages for a conversation
export const getConversationMessages = async (id: string) => {
  return get(`/conversations/${id}/messages`);
};

// Create a new conversation
export interface ConversationCreateParams {
  title: string;
  description?: string;
  participants?: { email: string; name?: string }[];
  agent_types?: string[];
}

export interface Conversation {
  id: string;
  title: string;
  description?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  creator_id: string;
  [key: string]: any; // Allow for additional properties
}

export const createConversation = async (params: ConversationCreateParams): Promise<Conversation> => {
  return post<Conversation>('/conversations', params);
};

// Delete a conversation
export const deleteConversation = async (id: string) => {
  return del(`/conversations/${id}`);
};

// Add a participant to a conversation
export const addParticipant = async (conversationId: string, email: string, name?: string) => {
  return post(`/conversations/${conversationId}/add-participant`, { email, name });
};

// Remove a participant from a conversation
export const removeParticipant = async (conversationId: string, email: string) => {
  // DELETE request with body is not standard, so we need to use post with a delete method
  // or adjust the implementation based on the API's requirements
  return post(`/conversations/${conversationId}/remove-participant`, { email });
};

// Send invitations to all participants in a conversation
export const sendInvitations = async (conversationId: string) => {
  return post(`/conversations/${conversationId}/send-invitations`);
};

// Join a conversation using an invitation token
export const joinConversation = async (token: string, name?: string) => {
  return post('/conversations/join', { invitation_token: token, name });
};