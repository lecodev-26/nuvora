/**
 * Tests — Widget embebible (14.9.12)
 *
 * Carga widget.js en jsdom simulando un <script> real y verifica:
 *   - Detección de modo (public vs legacy)
 *   - Creación de DOM
 *   - Llamadas a los endpoints correctos
 *   - Config visual aplicada
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { readFileSync } from 'fs';
import { resolve } from 'path';

// Cargar el código del widget como string
const WIDGET_CODE = readFileSync(
  resolve(__dirname, '../public/widget.js'),
  'utf-8'
);

// ============================================================
// HELPERS
// ============================================================

/**
 * Ejecuta el widget en jsdom con los atributos dados.
 * @param {object} attrs - atributos del <script> (ej: { 'data-bot-public-id': 'abc' })
 */
function runWidget(attrs = {}) {
  // Limpiar DOM previo
  document.body.innerHTML = '';
  document.head.innerHTML = '';

  // Crear el <script> con atributos
  const script = document.createElement('script');
  Object.entries(attrs).forEach(([k, v]) => script.setAttribute(k, v));
  document.body.appendChild(script);

  // Mockear currentScript
  Object.defineProperty(document, 'currentScript', {
    value: script,
    configurable: true,
  });

  // Ejecutar el código del widget
  // eslint-disable-next-line no-new-func
  new Function(WIDGET_CODE)();

  return script;
}

/**
 * Mock de fetch que devuelve respuestas según URL
 */
function mockFetch(routes) {
  global.fetch = vi.fn(async (url, opts = {}) => {
    const method = (opts.method || 'GET').toUpperCase();
    for (const [pattern, response] of Object.entries(routes)) {
      const [rMethod, rPath] = pattern.split(' ');
      if (rMethod === method && url.includes(rPath)) {
        const status = response.status || 200;
        return {
          ok: status >= 200 && status < 300,
          status,
          json: async () => response.body || {},
        };
      }
    }
    // Default 404
    return {
      ok: false,
      status: 404,
      json: async () => ({ detail: 'Not found' }),
    };
  });
}

// ============================================================
// SETUP
// ============================================================

beforeEach(() => {
  vi.clearAllMocks();
  sessionStorage.clear();
});

afterEach(() => {
  // Limpiar DOM
  document.body.innerHTML = '';
  document.head.innerHTML = '';
  vi.restoreAllMocks();
});

// ============================================================
// TESTS
// ============================================================

describe('Nuvora Widget', () => {
  // ==========================================================
  // 1. CARGA BÁSICA
  // ==========================================================

  describe('Carga básica', () => {
    it('crea #nuvora-bubble y #nuvora-window', async () => {
      mockFetch({});
      runWidget({ 'data-bot-public-id': 'test-id' });
      // Esperar microtasks (loadBotData es async)
      await new Promise((r) => setTimeout(r, 10));

      expect(document.getElementById('nuvora-bubble')).toBeTruthy();
      expect(document.getElementById('nuvora-window')).toBeTruthy();
    });

    it('crea el input y el botón de enviar', async () => {
      mockFetch({});
      runWidget({ 'data-bot-public-id': 'test-id' });
      await new Promise((r) => setTimeout(r, 10));

      expect(document.getElementById('nuvora-input')).toBeTruthy();
      expect(document.getElementById('nuvora-send')).toBeTruthy();
    });

    it('crea el header con el nombre y estado', async () => {
      mockFetch({});
      runWidget({ 'data-bot-public-id': 'test-id' });
      await new Promise((r) => setTimeout(r, 10));

      expect(document.getElementById('nuvora-business-name')).toBeTruthy();
      expect(document.querySelector('#nuvora-header .status')).toBeTruthy();
    });
  });

  // ==========================================================
  // 2. DETECCIÓN DE MODO
  // ==========================================================

  describe('Detección de modo', () => {
    it('modo PÚBLICO: llama a /public/bots/{id}', async () => {
      mockFetch({
        'GET /public/bots/test-public-id': {
          body: {
            public_id: 'test-public-id',
            name: 'Bot Test',
            business_name: 'Empresa Test',
            config: { welcome_message: 'Hola', show_branding: true },
          },
        },
        'POST /public/bots/test-public-id/session': {
          body: { session_id: 'sess-1' },
        },
      });

      runWidget({ 'data-bot-public-id': 'test-public-id' });
      await new Promise((r) => setTimeout(r, 20));

      const calls = global.fetch.mock.calls.map((c) => c[0]);
      expect(calls.some((u) => u.includes('/public/bots/test-public-id'))).toBe(true);
    });

    it('modo LEGACY: llama a /bots/{botId}/public', async () => {
      mockFetch({
        'GET /bots/9/public': {
          body: {
            id: 9,
            name: 'Bot Legacy',
            business_name: 'Empresa Legacy',
          },
        },
      });

      runWidget({ 'data-bot-id': '9' });
      await new Promise((r) => setTimeout(r, 20));

      const calls = global.fetch.mock.calls.map((c) => c[0]);
      expect(calls.some((u) => u.includes('/bots/9/public'))).toBe(true);
    });

    it('sin atributos: NO crea DOM y avisa en consola', () => {
      const errSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      runWidget({});

      expect(document.getElementById('nuvora-bubble')).toBeNull();
      expect(errSpy).toHaveBeenCalled();
    });
  });

  // ==========================================================
  // 3. MODO PÚBLICO — Config visual
  // ==========================================================

  describe('Modo público — config visual', () => {
    it('aplica el primary_color al header', async () => {
      mockFetch({
        'GET /public/bots/test-id': {
          body: {
            public_id: 'test-id',
            name: 'Bot',
            business_name: 'Empresa',
            config: {
              primary_color: '#FF0000',
              welcome_message: 'Hola',
              show_branding: true,
            },
          },
        },
        'POST /public/bots/test-id/session': {
          body: { session_id: 'sess-1' },
        },
      });

      runWidget({ 'data-bot-public-id': 'test-id' });
      await new Promise((r) => setTimeout(r, 30));

      const header = document.getElementById('nuvora-header');
      // jsdom normaliza #FF0000 a rgb(255, 0, 0)
      const bg = header.style.background;
      expect(bg.includes('#FF0000') || bg.includes('rgb(255, 0, 0)')).toBe(true);
    });

    it('aplica el welcome_message', async () => {
      mockFetch({
        'GET /public/bots/test-id': {
          body: {
            public_id: 'test-id',
            name: 'Bot',
            business_name: 'Empresa',
            config: { welcome_message: '¡Hola desde tests!' },
          },
        },
        'POST /public/bots/test-id/session': {
          body: { session_id: 'sess-1' },
        },
      });

      runWidget({ 'data-bot-public-id': 'test-id' });
      await new Promise((r) => setTimeout(r, 30));

      const greeting = document.getElementById('nuvora-greeting');
      expect(greeting.textContent).toContain('¡Hola desde tests!');
    });

    it('oculta el branding si show_branding=false', async () => {
      mockFetch({
        'GET /public/bots/test-id': {
          body: {
            public_id: 'test-id',
            name: 'Bot',
            business_name: 'Empresa',
            config: { show_branding: false },
          },
        },
        'POST /public/bots/test-id/session': {
          body: { session_id: 'sess-1' },
        },
      });

      runWidget({ 'data-bot-public-id': 'test-id' });
      await new Promise((r) => setTimeout(r, 30));

      const branding = document.getElementById('nuvora-branding');
      expect(branding.style.display).toBe('none');
    });

    it('muestra el branding si show_branding=true', async () => {
      mockFetch({
        'GET /public/bots/test-id': {
          body: {
            public_id: 'test-id',
            name: 'Bot',
            business_name: 'Empresa',
            config: { show_branding: true },
          },
        },
        'POST /public/bots/test-id/session': {
          body: { session_id: 'sess-1' },
        },
      });

      runWidget({ 'data-bot-public-id': 'test-id' });
      await new Promise((r) => setTimeout(r, 30));

      const branding = document.getElementById('nuvora-branding');
      expect(branding.style.display).not.toBe('none');
    });

    it('crea sesión (POST /session)', async () => {
      mockFetch({
        'GET /public/bots/test-id': {
          body: {
            public_id: 'test-id',
            name: 'Bot',
            business_name: 'Empresa',
            config: {},
          },
        },
        'POST /public/bots/test-id/session': {
          body: { session_id: 'sess-xyz' },
        },
      });

      runWidget({ 'data-bot-public-id': 'test-id' });
      await new Promise((r) => setTimeout(r, 30));

      const calls = global.fetch.mock.calls;
      const sessionCall = calls.find(
        (c) => typeof c[0] === 'string' && c[0].includes('/session')
      );
      expect(sessionCall).toBeTruthy();

      // Verifica que se guardó en sessionStorage
      const stored = sessionStorage.getItem('nuvora_session_test-id');
      expect(stored).toBe('sess-xyz');
    });
  });

  // ==========================================================
  // 4. ENVÍO DE MENSAJE (público)
  // ==========================================================

  describe('Envío de mensaje — modo público', () => {
    it('llama a POST /message con session_id + message', async () => {
      mockFetch({
        'GET /public/bots/test-id': {
          body: {
            public_id: 'test-id',
            name: 'Bot',
            business_name: 'Empresa',
            config: {},
          },
        },
        'POST /public/bots/test-id/session': {
          body: { session_id: 'sess-1' },
        },
        'POST /public/bots/test-id/message': {
          body: { reply: '¡Hola!', session_id: 'sess-1', status: 'completed' },
        },
      });

      runWidget({ 'data-bot-public-id': 'test-id' });
      await new Promise((r) => setTimeout(r, 30));

      // Escribir y enviar
      const input = document.getElementById('nuvora-input');
      const send = document.getElementById('nuvora-send');
      input.value = 'Hola';
      send.click();

      await new Promise((r) => setTimeout(r, 30));

      const calls = global.fetch.mock.calls;
      const messageCall = calls.find(
        (c) => typeof c[0] === 'string' && c[0].includes('/message')
      );
      expect(messageCall).toBeTruthy();

      // Verificar payload
      const opts = messageCall[1];
      const payload = JSON.parse(opts.body);
      expect(payload.session_id).toBe('sess-1');
      expect(payload.message).toBe('Hola');
    });

    it('añade el mensaje del bot al chat', async () => {
      mockFetch({
        'GET /public/bots/test-id': {
          body: {
            public_id: 'test-id',
            name: 'Bot',
            business_name: 'Empresa',
            config: {},
          },
        },
        'POST /public/bots/test-id/session': {
          body: { session_id: 'sess-1' },
        },
        'POST /public/bots/test-id/message': {
          body: { reply: 'Respuesta del bot', session_id: 'sess-1' },
        },
      });

      runWidget({ 'data-bot-public-id': 'test-id' });
      await new Promise((r) => setTimeout(r, 30));

      const input = document.getElementById('nuvora-input');
      const send = document.getElementById('nuvora-send');
      input.value = 'Hola';
      send.click();

      await new Promise((r) => setTimeout(r, 50));

      const messages = document.querySelectorAll('#nuvora-messages .n-msg');
      const texts = Array.from(messages).map((m) => m.textContent);
      expect(texts.some((t) => t.includes('Respuesta del bot'))).toBe(true);
    });
  });

  // ==========================================================
  // 5. UI básica
  // ==========================================================

  describe('UI básica', () => {
    it('bubble y window tienen las clases correctas', async () => {
      mockFetch({});
      runWidget({ 'data-bot-public-id': 'test-id' });
      await new Promise((r) => setTimeout(r, 10));

      const bubble = document.getElementById('nuvora-bubble');
      const win = document.getElementById('nuvora-window');
      expect(bubble).toBeTruthy();
      expect(win).toBeTruthy();
    });

    it('close oculta la ventana', async () => {
      mockFetch({});
      runWidget({ 'data-bot-public-id': 'test-id' });
      await new Promise((r) => setTimeout(r, 10));

      const win = document.getElementById('nuvora-window');
      const close = document.getElementById('nuvora-close');

      // Simular abierto
      win.classList.add('active');
      expect(win.classList.contains('active')).toBe(true);

      close.click();
      expect(win.classList.contains('active')).toBe(false);
    });
  });
});
