/**
 * Tests — publicApi (14.9.10)
 *
 * Verifica que publicApi llama a los endpoints correctos
 * con los parámetros correctos.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('axios', () => {
  const mockInstance = {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  };
  return {
    default: {
      create: vi.fn(() => mockInstance),
    },
  };
});

import axios from 'axios';
import { publicApi } from '../src/services/publicApi';

// Obtenemos la instancia mockeada
const mockHttp = axios.create();

describe('publicApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getBot', () => {
    it('llama a GET /public/bots/{identifier}', () => {
      publicApi.getBot('clinica-salud');
      expect(mockHttp.get).toHaveBeenCalledWith('/public/bots/clinica-salud');
    });

    it('url-encodea el identifier', () => {
      publicApi.getBot('a b/c');
      expect(mockHttp.get).toHaveBeenCalledWith('/public/bots/a%20b%2Fc');
    });
  });

  describe('createSession', () => {
    it('llama a POST /public/bots/{identifier}/session con body vacío', () => {
      publicApi.createSession('abc-123');
      expect(mockHttp.post).toHaveBeenCalledWith(
        '/public/bots/abc-123/session',
        {}
      );
    });
  });

  describe('sendMessage', () => {
    it('llama a POST /message con session_id + message', () => {
      publicApi.sendMessage('abc-123', 'sess-xyz', 'Hola');
      expect(mockHttp.post).toHaveBeenCalledWith(
        '/public/bots/abc-123/message',
        { session_id: 'sess-xyz', message: 'Hola' }
      );
    });
  });

  describe('closeSession', () => {
    it('llama a DELETE /session con session_id en query', () => {
      publicApi.closeSession('abc-123', 'sess-xyz');
      expect(mockHttp.delete).toHaveBeenCalledWith(
        '/public/bots/abc-123/session',
        { params: { session_id: 'sess-xyz' } }
      );
    });
  });
});
