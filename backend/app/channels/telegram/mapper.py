"""
Nuvora — Telegram Channel: Mapper
===================================
Convierte un TelegramUpdate en un ChannelRequest universal.

FILOSOFÍA:
    - Función pura. Sin efectos secundarios.
    - Sin acceso a BD, red ni estado global.
    - Testeable al 100%.

REGLAS DE NEGOCIO:
    - Solo se procesan mensajes de TEXTO en chats PRIVADOS.
    - Solo se procesan mensajes de usuarios humanos (no bots).
    - Los comandos /start se limpian de prefijo si vienen solos.
    - Mensajes que excedan MAX_TELEGRAM_MESSAGE_LENGTH se truncan.
    - Devuelve None para updates que NO deben procesarse.

REGLA ARQUITECTÓNICA:
    El mapper NO sabe nada del Core ni de negocio.
    Solo transforma datos. El bot_id lo recibe del webhook.
"""

import logging
from typing import Optional

from app.core.contracts import ChannelRequest
from app.channels.telegram.schemas import TelegramUpdate


logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTES
# ============================================================

# Longitud máxima del mensaje enviado al Core.
# Consistente con ChatRequest de Nuvora API (14.10).
MAX_TELEGRAM_MESSAGE_LENGTH = 2000

# Canal identificador (consistente con Conversation.channel).
CHANNEL_NAME = "telegram"


# ============================================================
# HELPERS INTERNOS
# ============================================================

def _clean_start_command(text: str) -> str:
    """
    Limpia comandos de Telegram del texto.

    - "/start" (solo) → "" (vacío, se tratará como saludo genérico)
    - "/start hola"   → "hola"
    - "hola"          → "hola" (sin cambios)
    - "/menu opcion"  → "opcion" (para futuros comandos)

    Regla: si empieza con "/<comando>", se quita ese prefijo.
    """
    text = text.strip()
    if not text.startswith("/"):
        return text

    # Quitar el comando (hasta el primer espacio)
    parts = text.split(maxsplit=1)
    if len(parts) == 1:
        # Solo "/comando" → texto vacío
        return ""
    return parts[1].strip()


def _truncate_if_needed(text: str) -> str:
    """Trunca el texto al límite máximo si excede."""
    if len(text) <= MAX_TELEGRAM_MESSAGE_LENGTH:
        return text
    truncated = text[:MAX_TELEGRAM_MESSAGE_LENGTH].rstrip()
    logger.warning(
        "Telegram: mensaje truncado de %d a %d chars",
        len(text), MAX_TELEGRAM_MESSAGE_LENGTH,
    )
    return truncated


# ============================================================
# MAPPER PRINCIPAL
# ============================================================

def update_to_channel_request(
    update: TelegramUpdate,
    bot_id: int,
) -> Optional[ChannelRequest]:
    """
    Convierte un TelegramUpdate a ChannelRequest universal.

    Args:
        update: Update ya parseado por los schemas.
        bot_id: ID del bot Nuvora al que pertenece la integración.

    Returns:
        ChannelRequest listo para pasar al Core, o None si el update
        no debe procesarse.

    Returns None si:
        - No es un mensaje de texto.
        - No es un chat privado.
        - El remitente es un bot.
        - El texto queda vacío tras limpiar comandos.
    """
    # 1. Validar que es un mensaje de texto procesable
    if not update.is_text_message():
        logger.debug(
            "Telegram update_id=%s ignorado: no es texto privado de usuario humano",
            update.update_id,
        )
        return None

    msg = update.message
    user = update.get_from_user()

    # 2. Limpiar comandos (/start, /menu, ...)
    cleaned_text = _clean_start_command(msg.text or "")

    # 3. Si tras limpiar queda vacío, usamos un saludo genérico
    #    (típico caso: usuario pulsa /start y no escribe nada)
    if not cleaned_text:
        cleaned_text = "/start"
        logger.debug(
            "Telegram update_id=%s: comando sin texto → usando '/start' como mensaje",
            update.update_id,
        )

    # 4. Truncar si excede el límite
    cleaned_text = _truncate_if_needed(cleaned_text)

    # 5. Construir metadata (NO entra en el prompt del Core)
    metadata = {
        "telegram_update_id": update.update_id,
        "telegram_message_id": msg.message_id,
        "telegram_chat_id": msg.chat.id,
        "telegram_chat_type": msg.chat.type,
    }
    if user:
        metadata["telegram_user_id"] = user.id
        if user.username:
            metadata["telegram_username"] = user.username
        if user.first_name:
            metadata["telegram_first_name"] = user.first_name
        if user.last_name:
            metadata["telegram_last_name"] = user.last_name
        if user.language_code:
            metadata["telegram_language_code"] = user.language_code

    # 6. Devolver ChannelRequest universal
    return ChannelRequest(
        bot_id=bot_id,
        session_id=None,  # El session helper lo asigna en el webhook
        message=cleaned_text,
        channel=CHANNEL_NAME,
        metadata=metadata,
    )


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "update_to_channel_request",
    "MAX_TELEGRAM_MESSAGE_LENGTH",
    "CHANNEL_NAME",
]
