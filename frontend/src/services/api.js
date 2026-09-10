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

// ============================================================
// BOTS
// ============================================================
export const botService = {
  create: (data) => api.post('/bots/', data),
  list: () => api.get('/bots/'),
  get: (id) => api.get(`/bots/${id}`),
};

// ============================================================
// MEMORIES
// ============================================================
export const memoryService = {
  add: (data) => api.post('/memories/', data),
  getByBot: (botId) => api.get(`/memories/${botId}`),
};

// ============================================================
// ASK
// ============================================================
export const askService = {
  ask: (botId, question) => api.post('/ask/', { bot_id: botId, question }),
};

// ============================================================
// TRAINING ASSISTANT (14.4.7)
// ============================================================
export const trainingService = {
  getReport: (botId, conversationLimit = 100) =>
    api.get(`/training/${botId}`, {
      params: { conversation_limit: conversationLimit },
    }),
};

export default api;
