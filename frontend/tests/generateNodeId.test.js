/**
 * Tests — generateNodeId
 */
import { describe, it, expect } from 'vitest';
import { generateNodeId } from '../src/hooks/useWorkflowBuilder';

describe('generateNodeId', () => {
  it('devuelve "type_1" si no hay nodos', () => {
    expect(generateNodeId('message', [])).toBe('message_1');
  });

  it('incrementa si type_1 ya existe', () => {
    const nodes = [{ node_id: 'message_1' }, { node_id: 'message_2' }];
    expect(generateNodeId('message', nodes)).toBe('message_3');
  });

  it('respeta tipos distintos', () => {
    const nodes = [{ node_id: 'message_1' }, { node_id: 'start_1' }];
    expect(generateNodeId('start', nodes)).toBe('start_2');
    expect(generateNodeId('end', nodes)).toBe('end_1');
  });

  it('rellena huecos si falta un número intermedio', () => {
    const nodes = [{ node_id: 'message_1' }, { node_id: 'message_3' }];
    // El algoritmo busca el primer hueco libre desde 1
    expect(generateNodeId('message', nodes)).toBe('message_2');
  });
});
