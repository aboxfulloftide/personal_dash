import axios from 'axios';
import { AuthService } from './AuthService';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  withCredentials: true,
});

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Request interceptor for auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken'); // Note: Changed from access_token to accessToken for consistency with AuthContext
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let onTokenRefreshFailureCallback = null;

export const setOnTokenRefreshFailure = (callback) => {
  onTokenRefreshFailureCallback = callback;
};

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Check if the error is 401 Unauthorized and not a refresh request itself
    if (error.response?.status === 401 && originalRequest.url !== '/auth/refresh') {
      if (isRefreshing) {
        return new Promise(function(resolve, reject) {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers['Authorization'] = 'Bearer ' + token;
          return api(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }

      isRefreshing = true;

      return new Promise(async (resolve, reject) => {
        try {
          const newAccessToken = await AuthService.refreshToken();
          localStorage.setItem('accessToken', newAccessToken);
          api.defaults.headers.common['Authorization'] = 'Bearer ' + newAccessToken;
          originalRequest.headers['Authorization'] = 'Bearer ' + newAccessToken;
          processQueue(null, newAccessToken);
          resolve(api(originalRequest));
        } catch (refreshError) {
          processQueue(refreshError);
          if (onTokenRefreshFailureCallback) {
            onTokenRefreshFailureCallback(); // Call the logout function from AuthContext
          }
          reject(refreshError);
        } finally {
          isRefreshing = false;
        }
      });
    }

    return Promise.reject(error);
  }
);

export default api;
