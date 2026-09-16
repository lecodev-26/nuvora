import React, { useState, useEffect } from 'react';
import Button from '../Button';

/**
 * TestEditor — Modal para crear/editar un test.
 *
 * Props:
 *   - open: boolean
 *   - test: TestCaseResponse | null  (null → crear)
 *   - onSave: (data) => Promise<void>
 *   - onClose: () => void
 *   - saving: boolean
 */

const ASSERTION_TYPES = [
  { value: 'response_contains', label: 'Respuesta contiene', fields: ['value'] },
  { value: 'response_equals', label: 'Respuesta igual a', fields: ['value'] },
  { value: 'response_not_contains', label: 'Respuesta NO contiene', fields: ['value'] },
  { value: 'node_visited', label: 'Nodo visitado', fields: ['node_id'] },
  { value: 'node_not_visited', label: 'Nodo NO visitado', fields: ['node_id'] },
  { value: 'variable_equals', label: 'Variable == valor', fields: ['variable', 'expected'] },
  { value: 'variable_exists', label: 'Variable existe', fields: ['variable'] },
  { value: 'variable_not_exists', label: 'Variable NO existe', fields: ['variable'] },
  { value: 'reaches_end', label: 'Llega al END', fields: [] },
  { value: 'max_steps', label: 'Máximo de pasos', fields: ['max_steps'] },
];

const MAX_MESSAGES = 20;
const MAX_ASSERTIONS = 30;

const emptyAssertion = () => ({ type: 'reaches_end' });

const TestEditor = ({ open, test, onSave, onClose, saving = false }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [messages, setMessages] = useState(['']);
  const [variables, setVariables] = useState({}); // dict
  const [assertions, setAssertions] = useState([emptyAssertion()]);
  const [enabled, setEnabled] = useState(true);
  const [error, setError] = useState(null);

  // Inicializar estado al abrir
  useEffect(() => {
    if (!open) return;
    if (test) {
      setName(test.name || '');
      setDescription(test.description || '');
      setMessages(test.input_messages?.length ? test.input_messages : ['']);
      setVariables(test.initial_variables || {});
      setAssertions(
        test.assertions?.length ? test.assertions : [emptyAssertion()]
      );
      setEnabled(test.enabled !== undefined ? test.enabled : true);
    } else {
      setName('');
      setDescription('');
      setMessages(['']);
      setVariables({});
      setAssertions([emptyAssertion()]);
      setEnabled(true);
    }
    setError(null);
  }, [open, test]);

  if (!open) return null;

  // ============================================================
  // MESSAGES
  // ============================================================

  const addMessage = () => {
    if (messages.length >= MAX_MESSAGES) return;
    setMessages([...messages, '']);
  };

  const updateMessage = (i, value) => {
    const copy = [...messages];
    copy[i] = value;
    setMessages(copy);
  };

  const removeMessage = (i) => {
    if (messages.length <= 1) return;
    setMessages(messages.filter((_, idx) => idx !== i));
  };

  // ============================================================
  // VARIABLES
  // ============================================================

  const addVariable = () => {
    setVariables({ ...variables, '': '' });
  };

  const updateVariable = (oldKey, newKey, newValue) => {
    const copy = { ...variables };
    if (oldKey !== newKey) delete copy[oldKey];
    copy[newKey] = newValue;
    setVariables(copy);
  };

  const removeVariable = (key) => {
    const copy = { ...variables };
    delete copy[key];
    setVariables(copy);
  };

  // ============================================================
  // ASSERTIONS
  // ============================================================

  const addAssertion = () => {
    if (assertions.length >= MAX_ASSERTIONS) return;
    setAssertions([...assertions, emptyAssertion()]);
  };

  const updateAssertion = (i, patch) => {
    const copy = [...assertions];
    copy[i] = { ...copy[i], ...patch };
    setAssertions(copy);
  };

  const changeAssertionType = (i, newType) => {
    // Reset campos al cambiar tipo
    const copy = [...assertions];
    copy[i] = { type: newType };
    setAssertions(copy);
  };

  const removeAssertion = (i) => {
    if (assertions.length <= 1) return;
    setAssertions(assertions.filter((_, idx) => idx !== i));
  };

  // ============================================================
  // GUARDAR
  // ============================================================

  const handleSave = async () => {
    setError(null);

    // Validaciones mínimas de UX
    if (!name.trim()) {
      setError('El nombre es obligatorio');
      return;
    }
    const nonEmpty = messages.filter((m) => m.trim());
    if (nonEmpty.length === 0) {
      setError('Debe haber al menos 1 mensaje no vacío');
      return;
    }

    // Filtrar variables vacías
    const cleanVars = {};
    for (const [k, v] of Object.entries(variables)) {
      if (k.trim()) cleanVars[k] = v;
    }

    const payload = {
      name: name.trim(),
      description: description.trim() || null,
      input_messages: nonEmpty,
      initial_variables: cleanVars,
      assertions: assertions,
      enabled,
    };

    try {
      await onSave(payload);
    } catch (err) {
      const detail = err.response?.data?.detail;
      const msg = Array.isArray(detail)
        ? detail.map((e) => e.msg || JSON.stringify(e)).join(', ')
        : detail || err.message || 'Error guardando test';
      setError(msg);
    }
  };

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <div
      className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-navy border border-white/10 rounded-2xl shadow-card w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
          <h2 className="text-white text-lg font-semibold">
            {test ? 'Editar test' : 'Nuevo test'}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-white/50 hover:text-white transition-colors text-xl"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-4 overflow-y-auto flex-1 space-y-4">
          {/* Error */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-300 text-sm">
              ⚠️ {error}
            </div>
          )}

          {/* Nombre */}
          <label className="block">
            <span className="text-white/60 text-xs uppercase tracking-wider">
              Nombre *
            </span>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ej: Reserva válida"
              className="mt-2 w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-400/60"
            />
          </label>

          {/* Descripción */}
          <label className="block">
            <span className="text-white/60 text-xs uppercase tracking-wider">
              Descripción
            </span>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Opcional"
              className="mt-2 w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-400/60"
            />
          </label>

          {/* Mensajes */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-white/60 text-xs uppercase tracking-wider">
                Mensajes ({messages.length}/{MAX_MESSAGES})
              </span>
              <button
                type="button"
                onClick={addMessage}
                disabled={messages.length >= MAX_MESSAGES}
                className="text-xs text-cyan-400 hover:text-cyan-300 disabled:opacity-30"
              >
                + Añadir mensaje
              </button>
            </div>
            <div className="space-y-2">
              {messages.map((msg, i) => (
                <div key={i} className="flex items-center gap-2">
                  <span className="text-white/40 text-xs w-6 shrink-0">
                    {i + 1}.
                  </span>
                  <input
                    type="text"
                    value={msg}
                    onChange={(e) => updateMessage(i, e.target.value)}
                    placeholder="Mensaje del usuario"
                    className="flex-1 bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white text-sm focus:outline-none focus:border-cyan-400/60"
                  />
                  <button
                    type="button"
                    onClick={() => removeMessage(i)}
                    disabled={messages.length <= 1}
                    className="text-red-400 hover:text-red-300 text-sm px-2 disabled:opacity-30"
                    title="Eliminar mensaje"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Variables iniciales */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-white/60 text-xs uppercase tracking-wider">
                Variables iniciales
              </span>
              <button
                type="button"
                onClick={addVariable}
                className="text-xs text-cyan-400 hover:text-cyan-300"
              >
                + Añadir variable
              </button>
            </div>
            {Object.keys(variables).length === 0 ? (
              <div className="text-white/30 text-xs italic">
                Sin variables iniciales
              </div>
            ) : (
              <div className="space-y-2">
                {Object.entries(variables).map(([key, value], i) => (
                  <div key={i} className="flex items-center gap-2">
                    <input
                      type="text"
                      value={key}
                      onChange={(e) => updateVariable(key, e.target.value, value)}
                      placeholder="nombre"
                      className="w-32 bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white font-mono text-xs focus:outline-none focus:border-cyan-400/60"
                    />
                    <span className="text-white/40">=</span>
                    <input
                      type="text"
                      value={value}
                      onChange={(e) => updateVariable(key, key, e.target.value)}
                      placeholder="valor"
                      className="flex-1 bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white text-xs focus:outline-none focus:border-cyan-400/60"
                    />
                    <button
                      type="button"
                      onClick={() => removeVariable(key)}
                      className="text-red-400 hover:text-red-300 text-sm px-2"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Assertions */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-white/60 text-xs uppercase tracking-wider">
                Assertions ({assertions.length}/{MAX_ASSERTIONS})
              </span>
              <button
                type="button"
                onClick={addAssertion}
                disabled={assertions.length >= MAX_ASSERTIONS}
                className="text-xs text-cyan-400 hover:text-cyan-300 disabled:opacity-30"
              >
                + Añadir assertion
              </button>
            </div>
            <div className="space-y-3">
              {assertions.map((a, i) => (
                <div
                  key={i}
                  className="bg-white/5 rounded-lg p-3 space-y-2"
                >
                  <div className="flex items-center gap-2">
                    <select
                      value={a.type}
                      onChange={(e) => changeAssertionType(i, e.target.value)}
                      className="flex-1 bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white text-xs focus:outline-none focus:border-cyan-400/60"
                    >
                      {ASSERTION_TYPES.map((t) => (
                        <option key={t.value} value={t.value}>
                          {t.label}
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      onClick={() => removeAssertion(i)}
                      disabled={assertions.length <= 1}
                      className="text-red-400 hover:text-red-300 text-sm px-2 disabled:opacity-30"
                    >
                      ✕
                    </button>
                  </div>

                  {/* Campos según tipo */}
                  <div className="flex gap-2">
                    {a.type.includes('response') && (
                      <input
                        type="text"
                        value={a.value || ''}
                        onChange={(e) => updateAssertion(i, { value: e.target.value })}
                        placeholder="texto esperado"
                        className="flex-1 bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white text-xs focus:outline-none focus:border-cyan-400/60"
                      />
                    )}
                    {a.type.includes('node_') && (
                      <input
                        type="text"
                        value={a.node_id || ''}
                        onChange={(e) => updateAssertion(i, { node_id: e.target.value })}
                        placeholder="node_id"
                        className="flex-1 bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white font-mono text-xs focus:outline-none focus:border-cyan-400/60"
                      />
                    )}
                    {a.type.includes('variable') && (
                      <>
                        <input
                          type="text"
                          value={a.variable || ''}
                          onChange={(e) => updateAssertion(i, { variable: e.target.value })}
                          placeholder="nombre"
                          className="w-32 bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white font-mono text-xs focus:outline-none focus:border-cyan-400/60"
                        />
                        {a.type === 'variable_equals' && (
                          <>
                            <span className="text-white/40 self-center">=</span>
                            <input
                              type="text"
                              value={a.expected ?? ''}
                              onChange={(e) => updateAssertion(i, { expected: e.target.value })}
                              placeholder="valor"
                              className="flex-1 bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white text-xs focus:outline-none focus:border-cyan-400/60"
                            />
                          </>
                        )}
                      </>
                    )}
                    {a.type === 'max_steps' && (
                      <input
                        type="number"
                        value={a.max_steps ?? ''}
                        onChange={(e) =>
                          updateAssertion(i, { max_steps: parseInt(e.target.value) || 0 })
                        }
                        placeholder="máx pasos"
                        className="w-32 bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white text-xs focus:outline-none focus:border-cyan-400/60"
                      />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Enabled */}
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={enabled}
              onChange={(e) => setEnabled(e.target.checked)}
              className="w-4 h-4 cursor-pointer accent-cyan-400"
            />
            <span className="text-white/70 text-sm">
              Test habilitado (se ejecuta en run-all)
            </span>
          </label>
        </div>

        {/* Footer */}
        <div className="border-t border-white/10 px-6 py-3 flex items-center justify-end gap-2 bg-white/5">
          <Button variant="secondary" size="sm" onClick={onClose}>
            Cancelar
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? 'Guardando...' : test ? 'Actualizar' : 'Crear test'}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default TestEditor;
