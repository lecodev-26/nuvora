(function() {
  const botId = document.currentScript.getAttribute('data-bot-id');
  const API_URL = 'https://nuvora-api-1hql.onrender.com/ask/';

  // Estilos
  const style = document.createElement('style');
  style.innerHTML = `
    #nuvora-bubble { position: fixed; bottom: 20px; right: 20px; width: 60px; height: 60px; border-radius: 50%; background: linear-gradient(135deg, #00C6FF, #7B5CFF, #FF4ECD); display:flex; align-items:center; justify-content:center; cursor:pointer; box-shadow: 0 8px 24px rgba(123,92,255,0.4); z-index: 99999; transition: transform 0.2s; }
    #nuvora-bubble:hover { transform: scale(1.05); }
    #nuvora-window { position: fixed; bottom: 90px; right: 20px; width: 360px; height: 480px; background: #0A0A14; border: 1px solid rgba(255,255,255,0.1); border-radius: 20px; display: none; flex-direction: column; overflow: hidden; z-index: 99999; box-shadow: 0 20px 60px rgba(0,0,0,0.5); font-family: Inter, sans-serif; }
    #nuvora-header { background: linear-gradient(90deg, #00C6FF, #7B5CFF, #FF4ECD); padding: 16px; color: white; font-weight: 600; display:flex; justify-content:space-between; align-items:center; }
    #nuvora-header img { height: 24px; vertical-align: middle; margin-right: 8px; border-radius: 4px; }
    #nuvora-messages { flex:1; overflow-y:auto; padding: 16px; display:flex; flex-direction:column; gap:10px; background: #0A0A14; }
    .n-msg { max-width: 80%; padding: 10px 14px; border-radius: 16px; font-size: 14px; line-height:1.4; }
    .n-bot { background: rgba(255,255,255,0.08); color: white; align-self:flex-start; border-bottom-left-radius: 4px; }
    .n-user { background: linear-gradient(90deg, #00C6FF, #7B5CFF); color: white; align-self:flex-end; border-bottom-right-radius: 4px; }
    #nuvora-input-area { padding: 12px; border-top: 1px solid rgba(255,255,255,0.1); display:flex; gap:8px; background: #0A0A14; }
    #nuvora-input { flex:1; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 999px; padding: 10px 16px; color: white; outline:none; font-size:14px; }
    #nuvora-send { background: linear-gradient(90deg, #00C6FF, #FF4ECD); border:none; border-radius: 999px; padding: 10px 18px; color:white; font-weight:600; cursor:pointer; }
    .n-quick { display:flex; gap:6px; flex-wrap:wrap; margin-top:4px; }
    .n-chip { background: rgba(123,92,255,0.15); border: 1px solid rgba(123,92,255,0.3); color: #A5B4FF; padding: 6px 12px; border-radius: 999px; font-size:12px; cursor:pointer; }
  `;
  document.head.appendChild(style);

  // HTML
  const bubble = document.createElement('div');
  bubble.id = 'nuvora-bubble';
  bubble.innerHTML = `<img src="https://raw.githubusercontent.com/lecodev-26/nuvora/main/assets/logo.png" style="width: 36px; height: 36px; border-radius: 50%; object-fit: cover;">`;

  const win = document.createElement('div');
  win.id = 'nuvora-window';
  win.innerHTML = `
    <div id="nuvora-header">
      <img src="https://raw.githubusercontent.com/lecodev-26/nuvora/main/assets/logo.png" alt="Nuvora">
      <span>Nuvora Bot</span>
      <span id="nuvora-close" style="cursor:pointer;">✕</span>
    </div>
    <div id="nuvora-messages">
      <div class="n-msg n-bot">¡Hola! Soy tu asistente inteligente, ¿en qué puedo ayudarte hoy?</div>
      <div class="n-quick">
        <span class="n-chip" data-q="Ver menú">Ver menú</span>
        <span class="n-chip" data-q="Reservar mesa">Reservar mesa</span>
        <span class="n-chip" data-q="Horario">Horario</span>
      </div>
    </div>
    <div id="nuvora-input-area">
      <input id="nuvora-input" placeholder="Escribe tu pregunta..." />
      <button id="nuvora-send">Enviar</button>
    </div>
  `;
  document.body.appendChild(bubble);
  document.body.appendChild(win);

  // Lógica
  const messagesEl = win.querySelector('#nuvora-messages');
  const inputEl = win.querySelector('#nuvora-input');

  function addMsg(text, who) {
    const d = document.createElement('div');
    d.className = `n-msg n-${who}`;
    d.textContent = text;
    messagesEl.appendChild(d);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  async function sendMessage(text) {
    if(!text.trim()) return;
    addMsg(text, 'user');
    inputEl.value = '';

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bot_id: parseInt(botId), question: text })
      });
      const data = await res.json();
      addMsg(data.answer || 'No tengo esa información.', 'bot');
    } catch {
      addMsg('Hubo un error. Intenta de nuevo.', 'bot');
    }
  }

  bubble.onclick = () => { win.style.display = win.style.display === 'flex'? 'none' : 'flex'; };
  win.querySelector('#nuvora-close').onclick = () => win.style.display = 'none';
  win.querySelector('#nuvora-send').onclick = () => sendMessage(inputEl.value);
  inputEl.onkeydown = e => { if(e.key==='Enter') sendMessage(inputEl.value); };
  win.querySelectorAll('.n-chip').forEach(c => c.onclick = () => sendMessage(c.dataset.q));
})();

