/**
 * Tests — TraceView (14.8.14)
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import TraceView from '../src/components/tester/TraceView';

describe('TraceView', () => {
  describe('Sin trace', () => {
    it('muestra mensaje cuando trace está vacío', () => {
      render(<TraceView trace={[]} />);
      expect(screen.getByText(/Sin trace de ejecución/i)).toBeInTheDocument();
    });

    it('muestra mensaje cuando trace es undefined', () => {
      render(<TraceView />);
      expect(screen.getByText(/Sin trace de ejecución/i)).toBeInTheDocument();
    });
  });

  describe('Con trace', () => {
    const trace = [
      { step: 1, node_id: 's1', type: 'start', output: null },
      { step: 2, node_id: 'm1', type: 'message', output: 'Hola' },
      { step: 3, node_id: 'e1', type: 'end', output: null },
    ];

    it('renderiza los 3 pasos', () => {
      render(<TraceView trace={trace} />);
      expect(screen.getByText('s1')).toBeInTheDocument();
      expect(screen.getByText('m1')).toBeInTheDocument();
      expect(screen.getByText('e1')).toBeInTheDocument();
    });

    it('renderiza los números de step', () => {
      render(<TraceView trace={trace} />);
      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
    });

    it('renderiza los tipos de nodo', () => {
      render(<TraceView trace={trace} />);
      expect(screen.getByText('start')).toBeInTheDocument();
      expect(screen.getByText('message')).toBeInTheDocument();
      expect(screen.getByText('end')).toBeInTheDocument();
    });

    it('renderiza el output del nodo message', () => {
      render(<TraceView trace={trace} />);
      expect(screen.getByText('Hola')).toBeInTheDocument();
    });

    it('renderiza iconos por tipo de nodo', () => {
      render(<TraceView trace={trace} />);
      // Iconos: start=▶, message=💬, end=■
      expect(screen.getByText('▶')).toBeInTheDocument();
      expect(screen.getByText('💬')).toBeInTheDocument();
      expect(screen.getByText('■')).toBeInTheDocument();
    });
  });

  describe('Con assertionResults', () => {
    const trace = [
      { step: 1, node_id: 's1', type: 'start', output: null },
    ];

    it('muestra sección "Assertions" si hay assertionResults', () => {
      const ar = [
        { type: 'response_contains', passed: true, expected: 'Hola', actual: 'Hola' },
      ];
      render(<TraceView trace={trace} assertionResults={ar} />);
      expect(screen.getByText('Assertions')).toBeInTheDocument();
    });

    it('muestra ✅ para assertion passed', () => {
      const ar = [{ type: 'reaches_end', passed: true }];
      render(<TraceView trace={trace} assertionResults={ar} />);
      expect(screen.getByText('✅')).toBeInTheDocument();
    });

    it('muestra ❌ para assertion failed', () => {
      const ar = [{ type: 'reaches_end', passed: false, message: 'No llegó' }];
      render(<TraceView trace={trace} assertionResults={ar} />);
      expect(screen.getByText('❌')).toBeInTheDocument();
      expect(screen.getByText('No llegó')).toBeInTheDocument();
    });

    it('no muestra sección Assertions si assertionResults está vacío', () => {
      render(<TraceView trace={trace} assertionResults={[]} />);
      expect(screen.queryByText('Assertions')).not.toBeInTheDocument();
    });
  });
});
