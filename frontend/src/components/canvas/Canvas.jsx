import React, { useCallback, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import CustomNode from './CustomNode';

/**
 * Canvas — Wrapper sobre ReactFlow para el Workflow Builder.
 *
 * Props:
 *   - nodes: array de nodos del builder ({node_id, type, name, config, position})
 *   - transitions: array de transiciones ({from_node_id, to_node_id, ...})
 *   - onNodeClick: (nodeId) => void
 *   - onNodeMove: (nodeId, position) => void  (al soltar)
 *   - onConnect: ({ source, target }) => void
 *   - selectedNodeId: string | null
 *
 * NO conoce la API. Solo dibuja y notifica eventos.
 */

const nodeTypes = {
  custom: CustomNode,
};

// ============================================================
// CONVERSIÓN BUILDER → REACT FLOW
// ============================================================

function builderToFlowNodes(builderNodes) {
  return builderNodes.map(n => ({
    id: n.node_id,
    type: 'custom',
    position: n.position || { x: 0, y: 0 },
    data: {
      type: n.type,
      node_id: n.node_id,
      name: n.name,
      config: n.config,
      label: n.name || n.node_id,
      preview: buildPreview(n),
    },
  }));
}

function builderToFlowEdges(builderTransitions) {
  return builderTransitions.map((t, idx) => ({
    id: `${t.from_node_id}-${t.to_node_id}-${idx}`,
    source: t.from_node_id,
    target: t.to_node_id,
    label: t.label || undefined,
    animated: false,
    style: { stroke: 'rgba(255,255,255,0.4)', strokeWidth: 2 },
    markerEnd: { type: MarkerType.ArrowClosed, color: 'rgba(255,255,255,0.6)' },
  }));
}

function buildPreview(node) {
  if (!node.config) return null;
  if (node.config.text) return `"${truncate(node.config.text, 40)}"`;
  if (node.config.variable) return `var: ${node.config.variable}`;
  if (node.config.condition) return `if (${truncate(node.config.condition, 30)})`;
  if (node.config.name) return `${node.config.name}`;
  return null;
}

function truncate(str, max) {
  if (!str) return '';
  return str.length > max ? str.slice(0, max) + '…' : str;
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
  const flowNodes = useMemo(() => {
    const converted = builderToFlowNodes(builderNodes);
    // Marcar seleccionado
    return converted.map(n => ({
      ...n,
      selected: n.id === selectedNodeId,
    }));
  }, [builderNodes, selectedNodeId]);

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
        onConnect({ source: connection.source, target: connection.target });
      }
    },
    [onConnect]
  );

  return (
    <div className="w-full h-full bg-navy">
      <ReactFlow
        nodes={flowNodes}
        edges={flowEdges}
        nodeTypes={nodeTypes}
        onNodeClick={handleNodeClick}
        onNodeDragStop={handleNodeDragStop}
        onConnect={handleConnect}
        fitView
        minZoom={0.2}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
        defaultEdgeOptions={{ animated: false }}
      >
        <Background color="rgba(255,255,255,0.1)" gap={20} size={1} />
        <Controls
          className="!bg-white/5 !backdrop-blur-sm !border !border-white/10 !rounded-lg"
          showInteractive={false}
        />
        <MiniMap
          className="!bg-white/5 !backdrop-blur-sm !border !border-white/10 !rounded-lg"
          nodeColor={(node) => {
            const t = node.data?.type;
            const colors = {
              start: '#10b981',
              message: '#00C6FF',
              question: '#7B5CFF',
              condition: '#f59e0b',
              variable: '#d946ef',
              response: '#3b82f6',
              end: '#ef4444',
            };
            return colors[t] || '#64748b';
          }}
          maskColor="rgba(10,10,20,0.7)"
        />
      </ReactFlow>
    </div>
  );
};

export default Canvas;
