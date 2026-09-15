"""
Nuvora Core — AI: DeepSeek Provider
=====================================
Implementación del provider DeepSeek (OpenAI-compatible).
"""

from app.config import settings
from app.core.ai.providers.base_openai_compatible import (
    BaseOpenAICompatibleProvider,
)
from app.core.ai.providers import register_provider


@register_provider("deepseek")
class DeepSeekProvider(BaseOpenAICompatibleProvider):
    """Provider DeepSeek (barato, OpenAI-compatible)."""

    name = "deepseek"
    base_url = "https://api.deepseek.com/v1"

    def get_api_key(self) -> str | None:
        return settings.ai.deepseek_api_key

    def get_model(self) -> str:
        return settings.ai.deepseek_model
