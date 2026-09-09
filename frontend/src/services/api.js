import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para añadir token automáticamente
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('nuvora_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const botService = {
  create: (data) => api.post('/bots/', data),
  list: () => api.get('/bots/'),
  get: (id) => api.get(`/bots/${id}`),
};

export const memoryService = {
  add: (data) => api.post('/memories/', data),
  getByBot: (botId) => api.get(`/memories/${botId}`),
};

export const askService = {
  ask: (botId, question) => api.post('/ask/', { bot_id: botId, question }),
};

export default api;
