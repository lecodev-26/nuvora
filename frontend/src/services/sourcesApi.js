/**
 * sourcesApi — Cliente HTTP para /sources/*
 *
 * Endpoints:
 *   POST   /sources/text                    → crear fuente desde texto
 *   POST   /sources/url                     → crear fuente desde URL
 *   GET    /sources/list/{bot_id}           → listar fuentes
 *   DELETE /sources/{source_id}             → borrar fuente
 *   POST   /sources/{source_id}/reindex     → reindexar
 *   POST   /sources/reindex-all/{bot_id}    → reindexar todas
 */

import api from './api';

export const sourcesService = {
  list: (botId) => api.get(`/sources/list/${botId}`),

  createText: (botId, title, content) =>
    api.post('/sources/text', { bot_id: botId, title, content }),

  createUrl: (botId, url, title) =>
    api.post('/sources/url', { bot_id: botId, url, title }),

  remove: (sourceId) => api.delete(`/sources/${sourceId}`),

  reindex: (sourceId) => api.post(`/sources/${sourceId}/reindex`),

  reindexAll: (botId) => api.post(`/sources/reindex-all/${botId}`),
};

export default sourcesService;
