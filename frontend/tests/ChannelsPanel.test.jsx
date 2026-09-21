/**
 * Tests — ChannelsPanel (14.11.15)
 * ==================================
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';

vi.mock('../src/services/telegramApi', () => ({
  telegramService: {
    getStatus: vi.fn(),
    connect: vi.fn(),
    test: vi.fn(),
    disconnect: vi.fn(),
  },
}));

import ChannelsPanel from '../src/components/channels/ChannelsPanel';
import { telegramService } from '../src/services/telegramApi';

const BOT_PUBLISHED = {
  id: 42,
  name: 'Mi Bot',
  is_published: true,
  public_slug: 'mi-bot',
  public_id: 'pub-uuid-xyz',
};

const BOT_UNPUBLISHED = {
  id: 42,
  name: 'Mi Bot',
  is_published: false,
  public_slug: null,
  public_id: null,
};

describe('ChannelsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    telegramService.getStatus.mockResolvedValue({ data: null });
  });

  describe('open=false', () => {
    it('no renderiza nada', () => {
      const { container } = render(
        <ChannelsPanel open={false} bot={null} onClose={() => {}} />
      );
      expect(container.firstChild).toBeNull();
    });
  });

  describe('bot=null', () => {
    it('muestra mensaje "Selecciona un bot primero"', () => {
      render(<ChannelsPanel open={true} bot={null} onClose={() => {}} />);
      expect(screen.getByText(/Selecciona un bot primero/i)).toBeInTheDocument();
    });
  });

  describe('bot publicado', () => {
    it('muestra "Publicado" para Web', () => {
      render(<ChannelsPanel open={true} bot={BOT_PUBLISHED} onClose={() => {}} />);
      // Puede aparecer más de una vez (badge Web), usamos getAllByText
      const publicados = screen.getAllByText(/^Publicado$/i);
      expect(publicados.length).toBeGreaterThan(0);
    });

    it('muestra "Ver publicado →"', () => {
      render(<ChannelsPanel open={true} bot={BOT_PUBLISHED} onClose={() => {}} />);
      expect(screen.getByText(/Ver publicado/i)).toBeInTheDocument();
    });
  });

  describe('bot no publicado', () => {
    it('muestra "No publicado"', () => {
      render(<ChannelsPanel open={true} bot={BOT_UNPUBLISHED} onClose={() => {}} />);
      expect(screen.getByText(/No publicado/i)).toBeInTheDocument();
    });
  });

  describe('canales listados', () => {
    it('muestra Web, API, Telegram, WhatsApp, Discord', () => {
      render(<ChannelsPanel open={true} bot={BOT_PUBLISHED} onClose={() => {}} />);
      // Usamos getAllByText para evitar fallos por coincidencias múltiples
      // y comprobamos que cada canal aparece al menos una vez.
      expect(screen.getAllByText(/Web/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/API/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Telegram/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/WhatsApp/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Discord/i).length).toBeGreaterThan(0);
    });

    it('muestra "Próximamente" para WhatsApp y Discord', () => {
      render(<ChannelsPanel open={true} bot={BOT_PUBLISHED} onClose={() => {}} />);
      const proximamente = screen.getAllByText(/Próximamente/i);
      expect(proximamente.length).toBe(2);
    });
  });
});
