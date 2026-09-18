/**
 * Tests — PublicationPanel (14.9.11)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

vi.mock('../src/services/publicationApi', () => ({
  publicationApi: {
    getPublication: vi.fn(),
    updatePublication: vi.fn(),
    publish: vi.fn(),
    unpublish: vi.fn(),
  },
}));

import PublicationPanel from '../src/components/publication/PublicationPanel';
import { publicationApi } from '../src/services/publicationApi';

const MOCK_NOT_PUBLISHED = {
  bot_id: 42,
  is_published: false,
  public_id: null,
  public_slug: null,
  published_at: null,
  public_url: null,
  config: {
    welcome_message: null,
    placeholder: null,
    primary_color: null,
    show_branding: true,
  },
};

const MOCK_PUBLISHED = {
  bot_id: 42,
  is_published: true,
  public_id: 'abc-123',
  public_slug: 'clinica-salud',
  published_at: '2026-09-18T15:00:00Z',
  public_url: 'https://nuvora-chi.vercel.app/b/clinica-salud',
  config: {
    welcome_message: 'Hola',
    placeholder: 'Escribe...',
    primary_color: '#7B5CFF',
    show_branding: true,
  },
};

describe('PublicationPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock clipboard
    Object.assign(navigator, {
      clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
    });
  });

  // ============================================================
  // NO PUBLICADO
  // ============================================================

  describe('Estado NO publicado', () => {
    beforeEach(() => {
      publicationApi.getPublication.mockResolvedValue({ data: MOCK_NOT_PUBLISHED });
    });

    it('muestra "No publicado"', async () => {
      render(<PublicationPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => {
        expect(screen.getByText(/No publicado/i)).toBeInTheDocument();
      });
    });

    it('muestra el botón "🚀 Publicar bot"', async () => {
      render(<PublicationPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => {
        expect(screen.getByText(/Publicar bot/i)).toBeInTheDocument();
      });
    });

    it('NO muestra el botón Despublicar', async () => {
      render(<PublicationPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => {
        expect(screen.queryByText('Despublicar')).not.toBeInTheDocument();
      });
    });

    it('NO muestra la URL pública', async () => {
      render(<PublicationPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => {
        expect(screen.queryByText(/URL pública/i)).not.toBeInTheDocument();
      });
    });
  });

  // ============================================================
  // PUBLICAR
  // ============================================================

  describe('Publicar', () => {
    beforeEach(() => {
      publicationApi.getPublication.mockResolvedValue({ data: MOCK_NOT_PUBLISHED });
      publicationApi.publish.mockResolvedValue({ data: { is_published: true } });
    });

    it('click "Publicar bot" llama a publish(botId)', async () => {
      render(<PublicationPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => {
        expect(screen.getByText(/Publicar bot/i)).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText(/Publicar bot/i));

      await waitFor(() => {
        expect(publicationApi.publish).toHaveBeenCalledWith(42);
      });
    });

    it('muestra error si publish falla', async () => {
      publicationApi.publish.mockRejectedValue({
        response: { data: { detail: 'El bot no tiene workflow activo' } },
      });
      render(<PublicationPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => {
        expect(screen.getByText(/Publicar bot/i)).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText(/Publicar bot/i));

      await waitFor(() => {
        expect(
          screen.getByText(/El bot no tiene workflow activo/i)
        ).toBeInTheDocument();
      });
    });
  });

  // ============================================================
  // PUBLICADO
  // ============================================================

  describe('Estado PUBLICADO', () => {
    beforeEach(() => {
      publicationApi.getPublication.mockResolvedValue({ data: MOCK_PUBLISHED });
    });

    it('muestra "🟢 Publicado"', async () => {
      render(<PublicationPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => {
        expect(screen.getByText(/Publicado/i)).toBeInTheDocument();
      });
    });

    it('muestra la URL pública', async () => {
      render(<PublicationPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => {
        expect(
          screen.getByDisplayValue(MOCK_PUBLISHED.public_url)
        ).toBeInTheDocument();
      });
    });

    it('muestra el botón Despublicar', async () => {
      render(<PublicationPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => {
        expect(screen.getByText('Despublicar')).toBeInTheDocument();
      });
    });

    it('NO muestra el botón "Publicar bot"', async () => {
      render(<PublicationPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => {
        expect(screen.queryByText(/Publicar bot/i)).not.toBeInTheDocument();
      });
    });

    it('link "Ver bot en nueva pestaña"', async () => {
      render(<PublicationPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => {
        const link = screen.getByText(/Ver bot en nueva pestaña/i);
        expect(link).toHaveAttribute('href', MOCK_PUBLISHED.public_url);
        expect(link).toHaveAttribute('target', '_blank');
      });
    });
  });

  // ============================================================
  // COPIAR URL
  // ============================================================

  describe('Copiar URL', () => {
    beforeEach(() => {
      publicationApi.getPublication.mockResolvedValue({ data: MOCK_PUBLISHED });
    });

    it('click Copiar → clipboard.writeText(url)', async () => {
      render(<PublicationPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => {
        expect(screen.getByText(/Copiar/i)).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText(/Copiar/i));

      await waitFor(() => {
        expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
          MOCK_PUBLISHED.public_url
        );
      });
    });

    it('muestra "✓ Copiado" tras copiar', async () => {
      render(<PublicationPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => {
        expect(screen.getByText(/Copiar/i)).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText(/Copiar/i));

      await waitFor(() => {
        expect(screen.getByText(/Copiado/i)).toBeInTheDocument();
      });
    });
  });

  // ============================================================
  // DESPUBLICAR
  // ============================================================

  describe('Despublicar', () => {
    beforeEach(() => {
      publicationApi.getPublication.mockResolvedValue({ data: MOCK_PUBLISHED });
      publicationApi.unpublish.mockResolvedValue({ data: { is_published: false } });
    });

    it('click "Despublicar" llama a unpublish(botId)', async () => {
      render(<PublicationPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => {
        expect(screen.getByText('Despublicar')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Despublicar'));

      await waitFor(() => {
        expect(publicationApi.unpublish).toHaveBeenCalledWith(42);
      });
    });
  });

  // ============================================================
  // CONFIG
  // ============================================================

  describe('Editar config', () => {
    beforeEach(() => {
      publicationApi.getPublication.mockResolvedValue({ data: MOCK_PUBLISHED });
      publicationApi.updatePublication.mockResolvedValue({ data: MOCK_PUBLISHED });
    });

    it('click "✎ Editar apariencia" abre el form', async () => {
      render(<PublicationPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => {
        expect(screen.getByText(/Editar apariencia/i)).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText(/Editar apariencia/i));

      await waitFor(() => {
        expect(screen.getByText(/Mensaje de bienvenida/i)).toBeInTheDocument();
      });
    });

    it('guardar llama a updatePublication con los campos', async () => {
      render(<PublicationPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => {
        expect(screen.getByText(/Editar apariencia/i)).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText(/Editar apariencia/i));

      await waitFor(() => {
        expect(screen.getByText(/Mensaje de bienvenida/i)).toBeInTheDocument();
      });

      // Encontramos el input de mensaje y lo editamos
      const inputs = screen.getAllByDisplayValue(/Hola/);
      fireEvent.change(inputs[0], { target: { value: 'Nuevo welcome' } });

      // Click guardar (el 2º botón con texto Guardar)
      const guardarBtns = screen.getAllByText('Guardar');
      fireEvent.click(guardarBtns[guardarBtns.length - 1]);

      await waitFor(() => {
        expect(publicationApi.updatePublication).toHaveBeenCalled();
        const call = publicationApi.updatePublication.mock.calls[0];
        expect(call[0]).toBe(42);
        expect(call[1].welcome_message).toBe('Nuevo welcome');
      });
    });

    it('cancelar cierra el form', async () => {
      render(<PublicationPanel open={true} botId={42} onClose={() => {}} />);
      await waitFor(() => {
        expect(screen.getByText(/Editar apariencia/i)).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText(/Editar apariencia/i));

      await waitFor(() => {
        expect(screen.getByText('Cancelar')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Cancelar'));

      await waitFor(() => {
        expect(screen.queryByText(/Mensaje de bienvenida/i)).not.toBeInTheDocument();
      });
    });
  });

  // ============================================================
  // CERRAR
  // ============================================================

  describe('Cerrar', () => {
    beforeEach(() => {
      publicationApi.getPublication.mockResolvedValue({ data: MOCK_NOT_PUBLISHED });
    });

    it('click en ✕ llama a onClose', async () => {
      const onClose = vi.fn();
      render(<PublicationPanel open={true} botId={42} onClose={onClose} />);
      await waitFor(() => {
        expect(screen.getByText('✕')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('✕'));
      expect(onClose).toHaveBeenCalled();
    });

    it('click en backdrop cierra', async () => {
      const onClose = vi.fn();
      const { container } = render(
        <PublicationPanel open={true} botId={42} onClose={onClose} />
      );
      await waitFor(() => {
        expect(screen.getByText(/Publicación/i)).toBeInTheDocument();
      });

      // El backdrop es el primer div con la clase fixed inset-0
      const backdrop = container.querySelector('.fixed.inset-0');
      fireEvent.click(backdrop);
      expect(onClose).toHaveBeenCalled();
    });
  });

  // ============================================================
  // open=false → no renderiza nada
  // ============================================================

  describe('open=false', () => {
    it('no renderiza nada', () => {
      const { container } = render(
        <PublicationPanel open={false} botId={42} onClose={() => {}} />
      );
      expect(container.firstChild).toBeNull();
    });
  });
});
