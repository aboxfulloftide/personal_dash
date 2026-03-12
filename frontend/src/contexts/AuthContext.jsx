import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setLoading(false);
        return;
      }
      const response = await api.get('/auth/me');
      setUser(response.data);
    } catch (error) {
      // Only clear auth if refresh token is also missing (meaning refresh failed)
      // If refresh token exists, the interceptor will handle the refresh
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        localStorage.removeItem('access_token');
        setUser(null);
      }
      // If we have refresh token, the axios interceptor will handle it
      // and we'll just retry this call
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  // Update document title based on user
  useEffect(() => {
    if (user?.display_name) {
      document.title = `${user.display_name}'s Dash`;
    } else {
      document.title = 'Personal Dash';
    }
  }, [user]);

  // Update favicon based on user preference, with local cache fallback
  useEffect(() => {
    const link = document.querySelector("link[rel~='icon']");
    if (!link) return;

    const faviconUrl = user?.favicon_url;

    if (!faviconUrl) {
      localStorage.removeItem('favicon_cache');
      link.href = '/vite.svg';
      return;
    }

    // Apply cached version immediately so there's no flicker
    const cached = localStorage.getItem('favicon_cache');
    if (cached) {
      try {
        const { url, dataUrl } = JSON.parse(cached);
        if (url === faviconUrl) {
          link.href = dataUrl;
        }
      } catch {
        localStorage.removeItem('favicon_cache');
      }
    }

    // Fetch and cache as data URL
    fetch(faviconUrl)
      .then((res) => res.blob())
      .then((blob) => {
        const reader = new FileReader();
        reader.onloadend = () => {
          const dataUrl = reader.result;
          try {
            localStorage.setItem('favicon_cache', JSON.stringify({ url: faviconUrl, dataUrl }));
          } catch {
            // localStorage full — skip caching
          }
          link.href = dataUrl;
        };
        reader.readAsDataURL(blob);
      })
      .catch(() => {
        // Fetch failed — keep cached version if available, else use original URL
        const cached = localStorage.getItem('favicon_cache');
        if (!cached) {
          link.href = faviconUrl;
        }
      });
  }, [user?.favicon_url]);

  const login = async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    localStorage.setItem('access_token', response.data.access_token);
    localStorage.setItem('refresh_token', response.data.refresh_token);
    await fetchUser();
    return response.data;
  };

  const register = async (email, password, displayName) => {
    const response = await api.post('/auth/register', {
      email,
      password,
      display_name: displayName
    });
    return response.data;
  };

  const logout = async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        await api.post('/auth/logout', { refresh_token: refreshToken });
      }
    } catch (error) {
      // Ignore errors on logout
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('favicon_cache');
    setUser(null);
  };

  const updateUser = async (updates) => {
    const response = await api.patch('/auth/me', updates);
    setUser(response.data);
    return response.data;
  };

  const refreshToken = async () => {
    try {
      const refresh_token = localStorage.getItem('refresh_token');
      if (!refresh_token) {
        throw new Error('No refresh token available');
      }
      const response = await api.post('/auth/refresh', { refresh_token });
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('refresh_token', response.data.refresh_token);
      return response.data.access_token;
    } catch (error) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
      throw error;
    }
  };

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    refreshToken,
    updateUser,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
