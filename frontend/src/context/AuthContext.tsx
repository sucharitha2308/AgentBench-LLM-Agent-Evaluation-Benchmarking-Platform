import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from '../services/api';
import { User } from '../types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  loginAsDemo: () => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchProfile = async () => {
    try {
      const token = localStorage.getItem('agentbench_access_token');
      if (!token) {
        setIsLoading(false);
        return;
      }
      const res = await apiClient.get<User>('/auth/me');
      setUser(res.data);
    } catch (err) {
      localStorage.removeItem('agentbench_access_token');
      localStorage.removeItem('agentbench_refresh_token');
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const res = await apiClient.post<{ access_token: string; refresh_token: string }>('/auth/login', {
        email,
        password,
      });
      localStorage.setItem('agentbench_access_token', res.data.access_token);
      localStorage.setItem('agentbench_refresh_token', res.data.refresh_token);
      await fetchProfile();
    } finally {
      setIsLoading(false);
    }
  };

  const loginAsDemo = async () => {
    await login('demo@agentbench.ai', 'agentbench123');
  };

  const register = async (email: string, password: string, fullName?: string) => {
    setIsLoading(true);
    try {
      await apiClient.post('/auth/register', {
        email,
        password,
        full_name: fullName,
      });
      // Immediately log in upon successful registration
      await login(email, password);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('agentbench_access_token');
    localStorage.removeItem('agentbench_refresh_token');
    setUser(null);
    window.location.href = '/auth';
  };

  const refreshProfile = async () => {
    await fetchProfile();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        loginAsDemo,
        register,
        logout,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
