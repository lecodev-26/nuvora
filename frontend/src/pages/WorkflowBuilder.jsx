import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useWorkflowBuilder, generateNodeId } from '../hooks/useWorkflowBuilder';
import { workflowService } from '../services/workflowApi';
import { validateWorkflow, getErrorNodeIds } from '../utils/workflowValidation';
import Canvas from '../components/canvas/Canvas';
import NodeInspector from '../components/inspector/NodeInspector';
import TransitionInspector from '../components/inspector/TransitionInspector';
import NodePalette from '../components/builder/NodePalette';
import RunPanel from '../components/builder/RunPanel';
import Button from '../components/Button';

/**
 * WorkflowBuilder — Página del Visual Workflow Builder.
 */

const WorkflowBuilder = () => {
  const { botId, workflowId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();

  const builder = useWorkflowBuilder();
  const {
    nodes,
    transitions,
    workflowMetadata,
    loading,
    saving,
    dirty,
    serverError,
    saveError,
    validationErrors,
    selectedNodeId,
    selectedNode,
    selectedTransitionId,
    canUndo,
    canRedo,
    loadStart,
    loadSuccess,
    loadError,
    addNode,
    updateNode,
    deleteNode,
    moveNode,
    addTransition,
    updateTransition,
    deleteTransition,
    updateMetadata,
    selectNode,
    selectTransition,
    clearSelection,
    saveStart,
    saveSuccess,
    saveError: setSaveError,
    undo,
    redo,
    buildSavePayload,
    reset,
  } = builder;

  const [saveMessage, setSaveMessage] = useState(null);
  const [showErrorPanel, setShowErrorPanel] = useState(true);
  const [showRunPanel, setShowRunPanel] = useState(false);

  // ============================================================
  // VALIDACIÓN LOCAL (UX)
  // ============================================================

  const validation = useMemo(
    () => validateWorkflow({ nodes, transitions, workflowMetadata }),
    [nodes, transitions, workflowMetadata]
  );

  const errorNodeIds = useMemo(() => getErrorNodeIds(validation), [validation]);
  const hasBlockingErrors = validation.errors.length > 0;

  // ============================================================
  // CARGA INICIAL
  // ============================================================

  useEffect(() => {
    if (!workflowId || workflowId === 'new') {
      reset();
      loadSuccess({
        workflowId: null,
        botId: parseInt(botId),
        metadata: {
          name: 'Nuevo workflow',
          description: '',
          status: 'draft',
          trigger: 'manual',
          entry_node_id: null,
          meta: {},
        },
        nodes: [],
        transitions: [],
      });
      return;
    }

    loadStart();
    workflowService
      .get(botId, workflowId)
      .then((res) => {
        const wf = res.data;
        const positions = wf.meta?.positions || {};
        const nodesWithPos = (wf.nodes || []).map((n) => ({
          node_id: n.node_id,
          type: n.type,
          name: n.name,
          config: n.config,
          position: positions[n.node_id] || { x: 0, y: 0 },
        }));

        loadSuccess({
          workflowId: wf.id,
          botId: wf.bot_id,
          metadata: {
            name: wf.name,
            description: wf.description,
            status: wf.status,
            trigger: wf.trigger,
            entry_node_id: wf.entry_node_id,
            meta: wf.meta || {},
          },
          nodes: nodesWithPos,
          transitions: (wf.transitions || []).map((t) => ({
            from_node_id: t.from_node_id,
            to_node_id: t.to_node_id,
            condition: t.condition,
            label: t.label,
            order: t.order,
          })),
        });
      })
      .catch((err) => {
        loadError(err.response?.data?.detail || err.message || 'Error cargando workflow');
      });
  }, [botId, workflowId, loadStart, loadSuccess, loadError, reset]);

  // ============================================================
  // TRANSICIÓN SELECCIONADA
  // ============================================================

  const selectedTransition = useMemo(() => {
    if (!selectedTransitionId) return null;
    const parts = selectedTransitionId.split('→');
    if (parts.length < 4) return null;
    const [from_node_id, to_node_id, label] = parts;
    const labelOrNull = label || null;

    return transitions.find(
      (t) =>
        t.from_node_id === from_node_id &&
        t.to_node_id === to_node_id &&
        (t.label || null) === labelOrNull
    ) || null;
  }, [selectedTransitionId, transitions]);

  // ============================================================
  // ACCIONES DEL CANVAS
  // ============================================================

  const handleNodeClick = useCallback((nodeId) => selectNode(nodeId), [selectNode]);

  const handleNodeMove = useCallback(
    (nodeId, position) => moveNode(nodeId, position),
    [moveNode]
  );

  const handleEdgeClick = useCallback(
    (edgeId) => selectTransition(edgeId),
    [selectTransition]
  );

  const handleConnect = useCallback(({ source, target, sourceHandle }) => {
    const label = sourceHandle === 'true' ? 'true'
                : sourceHandle === 'false' ? 'false'
                : null;
    addTransition({
      from_node_id: source,
      to_node_id: target,
      condition: null,
      label,
      order: 0,
    });
  }, [addTransition]);

  // ============================================================
  // ACCIONES DE NODOS
  // ============================================================

  const handleAddNodeByType = useCallback((type) => {
    const nodeId = generateNodeId(type, nodes);
    const position = nodes.length === 0
      ? { x: 300, y: 150 }
      : { x: 300 + Math.random() * 200, y: 150 + Math.random() * 200 };

    addNode({ node_id: nodeId, type, name: null, config: null, position });
  }, [nodes, addNode]);

  const handleUpdateNode = useCallback(
    (nodeId, patch) => updateNode(nodeId, patch),
    [updateNode]
  );

  const handleDeleteNode = useCallback((nodeId) => {
    if (!confirm(`¿Eliminar el nodo '${nodeId}' y sus conexiones?`)) return;
    deleteNode(nodeId);
  }, [deleteNode]);

  const handleDuplicateNode = useCallback((nodeId) => {
    const original = nodes.find((n) => n.node_id === nodeId);
    if (!original) return;

    const newId = generateNodeId(original.type, nodes);
    const newPosition = {
      x: (original.position?.x || 0) + 80,
      y: (original.position?.y || 0) + 80,
    };

    addNode({
      node_id: newId,
      type: original.type,
      name: original.name,
      config: original.config ? JSON.parse(JSON.stringify(original.config)) : null,
      position: newPosition,
    });
  }, [nodes, addNode]);

  // ============================================================
  // ACCIONES DEL INSPECTOR (TRANSITION)
  // ============================================================

  const handleUpdateTransition = useCallback((patch) => {
    if (!selectedTransition) return;
    updateTransition(
      selectedTransition.from_node_id,
      selectedTransition.to_node_id,
      patch
    );
  }, [selectedTransition, updateTransition]);

  const handleDeleteTransition = useCallback(() => {
    if (!selectedTransition) return;
    if (!confirm('¿Eliminar esta transición?')) return;
    deleteTransition(
      selectedTransition.from_node_id,
      selectedTransition.to_node_id
    );
    clearSelection();
  }, [selectedTransition, deleteTransition, clearSelection]);

  // ============================================================
  // TECLADO GLOBAL
  // ============================================================

  useEffect(() => {
    const handleKeyDown = (e) => {
      const tag = document.activeElement?.tagName;
      const inInput = tag === 'INPUT' || tag === 'TEXTAREA';

      const mod = e.ctrlKey || e.metaKey;
      if (mod && e.key.toLowerCase() === 'z') {
        e.preventDefault();
        if (e.shiftKey) {
          if (canRedo) redo();
        } else {
          if (canUndo) undo();
        }
        return;
      }
      if (mod && e.key.toLowerCase() === 'y') {
        e.preventDefault();
        if (canRedo) redo();
        return;
      }

      if (!inInput && (e.key === 'Delete' || e.key === 'Backspace')) {
        if (selectedTransitionId && selectedTransition) {
          e.preventDefault();
          handleDeleteTransition();
        } else if (selectedNodeId) {
          e.preventDefault();
          handleDeleteNode(selectedNodeId);
        }
      }

      if (e.key === 'Escape') {
        clearSelection();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    selectedNodeId,
    selectedTransitionId,
    selectedTransition,
    canUndo,
    canRedo,
    undo,
    redo,
    handleDeleteNode,
    handleDeleteTransition,
    clearSelection,
  ]);

  // ============================================================
  // GUARDAR
  // ============================================================

  const handleSave = async () => {
    setSaveMessage(null);

    if (hasBlockingErrors) {
      setSaveMessage({
        type: 'error',
        text: `Corrige los ${validation.errors.length} errores antes de guardar`,
      });
      setShowErrorPanel(true);
      return;
    }

    saveStart();

    try {
      const payload = buildSavePayload();
      let res;

      if (workflowId && workflowId !== 'new') {
        res = await workflowService.update(botId, workflowId, payload);
      } else {
        res = await workflowService.create(botId, payload);
        const newId = res.data.id;
        navigate(`/workflows/${botId}/${newId}`, { replace: true });
      }

      saveSuccess();
      setSaveMessage({ type: 'success', text: 'Guardado correctamente' });
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (err) {
      const detail = err.response?.data?.detail;
      const msg = Array.isArray(detail)
        ? detail.map((e) => e.msg || JSON.stringify(e)).join(', ')
        : detail || err.message || 'Error guardando';
      setSaveError(msg);
      setSaveMessage({ type: 'error', text: msg });
      setShowErrorPanel(true);
    }
  };

  // ============================================================
  // ESTADOS DE CARGA
  // ============================================================

  if (loading) {
    return (
      <div className="min-h-screen bg-navy flex items-center justify-center">
        <div className="text-white/50">Cargando workflow...</div>
      </div>
    );
  }

  if (serverError) {
    return (
      <div className="min-h-screen bg-navy flex flex-col items-center justify-center gap-4">
        <div className="text-red-400">{serverError}</div>
        <Button variant="secondary" onClick={() => navigate('/dashboard')}>
          Volver al dashboard
        </Button>
      </div>
    );
  }

  // ¿Se puede probar? (workflow guardado = tiene id válido)
  const canRun = workflowId && workflowId !== 'new';

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <div className="min-h-screen bg-navy flex flex-col">
      {/* Barra superior */}
      <div className="border-b border-white/10 bg-white/5 backdrop-blur-sm px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              if (dirty && !confirm('Hay cambios sin guardar. ¿Salir igualmente?')) return;
              navigate('/dashboard');
            }}
          >
            ← Volver
          </Button>

          <input
            type="text"
            value={workflowMetadata.name}
            onChange={(e) => updateMetadata({ name: e.target.value })}
            className="bg-transparent border-b border-white/20 text-white text-lg font-semibold px-2 py-1 focus:outline-none focus:border-cyan-400 min-w-[200px]"
            placeholder="Nombre del workflow"
          />

          {dirty && (
            <span className="text-xs text-amber-400 bg-amber-500/10 px-2 py-1 rounded">
              ● Sin guardar
            </span>
          )}

          {hasBlockingErrors && (
            <span className="text-xs text-red-400 bg-red-500/10 px-2 py-1 rounded">
              ⚠️ {validation.errors.length} error{validation.errors.length > 1 ? 'es' : ''}
            </span>
          )}
        </div>

        <div className="flex items-center gap-3">
          {/* Undo / Redo */}
          <div className="flex items-center gap-1 border-r border-white/10 pr-3">
            <button
              type="button"
              onClick={() => canUndo && undo()}
              disabled={!canUndo}
              title="Deshacer (Ctrl+Z)"
              className={`px-2 py-1 rounded text-sm transition-colors ${
                canUndo
                  ? 'text-white hover:bg-white/10'
                  : 'text-white/20 cursor-not-allowed'
              }`}
            >
              ⟲
            </button>
            <button
              type="button"
              onClick={() => canRedo && redo()}
              disabled={!canRedo}
              title="Rehacer (Ctrl+Shift+Z / Ctrl+Y)"
              className={`px-2 py-1 rounded text-sm transition-colors ${
                canRedo
                  ? 'text-white hover:bg-white/10'
                  : 'text-white/20 cursor-not-allowed'
              }`}
            >
              ⟳
            </button>
          </div>

          {saveMessage && (
            <span
              className={`text-sm ${
                saveMessage.type === 'success' ? 'text-emerald-400' : 'text-red-400'
              }`}
            >
              {saveMessage.text}
            </span>
          )}

          <Button
            variant="secondary"
            size="sm"
            onClick={() => setShowRunPanel(true)}
            disabled={!canRun}
            title={canRun ? 'Probar workflow' : 'Guarda el workflow primero'}
          >
            ▶ Probar
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={handleSave}
            disabled={saving || !dirty}
          >
            {saving ? 'Guardando...' : 'Guardar'}
          </Button>
        </div>
      </div>

      {/* Panel de validación */}
      {hasBlockingErrors && showErrorPanel && (
        <div className="bg-red-500/10 border-b border-red-500/30 px-6 py-3">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="text-red-400 font-semibold text-sm mb-2">
                ⚠️ Errores de validación ({validation.errors.length})
              </div>
              <ul className="text-red-300 text-xs space-y-1 max-h-32 overflow-y-auto">
                {validation.errors.map((e, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span>•</span>
                    <span>{e.message}</span>
                  </li>
                ))}
              </ul>
            </div>
            <button
              type="button"
              onClick={() => setShowErrorPanel(false)}
              className="text-red-400 hover:text-red-300 text-xs shrink-0"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Aviso errores del backend */}
      {saveError && (
        <div className="bg-red-500/10 border-b border-red-500/30 px-6 py-2">
          <div className="text-red-400 text-sm">
            <span className="font-semibold">Backend:</span> {saveError}
          </div>
        </div>
      )}

      {/* Área principal */}
      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 relative">
          <Canvas
            nodes={nodes}
            transitions={transitions}
            selectedNodeId={selectedNodeId}
            selectedTransitionId={selectedTransitionId}
            errorNodeIds={errorNodeIds}
            onNodeClick={handleNodeClick}
            onNodeMove={handleNodeMove}
            onConnect={handleConnect}
            onEdgeClick={handleEdgeClick}
          />

          <NodePalette onAdd={handleAddNodeByType} />

          <div className="absolute bottom-6 right-6 text-white/30 text-xs space-y-1 text-right pointer-events-none">
            <div>Delete: borrar · Esc: deseleccionar</div>
            <div>Ctrl+Z: deshacer · Ctrl+Shift+Z: rehacer</div>
          </div>
        </div>

        {/* Inspector */}
        <div className="w-80 border-l border-white/10 bg-white/5 backdrop-blur-sm p-4 overflow-y-auto">
          {selectedTransition ? (
            <TransitionInspector
              transition={selectedTransition}
              onUpdate={handleUpdateTransition}
              onDelete={handleDeleteTransition}
            />
          ) : (
            <NodeInspector
              node={selectedNode}
              onUpdate={handleUpdateNode}
              onDelete={handleDeleteNode}
              onDuplicate={handleDuplicateNode}
            />
          )}

          {/* Debug */}
          <div className="mt-6 pt-4 border-t border-white/10">
            <h4 className="text-white/60 text-xs uppercase mb-2">Debug</h4>
            <div className="text-xs text-white/40 space-y-1">
              <div>nodes: {nodes.length}</div>
              <div>transitions: {transitions.length}</div>
              <div>errors: {validation.errors.length}</div>
              <div>canUndo: {String(canUndo)}</div>
              <div>canRedo: {String(canRedo)}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Modal de ejecución */}
      <RunPanel
        open={showRunPanel}
        onClose={() => setShowRunPanel(false)}
        botId={botId}
        workflowId={workflowId}
        nodes={nodes}
        dirty={dirty}
      />
    </div>
  );
};

export default WorkflowBuilder;
