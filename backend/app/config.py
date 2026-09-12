"""
Nuvora — Configuración centralizada
====================================
Lee variables de entorno y expone un único objeto `settings`.

Ventajas:
    - Una sola fuente de verdad para toda la app
    - Fácil de testear (se puede mockear)
    - No dispersa os.getenv por 20 archivos

Uso:
    from app.config import settings
    print(settings.ai.provider)
    print(settings.database_url)
"""

import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv


# Cargar .env una sola vez al importar el módulo
load_dotenv()


# ============================================================
# SECCIONES
# ============================================================


@dataclass(frozen=True)
class AIConfig:
    """
    Configuración de la capa de IA (Fase 14.7).

    IMPORTANTE: aquí NO se decide proveedor comercial por defecto.
    El proveedor activo se elige con AI_PROVIDER. Si mañana cambiamos
    de política comercial (gratis vs premium), NO cambia esta clase.
    """
    # Provider activo: "gemini" | "groq" | "deepseek"
    provider: str = "gemini"

    # API keys (opcionales: solo se valida la del provider activo en runtime)
    gemini_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None

    # Timeouts y límites
    timeout_seconds: int = 30
    max_retries: int = 2

    # Límites de entrada
    max_prompt_length: int = 2000
    max_bot_context_keys: int = 10
    max_bot_context_value_length: int = 500

    # Límites de salida
    max_tokens_output: int = 4000

    # Modelos por defecto por provider (se pueden sobreescribir)
    gemini_model: str = "gemini-2.5-flash"
    groq_model: str = "llama-3.3-70b-versatile"
    deepseek_model: str = "deepseek-chat"

    # Feature flag global: si false, endpoints /ai/* devuelven 503
    enabled: bool = True

    def get_api_key_for(self, provider: Optional[str] = None) -> Optional[str]:
        """Devuelve la API key del provider indicado (o del activo)."""
        p = (provider or self.provider).lower()
        if p == "gemini":
            return self.gemini_api_key
        if p == "groq":
            return self.groq_api_key
        if p == "deepseek":
            return self.deepseek_api_key
        return None

    def get_model_for(self, provider: Optional[str] = None) -> str:
        """Devuelve el modelo por defecto del provider indicado."""
        p = (provider or self.provider).lower()
        if p == "gemini":
            return self.gemini_model
        if p == "groq":
            return self.groq_model
        if p == "deepseek":
            return self.deepseek_model
        return "unknown"


@dataclass(frozen=True)
class AppConfig:
    """Configuración general de la app (ya existente, centralizada)."""
    name: str = "Nuvora API"
    version: str = "0.1.0"
    frontend_url: str = "https://nuvora-chi.vercel.app"
    database_url: str = "sqlite:///./nuvora.db"

    # Sub-configs
    ai: AIConfig = field(default_factory=AIConfig)


# ============================================================
# HELPERS
# ============================================================


def _env_bool(key: str, default: bool) -> bool:
    """Parsea booleans de env: '1' 'true' 'yes' 'on' → True."""
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        return int(raw)
    except (ValueError, TypeError):
        return default


# ============================================================
# SINGLETON — se construye una vez al importar
# ============================================================


def _build_ai_config() -> AIConfig:
    return AIConfig(
        provider=os.getenv("AI_PROVIDER", "gemini").lower(),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        groq_api_key=os.getenv("GROQ_API_KEY"),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
        timeout_seconds=_env_int("AI_TIMEOUT_SECONDS", 30),
        max_retries=_env_int("AI_MAX_RETRIES", 2),
        max_prompt_length=_env_int("AI_MAX_PROMPT_LENGTH", 2000),
        max_bot_context_keys=_env_int("AI_MAX_BOT_CONTEXT_KEYS", 10),
        max_bot_context_value_length=_env_int("AI_MAX_BOT_CONTEXT_VALUE_LENGTH", 500),
        max_tokens_output=_env_int("AI_MAX_TOKENS_OUTPUT", 4000),
        gemini_model=os.getenv("AI_GEMINI_MODEL", "gemini-2.5-flash"),
        groq_model=os.getenv("AI_GROQ_MODEL", "llama-3.3-70b-versatile"),
        deepseek_model=os.getenv("AI_DEEPSEEK_MODEL", "deepseek-chat"),
        enabled=_env_bool("AI_ENABLED", True),
    )


def _build_app_config() -> AppConfig:
    return AppConfig(
        name=os.getenv("APP_NAME", "Nuvora API"),
        version=os.getenv("APP_VERSION", "0.1.0"),
        frontend_url=os.getenv("FRONTEND_URL", "https://nuvora-chi.vercel.app"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./nuvora.db"),
        ai=_build_ai_config(),
    )


# Singleton global
settings = _build_app_config()


__all__ = ["settings", "AIConfig", "AppConfig"]
