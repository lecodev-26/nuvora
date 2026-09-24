import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';

vi.mock('../src/services/api', () => ({
  default: { get: vi.fn() },
}));

import { useCreatorStatus } from '../src/hooks/useCreatorStatus';
import api from '../src/services/api';

describe('useCreatorStatus', () => {
  beforeEach(() => vi.clearAllMocks());

  it('fetch OK', async () => {
    api.get.mockResolvedValue({ data: { ready: true, next_step: null } });
    const { result } = renderHook(() => useCreatorStatus(1));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.status.ready).toBe(true);
    expect(api.get).toHaveBeenCalledWith('/bots/1/creator-status');
  });

  it('maneja error', async () => {
    api.get.mockRejectedValue({
      response: { data: { detail: 'Bot no encontrado' } },
    });
    const { result } = renderHook(() => useCreatorStatus(999));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBe('Bot no encontrado');
    expect(result.current.status).toBeNull();
  });

  it('sin botId → no fetch', async () => {
    const { result } = renderHook(() => useCreatorStatus(null));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(api.get).not.toHaveBeenCalled();
  });
});
