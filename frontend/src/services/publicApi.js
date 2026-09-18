/**
 * publicApi — Cliente HTTP para endpoints /public/* (sin JWT)
 *
 * Endpoints (14.9.8):
 *   GET    /public/bots/{identifier}              → info pública + config
 *   POST   /public/bots/{identifier}/session      → crear sesión
 *   POST   /public/bots/{identifier}/message      → enviar mensaje
 *   DELETE /public/bots/{identifier}/session      → cerrar sesión
 *
 * NO usa el interceptor de token (es público).
 * SÍ hereda baseURL del api por conveniencia.
 */

import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const publicHttp = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

export const publicApi = {
  /** Info pública de un bot publicado. */
  getBot: (identifier) =>
    publicHttp.get(`/public/bots/${encodeURIComponent(identifier)}`),

  /** Crea una sesión anónima. */
  createSession: (identifier) =>
    publicHttp.post(`/public/bots/${encodeURIComponent(identifier)}/session`, {}),

  /** Envía un mensaje al bot. */
  sendMessage: (identifier, sessionId, message) =>
    publicHttp.post(`/public/bots/${encodeURIComponent(identifier)}/message`, {
      session_id: sessionId,
      message,
    }),

  /** Cierra la sesión. */
  closeSession: (identifier, sessionId) =>
    publicHttp.delete(`/public/bots/${encodeURIComponent(identifier)}/session`, {
      params: { session_id: sessionId },
    }),
};

export default publicApi;
