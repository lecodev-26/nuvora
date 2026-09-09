import React, { useState, useEffect } from 'react';
import { useBot } from '../context/BotContext';
import { botService, memoryService } from '../services/api';

const Dashboard = () => {
  const { bots, setBots, selectedBot, setSelectedBot, loading, setLoading } = useBot();
  const [memories, setMemories] = useState([]);
  const [newMemory, setNewMemory] = useState({ fact: '', keyword: '' });
  const [newBot, setNewBot] = useState({ name: '', restaurant_name: '', owner_email: '' });

  // Cargar bots al inicio
  useEffect(() => {
    loadBots();
  }, []);

  const loadBots = async () => {
    setLoading(true);
    try {
      const response = await botService.list();
      setBots(response.data);
    } catch (error) {
      console.error('Error cargando bots:', error);
    }
    setLoading(false);
  };

  const loadMemories = async (botId) => {
    try {
      const response = await memoryService.getByBot(botId);
      setMemories(response.data);
    } catch (error) {
      console.error('Error cargando memorias:', error);
    }
  };

  const handleSelectBot = (bot) => {
    setSelectedBot(bot);
    loadMemories(bot.id);
  };

  const handleCreateBot = async (e) => {
    e.preventDefault();
    try {
      await botService.create(newBot);
      setNewBot({ name: '', restaurant_name: '', owner_email: '' });
      loadBots();
    } catch (error) {
      console.error('Error creando bot:', error);
    }
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
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h1>📊 Nuvora Dashboard</h1>

      {/* Crear Bot */}
      <div style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '8px', marginBottom: '20px' }}>
        <h2>Crear Nuevo Bot</h2>
        <form onSubmit={handleCreateBot}>
          <input
            type="text"
            placeholder="Nombre del bot"
            value={newBot.name}
            onChange={(e) => setNewBot({ ...newBot, name: e.target.value })}
            required
            style={{ padding: '8px', margin: '5px', width: '200px' }}
          />
          <input
            type="text"
            placeholder="Nombre del restaurante"
            value={newBot.restaurant_name}
            onChange={(e) => setNewBot({ ...newBot, restaurant_name: e.target.value })}
            required
            style={{ padding: '8px', margin: '5px', width: '200px' }}
          />
          <input
            type="email"
            placeholder="Email del propietario"
            value={newBot.owner_email}
            onChange={(e) => setNewBot({ ...newBot, owner_email: e.target.value })}
            required
            style={{ padding: '8px', margin: '5px', width: '200px' }}
          />
          <button type="submit" style={{ padding: '8px 16px', background: '#6C63FF', color: 'white', border: 'none', borderRadius: '4px' }}>
            Crear Bot
          </button>
        </form>
      </div>

      {/* Lista de Bots */}
      <div style={{ display: 'flex', gap: '20px' }}>
        <div style={{ flex: 1, border: '1px solid #ddd', padding: '15px', borderRadius: '8px' }}>
          <h2>Tus Bots ({bots.length})</h2>
          {loading ? (
            <p>Cargando...</p>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {bots.map((bot) => (
                <li
                  key={bot.id}
                  onClick={() => handleSelectBot(bot)}
                  style={{
                    padding: '10px',
                    margin: '5px 0',
                    background: selectedBot?.id === bot.id ? '#e8e8ff' : '#f5f5f5',
                    borderRadius: '4px',
                    cursor: 'pointer',
                  }}
                >
                  <strong>{bot.name}</strong> - {bot.restaurant_name}
                  <br />
                  <small>{bot.owner_email} | Plan: {bot.plan}</small>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Memorias del Bot Seleccionado */}
        <div style={{ flex: 2, border: '1px solid #ddd', padding: '15px', borderRadius: '8px' }}>
          <h2>{selectedBot ? `Memorias de ${selectedBot.name}` : 'Selecciona un bot'}</h2>
          {selectedBot && (
            <>
              <form onSubmit={handleAddMemory} style={{ marginBottom: '15px' }}>
                <input
                  type="text"
                  placeholder="Hecho (ej: Abrimos a las 9:00)"
                  value={newMemory.fact}
                  onChange={(e) => setNewMemory({ ...newMemory, fact: e.target.value })}
                  required
                  style={{ padding: '8px', margin: '5px', width: '300px' }}
                />
                <input
                  type="text"
                  placeholder="Palabra clave (ej: horario)"
                  value={newMemory.keyword}
                  onChange={(e) => setNewMemory({ ...newMemory, keyword: e.target.value })}
                  required
                  style={{ padding: '8px', margin: '5px', width: '150px' }}
                />
                <button type="submit" style={{ padding: '8px 16px', background: '#6C63FF', color: 'white', border: 'none', borderRadius: '4px' }}>
                  Añadir Memoria
                </button>
              </form>

              <ul style={{ listStyle: 'none', padding: 0 }}>
                {memories.map((memory) => (
                  <li key={memory.id} style={{ padding: '8px', margin: '5px 0', background: '#f9f9f9', borderRadius: '4px' }}>
                    <strong>{memory.keyword}:</strong> {memory.fact}
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      </div>

      {/* Código del Widget */}
      {selectedBot && (
        <div style={{ marginTop: '20px', border: '1px solid #ddd', padding: '15px', borderRadius: '8px', background: '#f9f9f9' }}>
          <h2>📋 Código del Widget</h2>
          <p>Copia este código en tu página web:</p>
          <pre style={{ background: '#333', color: '#fff', padding: '15px', borderRadius: '4px', overflow: 'auto' }}>
            {`<script src="${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/widget.js" data-bot-id="${selectedBot.id}"></script>`}
          </pre>
        </div>
      )}
    </div>
  );
};

export default Dashboard;

