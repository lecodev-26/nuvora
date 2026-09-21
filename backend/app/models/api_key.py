"""
Nuvora — Schemas Pydantic de Nuvora API (Fase 14.10)
======================================================
Contratos HTTP para la API pública y la gestión de API Keys.

SEGURIDAD:
    - El secret de la API key solo se devuelve UNA VEZ (ApiKeyCreatedResponse).
    - Las responses normales solo exponen `key_prefix`, nunca el hash ni el secret.
    - El chat público NO devuelve información interna del workflow.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal


# ============================================================
# API KEY — CREAR
# ============================================================

class ApiKeyCreate(BaseModel):
    """Payload para crear una nueva API Key."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre descriptivo de la key",
        examples=["Mi web", "Bot de Telegram", "Automatización interna"],
    )


# ============================================================
# API KEY — RESPUESTAS (sin secret)
# ============================================================

class ApiKeyResponse(BaseModel):
    """
    Datos de una API Key existente.
    NUNCA incluye el secret ni el hash.
    """
    id: int
    name: str
    key_prefix: str = Field(
        ...,
        description="Prefijo visible (ej: nvr_live_ab12)",
    )
    created_at: datetime
    last_used_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True


class ApiKeyCreatedResponse(BaseModel):
    """
    Respuesta al CREAR una API Key.
    Esta es la ÚNICA VEZ que se devuelve el secret completo.
    """
    id: int
    name: str
    key: str = Field(
        ...,
        description="API Key completa. Guárdala: no volverá a mostrarse.",
    )
    key_prefix: str
    created_at: datetime
    warning: str = Field(
        default="Guarda esta clave. No volverá a mostrarse.",
    )


class ApiKeyListResponse(BaseModel):
    """Lista de API Keys de un bot."""
    keys: list[ApiKeyResponse]
    total: int


# ============================================================
# API PÚBLICA — CHAT
# ============================================================

class ChatRequest(BaseModel):
    """Payload para POST /api/v1/chat."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Mensaje del usuario (máx 2000 chars)",
        examples=["Hola", "¿Qué servicios ofrecéis?"],
    )
    session_id: Optional[str] = Field(
        None,
        min_length=1,
        max_length=64,
        description="ID de sesión para conversación multi-turno (opcional). Si se omite, se crea una nueva.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )


class ChatResponse(BaseModel):
    """
    Respuesta del bot.
    NUNCA expone workflow_id, node_id, variables internas, prompts, etc.
    """
    answer: str
    session_id: str
    status: Literal["completed", "waiting_input", "error"] = "completed"


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "ApiKeyCreate",
    "ApiKeyResponse",
    "ApiKeyCreatedResponse",
    "ApiKeyListResponse",
    "ChatRequest",
    "ChatResponse",
]
