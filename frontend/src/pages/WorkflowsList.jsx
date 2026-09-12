import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { workflowService } from '../services/workflowApi';
import Button from '../components/Button';
import Card from '../components/Card';

/**
 * WorkflowsList — Lista de workflows de un bot.
 *
 * Ruta: /workflows/:botId
 *
 * Acciones:
 *  - Ver lista de workflows con status y fecha
 *  - Crear nuevo → /workflows/:botId/new
 *  - Abrir en Builder → /workflows/:botId/:workflowId
 *  - Eliminar workflow
 */

const STATUS_COLORS = {
  draft: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  active: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
  archived: 'bg-slate-500/20 text-slate-300 border-slate-500/30',
};

const STATUS_LABELS = {
  draft: 'Borrador',
  active: 'Activo',
  archived: 'Archivado',
};

const WorkflowsList = () => {
  const { botId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [workflows, setWorkflows] = useState([]);

  // ============================================================
  // CARGA
  // ============================================================

  const loadWorkflows = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await workflowService.list(botId);
      const data = res.data;
      setWorkflows(data.workflows || []);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(detail || err.message || 'Error cargando workflows');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWorkflows();
  }, [botId]);

  // ============================================================
  // ELIMINAR
  // ============================================================

  const handleDelete = async (wf) => {
    if (!confirm(`¿Eliminar el workflow "${wf.name}"? Esta acción no se puede deshacer.`)) {
      return;
    }
    try {
      await workflowService.delete(botId, wf.id);
      await loadWorkflows();
    } catch (err) {
      const detail = err.response?.data?.detail;
      alert(`Error eliminando: ${detail || err.message}`);
    }
  };

  // ============================================================
  // FORMATEAR FECHA
  // ============================================================

  const formatDate = (iso) => {
    if (!iso) return '—';
    try {
      const d = new Date(iso);
      return d.toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return iso;
    }
  };

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <div className="min-h-screen bg-navy px-6 py-8">
      {/* Header */}
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between gap-4 mb-8">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => navigate('/dashboard')}>
              ← Volver
            </Button>
            <div>
              <h1 className="text-3xl font-bold text-white">Workflows</h1>
              <p className="text-white/50 text-sm">
                Bot #{botId} · {workflows.length} workflow{workflows.length !== 1 ? 's' : ''}
              </p>
            </div>
          </div>

          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate(`/workflows/${botId}/new`)}
          >
            + Nuevo workflow
          </Button>
        </div>

        {/* Estados */}
        {loading && (
          <div className="text-center text-white/50 py-12">Cargando workflows...</div>
        )}

        {error && (
          <Card padding="p-6" className="text-center">
            <div className="text-red-400 mb-4">{error}</div>
            <Button variant="secondary" size="sm" onClick={loadWorkflows}>
              Reintentar
            </Button>
          </Card>
        )}

        {!loading && !error && workflows.length === 0 && (
          <Card padding="p-12" className="text-center">
            <div className="text-6xl mb-4">🎼</div>
            <h2 className="text-xl font-semibold text-white mb-2">
              Todavía no tienes workflows
            </h2>
            <p className="text-white/50 mb-6 max-w-md mx-auto">
              Los workflows te permiten guiar conversaciones paso a paso: preguntas,
              condiciones, variables y respuestas.
            </p>
            <Button
              variant="primary"
              onClick={() => navigate(`/workflows/${botId}/new`)}
            >
              Crear mi primer workflow
            </Button>
          </Card>
        )}

        {!loading && !error && workflows.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {workflows.map((wf) => (
              <Card
                key={wf.id}
                hover
                padding="p-5"
                className="flex flex-col justify-between min-h-[180px]"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <Link
                      to={`/workflows/${botId}/${wf.id}`}
                      className="text-white font-semibold text-lg hover:text-cyan-300 transition-colors line-clamp-2"
                    >
                      {wf.name}
                    </Link>
                    <span
                      className={`text-[10px] uppercase tracking-wider px-2 py-1 rounded border shrink-0 ${
                        STATUS_COLORS[wf.status] || STATUS_COLORS.draft
                      }`}
                    >
                      {STATUS_LABELS[wf.status] || wf.status}
                    </span>
                  </div>

                  {wf.description && (
                    <p className="text-white/50 text-sm line-clamp-2 mb-3">
                      {wf.description}
                    </p>
                  )}

                  <div className="text-white/40 text-xs space-y-0.5">
                    <div>v{wf.version} · trigger: {wf.trigger}</div>
                    <div>Actualizado: {formatDate(wf.updated_at || wf.created_at)}</div>
                  </div>
                </div>

                <div className="flex items-center gap-2 mt-4 pt-4 border-t border-white/10">
                  <Button
                    variant="primary"
                    size="sm"
                    className="flex-1"
                    onClick={() => navigate(`/workflows/${botId}/${wf.id}`)}
                  >
                    Abrir
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => handleDelete(wf)}
                  >
                    🗑
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkflowsList;
