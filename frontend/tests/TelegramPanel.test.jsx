/**
 * Tests — TelegramPanel (14.11.14)
 * ==================================
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

vi.mock('../src/services/telegramApi', () => ({
  telegramService: {
    getStatus: vi.fn(),
    connect: vi.fn(),
    test: vi.fn(),
    disconnect: vi.fn(),
  },
}));

import TelegramPanel from '../src/components/channels/TelegramPanel';
import { telegramService } from '../src/services/telegramApi';

const STATUS_CONNECTED = {
  status: 'connected',
  telegram_username: 'mi_bot',
  telegram_bot_id: '111222',
  is_active: true,
  token_configured: true,
  created_at: '2026-09-20T10:00:00Z',
  last_event_at: null,
  last_error: null,
};

describe('TelegramPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock global alert
    global.alert = vi.fn();
  });

  describe('estado inicial', () => {
    it('muestra "Cargando..." al principio', async () => {
      telegramService.getStatus.mockReturnValue(new Promise(() => {})); // nunca resuelve
      render(<TelegramPanel botId={42} />);
      expect(screen.getByText(/Cargando estado de Telegram/i)).toBeInTheDocument();
    });
  });

  describe('sin integración (null)', () => {
    beforeEach(() => {
      telegramService.getStatus.mockResolvedValue({ data: null });
    });

    it('muestra botón "Conectar Telegram"', async () => {
      render(<TelegramPanel botId={42} />);
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Conectar Telegram/i })).toBeInTheDocument();
      });
    });

    it('click Conectar → abre modal', async () => {
      render(<TelegramPanel botId={42} />);
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Conectar Telegram/i })).toBeInTheDocument();
      });
      fireEvent.click(screen.getByRole('button', { name: /Conectar Telegram/i }));
      // Modal aparece con instrucciones (@BotFather + /newbot)
      await waitFor(() => {
        expect(screen.getAllByText(/@BotFather/i).length).toBeGreaterThan(0);
      });
    });
  });

  describe('integración conectada', () => {
    beforeEach(() => {
      telegramService.getStatus.mockResolvedValue({ data: STATUS_CONNECTED });
    });

    it('muestra @username + botón Probar + botón Desconectar', async () => {
      render(<TelegramPanel botId={42} />);
      await waitFor(() => {
        expect(screen.getByText('@mi_bot')).toBeInTheDocument();
      });
      expect(screen.getByRole('button', { name: /Probar conexión/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Desconectar/i })).toBeInTheDocument();
    });

    it('click Probar → llama telegramService.test', async () => {
      telegramService.test.mockResolvedValue({ data: { ok: true, username: 'mi_bot', first_name: 'MiBot' } });
      render(<TelegramPanel botId={42} />);
      await waitFor(() => {
        expect(screen.getByText('@mi_bot')).toBeInTheDocument();
      });
      fireEvent.click(screen.getByRole('button', { name: /Probar conexión/i }));
      await waitFor(() => {
        expect(telegramService.test).toHaveBeenCalledWith(42);
      });
    });

    it('click Desconectar → abre ConfirmModal', async () => {
      render(<TelegramPanel botId={42} />);
      await waitFor(() => {
        expect(screen.getByText('@mi_bot')).toBeInTheDocument();
      });
      fireEvent.click(screen.getByRole('button', { name: /Desconectar/i }));
      await waitFor(() => {
        expect(screen.getByText(/Desconectar Telegram/i)).toBeInTheDocument();
        expect(screen.getByText(/dejará de responder/i)).toBeInTheDocument();
      });
    });

    it('confirmar Desconectar → llama telegramService.disconnect', async () => {
      telegramService.disconnect.mockResolvedValue({ data: { status: 'disconnected' } });
      telegramService.getStatus
        .mockResolvedValueOnce({ data: STATUS_CONNECTED })
        .mockResolvedValueOnce({ data: null });

      render(<TelegramPanel botId={42} />);
      await waitFor(() => {
        expect(screen.getByText('@mi_bot')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /Desconectar/i }));
      // El botón del ConfirmModal tiene el texto "Desconectar"
      await waitFor(() => {
        const buttons = screen.getAllByRole('button', { name: /^Desconectar$/i });
        expect(buttons.length).toBeGreaterThan(0);
      });
      const confirmBtn = screen.getAllByRole('button', { name: /^Desconectar$/i })[0];
      fireEvent.click(confirmBtn);

      await waitFor(() => {
        expect(telegramService.disconnect).toHaveBeenCalledWith(42);
      });
    });
  });
});
