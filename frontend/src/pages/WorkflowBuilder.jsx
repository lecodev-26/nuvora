import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useWorkflowBuilder } from '../hooks/useWorkflowBuilder';
import { workflowService } from '../services/workflowApi';
import Canvas from '../components/canvas/Canvas';
import NodeInspector from '../components/inspector/NodeInspector';
import Button from '../components/Button';

/**
 * WorkflowBuilder — Página del Visual Workflow Builder.
 *
 * Ruta: /workflows/:botId y /workflows/:botId/:workflowId
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
    loadStart,
    loadSuccess,
    loadError,
    addNode,
    updateNode,
    deleteNode,
    moveNode,
    addTransition,
    updateMetadata,
    selectNode,
    clearSelection,
    saveStart,
    saveSuccess,
    saveError: setSaveError,
    buildSavePayload,
    reset,
  } = builder;

  const [saveMessage, setSaveMessage] = useState(null);

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
  // ACCIONES DEL CANVAS
  // ============================================================

  const handleNodeClick = useCallback((nodeId) => {
    selectNode(nodeId);
  }, [selectNode]);

  const handleNodeMove = useCallback((nodeId, position) => {
    moveNode(nodeId, position);
  }, [moveNode]);

  const handleConnect = useCallback(({ source, target, sourceHandle }) => {
    // Si viene de CONDITION, usar el handle id como label (true/false)
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
  // ACCIONES DEL INSPECTOR
  // ============================================================

  const handleUpdateNode = useCallback((nodeId, patch) => {
    updateNode(nodeId, patch);
  }, [updateNode]);

  const handleDeleteNode = useCallback((nodeId) => {
    if (!confirm(`¿Eliminar el nodo '${nodeId}' y sus conexiones?`)) return;
    deleteNode(nodeId);
  }, [deleteNode]);

  // ============================================================
  // GUARDAR
  // ============================================================

  const handleSave = async () => {
    setSaveMessage(null);
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
    }
  };

  // ============================================================
  // AÑADIR NODO
  // ============================================================

  const handleAddNode = () => {
    const id = prompt('ID del nodo (ej: s1, m1, e1):');
    if (!id) return;
    const type = prompt('Tipo (start|message|question|condition|variable|response|end):');
    if (!type) return;

    // Posición: centrada con offset aleatorio
    const position = {
      x: 200 + Math.random() * 300,
      y: 100 + Math.random() * 300,
    };

    addNode({
      node_id: id,
      type,
      name: null,
      config: null,
      position,
    });
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
        </div>

        <div className="flex items-center gap-3">
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
            variant="primary"
            size="sm"
            onClick={handleSave}
            disabled={saving || !dirty}
          >
            {saving ? 'Guardando...' : 'Guardar'}
          </Button>
        </div>
      </div>

      {/* Aviso errores */}
      {(saveError || validationErrors.length > 0) && (
        <div className="bg-red-500/10 border-b border-red-500/30 px-6 py-2">
          <div className="text-red-400 text-sm">
            {saveError && <div>⚠️ {saveError}</div>}
            {validationErrors.map((e, i) => (
              <div key={i}>⚠️ {e.message}</div>
            ))}
          </div>
        </div>
      )}

      {/* Área principal: Canvas + Inspector */}
      <div className="flex-1 flex overflow-hidden">
        {/* Canvas */}
        <div className="flex-1 relative">
          <Canvas
            nodes={nodes}
            transitions={transitions}
            selectedNodeId={selectedNodeId}
            onNodeClick={handleNodeClick}
            onNodeMove={handleNodeMove}
            onConnect={handleConnect}
          />

          {/* Botón flotante: añadir nodo */}
          <div className="absolute bottom-6 left-6 flex gap-2">
            <Button variant="secondary" size="sm" onClick={handleAddNode}>
              + Añadir nodo
            </Button>
          </div>
        </div>

        {/* Inspector */}
        <div className="w-80 border-l border-white/10 bg-white/5 backdrop-blur-sm p-4 overflow-y-auto">
          <NodeInspector
            node={selectedNode}
            onUpdate={handleUpdateNode}
            onDelete={handleDeleteNode}
          />

          {/* Debug (temporal, quitar en 14.6.13) */}
          <div className="mt-6 pt-4 border-t border-white/10">
            <h4 className="text-white/60 text-xs uppercase mb-2">Debug</h4>
            <div className="text-xs text-white/40 space-y-1">
              <div>nodes: {nodes.length}</div>
              <div>transitions: {transitions.length}</div>
              <div>selected: {selectedNodeId || '—'}</div>
              <div>dirty: {String(dirty)}</div>
              <div>saving: {String(saving)}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorkflowBuilder;
