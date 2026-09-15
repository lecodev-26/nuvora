import React, { useEffect, useState } from 'react';
import { aiService } from '../../services/aiService';
import Button from '../Button';
import Spinner from '../ui/Spinner';

/**
 * TemplatesGrid — Grid de plantillas predefinidas.
 *
 * Props:
 *  - onSelect(templateId, workflow): cuando el usuario elige una plantilla
 *  - loading, error: si el padre ya tiene estos estados
 *
 * Carga las plantillas desde /ai/templates (sin IA, rápido).
 */

const TemplatesGrid = ({ onSelect }) => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [instantiating, setInstantiating] = useState(null);

  useEffect(() => {
    let cancelled = false;
    aiService
      .listTemplates()
      .then((res) => {
        if (cancelled) return;
        setTemplates(res.data.templates || []);
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        const detail = err.response?.data?.detail;
        setError(detail || err.message || 'Error cargando plantillas');
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSelect = async (templateId) => {
    setInstantiating(templateId);
    setError(null);
    try {
      const res = await aiService.instantiateTemplate(templateId);
      if (onSelect) {
        onSelect(templateId, res.data.workflow);
      }
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(detail || err.message || 'Error instanciando plantilla');
    } finally {
      setInstantiating(null);
    }
  };

  if (loading) {
    return (
      <div className="py-12 flex justify-center">
        <Spinner size="md" label="Cargando plantillas..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-300 text-sm">
        ⚠️ {error}
      </div>
    );
  }

  if (templates.length === 0) {
    return (
      <div className="text-center text-white/40 py-8">
        No hay plantillas disponibles.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {templates.map((t) => (
        <button
          key={t.id}
          type="button"
          disabled={instantiating !== null}
          onClick={() => handleSelect(t.id)}
          className={`
            text-left bg-white/5 border border-white/10 rounded-xl p-4
            hover:border-cyan-400/40 hover:bg-white/10
            transition-all duration-200
            ${instantiating === t.id ? 'opacity-60 cursor-wait' : ''}
            ${instantiating !== null && instantiating !== t.id ? 'opacity-40' : ''}
          `}
        >
          <div className="flex items-start gap-3">
            <span className="text-3xl leading-none shrink-0">{t.icon}</span>
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="text-white font-semibold text-sm truncate">
                  {t.name}
                </span>
                {instantiating === t.id && (
                  <span className="text-cyan-400 text-xs shrink-0">⟳</span>
                )}
              </div>
              <p className="text-white/60 text-xs leading-relaxed">
                {t.description}
              </p>
            </div>
          </div>
        </button>
      ))}
    </div>
  );
};

export default TemplatesGrid;
