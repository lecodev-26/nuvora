"""
Nuvora — Telegram Channel: Errores
====================================
Excepciones propias del canal Telegram.

Diseño:
    TelegramError (base)
    ├── TelegramAuthError       → token inválido / no autorizado
    ├── TelegramAPIError        → error devuelto por la API de Telegram
    └── TelegramNetworkError    → timeout / connection error

Regla:
    NO usar HTTPException de FastAPI aquí. Esta capa está aislada.
    El router que la use se encarga de mapear a HTTP.
"""


class TelegramError(Exception):
    """Base de todos los errores del canal Telegram."""
    pass


class TelegramAuthError(TelegramError):
    """
    Token inválido o no autorizado.

    Se lanza cuando Telegram responde 401 o cuando getMe() falla
    por token incorrecto. El llamador NO debe reintentar.
    """
    pass


class TelegramAPIError(TelegramError):
    """
    Error genérico devuelto por la API de Telegram.

    Ej: chat no encontrado, mensaje vacío, usuario bloqueado, etc.
    """
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class TelegramNetworkError(TelegramError):
    """
    Error de red (timeout, connection refused, DNS, etc.).

    El llamador PUEDE reintentar (el cliente ya lo hace 1 vez).
    """
    pass


__all__ = [
    "TelegramError",
    "TelegramAuthError",
    "TelegramAPIError",
    "TelegramNetworkError",
]
