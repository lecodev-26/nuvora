/**
 * Tests — useWorkflowBuilder (reducer)
 */
import { describe, it, expect } from 'vitest';
import { reducer, initialState } from '../src/hooks/useWorkflowBuilder';

const sampleWorkflow = {
  workflowId: 1,
  botId: 10,
  metadata: {
    name: 'WF Test',
    description: 'desc',
    status: 'draft',
    trigger: 'manual',
    entry_node_id: null,
    meta: {},
  },
  nodes: [
    { node_id: 's1', type: 'start', name: null, config: null, position: { x: 0, y: 0 } },
    { node_id: 'm1', type: 'message', name: 'Saludo', config: { text: 'Hola' }, position: { x: 200, y: 0 } },
    { node_id: 'e1', type: 'end', name: null, config: null, position: { x: 400, y: 0 } },
  ],
  transitions: [
    { from_node_id: 's1', to_node_id: 'm1', condition: null, label: null, order: 0 },
    { from_node_id: 'm1', to_node_id: 'e1', condition: null, label: null, order: 0 },
  ],
};

describe('useWorkflowBuilder reducer', () => {
  describe('LOAD_SUCCESS', () => {
    it('carga workflowId, botId, nodes, transitions', () => {
      const state = reducer(initialState, { type: 'LOAD_SUCCESS', payload: sampleWorkflow });
      expect(state.workflowId).toBe(1);
      expect(state.botId).toBe(10);
      expect(state.nodes).toHaveLength(3);
      expect(state.transitions).toHaveLength(2);
      expect(state.dirty).toBe(false);
      expect(state.loading).toBe(false);
    });
  });

  describe('ADD_NODE', () => {
    it('añade un nodo y marca dirty', () => {
      let state = reducer(initialState, { type: 'LOAD_SUCCESS', payload: sampleWorkflow });
      state = reducer(state, {
        type: 'ADD_NODE',
        payload: { node_id: 'q1', type: 'question', config: {}, position: { x: 0, y: 200 } },
      });
      expect(state.nodes).toHaveLength(4);
      expect(state.dirty).toBe(true);
      expect(state.past).toHaveLength(1);
    });

    it('rechaza node_id duplicado', () => {
      let state = reducer(initialState, { type: 'LOAD_SUCCESS', payload: sampleWorkflow });
      state = reducer(state, {
        type: 'ADD_NODE',
        payload: { node_id: 'm1', type: 'message', config: {} },
      });
      expect(state.nodes).toHaveLength(3);
      expect(state.validationErrors.some((e) => e.field === 'node_id')).toBe(true);
    });
  });

  describe('UPDATE_NODE', () => {
    it('actualiza name del nodo', () => {
      let state = reducer(initialState, { type: 'LOAD_SUCCESS', payload: sampleWorkflow });
      state = reducer(state, {
        type: 'UPDATE_NODE',
        payload: { nodeId: 'm1', patch: { name: 'Nuevo' } },
      });
      expect(state.nodes.find((n) => n.node_id === 'm1').name).toBe('Nuevo');
      expect(state.dirty).toBe(true);
    });
  });

  describe('DELETE_NODE', () => {
    it('borra nodo y sus transiciones huérfanas', () => {
      let state = reducer(initialState, { type: 'LOAD_SUCCESS', payload: sampleWorkflow });
      state = reducer(state, { type: 'DELETE_NODE', payload: { nodeId: 'm1' } });
      expect(state.nodes.some((n) => n.node_id === 'm1')).toBe(false);
      expect(state.transitions.some((t) => t.from_node_id === 'm1' || t.to_node_id === 'm1')).toBe(false);
    });
  });

  describe('ADD_TRANSITION', () => {
    it('añade transición nueva', () => {
      let state = reducer(initialState, { type: 'LOAD_SUCCESS', payload: sampleWorkflow });
      const before = state.transitions.length;
      state = reducer(state, {
        type: 'ADD_TRANSITION',
        payload: { from_node_id: 's1', to_node_id: 'e1' },
      });
      expect(state.transitions.length).toBe(before + 1);
    });

    it('ignora transición duplicada', () => {
      let state = reducer(initialState, { type: 'LOAD_SUCCESS', payload: sampleWorkflow });
      const before = state.transitions.length;
      state = reducer(state, {
        type: 'ADD_TRANSITION',
        payload: { from_node_id: 's1', to_node_id: 'm1' },
      });
      expect(state.transitions.length).toBe(before);
    });

    it('ignora auto-conexión', () => {
      let state = reducer(initialState, { type: 'LOAD_SUCCESS', payload: sampleWorkflow });
      const before = state.transitions.length;
      state = reducer(state, {
        type: 'ADD_TRANSITION',
        payload: { from_node_id: 'm1', to_node_id: 'm1' },
      });
      expect(state.transitions.length).toBe(before);
    });
  });

  describe('SELECT_NODE', () => {
    it('actualiza selectedNodeId y limpia edge', () => {
      let state = reducer(initialState, { type: 'SELECT_NODE', payload: 'm1' });
      expect(state.selectedNodeId).toBe('m1');
      expect(state.selectedTransitionId).toBe(null);
    });
  });

  describe('UNDO / REDO', () => {
    it('deshace y rehace una acción', () => {
      let state = reducer(initialState, { type: 'LOAD_SUCCESS', payload: sampleWorkflow });
      state = reducer(state, {
        type: 'ADD_NODE',
        payload: { node_id: 'x1', type: 'message', config: {} },
      });
      expect(state.nodes).toHaveLength(4);

      state = reducer(state, { type: 'UNDO' });
      expect(state.nodes).toHaveLength(3);
      expect(state.future.length).toBeGreaterThan(0);

      state = reducer(state, { type: 'REDO' });
      expect(state.nodes).toHaveLength(4);
    });

    it('no hace nada si no hay historia', () => {
      const state = reducer(initialState, { type: 'UNDO' });
      expect(state.nodes).toHaveLength(0);
    });
  });

  describe('SAVE_START / SAVE_SUCCESS / SAVE_ERROR', () => {
    it('saving=true en start, dirty=false en success', () => {
      let state = reducer(initialState, { type: 'SAVE_START' });
      expect(state.saving).toBe(true);

      state = reducer(state, { type: 'SAVE_SUCCESS' });
      expect(state.saving).toBe(false);
      expect(state.dirty).toBe(false);
    });

    it('saveError en error', () => {
      let state = reducer(initialState, { type: 'SAVE_ERROR', payload: 'fail' });
      expect(state.saveError).toBe('fail');
    });
  });

  describe('MOVE_NODE vs MOVE_NODE_DIRTY', () => {
    it('MOVE_NODE no marca dirty', () => {
      let state = reducer(initialState, { type: 'LOAD_SUCCESS', payload: sampleWorkflow });
      state = reducer(state, {
        type: 'MOVE_NODE',
        payload: { nodeId: 's1', position: { x: 99, y: 99 } },
      });
      expect(state.dirty).toBe(false);
      expect(state.nodes.find((n) => n.node_id === 's1').position).toEqual({ x: 99, y: 99 });
    });

    it('MOVE_NODE_DIRTY sí marca dirty', () => {
      let state = reducer(initialState, { type: 'LOAD_SUCCESS', payload: sampleWorkflow });
      state = reducer(state, {
        type: 'MOVE_NODE_DIRTY',
        payload: { nodeId: 's1', position: { x: 1, y: 2 } },
      });
      expect(state.dirty).toBe(true);
    });
  });

  describe('RESET', () => {
    it('vuelve al estado inicial', () => {
      let state = reducer(initialState, { type: 'LOAD_SUCCESS', payload: sampleWorkflow });
      state = reducer(state, { type: 'RESET' });
      expect(state.workflowId).toBe(null);
      expect(state.nodes).toHaveLength(0);
    });
  });

  describe('MAX_HISTORY', () => {
    it('limita el past a 50 entradas', () => {
      let state = initialState;
      for (let i = 0; i < 100; i++) {
        state = reducer(state, {
          type: 'ADD_NODE',
          payload: { node_id: `n${i}`, type: 'message', config: {} },
        });
      }
      expect(state.past.length).toBeLessThanOrEqual(50);
      expect(state.nodes).toHaveLength(100);
    });
  });
});
