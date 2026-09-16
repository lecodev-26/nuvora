/**
 * Tests — TestEditor (14.8.14)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import TestEditor from '../src/components/tester/TestEditor';

describe('TestEditor', () => {
  const baseTest = {
    id: 1,
    workflow_id: 10,
    bot_id: 5,
    name: 'Test existente',
    description: 'Descripción original',
    input_messages: ['Hola'],
    initial_variables: { name: 'Manuel' },
    assertions: [{ type: 'reaches_end' }],
    enabled: true,
    created_at: '2026-01-01T00:00:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Modo oculto', () => {
    it('no renderiza nada si open=false', () => {
      const { container } = render(
        <TestEditor open={false} test={null} onSave={vi.fn()} onClose={vi.fn()} />
      );
      expect(container.firstChild).toBeNull();
    });
  });

  describe('Modo crear', () => {
    it('muestra título "Nuevo test"', () => {
      render(<TestEditor open={true} test={null} onSave={vi.fn()} onClose={vi.fn()} />);
      expect(screen.getByText('Nuevo test')).toBeInTheDocument();
    });

    it('tiene 1 mensaje vacío por defecto', () => {
      render(<TestEditor open={true} test={null} onSave={vi.fn()} onClose={vi.fn()} />);
      const inputs = screen.getAllByPlaceholderText('Mensaje del usuario');
      expect(inputs).toHaveLength(1);
    });

    it('tiene 1 assertion por defecto (reaches_end)', () => {
      render(<TestEditor open={true} test={null} onSave={vi.fn()} onClose={vi.fn()} />);
      const select = screen.getByRole('combobox');
      expect(select.value).toBe('reaches_end');
    });
  });

  describe('Modo editar', () => {
    it('muestra título "Editar test"', () => {
      render(<TestEditor open={true} test={baseTest} onSave={vi.fn()} onClose={vi.fn()} />);
      expect(screen.getByText('Editar test')).toBeInTheDocument();
    });

    it('precarga el nombre', () => {
      render(<TestEditor open={true} test={baseTest} onSave={vi.fn()} onClose={vi.fn()} />);
      const input = screen.getByPlaceholderText('Ej: Reserva válida');
      expect(input.value).toBe('Test existente');
    });

    it('precarga el número de mensajes', () => {
      render(<TestEditor open={true} test={baseTest} onSave={vi.fn()} onClose={vi.fn()} />);
      const inputs = screen.getAllByPlaceholderText('Mensaje del usuario');
      expect(inputs).toHaveLength(1);
      expect(inputs[0].value).toBe('Hola');
    });

    it('precarga la variable inicial', () => {
      render(<TestEditor open={true} test={baseTest} onSave={vi.fn()} onClose={vi.fn()} />);
      const varInput = screen.getByDisplayValue('name');
      expect(varInput).toBeInTheDocument();
    });

    it('precarga el checkbox enabled', () => {
      render(<TestEditor open={true} test={baseTest} onSave={vi.fn()} onClose={vi.fn()} />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox.checked).toBe(true);
    });
  });

  describe('Añadir mensajes', () => {
    it('añade un mensaje al pulsar "+ Añadir mensaje"', () => {
      render(<TestEditor open={true} test={null} onSave={vi.fn()} onClose={vi.fn()} />);
      expect(screen.getAllByPlaceholderText('Mensaje del usuario')).toHaveLength(1);
      fireEvent.click(screen.getByText('+ Añadir mensaje'));
      expect(screen.getAllByPlaceholderText('Mensaje del usuario')).toHaveLength(2);
    });
  });

  describe('Añadir assertions', () => {
    it('añade una assertion al pulsar "+ Añadir assertion"', () => {
      render(<TestEditor open={true} test={null} onSave={vi.fn()} onClose={vi.fn()} />);
      expect(screen.getAllByRole('combobox')).toHaveLength(1);
      fireEvent.click(screen.getByText('+ Añadir assertion'));
      expect(screen.getAllByRole('combobox')).toHaveLength(2);
    });
  });

  describe('Validación', () => {
    it('muestra error si no hay nombre', async () => {
      const onSave = vi.fn();
      render(<TestEditor open={true} test={null} onSave={onSave} onClose={vi.fn()} />);

      // Rellenar mensaje pero NO nombre
      fireEvent.change(screen.getByPlaceholderText('Mensaje del usuario'), {
        target: { value: 'Hola' },
      });
      fireEvent.click(screen.getByText('Crear test'));

      await waitFor(() => {
        expect(screen.getByText(/nombre es obligatorio/i)).toBeInTheDocument();
      });
      expect(onSave).not.toHaveBeenCalled();
    });

    it('muestra error si todos los mensajes están vacíos', async () => {
      const onSave = vi.fn();
      render(<TestEditor open={true} test={null} onSave={onSave} onClose={vi.fn()} />);

      // Nombre pero mensaje vacío
      fireEvent.change(screen.getByPlaceholderText('Ej: Reserva válida'), {
        target: { value: 'Test' },
      });
      fireEvent.click(screen.getByText('Crear test'));

      await waitFor(() => {
        expect(screen.getByText(/al menos 1 mensaje/i)).toBeInTheDocument();
      });
      expect(onSave).not.toHaveBeenCalled();
    });
  });

  describe('Guardar', () => {
    it('llama a onSave con el payload correcto', async () => {
      const onSave = vi.fn().mockResolvedValue();
      render(<TestEditor open={true} test={null} onSave={onSave} onClose={vi.fn()} />);

      fireEvent.change(screen.getByPlaceholderText('Ej: Reserva válida'), {
        target: { value: 'Test válido' },
      });
      fireEvent.change(screen.getByPlaceholderText('Mensaje del usuario'), {
        target: { value: 'Hola' },
      });
      fireEvent.click(screen.getByText('Crear test'));

      await waitFor(() => {
        expect(onSave).toHaveBeenCalledTimes(1);
      });

      const payload = onSave.mock.calls[0][0];
      expect(payload.name).toBe('Test válido');
      expect(payload.input_messages).toEqual(['Hola']);
      expect(payload.assertions).toHaveLength(1);
    });
  });

  describe('Cancelar', () => {
    it('llama a onClose al pulsar Cancelar', () => {
      const onClose = vi.fn();
      render(<TestEditor open={true} test={null} onSave={vi.fn()} onClose={onClose} />);
      fireEvent.click(screen.getByText('Cancelar'));
      expect(onClose).toHaveBeenCalled();
    });

    it('llama a onClose al pulsar la X', () => {
      const onClose = vi.fn();
      render(<TestEditor open={true} test={null} onSave={vi.fn()} onClose={onClose} />);
      // Hay varios '✕' (cerrar modal + borrar mensaje). El primero es el de cerrar.
      const closeButtons = screen.getAllByText('✕');
      fireEvent.click(closeButtons[0]);
      expect(onClose).toHaveBeenCalled();
    });
  });
});
