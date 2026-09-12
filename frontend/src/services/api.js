import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor de petición: añade token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('nuvora_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor de respuesta: maneja 401 globalmente
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 401 → token expirado o inválido
    if (error.response?.status === 401) {
      // Limpiar token y redirigir a login
      const hadToken = localStorage.getItem('nuvora_token');
      localStorage.removeItem('nuvora_token');

      // Solo redirigir si no estamos ya en /login
      if (hadToken && !window.location.pathname.startsWith('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

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
