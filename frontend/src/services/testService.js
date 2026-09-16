import api from './api';

/**
 * testService — Cliente HTTP para /bots/{bot_id}/tests/*
 *
 * Endpoints (14.8.7):
 *   POST   /bots/{bot_id}/tests                    → crear test
 *   GET    /bots/{bot_id}/tests                    → listar tests
 *   GET    /bots/{bot_id}/tests/{test_id}          → ver test
 *   PUT    /bots/{bot_id}/tests/{test_id}          → actualizar test
 *   DELETE /bots/{bot_id}/tests/{test_id}          → borrar test
 *   POST   /bots/{bot_id}/tests/{test_id}/run      → ejecutar 1 test
 *   POST   /bots/{bot_id}/tests/run-all            → ejecutar todos
 *   POST   /bots/{bot_id}/tests/analyze            → static analysis
 */

export const testService = {
  // ============================================================
  // CRUD
  // ============================================================

  /**
   * Crea un test para un workflow del bot.
   * @param {number} botId
   * @param {number} workflowId
   * @param {object} payload - { name, description, input_messages, initial_variables, assertions, enabled }
   */
  create: (botId, workflowId, payload) =>
    api.post(`/bots/${botId}/tests`, payload, {
      params: { workflow_id: workflowId },
    }),

  /**
   * Lista los tests del bot (opcionalmente filtrando por workflow).
   * @param {number} botId
   * @param {object} [opts] - { workflow_id?, enabled_only? }
   */
  list: (botId, opts = {}) =>
    api.get(`/bots/${botId}/tests`, { params: opts }),

  /**
   * Devuelve un test individual.
   */
  get: (botId, testId) =>
    api.get(`/bots/${botId}/tests/${testId}`),

  /**
   * Actualiza parcialmente un test.
   */
  update: (botId, testId, payload) =>
    api.put(`/bots/${botId}/tests/${testId}`, payload),

  /**
   * Borra un test.
   */
  delete: (botId, testId) =>
    api.delete(`/bots/${botId}/tests/${testId}`),

  // ============================================================
  // EJECUCIÓN
  // ============================================================

  /**
   * Ejecuta un test individual.
   */
  run: (botId, testId) =>
    api.post(`/bots/${botId}/tests/${testId}/run`),

  /**
   * Ejecuta todos los tests de un workflow.
   * @param {number} botId
   * @param {number} workflowId
   * @param {boolean} [enabledOnly=true]
   */
  runAll: (botId, workflowId, enabledOnly = true) =>
    api.post(`/bots/${botId}/tests/run-all`, null, {
      params: { workflow_id: workflowId, enabled_only: enabledOnly },
    }),

  // ============================================================
  // ANÁLISIS
  // ============================================================

  /**
   * Análisis estático del workflow.
   * @param {number} botId
   * @param {number} workflowId
   */
  analyze: (botId, workflowId) =>
    api.post(`/bots/${botId}/tests/analyze`, null, {
      params: { workflow_id: workflowId },
    }),
};

export default testService;
