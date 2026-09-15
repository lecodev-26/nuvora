"""
Nuvora Core — AI: Groq Provider
=================================
Implementación del provider Groq (OpenAI-compatible).
"""

from app.config import settings
from app.core.ai.providers.base_openai_compatible import (
    BaseOpenAICompatibleProvider,
)
from app.core.ai.providers import register_provider


@register_provider("groq")
class GroqProvider(BaseOpenAICompatibleProvider):
    """Provider Groq (rápido, OpenAI-compatible)."""

    name = "groq"
    base_url = "https://api.groq.com/openai/v1"

    def get_api_key(self) -> str | None:
        if self.api_key_override:
            return self.api_key_override
        return settings.ai.groq_api_key

    def get_model(self) -> str:
        return settings.ai.groq_model
