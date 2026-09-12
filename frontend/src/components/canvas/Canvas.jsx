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
 *   - nodes: array de nodos del builder ({node_id, type, name, config, position})
 *   - transitions: array de transiciones ({from_node_id, to_node_id, label, condition})
 *   - onNodeClick: (nodeId) => void
 *   - onNodeMove: (nodeId, position) => void
 *   - onConnect: ({ source, target, sourceHandle, targetHandle }) => void
 *   - selectedNodeId: string | null
 *
 * NO conoce la API. Solo dibuja y notifica eventos.
 */

// ============================================================
// CONVERSIÓN BUILDER → REACT FLOW
// ============================================================

function builderToFlowNodes(builderNodes, selectedNodeId) {
  return builderNodes.map((n) => ({
    id: n.node_id,
    type: n.type,                 // ← coincide con NODE_TYPES
    position: n.position || { x: 0, y: 0 },
    data: {
      node_id: n.node_id,
      type: n.type,
      name: n.name,
      config: n.config,
      label: n.name || null,
    },
    selected: n.node_id === selectedNodeId,
  }));
}

function builderToFlowEdges(builderTransitions) {
  return builderTransitions.map((t, idx) => {
    const isConditional = t.condition || t.label === 'true' || t.label === 'false';
    const isTrue = t.label === 'true';
    const isFalse = t.label === 'false';

    // Color según tipo
    let stroke = 'rgba(255,255,255,0.4)';
    let markerColor = 'rgba(255,255,255,0.6)';

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

    return {
      id: `${t.from_node_id}→${t.to_node_id}→${idx}`,
      source: t.from_node_id,
      target: t.to_node_id,
      sourceHandle: t.label === 'true' ? 'true' : t.label === 'false' ? 'false' : undefined,
      label: t.condition || undefined,
      animated: false,
      style: { stroke, strokeWidth: 2 },
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
  selectedNodeId,
}) => {
  // Convertir a formato React Flow
  const flowNodes = useMemo(
    () => builderToFlowNodes(builderNodes, selectedNodeId),
    [builderNodes, selectedNodeId]
  );

  const flowEdges = useMemo(
    () => builderToFlowEdges(builderTransitions),
    [builderTransitions]
  );

  // Handlers
  const handleNodeClick = useCallback(
    (event, node) => {
      if (onNodeClick) onNodeClick(node.id);
    },
    [onNodeClick]
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

  return (
    <div className="w-full h-full bg-navy">
      <ReactFlow
        nodes={flowNodes}
        edges={flowEdges}
        nodeTypes={NODE_TYPES}
        onNodeClick={handleNodeClick}
        onNodeDragStop={handleNodeDragStop}
        onConnect={handleConnect}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.2}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
        defaultEdgeOptions={{ animated: false }}
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
