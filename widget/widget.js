(function() {
  // ============================================================
  // CONFIGURACIÓN
  // ============================================================
  const scriptTag = document.currentScript;
  const botId = scriptTag ? parseInt(scriptTag.getAttribute('data-bot-id')) || 1 : 1;
  const API_URL = 'https://nuvora-api-1hql.onrender.com';

  // Logo de Nuvora
  const LOGO_URL = 'https://raw.githubusercontent.com/lecodev-26/nuvora/main/assets/logo.png';

  // Nichos (datos maestros — deben estar sincronizados con frontend/src/data/nichos.js)
  const NICHOS = {
    restaurantes: {
      icon: '🍽️',
      greeting: '¡Hola! Soy el asistente de {business_name}. ¿En qué puedo ayudarte?',
      quickQuestions: ['Horario', 'Menú', 'Reservas', 'Ubicación', 'Alergenos'],
    },
    peluquerias: {
      icon: '💇',
      greeting: '¡Hola! Soy el asistente de {business_name}. ¿En qué puedo ayudarte?',
      quickQuestions: ['Horario', 'Servicios', 'Precios', 'Reservas', 'Productos'],
    },
    hoteles: {
      icon: '🏨',
      greeting: '¡Hola! Soy el asistente de {business_name}. ¿En qué puedo ayudarte?',
      quickQuestions: ['Horario', 'Habitaciones', 'Precios', 'Servicios', 'Ubicación'],
    },
    gimnasios: {
      icon: '🏋️',
      greeting: '¡Hola! Soy el asistente de {business_name}. ¿En qué puedo ayudarte?',
      quickQuestions: ['Horario', 'Precios', 'Clases', 'Instalaciones', 'Ubicación'],
    },
    clinicas: {
      icon: '🏥',
      greeting: '¡Hola! Soy el asistente de {business_name}. ¿En qué puedo ayudarte?',
      quickQuestions: ['Horario', 'Servicios', 'Citas', 'Ubicación', 'Contacto'],
    },
    tiendas: {
      icon: '🛍️',
      greeting: '¡Hola! Soy el asistente de {business_name}. ¿En qué puedo ayudarte?',
      quickQuestions: ['Horario', 'Productos', 'Precios', 'Envíos', 'Ubicación'],
    },
    otro: {
      icon: '🏪',
      greeting: '¡Hola! Soy el asistente de {business_name}. ¿En qué puedo ayudarte?',
      quickQuestions: ['Horario', 'Servicios', 'Ubicación', 'Contacto'],
    },
  };

  // Session ID para analytics
  function generateSessionId() {
    return 'sess_' + Math.random().toString(36).substring(2, 15) + Date.now().toString(36);
  }
  const sessionId = sessionStorage.getItem('nuvora_session_id') || generateSessionId();
  sessionStorage.setItem('nuvora_session_id', sessionId);

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
      #nuvora-header img { width: 32px; height: 32px; }
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
      <img src="${LOGO_URL}" alt="Nuvora">
      <div id="nuvora-header-info">
        <div class="name" id="nuvora-business-name">Asistente Nuvora</div>
        <div class="status"><span class="dot"></span> En línea</div>
      </div>
      <button id="nuvora-close">✕</button>
    </div>
    <div id="nuvora-messages">
      <div class="n-msg n-bot" id="nuvora-greeting">¡Hola! 👋 Soy el asistente de <span class="highlight">tu negocio</span>. ¿En qué puedo ayudarte hoy?</div>
      <div class="n-quick" id="nuvora-quick-questions"></div>
    </div>
    <div id="nuvora-input-area">
      <input id="nuvora-input" placeholder="Escribe tu pregunta..." autofocus>
      <button id="nuvora-send">Enviar</button>
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
  const quickQuestionsEl = win.querySelector('#nuvora-quick-questions');

  // ============================================================
  // CARGAR DATOS DEL BOT (nombre y nicho)
  // ============================================================
  let botData = { name: 'Asistente Nuvora', nicho_id: 'otro' };

  async function loadBotData() {
    try {
      // Intentar cargar datos del bot desde la API
      const res = await fetch(`${API_URL}/bots/${botId}/public`);
      if (res.ok) {
        const data = await res.json();
        botData = {
          name: data.name || 'Asistente Nuvora',
          restaurant_name: data.restaurant_name || '',
          nicho_id: data.nicho_id || 'otro',
        };
      }
    } catch (error) {
      console.log('Usando datos por defecto del bot');
    }

    // Actualizar nombre del negocio en el header
    if (botData.restaurant_name) {
      businessNameEl.textContent = `Asistente de ${botData.restaurant_name}`;
    } else {
      businessNameEl.textContent = botData.name;
    }

    // Obtener datos del nicho
    const nicho = NICHOS[botData.nicho_id] || NICHOS.otro;

    // Actualizar saludo
    const businessName = botData.restaurant_name || botData.name || 'tu negocio';
    const greeting = nicho.greeting.replace('{business_name}', businessName);
    greetingEl.innerHTML = `¡Hola! 👋 Soy el asistente de <span class="highlight">${businessName}</span>. ¿En qué puedo ayudarte hoy?`;

    // Actualizar preguntas rápidas
    quickQuestionsEl.innerHTML = nicho.quickQuestions
      .map(q => `<span class="n-chip" data-q="${q}">${q}</span>`)
      .join('');

    // Añadir eventos a los chips
    quickQuestionsEl.querySelectorAll('.n-chip').forEach(chip => {
      chip.onclick = () => sendMessage(chip.dataset.q);
    });
  }

  // ============================================================
  // FUNCIONES
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
      const res = await fetch(`${API_URL}/ask/public`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bot_id: botId,
          question: text,
          session_id: sessionId
        })
      });

      const data = await res.json();
      hideTyping();

      const answer = data.answer || 'No tengo esa información en mi memoria. Te recomiendo contactar directamente con el negocio.';
      addMessage(answer, 'bot');

    } catch (error) {
      hideTyping();
      console.error('Error:', error);
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

  console.log(`✅ Nuvora Widget cargado — Bot ID: ${botId} | Session: ${sessionId}`);
})();
