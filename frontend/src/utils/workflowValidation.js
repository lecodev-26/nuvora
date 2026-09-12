/**
 * workflowValidation — Validación UX del Workflow Builder.
 *
 * IMPORTANTE:
 *   Esta validación es SOLO para UX (feedback rápido al usuario).
 *   La validación AUTORITATIVA es la del backend 14.5.4 (WorkflowValidator).
 *   El frontend NO inventa reglas nuevas; replica las del backend para
 *   dar feedback sin esperar al servidor.
 *
 * NO modifica el workflow. Solo lee y devuelve errores/warnings.
 */

/**
 * @typedef {Object} ValidationIssue
 * @property {string} code       - identificador técnico ('missing_start', etc.)
 * @property {string} message    - mensaje humano para mostrar en UI
 * @property {string} [node_id]  - nodo al que se refiere (opcional)
 * @property {string} [edge_key] - transición (from→to) a la que se refiere (opcional)
 */

/**
 * Valida el estado actual del builder.
 * @param {Object} state - { nodes, transitions, workflowMetadata }
 * @returns {{ errors: ValidationIssue[], warnings: ValidationIssue[] }}
 */
export function validateWorkflow(state) {
  const { nodes = [], transitions = [], workflowMetadata = {} } = state;
  const errors = [];
  const warnings = [];

  // -------- 1. Metadata --------
  if (!workflowMetadata.name || !workflowMetadata.name.trim()) {
    errors.push({
      code: 'missing_name',
      message: 'El workflow debe tener un nombre.',
    });
  }

  // -------- 2. START --------
  const starts = nodes.filter((n) => n.type === 'start');
  if (starts.length === 0) {
    errors.push({
      code: 'missing_start',
      message: 'El workflow necesita exactamente 1 nodo START.',
    });
  } else if (starts.length > 1) {
    errors.push({
      code: 'multiple_starts',
      message: `Hay ${starts.length} nodos START (solo se permite 1).`,
    });
  }

  // -------- 3. END --------
  const ends = nodes.filter((n) => n.type === 'end');
  if (ends.length === 0) {
    errors.push({
      code: 'missing_end',
      message: 'El workflow necesita al menos 1 nodo END.',
    });
  }

  // -------- 4. node_id únicos --------
  const seen = new Set();
  const duplicates = new Set();
  for (const n of nodes) {
    if (seen.has(n.node_id)) duplicates.add(n.node_id);
    seen.add(n.node_id);
  }
  for (const dup of duplicates) {
    errors.push({
      code: 'duplicate_node_id',
      message: `node_id duplicado: '${dup}'`,
      node_id: dup,
    });
  }

  // -------- 5. Tipos válidos --------
  const VALID_TYPES = new Set([
    'start', 'message', 'question', 'condition', 'variable', 'response', 'end',
  ]);
  for (const n of nodes) {
    if (!VALID_TYPES.has(n.type)) {
      errors.push({
        code: 'invalid_node_type',
        message: `Nodo '${n.node_id}': tipo inválido '${n.type}'`,
        node_id: n.node_id,
      });
    }
  }

  // -------- 6. Config por tipo --------
  for (const n of nodes) {
    const cfg = n.config || {};
    if (n.type === 'message' || n.type === 'response') {
      if (!cfg.text || !String(cfg.text).trim()) {
        errors.push({
          code: 'missing_text',
          message: `Nodo '${n.node_id}' necesita texto.`,
          node_id: n.node_id,
        });
      }
    } else if (n.type === 'question') {
      if (!cfg.text || !String(cfg.text).trim()) {
        errors.push({
          code: 'missing_question_text',
          message: `Nodo '${n.node_id}' necesita el texto de la pregunta.`,
          node_id: n.node_id,
        });
      }
      if (!cfg.variable || !String(cfg.variable).trim()) {
        errors.push({
          code: 'missing_question_variable',
          message: `Nodo '${n.node_id}' necesita una variable.`,
          node_id: n.node_id,
        });
      }
    } else if (n.type === 'variable') {
      if (!cfg.name || !String(cfg.name).trim()) {
        errors.push({
          code: 'missing_variable_name',
          message: `Nodo '${n.node_id}' necesita un nombre de variable.`,
          node_id: n.node_id,
        });
      }
    } else if (n.type === 'condition') {
      if (!cfg.condition || !String(cfg.condition).trim()) {
        errors.push({
          code: 'missing_condition',
          message: `Nodo '${n.node_id}' necesita una condición.`,
          node_id: n.node_id,
        });
      } else {
        const basicErr = basicValidateCondition(cfg.condition);
        if (basicErr) {
          errors.push({
            code: 'invalid_condition',
            message: `Nodo '${n.node_id}': ${basicErr}`,
            node_id: n.node_id,
          });
        }
      }
    }
  }

  // -------- 7. Transiciones apuntan a nodos existentes --------
  const nodeIds = new Set(nodes.map((n) => n.node_id));
  for (const t of transitions) {
    if (!nodeIds.has(t.from_node_id)) {
      errors.push({
        code: 'transition_missing_from',
        message: `Transición desde nodo inexistente: '${t.from_node_id}'`,
        edge_key: `${t.from_node_id}→${t.to_node_id}`,
      });
    }
    if (!nodeIds.has(t.to_node_id)) {
      errors.push({
        code: 'transition_missing_to',
        message: `Transición hacia nodo inexistente: '${t.to_node_id}'`,
        edge_key: `${t.from_node_id}→${t.to_node_id}`,
      });
    }
  }

  // -------- 8. END sin transiciones salientes --------
  for (const n of nodes) {
    if (n.type === 'end') {
      const outs = transitions.filter((t) => t.from_node_id === n.node_id);
      if (outs.length > 0) {
        errors.push({
          code: 'end_with_outgoing',
          message: `Nodo END '${n.node_id}' no puede tener transiciones salientes.`,
          node_id: n.node_id,
        });
      }
    }
  }

  // -------- 9. START sin transiciones entrantes --------
  for (const n of nodes) {
    if (n.type === 'start') {
      const ins = transitions.filter((t) => t.to_node_id === n.node_id);
      if (ins.length > 0) {
        errors.push({
          code: 'start_with_incoming',
          message: `Nodo START '${n.node_id}' no puede tener transiciones entrantes.`,
          node_id: n.node_id,
        });
      }
    }
  }

  // -------- 10. CONDITION ≥ 2 salidas --------
  for (const n of nodes) {
    if (n.type === 'condition') {
      const outs = transitions.filter((t) => t.from_node_id === n.node_id);
      if (outs.length < 2) {
        errors.push({
          code: 'condition_few_outputs',
          message: `Nodo CONDITION '${n.node_id}' necesita al menos 2 salidas (tiene ${outs.length}).`,
          node_id: n.node_id,
        });
      }
    }
  }

  // -------- 11. Warnings (no bloquean guardar) --------
  // Nodos huérfanos (sin entradas ni salidas), excluyendo START/END
  for (const n of nodes) {
    if (n.type === 'start' || n.type === 'end') continue;
    const ins = transitions.filter((t) => t.to_node_id === n.node_id);
    const outs = transitions.filter((t) => t.from_node_id === n.node_id);
    if (ins.length === 0 && outs.length === 0) {
      warnings.push({
        code: 'orphan_node',
        message: `Nodo '${n.node_id}' no está conectado a nada.`,
        node_id: n.node_id,
      });
    }
  }

  // Nodos sin nombre (no es error, solo UX)
  for (const n of nodes) {
    if (!n.name || !String(n.name).trim()) {
      warnings.push({
        code: 'node_no_name',
        message: `Nodo '${n.node_id}' no tiene nombre descriptivo.`,
        node_id: n.node_id,
      });
    }
  }

  return { errors, warnings };
}

/**
 * Validación ligera de condición (misma sintaxis que backend 14.5.6).
 * @returns {string|null} mensaje de error o null si es válida
 */
export function basicValidateCondition(expr) {
  if (!expr || !expr.trim()) return 'La condición no puede estar vacía';
  const match = expr.match(/^\s*\S+\s*(==|!=|>=|<=|>|<)\s*.+$/);
  if (!match) {
    return 'Formato inválido. Se esperaba: variable operador valor (ej: age > 18)';
  }
  return null;
}

/**
 * Índice rápido: devuelve un Set con los node_id que tienen errores.
 * Útil para pintar bordes rojos en el canvas.
 */
export function getErrorNodeIds(validationResult) {
  const set = new Set();
  for (const e of validationResult.errors) {
    if (e.node_id) set.add(e.node_id);
  }
  return set;
}
