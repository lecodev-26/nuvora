import React from 'react';
import InspectorHeader from './InspectorHeader';
import InspectorMessage from './InspectorMessage';
import InspectorQuestion from './InspectorQuestion';
import InspectorCondition from './InspectorCondition';
import InspectorVariable from './InspectorVariable';
import InspectorResponse from './InspectorResponse';

/**
 * NodeInspector — panel derecho del Workflow Builder.
 *
 * Al seleccionar un nodo, muestra el formulario específico según su tipo.
 * START y END no tienen inspector propio (solo header + nombre).
 */
const NodeInspector = ({ node, onUpdate, onDelete }) => {
  if (!node) {
    return (
      <div className="text-white/40 text-sm">
        Selecciona un nodo para ver sus propiedades.
      </div>
    );
  }

  // Handler para actualizar campos del nodo
  const handleUpdate = (patch) => {
    // patch puede incluir { config: {...}, name: '...' }
    onUpdate(node.node_id, patch);
  };

  // Config base para START/END (solo nombre)
  const renderBaseName = () => (
    <label className="block">
      <span className="text-white/60 text-xs uppercase tracking-wider">
        Nombre (opcional)
      </span>
      <input
        type="text"
        value={node.name || ''}
        onChange={(e) => handleUpdate({ name: e.target.value })}
        placeholder="Ej: Inicio"
        className="mt-2 w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-400/60"
      />
    </label>
  );

  // Elegir inspector según tipo
  let body;
  switch (node.type) {
    case 'message':
      body = <InspectorMessage node={node} onUpdate={handleUpdate} />;
      break;
    case 'question':
      body = <InspectorQuestion node={node} onUpdate={handleUpdate} />;
      break;
    case 'condition':
      body = <InspectorCondition node={node} onUpdate={handleUpdate} />;
      break;
    case 'variable':
      body = <InspectorVariable node={node} onUpdate={handleUpdate} />;
      break;
    case 'response':
      body = <InspectorResponse node={node} onUpdate={handleUpdate} />;
      break;
    case 'start':
    case 'end':
      body = (
        <div className="space-y-3">
          <div className="text-white/40 text-xs">
            Este nodo no tiene configuración adicional.
          </div>
          {renderBaseName()}
        </div>
      );
      break;
    default:
      body = (
        <div className="text-amber-400 text-sm">
          ⚠️ Tipo de nodo desconocido: {node.type}
        </div>
      );
  }

  return (
    <div>
      <InspectorHeader node={node} onDelete={() => onDelete(node.node_id)} />
      {body}
    </div>
  );
};

export default NodeInspector;
