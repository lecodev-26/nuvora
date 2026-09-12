"""
Nuvora Core — AI: Prompt de Análisis
=======================================
Prompt para analizar un workflow y detectar problemas + sugerir mejoras.

IMPORTANTE:
    - El análisis de la IA es INFORMATIVO, no autoritativo.
    - La validación estructural real la hace WorkflowValidator (14.5.4).
    - Este análisis solo detecta cosas de calidad/UX que el validator no ve.
"""

import json
from app.models.ai import GeneratedWorkflow


ANALYZE_USER_TEMPLATE = """TAREA: Analiza este workflow y devuelve warnings + sugerencias.

WORKFLOW (JSON):
{workflow_json}

QUÉ DETECTAR (warnings):
- Nodos que no están conectados a nada (huérfanos).
- Variables que se recogen pero nunca se usan después.
- Ramas que terminan abruptamente sin response antes de end.
- Condiciones que probablemente nunca se cumplirán dado el contexto.
- Preguntas que podrían ser ambiguas para el usuario final.
- Falta de mensaje de bienvenida o despedida.

QUÉ SUGERIR (suggestions):
- Mejoras opcionales que harían el workflow más útil o claro.
- Añadidos que aportarían valor sin complicar (ej: confirmación final).
- Buenas prácticas de UX conversacional.

REGLAS:
1. NO repitas warnings del validator estructural (esos ya se detectan antes).
2. NO inventes problemas que no existan.
3. Sé específico: referencia node_id concretos.
4. Sé breve: máximo 5 warnings, máximo 5 suggestions.
5. Si no hay warnings, devuelve una lista vacía.

Devuelve un JSON con esta estructura:
{{
  "warnings": ["..."],
  "suggestions": ["..."]
}}
"""


def build_analyze_prompt(workflow: GeneratedWorkflow) -> str:
    """Construye el prompt de usuario para analizar un workflow."""
    workflow_json = json.dumps(workflow.model_dump(), indent=2, ensure_ascii=False)
    return ANALYZE_USER_TEMPLATE.format(workflow_json=workflow_json)


__all__ = ["ANALYZE_USER_TEMPLATE", "build_analyze_prompt"]
