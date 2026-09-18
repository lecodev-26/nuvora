/**
 * Tests — publicationApi (14.9.11)
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
import { publicationApi } from '../src/services/publicationApi';

describe('publicationApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getPublication', () => {
    it('GET /bots/{botId}/publication', () => {
      publicationApi.getPublication(42);
      expect(api.get).toHaveBeenCalledWith('/bots/42/publication');
    });
  });

  describe('updatePublication', () => {
    it('PUT /bots/{botId}/publication con config', () => {
      const config = { welcome_message: 'Hola', show_branding: true };
      publicationApi.updatePublication(42, config);
      expect(api.put).toHaveBeenCalledWith(
        '/bots/42/publication',
        { config }
      );
    });
  });

  describe('publish', () => {
    it('POST /bots/{botId}/publish', () => {
      publicationApi.publish(42);
      expect(api.post).toHaveBeenCalledWith('/bots/42/publish');
    });
  });

  describe('unpublish', () => {
    it('POST /bots/{botId}/unpublish', () => {
      publicationApi.unpublish(42);
      expect(api.post).toHaveBeenCalledWith('/bots/42/unpublish');
    });
  });
});
