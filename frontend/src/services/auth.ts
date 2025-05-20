// src/services/auth.ts
import { api } from './api'

export interface LoginCredentials {
  username: string
  password: string
}

export interface RegisterCredentials {
  username: string
  email: string
  phone: string
  password: string
  password_confirm: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user_id: string
  username: string
  email: string
  phone?: string
}

export interface RegistrationResponse {
  message: string
  email: string
}

const TOKEN_KEY = 'agent_framework_token'
const USER_KEY = 'agent_framework_user'

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const formData = new URLSearchParams()
    formData.append('username', credentials.username)
    formData.append('password', credentials.password)

    const response = await api.post<AuthResponse>(
      '/api/auth/token',
      formData,
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    )

    if (!response?.data) {
      throw new Error('No response data received from login')
    }

    this.saveToken(response.data.access_token)
    this.saveUser({
      id: response.data.user_id,
      username: response.data.username,
      email: response.data.email,
      phone: response.data.phone
    })

    return response.data
  },

  async register(credentials: RegisterCredentials): Promise<RegistrationResponse> {
    const response = await api.post<RegistrationResponse>('/api/auth/register', credentials)
    
    if (!response?.data) {
      throw new Error('No response data received from registration')
    }

    return response.data;
  },

  saveToken(token: string): void {
    console.log('Full token before save:', token);
    try {
      // Save to localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem(TOKEN_KEY, token)
      }
      
      // Save to cookie
      document.cookie = `token=${token}; path=/; max-age=86400` // 24 hours
    } catch (err) {
      console.error('Error saving token:', err)
    }
  },

  saveUser(user: { id: string, username: string, email: string, phone?: string }): void {
    try {
      if (typeof window !== 'undefined') {
        localStorage.setItem(USER_KEY, JSON.stringify(user))
      }
    } catch (err) {
      console.error('Error saving user:', err)
    }
  },

  getToken(): string | null {
    try {
      if (typeof window !== 'undefined') {
        // Try cookie first
        const cookieToken = document.cookie
          .split('; ')
          .find(row => row.startsWith('token='))
          ?.split('=')[1]

        if (cookieToken) {
          return cookieToken
        }

        // Fallback to localStorage
        const token = localStorage.getItem(TOKEN_KEY)
        if (token) {
          // If found in localStorage but not in cookie, restore the cookie
          this.saveToken(token)
        }
        return token
      }
    } catch (err) {
      console.error('Error getting token:', err)
    }
    return null
  },

  getUser(): { id: string, username: string, email: string, phone?: string } | null {
    try {
      if (typeof window !== 'undefined') {
        const userStr = localStorage.getItem(USER_KEY)
        return userStr ? JSON.parse(userStr) : null
      }
    } catch (err) {
      console.error('Error getting user:', err)
    }
    return null
  },
  
  async requestPasswordReset(email: string): Promise<void> {
    await api.post('/api/auth/request-password-reset', { email });
  },

  async resetPassword(token: string, newPassword: string): Promise<void> {
    await api.post('/api/auth/reset-password', { 
        token, 
        new_password: newPassword 
    });
 },

  removeToken(): void {
    try {
      if (typeof window !== 'undefined') {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
        document.cookie = 'token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;'
      }
    } catch (err) {
      console.error('Error removing token:', err)
    }
  },

  isAuthenticated(): boolean {
    return !!this.getToken()
  }
}
