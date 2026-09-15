import api from './api';

/**
 * aiService — Cliente HTTP para /ai/*
 *
 * Wraps los endpoints del backend 14.7:
 *   POST /ai/workflows/generate       → generar workflow desde prompt
 *   POST /ai/workflows/modify         → modificar workflow existente
 *   POST /ai/workflows/explain        → explicar workflow
 *   POST /ai/workflows/analyze        → analizar workflow
 *   GET  /ai/templates                → listar plantillas
 *   POST /ai/templates/{id}/instantiate → instanciar plantilla
 *
 *   GET  /ai/config                   → listar configs BYOK
 *   POST /ai/config                   → crear/actualizar BYOK
 *   DELETE /ai/config/{provider}      → borrar BYOK
 */

export const aiService = {
  // ============================================================
  // WORKFLOWS
  // ============================================================

  /**
   * Genera un workflow desde una descripción en lenguaje natural.
   * @param {string} prompt
   * @param {object} [botContext] - { bot_name?, description?, business_type?, language?, tone? }
   */
  generate: (prompt, botContext = null) =>
    api.post('/ai/workflows/generate', {
      prompt,
      bot_context: botContext,
    }),

  /**
   * Modifica un workflow existente según una instrucción.
   * @param {object} workflow - { name, description, nodes, transitions }
   * @param {string} instruction
   */
  modify: (workflow, instruction) =>
    api.post('/ai/workflows/modify', { workflow, instruction }),

  /**
   * Explica un workflow en lenguaje humano.
   * @param {object} workflow
   */
  explain: (workflow) =>
    api.post('/ai/workflows/explain', { workflow }),

  /**
   * Analiza un workflow: warnings + suggestions.
   * @param {object} workflow
   */
  analyze: (workflow) =>
    api.post('/ai/workflows/analyze', { workflow }),

  // ============================================================
  // TEMPLATES
  // ============================================================

  /**
   * Lista todas las plantillas disponibles.
   */
  listTemplates: () => api.get('/ai/templates'),

  /**
   * Devuelve el workflow de una plantilla.
   * @param {string} templateId
   */
  instantiateTemplate: (templateId) =>
    api.post(`/ai/templates/${templateId}/instantiate`),

  // ============================================================
  // BYOK (API keys propias del usuario)
  // ============================================================

  /**
   * Lista las configs BYOK del usuario (sin devolver las keys).
   */
  listConfigs: () => api.get('/ai/config'),

  /**
   * Crea o actualiza una key BYOK.
   * @param {string} provider - 'gemini' | 'groq' | 'deepseek' | 'openai' | 'mistral' | 'anthropic' | 'ollama'
   * @param {string} apiKey
   */
  setConfig: (provider, apiKey) =>
    api.post('/ai/config', { provider, api_key: apiKey }),

  /**
   * Borra la key BYOK de un provider.
   * @param {string} provider
   */
  deleteConfig: (provider) =>
    api.delete(`/ai/config/${provider}`),
};

export default aiService;
