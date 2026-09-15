import React, { useState } from 'react';
import Button from '../Button';
import TemplatesGrid from './TemplatesGrid';
import { aiService } from '../../services/aiService';

/**
 * AIDesignerPanel — Modal de generación de workflows con IA.
 *
 * Props:
 *   - open: boolean
 *   - onClose: () => void
 *   - onGenerated: (workflow) => void  ← se llama con el workflow listo
 *
 * Tabs:
 *   - "prompt":    textarea + botón Generar (usa IA)
 *   - "templates": grid de plantillas predefinidas (sin IA)
 *
 * Al recibir un workflow (IA o template) → se llama onGenerated y se cierra.
 */

const MIN_PROMPT_LENGTH = 10;
const MAX_PROMPT_LENGTH = 2000;

const AIDesignerPanel = ({ open, onClose, onGenerated }) => {
  const [tab, setTab] = useState('prompt');
  const [prompt, setPrompt] = useState('');
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null); // { workflow, explanation, warnings }

  if (!open) return null;

  const promptLength = prompt.trim().length;
  const canGenerate = promptLength >= MIN_PROMPT_LENGTH && !generating;

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    setResult(null);

    try {
      const res = await aiService.generate(prompt.trim());
      setResult(res.data);
    } catch (err) {
      const detail = err.response?.data?.detail;
      const msg = Array.isArray(detail)
        ? detail.map((e) => e.msg || JSON.stringify(e)).join(', ')
        : detail || err.message || 'Error generando workflow';
      setError(msg);
    } finally {
      setGenerating(false);
    }
  };

  const handleAcceptResult = () => {
    if (!result?.workflow) return;
    onGenerated(result.workflow);
    // Limpiar estado interno
    setResult(null);
    setPrompt('');
    setError(null);
    onClose();
  };

  const handleTemplateSelect = (templateId, workflow) => {
    onGenerated(workflow);
    onClose();
  };

  const handleClose = () => {
    if (generating) return; // bloquear cierre mientras se genera
    setResult(null);
    setError(null);
    onClose();
  };

  return (
    <div
      className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={handleClose}
    >
      <div
        className="bg-navy border border-white/10 rounded-2xl shadow-card w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
          <div>
            <h2 className="text-white text-lg font-semibold flex items-center gap-2">
              <span className="text-2xl">✨</span>
              AI Workflow Designer
            </h2>
            <p className="text-white/50 text-xs mt-0.5">
              Describe tu bot o elige una plantilla. La IA genera el workflow editable.
            </p>
          </div>
          <button
            type="button"
            onClick={handleClose}
            disabled={generating}
            className="text-white/50 hover:text-white transition-colors text-xl disabled:opacity-30"
          >
            ✕
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-white/10 px-6">
          <button
            type="button"
            onClick={() => setTab('prompt')}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
              tab === 'prompt'
                ? 'text-cyan-400 border-cyan-400'
                : 'text-white/50 hover:text-white border-transparent'
            }`}
          >
            📝 Describe tu bot
          </button>
          <button
            type="button"
            onClick={() => setTab('templates')}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
              tab === 'templates'
                ? 'text-cyan-400 border-cyan-400'
                : 'text-white/50 hover:text-white border-transparent'
            }`}
          >
            📋 Plantillas
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 overflow-y-auto flex-1">
          {tab === 'prompt' && (
            <>
              {/* Prompt */}
              <label className="block mb-3">
                <span className="text-white/60 text-xs uppercase tracking-wider">
                  ¿Qué quieres que haga tu bot?
                </span>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  disabled={generating}
                  rows={5}
                  maxLength={MAX_PROMPT_LENGTH}
                  placeholder="Ej: Quiero un bot para una clínica. Cuando un usuario pregunte por una cita, que pida su nombre, el día y compruebe si es mayor de edad."
                  className="mt-2 w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-400/60 resize-none disabled:opacity-50"
                />
                <div className="flex justify-between mt-1 text-xs">
                  <span className="text-white/40">
                    Cuanto más específico, mejor resultado.
                  </span>
                  <span
                    className={
                      promptLength > MAX_PROMPT_LENGTH * 0.9
                        ? 'text-amber-400'
                        : 'text-white/40'
                    }
                  >
                    {promptLength} / {MAX_PROMPT_LENGTH}
                  </span>
                </div>
              </label>

              {/* Botón generar */}
              <div className="flex justify-end gap-2 mb-4">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleGenerate}
                  disabled={!canGenerate}
                >
                  {generating ? '⟳ Generando...' : '✨ Generar workflow'}
                </Button>
              </div>

              {/* Error */}
              {error && (
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-300 text-sm mb-4">
                  ⚠️ {error}
                </div>
              )}

              {/* Loading */}
              {generating && (
                <div className="text-center py-8 text-white/50 text-sm">
                  <div className="inline-block w-6 h-6 border-2 border-white/20 border-t-cyan-400 rounded-full animate-spin mb-3" />
                  <div>La IA está diseñando tu workflow...</div>
                  <div className="text-xs text-white/30 mt-1">
                    Esto puede tardar 5-15 segundos
                  </div>
                </div>
              )}

              {/* Resultado */}
              {result && !generating && (
                <div className="space-y-3 border-t border-white/10 pt-4">
                  <div className="flex items-center gap-2 text-emerald-400 text-sm font-semibold">
                    ✅ Workflow generado
                  </div>

                  <div>
                    <div className="text-white/60 text-xs uppercase tracking-wider mb-1">
                      Nombre
                    </div>
                    <div className="text-white text-sm font-medium">
                      {result.workflow.name}
                    </div>
                  </div>

                  {result.explanation && (
                    <div>
                      <div className="text-white/60 text-xs uppercase tracking-wider mb-1">
                        Explicación
                      </div>
                      <div className="text-white/80 text-sm leading-relaxed bg-white/5 rounded-lg p-3">
                        {result.explanation}
                      </div>
                    </div>
                  )}

                  {result.warnings && result.warnings.length > 0 && (
                    <div>
                      <div className="text-amber-400 text-xs uppercase tracking-wider mb-1">
                        ⚠️ Avisos ({result.warnings.length})
                      </div>
                      <ul className="text-amber-300/80 text-xs space-y-1 bg-amber-500/5 rounded-lg p-3">
                        {result.warnings.map((w, i) => (
                          <li key={i}>• {w}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="text-white/40 text-xs pt-2 border-t border-white/10 flex flex-wrap gap-4">
                    <div>
                      <span className="text-white/30">nodos:</span>{' '}
                      <span className="font-mono">
                        {result.workflow.nodes?.length || 0}
                      </span>
                    </div>
                    <div>
                      <span className="text-white/30">transiciones:</span>{' '}
                      <span className="font-mono">
                        {result.workflow.transitions?.length || 0}
                      </span>
                    </div>
                    <div>
                      <span className="text-white/30">provider:</span>{' '}
                      <span className="font-mono">{result.provider_used}</span>
                    </div>
                    {result.tokens_used && (
                      <div>
                        <span className="text-white/30">tokens:</span>{' '}
                        <span className="font-mono">{result.tokens_used}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </>
          )}

          {tab === 'templates' && (
            <>
              <p className="text-white/60 text-sm mb-4">
                Plantillas listas para usar. Sin IA, sin coste, instantáneo.
              </p>
              <TemplatesGrid onSelect={handleTemplateSelect} />
            </>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-white/10 px-6 py-3 flex items-center justify-between bg-white/5">
          <div className="text-white/40 text-xs">
            La IA solo genera JSON. El validator de Nuvora decide si es válido.
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" onClick={handleClose} disabled={generating}>
              Cancelar
            </Button>
            {result && tab === 'prompt' && (
              <Button
                variant="primary"
                size="sm"
                onClick={handleAcceptResult}
              >
                ✓ Cargar en el Builder
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIDesignerPanel;
