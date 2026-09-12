/**
 * Tests — workflowValidation
 */
import { describe, it, expect } from 'vitest';
import { validateWorkflow, basicValidateCondition, getErrorNodeIds } from '../src/utils/workflowValidation';

const emptyMeta = { name: 'Test' };

function makeState(nodes, transitions, meta = emptyMeta) {
  return { nodes, transitions, workflowMetadata: meta };
}

describe('validateWorkflow', () => {
  it('error si no hay name', () => {
    const state = makeState([], [], { name: '' });
    const r = validateWorkflow(state);
    expect(r.errors.some((e) => e.code === 'missing_name')).toBe(true);
  });

  it('error si no hay START', () => {
    const state = makeState(
      [{ node_id: 'e1', type: 'end', config: null }],
      []
    );
    const r = validateWorkflow(state);
    expect(r.errors.some((e) => e.code === 'missing_start')).toBe(true);
  });

  it('error si hay múltiples START', () => {
    const state = makeState(
      [
        { node_id: 's1', type: 'start', config: null },
        { node_id: 's2', type: 'start', config: null },
        { node_id: 'e1', type: 'end', config: null },
      ],
      []
    );
    const r = validateWorkflow(state);
    expect(r.errors.some((e) => e.code === 'multiple_starts')).toBe(true);
  });

  it('error si no hay END', () => {
    const state = makeState([{ node_id: 's1', type: 'start', config: null }], []);
    const r = validateWorkflow(state);
    expect(r.errors.some((e) => e.code === 'missing_end')).toBe(true);
  });

  it('error si hay node_id duplicado', () => {
    const state = makeState(
      [
        { node_id: 's1', type: 'start', config: null },
        { node_id: 's1', type: 'message', config: { text: 'x' } },
        { node_id: 'e1', type: 'end', config: null },
      ],
      []
    );
    const r = validateWorkflow(state);
    expect(r.errors.some((e) => e.code === 'duplicate_node_id')).toBe(true);
  });

  it('error si MESSAGE sin text', () => {
    const state = makeState(
      [
        { node_id: 's1', type: 'start', config: null },
        { node_id: 'm1', type: 'message', config: {} },
        { node_id: 'e1', type: 'end', config: null },
      ],
      []
    );
    const r = validateWorkflow(state);
    expect(r.errors.some((e) => e.code === 'missing_text')).toBe(true);
  });

  it('error si QUESTION sin variable', () => {
    const state = makeState(
      [
        { node_id: 's1', type: 'start', config: null },
        { node_id: 'q1', type: 'question', config: { text: '¿?' } },
        { node_id: 'e1', type: 'end', config: null },
      ],
      []
    );
    const r = validateWorkflow(state);
    expect(r.errors.some((e) => e.code === 'missing_question_variable')).toBe(true);
  });

  it('error si CONDITION sin 2 salidas', () => {
    const state = makeState(
      [
        { node_id: 's1', type: 'start', config: null },
        { node_id: 'c1', type: 'condition', config: { condition: 'age > 18' } },
        { node_id: 'e1', type: 'end', config: null },
      ],
      [
        { from_node_id: 's1', to_node_id: 'c1' },
        { from_node_id: 'c1', to_node_id: 'e1' },
      ]
    );
    const r = validateWorkflow(state);
    expect(r.errors.some((e) => e.code === 'condition_few_outputs')).toBe(true);
  });

  it('warning si hay nodo huérfano', () => {
    const state = makeState(
      [
        { node_id: 's1', type: 'start', config: null },
        { node_id: 'm1', type: 'message', config: { text: 'x' } },
        { node_id: 'e1', type: 'end', config: null },
      ],
      [
        { from_node_id: 's1', to_node_id: 'e1' },
      ]
    );
    const r = validateWorkflow(state);
    expect(r.warnings.some((w) => w.code === 'orphan_node')).toBe(true);
  });

  it('workflow válido completo → sin errores', () => {
    const state = makeState(
      [
        { node_id: 's1', type: 'start', config: null },
        { node_id: 'm1', type: 'message', config: { text: 'Hola' } },
        { node_id: 'e1', type: 'end', config: null },
      ],
      [
        { from_node_id: 's1', to_node_id: 'm1' },
        { from_node_id: 'm1', to_node_id: 'e1' },
      ]
    );
    const r = validateWorkflow(state);
    expect(r.errors).toHaveLength(0);
  });
});

describe('basicValidateCondition', () => {
  it('OK con age > 18', () => {
    expect(basicValidateCondition('age > 18')).toBe(null);
  });

  it('KO con age 18 (sin operador)', () => {
    expect(basicValidateCondition('age 18')).not.toBe(null);
  });

  it('KO vacío', () => {
    expect(basicValidateCondition('')).not.toBe(null);
  });
});

describe('getErrorNodeIds', () => {
  it('devuelve Set con node_ids con error', () => {
    const r = {
      errors: [
        { code: 'x', message: 'x', node_id: 'm1' },
        { code: 'y', message: 'y', node_id: 'q1' },
        { code: 'z', message: 'z' },
      ],
      warnings: [],
    };
    const ids = getErrorNodeIds(r);
    expect(ids.has('m1')).toBe(true);
    expect(ids.has('q1')).toBe(true);
    expect(ids.size).toBe(2);
  });
});
