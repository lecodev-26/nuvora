(function() {
  // ============================================================
  // CONFIGURACIÓN
  // ============================================================
  const scriptTag = document.currentScript;

  // Dual mode:
  //   data-bot-public-id="uuid"  → nuevo (14.9) /public/*
  //   data-bot-id="9"            → legacy (compatibilidad) /ask/public
  const publicId = scriptTag ? scriptTag.getAttribute('data-bot-public-id') : null;
  const legacyBotId = scriptTag ? parseInt(scriptTag.getAttribute('data-bot-id')) || null : null;

  const isPublicMode = !!publicId;

  if (!isPublicMode && !legacyBotId) {
    console.error('❌ Nuvora Widget: falta data-bot-public-id o data-bot-id');
    return;
  }

  const API_URL = 'https://nuvora-api-1hql.onrender.com';
  const LOGO_URL = 'https://raw.githubusercontent.com/lecodev-26/nuvora/main/assets/logo.png';

  // Fallback si el server no devuelve config visual
  const DEFAULT_CONFIG = {
    welcome_message: '¡Hola! 👋 ¿En qué puedo ayudarte?',
    placeholder: 'Escribe un mensaje...',
    primary_color: null,
    avatar_url: null,
    show_branding: true,
  };

  // ============================================================
  // SESSION ID
  // ============================================================
  function generateSessionKey() {
    return 'nuvora_session_' + (publicId || legacyBotId);
  }
  const SESSION_STORAGE_KEY = generateSessionKey();
  let sessionId = sessionStorage.getItem(SESSION_STORAGE_KEY);

  // ============================================================
  // ESTILOS
  // ============================================================
  const style = document.createElement('style');
  style.innerHTML = `
    #nuvora-bubble {
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: linear-gradient(135deg, #00C6FF, #7B5CFF, #FF4ECD);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      box-shadow: 0 8px 32px rgba(123, 92, 255, 0.5);
      z-index: 99999;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      border: none;
      animation: nuvora-pulse 3s ease-in-out infinite;
    }
    #nuvora-bubble:hover {
      transform: scale(1.08);
      box-shadow: 0 12px 48px rgba(123, 92, 255, 0.7);
    }
    #nuvora-bubble img {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      object-fit: cover;
      border: 2px solid rgba(255,255,255,0.3);
    }
    @keyframes nuvora-pulse {
      0%, 100% { box-shadow: 0 8px 32px rgba(123, 92, 255, 0.4); }
      50% { box-shadow: 0 8px 48px rgba(123, 92, 255, 0.7); }
    }

    #nuvora-window {
      position: fixed;
      bottom: 96px;
      right: 24px;
      width: 380px;
      height: 520px;
      max-height: calc(100vh - 120px);
      background: #0A0A14;
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 20px;
      display: none;
      flex-direction: column;
      overflow: hidden;
      z-index: 99999;
      box-shadow: 0 24px 64px rgba(0,0,0,0.6);
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      animation: nuvora-slide-up 0.3s ease;
    }
    #nuvora-window.active { display: flex; }
    @keyframes nuvora-slide-up {
      from { opacity: 0; transform: translateY(20px) scale(0.95); }
      to { opacity: 1; transform: translateY(0) scale(1); }
    }

    #nuvora-header {
      background: linear-gradient(135deg, #00C6FF, #7B5CFF, #FF4ECD);
      padding: 16px 20px;
      display: flex;
      align-items: center;
      gap: 12px;
      flex-shrink: 0;
    }
    #nuvora-header img {
      width: 36px;
      height: 36px;
      border-radius: 10px;
      object-fit: cover;
      border: 2px solid rgba(255,255,255,0.2);
    }
    #nuvora-header-avatar {
      width: 36px;
      height: 36px;
      border-radius: 10px;
      background: rgba(255,255,255,0.2);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-weight: 700;
      font-size: 16px;
      border: 2px solid rgba(255,255,255,0.2);
    }
    #nuvora-header-info { flex: 1; min-width: 0; }
    #nuvora-header-info .name {
      font-weight: 700;
      font-size: 15px;
      color: white;
      line-height: 1.2;
    }
    #nuvora-header-info .status {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      color: rgba(255,255,255,0.8);
    }
    #nuvora-header-info .status .dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #34D399;
      animation: nuvora-dot-pulse 1.5s ease-in-out infinite;
    }
    @keyframes nuvora-dot-pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.5; transform: scale(0.8); }
    }
    #nuvora-close {
      cursor: pointer;
      color: rgba(255,255,255,0.7);
      font-size: 18px;
      line-height: 1;
      padding: 4px 8px;
      border-radius: 8px;
      transition: all 0.2s;
      background: none;
      border: none;
    }
    #nuvora-close:hover {
      background: rgba(255,255,255,0.15);
      color: white;
    }

    #nuvora-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px 20px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      background: #0A0A14;
    }
    #nuvora-messages::-webkit-scrollbar { width: 4px; }
    #nuvora-messages::-webkit-scrollbar-track { background: rgba(255,255,255,0.03); }
    #nuvora-messages::-webkit-scrollbar-thumb {
      background: linear-gradient(135deg, #00C6FF, #7B5CFF);
      border-radius: 10px;
    }

    .n-msg {
      max-width: 85%;
      padding: 10px 16px;
      border-radius: 16px;
      font-size: 14px;
      line-height: 1.5;
      word-wrap: break-word;
      animation: nuvora-msg-in 0.3s ease;
    }
    @keyframes nuvora-msg-in {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .n-msg.n-bot {
      background: rgba(255,255,255,0.06);
      color: #E8E8E8;
      align-self: flex-start;
      border-bottom-left-radius: 4px;
      border: 1px solid rgba(255,255,255,0.04);
    }
    .n-msg.n-user {
      background: linear-gradient(135deg, #00C6FF, #7B5CFF);
      color: white;
      align-self: flex-end;
      border-bottom-right-radius: 4px;
    }
    .n-msg.n-bot .highlight { color: #00C6FF; font-weight: 500; }

    .n-quick {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 4px;
      margin-left: 8px;
    }
    .n-chip {
      background: rgba(123, 92, 255, 0.12);
      border: 1px solid rgba(123, 92, 255, 0.2);
      color: #A5B4FF;
      padding: 6px 14px;
      border-radius: 9999px;
      font-size: 12px;
      cursor: pointer;
      transition: all 0.2s;
      user-select: none;
    }
    .n-chip:hover {
      background: rgba(123, 92, 255, 0.25);
      border-color: rgba(123, 92, 255, 0.4);
      color: white;
      transform: scale(1.02);
    }

    #nuvora-input-area {
      padding: 12px 16px 16px;
      border-top: 1px solid rgba(255,255,255,0.05);
      display: flex;
      gap: 8px;
      background: #0A0A14;
      flex-shrink: 0;
    }
    #nuvora-input {
      flex: 1;
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 9999px;
      padding: 10px 16px;
      color: white;
      outline: none;
      font-size: 14px;
      font-family: inherit;
      transition: all 0.2s;
    }
    #nuvora-input::placeholder { color: rgba(255,255,255,0.3); }
    #nuvora-input:focus {
      border-color: rgba(123, 92, 255, 0.5);
      background: rgba(255,255,255,0.08);
      box-shadow: 0 0 0 3px rgba(123, 92, 255, 0.15);
    }
    #nuvora-send {
      background: linear-gradient(135deg, #00C6FF, #7B5CFF);
      border: none;
      border-radius: 9999px;
      padding: 10px 20px;
      color: white;
      font-weight: 600;
      font-size: 14px;
      cursor: pointer;
      transition: all 0.2s;
      font-family: inherit;
      flex-shrink: 0;
    }
    #nuvora-send:hover {
      transform: scale(1.04);
      box-shadow: 0 4px 20px rgba(123, 92, 255, 0.4);
    }
    #nuvora-send:active { transform: scale(0.96); }
    #nuvora-send:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }

    .n-typing {
      display: flex;
      align-items: center;
      gap: 4px;
      padding: 10px 16px;
      background: rgba(255,255,255,0.06);
      border-radius: 16px;
      border-bottom-left-radius: 4px;
      align-self: flex-start;
      border: 1px solid rgba(255,255,255,0.04);
    }
    .n-typing span {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: rgba(255,255,255,0.4);
      display: inline-block;
      animation: nuvora-typing-bounce 1.4s infinite ease-in-out both;
    }
    .n-typing span:nth-child(1) { animation-delay: -0.32s; }
    .n-typing span:nth-child(2) { animation-delay: -0.16s; }
    .n-typing span:nth-child(3) { animation-delay: 0s; }
    @keyframes nuvora-typing-bounce {
      0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
      40% { transform: scale(1); opacity: 1; }
    }

    #nuvora-branding {
      padding: 8px 16px;
      border-top: 1px solid rgba(255,255,255,0.05);
      text-align: center;
      font-size: 11px;
      color: rgba(255,255,255,0.4);
    }
    #nuvora-branding a {
      color: rgba(255,255,255,0.5);
      text-decoration: none;
    }
    #nuvora-branding a:hover { color: rgba(255,255,255,0.7); }

    @media (max-width: 480px) {
      #nuvora-window {
        right: 12px;
        bottom: 80px;
        width: calc(100vw - 24px);
        height: calc(100vh - 100px);
        max-height: calc(100vh - 100px);
        border-radius: 16px;
      }
      #nuvora-bubble { bottom: 16px; right: 16px; width: 56px; height: 56px; }
      #nuvora-bubble img { width: 28px; height: 28px; }
      #nuvora-header { padding: 14px 16px; }
      #nuvora-messages { padding: 12px 16px; }
      .n-msg { font-size: 13px; padding: 8px 14px; }
      #nuvora-input-area { padding: 10px 12px 12px; }
      #nuvora-input { font-size: 13px; padding: 8px 14px; }
      #nuvora-send { font-size: 13px; padding: 8px 16px; }
    }
  `;
  document.head.appendChild(style);

  // ============================================================
  // HTML
  // ============================================================
  const bubble = document.createElement('div');
  bubble.id = 'nuvora-bubble';
  bubble.innerHTML = `<img src="${LOGO_URL}" alt="Nuvora">`;
  document.body.appendChild(bubble);

  const win = document.createElement('div');
  win.id = 'nuvora-window';
  win.innerHTML = `
    <div id="nuvora-header">
      <div id="nuvora-header-avatar">N</div>
      <div id="nuvora-header-info">
        <div class="name" id="nuvora-business-name">Asistente Nuvora</div>
        <div class="status"><span class="dot"></span> En línea</div>
      </div>
      <button id="nuvora-close">✕</button>
    </div>
    <div id="nuvora-messages">
      <div class="n-msg n-bot" id="nuvora-greeting">¡Hola! 👋 Soy el asistente de <span class="highlight">tu negocio</span>. ¿En qué puedo ayudarte hoy?</div>
    </div>
    <div id="nuvora-input-area">
      <input id="nuvora-input" placeholder="Escribe tu pregunta..." autofocus>
      <button id="nuvora-send">Enviar</button>
    </div>
    <div id="nuvora-branding" style="display: none;">
      <a href="https://nuvora-chi.vercel.app" target="_blank" rel="noopener">✨ Powered by Nuvora</a>
    </div>
  `;
  document.body.appendChild(win);

  // ============================================================
  // REFERENCIAS
  // ============================================================
  const messagesEl = win.querySelector('#nuvora-messages');
  const inputEl = win.querySelector('#nuvora-input');
  const sendBtn = win.querySelector('#nuvora-send');
  const closeBtn = win.querySelector('#nuvora-close');
  const greetingEl = win.querySelector('#nuvora-greeting');
  const businessNameEl = win.querySelector('#nuvora-business-name');
  const headerAvatar = win.querySelector('#nuvora-header-avatar');
  const brandingEl = win.querySelector('#nuvora-branding');

  // ============================================================
  // CARGAR DATOS DEL BOT
  // ============================================================
  let botConfig = { ...DEFAULT_CONFIG };

  async function loadBotData() {
    try {
      if (isPublicMode) {
        // NUEVO modo: /public/bots/{public_id}
        const res = await fetch(`${API_URL}/public/bots/${encodeURIComponent(publicId)}`);
        if (res.ok) {
          const data = await res.json();
          const cfg = data.config || {};

          businessNameEl.textContent = data.business_name || data.name || 'Asistente Nuvora';

          botConfig = {
            welcome_message: cfg.welcome_message || DEFAULT_CONFIG.welcome_message,
            placeholder: cfg.placeholder || DEFAULT_CONFIG.placeholder,
            primary_color: cfg.primary_color || null,
            avatar_url: cfg.avatar_url || null,
            show_branding: cfg.show_branding !== false,
          };

          // Aplicar color al header
          if (botConfig.primary_color) {
            const header = win.querySelector('#nuvora-header');
            header.style.background = `linear-gradient(135deg, ${botConfig.primary_color}, ${botConfig.primary_color}dd)`;
          }

          // Aplicar avatar
          if (botConfig.avatar_url) {
            headerAvatar.style.backgroundImage = `url(${botConfig.avatar_url})`;
            headerAvatar.style.backgroundSize = 'cover';
            headerAvatar.style.backgroundPosition = 'center';
            headerAvatar.textContent = '';
          } else {
            headerAvatar.textContent = (data.business_name || data.name || 'N')[0].toUpperCase();
          }

          // Aplicar welcome
          greetingEl.innerHTML = `¡Hola! 👋 Soy el asistente de <span class="highlight">${data.business_name || data.name || 'tu negocio'}</span>. ¿En qué puedo ayudarte hoy?`;
          if (botConfig.welcome_message) {
            greetingEl.textContent = botConfig.welcome_message;
          }

          // Aplicar placeholder
          inputEl.placeholder = botConfig.placeholder;

          // Aplicar branding
          brandingEl.style.display = botConfig.show_branding ? 'block' : 'none';

          // Crear sesión
          await ensurePublicSession();
        } else {
          // 404 → bot no existe o no publicado
          console.warn('Nuvora Widget: bot no encontrado o no publicado');
        }
      } else {
        // MODO LEGACY: /bots/{botId}/public
        const res = await fetch(`${API_URL}/bots/${legacyBotId}/public`);
        if (res.ok) {
          const data = await res.json();
          businessNameEl.textContent = `Asistente de ${data.business_name || data.restaurant_name || data.name || 'Nuvora'}`;
          headerAvatar.textContent = (data.business_name || data.name || 'N')[0].toUpperCase();
        }
      }
    } catch (error) {
      console.log('Nuvora Widget: error cargando datos del bot', error);
    }
  }

  // ============================================================
  // SESIÓN PÚBLICA (solo modo public)
  // ============================================================
  async function ensurePublicSession() {
    if (sessionId) return sessionId;

    try {
      const res = await fetch(`${API_URL}/public/bots/${encodeURIComponent(publicId)}/session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      if (res.ok) {
        const data = await res.json();
        sessionId = data.session_id;
        sessionStorage.setItem(SESSION_STORAGE_KEY, sessionId);
      }
    } catch (error) {
      console.error('Nuvora Widget: error creando sesión', error);
    }
    return sessionId;
  }

  // ============================================================
  // MENSAJES
  // ============================================================
  function addMessage(text, who) {
    const d = document.createElement('div');
    d.className = `n-msg n-${who}`;
    d.textContent = text;
    messagesEl.appendChild(d);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function showTyping() {
    const typing = document.createElement('div');
    typing.className = 'n-typing';
    typing.innerHTML = '<span></span><span></span><span></span>';
    typing.id = 'nuvora-typing';
    messagesEl.appendChild(typing);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function hideTyping() {
    const typing = document.getElementById('nuvora-typing');
    if (typing) typing.remove();
  }

  async function sendMessage(text) {
    if (!text.trim()) return;

    addMessage(text, 'user');
    inputEl.value = '';
    sendBtn.disabled = true;
    showTyping();

    try {
      if (isPublicMode) {
        // Asegurar sesión activa
        if (!sessionId) await ensurePublicSession();

        const res = await fetch(`${API_URL}/public/bots/${encodeURIComponent(publicId)}/message`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: sessionId, message: text }),
        });

        // Si la sesión expiró, crear nueva y reintentar 1 vez
        if (res.status === 404) {
          sessionStorage.removeItem(SESSION_STORAGE_KEY);
          sessionId = null;
          await ensurePublicSession();

          const retry = await fetch(`${API_URL}/public/bots/${encodeURIComponent(publicId)}/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, message: text }),
          });
          const retryData = await retry.json();
          hideTyping();
          addMessage(retryData.reply || 'Error', 'bot');
          sendBtn.disabled = false;
          inputEl.focus();
          return;
        }

        const data = await res.json();
        hideTyping();
        addMessage(data.reply || 'Sin respuesta', 'bot');
      } else {
        // MODO LEGACY
        const res = await fetch(`${API_URL}/ask/public`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            bot_id: legacyBotId,
            question: text,
            session_id: sessionId || undefined,
          }),
        });
        const data = await res.json();
        hideTyping();
        addMessage(data.answer || 'No tengo esa información en mi memoria.', 'bot');
      }
    } catch (error) {
      hideTyping();
      console.error('Nuvora Widget error:', error);
      addMessage('Hubo un error al procesar tu pregunta. Inténtalo de nuevo.', 'bot');
    }

    sendBtn.disabled = false;
    inputEl.focus();
  }

  // ============================================================
  // EVENTOS
  // ============================================================
  bubble.onclick = () => {
    win.classList.toggle('active');
    if (win.classList.contains('active')) inputEl.focus();
  };

  closeBtn.onclick = () => win.classList.remove('active');
  sendBtn.onclick = () => sendMessage(inputEl.value);
  inputEl.onkeydown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      sendMessage(inputEl.value);
    }
  };

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && win.classList.contains('active')) {
      win.classList.remove('active');
    }
  });

  // ============================================================
  // INICIALIZAR
  // ============================================================
  loadBotData();

  console.log(
    `✅ Nuvora Widget cargado — Modo: ${isPublicMode ? 'PÚBLICO' : 'LEGACY'} | ` +
    `${isPublicMode ? `public_id=${publicId}` : `bot_id=${legacyBotId}`}`
  );
})();
