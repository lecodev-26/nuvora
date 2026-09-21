/**
 * telegramApi — Cliente HTTP para /bots/{bot_id}/telegram
 *
 * Endpoints (14.11.8):
 *   GET    /bots/{bot_id}/telegram                → estado
 *   POST   /bots/{bot_id}/telegram/connect        → conectar
 *   POST   /bots/{bot_id}/telegram/test           → probar conexión
 *   POST   /bots/{bot_id}/telegram/disconnect     → desconectar
 *
 * SEGURIDAD:
 *   - El token de Telegram NUNCA se devuelve por el backend.
 *   - Solo se envía al backend en `connect()` (una vez).
 *
 * Usa el api (con JWT).
 */

import api from './api';

export const telegramService = {
  /**
   * Estado actual de la integración Telegram.
   * Devuelve null si no existe integración.
   */
  getStatus: (botId) =>
    api.get(`/bots/${botId}/telegram`),

  /**
   * Conecta un bot Nuvora con un bot de Telegram.
   *
   * @param {number} botId - ID del bot Nuvora.
   * @param {string} token - Token del bot de Telegram (formato "123456:ABC...").
   *
   * @returns {Promise} response con:
   *   { status, telegram_username, telegram_bot_id, webhook_url }
   *
   * Errores habituales:
   *   400 → token inválido
   *   409 → ya hay integración activa
   *   403 → bot ajeno
   */
  connect: (botId, token) =>
    api.post(`/bots/${botId}/telegram/connect`, { token }),

  /**
   * Prueba la conexión con Telegram (llama getMe internamente).
   * Útil para verificar que el token sigue siendo válido.
   *
   * @returns {Promise} response con:
   *   { ok, id, username, first_name }
   */
  test: (botId) =>
    api.post(`/bots/${botId}/telegram/test`),

  /**
   * Desconecta el bot de Telegram.
   * Llama deleteWebhook en Telegram (best-effort) + marca como inactivo.
   *
   * @returns {Promise} response con:
   *   { status, is_active }
   */
  disconnect: (botId) =>
    api.post(`/bots/${botId}/telegram/disconnect`),
};

export default telegramService;
