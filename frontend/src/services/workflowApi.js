import api from './api';

/**
 * workflowApi — Cliente HTTP para /workflows/*
 *
 * Wraps los endpoints del backend 14.5/14.6.2:
 *   POST   /workflows/{bot_id}
 *   GET    /workflows/{bot_id}
 *   GET    /workflows/{bot_id}/{workflow_id}
 *   PUT    /workflows/{bot_id}/{workflow_id}   (PUT transaccional completo)
 *   DELETE /workflows/{bot_id}/{workflow_id}
 *   POST   /workflows/{bot_id}/{workflow_id}/run
 */

export const workflowService = {
  /** Lista todos los workflows de un bot. */
  list: (botId) => api.get(`/workflows/${botId}`),

  /** Carga un workflow completo (con nodes + transitions). */
  get: (botId, workflowId) => api.get(`/workflows/${botId}/${workflowId}`),

  /** Crea un workflow completo. */
  create: (botId, payload) => api.post(`/workflows/${botId}`, payload),

  /**
   * Actualiza un workflow.
   *
   * Payload puede incluir:
   *   - metadata (name, description, status, trigger, meta)
   *   - nodes (opcional, replace-all)
   *   - transitions (opcional, replace-all)
   *
   * Si `nodes`/`transitions` están ausentes (undefined) → no se tocan.
   * Si son `[]` → se borran todos.
   * Si son `[...]` → se reemplazan todos.
   */
  update: (botId, workflowId, payload) =>
    api.put(`/workflows/${botId}/${workflowId}`, payload),

  /** Elimina un workflow. */
  delete: (botId, workflowId) =>
    api.delete(`/workflows/${botId}/${workflowId}`),

  /**
   * Ejecuta un workflow (testing).
   * @param {number} botId
   * @param {number} workflowId
   * @param {object} vars - variables iniciales (ej: { name: 'Manuel' })
   * @param {number} maxSteps - límite de pasos (default 100)
   */
  run: (botId, workflowId, vars = {}, maxSteps = 100) =>
    api.post(`/workflows/${botId}/${workflowId}/run`, {
      initial_variables: vars,
      max_steps: maxSteps,
    }),
};

export default workflowService;
