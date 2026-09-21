"""
Nuvora — Telegram Channel (Fase 14.11).

Punto de entrada del canal Telegram. Exporta las piezas públicas
del módulo.

USO:
    from app.channels.telegram import TelegramAdapter
    adapter = TelegramAdapter(token="123:ABC...")
"""

from app.channels.telegram.adapter import TelegramAdapter
from app.channels.telegram.client import TelegramClient
from app.channels.telegram.errors import (
    TelegramError,
    TelegramAuthError,
    TelegramAPIError,
    TelegramNetworkError,
)
from app.channels.telegram.mapper import update_to_channel_request
from app.channels.telegram.schemas import (
    TelegramUser,
    TelegramChat,
    TelegramMessage,
    TelegramUpdate,
)

__all__ = [
    "TelegramAdapter",
    "TelegramClient",
    "TelegramError",
    "TelegramAuthError",
    "TelegramAPIError",
    "TelegramNetworkError",
    "update_to_channel_request",
    "TelegramUser",
    "TelegramChat",
    "TelegramMessage",
    "TelegramUpdate",
]
