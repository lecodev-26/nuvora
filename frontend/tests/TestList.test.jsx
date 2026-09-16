/**
 * Tests — TestList (14.8.14)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import TestList from '../src/components/tester/TestList';

describe('TestList', () => {
  const baseTest = {
    id: 1,
    workflow_id: 10,
    bot_id: 5,
    name: 'Test saludo',
    description: 'Verifica que el bot saluda',
    input_messages: ['Hola', '¿Qué tal?'],
    initial_variables: {},
    assertions: [
      { type: 'response_contains', value: 'Hola' },
      { type: 'reaches_end' },
    ],
    enabled: true,
    created_at: '2026-01-01T00:00:00Z',
  };

  describe('Estado vacío', () => {
    it('muestra mensaje cuando no hay tests', () => {
      render(<TestList tests={[]} />);
      expect(screen.getByText(/Aún no hay tests/i)).toBeInTheDocument();
    });
  });

  describe('Estado cargando', () => {
    it('muestra "Cargando tests..." cuando loading=true', () => {
      render(<TestList tests={[]} loading={true} />);
      expect(screen.getByText(/Cargando tests/i)).toBeInTheDocument();
    });
  });

  describe('Con tests', () => {
    it('renderiza el nombre del test', () => {
      render(<TestList tests={[baseTest]} />);
      expect(screen.getByText('Test saludo')).toBeInTheDocument();
    });

    it('renderiza el número de mensajes y assertions', () => {
      render(<TestList tests={[baseTest]} />);
      expect(screen.getByText(/2 mensajes/i)).toBeInTheDocument();
      expect(screen.getByText(/2 assertions/i)).toBeInTheDocument();
    });

    it('renderiza el botón de ejecutar (▶)', () => {
      render(<TestList tests={[baseTest]} />);
      expect(screen.getByTitle('Ejecutar test')).toBeInTheDocument();
    });

    it('renderiza el botón de editar (✎)', () => {
      render(<TestList tests={[baseTest]} />);
      expect(screen.getByTitle('Editar')).toBeInTheDocument();
    });

    it('renderiza el botón de eliminar (🗑)', () => {
      render(<TestList tests={[baseTest]} />);
      expect(screen.getByTitle('Eliminar')).toBeInTheDocument();
    });

    it('el checkbox refleja enabled=true', () => {
      render(<TestList tests={[baseTest]} />);
      const checkbox = screen.getByTitle('Deshabilitar test');
      expect(checkbox).toBeChecked();
    });

    it('el checkbox refleja enabled=false', () => {
      const disabled = { ...baseTest, enabled: false };
      render(<TestList tests={[disabled]} />);
      const checkbox = screen.getByTitle('Habilitar test');
      expect(checkbox).not.toBeChecked();
    });
  });

  describe('Handlers', () => {
    it('onRun se llama con testId al click ▶', () => {
      const onRun = vi.fn();
      render(<TestList tests={[baseTest]} onRun={onRun} />);
      fireEvent.click(screen.getByTitle('Ejecutar test'));
      expect(onRun).toHaveBeenCalledWith(1);
    });

    it('onEdit se llama con testId al click ✎', () => {
      const onEdit = vi.fn();
      render(<TestList tests={[baseTest]} onEdit={onEdit} />);
      fireEvent.click(screen.getByTitle('Editar'));
      expect(onEdit).toHaveBeenCalledWith(1);
    });

    it('onDelete se llama con testId al click 🗑', () => {
      const onDelete = vi.fn();
      render(<TestList tests={[baseTest]} onDelete={onDelete} />);
      fireEvent.click(screen.getByTitle('Eliminar'));
      expect(onDelete).toHaveBeenCalledWith(1);
    });

    it('onToggleEnabled se llama al cambiar el checkbox', () => {
      const onToggleEnabled = vi.fn();
      render(<TestList tests={[baseTest]} onToggleEnabled={onToggleEnabled} />);
      fireEvent.click(screen.getByTitle('Deshabilitar test'));
      expect(onToggleEnabled).toHaveBeenCalledWith(1);
    });
  });

  describe('Expansión', () => {
    it('al hacer click en el nombre expande los detalles', () => {
      render(<TestList tests={[baseTest]} />);
      // Inicialmente no se muestra la descripción
      expect(screen.queryByText(/Verifica que el bot saluda/i)).not.toBeInTheDocument();

      // Click en el nombre
      fireEvent.click(screen.getByText('Test saludo'));

      // Ahora sí se muestra
      expect(screen.getByText(/Verifica que el bot saluda/i)).toBeInTheDocument();
    });

    it('muestra las assertions al expandir', () => {
      render(<TestList tests={[baseTest]} />);
      fireEvent.click(screen.getByText('Test saludo'));
      expect(screen.getByText('response_contains')).toBeInTheDocument();
      expect(screen.getByText('reaches_end')).toBeInTheDocument();
    });
  });

  describe('Con resultado', () => {
    it('muestra badge PASSED si lastResults tiene status=passed', () => {
      const results = { 1: { status: 'passed', assertions_passed: 2, assertions_failed: 0, steps_used: 3, duration_ms: 10 } };
      render(<TestList tests={[baseTest]} lastResults={results} />);
      expect(screen.getByText(/PASSED/i)).toBeInTheDocument();
    });

    it('muestra badge FAILED si status=failed', () => {
      const results = { 1: { status: 'failed', assertions_passed: 1, assertions_failed: 1, steps_used: 3, duration_ms: 10 } };
      render(<TestList tests={[baseTest]} lastResults={results} />);
      expect(screen.getByText(/FAILED/i)).toBeInTheDocument();
    });

    it('muestra badge ERROR si status=error', () => {
      const results = { 1: { status: 'error', error: 'MaxStepsExceeded', assertions_passed: 0, assertions_failed: 0, steps_used: 5, duration_ms: 10 } };
      render(<TestList tests={[baseTest]} lastResults={results} />);
      expect(screen.getByText(/ERROR/i)).toBeInTheDocument();
    });
  });
});
