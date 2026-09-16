"""
Nuvora Core — AI: Prompt de Generación de Tests
==================================================
Prompt para que la IA genere DEFINICIONES de tests a partir de un workflow.

FILOSOFÍA:
    - La IA NO ejecuta workflows.
    - Solo genera JSON de definiciones de tests.
    - La validación real la hace Pydantic (models/test.py).

Tipos de assertions disponibles (10):
    - response_contains       → value
    - response_equals         → value
    - response_not_contains   → value
    - node_visited            → node_id
    - node_not_visited        → node_id
    - variable_equals         → variable + expected
    - variable_exists         → variable
    - variable_not_exists     → variable
    - reaches_end             → (sin campos)
    - max_steps               → max_steps
"""

import json
from typing import Any


GENERATE_TESTS_USER_TEMPLATE = """TAREA: Genera definiciones de tests para este workflow.

WORKFLOW (JSON):
{workflow_json}

INSTRUCCIONES:
1. Analiza el workflow: entiende qué hace y qué caminos puede tomar.
2. Genera entre 3 y 5 tests que cubran:
   a) El camino principal (happy path)
   b) Al menos un caso con CONDITION (si existe)
   c) Al menos un caso con QUESTION (variables)
   d) Un caso de error o borde (si tiene sentido)
3. Cada test debe tener:
   - name: nombre corto y descriptivo
   - description: qué verifica
   - input_messages: lista de strings (máx 5 mensajes por test)
   - initial_variables: dict (para simular variables previas)
   - assertions: lista de assertions (usa los 10 tipos disponibles)
4. NO inventes nodos. Usa SOLO los node_id que existen en el workflow.
5. Si un nodo QUESTION pregunta algo, simula la respuesta en las variables iniciales.

TIPOS DE ASSERTIONS (usa exactamente estos nombres):
{{
  "type": "response_contains",       "value": "texto esperado"
  "type": "response_equals",         "value": "texto exacto"
  "type": "response_not_contains",   "value": "texto no esperado"
  "type": "node_visited",            "node_id": "node_id_lógico"
  "type": "node_not_visited",        "node_id": "node_id_lógico"
  "type": "variable_equals",         "variable": "nombre", "expected": "valor"
  "type": "variable_exists",         "variable": "nombre"
  "type": "variable_not_exists",     "variable": "nombre"
  "type": "reaches_end"
  "type": "max_steps",               "max_steps": 50
}}

Devuelve un JSON con esta estructura EXACTA:
{{
  "generated": [
    {{
      "name": "string (máx 200 chars)",
      "description": "string (opcional)",
      "input_messages": ["string", "..."],
      "initial_variables": {{}},
      "assertions": [{{"type": "...", ...}}],
      "enabled": true
    }}
  ],
  "count": 5,
  "notes": ["nota opcional 1", "nota opcional 2"]
}}

IMPORTANTE:
- `count` debe coincidir con el número real de tests en `generated`.
- `notes` puede ser [] si no hay notas.
- Cada test debe tener al menos 1 assertion.
"""


def build_generate_tests_prompt(workflow_data: dict) -> str:
    """
    Construye el prompt de usuario para generar tests.

    Args:
        workflow_data: dict con 'nodes' y 'transitions' (formato engine).

    Returns:
        String con el prompt final listo para enviar al provider.
    """
    workflow_json = json.dumps(workflow_data, indent=2, ensure_ascii=False)
    return GENERATE_TESTS_USER_TEMPLATE.format(workflow_json=workflow_json)


__all__ = ["build_generate_tests_prompt", "GENERATE_TESTS_USER_TEMPLATE"]
