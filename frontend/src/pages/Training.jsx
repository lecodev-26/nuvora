import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { botService, trainingService } from '../services/api';
import Button from '../components/Button';
import Card from '../components/Card';
import Badge from '../components/Badge';

const LOGO_URL = '/logo.png';

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
            disabled
            onClick={() => onAction && onAction(rec)}
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

  // 1. Cargar lista de bots al montar
  useEffect(() => {
    const loadBots = async () => {
      try {
        setLoading(true);
        const res = await botService.list();
        const userBots = res.data || [];
        setBots(userBots);

        // Resolver bot_id según reglas
        if (urlBotId) {
          // Caso 1: bot_id presente en query → usarlo (validar que pertenece al usuario)
          const found = userBots.find(b => b.id === parseInt(urlBotId));
          if (found) {
            setSelectedBotId(found.id);
          } else if (userBots.length > 0) {
            setSelectedBotId(userBots[0].id);
          }
        } else if (userBots.length === 1) {
          // Caso 2: sin bot_id, 1 bot → cargar automáticamente
          setSelectedBotId(userBots[0].id);
        } else if (userBots.length > 1) {
          // Caso 3: sin bot_id, varios bots → dejamos que el usuario elija
          // (selectedBotId queda en el primero por defecto, pero mostramos selector)
          setSelectedBotId(userBots[0].id);
        }
        // Caso 4: 0 bots → selectedBotId queda null
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
    const loadReport = async () => {
      try {
        setLoadingReport(true);
        setError(null);
        const res = await trainingService.getReport(selectedBotId, 100);
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
    loadReport();
  }, [selectedBotId]);

  // 3. Sincronizar URL con bot seleccionado
  useEffect(() => {
    if (selectedBotId) {
      setSearchParams({ bot_id: selectedBotId }, { replace: true });
    }
    // eslint-disable-next-line
  }, [selectedBotId]);

  // Handlers
  const handleSelectBot = (id) => setSelectedBotId(id);
  const handleAction = (rec) => {
    // 14.4.8 conectará esto
    console.log('Acción pendiente (14.4.8):', rec);
  };

  // ============================================================
  // RENDER
  // ============================================================

  // Loading inicial
  if (loading) {
    return (
      <div className="min-h-screen bg-navy flex items-center justify-center">
        <div className="text-white/50">Cargando...</div>
      </div>
    );
  }

  // Sin bots
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
      {/* Header */}
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

          {/* Selector de bot (si hay varios) */}
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

      {/* Contenido */}
      <main className="max-w-6xl mx-auto px-4 md:px-8 py-8 space-y-8">
        {/* Error */}
        {error && (
          <Card className="p-4 border-red-500/30 bg-red-500/5">
            <p className="text-red-400 text-sm">{error}</p>
          </Card>
        )}

        {/* Loading reporte */}
        {loadingReport && (
          <Card className="p-8 text-center">
            <p className="text-white/50">Analizando tu bot...</p>
          </Card>
        )}

        {/* Reporte */}
        {report && !loadingReport && (
          <>
            {/* Progreso */}
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

            {/* Prioridades (recomendaciones) */}
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

            {/* Preguntas sin responder */}
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

            {/* Todos los temas (colapsable) */}
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

            {/* Metadata */}
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

        {/* Sin reporte ni error */}
        {!report && !loadingReport && !error && (
          <Card className="p-8 text-center">
            <p className="text-white/50">Selecciona un bot para ver el análisis.</p>
          </Card>
        )}
      </main>
    </div>
  );
};

export default Training;
