"""
Nuvora Core — AI: Prompts (Fase 14.7)
========================================
System prompts + builders de user prompts para cada tarea.

Tareas:
    - generate: crear workflow nuevo desde descripción
    - modify:   modificar workflow existente según instrucción
    - explain:  explicar un workflow en lenguaje humano
    - analyze:  detectar problemas + sugerir mejoras
"""

from app.core.ai.prompts.system import (
    SYSTEM_PROMPT_BASE,
    STRUCTURAL_RULES_SUMMARY,
)
from app.core.ai.prompts.generate import (
    GENERATE_USER_TEMPLATE,
    build_generate_prompt,
)
from app.core.ai.prompts.modify import (
    MODIFY_USER_TEMPLATE,
    build_modify_prompt,
)
from app.core.ai.prompts.explain import (
    EXPLAIN_USER_TEMPLATE,
    build_explain_prompt,
)
from app.core.ai.prompts.analyze import (
    ANALYZE_USER_TEMPLATE,
    build_analyze_prompt,
)

__all__ = [
    "SYSTEM_PROMPT_BASE",
    "STRUCTURAL_RULES_SUMMARY",
    "GENERATE_USER_TEMPLATE",
    "build_generate_prompt",
    "MODIFY_USER_TEMPLATE",
    "build_modify_prompt",
    "EXPLAIN_USER_TEMPLATE",
    "build_explain_prompt",
    "ANALYZE_USER_TEMPLATE",
    "build_analyze_prompt",
]
