/**
 * Tests — PublicChat (14.9.10)
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import PublicChat from '../src/components/public/PublicChat';

describe('PublicChat', () => {
  describe('Render básico', () => {
    it('muestra el placeholder por defecto', () => {
      render(<PublicChat messages={[]} onSend={() => {}} />);
      expect(
        screen.getByPlaceholderText('Escribe un mensaje...')
      ).toBeInTheDocument();
    });

    it('muestra un placeholder personalizado', () => {
      render(
        <PublicChat
          messages={[]}
          onSend={() => {}}
          placeholder="Dime algo..."
        />
      );
      expect(screen.getByPlaceholderText('Dime algo...')).toBeInTheDocument();
    });

    it('muestra el botón Enviar', () => {
      render(<PublicChat messages={[]} onSend={() => {}} />);
      expect(screen.getByText('Enviar')).toBeInTheDocument();
    });
  });

  describe('Welcome message', () => {
    it('muestra welcomeMessage si no hay mensajes', () => {
      render(
        <PublicChat
          messages={[]}
          onSend={() => {}}
          welcomeMessage="¡Hola!"
        />
      );
      expect(screen.getByText('¡Hola!')).toBeInTheDocument();
    });

    it('NO muestra welcomeMessage si ya hay mensajes', () => {
      render(
        <PublicChat
          messages={[{ role: 'user', text: 'Hola' }]}
          onSend={() => {}}
          welcomeMessage="¡Hola!"
        />
      );
      expect(screen.queryByText('¡Hola!')).not.toBeInTheDocument();
    });
  });

  describe('Render de mensajes', () => {
    it('renderiza mensajes del usuario y del bot', () => {
      render(
        <PublicChat
          messages={[
            { role: 'user', text: 'Hola' },
            { role: 'bot', text: '¿Qué tal?' },
          ]}
          onSend={() => {}}
        />
      );
      expect(screen.getByText('Hola')).toBeInTheDocument();
      expect(screen.getByText('¿Qué tal?')).toBeInTheDocument();
    });
  });

  describe('Envío de mensajes', () => {
    it('llama a onSend con el texto al hacer click en Enviar', () => {
      const onSend = vi.fn();
      render(<PublicChat messages={[]} onSend={onSend} />);
      const input = screen.getByPlaceholderText('Escribe un mensaje...');
      fireEvent.change(input, { target: { value: 'Hola' } });
      fireEvent.click(screen.getByText('Enviar'));
      expect(onSend).toHaveBeenCalledWith('Hola');
    });

    it('llama a onSend con Enter', () => {
      const onSend = vi.fn();
      render(<PublicChat messages={[]} onSend={onSend} />);
      const input = screen.getByPlaceholderText('Escribe un mensaje...');
      fireEvent.change(input, { target: { value: 'Hola' } });
      fireEvent.keyDown(input, { key: 'Enter', shiftKey: false });
      expect(onSend).toHaveBeenCalledWith('Hola');
    });

    it('NO llama a onSend con Shift+Enter', () => {
      const onSend = vi.fn();
      render(<PublicChat messages={[]} onSend={onSend} />);
      const input = screen.getByPlaceholderText('Escribe un mensaje...');
      fireEvent.change(input, { target: { value: 'Hola' } });
      fireEvent.keyDown(input, { key: 'Enter', shiftKey: true });
      expect(onSend).not.toHaveBeenCalled();
    });

    it('NO llama a onSend con texto vacío', () => {
      const onSend = vi.fn();
      render(<PublicChat messages={[]} onSend={onSend} />);
      fireEvent.click(screen.getByText('Enviar'));
      expect(onSend).not.toHaveBeenCalled();
    });

    it('NO llama a onSend con solo espacios', () => {
      const onSend = vi.fn();
      render(<PublicChat messages={[]} onSend={onSend} />);
      const input = screen.getByPlaceholderText('Escribe un mensaje...');
      fireEvent.change(input, { target: { value: '   ' } });
      fireEvent.click(screen.getByText('Enviar'));
      expect(onSend).not.toHaveBeenCalled();
    });

    it('limpia el input tras enviar', () => {
      const onSend = vi.fn();
      render(<PublicChat messages={[]} onSend={onSend} />);
      const input = screen.getByPlaceholderText('Escribe un mensaje...');
      fireEvent.change(input, { target: { value: 'Hola' } });
      fireEvent.click(screen.getByText('Enviar'));
      expect(input.value).toBe('');
    });
  });

  describe('Estados disabled/sending', () => {
    it('deshabilita el input si disabled=true', () => {
      render(<PublicChat messages={[]} onSend={() => {}} disabled={true} />);
      const input = screen.getByPlaceholderText('Escribe un mensaje...');
      expect(input).toBeDisabled();
    });

    it('deshabilita el botón si sending=true', () => {
      render(<PublicChat messages={[]} onSend={() => {}} sending={true} />);
      const button = screen.getByText('Enviar');
      expect(button).toBeDisabled();
    });

    it('NO llama a onSend si sending=true', () => {
      const onSend = vi.fn();
      render(
        <PublicChat
          messages={[]}
          onSend={onSend}
          sending={true}
        />
      );
      const input = screen.getByPlaceholderText('Escribe un mensaje...');
      fireEvent.change(input, { target: { value: 'Hola' } });
      fireEvent.click(screen.getByText('Enviar'));
      expect(onSend).not.toHaveBeenCalled();
    });
  });
});
