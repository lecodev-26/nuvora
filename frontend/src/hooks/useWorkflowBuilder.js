import { useCallback, useMemo, useReducer } from 'react';

/**
 * useWorkflowBuilder — Hook de estado para el Visual Workflow Builder.
 */

export const initialState = {
  workflowId: null,
  botId: null,
  workflowMetadata: {
    name: '',
    description: '',
    status: 'draft',
    trigger: 'manual',
    entry_node_id: null,
    meta: {},
  },
  loading: false,
  serverError: null,

  nodes: [],
  transitions: [],
  dirty: false,
  saving: false,
  saveError: null,
  validationErrors: [],

  selectedNodeId: null,
  selectedTransitionId: null,

  past: [],
  future: [],
};

export function reducer(state, action) {
  switch (action.type) {
    case 'LOAD_START':
      return { ...state, loading: true, serverError: null };

    case 'LOAD_SUCCESS': {
      const { workflowId, botId, metadata, nodes, transitions } = action.payload;
      return {
        ...state,
        loading: false,
        serverError: null,
        workflowId,
        botId,
        workflowMetadata: metadata,
        nodes,
        transitions,
        dirty: false,
        past: [],
        future: [],
      };
    }

    case 'LOAD_ERROR':
      return { ...state, loading: false, serverError: action.payload };

    case 'RESET':
      return { ...initialState };

    case 'UPDATE_METADATA':
      return {
        ...snapshot(state),
        workflowMetadata: { ...state.workflowMetadata, ...action.payload },
        dirty: true,
      };

    case 'ADD_NODE': {
      const node = action.payload;
      if (state.nodes.some(n => n.node_id === node.node_id)) {
        return {
          ...state,
          validationErrors: [
            ...state.validationErrors.filter(e => e.field !== 'node_id'),
            { field: 'node_id', message: `node_id duplicado: '${node.node_id}'` },
          ],
        };
      }
      return {
        ...snapshot(state),
        nodes: [...state.nodes, node],
        dirty: true,
      };
    }

    case 'UPDATE_NODE':
      return {
        ...snapshot(state),
        nodes: state.nodes.map(n =>
          n.node_id === action.payload.nodeId
            ? { ...n, ...action.payload.patch }
            : n
        ),
        dirty: true,
      };

    case 'DELETE_NODE': {
      const nodeId = action.payload.nodeId;
      return {
        ...snapshot(state),
        nodes: state.nodes.filter(n => n.node_id !== nodeId),
        transitions: state.transitions.filter(
          t => t.from_node_id !== nodeId && t.to_node_id !== nodeId
        ),
        selectedNodeId: state.selectedNodeId === nodeId ? null : state.selectedNodeId,
        dirty: true,
      };
    }

    case 'MOVE_NODE':
      return {
        ...state,
        nodes: state.nodes.map(n =>
          n.node_id === action.payload.nodeId
            ? { ...n, position: action.payload.position }
            : n
        ),
      };

    case 'MOVE_NODE_DIRTY':
      return {
        ...snapshot(state),
        nodes: state.nodes.map(n =>
          n.node_id === action.payload.nodeId
            ? { ...n, position: action.payload.position }
            : n
        ),
        dirty: true,
      };

    case 'ADD_TRANSITION': {
      const t = action.payload;
      const exists = state.transitions.some(
        x => x.from_node_id === t.from_node_id && x.to_node_id === t.to_node_id
      );
      if (exists) return state;
      if (t.from_node_id === t.to_node_id) return state;

      return {
        ...snapshot(state),
        transitions: [...state.transitions, t],
        dirty: true,
      };
    }

    case 'UPDATE_TRANSITION':
      return {
        ...snapshot(state),
        transitions: state.transitions.map(t =>
          t.from_node_id === action.payload.from &&
          t.to_node_id === action.payload.to
            ? { ...t, ...action.payload.patch }
            : t
        ),
        dirty: true,
      };

    case 'DELETE_TRANSITION': {
      const { from, to } = action.payload;
      return {
        ...snapshot(state),
        transitions: state.transitions.filter(
          t => !(t.from_node_id === from && t.to_node_id === to)
        ),
        dirty: true,
      };
    }

    case 'SELECT_NODE':
      return { ...state, selectedNodeId: action.payload, selectedTransitionId: null };

    case 'SELECT_TRANSITION':
      return { ...state, selectedTransitionId: action.payload, selectedNodeId: null };

    case 'CLEAR_SELECTION':
      return { ...state, selectedNodeId: null, selectedTransitionId: null };

    case 'SAVE_START':
      return { ...state, saving: true, saveError: null };

    case 'SAVE_SUCCESS':
      return { ...state, saving: false, dirty: false, saveError: null };

    case 'SAVE_ERROR':
      return { ...state, saving: false, saveError: action.payload };

    case 'SET_VALIDATION_ERRORS':
      return { ...state, validationErrors: action.payload };

    case 'UNDO': {
      if (state.past.length === 0) return state;
      const previous = state.past[state.past.length - 1];
      const newPast = state.past.slice(0, -1);
      const currentSnapshot = makeSnapshot(state);
      return {
        ...state,
        nodes: previous.nodes,
        transitions: previous.transitions,
        workflowMetadata: previous.workflowMetadata,
        past: newPast,
        future: [currentSnapshot, ...state.future],
        dirty: true,
      };
    }

    case 'REDO': {
      if (state.future.length === 0) return state;
      const next = state.future[0];
      const newFuture = state.future.slice(1);
      const currentSnapshot = makeSnapshot(state);
      return {
        ...state,
        nodes: next.nodes,
        transitions: next.transitions,
        workflowMetadata: next.workflowMetadata,
        past: [...state.past, currentSnapshot],
        future: newFuture,
        dirty: true,
      };
    }

    default:
      return state;
  }
}

const MAX_HISTORY = 50;

function makeSnapshot(state) {
  return {
    nodes: JSON.parse(JSON.stringify(state.nodes)),
    transitions: JSON.parse(JSON.stringify(state.transitions)),
    workflowMetadata: JSON.parse(JSON.stringify(state.workflowMetadata)),
  };
}

function snapshot(state) {
  const newPast = [...state.past, makeSnapshot(state)];
  const trimmed = newPast.length > MAX_HISTORY
    ? newPast.slice(newPast.length - MAX_HISTORY)
    : newPast;
  return {
    ...state,
    past: trimmed,
    future: [],
  };
}

export function useWorkflowBuilder() {
  const [state, dispatch] = useReducer(reducer, initialState);

  const actions = useMemo(() => ({
    loadStart: () => dispatch({ type: 'LOAD_START' }),
    loadSuccess: (payload) => dispatch({ type: 'LOAD_SUCCESS', payload }),
    loadError: (error) => dispatch({ type: 'LOAD_ERROR', payload: error }),
    reset: () => dispatch({ type: 'RESET' }),

    updateMetadata: (patch) => dispatch({ type: 'UPDATE_METADATA', payload: patch }),

    addNode: (node) => dispatch({ type: 'ADD_NODE', payload: node }),
    updateNode: (nodeId, patch) => dispatch({ type: 'UPDATE_NODE', payload: { nodeId, patch } }),
    deleteNode: (nodeId) => dispatch({ type: 'DELETE_NODE', payload: { nodeId } }),
    moveNode: (nodeId, position) => dispatch({ type: 'MOVE_NODE', payload: { nodeId, position } }),
    moveNodeDirty: (nodeId, position) => dispatch({ type: 'MOVE_NODE_DIRTY', payload: { nodeId, position } }),

    addTransition: (t) => dispatch({ type: 'ADD_TRANSITION', payload: t }),
    updateTransition: (from, to, patch) =>
      dispatch({ type: 'UPDATE_TRANSITION', payload: { from, to, patch } }),
    deleteTransition: (from, to) =>
      dispatch({ type: 'DELETE_TRANSITION', payload: { from, to } }),

    selectNode: (nodeId) => dispatch({ type: 'SELECT_NODE', payload: nodeId }),
    selectTransition: (t) => dispatch({ type: 'SELECT_TRANSITION', payload: t }),
    clearSelection: () => dispatch({ type: 'CLEAR_SELECTION' }),

    saveStart: () => dispatch({ type: 'SAVE_START' }),
    saveSuccess: () => dispatch({ type: 'SAVE_SUCCESS' }),
    saveError: (error) => dispatch({ type: 'SAVE_ERROR', payload: error }),

    setValidationErrors: (errors) => dispatch({ type: 'SET_VALIDATION_ERRORS', payload: errors }),

    undo: () => dispatch({ type: 'UNDO' }),
    redo: () => dispatch({ type: 'REDO' }),
  }), []);

  const selectedNode = useMemo(
    () => state.nodes.find(n => n.node_id === state.selectedNodeId) || null,
    [state.nodes, state.selectedNodeId]
  );

  const canUndo = state.past.length > 0;
  const canRedo = state.future.length > 0;

  const buildSavePayload = useCallback(() => {
    const positions = {};
    state.nodes.forEach(n => {
      if (n.position) {
        positions[n.node_id] = n.position;
      }
    });

    return {
      name: state.workflowMetadata.name,
      description: state.workflowMetadata.description,
      status: state.workflowMetadata.status,
      trigger: state.workflowMetadata.trigger,
      entry_node_id: state.workflowMetadata.entry_node_id,
      meta: {
        ...(state.workflowMetadata.meta || {}),
        positions,
      },
      nodes: state.nodes.map(n => ({
        node_id: n.node_id,
        type: n.type,
        name: n.name || null,
        config: n.config || null,
      })),
      transitions: state.transitions.map(t => ({
        from_node_id: t.from_node_id,
        to_node_id: t.to_node_id,
        condition: t.condition || null,
        label: t.label || null,
        order: t.order || 0,
      })),
    };
  }, [state.nodes, state.transitions, state.workflowMetadata]);

  return {
    ...state,
    selectedNode,
    canUndo,
    canRedo,
    ...actions,
    buildSavePayload,
  };
}

export default useWorkflowBuilder;
