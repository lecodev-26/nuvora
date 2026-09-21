/**
 * Tests — ApiKeysPanel + ApiKeyCreateModal (14.10.10)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

vi.mock('../src/services/apiKeysApi', () => ({
  apiKeysService: {
    list: vi.fn(),
    create: vi.fn(),
    revoke: vi.fn(),
  },
}));

import ApiKeysPanel from '../src/components/api-keys/ApiKeysPanel';
import { apiKeysService } from '../src/services/apiKeysApi';

const MOCK_KEY = {
  id: 1,
  name: 'Mi web',
  key_prefix: 'nvr_live_ab12',
  created_at: '2026-09-20T10:00:00Z',
  last_used_at: null,
  revoked_at: null,
  is_active: true,
};

const MOCK_REVOKED = {
  id: 2,
  name: 'Vieja',
  key_prefix: 'nvr_live_old',
  created_at: '2026-09-15T10:00:00Z',
  last_used_at: '2026-09-16T12:00:00Z',
  revoked_at: '2026-09-17T08:00:00Z',
  is_active: false,
};

describe('ApiKeysPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.assign(navigator, {
      clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
    });
  });

  describe('open=false', () => {
    it('no renderiza nada', () => {
      const { container } = render(
        <ApiKeysPanel open={false} botId={42} onClose={() => {}} />
      );
      expect(container.firstChild).toBeNull();
    });
  });

  describe('Estado vacío', () => {
    beforeEach(() => {
      apiKeysService.list.mockResolvedValue({ data: { keys: [], total: 0 } });
    });

    it('muestra mensaje cuando no hay keys', async () => {
      render(<ApiKeysPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => {
        expect(screen.getByText(/Aún no tienes API Keys/i)).toBeInTheDocument();
      });
    });

    it('muestra botón "+ Nueva API Key"', async () => {
      render(<ApiKeysPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => {
        expect(screen.getByText(/Nueva API Key/i)).toBeInTheDocument();
      });
    });
  });

  describe('Lista con keys', () => {
    beforeEach(() => {
      apiKeysService.list.mockResolvedValue({
        data: { keys: [MOCK_KEY, MOCK_REVOKED], total: 2 },
      });
    });

    it('renderiza ambas keys', async () => {
      render(<ApiKeysPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => {
        expect(screen.getByText('Mi web')).toBeInTheDocument();
        expect(screen.getByText('Vieja')).toBeInTheDocument();
      });
    });

    it('muestra el key_prefix', async () => {
      render(<ApiKeysPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => {
        expect(screen.getByText(/nvr_live_ab12/i)).toBeInTheDocument();
      });
    });

    it('muestra REVOCADA para key inactiva', async () => {
      render(<ApiKeysPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => {
        // getAllByText porque "Revocada" también aparece en la línea de fechas
        const matches = screen.getAllByText(/REVOCADA/i);
        expect(matches.length).toBeGreaterThanOrEqual(1);
      });
    });

    it('key inactiva NO muestra botón Revocar', async () => {
      render(<ApiKeysPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => {
        // Solo 1 botón Revocar (para la activa)
        const btns = screen.getAllByText('Revocar');
        expect(btns).toHaveLength(1);
      });
    });
  });

  describe('Revocar', () => {
    beforeEach(() => {
      apiKeysService.list.mockResolvedValue({
        data: { keys: [MOCK_KEY], total: 1 },
      });
      apiKeysService.revoke.mockResolvedValue({ data: { id: 1 } });
    });

    it('click Revocar → abre confirm', async () => {
      render(<ApiKeysPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => {
        expect(screen.getByText('Revocar')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Revocar'));

      await waitFor(() => {
        expect(screen.getByText(/Revocar API Key/i)).toBeInTheDocument();
      });
    });

    it('confirmar → llama revoke + recarga', async () => {
      render(<ApiKeysPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => screen.getByText('Revocar'));
      fireEvent.click(screen.getByText('Revocar'));

      await waitFor(() => screen.getByText(/Las aplicaciones que usen/i));

      // El confirm tiene botón "Revocar" (el 2º ahora)
      const btns = screen.getAllByText('Revocar');
      fireEvent.click(btns[btns.length - 1]);

      await waitFor(() => {
        expect(apiKeysService.revoke).toHaveBeenCalledWith(42, 1);
      });
    });
  });

  describe('Crear API Key', () => {
    beforeEach(() => {
      apiKeysService.list.mockResolvedValue({
        data: { keys: [], total: 0 },
      });
      apiKeysService.create.mockResolvedValue({
        data: {
          id: 99,
          name: 'Nueva',
          key: 'nvr_live_NEW_SECRET_123',
          key_prefix: 'nvr_live_NEW_S',
          created_at: '2026-09-21T10:00:00Z',
          warning: 'Guarda esta clave. No volverá a mostrarse.',
        },
      });
    });

    it('click "+ Nueva API Key" abre modal crear', async () => {
      render(<ApiKeysPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => screen.getByText(/Nueva API Key/i));

      fireEvent.click(screen.getByText(/Nueva API Key/i));

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Mi integración/i)).toBeInTheDocument();
      });
    });

    it('crear con nombre → llama create + muestra secret', async () => {
      render(<ApiKeysPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => screen.getByText(/Nueva API Key/i));
      fireEvent.click(screen.getByText(/Nueva API Key/i));

      await waitFor(() => screen.getByPlaceholderText(/Mi integración/i));
      const input = screen.getByPlaceholderText(/Mi integración/i);
      fireEvent.change(input, { target: { value: 'Nueva' } });

      fireEvent.click(screen.getByText(/Crear API Key/i));

      await waitFor(() => {
        expect(apiKeysService.create).toHaveBeenCalledWith(42, 'Nueva');
      });

      // Debe mostrar el secret
      await waitFor(() => {
        expect(screen.getByDisplayValue('nvr_live_NEW_SECRET_123')).toBeInTheDocument();
      });
    });

    it('muestra warning "No volverá a mostrarse"', async () => {
      render(<ApiKeysPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => screen.getByText(/Nueva API Key/i));
      fireEvent.click(screen.getByText(/Nueva API Key/i));

      await waitFor(() => screen.getByPlaceholderText(/Mi integración/i));
      fireEvent.change(screen.getByPlaceholderText(/Mi integración/i), {
        target: { value: 'Nueva' },
      });
      fireEvent.click(screen.getByText(/Crear API Key/i));

      await waitFor(() => {
        expect(screen.getByText(/No volverá a mostrarse/i)).toBeInTheDocument();
      });
    });

    it('botón Copiar funciona', async () => {
      render(<ApiKeysPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => screen.getByText(/Nueva API Key/i));
      fireEvent.click(screen.getByText(/Nueva API Key/i));

      await waitFor(() => screen.getByPlaceholderText(/Mi integración/i));
      fireEvent.change(screen.getByPlaceholderText(/Mi integración/i), {
        target: { value: 'Nueva' },
      });
      fireEvent.click(screen.getByText(/Crear API Key/i));

      await waitFor(() => screen.getByText(/Copiar al portapapeles/i));
      fireEvent.click(screen.getByText(/Copiar al portapapeles/i));

      await waitFor(() => {
        expect(navigator.clipboard.writeText).toHaveBeenCalledWith('nvr_live_NEW_SECRET_123');
      });
    });

    it('crear sin nombre → error', async () => {
      render(<ApiKeysPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => screen.getByText(/Nueva API Key/i));
      fireEvent.click(screen.getByText(/Nueva API Key/i));

      await waitFor(() => screen.getByText(/Crear API Key/i));
      fireEvent.click(screen.getByText(/Crear API Key/i));

      await waitFor(() => {
        expect(screen.getByText(/El nombre es obligatorio/i)).toBeInTheDocument();
      });
    });
  });
});
