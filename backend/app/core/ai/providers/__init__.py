"""
Nuvora Core — AI Providers (Fase 14.7.5)
==========================================
Registry + factory de providers de IA.

Soporta dos modos:
    1. Sistema (sin db/user_id): usa las keys del .env
    2. BYOK (con db/user_id): usa las keys propias del usuario si existen

Uso:
    from app.core.ai.providers import get_provider

    # Modo sistema
    provider = get_provider("gemini")
    response = provider.generate_json(request)

    # Modo BYOK
    provider = get_provider("gemini", db=db, user_id=user.id)
    response = provider.generate_json(request)
"""

from typing import Optional

from sqlalchemy.orm import Session

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


def _import_all_providers():
    """Importa todos los providers para que se registren."""
    from app.core.ai.providers import gemini  # noqa
    from app.core.ai.providers import groq  # noqa
    from app.core.ai.providers import deepseek  # noqa
    from app.core.ai.providers import openai  # noqa
    from app.core.ai.providers import mistral  # noqa
    from app.core.ai.providers import anthropic  # noqa
    from app.core.ai.providers import ollama  # noqa


def get_provider(
    name: Optional[str] = None,
    db: Optional[Session] = None,
    user_id: Optional[int] = None,
) -> AIProvider:
    """
    Devuelve una instancia del provider solicitado.

    Args:
        name: nombre del provider. Si es None, usa settings.ai.provider.
        db: sesión SQLAlchemy (necesaria para BYOK).
        user_id: ID del usuario (necesario para BYOK).

    Returns:
        Instancia del provider.

    Raises:
        AIConfigError: si el provider no está registrado.

    Modos:
        - Si NO se pasa db ni user_id → modo sistema.
        - Si se pasan AMBOS → resuelve la key con get_effective_api_key
          (BYOK si existe, fallback al sistema).
    """
    _import_all_providers()

    from app.config import settings

    provider_name = (name or settings.ai.provider).lower().strip()

    if provider_name not in _PROVIDER_REGISTRY:
        raise AIConfigError(
            f"Provider desconocido: '{provider_name}'. "
            f"Disponibles: {list(_PROVIDER_REGISTRY.keys())}"
        )

    provider_cls = _PROVIDER_REGISTRY[provider_name]

    # Resolver api_key_override si BYOK
    api_key_override: Optional[str] = None
    if db is not None and user_id is not None:
        try:
            from app.services.ai_config_service import get_effective_api_key
            api_key_override = get_effective_api_key(db, user_id, provider_name)
        except Exception:
            # Si falla la resolución BYOK, caemos al modo sistema
            api_key_override = None

    return provider_cls(api_key_override=api_key_override)


def list_available_providers() -> list[str]:
    """Devuelve la lista de providers registrados."""
    _import_all_providers()
    return sorted(_PROVIDER_REGISTRY.keys())


__all__ = [
    "get_provider",
    "register_provider",
    "list_available_providers",
]
