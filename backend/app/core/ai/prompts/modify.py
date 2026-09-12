"""
Nuvora Core — AI: Prompt de Modificación
==========================================
Prompt para modificar un workflow existente según una instrucción
en lenguaje natural.

REGLA CRÍTICA:
    - Preservar todos los nodos y transiciones que NO necesiten cambios.
    - Solo modificar lo mínimo necesario para cumplir la instrucción.
    - Mantener los node_id existentes siempre que sea posible.
"""

import json
from app.models.ai import GeneratedWorkflow


MODIFY_USER_TEMPLATE = """TAREA: Modifica el workflow existente según la instrucción del usuario.

WORKFLOW ACTUAL (JSON):
{workflow_json}

INSTRUCCIÓN DEL USUARIO:
{instruction}

REGLAS DE MODIFICACIÓN:
1. Preserva TODOS los nodos y transiciones que no sea necesario cambiar.
2. Solo modifica lo mínimo indispensable para cumplir la instrucción.
3. Mantén los node_id existentes siempre que sea posible.
4. Si añades nodos, usa node_id descriptivos y únicos.
5. Si eliminas nodos, elimina también sus transiciones asociadas.
6. El workflow resultante DEBE cumplir TODAS las reglas estructurales.
7. Si la instrucción es ambigua, haz la interpretación más razonable
   y añade una nota en "warnings".

Devuelve un JSON con esta estructura:
{{
  "workflow": {{
    "name": "string",
    "description": "string",
    "nodes": [...],
    "transitions": [...]
  }},
  "explanation": "string (explica qué cambios hiciste)",
  "warnings": ["..."]
}}
"""


def build_modify_prompt(
    workflow: GeneratedWorkflow,
    instruction: str,
) -> str:
    """Construye el prompt de usuario para modificar un workflow."""
    workflow_json = json.dumps(workflow.model_dump(), indent=2, ensure_ascii=False)
    return MODIFY_USER_TEMPLATE.format(
        workflow_json=workflow_json,
        instruction=instruction,
    )


__all__ = ["MODIFY_USER_TEMPLATE", "build_modify_prompt"]
