// contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api';
import { User } from '@/types/api';
import { AuthContextType } from '@/types/auth';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Create API functions instead of calling methods directly on axios
const getCurrentUser = async () => {
  const response = await apiClient.get('/api/auth/current-user');
  return response.data;
};

const loginApi = async (credentials: { username: string; password: string }) => {
  const response = await apiClient.post('/api/auth/login', credentials);
  return response.data;
};

const logoutApi = async () => {
  const response = await apiClient.post('/api/auth/logout');
  return response.data;
};

const registerApi = async (userData: { username: string; email: string; password: string }) => {
  const response = await apiClient.post('/api/auth/register', userData);
  return response.data;
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        if (typeof window !== 'undefined' && localStorage.getItem('token')) {
          const userData = await getCurrentUser();
          setUser(userData);
        }
      } catch (err) {
        console.error('Error checking auth:', err);
        localStorage.removeItem('token');
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      setError(null);
      setLoading(true);

      const response = await loginApi({ username: email, password });

      const userData = await getCurrentUser();
      setUser(userData);

      router.push('/dashboard');
      return response;
    } catch (err: unknown) {
      if (err instanceof Error) {
        if (err.message.includes('credentials')) {
          setError('Invalid email or password');
        } else {
          setError(err.message);
        }
      } else {
        setError('Login failed. Please try again.');
      }
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    await logoutApi();
    setUser(null);
    router.push('/login');
  };

  const register = async (username: string, email: string, password: string) => {
    try {
      setError(null);

      const registerResponse = await registerApi({ username, email, password });

      await login(email, password);

      return registerResponse;
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Registration failed';
      setError(errorMessage);
      throw err;
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, error, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};