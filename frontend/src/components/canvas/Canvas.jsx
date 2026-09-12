import React, { useCallback, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { NODE_TYPES } from './nodes';

/**
 * Canvas — Wrapper sobre ReactFlow para el Workflow Builder.
 *
 * Props:
 *   - nodes: array de nodos del builder
 *   - transitions: array de transiciones
 *   - onNodeClick: (nodeId) => void
 *   - onNodeMove: (nodeId, position) => void
 *   - onConnect: ({ source, target, sourceHandle }) => void
 *   - onEdgeClick: (transitionId) => void
 *   - selectedNodeId, selectedTransitionId
 */

// ============================================================
// CONVERSIÓN BUILDER → REACT FLOW
// ============================================================

function builderToFlowNodes(builderNodes, selectedNodeId, errorNodeIds) {
  const errorSet = errorNodeIds instanceof Set ? errorNodeIds : new Set();
  return builderNodes.map((n) => ({
    id: n.node_id,
    type: n.type,
    position: n.position || { x: 0, y: 0 },
    data: {
      node_id: n.node_id,
      type: n.type,
      name: n.name,
      config: n.config,
      label: n.name || null,
      hasError: errorSet.has(n.node_id),
    },
    selected: n.node_id === selectedNodeId,
  }));
}

function makeEdgeId(t, idx) {
  return `${t.from_node_id}→${t.to_node_id}→${t.label || ''}→${idx}`;
}

function builderToFlowEdges(builderTransitions, selectedTransitionId) {
  return builderTransitions.map((t, idx) => {
    const edgeId = makeEdgeId(t, idx);

    // Determinar color por tipo
    const isTrue = t.label === 'true';
    const isFalse = t.label === 'false';
    const isConditional = t.condition;

    let stroke = 'rgba(255,255,255,0.4)';
    let markerColor = 'rgba(255,255,255,0.6)';
    let strokeWidth = 2;

    if (isTrue) {
      stroke = 'rgba(16,185,129,0.7)';
      markerColor = 'rgba(16,185,129,0.9)';
    } else if (isFalse) {
      stroke = 'rgba(239,68,68,0.7)';
      markerColor = 'rgba(239,68,68,0.9)';
    } else if (isConditional) {
      stroke = 'rgba(245,158,11,0.7)';
      markerColor = 'rgba(245,158,11,0.9)';
    }

    const isSelected = selectedTransitionId === edgeId;

    if (isSelected) {
      strokeWidth = 3;
      stroke = stroke.replace(/[\d.]+\)$/, '1)');
    }

    return {
      id: edgeId,
      source: t.from_node_id,
      target: t.to_node_id,
      sourceHandle: t.label === 'true' ? 'true' : t.label === 'false' ? 'false' : undefined,
      label: t.condition || undefined,
      animated: false,
      selected: isSelected,
      style: { stroke, strokeWidth },
      markerEnd: { type: MarkerType.ArrowClosed, color: markerColor },
      labelStyle: { fill: 'rgba(255,255,255,0.7)', fontSize: 10 },
      labelBgStyle: { fill: 'rgba(10,10,20,0.8)' },
      labelBgPadding: [4, 2],
      labelBgBorderRadius: 4,
    };
  });
}

// ============================================================
// COMPONENTE
// ============================================================

const Canvas = ({
  nodes: builderNodes,
  transitions: builderTransitions,
  onNodeClick,
  onNodeMove,
  onConnect,
  onEdgeClick,
  selectedNodeId,
  selectedTransitionId,
  errorNodeIds,
}) => {
  const flowNodes = useMemo(
    () => builderToFlowNodes(builderNodes, selectedNodeId, errorNodeIds),
    [builderNodes, selectedNodeId, errorNodeIds]
  );

  const flowEdges = useMemo(
    () => builderToFlowEdges(builderTransitions, selectedTransitionId),
    [builderTransitions, selectedTransitionId]
  );

  // Handlers
  const handleNodeClick = useCallback(
    (event, node) => {
      if (onNodeClick) onNodeClick(node.id);
    },
    [onNodeClick]
  );

  const handleEdgeClick = useCallback(
    (event, edge) => {
      if (onEdgeClick) onEdgeClick(edge.id);
    },
    [onEdgeClick]
  );

  const handleNodeDragStop = useCallback(
    (event, node) => {
      if (onNodeMove) onNodeMove(node.id, { x: node.position.x, y: node.position.y });
    },
    [onNodeMove]
  );

  const handleConnect = useCallback(
    (connection) => {
      if (onConnect) {
        onConnect({
          source: connection.source,
          target: connection.target,
          sourceHandle: connection.sourceHandle,
          targetHandle: connection.targetHandle,
        });
      }
    },
    [onConnect]
  );

  /**
   * Validación UX de conexiones:
   *  - No permitir conectar hacia un START
   *  - No permitir conectar desde un END
   *  - No permitir auto-conexión
   *  - No permitir duplicados exactos
   */
  const isValidConnection = useCallback(
    (connection) => {
      const sourceNode = builderNodes.find((n) => n.node_id === connection.source);
      const targetNode = builderNodes.find((n) => n.node_id === connection.target);

      if (!sourceNode || !targetNode) return false;
      if (sourceNode.node_id === targetNode.node_id) return false;
      if (sourceNode.type === 'end') return false;
      if (targetNode.type === 'start') return false;

      // Duplicados exactos
      const exists = builderTransitions.some(
        (t) =>
          t.from_node_id === connection.source &&
          t.to_node_id === connection.target &&
          (t.label || null) === (connection.sourceHandle || null)
      );
      if (exists) return false;

      return true;
    },
    [builderNodes, builderTransitions]
  );

  return (
    <div className="w-full h-full bg-navy">
      <ReactFlow
        nodes={flowNodes}
        edges={flowEdges}
        nodeTypes={NODE_TYPES}
        onNodeClick={handleNodeClick}
        onNodeDragStop={handleNodeDragStop}
        onConnect={handleConnect}
        onEdgeClick={handleEdgeClick}
        isValidConnection={isValidConnection}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.2}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
        defaultEdgeOptions={{ animated: false }}
        edgesFocusable
        edgesReconnectable={false}
        elementsSelectable
      >
        <Background color="rgba(255,255,255,0.08)" gap={24} size={1} />
        <Controls
          className="!bg-white/5 !backdrop-blur-sm !border !border-white/10 !rounded-lg"
          showInteractive={false}
        />
        <MiniMap
          className="!bg-white/5 !backdrop-blur-sm !border !border-white/10 !rounded-lg"
          nodeColor={(node) => {
            const colors = {
              start: '#10b981',
              message: '#00C6FF',
              question: '#7B5CFF',
              condition: '#f59e0b',
              variable: '#d946ef',
              response: '#3b82f6',
              end: '#ef4444',
            };
            return colors[node.type] || '#64748b';
          }}
          maskColor="rgba(10,10,20,0.7)"
          pannable
          zoomable
        />
      </ReactFlow>
    </div>
  );
};

export default Canvas;
