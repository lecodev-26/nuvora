/**
 * Tests — telegramApi (14.11.13)
 * =================================
 * Verifica que cada método llama al endpoint correcto.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../src/services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

import { telegramService } from '../src/services/telegramApi';
import api from '../src/services/api';

describe('telegramApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getStatus', () => {
    it('GET /bots/{botId}/telegram', async () => {
      api.get.mockResolvedValue({ data: null });
      const res = await telegramService.getStatus(42);
      expect(api.get).toHaveBeenCalledWith('/bots/42/telegram');
      expect(res.data).toBeNull();
    });

    it('devuelve estado conectado si existe', async () => {
      const state = { status: 'connected', telegram_username: 'mi_bot' };
      api.get.mockResolvedValue({ data: state });
      const res = await telegramService.getStatus(7);
      expect(res.data).toEqual(state);
    });
  });

  describe('connect', () => {
    it('POST con token en body', async () => {
      api.post.mockResolvedValue({
        data: { status: 'connected', telegram_username: 'mi_bot' },
      });
      await telegramService.connect(42, '123:ABC');
      expect(api.post).toHaveBeenCalledWith(
        '/bots/42/telegram/connect',
        { token: '123:ABC' },
      );
    });

    it('propaga errores del backend', async () => {
      api.post.mockRejectedValue(new Error('Token inválido'));
      await expect(
        telegramService.connect(42, 'malo'),
      ).rejects.toThrow('Token inválido');
    });
  });

  describe('test', () => {
    it('POST /bots/{botId}/telegram/test sin body', async () => {
      api.post.mockResolvedValue({ data: { ok: true, username: 'x' } });
      const res = await telegramService.test(42);
      expect(api.post).toHaveBeenCalledWith('/bots/42/telegram/test');
      expect(res.data.ok).toBe(true);
    });
  });

  describe('disconnect', () => {
    it('POST /bots/{botId}/telegram/disconnect sin body', async () => {
      api.post.mockResolvedValue({ data: { status: 'disconnected' } });
      const res = await telegramService.disconnect(42);
      expect(api.post).toHaveBeenCalledWith('/bots/42/telegram/disconnect');
      expect(res.data.status).toBe('disconnected');
    });
  });
});
