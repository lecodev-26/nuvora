import React, { useState, useRef, useEffect } from 'react';

/**
 * PublicChat — Componente de chat público.
 *
 * Props:
 *   - messages: array de { role: 'user'|'bot', text: string }
 *   - onSend: (text) => void
 *   - sending: boolean (indicando que se está enviando)
 *   - disabled: boolean
 *   - welcomeMessage: texto de bienvenida inicial
 *   - placeholder: placeholder del input
 */

const PublicChat = ({
  messages = [],
  onSend,
  sending = false,
  disabled = false,
  welcomeMessage,
  placeholder = 'Escribe un mensaje...',
}) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll al final
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView?.({ behavior: 'smooth' });
  }, [messages, sending]);

  // Focus al montar
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSend = () => {
    const text = input.trim();
    if (!text || sending || disabled) return;
    onSend(text);
    setInput('');
    inputRef.current?.focus();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Área de mensajes */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {/* Welcome message (siempre visible al principio) */}
        {welcomeMessage && messages.length === 0 && (
          <div className="flex justify-start">
            <div className="bg-white/10 text-white/90 rounded-2xl rounded-bl-md px-4 py-2.5 max-w-[85%] text-sm leading-relaxed">
              {welcomeMessage}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div
            key={i}
            className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`
                max-w-[85%] px-4 py-2.5 text-sm leading-relaxed rounded-2xl break-words
                ${m.role === 'user'
                  ? 'bg-gradient-to-r from-cyan-500 to-violet-500 text-white rounded-br-md'
                  : 'bg-white/10 text-white/90 rounded-bl-md'}
              `}
            >
              {m.text}
            </div>
          </div>
        ))}

        {sending && (
          <div className="flex justify-start">
            <div className="bg-white/10 rounded-2xl rounded-bl-md px-4 py-3 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-3 border-t border-white/10 flex gap-2 shrink-0">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={sending || disabled}
          maxLength={2000}
          className="flex-1 bg-white/5 border border-white/10 rounded-full px-4 py-2.5 text-white text-sm placeholder-white/30 focus:outline-none focus:border-violet-500/60 focus:bg-white/10 transition-colors disabled:opacity-50"
        />
        <button
          type="button"
          onClick={handleSend}
          disabled={!input.trim() || sending || disabled}
          className="px-5 py-2.5 rounded-full bg-gradient-to-r from-cyan-500 to-violet-500 text-white text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed hover:shadow-glow active:scale-95 transition-all"
        >
          Enviar
        </button>
      </div>
    </div>
  );
};

export default PublicChat;
