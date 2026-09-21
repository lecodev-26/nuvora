/**
 * Tests — apiKeysApi (14.10.10)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../src/services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

import api from '../src/services/api';
import { apiKeysService } from '../src/services/apiKeysApi';

describe('apiKeysService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('list', () => {
    it('GET /bots/{botId}/api-keys', () => {
      apiKeysService.list(42);
      expect(api.get).toHaveBeenCalledWith('/bots/42/api-keys');
    });
  });

  describe('create', () => {
    it('POST /bots/{botId}/api-keys con body {name}', () => {
      apiKeysService.create(42, 'Mi web');
      expect(api.post).toHaveBeenCalledWith(
        '/bots/42/api-keys',
        { name: 'Mi web' }
      );
    });
  });

  describe('revoke', () => {
    it('DELETE /bots/{botId}/api-keys/{keyId}', () => {
      apiKeysService.revoke(42, 7);
      expect(api.delete).toHaveBeenCalledWith('/bots/42/api-keys/7');
    });
  });
});
