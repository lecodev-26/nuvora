import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

import Card from '../../components/Card';
import Button from '../../components/Button';
import Input from '../../components/Input';
import CreatorError from '../../components/creator/CreatorError';
import Spinner from '../../components/ui/Spinner';
import NichoSelector from '../../components/NichoSelector';
import { botService } from '../../services/api';

/**
 * CreatorConfig — Configuración del bot en Creator Mode.
 *
 * Estructura:
 *   - 3 tabs: Básico / Personalidad / Comportamiento
 *   - Formulario con botón "Guardar cambios"
 *   - Validación al guardar
 *   - nicho_id editable (null = desde cero)
 */
const CreatorConfig = () => {
  const { botId } = useParams();
  const navigate = useNavigate();

  const [bot, setBot] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('basic');
  const [saving, setSaving] = useState(false);
  const [savedMsg, setSavedMsg] = useState(null);
  const [saveError, setSaveError] = useState(null);

  // Form state (copiado del bot al cargar)
  const [form, setForm] = useState({
    name: '',
    description: '',
    business_name: '',
    business_type: '',
    nicho_id: null,
    goal: '',
    personality: '',
    tone: '',
    greeting: '',
    fallback_message: '',
    answer_mode: 'strict',
  });

  // ----- Cargar bot -----
  useEffect(() => {
    const load = async () => {
      if (!botId) return;
      setLoading(true);
      setError(null);
      try {
        const res = await botService.get(botId);
        const b = res.data;
        setBot(b);
        setForm({
          name: b.name || '',
          description: b.description || '',
          business_name: b.business_name || '',
          business_type: b.business_type || '',
          nicho_id: b.nicho_id || null,
          goal: b.goal || '',
          personality: b.personality || '',
          tone: b.tone || '',
          greeting: b.greeting || '',
          fallback_message: b.fallback_message || '',
          answer_mode: b.answer_mode || 'strict',
        });
      } catch (err) {
        const detail = err.response?.data?.detail;
        setError(typeof detail === 'string' ? detail : 'Error cargando el bot');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [botId]);

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setSavedMsg(null);
    setSaveError(null);
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveError(null);
    setSavedMsg(null);

    // Validación mínima
    if (!form.name || !form.name.trim()) {
      setSaveError('El nombre es obligatorio');
      setSaving(false);
      return;
    }

    try {
      const payload = {
        name: form.name.trim(),
        description: form.description.trim() || null,
        business_name: form.business_name.trim() || null,
        business_type: form.business_type.trim() || null,
        nicho_id: form.nicho_id, // puede ser null = desde cero
        goal: form.goal.trim() || null,
        personality: form.personality.trim() || null,
        tone: form.tone.trim() || null,
        greeting: form.greeting.trim() || null,
        fallback_message: form.fallback_message.trim() || null,
        answer_mode: form.answer_mode,
      };
      const res = await botService.update(botId, payload);
      setBot(res.data);
      setSavedMsg('Cambios guardados');
      setTimeout(() => setSavedMsg(null), 2500);
    } catch (err) {
      const detail = err.response?.data?.detail;
      const msg = Array.isArray(detail)
        ? detail.map((e) => e.msg || JSON.stringify(e)).join(', ')
        : typeof detail === 'string'
          ? detail
          : 'Error guardando cambios';
      setSaveError(msg);
    } finally {
      setSaving(false);
    }
  };

  // ----- Loading / Error -----
  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner />
      </div>
    );
  }

  if (error) {
    return (
      <CreatorError
        title="No se pudo cargar el bot"
        description={error}
        ctaLabel="Reintentar"
        onCta={() => window.location.reload()}
        secondaryLabel="Volver a Mis bots"
        onSecondary={() => navigate('/dashboard')}
      />
    );
  }

  const tabs = [
    { id: 'basic', label: 'Básico', icon: '⚙️' },
    { id: 'personality', label: 'Personalidad', icon: '🎭' },
    { id: 'behavior', label: 'Comportamiento', icon: '💬' },
  ];

  return (
    <div className="space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-xl md:text-2xl font-bold text-white">Configuración</h1>
        <p className="text-white/50 text-sm mt-1">
          Ajusta la información y comportamiento de tu bot.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-white/10 overflow-x-auto -mx-4 md:mx-0 px-4 md:px-0">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setActiveTab(t.id)}
            className={`px-4 py-2 text-sm font-medium transition border-b-2 -mb-px whitespace-nowrap flex-shrink-0 ${
              activeTab === t.id
                ? 'text-white border-cyan-400'
                : 'text-white/50 border-transparent hover:text-white/80'
            }`}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {/* Mensajes */}
      {savedMsg && (
        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg px-4 py-2.5 text-emerald-300 text-sm">
          ✅ {savedMsg}
        </div>
      )}
      {saveError && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-2.5 text-red-300 text-sm">
          ⚠️ {saveError}
        </div>
      )}

      {/* Contenido por tab */}
      <Card>
        {activeTab === 'basic' && (
          <div className="space-y-5">
            <Input
              label="Nombre del bot *"
              value={form.name}
              onChange={(e) => handleChange('name', e.target.value)}
              placeholder="Ej: Mi asistente"
            />
            <Input
              label="Descripción"
              value={form.description}
              onChange={(e) => handleChange('description', e.target.value)}
              placeholder="Breve descripción de qué hace tu bot"
            />
            <Input
              label="Nombre del negocio o proyecto"
              value={form.business_name}
              onChange={(e) => handleChange('business_name', e.target.value)}
              placeholder="Ej: Restaurante El Sol"
            />
            <Input
              label="Tipo de negocio (opcional)"
              value={form.business_type}
              onChange={(e) => handleChange('business_type', e.target.value)}
              placeholder="Ej: restaurante, gimnasio, comunidad..."
            />
            <div>
              <label className="block text-sm font-medium text-white/70 mb-3">
                Nicho / Plantilla
              </label>
              <NichoSelector
                selected={form.nicho_id}
                onSelect={(id) => handleChange('nicho_id', id)}
                columns="grid-cols-2 md:grid-cols-4"
              />
              <p className="text-white/40 text-[11px] mt-2">
                ✨ "Desde cero" es una opción válida: creas un bot sin plantilla.
              </p>
            </div>
          </div>
        )}

        {activeTab === 'personality' && (
          <div className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-white/70 mb-2">
                Objetivo del bot
              </label>
              <textarea
                value={form.goal}
                onChange={(e) => handleChange('goal', e.target.value)}
                placeholder="Ej: Responder dudas de mi comunidad sobre videojuegos"
                rows={3}
                className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-400/60 resize-none"
              />
            </div>
            <Input
              label="Personalidad"
              value={form.personality}
              onChange={(e) => handleChange('personality', e.target.value)}
              placeholder="Ej: cercano, profesional, divertido"
            />
            <Input
              label="Tono"
              value={form.tone}
              onChange={(e) => handleChange('tone', e.target.value)}
              placeholder="Ej: amigable, formal, técnico"
            />
            <div>
              <label className="block text-sm font-medium text-white/70 mb-2">
                Instrucciones adicionales
              </label>
              <textarea
                value={form.instructions || ''}
                onChange={(e) => handleChange('instructions', e.target.value)}
                placeholder="Instrucciones específicas para el bot"
                rows={3}
                className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-400/60 resize-none"
              />
            </div>
          </div>
        )}

        {activeTab === 'behavior' && (
          <div className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-white/70 mb-2">
                Mensaje de bienvenida
              </label>
              <textarea
                value={form.greeting}
                onChange={(e) => handleChange('greeting', e.target.value)}
                placeholder="¡Hola! ¿En qué puedo ayudarte?"
                rows={2}
                className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-400/60 resize-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-white/70 mb-2">
                Mensaje fallback (cuando no sabe responder)
              </label>
              <textarea
                value={form.fallback_message}
                onChange={(e) => handleChange('fallback_message', e.target.value)}
                placeholder="Lo siento, no tengo esa información."
                rows={2}
                className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-400/60 resize-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-white/70 mb-2">
                Modo de respuesta
              </label>
              <div className="flex gap-2">
                {[
                  { value: 'strict', label: 'Estricto', desc: 'Solo responde si tiene alta confianza' },
                  { value: 'flexible', label: 'Flexible', desc: 'Responde con cualquier coincidencia' },
                ].map((m) => (
                  <button
                    key={m.value}
                    type="button"
                    onClick={() => handleChange('answer_mode', m.value)}
                    className={`flex-1 text-left px-4 py-3 rounded-lg border transition ${
                      form.answer_mode === m.value
                        ? 'border-cyan-500/50 bg-cyan-500/10'
                        : 'border-white/10 bg-white/[0.02] hover:border-white/20'
                    }`}
                  >
                    <p className="text-white text-sm font-medium">{m.label}</p>
                    <p className="text-white/50 text-[11px] mt-0.5">{m.desc}</p>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* Footer con botón Guardar */}
      <div className="flex justify-end">
        <Button
          variant="primary"
          size="md"
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? 'Guardando...' : '💾 Guardar cambios'}
        </Button>
      </div>
    </div>
  );
};

export default CreatorConfig;
