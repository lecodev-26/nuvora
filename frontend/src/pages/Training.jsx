import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { botService, trainingService, memoryService } from '../services/api';
import Button from '../components/Button';
import Card from '../components/Card';
import Badge from '../components/Badge';
import Input from '../components/Input';

const LOGO_URL = '/logo.png';

// ============================================================
// UTILIDADES
// ============================================================

const STOPWORDS_ES = new Set([
  'que', 'cual', 'como', 'donde', 'cuando', 'quien', 'quienes',
  'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
  'de', 'del', 'al', 'a', 'en', 'por', 'para', 'con', 'sin',
  'y', 'o', 'u', 'e', 'es', 'son', 'era', 'fue', 'ser',
  'hay', 'tiene', 'tienen', 'teneis', 'tenemos', 'tengo', 'tienes',
  'puede', 'pueden', 'podeis', 'podemos', 'puedo', 'puedes',
  'hace', 'hacen', 'haceis', 'hacemos', 'hago', 'haces',
  'muy', 'mas', 'menos', 'tan', 'tanto', 'mucho', 'poco',
  'me', 'te', 'se', 'nos', 'os', 'lo', 'le', 'les',
  'mi', 'tu', 'su', 'nuestro', 'vuestro', 'mis', 'tus', 'sus',
  'si', 'no', 'ya', 'tambien', 'todo', 'nada', 'algo',
]);

function deriveKeyword(question) {
  const cleaned = question
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[¿?¡!.,;:()"']/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

  const tokens = cleaned
    .split(' ')
    .filter(w => w.length >= 2 && !STOPWORDS_ES.has(w))
    .slice(0, 3);

  return tokens.join(',');
}

// ============================================================
// SUB-COMPONENTES
// ============================================================

const ProgressBar = ({ progress }) => {
  const pct = Math.round((progress || 0) * 100);
  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-white/60">Progreso de preparación</span>
        <span className="text-2xl font-bold text-gradient">{pct}%</span>
      </div>
      <div className="h-3 bg-white/5 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-cyan-500 via-violet-500 to-magenta-500 transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
};

const SummaryStats = ({ covered, partial, missing }) => (
  <div className="grid grid-cols-3 gap-3">
    <Card className="p-4 text-center">
      <p className="text-2xl font-bold text-emerald-400">{covered}</p>
      <p className="text-xs text-white/50">🟢 Cubiertos</p>
    </Card>
    <Card className="p-4 text-center">
      <p className="text-2xl font-bold text-amber-400">{partial}</p>
      <p className="text-xs text-white/50">🟡 Parciales</p>
    </Card>
    <Card className="p-4 text-center">
      <p className="text-2xl font-bold text-red-400">{missing}</p>
      <p className="text-xs text-white/50">🔴 Faltantes</p>
    </Card>
  </div>
);

const RecommendationCard = ({ rec, onAction }) => {
  const typeIcons = {
    missing_topic: '🔴',
    partial_topic: '🟡',
    frequent_question: '⚠️',
  };
  const actionLabels = {
    add_memory: 'Añadir información',
    add_source: 'Añadir fuente',
    answer_question: 'Responder',
  };

  return (
    <Card className="p-4 hover:border-violet-500/30 transition">
      <div className="flex items-start gap-3">
        <span className="text-2xl">{typeIcons[rec.type] || '💡'}</span>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-white">{rec.title}</p>
          <p className="text-sm text-white/50 mt-1">{rec.reason}</p>
          <Button
            variant="secondary"
            size="sm"
            className="mt-3"
            onClick={() => onAction(rec)}
          >
            {actionLabels[rec.action_type] || 'Acción'} →
          </Button>
        </div>
      </div>
    </Card>
  );
};

const TopicItem = ({ topic }) => {
  const statusIcons = {
    covered: '🟢',
    partial: '🟡',
    missing: '🔴',
  };
  return (
    <div className="flex items-center justify-between p-3 rounded-xl bg-white/5">
      <div className="flex items-center gap-3">
        <span>{statusIcons[topic.status]}</span>
        <div>
          <p className="text-sm font-medium text-white">{topic.label}</p>
          <p className="text-xs text-white/40">{topic.description}</p>
        </div>
      </div>
      <span className="text-xs text-white/30">
        {topic.evidence_count} evid.
      </span>
    </div>
  );
};

const QuestionGroupCard = ({ group }) => (
  <Card className="p-4">
    <div className="flex items-start gap-3">
      <span className="text-xl">💬</span>
      <div className="flex-1 min-w-0">
        <p className="font-medium text-white">{group.representative}</p>
        <p className="text-xs text-white/40 mt-1">
          {group.count} {group.count === 1 ? 'vez' : 'veces'} sin respuesta
        </p>
        {group.variants && group.variants.length > 1 && (
          <details className="mt-2">
            <summary className="text-xs text-violet-300 cursor-pointer">
              Ver {group.variants.length} variantes
            </summary>
            <ul className="mt-2 space-y-1 text-xs text-white/50 pl-4">
              {group.variants.map((v, i) => (
                <li key={i}>• {v}</li>
              ))}
            </ul>
          </details>
        )}
      </div>
    </div>
  </Card>
);

// ============================================================
// MODAL — AÑADIR CONOCIMIENTO
// ============================================================

const AddKnowledgeModal = ({ open, rec, botId, onClose, onSaved }) => {
  const [fact, setFact] = useState('');
  const [keyword, setKeyword] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!open || !rec) return;
    setError('');
    if (rec.action_type === 'answer_question') {
      setFact('');
      setKeyword(deriveKeyword(rec.action_payload.question || ''));
    } else {
      setFact('');
      setKeyword(rec.action_payload.suggested_keyword || '');
    }
  }, [open, rec]);

  if (!open || !rec) return null;

  const isQuestion = rec.action_type === 'answer_question';
  const title = isQuestion
    ? `Responder a: "${rec.action_payload.question}"`
    : rec.title;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!fact.trim()) {
      setError('Escribe el contenido.');
      return;
    }
    if (!keyword.trim()) {
      setError('La palabra clave es obligatoria.');
      return;
    }
    setSaving(true);
    try {
      await memoryService.add({
        bot_id: botId,
        fact: fact.trim(),
        keyword: keyword.trim().toLowerCase(),
      });
      if (onSaved) onSaved();
      onClose();
    } catch (e) {
      setError(
        e.response?.data?.detail || 'No se pudo guardar. Inténtalo de nuevo.'
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-navy border border-white/10 rounded-2xl max-w-lg w-full p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 mb-4">
          <h3 className="text-lg font-bold text-white pr-4">{title}</h3>
          <button
            onClick={onClose}
            className="text-white/40 hover:text-white transition text-xl leading-none"
            disabled={saving}
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {isQuestion && (
            <div className="p-3 rounded-xl bg-white/5 border border-white/10">
              <p className="text-xs text-white/50">Pregunta original</p>
              <p className="text-sm text-white mt-1">
                {rec.action_payload.question}
              </p>
            </div>
          )}

          <div>
            <label className="block text-sm text-white/70 mb-2">
              {isQuestion ? 'Respuesta' : 'Información'}
            </label>
            <textarea
              value={fact}
              onChange={(e) => setFact(e.target.value)}
              placeholder={
                isQuestion
                  ? 'Escribe la respuesta que quieres que dé el bot...'
                  : 'Escribe aquí la información que quieres que conozca tu bot...'
              }
              rows={4}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-violet-500/50 resize-none"
              disabled={saving}
              autoFocus
            />
          </div>

          <div>
            <label className="block text-sm text-white/70 mb-2">
              Palabra clave
            </label>
            <Input
              type="text"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="ej: horarios"
              disabled={saving}
            />
            <p className="text-[11px] text-white/30 mt-1">
              Se usa para que el bot encuentre esta información cuando pregunten.
            </p>
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 text-sm text-red-400">
              {error}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <Button
              type="button"
              variant="ghost"
              size="md"
              onClick={onClose}
              disabled={saving}
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="md"
              disabled={saving || !fact.trim() || !keyword.trim()}
            >
              {saving
                ? 'Guardando...'
                : isQuestion
                ? 'Guardar respuesta'
                : 'Guardar conocimiento'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ============================================================
// PÁGINA PRINCIPAL
// ============================================================

const Training = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const urlBotId = searchParams.get('bot_id');

  const [bots, setBots] = useState([]);
  const [selectedBotId, setSelectedBotId] = useState(urlBotId ? parseInt(urlBotId) : null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingReport, setLoadingReport] = useState(false);
  const [error, setError] = useState(null);

  // Modal
  const [modalOpen, setModalOpen] = useState(false);
  const [modalRec, setModalRec] = useState(null);

  // 1. Cargar lista de bots al montar
  useEffect(() => {
    const loadBots = async () => {
      try {
        setLoading(true);
        const res = await botService.list();
        const userBots = res.data || [];
        setBots(userBots);

        if (urlBotId) {
          const found = userBots.find(b => b.id === parseInt(urlBotId));
          if (found) {
            setSelectedBotId(found.id);
          } else if (userBots.length > 0) {
            setSelectedBotId(userBots[0].id);
          }
        } else if (userBots.length >= 1) {
          setSelectedBotId(userBots[0].id);
        }
      } catch (e) {
        setError('No se pudieron cargar tus bots.');
      } finally {
        setLoading(false);
      }
    };
    loadBots();
    // eslint-disable-next-line
  }, []);

  // 2. Cargar reporte cuando cambia el bot seleccionado
  useEffect(() => {
    if (!selectedBotId) {
      setReport(null);
      return;
    }
    loadReport(selectedBotId);
    // eslint-disable-next-line
  }, [selectedBotId]);

  // 3. Sincronizar URL
  useEffect(() => {
    if (selectedBotId) {
      setSearchParams({ bot_id: selectedBotId }, { replace: true });
    }
    // eslint-disable-next-line
  }, [selectedBotId]);

  const loadReport = async (botId) => {
    try {
      setLoadingReport(true);
      setError(null);
      const res = await trainingService.getReport(botId, 100);
      setReport(res.data);
    } catch (e) {
      setError(
        e.response?.data?.detail ||
          'No se pudo cargar el análisis del Training Assistant.'
      );
    } finally {
      setLoadingReport(false);
    }
  };

  const handleSelectBot = (id) => setSelectedBotId(id);

  const handleAction = (rec) => {
    setModalRec(rec);
    setModalOpen(true);
  };

  const handleSaved = () => {
    // Refrescar el reporte con el mismo bot
    if (selectedBotId) {
      loadReport(selectedBotId);
    }
  };

  // ============================================================
  // RENDER
  // ============================================================

  if (loading) {
    return (
      <div className="min-h-screen bg-navy flex items-center justify-center">
        <div className="text-white/50">Cargando...</div>
      </div>
    );
  }

  if (bots.length === 0) {
    return (
      <div className="min-h-screen bg-navy text-white p-6">
        <div className="max-w-3xl mx-auto mt-20 text-center">
          <img src={LOGO_URL} alt="Nuvora" className="h-16 w-16 rounded-2xl mx-auto mb-6" />
          <h1 className="text-3xl font-bold mb-2">Training Assistant</h1>
          <p className="text-white/50 mb-8">
            Aún no tienes ningún bot. Crea uno para analizar su preparación.
          </p>
          <Button variant="primary" size="lg" onClick={() => navigate('/onboarding')}>
            Crear mi primer bot →
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-navy text-white">
      <header className="border-b border-white/5 bg-navy/80 backdrop-blur-xl sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 md:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/dashboard')}
              className="text-white/50 hover:text-white transition"
            >
              ←
            </button>
            <img src={LOGO_URL} alt="Nuvora" className="h-8 w-8 rounded-lg object-cover" />
            <h1 className="text-lg font-bold">Training Assistant</h1>
          </div>

          {bots.length > 1 && (
            <select
              value={selectedBotId || ''}
              onChange={(e) => handleSelectBot(parseInt(e.target.value))}
              className="bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-violet-500/50"
            >
              {bots.map((b) => (
                <option key={b.id} value={b.id} className="bg-navy">
                  {b.name}
                </option>
              ))}
            </select>
          )}
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 md:px-8 py-8 space-y-8">
        {error && (
          <Card className="p-4 border-red-500/30 bg-red-500/5">
            <p className="text-red-400 text-sm">{error}</p>
          </Card>
        )}

        {loadingReport && (
          <Card className="p-8 text-center">
            <p className="text-white/50">Analizando tu bot...</p>
          </Card>
        )}

        {report && !loadingReport && (
          <>
            <Card className="p-6">
              <ProgressBar progress={report.progress} />
              <div className="mt-6">
                <SummaryStats
                  covered={report.covered_count}
                  partial={report.partial_count}
                  missing={report.missing_count}
                />
              </div>
            </Card>

            {report.recommendations && report.recommendations.length > 0 && (
              <section>
                <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                  ⚠️ Prioridades
                  <Badge variant="magenta">{report.recommendations.length}</Badge>
                </h2>
                <div className="space-y-3">
                  {report.recommendations.map((rec) => (
                    <RecommendationCard key={rec.id} rec={rec} onAction={handleAction} />
                  ))}
                </div>
              </section>
            )}

            {report.unanswered_questions && report.unanswered_questions.length > 0 && (
              <section>
                <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                  🔥 Preguntas sin respuesta
                  <Badge variant="cyan">{report.unanswered_questions.length}</Badge>
                </h2>
                <div className="space-y-3">
                  {report.unanswered_questions.map((group, i) => (
                    <QuestionGroupCard key={i} group={group} />
                  ))}
                </div>
              </section>
            )}

            <section>
              <details className="group">
                <summary className="cursor-pointer text-lg font-bold flex items-center gap-2 hover:text-violet-300 transition">
                  📋 Todos los temas
                  <span className="text-sm text-white/40">({report.total_topics})</span>
                  <span className="text-xs text-white/30 ml-auto group-open:hidden">
                    Expandir ▾
                  </span>
                  <span className="text-xs text-white/30 ml-auto hidden group-open:inline">
                    Colapsar ▴
                  </span>
                </summary>
                <div className="mt-4 space-y-2">
                  {report.topics.map((t) => (
                    <TopicItem key={t.topic_id} topic={t} />
                  ))}
                </div>
              </details>
            </section>

            <Card className="p-4 text-xs text-white/30">
              <div className="flex flex-wrap gap-4">
                <span>Bot: {report.bot_name}</span>
                <span>Nicho: {report.nicho_id || 'otro'}</span>
                <span>Memorias: {report.memories_count}</span>
                <span>Fuentes listas: {report.ready_sources_count}</span>
              </div>
            </Card>
          </>
        )}

        {!report && !loadingReport && !error && (
          <Card className="p-8 text-center">
            <p className="text-white/50">Selecciona un bot para ver el análisis.</p>
          </Card>
        )}
      </main>

      {/* Modal */}
      <AddKnowledgeModal
        open={modalOpen}
        rec={modalRec}
        botId={selectedBotId}
        onClose={() => {
          setModalOpen(false);
          setModalRec(null);
        }}
        onSaved={handleSaved}
      />
    </div>
  );
};

export default Training;
