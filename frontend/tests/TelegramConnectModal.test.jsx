/**
 * Tests — TelegramConnectModal (14.11.14)
 * =========================================
 * Verifica UI + flujo de conexión.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

import TelegramConnectModal from '../src/components/channels/TelegramConnectModal';

describe('TelegramConnectModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('open=false', () => {
    it('no renderiza nada', () => {
      const { container } = render(
        <TelegramConnectModal open={false} onConnect={vi.fn()} onClose={vi.fn()} />
      );
      expect(container.firstChild).toBeNull();
    });
  });

  describe('open=true', () => {
    it('muestra título e instrucciones de BotFather', () => {
      render(
        <TelegramConnectModal open={true} onConnect={vi.fn()} onClose={vi.fn()} />
      );
      // El título está en un h2
      expect(screen.getByRole('heading', { name: /Conectar Telegram/i })).toBeInTheDocument();
      expect(screen.getByText(/@BotFather/i)).toBeInTheDocument();
      expect(screen.getByText(/\/newbot/i)).toBeInTheDocument();
    });

    it('input de token tipo password', () => {
      render(
        <TelegramConnectModal open={true} onConnect={vi.fn()} onClose={vi.fn()} />
      );
      const input = screen.getByPlaceholderText(/1234567890/i);
      expect(input).toBeInTheDocument();
      expect(input.type).toBe('password');
    });

    it('click Conectar con token vacío → error inline, no llama onConnect', async () => {
      const onConnect = vi.fn();
      render(
        <TelegramConnectModal open={true} onConnect={onConnect} onClose={vi.fn()} />
      );
      fireEvent.click(screen.getByRole('button', { name: /Conectar Telegram/i }));
      await waitFor(() => {
        expect(screen.getByText(/token es obligatorio/i)).toBeInTheDocument();
      });
      expect(onConnect).not.toHaveBeenCalled();
    });

    it('click Conectar con token válido → llama onConnect(token)', async () => {
      const onConnect = vi.fn().mockResolvedValue({});
      render(
        <TelegramConnectModal open={true} onConnect={onConnect} onClose={vi.fn()} />
      );
      const input = screen.getByPlaceholderText(/1234567890/i);
      fireEvent.change(input, { target: { value: '1234567890:ABCdef' } });
      fireEvent.click(screen.getByRole('button', { name: /Conectar Telegram/i }));
      await waitFor(() => {
        expect(onConnect).toHaveBeenCalledWith('1234567890:ABCdef');
      });
    });

    it('onConnect rechaza → muestra error', async () => {
      const onConnect = vi.fn().mockRejectedValue({
        response: { data: { detail: 'Token inválido para Telegram' } },
      });
      render(
        <TelegramConnectModal open={true} onConnect={onConnect} onClose={vi.fn()} />
      );
      const input = screen.getByPlaceholderText(/1234567890/i);
      fireEvent.change(input, { target: { value: '1234567890:ABCdef' } });
      fireEvent.click(screen.getByRole('button', { name: /Conectar Telegram/i }));
      await waitFor(() => {
        expect(screen.getByText(/Token inválido para Telegram/i)).toBeInTheDocument();
      });
    });
  });
});
