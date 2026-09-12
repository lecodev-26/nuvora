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
"""

from app.core.ai.provider import AIProvider, AIRequest, AIResponse
from app.core.ai.errors import (
    AIError,
    AIProviderError,
    AIInvalidOutputError,
    AIConfigError,
    AIUnavailableError,
)

__all__ = [
    "AIProvider",
    "AIRequest",
    "AIResponse",
    "AIError",
    "AIProviderError",
    "AIInvalidOutputError",
    "AIConfigError",
    "AIUnavailableError",
]
