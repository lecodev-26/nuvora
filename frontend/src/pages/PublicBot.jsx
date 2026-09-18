import React, { useEffect, useState, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { publicApi } from '../services/publicApi';
import PublicHeader from '../components/public/PublicHeader';
import PublicChat from '../components/public/PublicChat';
import PublicFooter from '../components/public/PublicFooter';

/**
 * PublicBot — Página pública del bot.
 *
 * Ruta: /b/:identifier
 *   identifier puede ser public_slug ("clinica-salud") o public_id (UUID).
 *
 * SIN login. SIN sidebar. SIN acceso al panel.
 * Solo: cargar bot + conversar.
 */

const SESSION_STORAGE_KEY_PREFIX = 'nuvora_public_session_';

const PublicBot = () => {
  const { identifier } = useParams();

  const [botInfo, setBotInfo] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sending, setSending] = useState(false);
  const [notFound, setNotFound] = useState(false);

  // ============================================================
  // CARGA INICIAL: bot + sesión
  // ============================================================
  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      setError(null);
      setNotFound(false);

      try {
        // 1. Cargar info del bot
        const res = await publicApi.getBot(identifier);
        if (cancelled) return;
        setBotInfo(res.data);

        // 2. Recuperar sesión existente (si hay)
        const key = SESSION_STORAGE_KEY_PREFIX + identifier;
        let sid = sessionStorage.getItem(key);

        // 3. Crear sesión si no hay
        if (!sid) {
          const sres = await publicApi.createSession(identifier);
          if (cancelled) return;
          sid = sres.data.session_id;
          sessionStorage.setItem(key, sid);
        }
        setSessionId(sid);

        setLoading(false);
      } catch (err) {
        if (cancelled) return;
        if (err.response?.status === 404) {
          setNotFound(true);
        } else {
          setError(
            err.response?.data?.detail ||
            err.message ||
            'Error cargando el bot'
          );
        }
        setLoading(false);
      }
    };

    load();
    return () => { cancelled = true; };
  }, [identifier]);

  // ============================================================
  // ENVIAR MENSAJE
  // ============================================================
  const handleSend = useCallback(async (text) => {
    if (!text.trim() || sending || !sessionId) return;

    const userMsg = { role: 'user', text };
    setMessages((prev) => [...prev, userMsg]);
    setSending(true);

    try {
      const res = await publicApi.sendMessage(identifier, sessionId, text);
      const botMsg = { role: 'bot', text: res.data.reply };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      // Si la sesión expiró (404), crear nueva y reintentar 1 vez
      if (err.response?.status === 404) {
        try {
          sessionStorage.removeItem(SESSION_STORAGE_KEY_PREFIX + identifier);
          const sres = await publicApi.createSession(identifier);
          const newSid = sres.data.session_id;
          sessionStorage.setItem(SESSION_STORAGE_KEY_PREFIX + identifier, newSid);
          setSessionId(newSid);

          const retry = await publicApi.sendMessage(identifier, newSid, text);
          setMessages((prev) => [...prev, { role: 'bot', text: retry.data.reply }]);
          setSending(false);
          return;
        } catch (retryErr) {
          setMessages((prev) => [
            ...prev,
            { role: 'bot', text: 'Lo siento, ha ocurrido un error. Inténtalo de nuevo.' },
          ]);
          setSending(false);
          return;
        }
      }

      const errMsg = err.response?.data?.detail || 'Error al enviar el mensaje';
      setMessages((prev) => [...prev, { role: 'bot', text: errMsg }]);
    } finally {
      setSending(false);
    }
  }, [identifier, sessionId, sending]);

  // ============================================================
  // RENDER: loading
  // ============================================================
  if (loading) {
    return (
      <div className="min-h-screen bg-navy flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 rounded-full border-2 border-white/20 border-t-cyan-400 animate-spin" />
          <div className="text-white/50 text-sm">Cargando...</div>
        </div>
      </div>
    );
  }

  // ============================================================
  // RENDER: not found
  // ============================================================
  if (notFound) {
    return (
      <div className="min-h-screen bg-navy flex flex-col items-center justify-center gap-4 p-6 text-center">
        <div className="text-6xl">🔍</div>
        <div className="text-white text-xl font-semibold">Bot no encontrado</div>
        <div className="text-white/50 text-sm max-w-md">
          El bot que buscas no existe o no está publicado.
        </div>
        <a
          href="/"
          className="mt-2 text-cyan-400 hover:text-cyan-300 text-sm underline"
        >
          Ir a Nuvora →
        </a>
      </div>
    );
  }

  // ============================================================
  // RENDER: error
  // ============================================================
  if (error) {
    return (
      <div className="min-h-screen bg-navy flex flex-col items-center justify-center gap-4 p-6 text-center">
        <div className="text-5xl">⚠️</div>
        <div className="text-white text-lg font-semibold">Error</div>
        <div className="text-white/50 text-sm max-w-md">{error}</div>
        <button
          onClick={() => window.location.reload()}
          className="mt-2 px-5 py-2 rounded-full bg-white/10 hover:bg-white/20 text-white text-sm transition-colors"
        >
          Reintentar
        </button>
      </div>
    );
  }

  // ============================================================
  // RENDER: chat
  // ============================================================
  const config = botInfo?.config || {};
  const welcomeMessage = config.welcome_message
    || `¡Hola! 👋 Soy el asistente de ${botInfo?.business_name || botInfo?.name || 'este negocio'}. ¿En qué puedo ayudarte?`;
  const placeholder = config.placeholder || 'Escribe un mensaje...';

  return (
    <div className="min-h-screen bg-navy flex items-center justify-center p-0 md:p-6">
      <div className="w-full max-w-md h-screen md:h-[700px] md:max-h-[90vh] bg-black/40 border border-white/10 md:rounded-2xl overflow-hidden flex flex-col shadow-card">
        <PublicHeader
          name={botInfo?.name}
          businessName={botInfo?.business_name}
          avatarUrl={config.avatar_url}
          primaryColor={config.primary_color}
        />

        <PublicChat
          messages={messages}
          onSend={handleSend}
          sending={sending}
          welcomeMessage={messages.length === 0 ? welcomeMessage : null}
          placeholder={placeholder}
        />

        {config.show_branding && <PublicFooter />}
      </div>
    </div>
  );
};

export default PublicBot;
