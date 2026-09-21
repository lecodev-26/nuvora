"""
Nuvora — Telegram Channel: Schemas
====================================
Schemas Pydantic que parsean el Update crudo de Telegram.

FILOSOFÍA:
    - Solo VALIDAN y PARSEAN. Cero lógica de negocio.
    - Reflejan la estructura de la Bot API de Telegram.
    - Todos los campos opcionales salvo los imprescindibles.

REFERENCIA:
    https://core.telegram.org/bots/api#update

REGLA:
    Si Telegram cambia su esquema, se actualiza aquí.
    El mapper usa estos schemas para convertir a ChannelRequest.
"""

from typing import Optional
from pydantic import BaseModel, Field


# ============================================================
# COMPONENTES BÁSICOS
# ============================================================

class TelegramUser(BaseModel):
    """Usuario de Telegram (from)."""
    id: int
    is_bot: bool = False
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None


class TelegramChat(BaseModel):
    """Chat de Telegram."""
    id: int
    type: str  # "private" | "group" | "supergroup" | "channel"
    title: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class TelegramMessage(BaseModel):
    """Mensaje de Telegram."""
    message_id: int
    date: int
    chat: TelegramChat
    from_: Optional[TelegramUser] = Field(None, alias="from")
    text: Optional[str] = None
    # Otros campos (photo, audio, sticker, etc.) ignorados en MVP

    class Config:
        populate_by_name = True


# ============================================================
# UPDATE PRINCIPAL
# ============================================================

class TelegramUpdate(BaseModel):
    """
    Update de Telegram.

    Telegram envía esto al webhook cuando ocurre algo.
    En MVP solo procesamos updates con `message`.
    Otros campos (edited_message, callback_query, etc.) se ignoran.
    """
    update_id: int
    message: Optional[TelegramMessage] = None

    # ============================================================
    # HELPERS
    # ============================================================

    def is_text_message(self) -> bool:
        """
        True si el update es un mensaje de texto en chat privado
        enviado por un usuario humano (no un bot).
        """
        if not self.message:
            return False
        if not self.message.text:
            return False
        if self.message.chat.type != "private":
            return False
        if self.message.from_ and self.message.from_.is_bot:
            return False
        return True

    def get_from_user(self) -> Optional[TelegramUser]:
        """Devuelve el usuario remitente (o None si no aplica)."""
        return self.message.from_ if self.message else None


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "TelegramUser",
    "TelegramChat",
    "TelegramMessage",
    "TelegramUpdate",
]
