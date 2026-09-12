"""
Nuvora Core — AI (Fase 14.7)
==============================
Capa de IA para el AI Workflow Designer.

Filosofía:
    - La IA NO ejecuta workflows.
    - La IA produce datos JSON estructurados.
    - WorkflowValidator (14.5.4) sigue siendo la autoridad.
    - Providers abstraídos.

Público:
    - AIProvider, AIRequest, AIResponse
    - Errores: AIError y subclases
    - JSON schemas internos
"""

from app.core.ai.provider import AIProvider, AIRequest, AIResponse
from app.core.ai.errors import (
    AIError,
    AIProviderError,
    AIInvalidOutputError,
    AIConfigError,
    AIUnavailableError,
)
from app.core.ai.schemas import (
    VALID_NODE_TYPES,
    WORKFLOW_JSON_SCHEMA,
    GENERATE_RESPONSE_SCHEMA,
    MODIFY_RESPONSE_SCHEMA,
    EXPLAIN_RESPONSE_SCHEMA,
    ANALYZE_RESPONSE_SCHEMA,
)

__all__ = [
    # Provider
    "AIProvider",
    "AIRequest",
    "AIResponse",
    # Errores
    "AIError",
    "AIProviderError",
    "AIInvalidOutputError",
    "AIConfigError",
    "AIUnavailableError",
    # Schemas
    "VALID_NODE_TYPES",
    "WORKFLOW_JSON_SCHEMA",
    "GENERATE_RESPONSE_SCHEMA",
    "MODIFY_RESPONSE_SCHEMA",
    "EXPLAIN_RESPONSE_SCHEMA",
    "ANALYZE_RESPONSE_SCHEMA",
]
