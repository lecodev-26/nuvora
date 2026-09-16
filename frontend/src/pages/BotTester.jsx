import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { testService } from '../services/testService';
import { workflowService } from '../services/workflowApi';
import Button from '../components/Button';
import Spinner from '../components/ui/Spinner';
import ConfirmModal from '../components/ui/ConfirmModal';
import TestList from '../components/tester/TestList';
import TestEditor from '../components/tester/TestEditor';
import TestResults from '../components/tester/TestResults';

/**
 * BotTester — Página principal del Bot Tester (14.8.10).
 *
 * Ruta: /bots/:botId/tester?workflow_id=N
 *
 * Features:
 *   - Lista de tests del workflow
 *   - Editor para crear/editar tests
 *   - Ejecutar test individual
 *   - Ejecutar todos los tests
 *   - Análisis estático del workflow
 *   - Visualización de resultados y trace
 */

const BotTester = () => {
  const { botId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { token } = useAuth();

  const workflowIdParam = searchParams.get('workflow_id');
  const [workflowId, setWorkflowId] = useState(
    workflowIdParam ? parseInt(workflowIdParam) : null
  );
  const [workflows, setWorkflows] = useState([]);
  const [workflow, setWorkflow] = useState(null);

  // Estado
  const [tests, setTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [running, setRunning] = useState(false);

  // Editor
  const [showEditor, setShowEditor] = useState(false);
  const [editingTest, setEditingTest] = useState(null);

  // Resultados
  const [lastResults, setLastResults] = useState({});
  const [showResults, setShowResults] = useState(null);

  // Análisis
  const [analysis, setAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);

  // Confirm
  const [confirmDialog, setConfirmDialog] = useState(null);

  // ============================================================
  // CARGA INICIAL
  // ============================================================

  const loadWorkflows = useCallback(async () => {
    try {
      const res = await workflowService.list(botId);
      setWorkflows(res.data.workflows || []);
      // Si no hay workflow seleccionado, usar el primero
      if (!workflowId && res.data.workflows?.length > 0) {
        setWorkflowId(res.data.workflows[0].id);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Error cargando workflows');
    }
  }, [botId, workflowId]);

  const loadWorkflow = useCallback(async () => {
    if (!workflowId) return;
    try {
      const res = await workflowService.get(botId, workflowId);
      setWorkflow(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error cargando workflow');
    }
  }, [botId, workflowId]);

  const loadTests = useCallback(async () => {
    if (!workflowId) {
      setTests([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const res = await testService.list(botId, { workflow_id: workflowId });
      setTests(res.data.tests || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error cargando tests');
    } finally {
      setLoading(false);
    }
  }, [botId, workflowId]);

  useEffect(() => {
    loadWorkflows();
  }, [loadWorkflows]);

  useEffect(() => {
    if (workflowId) {
      loadWorkflow();
      loadTests();
    }
  }, [workflowId, loadWorkflow, loadTests]);

  // ============================================================
  // CRUD
  // ============================================================

  const handleCreateClick = () => {
    setEditingTest(null);
    setShowEditor(true);
  };

  const handleEditClick = (testId) => {
    const t = tests.find((x) => x.id === testId);
    setEditingTest(t || null);
    setShowEditor(true);
  };

  const handleSaveTest = async (payload) => {
    setSaving(true);
    try {
      if (editingTest) {
        await testService.update(botId, editingTest.id, payload);
      } else {
        await testService.create(botId, workflowId, payload);
      }
      setShowEditor(false);
      setEditingTest(null);
      await loadTests();
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteTest = (testId) => {
    const t = tests.find((x) => x.id === testId);
    setConfirmDialog({
      title: 'Eliminar test',
      message: `¿Eliminar el test "${t?.name}"?`,
      confirmText: 'Eliminar',
      danger: true,
      onConfirm: async () => {
        setConfirmDialog(null);
        try {
          await testService.delete(botId, testId);
          await loadTests();
        } catch (err) {
          setError(err.response?.data?.detail || 'Error eliminando test');
        }
      },
    });
  };

  const handleToggleEnabled = async (testId) => {
    const t = tests.find((x) => x.id === testId);
    if (!t) return;
    try {
      await testService.update(botId, testId, { enabled: !t.enabled });
      await loadTests();
    } catch (err) {
      setError(err.response?.data?.detail || 'Error actualizando test');
    }
  };

  // ============================================================
  // EJECUCIÓN
  // ============================================================

  const handleRunTest = async (testId) => {
    setRunning(true);
    try {
      const res = await testService.run(botId, testId);
      setLastResults((prev) => ({ ...prev, [testId]: res.data }));
      setShowResults(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error ejecutando test');
    } finally {
      setRunning(false);
    }
  };

  const handleRunAll = async () => {
    if (!workflowId) return;
    setRunning(true);
    try {
      const res = await testService.runAll(botId, workflowId, true);
      // Guardar resultados por test
      const newResults = { ...lastResults };
      (res.data.results || []).forEach((r) => {
        if (r.test_id) newResults[r.test_id] = r;
      });
      setLastResults(newResults);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error ejecutando tests');
    } finally {
      setRunning(false);
    }
  };

  const handleAnalyze = async () => {
    if (!workflowId) return;
    setAnalyzing(true);
    try {
      const res = await testService.analyze(botId, workflowId);
      setAnalysis(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error analizando workflow');
    } finally {
      setAnalyzing(false);
    }
  };

  // ============================================================
  // RENDER
  // ============================================================

  if (workflows.length === 0 && loading) {
    return <Spinner fullScreen size="lg" label="Cargando..." />;
  }

  if (workflows.length === 0) {
    return (
      <div className="min-h-screen bg-navy flex flex-col items-center justify-center gap-4 p-6">
        <div className="text-white/60">No hay workflows en este bot.</div>
        <Button variant="secondary" onClick={() => navigate(`/workflows/${botId}`)}>
          Ir a Workflows
        </Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-navy">
      {/* Header */}
      <div className="border-b border-white/10 bg-white/5 backdrop-blur-sm px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(`/workflows/${botId}/${workflowId}`)}
          >
            ← Volver al Builder
          </Button>
          <div>
            <h1 className="text-white font-semibold flex items-center gap-2">
              🧪 Bot Tester
            </h1>
            <div className="text-white/50 text-xs">
              {workflow?.name || 'Workflow'} · {tests.length} tests
            </div>
          </div>
        </div>

        {/* Selector de workflow */}
        {workflows.length > 1 && (
          <select
            value={workflowId || ''}
            onChange={(e) => setWorkflowId(parseInt(e.target.value))}
            className="bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white text-sm focus:outline-none focus:border-cyan-400/60"
          >
            {workflows.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name}
              </option>
            ))}
          </select>
        )}

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={handleAnalyze}
            disabled={analyzing}
          >
            {analyzing ? '🔍 Analizando...' : '🔍 Analizar'}
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={handleRunAll}
            disabled={running || tests.length === 0}
          >
            {running ? '▶ Ejecutando...' : '▶ Run all'}
          </Button>
          <Button variant="primary" size="sm" onClick={handleCreateClick}>
            + Nuevo test
          </Button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-500/10 border-b border-red-500/30 px-6 py-2">
          <div className="text-red-400 text-sm flex items-center justify-between">
            <span>⚠️ {error}</span>
            <button
              onClick={() => setError(null)}
              className="text-red-400 hover:text-red-300 text-xs"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Contenido */}
      <div className="max-w-4xl mx-auto px-6 py-6 space-y-6">
        {/* Análisis estático */}
        {analysis && (
          <div className="bg-white/5 border border-white/10 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="text-white font-semibold text-sm">
                Análisis del workflow
              </div>
              <button
                onClick={() => setAnalysis(null)}
                className="text-white/40 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-3 gap-3 mb-3 text-xs">
              <div className="text-center">
                <div className="text-2xl font-bold text-red-400">
                  {analysis.summary?.error || 0}
                </div>
                <div className="text-white/40 uppercase tracking-wider">Errores</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-amber-400">
                  {analysis.summary?.warning || 0}
                </div>
                <div className="text-white/40 uppercase tracking-wider">Warnings</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-cyan-400">
                  {analysis.summary?.info || 0}
                </div>
                <div className="text-white/40 uppercase tracking-wider">Info</div>
              </div>
            </div>

            {analysis.issues && analysis.issues.length > 0 ? (
              <div className="space-y-1">
                {analysis.issues.map((issue, i) => (
                  <div
                    key={i}
                    className={`
                      flex items-start gap-2 text-xs rounded px-2 py-1
                      ${issue.severity === 'error' ? 'text-red-300' :
                        issue.severity === 'warning' ? 'text-amber-300' :
                        'text-cyan-300'}
                    `}
                  >
                    <span className="shrink-0">
                      {issue.severity === 'error' ? '❌' :
                       issue.severity === 'warning' ? '⚠️' : 'ℹ️'}
                    </span>
                    <div className="min-w-0">
                      <span className="font-mono text-[10px] opacity-60">
                        {issue.code}
                      </span>
                      <div>{issue.message}</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-emerald-400 text-sm text-center">
                ✅ Sin problemas detectados
              </div>
            )}
          </div>
        )}

        {/* Resultado expandido */}
        {showResults && (
          <TestResults
            result={showResults}
            botId={botId}
            workflowId={workflowId}
            onClose={() => setShowResults(null)}
          />
        )}

        {/* Lista de tests */}
        <TestList
          tests={tests}
          onRun={handleRunTest}
          onEdit={handleEditClick}
          onDelete={handleDeleteTest}
          onToggleEnabled={handleToggleEnabled}
          lastResults={lastResults}
          loading={loading}
        />
      </div>

      {/* Editor */}
      <TestEditor
        open={showEditor}
        test={editingTest}
        onSave={handleSaveTest}
        onClose={() => {
          setShowEditor(false);
          setEditingTest(null);
        }}
        saving={saving}
      />

      {/* Confirm */}
      <ConfirmModal
        open={!!confirmDialog}
        title={confirmDialog?.title}
        message={confirmDialog?.message}
        confirmText={confirmDialog?.confirmText}
        danger={confirmDialog?.danger}
        onConfirm={confirmDialog?.onConfirm}
        onCancel={() => setConfirmDialog(null)}
      />
    </div>
  );
};

export default BotTester;
