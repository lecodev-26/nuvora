"""
Nuvora Core — AI: Mistral Provider
=====================================
Implementación del provider Mistral (OpenAI-compatible, europeo).
"""

from app.config import settings
from app.core.ai.providers.base_openai_compatible import (
    BaseOpenAICompatibleProvider,
)
from app.core.ai.providers import register_provider


@register_provider("mistral")
class MistralProvider(BaseOpenAICompatibleProvider):
    """Provider Mistral (europeo, OpenAI-compatible)."""

    name = "mistral"
    base_url = "https://api.mistral.ai/v1"

    def get_api_key(self) -> str | None:
        return settings.ai.mistral_api_key

    def get_model(self) -> str:
        return settings.ai.mistral_model
