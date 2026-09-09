import { useState, useEffect } from 'react';
import { botService, memoryService } from '../services/api';

const LOGO_URL = 'https://raw.githubusercontent.com/lecodev-26/nuvora/main/assets/logo.png';

export default function NuvoraDashboard() {
  const [bots, setBots] = useState([]);
  const [form, setForm] = useState({ botName: '', resto: '', email: '' });
  const [selectedBot, setSelectedBot] = useState(null);
  const [memories, setMemories] = useState([]);
  const [newMemory, setNewMemory] = useState({ fact: '', keyword: '' });

  // Cargar bots al inicio
  useEffect(() => {
    loadBots();
  }, []);

  const loadBots = async () => {
    try {
      const response = await botService.list();
      setBots(response.data);
    } catch (error) {
      console.error('Error cargando bots:', error);
    }
  };

  const loadMemories = async (botId) => {
    try {
      const response = await memoryService.getByBot(botId);
      setMemories(response.data);
    } catch (error) {
      console.error('Error cargando memorias:', error);
    }
  };

  const crearBot = async () => {
    if (!form.botName || !form.resto) return;
    try {
      const response = await botService.create({
        name: form.botName,
        restaurant_name: form.resto,
        owner_email: form.email || 'admin@nuvora.com'
      });
      setBots([{
        id: response.data.id,
        name: response.data.name,
        resto: response.data.restaurant_name,
        msgs: 0,
        status: 'Online',
        last: 'ahora'
      }, ...bots]);
      setForm({ botName: '', resto: '', email: '' });
    } catch (error) {
      console.error('Error creando bot:', error);
    }
  };

  const handleSelectBot = (bot) => {
    setSelectedBot(bot);
    loadMemories(bot.id);
  };

  const handleAddMemory = async (e) => {
    e.preventDefault();
    if (!selectedBot) return;
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
    }
  };

  return (
    <div className="min-h-screen bg-[#0A0A14] text-white font-['Inter'] p-4 md:p-6">
      {/* Glow de fondo */}
      <div className="fixed top-0 left-0 w-[500px] h-[500px] bg-[#00C6FF]/20 blur-[150px] rounded-full -translate-x-1/2 -translate-y-1/2 pointer-events-none" />
      <div className="fixed bottom-0 right-0 w-[600px] h-[600px] bg-[#FF4ECD]/20 blur-[150px] rounded-full translate-x-1/3 translate-y-1/3 pointer-events-none" />

      {/* HEADER */}
      <header className="relative z-10 flex items-center justify-between border border-white/10 rounded-2xl bg-white/[0.04] backdrop-blur-xl px-6 py-4 mb-6">
        <div className="flex items-center gap-4">
          <img src={LOGO_URL} alt="Nuvora" className="w-10 h-10 rounded-xl object-cover" />
          <h1 className="text-2xl font-bold">Nuvora <span className="text-white/50 font-normal ml-3 text-lg">Dashboard</span></h1>
        </div>
        <div className="flex items-center gap-3">
          <div className="hidden md:flex items-center bg-white/10 rounded-full px-4 py-2 text-sm text-white/60">🔍 Buscar...</div>
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-[#00C6FF] to-[#FF4ECD] p-[2px]">
            <div className="w-full h-full rounded-full bg-black flex items-center justify-center text-xs">AR</div>
          </div>
        </div>
      </header>

      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-[380px_1fr] gap-6 max-w-[1600px] mx-auto">
        {/* CREAR BOT */}
        <div className="h-fit rounded-[20px] border border-white/10 bg-gradient-to-b from-white/[0.07] to-white/[0.02] backdrop-blur-xl p-6 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.1)]">
          <h2 className="text-xl font-bold mb-1 flex gap-2 items-center">🤖 Crear Nuevo Bot</h2>
          <p className="text-sm text-white/50 mb-6">Configura tu asistente AI para tu restaurante en segundos</p>

          <div className="space-y-4">
            <div>
              <label className="text-xs text-white/70 mb-2 block">Nombre del bot</label>
              <input
                value={form.botName}
                onChange={e => setForm({ ...form, botName: e.target.value })}
                placeholder="Asistente Reservas"
                className="w-full bg-white/[0.06] border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-[#7B5CFF] placeholder:text-white/30"
              />
            </div>
            <div>
              <label className="text-xs text-white/70 mb-2 block">Nombre del restaurante</label>
              <input
                value={form.resto}
                onChange={e => setForm({ ...form, resto: e.target.value })}
                placeholder="La Trattoria Roma"
                className="w-full bg-white/[0.06] border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-[#7B5CFF] placeholder:text-white/30"
              />
            </div>
            <div>
              <label className="text-xs text-white/70 mb-2 block">Email del propietario</label>
              <input
                value={form.email}
                onChange={e => setForm({ ...form, email: e.target.value })}
                placeholder="propietario@email.com"
                className="w-full bg-white/[0.06] border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-[#7B5CFF] placeholder:text-white/30"
              />
            </div>
            <button
              onClick={crearBot}
              className="w-full mt-2 rounded-xl py-3.5 font-semibold bg-gradient-to-r from-[#00C6FF] to-[#FF4ECD] hover:opacity-90 transition shadow-[0_0_20px_rgba(123,92,255,0.4)]"
            >
              + Crear Bot
            </button>
            <p className="text-[11px] text-center text-white/40">El bot estará listo en menos de 1 minuto</p>
          </div>
        </div>

        {/* DERECHA */}
        <div className="space-y-6">
          {/* STATS */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { label: 'Mensajes hoy', value: '1,240', sub: '+12.5% vs ayer' },
              { label: 'Tasa de respuesta', value: '98.2%', sub: '+1.8% vs ayer' },
              { label: 'Satisfacción', value: '4.7/5', sub: 'Promedio 112 reseñas' },
            ].map(s => (
              <div key={s.label} className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
                <p className="text-xs text-white/50">{s.label}</p>
                <p className="text-3xl font-bold mt-2">{s.value}</p>
                <p className="text-xs text-emerald-400 mt-1">{s.sub}</p>
              </div>
            ))}
          </div>

          {/* TUS BOTS */}
          <div>
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-lg">Tus Bots</h3>
              <span className="text-xs bg-white/10 px-3 py-1 rounded-full">{bots.length} activos</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {bots.map(b => (
                <div
                  key={b.id}
                  onClick={() => handleSelectBot(b)}
                  className="rounded-2xl border border-white/10 bg-gradient-to-b from-white/[0.06] to-transparent p-5 hover:border-[#7B5CFF]/50 transition cursor-pointer"
                >
                  <div className="flex justify-between items-start">
                    <div className="w-2 h-2 rounded-full bg-emerald-400 mt-1" />
                    <span className="text-[11px] bg-emerald-500/20 text-emerald-300 px-2 py-1 rounded-full">Online</span>
                  </div>
                  <h4 className="font-semibold mt-3">{b.name}</h4>
                  <p className="text-sm text-white/50">{b.restaurant_name || b.resto}</p>
                  <div className="mt-4 pt-4 border-t border-white/10 text-xs text-white/60">
                    <p>{b.msgs || 0} mensajes gestionados</p>
                    <p className="mt-1 text-white/40">Última actividad: {b.last || 'ahora'}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* MEMORIAS DEL BOT SELECCIONADO */}
          {selectedBot && (
            <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
              <h4 className="font-bold mb-4">Memorias de {selectedBot.name}</h4>
              <form onSubmit={handleAddMemory} className="flex gap-3 mb-4 flex-wrap">
                <input
                  type="text"
                  placeholder="Hecho (ej: Abrimos a las 9:00)"
                  value={newMemory.fact}
                  onChange={(e) => setNewMemory({ ...newMemory, fact: e.target.value })}
                  className="flex-1 bg-white/[0.06] border border-white/10 rounded-xl px-4 py-2 text-sm focus:outline-none focus:border-[#7B5CFF] placeholder:text-white/30"
                  required
                />
                <input
                  type="text"
                  placeholder="Palabra clave"
                  value={newMemory.keyword}
                  onChange={(e) => setNewMemory({ ...newMemory, keyword: e.target.value })}
                  className="w-32 bg-white/[0.06] border border-white/10 rounded-xl px-4 py-2 text-sm focus:outline-none focus:border-[#7B5CFF] placeholder:text-white/30"
                  required
                />
                <button type="submit" className="px-4 py-2 rounded-xl bg-gradient-to-r from-[#00C6FF] to-[#7B5CFF] text-white font-semibold text-sm">
                  Añadir
                </button>
              </form>
              <ul className="space-y-2">
                {memories.map(m => (
                  <li key={m.id} className="bg-white/[0.04] px-4 py-2 rounded-xl text-sm flex justify-between">
                    <span className="text-white/60">{m.keyword}:</span>
                    <span>{m.fact}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
