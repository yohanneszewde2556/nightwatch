import React, { createContext, useContext, useEffect, useState } from 'react';
import { apiClient } from '../api/client';

interface AuthContextType {
  isAuthenticated: boolean;
  login: (password: string) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(apiClient.isAuthenticated());

  useEffect(() => {
    const handleUnauthorized = () => {
      setIsAuthenticated(false);
    };
    window.addEventListener('nightwatch:unauthorized', handleUnauthorized);
    return () => {
      window.removeEventListener('nightwatch:unauthorized', handleUnauthorized);
    };
  }, []);

  const login = async (password: string): Promise<boolean> => {
    const success = await apiClient.verifyPassword(password);
    if (success) {
      setIsAuthenticated(true);
    }
    return success;
  };

  const logout = () => {
    apiClient.clearToken();
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
