"""
Nuvora - Schemas Pydantic de Telegram (Fase 14.11)
====================================================
Contratos HTTP para los endpoints privados de integracion Telegram.

SEGURIDAD:
    - El token del bot NUNCA se devuelve por API.
    - En las responses solo aparece `token_configured: bool`.
    - El webhook_secret tampoco se devuelve (es interno).
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ============================================================
# REQUESTS
# ============================================================

class TelegramConnectRequest(BaseModel):
    """Payload para POST /bots/{bot_id}/telegram/connect."""
    token: str = Field(
        ...,
        min_length=10,
        max_length=200,
        description="Token del bot de Telegram (formato 123456:ABC...)",
        examples=["1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ"],
    )


# ============================================================
# RESPONSES
# ============================================================

class TelegramStatusResponse(BaseModel):
    """
    Estado actual de la integracion Telegram de un bot.

    NUNCA incluye el token ni el webhook_secret.
    """
    status: str = Field(
        ...,
        description="pending | connected | error | disconnected",
    )
    telegram_username: Optional[str] = None
    telegram_bot_id: Optional[str] = None
    is_active: bool = False
    token_configured: bool = Field(
        ...,
        description="True si hay un token guardado (nunca se devuelve el token)",
    )
    created_at: Optional[datetime] = None
    last_event_at: Optional[datetime] = None
    last_error: Optional[str] = None

    class Config:
        from_attributes = True


class TelegramConnectResponse(BaseModel):
    """Respuesta de POST /bots/{bot_id}/telegram/connect."""
    status: str
    telegram_username: Optional[str] = None
    telegram_bot_id: Optional[str] = None
    webhook_url: Optional[str] = None

    class Config:
        from_attributes = True


class TelegramTestResponse(BaseModel):
    """Respuesta de POST /bots/{bot_id}/telegram/test."""
    ok: bool
    id: Optional[int] = None
    username: Optional[str] = None
    first_name: Optional[str] = None


class TelegramDisconnectResponse(BaseModel):
    """Respuesta de POST /bots/{bot_id}/telegram/disconnect."""
    status: str
    is_active: bool


__all__ = [
    "TelegramConnectRequest",
    "TelegramStatusResponse",
    "TelegramConnectResponse",
    "TelegramTestResponse",
    "TelegramDisconnectResponse",
]
