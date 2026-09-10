"""
Nuvora Core — Contratos universales de entrada/salida.
El Core NO conoce ningún canal específico (widget, Telegram, etc.).
Solo conoce ChannelRequest y ChannelResponse.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any


class ChannelRequest(BaseModel):
    """
    Contrato universal de entrada al Core.
    Cualquier canal (widget, link, Telegram, WhatsApp) traduce a este formato.
    """
    bot_id: int
    session_id: Optional[str] = None
    message: str
    channel: str = "widget"  # widget | link | telegram | whatsapp | api
    metadata: Optional[dict[str, Any]] = None


class ChannelResponse(BaseModel):
    """
    Contrato universal de salida del Core.
    El canal que invocó el Core traduce esto a su formato.
    """
    answer: Optional[str] = None
    found: bool = False
    metadata: Optional[dict[str, Any]] = None
