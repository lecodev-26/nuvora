// Nuvora Widget - Chatbot para restaurantes
(function() {
    // Configuración
    const API_URL = 'http://localhost:8000';
    // Obtener bot_id del atributo data-bot-id del script
const scriptTag = document.currentScript;
const BOT_ID = scriptTag ? parseInt(scriptTag.getAttribute('data-bot-id')) || 1 : 1;

    // Crear estilos del widget
    const styles = `
        #nuvora-widget {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
            font-family: Arial, sans-serif;
        }
        #nuvora-toggle {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: #6C63FF;
            color: white;
            border: none;
            font-size: 28px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            transition: all 0.3s;
        }
        #nuvora-toggle:hover {
            transform: scale(1.1);
        }
        #nuvora-chat {
            display: none;
            position: absolute;
            bottom: 80px;
            right: 0;
            width: 350px;
            height: 450px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
            overflow: hidden;
            flex-direction: column;
        }
        #nuvora-chat.active {
            display: flex;
        }
        #nuvora-header {
            background: #6C63FF;
            color: white;
            padding: 15px;
            font-weight: bold;
            font-size: 16px;
            text-align: center;
        }
        #nuvora-messages {
            flex: 1;
            padding: 15px;
            overflow-y: auto;
            background: #f5f5f5;
        }
        .nuvora-message {
            margin-bottom: 10px;
            padding: 10px 14px;
            border-radius: 12px;
            max-width: 85%;
            word-wrap: break-word;
        }
        .nuvora-message.user {
            background: #6C63FF;
            color: white;
            margin-left: auto;
        }
        .nuvora-message.bot {
            background: white;
            color: #333;
            border: 1px solid #ddd;
        }
        #nuvora-input-area {
            display: flex;
            padding: 10px;
            border-top: 1px solid #ddd;
            background: white;
        }
        #nuvora-input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 20px;
            outline: none;
            font-size: 14px;
        }
        #nuvora-send {
            background: #6C63FF;
            color: white;
            border: none;
            border-radius: 20px;
            padding: 10px 20px;
            margin-left: 10px;
            cursor: pointer;
            font-weight: bold;
        }
        #nuvora-send:hover {
            background: #5a52d5;
        }
        .nuvora-typing {
            color: #999;
            font-style: italic;
            padding: 10px 14px;
        }
#nuvora-header {
    background: #6C63FF;
    color: white;
    padding: 15px;
    font-weight: bold;
    font-size: 16px;
    text-align: center;
    border-bottom: 3px solid #5a52d5;
}

#nuvora-messages {
    flex: 1;
    padding: 15px;
    overflow-y: auto;
    background: #f5f5f5;
    min-height: 200px;
    max-height: 350px;
}

.nuvora-message {
    margin-bottom: 10px;
    padding: 10px 14px;
    border-radius: 12px;
    max-width: 85%;
    word-wrap: break-word;
    animation: nuvora-fade-in 0.3s ease;
}

@keyframes nuvora-fade-in {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
    `;

    // Inyectar estilos
    const styleTag = document.createElement('style');
    styleTag.textContent = styles;
    document.head.appendChild(styleTag);

    // Crear estructura HTML
    const widget = document.createElement('div');
    widget.id = 'nuvora-widget';
    widget.innerHTML = `
        <div id="nuvora-chat">
            <div id="nuvora-header">💬 Nuvora Bot</div>
            <div id="nuvora-messages">
                <div class="nuvora-message bot">¡Hola! Soy el asistente del restaurante. ¿En qué puedo ayudarte?</div>
            </div>
            <div id="nuvora-input-area">
                <input id="nuvora-input" placeholder="Escribe tu pregunta...">
                <button id="nuvora-send">Enviar</button>
            </div>
        </div>
        <button id="nuvora-toggle">💬</button>
    `;
    document.body.appendChild(widget);

    // Referencias a elementos
    const chat = document.getElementById('nuvora-chat');
    const toggle = document.getElementById('nuvora-toggle');
    const input = document.getElementById('nuvora-input');
    const sendBtn = document.getElementById('nuvora-send');
    const messages = document.getElementById('nuvora-messages');

    // Toggle chat
    toggle.addEventListener('click', () => {
        chat.classList.toggle('active');
    });

    // Enviar mensaje
    function sendMessage() {
        const text = input.value.trim();
        if (!text) return;

        // Mostrar mensaje del usuario
        const userMsg = document.createElement('div');
        userMsg.className = 'nuvora-message user';
        userMsg.textContent = text;
        messages.appendChild(userMsg);
        input.value = '';
        messages.scrollTop = messages.scrollHeight;

        // Mostrar indicador de "escribiendo"
        const typing = document.createElement('div');
        typing.className = 'nuvora-typing';
        typing.textContent = 'Escribiendo...';
        messages.appendChild(typing);
        messages.scrollTop = messages.scrollHeight;

        // Llamar a la API
        fetch(`${API_URL}/ask/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                bot_id: BOT_ID,
                question: text
            })
        })
        .then(response => response.json())
        .then(data => {
            // Quitar indicador de escritura
            messages.removeChild(typing);

            // Mostrar respuesta del bot
            const botMsg = document.createElement('div');
            botMsg.className = 'nuvora-message bot';
            botMsg.textContent = data.answer;
            messages.appendChild(botMsg);
            messages.scrollTop = messages.scrollHeight;
        })
        .catch(error => {
            messages.removeChild(typing);
            const errorMsg = document.createElement('div');
            errorMsg.className = 'nuvora-message bot';
            errorMsg.textContent = 'Lo siento, hubo un error. Intenta de nuevo.';
            messages.appendChild(errorMsg);
            messages.scrollTop = messages.scrollHeight;
            console.error('Error:', error);
        });
    }

    // Eventos
    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
})();
