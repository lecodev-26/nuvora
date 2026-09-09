import api from './api';

export const authService = {
  register: (data) => api.post('/auth/register', data),
  login: (email, password) => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    return api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
  },
  getMe: (token) => api.get('/auth/me', {
    headers: { 'Authorization': `Bearer ${token}` }
  })
};
