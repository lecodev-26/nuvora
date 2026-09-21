/**
 * apiKeysApi — Cliente HTTP para /bots/{bot_id}/api-keys
 *
 * Endpoints (14.10.6):
 *   GET    /bots/{bot_id}/api-keys
 *   POST   /bots/{bot_id}/api-keys
 *   DELETE /bots/{bot_id}/api-keys/{key_id}
 *
 * Usa el api (con JWT).
 */

import api from './api';

export const apiKeysService = {
  /** Lista las API Keys de un bot. */
  list: (botId) => api.get(`/bots/${botId}/api-keys`),

  /** Crea una nueva API Key. Devuelve el secret UNA VEZ. */
  create: (botId, name) =>
    api.post(`/bots/${botId}/api-keys`, { name }),

  /** Revoca una API Key. */
  revoke: (botId, keyId) =>
    api.delete(`/bots/${botId}/api-keys/${keyId}`),
};

export default apiKeysService;
