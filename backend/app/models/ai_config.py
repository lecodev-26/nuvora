"""
Nuvora — Schemas Pydantic para BYOK (Fase 14.7.4b)
====================================================
Contratos HTTP para la configuración de API keys propias del usuario.

SEGURIDAD:
    - El campo `api_key` (input) NUNCA se devuelve en responses.
    - La response solo indica `has_key: bool` para cada provider.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal


# ============================================================
# TIPOS
# ============================================================

AIProviderName = Literal["gemini", "groq", "deepseek"]

VALID_PROVIDERS = ("gemini", "groq", "deepseek")


# ============================================================
# REQUEST
# ============================================================

class AIConfigCreate(BaseModel):
    """Payload para crear/actualizar una API key propia."""
    provider: AIProviderName
    api_key: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="API key del provider. Se guardará cifrada.",
    )


# ============================================================
# RESPONSE
# ============================================================

class AIConfigItem(BaseModel):
    """Estado de un provider para el usuario."""
    provider: AIProviderName
    has_key: bool
    updated_at: datetime

    class Config:
        from_attributes = True


class AIConfigListResponse(BaseModel):
    """Lista de providers configurados por el usuario."""
    configs: list[AIConfigItem]
    system_provider: str = Field(
        ...,
        description="Provider por defecto del sistema (AI_PROVIDER del .env)",
    )


class AIConfigDeleteResponse(BaseModel):
    """Respuesta al borrar una config."""
    provider: AIProviderName
    deleted: bool


__all__ = [
    "AIProviderName",
    "VALID_PROVIDERS",
    "AIConfigCreate",
    "AIConfigItem",
    "AIConfigListResponse",
    "AIConfigDeleteResponse",
]
