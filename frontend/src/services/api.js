import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Servicios para Bots
export const botService = {
  create: (data) => api.post('/bots/', data),
  list: () => api.get('/bots/'),
  get: (id) => api.get(`/bots/${id}`),
};

// Servicios para Memorias
export const memoryService = {
  add: (data) => api.post('/memories/', data),
  getByBot: (botId) => api.get(`/memories/${botId}`),
};

// Servicios para Preguntas
export const askService = {
  ask: (botId, question) => api.post('/ask/', { bot_id: botId, question }),
};

export default api;
