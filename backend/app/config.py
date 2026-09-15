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

    Providers soportados:
        - gemini     (Google, API propia)
        - groq       (OpenAI-compatible, ultrarrápido)
        - deepseek   (OpenAI-compatible, barato)
        - openai     (OpenAI-compatible, estándar de facto)
        - mistral    (OpenAI-compatible, europeo)
        - anthropic  (API propia, Claude)
        - ollama     (OpenAI-compatible, local, sin key)
    """
    # Provider activo
    provider: str = "gemini"

    # API keys (solo la del provider activo se valida en runtime)
    gemini_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    mistral_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    # Ollama no requiere API key (local); solo base_url
    ollama_base_url: Optional[str] = None

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
    openai_model: str = "gpt-4o-mini"
    mistral_model: str = "mistral-small-latest"
    anthropic_model: str = "claude-3-5-haiku-latest"
    ollama_model: str = "llama3.2"
    ollama_base_url_default: str = "http://localhost:11434/v1"

    # Feature flag global: si false, endpoints /ai/* devuelven 503
    enabled: bool = True

    # Rate limiting (14.7.13)
    rate_limit_enabled: bool = True
    rate_limit_generate: int = 10       # /ai/workflows/generate por hora
    rate_limit_modify: int = 20         # /ai/workflows/modify por hora
    rate_limit_explain: int = 30        # /ai/workflows/explain por hora
    rate_limit_analyze: int = 30        # /ai/workflows/analyze por hora
    rate_limit_templates_list: int = 100   # GET /ai/templates por hora
    rate_limit_templates_instantiate: int = 50  # POST /ai/templates/{id}/instantiate por hora

    def get_api_key_for(self, provider: Optional[str] = None) -> Optional[str]:
        """Devuelve la API key del provider indicado (o del activo)."""
        p = (provider or self.provider).lower()
        if p == "gemini":
            return self.gemini_api_key
        if p == "groq":
            return self.groq_api_key
        if p == "deepseek":
            return self.deepseek_api_key
        if p == "openai":
            return self.openai_api_key
        if p == "mistral":
            return self.mistral_api_key
        if p == "anthropic":
            return self.anthropic_api_key
        if p == "ollama":
            # Ollama no requiere key (local); devolvemos un placeholder
            # para que el BaseOpenAICompatibleProvider no rechace la petición
            return "ollama-local-no-key-required"
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
        if p == "openai":
            return self.openai_model
        if p == "mistral":
            return self.mistral_model
        if p == "anthropic":
            return self.anthropic_model
        if p == "ollama":
            return self.ollama_model
        return "unknown"

    def get_ollama_base_url(self) -> str:
        """Devuelve la base_url de Ollama (con fallback)."""
        return self.ollama_base_url or self.ollama_base_url_default


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
        # API keys
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        groq_api_key=os.getenv("GROQ_API_KEY"),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL"),
        # Timeouts
        timeout_seconds=_env_int("AI_TIMEOUT_SECONDS", 30),
        max_retries=_env_int("AI_MAX_RETRIES", 2),
        # Límites
        max_prompt_length=_env_int("AI_MAX_PROMPT_LENGTH", 2000),
        max_bot_context_keys=_env_int("AI_MAX_BOT_CONTEXT_KEYS", 10),
        max_bot_context_value_length=_env_int("AI_MAX_BOT_CONTEXT_VALUE_LENGTH", 500),
        max_tokens_output=_env_int("AI_MAX_TOKENS_OUTPUT", 4000),
        # Modelos
        gemini_model=os.getenv("AI_GEMINI_MODEL", "gemini-2.5-flash"),
        groq_model=os.getenv("AI_GROQ_MODEL", "llama-3.3-70b-versatile"),
        deepseek_model=os.getenv("AI_DEEPSEEK_MODEL", "deepseek-chat"),
        openai_model=os.getenv("AI_OPENAI_MODEL", "gpt-4o-mini"),
        mistral_model=os.getenv("AI_MISTRAL_MODEL", "mistral-small-latest"),
        anthropic_model=os.getenv("AI_ANTHROPIC_MODEL", "claude-3-5-haiku-latest"),
        ollama_model=os.getenv("AI_OLLAMA_MODEL", "llama3.2"),
        ollama_base_url_default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        enabled=_env_bool("AI_ENABLED", True),
        # Rate limiting
        rate_limit_enabled=_env_bool("AI_RATE_LIMIT_ENABLED", True),
        rate_limit_generate=_env_int("AI_RATE_LIMIT_GENERATE", 10),
        rate_limit_modify=_env_int("AI_RATE_LIMIT_MODIFY", 20),
        rate_limit_explain=_env_int("AI_RATE_LIMIT_EXPLAIN", 30),
        rate_limit_analyze=_env_int("AI_RATE_LIMIT_ANALYZE", 30),
        rate_limit_templates_list=_env_int("AI_RATE_LIMIT_TEMPLATES_LIST", 100),
        rate_limit_templates_instantiate=_env_int("AI_RATE_LIMIT_TEMPLATES_INSTANTIATE", 50),
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
