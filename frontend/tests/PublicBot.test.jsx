/**
 * Tests — PublicBot (14.9.10)
 *
 * Mockea react-router-dom (useParams), publicApi y sessionStorage.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

// Mock react-router-dom
vi.mock('react-router-dom', () => ({
  useParams: () => ({ identifier: 'test-bot' }),
  Link: ({ children, ...props }) => <a {...props}>{children}</a>,
}));

// Mock publicApi
vi.mock('../src/services/publicApi', () => ({
  publicApi: {
    getBot: vi.fn(),
    createSession: vi.fn(),
    sendMessage: vi.fn(),
    closeSession: vi.fn(),
  },
}));

import PublicBot from '../src/pages/PublicBot';
import { publicApi } from '../src/services/publicApi';

const MOCK_BOT = {
  public_id: 'abc-123',
  name: 'Bot Test',
  description: 'Bot para tests',
  nicho_id: 'otro',
  business_name: 'Test Inc',
  config: {
    welcome_message: 'Hola desde test',
    placeholder: 'Escribe aquí',
    show_branding: true,
  },
};

const MOCK_SESSION = { session_id: 'sess-xyz' };
const MOCK_MESSAGE = { reply: '¡Hola! ¿En qué puedo ayudarte?' };

describe('PublicBot', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
  });

  describe('Loading', () => {
    it('muestra spinner mientras carga', () => {
      publicApi.getBot.mockReturnValue(new Promise(() => {})); // nunca resuelve
      render(<PublicBot />);
      expect(screen.getByText('Cargando...')).toBeInTheDocument();
    });
  });

  describe('Not found (404)', () => {
    it('muestra mensaje si el bot no existe', async () => {
      publicApi.getBot.mockRejectedValue({ response: { status: 404 } });
      render(<PublicBot />);
      await waitFor(() => {
        expect(screen.getByText(/Bot no encontrado/i)).toBeInTheDocument();
      });
    });
  });

  describe('Error genérico', () => {
    it('muestra error si falla con 500', async () => {
      publicApi.getBot.mockRejectedValue({
        response: { status: 500, data: { detail: 'Explotó' } },
      });
      render(<PublicBot />);
      await waitFor(() => {
        expect(screen.getByText('Error')).toBeInTheDocument();
      });
      expect(screen.getByText('Explotó')).toBeInTheDocument();
    });
  });

  describe('Carga OK', () => {
    beforeEach(() => {
      publicApi.getBot.mockResolvedValue({ data: MOCK_BOT });
      publicApi.createSession.mockResolvedValue({ data: MOCK_SESSION });
    });

    it('muestra el welcome_message', async () => {
      render(<PublicBot />);
      await waitFor(() => {
        expect(screen.getByText('Hola desde test')).toBeInTheDocument();
      });
    });

    it('muestra el placeholder custom', async () => {
      render(<PublicBot />);
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Escribe aquí')).toBeInTheDocument();
      });
    });

    it('muestra el nombre del negocio', async () => {
      render(<PublicBot />);
      await waitFor(() => {
        expect(screen.getByText('Test Inc')).toBeInTheDocument();
      });
    });

    it('guarda session_id en sessionStorage', async () => {
      render(<PublicBot />);
      await waitFor(() => {
        expect(
          sessionStorage.getItem('nuvora_public_session_test-bot')
        ).toBe('sess-xyz');
      });
    });

    it('reutiliza session_id si ya existe en sessionStorage', async () => {
      sessionStorage.setItem('nuvora_public_session_test-bot', 'sess-old');
      render(<PublicBot />);
      await waitFor(() => {
        expect(publicApi.createSession).not.toHaveBeenCalled();
      });
    });

    it('muestra "Powered by Nuvora" si show_branding=true', async () => {
      render(<PublicBot />);
      await waitFor(() => {
        expect(screen.getByText(/Powered by/i)).toBeInTheDocument();
      });
    });
  });

  describe('Envío de mensaje', () => {
    beforeEach(() => {
      publicApi.getBot.mockResolvedValue({ data: MOCK_BOT });
      publicApi.createSession.mockResolvedValue({ data: MOCK_SESSION });
      publicApi.sendMessage.mockResolvedValue({ data: MOCK_MESSAGE });
    });

    it('muestra el mensaje del usuario y la respuesta', async () => {
      render(<PublicBot />);
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Escribe aquí')).toBeInTheDocument();
      });

      const input = screen.getByPlaceholderText('Escribe aquí');
      fireEvent.change(input, { target: { value: 'Hola' } });
      fireEvent.click(screen.getByText('Enviar'));

      await waitFor(() => {
        expect(screen.getByText('Hola')).toBeInTheDocument();
      });
      await waitFor(() => {
        expect(screen.getByText(MOCK_MESSAGE.reply)).toBeInTheDocument();
      });
    });

    it('llama a sendMessage con identifier + session_id + texto', async () => {
      render(<PublicBot />);
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Escribe aquí')).toBeInTheDocument();
      });

      const input = screen.getByPlaceholderText('Escribe aquí');
      fireEvent.change(input, { target: { value: 'Hola' } });
      fireEvent.click(screen.getByText('Enviar'));

      await waitFor(() => {
        expect(publicApi.sendMessage).toHaveBeenCalledWith(
          'test-bot',
          'sess-xyz',
          'Hola'
        );
      });
    });
  });

  describe('Bot sin branding', () => {
    it('NO muestra Powered by si show_branding=false', async () => {
      publicApi.getBot.mockResolvedValue({
        data: { ...MOCK_BOT, config: { ...MOCK_BOT.config, show_branding: false } },
      });
      publicApi.createSession.mockResolvedValue({ data: MOCK_SESSION });
      render(<PublicBot />);
      await waitFor(() => {
        expect(screen.queryByText(/Powered by/i)).not.toBeInTheDocument();
      });
    });
  });
});
