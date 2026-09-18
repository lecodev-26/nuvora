/**
 * publicationApi — Cliente HTTP para endpoints privados de publicación
 *
 * Endpoints (14.9.5):
 *   GET    /bots/{bot_id}/publication
 *   PUT    /bots/{bot_id}/publication
 *   POST   /bots/{bot_id}/publish
 *   POST   /bots/{bot_id}/unpublish
 *
 * Usa el `api` (con JWT).
 */

import api from './api';

export const publicationApi = {
  /** Estado de publicación del bot. */
  getPublication: (botId) => api.get(`/bots/${botId}/publication`),

  /** Actualiza la config de publicación (visual/textos). */
  updatePublication: (botId, config) =>
    api.put(`/bots/${botId}/publication`, { config }),

  /** Publica el bot (requiere workflow activo válido). */
  publish: (botId) => api.post(`/bots/${botId}/publish`),

  /** Despublica el bot (mantiene public_id / public_slug). */
  unpublish: (botId) => api.post(`/bots/${botId}/unpublish`),
};

export default publicationApi;
