"""
Nuvora Core — AI Providers (Fase 14.7.5)
==========================================
Registry + factory de providers de IA.

Uso:
    from app.core.ai.providers import get_provider

    provider = get_provider("gemini")
    response = provider.generate_json(request)
"""

from typing import Optional

from app.core.ai.provider import AIProvider
from app.core.ai.errors import AIConfigError


# ============================================================
# REGISTRY (se llena al importar los módulos)
# ============================================================

_PROVIDER_REGISTRY: dict[str, type[AIProvider]] = {}


def register_provider(name: str):
    """
    Decorador para registrar un provider en el registry.

    Uso:
        @register_provider("gemini")
        class GeminiProvider(AIProvider):
            ...
    """
    def decorator(cls: type[AIProvider]) -> type[AIProvider]:
        _PROVIDER_REGISTRY[name.lower()] = cls
        return cls
    return decorator


def get_provider(name: Optional[str] = None) -> AIProvider:
    """
    Devuelve una instancia del provider solicitado.

    Args:
        name: nombre del provider ("gemini", "groq", "deepseek"...).
              Si es None, usa settings.ai.provider.

    Returns:
        Instancia del provider.

    Raises:
        AIConfigError: si el provider no está registrado.
    """
    # Importar los providers para que se registren
    from app.core.ai.providers import gemini  # noqa
    from app.core.ai.providers import groq  # noqa
    from app.core.ai.providers import deepseek  # noqa
    from app.core.ai.providers import openai  # noqa
    from app.core.ai.providers import mistral  # noqa
    from app.core.ai.providers import anthropic  # noqa
    from app.core.ai.providers import ollama  # noqa

    from app.config import settings

    provider_name = (name or settings.ai.provider).lower().strip()

    if provider_name not in _PROVIDER_REGISTRY:
        raise AIConfigError(
            f"Provider desconocido: '{provider_name}'. "
            f"Disponibles: {list(_PROVIDER_REGISTRY.keys())}"
        )

    provider_cls = _PROVIDER_REGISTRY[provider_name]
    return provider_cls()


def list_available_providers() -> list[str]:
    """Devuelve la lista de providers registrados."""
    # Importar para asegurar registro
    from app.core.ai.providers import gemini  # noqa
    from app.core.ai.providers import groq  # noqa
    from app.core.ai.providers import deepseek  # noqa
    from app.core.ai.providers import openai  # noqa
    from app.core.ai.providers import mistral  # noqa
    from app.core.ai.providers import anthropic  # noqa
    from app.core.ai.providers import ollama  # noqa

    return sorted(_PROVIDER_REGISTRY.keys())


__all__ = [
    "get_provider",
    "register_provider",
    "list_available_providers",
]
