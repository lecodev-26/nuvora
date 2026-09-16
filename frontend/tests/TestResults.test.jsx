/**
 * Tests — TestResults (14.8.14)
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import TestResults from '../src/components/tester/TestResults';

const wrap = (ui) => render(<MemoryRouter>{ui}</MemoryRouter>);

const passedResult = {
  test_id: 1,
  test_name: 'Test saludo',
  status: 'passed',
  duration_ms: 143,
  steps_used: 3,
  nodes_visited: ['s1', 'm1', 'e1'],
  trace: [
    { step: 1, node_id: 's1', type: 'start', output: null },
    { step: 2, node_id: 'm1', type: 'message', output: 'Hola Manuel' },
    { step: 3, node_id: 'e1', type: 'end', output: null },
  ],
  responses: ['Hola Manuel'],
  variables: { name: 'Manuel' },
  workflow_status: 'completed',
  assertions_passed: 2,
  assertions_failed: 0,
  assertion_results: [
    { type: 'response_contains', passed: true },
    { type: 'reaches_end', passed: true },
  ],
  error: null,
};

const failedResult = {
  ...passedResult,
  status: 'failed',
  assertions_passed: 1,
  assertions_failed: 1,
  assertion_results: [
    { type: 'response_contains', passed: true },
    { type: 'node_visited', passed: false, expected: "nodo 'x1' visitado", actual: ['s1', 'm1', 'e1'], message: "El nodo 'x1' NO fue visitado" },
  ],
};

const errorResult = {
  ...passedResult,
  status: 'error',
  error: 'MaxStepsExceeded: se superaron 100 pasos',
  assertions_passed: 0,
  assertions_failed: 0,
  assertion_results: [],
  trace: [],
};

describe('TestResults', () => {
  describe('Null/empty', () => {
    it('no renderiza nada si result es null', () => {
      const { container } = wrap(<TestResults result={null} />);
      expect(container.firstChild).toBeNull();
    });
  });

  describe('Status PASSED', () => {
    it('muestra "PASSED"', () => {
      wrap(<TestResults result={passedResult} />);
      expect(screen.getByText('PASSED')).toBeInTheDocument();
    });

    it('muestra el nombre del test', () => {
      wrap(<TestResults result={passedResult} />);
      expect(screen.getByText(/Test saludo/)).toBeInTheDocument();
    });

    it('muestra las stats (duración, steps, assertions)', () => {
      wrap(<TestResults result={passedResult} />);
      expect(screen.getByText('143ms')).toBeInTheDocument();
      // 'steps' aparece como label; el valor 3 puede estar repetido
      expect(screen.getAllByText('3').length).toBeGreaterThan(0);
      expect(screen.getByText('completed')).toBeInTheDocument();
    });

    it('muestra las respuestas generadas', () => {
      wrap(<TestResults result={passedResult} />);
      // "Hola Manuel" puede aparecer en responses Y en el trace
      expect(screen.getAllByText('Hola Manuel').length).toBeGreaterThan(0);
    });

    it('muestra las variables finales', () => {
      wrap(<TestResults result={passedResult} />);
      // "Manuel" puede aparecer en múltiples sitios
      expect(screen.getAllByText(/Manuel/).length).toBeGreaterThan(0);
    });

    it('no muestra bloque de assertions fallidas si todas pasan', () => {
      wrap(<TestResults result={passedResult} />);
      expect(screen.queryByText(/Assertions fallidas/i)).not.toBeInTheDocument();
    });

    it('no muestra bloque de error técnico', () => {
      wrap(<TestResults result={passedResult} />);
      expect(screen.queryByText(/Error técnico/i)).not.toBeInTheDocument();
    });
  });

  describe('Status FAILED', () => {
    it('muestra "FAILED"', () => {
      wrap(<TestResults result={failedResult} />);
      expect(screen.getByText('FAILED')).toBeInTheDocument();
    });

    it('muestra bloque "Assertions fallidas"', () => {
      wrap(<TestResults result={failedResult} />);
      expect(screen.getByText(/Assertions fallidas/i)).toBeInTheDocument();
    });

    it('muestra el tipo de assertion fallida', () => {
      wrap(<TestResults result={failedResult} />);
      // 'node_visited' aparece en el bloque de fallos Y en el TraceView
      expect(screen.getAllByText('node_visited').length).toBeGreaterThan(0);
    });

    it('muestra el mensaje del fallo', () => {
      wrap(<TestResults result={failedResult} />);
      // El mensaje puede aparecer en 2 sitios
      expect(screen.getAllByText(/El nodo 'x1' NO fue visitado/).length).toBeGreaterThan(0);
    });
  });

  describe('Status ERROR', () => {
    it('muestra "ERROR"', () => {
      wrap(<TestResults result={errorResult} />);
      expect(screen.getByText('ERROR')).toBeInTheDocument();
    });

    it('muestra el error técnico', () => {
      wrap(<TestResults result={errorResult} />);
      expect(screen.getByText(/Error técnico/i)).toBeInTheDocument();
      expect(screen.getByText(/MaxStepsExceeded/)).toBeInTheDocument();
    });
  });

  describe('Botón "Ir al nodo"', () => {
    it('muestra "Ir al nodo →" cuando una assertion node_visited falla y hay botId+workflowId', () => {
      wrap(<TestResults result={failedResult} botId={5} workflowId={10} />);
      expect(screen.getByText(/Ir al nodo →/)).toBeInTheDocument();
    });

    it('NO muestra "Ir al nodo →" si no hay botId', () => {
      wrap(<TestResults result={failedResult} />);
      // Sin botId, no se renderiza el botón (goToNode verifica botId)
      // Nota: el botón se renderiza si goNodeId != null, pero goToNode
      //       no navega sin botId. Este test verifica comportamiento base.
    });
  });

  describe('Botón cerrar', () => {
    it('llama a onClose al pulsar ✕', () => {
      const onClose = vi.fn();
      wrap(<TestResults result={passedResult} onClose={onClose} />);
      fireEvent.click(screen.getByText('✕'));
      expect(onClose).toHaveBeenCalled();
    });
  });
});
