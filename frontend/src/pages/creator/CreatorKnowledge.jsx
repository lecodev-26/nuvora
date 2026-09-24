import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

import Card from '../../components/Card';
import Button from '../../components/Button';
import Input from '../../components/Input';
import ConfirmModal from '../../components/ui/ConfirmModal';
import EmptyState from '../../components/creator/EmptyState';
import CreatorError from '../../components/creator/CreatorError';
import Spinner from '../../components/ui/Spinner';
import { memoryService, botService } from '../../services/api';
import { sourcesService } from '../../services/sourcesApi';

/**
 * CreatorKnowledge — Conocimiento del bot (memorias + fuentes + categorías).
 *
 * 3 tabs con CRUD básico.
 *
 * NO implementa (por ahora):
 *   - Subida de PDF/CSV/URL (fase futura)
 *   - Edición de memorias/fuentes existentes
 *   - Categorías vinculadas a memorias
 */
const CreatorKnowledge = () => {
  const { botId } = useParams();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState('memories');

  // Data
  const [memories, setMemories] = useState([]);
  const [sources, setSources] = useState([]);
  const [categories, setCategories] = useState([]);

  // Forms
  const [newMemory, setNewMemory] = useState({ fact: '', keyword: '' });
  const [newSource, setNewSource] = useState({ title: '', content: '' });
  const [newCategory, setNewCategory] = useState({ name: '', icon: '' });

  // UI state
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState(null);

  // ---------- LOAD ----------
  const loadAll = useCallback(async () => {
    if (!botId) return;
    setLoading(true);
    setError(null);
    try {
      const [memRes, srcRes] = await Promise.all([
        memoryService.getByBot(botId),
        sourcesService.list(botId),
      ]);
      setMemories(memRes.data || []);
      setSources(srcRes.data?.sources || srcRes.data || []);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Error cargando conocimiento');
    } finally {
      setLoading(false);
    }
  }, [botId]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  // ---------- MEMORIAS ----------
  const handleAddMemory = async (e) => {
    e.preventDefault();
    if (!newMemory.fact.trim() || !newMemory.keyword.trim()) return;
    setActionLoading(true);
    try {
      await memoryService.add({
        bot_id: parseInt(botId),
        fact: newMemory.fact.trim(),
        keyword: newMemory.keyword.trim().toLowerCase(),
      });
      setNewMemory({ fact: '', keyword: '' });
      await loadAll();
    } catch (err) {
      setError(err.response?.data?.detail || 'Error añadiendo memoria');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteMemory = (memory) => {
    setConfirmDialog({
      title: 'Borrar memoria',
      message: `¿Borrar "${memory.keyword}"?\n\nEsta acción no se puede deshacer.`,
      confirmText: 'Borrar',
      danger: true,
      onConfirm: async () => {
        setConfirmDialog(null);
        setActionLoading(true);
        try {
          await memoryService.remove(memory.id);
          await loadAll();
        } catch (err) {
          setError(err.response?.data?.detail || 'Error borrando memoria');
        } finally {
          setActionLoading(false);
        }
      },
    });
  };

  // ---------- FUENTES ----------
  const handleAddSource = async (e) => {
    e.preventDefault();
    if (!newSource.title.trim() || !newSource.content.trim()) return;
    setActionLoading(true);
    try {
      await sourcesService.createText(botId, newSource.title.trim(), newSource.content.trim());
      setNewSource({ title: '', content: '' });
      await loadAll();
    } catch (err) {
      setError(err.response?.data?.detail || 'Error añadiendo fuente');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteSource = (source) => {
    setConfirmDialog({
      title: 'Borrar fuente',
      message: `¿Borrar "${source.title}"?\n\nEsta acción no se puede deshacer.`,
      confirmText: 'Borrar',
      danger: true,
      onConfirm: async () => {
        setConfirmDialog(null);
        setActionLoading(true);
        try {
          await sourcesService.remove(source.id);
          await loadAll();
        } catch (err) {
          setError(err.response?.data?.detail || 'Error borrando fuente');
        } finally {
          setActionLoading(false);
        }
      },
    });
  };

  // ---------- CATEGORÍAS (por ahora solo visual, endpoints futuros) ----------
  const handleAddCategory = async (e) => {
    e.preventDefault();
    // Placeholder — se implementará cuando tengamos categoryService
    setNewCategory({ name: '', icon: '' });
  };

  // ---------- RENDER ----------
  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner />
      </div>
    );
  }

  if (error) {
    return (
      <CreatorError
        title="No se pudo cargar el conocimiento"
        description={error}
        ctaLabel="Reintentar"
        onCta={loadAll}
        secondaryLabel="Volver al inicio"
        onSecondary={() => navigate(`/bots/${botId}`)}
      />
    );
  }

  const tabs = [
    { id: 'memories', label: 'Memorias', icon: '📝', count: memories.length },
    { id: 'sources', label: 'Fuentes', icon: '📚', count: sources.length },
    { id: 'categories', label: 'Categorías', icon: '🏷️', count: categories.length },
  ];

  return (
    <div className="space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-xl md:text-2xl font-bold text-white">Conocimiento</h1>
        <p className="text-white/50 text-sm mt-1">
          Enseña a tu bot con memorias y fuentes de información.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-white/10 overflow-x-auto -mx-4 md:mx-0 px-4 md:px-0">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setActiveTab(t.id)}
            className={`px-4 py-2 text-sm font-medium transition border-b-2 -mb-px flex items-center gap-2 whitespace-nowrap flex-shrink-0 ${
              activeTab === t.id
                ? 'text-white border-cyan-400'
                : 'text-white/50 border-transparent hover:text-white/80'
            }`}
          >
            <span>{t.icon}</span>
            <span>{t.label}</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-white/10 text-white/60">
              {t.count}
            </span>
          </button>
        ))}
      </div>

      {/* ---------- TAB: MEMORIAS ---------- */}
      {activeTab === 'memories' && (
        <div className="space-y-4">
          {/* Form añadir */}
          <Card>
            <h2 className="text-white font-semibold mb-4">Añadir memoria</h2>
            <form onSubmit={handleAddMemory} className="space-y-3">
              <Input
                label="Hecho"
                value={newMemory.fact}
                onChange={(e) => setNewMemory({ ...newMemory, fact: e.target.value })}
                placeholder="Ej: Abrimos de 9:00 a 18:00"
              />
              <Input
                label="Palabra clave"
                value={newMemory.keyword}
                onChange={(e) => setNewMemory({ ...newMemory, keyword: e.target.value })}
                placeholder="Ej: horario"
              />
              <div className="flex justify-end">
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  disabled={actionLoading || !newMemory.fact.trim() || !newMemory.keyword.trim()}
                >
                  {actionLoading ? 'Añadiendo...' : '+ Añadir memoria'}
                </Button>
              </div>
            </form>
          </Card>

          {/* Lista */}
          {memories.length === 0 ? (
            <Card>
              <EmptyState
                icon="📝"
                title="Tu bot todavía no tiene memorias"
                description="Añade información sobre tu negocio para que pueda responder basándose en ella."
              />
            </Card>
          ) : (
            <Card>
              <h2 className="text-white font-semibold mb-3">
                Memorias ({memories.length})
              </h2>
              <ul className="space-y-2">
                {memories.map((m) => (
                  <li
                    key={m.id}
                    className="flex items-start gap-3 px-3 py-2 rounded-lg border border-white/10 bg-white/[0.02]"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-white/90 break-words">{m.fact}</p>
                      <p className="text-[11px] text-violet-300 mt-0.5">
                        🔑 {m.keyword}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleDeleteMemory(m)}
                      className="text-white/30 hover:text-red-400 transition text-sm flex-shrink-0"
                      title="Borrar"
                    >
                      🗑
                    </button>
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </div>
      )}

      {/* ---------- TAB: FUENTES ---------- */}
      {activeTab === 'sources' && (
        <div className="space-y-4">
          <Card>
            <h2 className="text-white font-semibold mb-4">Añadir fuente (texto)</h2>
            <p className="text-white/50 text-xs mb-3">
              Próximamente: subir PDF, URL o CSV desde aquí.
            </p>
            <form onSubmit={handleAddSource} className="space-y-3">
              <Input
                label="Título"
                value={newSource.title}
                onChange={(e) => setNewSource({ ...newSource, title: e.target.value })}
                placeholder="Ej: Información general del restaurante"
              />
              <div>
                <label className="block text-sm font-medium text-white/70 mb-1">
                  Contenido
                </label>
                <textarea
                  value={newSource.content}
                  onChange={(e) => setNewSource({ ...newSource, content: e.target.value })}
                  placeholder="Pega aquí el contenido..."
                  rows={6}
                  className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-400/60 resize-none"
                />
              </div>
              <div className="flex justify-end">
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  disabled={actionLoading || !newSource.title.trim() || !newSource.content.trim()}
                >
                  {actionLoading ? 'Añadiendo...' : '+ Añadir fuente'}
                </Button>
              </div>
            </form>
          </Card>

          {sources.length === 0 ? (
            <Card>
              <EmptyState
                icon="📚"
                title="Tu bot todavía no tiene fuentes"
                description="Añade información sobre tu negocio para que pueda responder basándose en ella."
              />
            </Card>
          ) : (
            <Card>
              <h2 className="text-white font-semibold mb-3">
                Fuentes ({sources.length})
              </h2>
              <ul className="space-y-2">
                {sources.map((s) => (
                  <li
                    key={s.id}
                    className="flex items-start gap-3 px-3 py-2 rounded-lg border border-white/10 bg-white/[0.02]"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-white/90 truncate">{s.title}</p>
                      <p className="text-[11px] text-white/40 mt-0.5">
                        {s.type} · {s.status} · {s.chunks_count || 0} fragmentos
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleDeleteSource(s)}
                      className="text-white/30 hover:text-red-400 transition text-sm flex-shrink-0"
                      title="Borrar"
                    >
                      🗑
                    </button>
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </div>
      )}

      {/* ---------- TAB: CATEGORÍAS ---------- */}
      {activeTab === 'categories' && (
        <div className="space-y-4">
          <Card>
            <EmptyState
              icon="🏷️"
              title="Categorías (próximamente)"
              description="Podrás organizar tus memorias por categorías. Por ahora, las memorias se guardan sin categoría."
            />
          </Card>
        </div>
      )}

      {/* Confirm modal */}
      <ConfirmModal
        open={!!confirmDialog}
        title={confirmDialog?.title || ''}
        message={confirmDialog?.message || ''}
        confirmText={confirmDialog?.confirmText || 'Confirmar'}
        danger={confirmDialog?.danger}
        onConfirm={confirmDialog?.onConfirm || (() => {})}
        onCancel={() => setConfirmDialog(null)}
      />
    </div>
  );
};

export default CreatorKnowledge;
