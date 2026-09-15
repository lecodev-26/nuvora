"""
Nuvora Core — AI: Ollama Provider
====================================
Implementación del provider Ollama (LLM local, OpenAI-compatible).

Ollama expone una API OpenAI-compatible en:
    http://localhost:11434/v1/chat/completions

NO requiere API key (es local).

IMPORTANTE:
    - Si el usuario final usa Ollama, debe tenerlo corriendo en su máquina.
    - En Render (producción) NO funciona porque Render no tiene acceso a
      localhost del usuario. Solo sirve para desarrollo o instalaciones
      self-hosted.
"""

from app.config import settings
from app.core.ai.providers.base_openai_compatible import (
    BaseOpenAICompatibleProvider,
)
from app.core.ai.providers import register_provider


@register_provider("ollama")
class OllamaProvider(BaseOpenAICompatibleProvider):
    """Provider Ollama (LLM local, OpenAI-compatible, sin key)."""

    name = "ollama"

    @property
    def base_url(self) -> str:
        # Dinámico: se lee de settings en cada instancia
        return settings.ai.get_ollama_base_url()

    def get_api_key(self) -> str | None:
        # Ollama no usa key; devolvemos un placeholder para que la base no falle.
        # Si hay override (BYOK), lo respetamos (aunque Ollama lo ignorará).
        if self.api_key_override:
            return self.api_key_override
        return "ollama-local-no-key-required"

    def get_model(self) -> str:
        return settings.ai.ollama_model

    def _build_headers(self, api_key: str) -> dict:
        # Ollama no valida la key; quitamos el Authorization
        return {
            "Content-Type": "application/json",
        }
