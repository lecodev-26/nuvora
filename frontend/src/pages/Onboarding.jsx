import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useBot } from '../context/BotContext';
import { botService, memoryService, askService } from '../services/api';
import Button from '../components/Button';
import Card from '../components/Card';
import Input from '../components/Input';
import Badge from '../components/Badge';

const LOGO_URL = '/logo.png';

const Onboarding = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { setSelectedBot } = useBot();

  // Estado del onboarding
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [bot, setBot] = useState(null);
  const [memories, setMemories] = useState([]);

  // Paso 1: Crear negocio
  const [botData, setBotData] = useState({
    name: '',
    restaurant_name: '',
    owner_email: user?.email || '',
  });

  // Paso 2: Añadir información
  const [newMemory, setNewMemory] = useState({
    fact: '',
    keyword: '',
  });

  // Paso 3: Probar asistente
  const [question, setQuestion] = useState('');
  const [chatMessages, setChatMessages] = useState([
    { type: 'bot', text: '¡Hola! Soy tu asistente. ¿Qué quieres preguntar?' }
  ]);
  const [isTyping, setIsTyping] = useState(false);

  // ============================================================
  // PASO 1 — CREAR NEGOCIO
  // ============================================================

  const handleCreateBot = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await botService.create({
        name: botData.name,
        restaurant_name: botData.restaurant_name,
        owner_email: botData.owner_email || user?.email,
      });
      setBot(response.data);
      setSelectedBot(response.data);
      setStep(2);
    } catch (error) {
      console.error('Error creando bot:', error);
      alert('Error al crear el bot. Inténtalo de nuevo.');
    }
    setLoading(false);
  };

  // ============================================================
  // PASO 2 — AÑADIR INFORMACIÓN
  // ============================================================

  const handleAddMemory = async (e) => {
    e.preventDefault();
    if (!bot) return;
    setLoading(true);
    try {
      const response = await memoryService.add({
        bot_id: bot.id,
        fact: newMemory.fact,
        keyword: newMemory.keyword,
      });
      setMemories([...memories, response.data]);
      setNewMemory({ fact: '', keyword: '' });
    } catch (error) {
      console.error('Error añadiendo memoria:', error);
      alert('Error al añadir la información. Inténtalo de nuevo.');
    }
    setLoading(false);
  };

  const handleSkipMemories = () => {
    setStep(3);
  };

  // ============================================================
  // PASO 3 — PROBAR ASISTENTE
  // ============================================================

  const handleAskQuestion = async (e) => {
    e.preventDefault();
    if (!bot || !question.trim()) return;

    const userQuestion = question.trim();
    setChatMessages([...chatMessages, { type: 'user', text: userQuestion }]);
    setQuestion('');
    setIsTyping(true);

    try {
      const response = await askService.ask(bot.id, userQuestion);
      const answer = response.data.answer || 'No tengo esa información en mi memoria. Te recomiendo contactar directamente con el restaurante.';
      setChatMessages(prev => [...prev, { type: 'bot', text: answer }]);
    } catch (error) {
      console.error('Error preguntando:', error);
      setChatMessages(prev => [...prev, { type: 'bot', text: 'Hubo un error al procesar tu pregunta. Inténtalo de nuevo.' }]);
    }
    setIsTyping(false);
  };

  const handleFinishOnboarding = () => {
    navigate('/dashboard');
  };

  // ============================================================
  // RENDER
  // ============================================================

  const renderStepIndicator = () => (
    <div className="flex items-center justify-center gap-3 mb-8">
      {[1, 2, 3, 4].map((s) => (
        <div key={s} className="flex items-center gap-3">
          <div
            className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all ${
              s === step
                ? 'bg-gradient-primary text-white shadow-glow'
                : s < step
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'bg-white/10 text-white/30'
            }`}
          >
            {s < step ? '✓' : s}
          </div>
          {s < 4 && (
            <div
              className={`w-12 h-0.5 rounded ${
                s < step ? 'bg-emerald-500/50' : 'bg-white/10'
              }`}
            />
          )}
        </div>
      ))}
    </div>
  );

  const renderStep1 = () => (
    <div className="max-w-md mx-auto animate-fade-in-up">
      <h2 className="text-2xl md:text-3xl font-bold text-center mb-2">
        Crea tu <span className="text-gradient">negocio</span>
      </h2>
      <p className="text-white/50 text-center mb-8">
        Configura tu asistente con los datos básicos de tu negocio.
      </p>

      <form onSubmit={handleCreateBot} className="space-y-4">
        <Input
          label="Nombre del bot"
          placeholder="Ej: Asistente La Marina"
          value={botData.name}
          onChange={(e) => setBotData({ ...botData, name: e.target.value })}
          required
        />
        <Input
          label="Nombre del negocio"
          placeholder="Ej: Restaurante La Marina"
          value={botData.restaurant_name}
          onChange={(e) => setBotData({ ...botData, restaurant_name: e.target.value })}
          required
        />
        <Input
          label="Email del propietario"
          type="email"
          placeholder="tu@email.com"
          value={botData.owner_email}
          onChange={(e) => setBotData({ ...botData, owner_email: e.target.value })}
          required
        />

        <Button type="submit" variant="primary" size="lg" className="w-full" disabled={loading}>
          {loading ? 'Creando...' : 'Crear negocio →'}
        </Button>
      </form>
    </div>
  );

  const renderStep2 = () => (
    <div className="max-w-md mx-auto animate-fade-in-up">
      <h2 className="text-2xl md:text-3xl font-bold text-center mb-2">
        Añade <span className="text-gradient">información</span>
      </h2>
      <p className="text-white/50 text-center mb-8">
        Enséñale a tu asistente lo que necesita saber sobre tu negocio.
      </p>

      <form onSubmit={handleAddMemory} className="space-y-4">
        <Input
          label="Hecho"
          placeholder="Ej: Abrimos de 9:00 a 18:00"
          value={newMemory.fact}
          onChange={(e) => setNewMemory({ ...newMemory, fact: e.target.value })}
          required
        />
        <Input
          label="Palabra clave"
          placeholder="Ej: horario"
          value={newMemory.keyword}
          onChange={(e) => setNewMemory({ ...newMemory, keyword: e.target.value.toLowerCase() })}
          required
        />

        <Button type="submit" variant="secondary" size="md" className="w-full" disabled={loading}>
          {loading ? 'Añadiendo...' : '+ Añadir información'}
        </Button>
      </form>

      {memories.length > 0 && (
        <div className="mt-6">
          <p className="text-sm text-white/50 mb-3">Información añadida ({memories.length}):</p>
          <div className="space-y-2">
            {memories.map((m, i) => (
              <div key={i} className="bg-white/5 rounded-xl px-4 py-2 text-sm flex justify-between">
                <span className="text-white/60">{m.keyword}:</span>
                <span className="text-white/90">{m.fact}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-6 flex gap-3">
        <Button variant="outline" size="md" className="flex-1" onClick={handleSkipMemories}>
          Saltar (más tarde)
        </Button>
        <Button variant="primary" size="md" className="flex-1" onClick={() => setStep(3)}>
          Continuar →
        </Button>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="max-w-2xl mx-auto animate-fade-in-up">
      <h2 className="text-2xl md:text-3xl font-bold text-center mb-2">
        Prueba tu <span className="text-gradient">asistente</span>
      </h2>
      <p className="text-white/50 text-center mb-8">
        Haz una prueba y comprueba cómo responde tu asistente.
      </p>

      <Card className="p-0 overflow-hidden border-white/20">
        {/* Header del chat */}
        <div className="bg-gradient-primary p-4 flex items-center gap-3">
          <img src={LOGO_URL} alt="Nuvora" className="h-8 w-8 rounded-lg object-cover" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-white">{bot?.name || 'Nuvora Bot'}</p>
            <p className="text-xs text-white/70 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              En línea
            </p>
          </div>
        </div>

        {/* Mensajes */}
        <div className="p-4 space-y-3 bg-navy/50 min-h-[300px] max-h-[400px] overflow-y-auto">
          {chatMessages.map((msg, i) => (
            <div
              key={i}
              className={`flex items-start gap-2 ${
                msg.type === 'user' ? 'justify-end' : ''
              }`}
            >
              {msg.type === 'bot' && (
                <div className="w-7 h-7 rounded-full bg-gradient-primary flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
                  N
                </div>
              )}
              <div
                className={`rounded-2xl px-4 py-2.5 text-sm max-w-[80%] ${
                  msg.type === 'user'
                    ? 'bg-gradient-primary text-white rounded-tr-none'
                    : 'bg-white/10 text-white rounded-tl-none'
                }`}
              >
                {msg.text}
              </div>
            </div>
          ))}
          {isTyping && (
            <div className="flex items-start gap-2">
              <div className="w-7 h-7 rounded-full bg-gradient-primary flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
                N
              </div>
              <div className="bg-white/10 rounded-2xl rounded-tl-none px-4 py-3">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-white/50 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 bg-white/50 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 bg-white/50 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <form onSubmit={handleAskQuestion} className="p-4 border-t border-white/5 flex gap-2">
          <input
            type="text"
            placeholder="Escribe tu pregunta..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            className="flex-1 bg-white/5 border border-white/10 rounded-full px-4 py-2 text-sm text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-violet-500/50"
          />
          <Button type="submit" variant="primary" size="sm" disabled={!question.trim() || isTyping}>
            {isTyping ? '...' : 'Enviar'}
          </Button>
        </form>
      </Card>

      <div className="mt-6 flex justify-end">
        <Button variant="primary" size="lg" onClick={handleFinishOnboarding}>
          Ir al Dashboard →
        </Button>
      </div>
    </div>
  );

  const renderStep4 = () => (
    <div className="max-w-md mx-auto animate-fade-in-up">
      <h2 className="text-2xl md:text-3xl font-bold text-center mb-2">
        Instala el <span className="text-gradient">widget</span>
      </h2>
      <p className="text-white/50 text-center mb-8">
        Copia este código y añádelo a tu sitio web. El widget aparecerá automáticamente.
      </p>

      <Card className="p-6 bg-navy/80 border-white/10">
        <p className="text-xs text-white/50 mb-2">Código del widget:</p>
        <div className="bg-black/50 rounded-xl p-4 overflow-x-auto">
          <code className="text-xs text-cyan-400 break-all">
            {`<script src="https://nuvora-api-1hql.onrender.com/widget.js" data-bot-id="${bot?.id || 1}"></script>`}
          </code>
        </div>
        <button
          onClick={() => {
            const code = `<script src="https://nuvora-api-1hql.onrender.com/widget.js" data-bot-id="${bot?.id || 1}"></script>`;
            navigator.clipboard?.writeText(code);
            alert('¡Código copiado al portapapeles!');
          }}
          className="mt-4 w-full py-2 text-sm bg-white/10 hover:bg-white/20 rounded-xl transition text-white/70"
        >
          📋 Copiar código
        </button>
      </Card>

      <div className="mt-6 flex flex-col gap-3">
        <p className="text-sm text-white/40 text-center">
          🎉 ¡Tu asistente está listo! Ahora puedes verlo en el dashboard.
        </p>
        <Button variant="primary" size="lg" className="w-full" onClick={handleFinishOnboarding}>
          Ir al Dashboard →
        </Button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-navy text-white py-12 px-4 md:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <img src={LOGO_URL} alt="Nuvora" className="h-10 w-10 rounded-xl object-cover" />
          <span className="text-xl font-bold">Nuvora</span>
        </div>

        {/* Indicador de progreso */}
        {renderStepIndicator()}

        {/* Contenido del paso */}
        {step === 1 && renderStep1()}
        {step === 2 && renderStep2()}
        {step === 3 && renderStep3()}
        {step === 4 && renderStep4()}
      </div>
    </div>
  );
};

export default Onboarding;
