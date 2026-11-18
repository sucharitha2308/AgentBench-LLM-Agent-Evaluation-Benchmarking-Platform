import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT access token to all outgoing requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('agentbench_access_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor to handle 401 Unauthorized
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token if expired or invalid
      if (!window.location.pathname.includes('/auth')) {
        localStorage.removeItem('agentbench_access_token');
        localStorage.removeItem('agentbench_refresh_token');
        window.location.href = '/auth';
      }
    }
    return Promise.reject(error);
  }
);
