// contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api';
import { User } from '@/types/api';
import { AuthContextType } from '@/types/auth';

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
          const userData = await apiClient.getCurrentUser();
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

      const response = await apiClient.login(email, password);
      localStorage.setItem('token', response.access_token);

      const userData = await apiClient.getCurrentUser();
      setUser(userData);

      router.push('/dashboard');
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
    localStorage.removeItem('token');
    setUser(null);
    router.push('/login');
  };

  const register = async (username: string, email: string, password: string) => {
    try {
      setError(null);

      await apiClient.register(username, email, password);
      await login(email, password);
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
