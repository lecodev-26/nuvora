"""
Nuvora Core — AI: OpenAI Provider
====================================
Implementación del provider OpenAI (OpenAI-compatible, oficial).
"""

from app.config import settings
from app.core.ai.providers.base_openai_compatible import (
    BaseOpenAICompatibleProvider,
)
from app.core.ai.providers import register_provider


@register_provider("openai")
class OpenAIProvider(BaseOpenAICompatibleProvider):
    """Provider OpenAI (oficial, OpenAI-compatible)."""

    name = "openai"
    base_url = "https://api.openai.com/v1"

    def get_api_key(self) -> str | None:
        if self.api_key_override:
            return self.api_key_override
        return settings.ai.openai_api_key

    def get_model(self) -> str:
        return settings.ai.openai_model
