/**
 * useCreatorStatus — Hook para obtener el estado del bot en Creator Mode.
 *
 * Hace fetch al endpoint GET /bots/{botId}/creator-status.
 *
 * Diseño:
 *   - Fetch bajo demanda (no en Context global → evita God Object).
 *   - Cada componente que lo necesite, lo usa.
 *   - Refresco manual disponible (`reload()`).
 *
 * Uso:
 *   const { status, loading, error, reload } = useCreatorStatus(botId);
 */

import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';


export function useCreatorStatus(botId) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    if (!botId) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.get(`/bots/${botId}/creator-status`);
      setStatus(res.data);
    } catch (err) {
      const detail = err.response?.data?.detail;
      const msg =
        typeof detail === 'string'
          ? detail
          : err.message || 'Error cargando estado del bot';
      setError(msg);
      setStatus(null);
    } finally {
      setLoading(false);
    }
  }, [botId]);

  useEffect(() => {
    load();
  }, [load]);

  return { status, loading, error, reload: load };
}


export default useCreatorStatus;
