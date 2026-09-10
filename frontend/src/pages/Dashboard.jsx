import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useBot } from '../context/BotContext';
import { botService, memoryService, askService } from '../services/api';
import { getNicho } from '../data/nichos';
import Button from '../components/Button';
import Card from '../components/Card';
import Badge from '../components/Badge';
import Input from '../components/Input';
import NichoSelector from '../components/NichoSelector';
import NichoBadge from '../components/NichoBadge';

const LOGO_URL = '/logo.png';
const API_URL = import.meta.env.VITE_API_URL || 'https://nuvora-api-1hql.onrender.com';

const Dashboard = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { bots, setBots, selectedBot, setSelectedBot, loading, setLoading } = useBot();

  // Estados
  const [memories, setMemories] = useState([]);
  const [newMemory, setNewMemory] = useState({ fact: '', keyword: '' });
  const [newBot, setNewBot] = useState({ name: '', restaurant_name: '', nicho_id: 'otro' });
  const [showCreateBot, setShowCreateBot] = useState(false);
  const [analytics, setAnalytics] = useState(null);
  const [serviceStatus, setServiceStatus] = useState(null);
  const [chatQuestion, setChatQuestion] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [showNichoConfig, setShowNichoConfig] = useState(false);
  const [nichoUpdateLoading, setNichoUpdateLoading] = useState(false);

  // Cargar bots al inicio
  useEffect(() => {
    loadBots();
    loadServiceStatus();
  }, []);

  // Cargar datos cuando se selecciona un bot
  useEffect(() => {
    if (selectedBot) {
      loadAnalytics(selectedBot.id);
      loadMemories(selectedBot.id);
    }
  }, [selectedBot]);

  const loadBots = async () => {
    setLoading(true);
    try {
      const response = await botService.list();
      setBots(response.data || []);
      if (response.data && response.data.length > 0) {
        setSelectedBot(response.data[0]);
      }
    } catch (error) {
      console.error('Error cargando bots:', error);
    }
    setLoading(false);
  };

  const loadMemories = async (botId) => {
    try {
      const response = await memoryService.getByBot(botId);
      setMemories(response.data || []);
    } catch (error) {
      console.error('Error cargando memorias:', error);
    }
  };

  const loadAnalytics = async (botId) => {
    try {
      const token = localStorage.getItem('nuvora_token');
      const response = await fetch(`${API_URL}/analytics/by-bot/${botId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      }
    } catch (error) {
      console.error('Error cargando analytics:', error);
    }
  };

  const loadServiceStatus = async () => {
    try {
      const token = localStorage.getItem('nuvora_token');
      const response = await fetch(`${API_URL}/payments/status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setServiceStatus(data);
      }
    } catch (error) {
      console.error('Error cargando estado del servicio:', error);
    }
  };

  const handleCreateBot = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await botService.create({
        name: newBot.name,
        restaurant_name: newBot.restaurant_name,
        owner_email: user?.email,
        nicho_id: newBot.nicho_id,
      });
      setBots([...bots, response.data]);
      setSelectedBot(response.data);
      setNewBot({ name: '', restaurant_name: '', nicho_id: 'otro' });
      setShowCreateBot(false);
    } catch (error) {
      console.error('Error creando bot:', error);
      alert('Error al crear el bot. Inténtalo de nuevo.');
    }
    setLoading(false);
  };

  const handleUpdateNicho = async (nichoId) => {
    if (!selectedBot) return;
    setNichoUpdateLoading(true);
    try {
      const token = localStorage.getItem('nuvora_token');
      const response = await fetch(`${API_URL}/bots/${selectedBot.id}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ nicho_id: nichoId })
      });

      if (response.ok) {
        const updatedBot = await response.json();
        // Actualizar el bot en la lista sin recargar memorias
        setBots(bots.map(b => b.id === updatedBot.id ? updatedBot : b));
        setSelectedBot(updatedBot);
        setShowNichoConfig(false);
      } else {
        alert('Error al actualizar el nicho.');
      }
    } catch (error) {
      console.error('Error actualizando nicho:', error);
      alert('Error de conexión. Inténtalo de nuevo.');
    }
    setNichoUpdateLoading(false);
  };

  const handleAddMemory = async (e) => {
    e.preventDefault();
    if (!selectedBot) return;
    setLoading(true);
    try {
      await memoryService.add({
        bot_id: selectedBot.id,
        fact: newMemory.fact,
        keyword: newMemory.keyword,
      });
      setNewMemory({ fact: '', keyword: '' });
      loadMemories(selectedBot.id);
    } catch (error) {
      console.error('Error añadiendo memoria:', error);
      alert('Error al añadir la memoria. Inténtalo de nuevo.');
    }
    setLoading(false);
  };

  const handleAskQuestion = async (e) => {
    e.preventDefault();
    if (!selectedBot || !chatQuestion.trim()) return;

    const question = chatQuestion.trim();
    setChatMessages([...chatMessages, { type: 'user', text: question }]);
    setChatQuestion('');
    setIsTyping(true);

    try {
      const response = await askService.ask(selectedBot.id, question);
      const answer = response.data.answer || 'No tengo esa información en mi memoria.';
      setChatMessages(prev => [...prev, { type: 'bot', text: answer }]);
    } catch (error) {
      console.error('Error preguntando:', error);
      setChatMessages(prev => [...prev, { type: 'bot', text: 'Hubo un error al procesar tu pregunta.' }]);
    }
    setIsTyping(false);
  };

  const handlePayment = async () => {
    setPaymentLoading(true);
    try {
      const token = localStorage.getItem('nuvora_token');
      const response = await fetch(`${API_URL}/payments/create-checkout-session`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.url) {
          window.location.href = data.url;
        } else {
          alert('Error al crear la sesión de pago.');
        }
      } else {
        const error = await response.json();
        alert(error.detail || 'Error al iniciar el pago.');
      }
    } catch (error) {
      console.error('Error en el pago:', error);
      alert('Error de conexión. Inténtalo de nuevo.');
    }
    setPaymentLoading(false);
  };

  // ============================================================
  // RENDERIZAR ESTADO DEL SERVICIO
  // ============================================================
  const renderServiceStatus = () => {
    if (!serviceStatus) return (
      <Card className="p-4 border-white/10">
        <p className="text-white/30 text-sm">Cargando estado del servicio...</p>
      </Card>
    );

    const statusMap = {
      trial: { label: 'Prueba gratuita', color: 'trial', icon: '🟡', message: 'Estás en periodo de prueba.' },
      active: { label: 'Activo', color: 'active', icon: '🟢', message: 'Tu servicio está activo.' },
      expired: { label: 'Expirado', color: 'expired', icon: '🔴', message: 'Tu servicio ha expirado.' },
    };

    const status = statusMap[serviceStatus.status] || statusMap.trial;
    const daysLeft = serviceStatus.days_left !== null ? serviceStatus.days_left : serviceStatus.trial_days_left;

    return (
      <Card className="p-4 border-white/10 bg-gradient-hero">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{status.icon}</span>
            <div>
              <p className="text-sm font-semibold">Estado del servicio</p>
              <Badge variant={status.color}>{status.label}</Badge>
              <p className="text-xs text-white/40 mt-0.5">{status.message}</p>
            </div>
          </div>

          <div className="text-left md:text-right">
            {daysLeft !== null && daysLeft !== undefined && (
              <p className="text-sm font-medium">
                {daysLeft > 0 ? `${daysLeft} días restantes` : 'Sin días restantes'}
              </p>
            )}
            {serviceStatus.expiration_date && (
              <p className="text-xs text-white/30">
                Expira: {new Date(serviceStatus.expiration_date).toLocaleDateString()}
              </p>
            )}

            {(serviceStatus.status === 'trial' || serviceStatus.status === 'expired') && (
              <Button
                variant="primary"
                size="sm"
                className="mt-2 animate-pulse-glow"
                onClick={handlePayment}
                disabled={paymentLoading}
              >
                {paymentLoading ? 'Cargando...' : 'Activar por 29,99 € →'}
              </Button>
            )}

            {serviceStatus.status === 'active' && (
              <p className="text-xs text-emerald-400 mt-1">✓ Servicio activo</p>
            )}
          </div>
        </div>
      </Card>
    );
  };

  // ============================================================
  // RENDER
  // ============================================================
  return (
    <div className="min-h-screen bg-navy text-white flex">
      {/* ============================================================
          SIDEBAR
          ============================================================ */}
      <aside className="hidden md:flex flex-col w-64 bg-navy/80 border-r border-white/5 p-6 sticky top-0 h-screen">
        <div className="flex items-center gap-3 mb-8">
          <img src={LOGO_URL} alt="Nuvora" className="h-10 w-10 rounded-xl object-cover" />
          <span className="text-xl font-bold">Nuvora</span>
        </div>

        <nav className="flex-1 space-y-1">
          <button className="w-full text-left px-4 py-2.5 rounded-xl bg-white/10 text-white font-medium">
            📊 Inicio
          </button>
          <button className="w-full text-left px-4 py-2.5 rounded-xl text-white/50 hover:text-white hover:bg-white/5 transition">
            🤖 Mi negocio
          </button>
          <button className="w-full text-left px-4 py-2.5 rounded-xl text-white/50 hover:text-white hover:bg-white/5 transition">
            💬 Conversaciones
          </button>
          <button className="w-full text-left px-4 py-2.5 rounded-xl text-white/50 hover:text-white hover:bg-white/5 transition">
            📈 Analíticas
          </button>
          <button className="w-full text-left px-4 py-2.5 rounded-xl text-white/50 hover:text-white hover:bg-white/5 transition">
            🔌 Instalar widget
          </button>
        </nav>

        <div className="pt-6 border-t border-white/5 space-y-3">
          <div className="flex items-center gap-3 px-4 py-2 rounded-xl bg-white/5">
            <div className="w-8 h-8 rounded-full bg-gradient-primary flex items-center justify-center text-sm font-bold">
              {user?.full_name?.[0] || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.full_name || 'Usuario'}</p>
              <p className="text-xs text-white/40 truncate">{user?.email}</p>
            </div>
          </div>
          <Button variant="ghost" size="sm" className="w-full" onClick={logout}>
            Cerrar sesión
          </Button>
        </div>
      </aside>

      {/* ============================================================
          CONTENIDO PRINCIPAL
          ============================================================ */}
      <main className="flex-1 p-4 md:p-8 overflow-y-auto">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Header móvil */}
          <div className="flex md:hidden items-center justify-between">
            <div className="flex items-center gap-3">
              <img src={LOGO_URL} alt="Nuvora" className="h-8 w-8 rounded-lg object-cover" />
              <span className="text-lg font-bold">Nuvora</span>
            </div>
            <button onClick={logout} className="text-white/50 text-sm">
              Salir
            </button>
          </div>

          {/* Estado del servicio */}
          {renderServiceStatus()}

          {/* Métricas */}
          {analytics && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card className="p-4 text-center">
                <p className="text-2xl font-bold">{analytics.total_conversations || 0}</p>
                <p className="text-xs text-white/50">Total preguntas</p>
              </Card>
              <Card className="p-4 text-center">
                <p className="text-2xl font-bold text-emerald-400">{analytics.answered || 0}</p>
                <p className="text-xs text-white/50">Respondidas</p>
              </Card>
              <Card className="p-4 text-center">
                <p className="text-2xl font-bold text-amber-400">{analytics.unanswered || 0}</p>
                <p className="text-xs text-white/50">Sin respuesta</p>
              </Card>
              <Card className="p-4 text-center">
                <p className="text-2xl font-bold text-cyan-400">{analytics.response_rate || 0}%</p>
                <p className="text-xs text-white/50">Tasa de respuesta</p>
              </Card>
            </div>
          )}

          {/* Bots y Memorias */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Lista de bots */}
            <Card className="p-4 lg:col-span-1">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold">Tus bots</h3>
                <Button variant="primary" size="sm" onClick={() => setShowCreateBot(!showCreateBot)}>
                  + Nuevo
                </Button>
              </div>

              {showCreateBot && (
                <form onSubmit={handleCreateBot} className="mb-4 p-3 bg-white/5 rounded-xl space-y-3">
                  <Input
                    placeholder="Nombre del bot"
                    value={newBot.name}
                    onChange={(e) => setNewBot({ ...newBot, name: e.target.value })}
                    className="text-sm"
                    required
                  />
                  <Input
                    placeholder="Nombre del negocio"
                    value={newBot.restaurant_name}
                    onChange={(e) => setNewBot({ ...newBot, restaurant_name: e.target.value })}
                    className="text-sm"
                    required
                  />
                  <Button type="submit" variant="primary" size="sm" className="w-full" disabled={loading}>
                    Crear
                  </Button>
                </form>
              )}

              <div className="space-y-2">
                {bots.map((bot) => (
                  <button
                    key={bot.id}
                    onClick={() => {
                      setSelectedBot(bot);
                      setShowNichoConfig(false);
                    }}
                    className={`w-full text-left p-3 rounded-xl transition ${
                      selectedBot?.id === bot.id
                        ? 'bg-white/10 border border-violet-500/30'
                        : 'hover:bg-white/5'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <p className="font-medium text-sm">{bot.name}</p>
                      <NichoBadge nichoId={bot.nicho_id} showName={false} />
                    </div>
                    <p className="text-xs text-white/40">{bot.restaurant_name}</p>
                  </button>
                ))}
                {bots.length === 0 && (
                  <p className="text-sm text-white/30 text-center py-4">No tienes bots todavía</p>
                )}
              </div>
            </Card>

            {/* Memorias y chat */}
            <Card className="p-4 lg:col-span-2">
              {selectedBot ? (
                <div className="space-y-4">
                  {/* Header con nicho y botón de configuración */}
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold">Memorias de {selectedBot.name}</h3>
                      <NichoBadge nichoId={selectedBot.nicho_id} />
                    </div>
                    <button
                      onClick={() => setShowNichoConfig(!showNichoConfig)}
                      className="text-xs text-white/40 hover:text-white/70 transition"
                    >
                      ⚙️ Cambiar nicho
                    </button>
                  </div>

                  {/* Configuración de nicho */}
                  {showNichoConfig && (
                    <Card className="p-4 bg-white/5 border-violet-500/20">
                      <p className="text-sm font-medium mb-3">
                        Selecciona un nuevo nicho para tu negocio
                      </p>
                      <NichoSelector
                        selected={selectedBot.nicho_id}
                        onSelect={handleUpdateNicho}
                        columns="grid-cols-2 md:grid-cols-4"
                      />
                      <div className="mt-3 flex justify-end">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setShowNichoConfig(false)}
                        >
                          Cancelar
                        </Button>
                      </div>
                      {nichoUpdateLoading && (
                        <p className="text-xs text-violet-400 mt-2">Actualizando nicho...</p>
                      )}
                      <p className="text-[10px] text-white/30 mt-2">
                        ℹ️ Cambiar de nicho no modifica tus memorias existentes.
                      </p>
                    </Card>
                  )}

                  {/* Añadir memoria */}
                  <form onSubmit={handleAddMemory} className="flex flex-wrap gap-2">
                    <Input
                      placeholder="Hecho (ej: Abrimos a las 9:00)"
                      value={newMemory.fact}
                      onChange={(e) => setNewMemory({ ...newMemory, fact: e.target.value })}
                      className="flex-1 min-w-[200px] text-sm"
                      required
                    />
                    <Input
                      placeholder="Palabra clave"
                      value={newMemory.keyword}
                      onChange={(e) => setNewMemory({ ...newMemory, keyword: e.target.value.toLowerCase() })}
                      className="w-32 text-sm"
                      required
                    />
                    <Button type="submit" variant="primary" size="sm" disabled={loading}>
                      Añadir
                    </Button>
                  </form>

                  {/* Lista de memorias */}
                  <div className="space-y-1 max-h-40 overflow-y-auto">
                    {memories.map((m) => (
                      <div key={m.id} className="bg-white/5 rounded-lg px-3 py-2 text-sm flex justify-between">
                        <span className="text-white/60">{m.keyword}:</span>
                        <span className="text-white/90">{m.fact}</span>
                      </div>
                    ))}
                    {memories.length === 0 && (
                      <p className="text-sm text-white/30 text-center py-4">
                        Aún no hay memorias. Añade información para que el bot aprenda.
                      </p>
                    )}
                  </div>

                  {/* Chat rápido */}
                  <div className="border-t border-white/5 pt-4">
                    <p className="text-sm font-medium mb-2">Probar asistente</p>
                    <form onSubmit={handleAskQuestion} className="flex gap-2">
                      <input
                        type="text"
                        placeholder="Haz una pregunta..."
                        value={chatQuestion}
                        onChange={(e) => setChatQuestion(e.target.value)}
                        className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-violet-500/50"
                      />
                      <Button type="submit" variant="primary" size="sm" disabled={!chatQuestion.trim() || isTyping}>
                        {isTyping ? '...' : 'Enviar'}
                      </Button>
                    </form>
                    <div className="mt-3 space-y-1 max-h-32 overflow-y-auto">
                      {chatMessages.map((msg, i) => (
                        <div
                          key={i}
                          className={`text-sm ${msg.type === 'user' ? 'text-cyan-400 text-right' : 'text-white/70'}`}
                        >
                          {msg.type === 'user' ? 'Tú: ' : 'Bot: '}{msg.text}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Código del widget */}
                  <div className="border-t border-white/5 pt-4">
                    <p className="text-xs text-white/50 mb-2">Código del widget:</p>
                    <div className="bg-black/50 rounded-xl p-3 overflow-x-auto">
                      <code className="text-xs text-cyan-400 break-all">
                        {`<script src="https://nuvora-api-1hql.onrender.com/widget.js" data-bot-id="${selectedBot.id}"></script>`}
                      </code>
                    </div>
                    <button
                      onClick={() => {
                        const code = `<script src="https://nuvora-api-1hql.onrender.com/widget.js" data-bot-id="${selectedBot.id}"></script>`;
                        navigator.clipboard?.writeText(code);
                        alert('¡Código copiado al portapapeles!');
                      }}
                      className="mt-2 text-xs text-cyan-400 hover:underline"
                    >
                      📋 Copiar código
                    </button>
                  </div>
                </div>
              ) : (
                <p className="text-white/30 text-center py-8">
                  Selecciona un bot para empezar.
                </p>
              )}
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
