"""
Nuvora Core — AI: Prompt de Explicación
==========================================
Prompt para explicar un workflow en lenguaje humano.
"""

import json
from app.models.ai import GeneratedWorkflow


EXPLAIN_USER_TEMPLATE = """TAREA: Explica en lenguaje humano qué hace este workflow.

WORKFLOW (JSON):
{workflow_json}

INSTRUCCIONES:
1. Explica el flujo paso a paso: qué nodo va después de cuál, y por qué.
2. Explica el propósito de las preguntas (question) y qué variables recogen.
3. Explica las bifurcaciones (condition) y sus consecuencias.
4. Usa un lenguaje claro, sin jerga técnica.
5. Sé conciso: máximo 6 párrafos cortos.
6. No inventes funcionalidades que el workflow no tenga.

Devuelve un JSON con esta estructura:
{{
  "explanation": "string (explicación completa en lenguaje humano)"
}}
"""


def build_explain_prompt(workflow: GeneratedWorkflow) -> str:
    """Construye el prompt de usuario para explicar un workflow."""
    workflow_json = json.dumps(workflow.model_dump(), indent=2, ensure_ascii=False)
    return EXPLAIN_USER_TEMPLATE.format(workflow_json=workflow_json)


__all__ = ["EXPLAIN_USER_TEMPLATE", "build_explain_prompt"]
