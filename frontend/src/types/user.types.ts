// src/types/user.types.ts

// Basic user information
export interface User {
  id: string;
  username: string;
  email: string;
  created_at: string;
  last_login?: string;
  is_active: boolean;
  email_verified: boolean;
}

// Response from token endpoints
export interface TokenResponse {
  tokens_remaining: number;
  tokens_used?: number;
  last_updated?: string;
}

// User profile/settings
export interface UserProfile {
  id: string;
  username: string;
  email: string;
  settings?: UserSettings;
}

// User settings/preferences
export interface UserSettings {
  notifications_enabled?: boolean;
  theme?: 'light' | 'dark' | 'system';
  language?: string;
  timezone?: string;
}

// Authentication response
export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  username: string;
  email: string;
}

// Registration data
export interface RegistrationData {
  username: string;
  email: string;
  password: string;
}

// Login credentials
export interface LoginCredentials {
  username: string;
  password: string;
}

// Password update data
export interface PasswordUpdateData {
  current_password: string;
  new_password: string;
}
