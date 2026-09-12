"""
Nuvora Core — AI: Prompt de Generación
========================================
Prompt para generar un workflow nuevo desde cero a partir de
una descripción en lenguaje natural.
"""

from typing import Optional
from app.models.ai import BotContext


GENERATE_USER_TEMPLATE = """TAREA: Genera un workflow nuevo a partir de la siguiente descripción.

DESCRIPCIÓN DEL USUARIO:
{prompt}

{bot_context_section}

INSTRUCCIONES:
1. Interpreta la descripción y diseña un workflow que cumpla EXACTAMENTE con lo que el usuario pide.
2. Si algo es ambiguo, toma la decisión más razonable e inclúyela en "warnings".
3. No añadas funcionalidades que el usuario no haya pedido.
4. Mantén el workflow simple: prefiere pocos nodos bien conectados a muchos innecesarios.
5. Usa node_id descriptivos cuando aporten claridad (ej: "ask_name", "check_age").

Devuelve un JSON con esta estructura:
{{
  "workflow": {{
    "name": "string",
    "description": "string",
    "nodes": [{{ "node_id": "...", "type": "...", "name": "...", "config": {{...}} }}],
    "transitions": [{{ "from_node_id": "...", "to_node_id": "...", "condition": "...", "label": "...", "order": 0 }}]
  }},
  "explanation": "string (2-4 frases explicando qué hace el workflow)",
  "warnings": ["..."]
}}
"""


def build_generate_prompt(
    prompt: str,
    bot_context: Optional[BotContext] = None,
) -> str:
    """
    Construye el prompt de usuario para la tarea de generación.

    Args:
        prompt: descripción del usuario.
        bot_context: contexto opcional del bot (limitado).

    Returns:
        String con el prompt final listo para enviar al provider.
    """
    bot_context_section = ""
    if bot_context:
        parts = []
        if bot_context.bot_name:
            parts.append(f"- Nombre del bot: {bot_context.bot_name}")
        if bot_context.description:
            parts.append(f"- Descripción del negocio: {bot_context.description}")
        if bot_context.business_type:
            parts.append(f"- Tipo de negocio: {bot_context.business_type}")
        if bot_context.tone:
            parts.append(f"- Tono deseado: {bot_context.tone}")
        if bot_context.language and bot_context.language != "es":
            parts.append(f"- Idioma: {bot_context.language}")

        if parts:
            bot_context_section = (
                "CONTEXTO DEL BOT (opcional, úsalo para personalizar):\n"
                + "\n".join(parts)
            )

    return GENERATE_USER_TEMPLATE.format(
        prompt=prompt,
        bot_context_section=bot_context_section,
    )


__all__ = ["GENERATE_USER_TEMPLATE", "build_generate_prompt"]
