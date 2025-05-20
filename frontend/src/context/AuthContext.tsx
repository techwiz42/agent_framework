// src/context/AuthContext.tsx
import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { authService, LoginCredentials, RegisterCredentials } from '@/services/auth';
import { RegistrationResponse } from '@/types';

interface AuthState {
  token: string | null;
  isAuthenticated: boolean;
  user: {
    id: string;
    username: string;
    email: string;
    phone?: string;
    role: string;
  } | null;
  isInitialized: boolean;
  isLoading: boolean;
  error: string | null;
}

interface AuthContextValue extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<RegistrationResponse>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [authState, setAuthState] = useState<AuthState>({
    token: null,
    user: null,
    isInitialized: false,
    isLoading: true,
    isAuthenticated: false,
    error: null
  });
  const router = useRouter();

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const savedToken = authService.getToken();
        if (savedToken) {
          try {
            const tokenData = JSON.parse(atob(savedToken.split('.')[1]));
            setAuthState(prev => ({
              ...prev,
              token: savedToken,
              user: {
                id: tokenData.user_id,
                username: tokenData.sub,
                email: tokenData.email,
                phone: tokenData.phone,
                role: tokenData.role
              },
              isInitialized: true,
              isLoading: false
            }));
          } catch (e) {
            console.error('Failed to parse token:', e);
            authService.removeToken();
            setAuthState(prev => ({
              ...prev,
              isInitialized: true,
              isLoading: false
            }));
          }
        } else {
          setAuthState(prev => ({
            ...prev,
            isInitialized: true,
            isLoading: false
          }));
        }
      } catch (e) {
        console.error('Auth initialization error:', e);
        setAuthState(prev => ({
          ...prev,
          error: e instanceof Error ? e.message : 'Failed to initialize authentication',
          isInitialized: true,
          isLoading: false
        }));
      }
    };

    initializeAuth();
  }, []);

  useEffect(() => {
    const checkTokenExpiration = () => {
      const token = authService.getToken();
      if (token) {
        const decodedToken = JSON.parse(atob(token.split('.')[1]));
        const currentTime = Date.now() / 1000;
        if (decodedToken.exp < currentTime) {
          logout();
        }
      }
    };

    // Check token expiration every minute
    const intervalId = setInterval(checkTokenExpiration, 60 * 1000);

    return () => {
      clearInterval(intervalId);
    };
  });

  const login = async (credentials: LoginCredentials) => {
    try {
      setAuthState(prev => ({ ...prev, isLoading: true, error: null }));
      const response = await authService.login(credentials);
      
      const tokenData = JSON.parse(atob(response.access_token.split('.')[1]));
      setAuthState({
        token: response.access_token,
        user: {
          id: tokenData.user_id,
          username: tokenData.sub,
          email: tokenData.email,
          phone: tokenData.phone,
          role: tokenData.role
        },
        isAuthenticated: true,
        isInitialized: true,
        isLoading: false,
        error: null
      });
      
      router.push('/conversations');
    } catch (err) {
      console.error('Login error:', err);
      setAuthState(prev => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : 'Failed to login'
      }));
      throw err;
    }
  };

  const register = async (credentials: RegisterCredentials): Promise<RegistrationResponse> => {
    try {
      setAuthState(prev => ({ ...prev, isLoading: true, error: null }));
      const response = await authService.register(credentials);
      setAuthState(prev => ({ ...prev, isLoading: false }));
      return response;
    } catch (err) {
      console.error('Registration error:', err);
      setAuthState(prev => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : 'Failed to register'
      }));
      throw err;
    }
  };

  const logout = () => {
    authService.removeToken();
    setAuthState({
      token: null,
      user: null,
      isInitialized: true,
      isLoading: false,
      isAuthenticated: false,
      error: null
    });
    router.push('/login');
  };

  // Don't render children until auth is initialized
  if (!authState.isInitialized) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  return (
    <AuthContext.Provider 
      value={{ 
        ...authState,
        login, 
        register, 
        logout 
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
