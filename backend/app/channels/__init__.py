"""
Nuvora — Channels package.

Cada canal de Nuvora (widget, API, Telegram, ...) implementa aquí su
Adapter que traduce entre su formato nativo y los contratos
universales del Core (ChannelRequest / ChannelResponse).

Regla arquitectónica:
    El Core NO conoce ningún canal específico.
    Los canales NO meten lógica de negocio en el Core.
    La frontera son los contratos universales.
"""

from app.channels.base import ChannelAdapter

__all__ = ["ChannelAdapter"]
