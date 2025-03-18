// contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/router';
import api from '../lib/api';
import { User } from '../types/api';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (username: string, email: string, password: string) => Promise<void>;
}

export interface ApiError {
    response: {
      data: {
        detail: string;
      };
    };
  }
  

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        if (typeof window !== 'undefined' && localStorage.getItem('token')) {
          const { data } = await api.get<User>('/auth/me');
          setUser(data);
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
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);
      
      const { data } = await api.post('/auth/token', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      
      localStorage.setItem('token', data.access_token);
      
      const userResponse = await api.get<User>('/auth/me');
      setUser(userResponse.data);
      router.push('/dashboard');
    } catch (err: unknown) {
      setError((err as ApiError).response?.data?.detail || 'Login failed');
      throw err;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    router.push('/login');
  };

  const register = async (username: string, email: string, password: string) => {
    try {
      setError(null);
      await api.post('/auth/register', { username, email, password });
      await login(email, password);
    } catch (err: unknown) {
      setError((err as ApiError).response?.data?.detail || 'Registration failed');
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