/**
 * Tests manuales del reducer de useWorkflowBuilder.
 * Se ejecutan con Node (sin Vitest todavía).
 *
 * Uso: node tests/useWorkflowBuilder.test.mjs
 */

import { reducer, initialState } from '../src/hooks/useWorkflowBuilder.js';

// ============================================================
// MINI FRAMEWORK
// ============================================================

let testsPassed = 0;
let testsFailed = 0;

function test(name, fn) {
  try {
    fn();
    console.log(`  ✅ ${name}`);
    testsPassed++;
  } catch (e) {
    console.log(`  ❌ ${name}`);
    console.log(`     ${e.message}`);
    testsFailed++;
  }
}

function assert(condition, msg) {
  if (!condition) throw new Error(msg || 'Assertion failed');
}

function assertEqual(a, b, msg) {
  if (a !== b) throw new Error(`${msg || 'No iguales'}: ${a} !== ${b}`);
}

function assertDeepEqual(a, b, msg) {
  const sa = JSON.stringify(a);
  const sb = JSON.stringify(b);
  if (sa !== sb) throw new Error(`${msg || 'No iguales'}:\n  A: ${sa}\n  B: ${sb}`);
}

// ============================================================
// SETUP
// ============================================================

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

let state;

// ============================================================
// TESTS
// ============================================================

console.log('═══════════════════════════════════════════════════════════════');
console.log('  TESTS — useWorkflowBuilder reducer');
console.log('═══════════════════════════════════════════════════════════════');

console.log('\n[1] LOAD_SUCCESS');
state = reducer(initialState, { type: 'LOAD_SUCCESS', payload: sampleWorkflow });
test('workflowId y botId cargados', () => {
  assertEqual(state.workflowId, 1);
  assertEqual(state.botId, 10);
});
test('nodes cargados (3)', () => assertEqual(state.nodes.length, 3));
test('transitions cargadas (2)', () => assertEqual(state.transitions.length, 2));
test('dirty = false', () => assertEqual(state.dirty, false));
test('loading = false', () => assertEqual(state.loading, false));

console.log('\n[2] ADD_NODE');
state = reducer(state, {
  type: 'ADD_NODE',
  payload: { node_id: 'q1', type: 'question', config: { text: '¿?', variable: 'x' }, position: { x: 0, y: 200 } },
});
test('nodes = 4', () => assertEqual(state.nodes.length, 4));
test('dirty = true', () => assertEqual(state.dirty, true));
test('past tiene 1 snapshot', () => assertEqual(state.past.length, 1));

console.log('\n[3] ADD_NODE duplicado');
const beforeDup = state.nodes.length;
state = reducer(state, {
  type: 'ADD_NODE',
  payload: { node_id: 'q1', type: 'question', config: {} },
});
test('nodes NO cambia', () => assertEqual(state.nodes.length, beforeDup));
test('validationErrors tiene node_id duplicado', () => {
  assert(state.validationErrors.some(e => e.field === 'node_id'));
});

console.log('\n[4] UPDATE_NODE');
state = reducer(state, {
  type: 'UPDATE_NODE',
  payload: { nodeId: 'm1', patch: { name: 'Nuevo nombre' } },
});
test('m1.name actualizado', () => {
  const m1 = state.nodes.find(n => n.node_id === 'm1');
  assertEqual(m1.name, 'Nuevo nombre');
});

console.log('\n[5] SELECT_NODE');
state = reducer(state, { type: 'SELECT_NODE', payload: 'm1' });
test('selectedNodeId = m1', () => assertEqual(state.selectedNodeId, 'm1'));
test('selectedTransitionId = null', () => assertEqual(state.selectedTransitionId, null));

console.log('\n[6] ADD_TRANSITION');
const beforeT = state.transitions.length;
state = reducer(state, {
  type: 'ADD_TRANSITION',
  payload: { from_node_id: 'q1', to_node_id: 'e1', condition: null, label: null, order: 0 },
});
test('transitions +1', () => assertEqual(state.transitions.length, beforeT + 1));

console.log('\n[7] ADD_TRANSITION duplicada (no-op)');
const beforeDupT = state.transitions.length;
state = reducer(state, {
  type: 'ADD_TRANSITION',
  payload: { from_node_id: 'q1', to_node_id: 'e1' },
});
test('transitions NO cambian', () => assertEqual(state.transitions.length, beforeDupT));

console.log('\n[8] ADD_TRANSITION auto-conexión (no-op)');
state = reducer(state, {
  type: 'ADD_TRANSITION',
  payload: { from_node_id: 'm1', to_node_id: 'm1' },
});
test('transitions NO cambian', () => assertEqual(state.transitions.length, beforeDupT));

console.log('\n[9] DELETE_NODE (elimina transiciones huérfanas)');
const transitionsBefore = state.transitions.length;
state = reducer(state, { type: 'DELETE_NODE', payload: { nodeId: 'm1' } });
test('nodes sin m1', () => assert(!state.nodes.some(n => n.node_id === 'm1')));
test('transiciones huérfanas eliminadas', () => {
  assert(!state.transitions.some(t => t.from_node_id === 'm1' || t.to_node_id === 'm1'));
});

console.log('\n[10] UNDO');
const nodesAfterDelete = state.nodes.length;
state = reducer(state, { type: 'UNDO' });
test('nodes restaurados (m1 vuelve)', () => {
  assert(state.nodes.length > nodesAfterDelete);
  assert(state.nodes.some(n => n.node_id === 'm1'));
});
test('canRedo = future.length > 0', () => assert(state.future.length > 0));

console.log('\n[11] REDO');
state = reducer(state, { type: 'REDO' });
test('nodes vuelven a estado post-delete', () => {
  assert(!state.nodes.some(n => n.node_id === 'm1'));
});

console.log('\n[12] UPDATE_METADATA');
state = reducer(state, { type: 'UPDATE_METADATA', payload: { name: 'Nuevo nombre WF' } });
test('name actualizado', () => assertEqual(state.workflowMetadata.name, 'Nuevo nombre WF'));
test('dirty = true', () => assertEqual(state.dirty, true));

console.log('\n[13] SAVE_START / SAVE_SUCCESS');
state = reducer(state, { type: 'SAVE_START' });
test('saving = true', () => assertEqual(state.saving, true));
state = reducer(state, { type: 'SAVE_SUCCESS' });
test('saving = false, dirty = false', () => {
  assertEqual(state.saving, false);
  assertEqual(state.dirty, false);
});

console.log('\n[14] SAVE_ERROR');
state = reducer(state, { type: 'SAVE_ERROR', payload: 'Falló' });
test('saveError = "Falló"', () => assertEqual(state.saveError, 'Falló'));

console.log('\n[15] MOVE_NODE (no dirty)');
const dirtyBefore = state.dirty;
state = reducer(state, {
  type: 'MOVE_NODE',
  payload: { nodeId: 's1', position: { x: 999, y: 999 } },
});
test('posición actualizada', () => {
  const s1 = state.nodes.find(n => n.node_id === 's1');
  assertDeepEqual(s1.position, { x: 999, y: 999 });
});
test('dirty NO cambia con MOVE_NODE', () => assertEqual(state.dirty, dirtyBefore));

console.log('\n[16] MOVE_NODE_DIRTY (sí dirty)');
state = reducer(state, { type: 'SAVE_SUCCESS' }); // reset dirty
state = reducer(state, {
  type: 'MOVE_NODE_DIRTY',
  payload: { nodeId: 's1', position: { x: 111, y: 222 } },
});
test('dirty = true con MOVE_NODE_DIRTY', () => assertEqual(state.dirty, true));

console.log('\n[17] RESET');
state = reducer(state, { type: 'RESET' });
test('estado = initialState', () => {
  assertEqual(state.workflowId, null);
  assertEqual(state.nodes.length, 0);
  assertEqual(state.transitions.length, 0);
  assertEqual(state.dirty, false);
});

console.log('\n[18] UNDO sin historia (no-op)');
const stateEmpty = reducer(initialState, { type: 'UNDO' });
test('UNDO sin historia devuelve el mismo estado', () => {
  assertEqual(stateEmpty.nodes.length, 0);
});

console.log('\n[19] REDO sin futuro (no-op)');
const stateNoFuture = reducer(initialState, { type: 'REDO' });
test('REDO sin futuro devuelve el mismo estado', () => {
  assertEqual(stateNoFuture.nodes.length, 0);
});

console.log('\n[20] MAX_HISTORY (límite de 50)');
let stateHist = initialState;
for (let i = 0; i < 100; i++) {
  stateHist = reducer(stateHist, {
    type: 'ADD_NODE',
    payload: { node_id: `n${i}`, type: 'message', config: { text: `t${i}` } },
  });
}
test('past <= 50', () => {
  assert(stateHist.past.length <= 50, `past tiene ${stateHist.past.length}`);
});
test('nodes = 100', () => assertEqual(stateHist.nodes.length, 100));

// ============================================================
// RESULTADO
// ============================================================

console.log('\n═══════════════════════════════════════════════════════════════');
console.log(`  RESULTADO: ${testsPassed} pasados, ${testsFailed} fallidos`);
console.log('═══════════════════════════════════════════════════════════════');

if (testsFailed > 0) {
  process.exit(1);
}
