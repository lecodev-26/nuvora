/**
 * Tests — testService (14.8.14)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import api from '../src/services/api';
import { testService } from '../src/services/testService';

vi.mock('../src/services/api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('testService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('create', () => {
    it('llama a POST /bots/{botId}/tests con workflow_id en query', () => {
      const payload = { name: 'Test' };
      testService.create(42, 7, payload);
      expect(api.post).toHaveBeenCalledWith(
        '/bots/42/tests',
        payload,
        { params: { workflow_id: 7 } }
      );
    });
  });

  describe('list', () => {
    it('llama a GET /bots/{botId}/tests sin filtros', () => {
      testService.list(42);
      expect(api.get).toHaveBeenCalledWith(
        '/bots/42/tests',
        { params: {} }
      );
    });

    it('pasa workflow_id y enabled_only cuando se especifican', () => {
      testService.list(42, { workflow_id: 7, enabled_only: true });
      expect(api.get).toHaveBeenCalledWith(
        '/bots/42/tests',
        { params: { workflow_id: 7, enabled_only: true } }
      );
    });
  });

  describe('get', () => {
    it('llama a GET /bots/{botId}/tests/{testId}', () => {
      testService.get(42, 5);
      expect(api.get).toHaveBeenCalledWith('/bots/42/tests/5');
    });
  });

  describe('update', () => {
    it('llama a PUT con payload', () => {
      const payload = { name: 'Nuevo' };
      testService.update(42, 5, payload);
      expect(api.put).toHaveBeenCalledWith('/bots/42/tests/5', payload);
    });
  });

  describe('delete', () => {
    it('llama a DELETE /bots/{botId}/tests/{testId}', () => {
      testService.delete(42, 5);
      expect(api.delete).toHaveBeenCalledWith('/bots/42/tests/5');
    });
  });

  describe('run', () => {
    it('llama a POST /tests/{testId}/run', () => {
      testService.run(42, 5);
      expect(api.post).toHaveBeenCalledWith('/bots/42/tests/5/run');
    });
  });

  describe('runAll', () => {
    it('llama a POST /tests/run-all con enabled_only=true por defecto', () => {
      testService.runAll(42, 7);
      expect(api.post).toHaveBeenCalledWith(
        '/bots/42/tests/run-all',
        null,
        { params: { workflow_id: 7, enabled_only: true } }
      );
    });

    it('pasa enabled_only=false si se especifica', () => {
      testService.runAll(42, 7, false);
      expect(api.post).toHaveBeenCalledWith(
        '/bots/42/tests/run-all',
        null,
        { params: { workflow_id: 7, enabled_only: false } }
      );
    });
  });

  describe('analyze', () => {
    it('llama a POST /tests/analyze con workflow_id', () => {
      testService.analyze(42, 7);
      expect(api.post).toHaveBeenCalledWith(
        '/bots/42/tests/analyze',
        null,
        { params: { workflow_id: 7 } }
      );
    });
  });
});
