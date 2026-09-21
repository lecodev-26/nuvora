"""
Nuvora — Channel Adapter base.

Contrato mínimo que cualquier canal (widget, API, Telegram, ...) debe
respetar para traducir su formato nativo a/desde los contratos
universales del Core (ChannelRequest / ChannelResponse).

FILOSOFÍA:
    - El Core NO conoce canales específicos.
    - Cada canal implementa su propio Adapter.
    - Esta clase es solo una guía estructural. NO impone herencia
      estricta. Cada canal puede implementar sus métodos a su manera
      mientras respete los contratos universales.

NO AÑADIR AQUÍ:
    - Lógica de canales específicos (Telegram, WhatsApp, ...).
    - Lógica de negocio.
    - Dependencias externas.

Regla (14.11 y posteriores):
    Si para implementar un canal hay que tocar el Core, la
    arquitectura está fallando.
"""

from typing import Protocol, Any
from app.core.contracts import ChannelRequest, ChannelResponse


class ChannelAdapter(Protocol):
    """
    Protocolo estructural de un Channel Adapter.

    Cualquier canal que quiera integrarse en Nuvora debe poder:
        1. Convertir su mensaje nativo a ChannelRequest.
        2. Convertir ChannelResponse a su formato nativo y enviarlo.

    Esta clase NO se hereda obligatoriamente. Es solo una guía.
    """

    # Identificador del canal. Ej: "widget", "api", "telegram".
    channel: str

    def to_request(self, raw: Any) -> ChannelRequest:
        """
        Convierte un mensaje nativo del canal a ChannelRequest.

        Args:
            raw: mensaje en formato nativo del canal (Update de Telegram,
                 payload HTTP del widget, etc.).

        Returns:
            ChannelRequest listo para pasar al Core.
        """
        ...

    def send_response(self, response: ChannelResponse, raw: Any) -> None:
        """
        Convierte ChannelResponse a formato del canal y lo envía.

        Args:
            response: respuesta del Core.
            raw: contexto del mensaje original (chat_id de Telegram, etc.).
        """
        ...


__all__ = ["ChannelAdapter"]
