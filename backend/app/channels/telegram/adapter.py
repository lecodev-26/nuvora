"""
Nuvora — Telegram Channel: TelegramAdapter
============================================
Adaptador que conecta Telegram con el Core de Nuvora.

RESPONSABILIDADES:
    - to_request():   Update de Telegram → ChannelRequest universal
    - send_response(): ChannelResponse → mensaje de Telegram

FILOSOFÍA:
    - Es SOLO un traductor. No conoce Core ni WorkflowEngine.
    - No tiene lógica de negocio.
    - Orquesta mapper + client.
    - Fácil de mockear en tests.

REGLA ARQUITECTÓNICA (14.11):
    El Core NUNCA debe saber que Telegram existe.
    Este adapter es la única frontera.

USO:
    adapter = TelegramAdapter(token="123:ABC...")

    # Update → ChannelRequest
    request = adapter.to_request(update, bot_id=5)

    # ... (el Core procesa y devuelve ChannelResponse) ...

    # ChannelResponse → Telegram
    adapter.send_response(response, chat_id=111)
"""

import logging

from app.core.contracts import ChannelRequest, ChannelResponse
from app.channels.telegram.client import TelegramClient
from app.channels.telegram.errors import TelegramError
from app.channels.telegram.mapper import update_to_channel_request
from app.channels.telegram.schemas import TelegramUpdate


logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTES
# ============================================================

# Fallback cuando el Core no devuelve `answer` (bot inactivo, error, etc.)
FALLBACK_ANSWER = (
    "Lo siento, no he podido procesar tu mensaje. "
    "Inténtalo de nuevo en unos segundos."
)

# Identificador del canal (consistente con Conversation.channel).
CHANNEL_NAME = "telegram"


# ============================================================
# ADAPTER
# ============================================================

class TelegramAdapter:
    """
    Adaptador Telegram <-> Nuvora Core.

    Instanciado con un token de bot de Telegram. Cada webhook recibido
    se procesa con una instancia nueva (o reutilizable dentro del mismo
    request).
    """

    def __init__(self, token: str):
        self._client = TelegramClient(token=token)

    # ============================================================
    # UPDATE → CHANNELREQUEST
    # ============================================================

    def to_request(
        self,
        update: TelegramUpdate,
        bot_id: int,
    ) -> ChannelRequest | None:
        """
        Convierte un TelegramUpdate a ChannelRequest universal.

        Delega en el mapper. Devuelve None si el update no debe
        procesarse (grupo, sin texto, de bot, etc.).

        Args:
            update: Update ya parseado por schemas.
            bot_id: ID del bot Nuvora al que pertenece la integración.

        Returns:
            ChannelRequest o None.
        """
        return update_to_channel_request(update, bot_id=bot_id)

    # ============================================================
    # CHANNELRESPONSE → TELEGRAM
    # ============================================================

    def send_response(
        self,
        response: ChannelResponse,
        chat_id: int | str,
    ) -> bool:
        """
        Envía la respuesta del Core a un chat de Telegram.

        Si `response.answer` está vacío o es None, envía un
        fallback genérico para no dejar al usuario sin respuesta.

        Args:
            response: ChannelResponse del Core.
            chat_id: ID del chat de Telegram al que responder.

        Returns:
            True si el mensaje se envió correctamente.
            False si hubo un error (se loguea el motivo).
        """
        text = (response.answer or "").strip()
        if not text:
            logger.info(
                "Telegram chat_id=%s: respuesta vacía del Core → usando fallback",
                chat_id,
            )
            text = FALLBACK_ANSWER

        try:
            self._client.send_message(chat_id=chat_id, text=text)
            return True
        except TelegramError as e:
            logger.warning(
                "Telegram chat_id=%s: fallo al enviar respuesta: %s",
                chat_id, e,
            )
            return False
        except Exception as e:
            # Nunca debe romper el webhook por un fallo inesperado aquí
            logger.exception(
                "Telegram chat_id=%s: error inesperado al enviar respuesta: %s",
                chat_id, e,
            )
            return False

    # ============================================================
    # ACCESO AL CLIENT (para tests / uso avanzado)
    # ============================================================

    @property
    def client(self) -> TelegramClient:
        """Devuelve el TelegramClient subyacente."""
        return self._client


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "TelegramAdapter",
    "FALLBACK_ANSWER",
    "CHANNEL_NAME",
]
