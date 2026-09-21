"""
Nuvora — Errores uniformes para /api/v1/* (Fase 14.10.8)
==========================================================
Formato de error:
    {
        "error": {
            "code": "INVALID_API_KEY",
            "message": "API Key is invalid."
        }
    }

USO:
    from app.core.api_errors import ApiError, ErrorCode

    raise ApiError(ErrorCode.INVALID_API_KEY)

Solo se aplica a rutas /api/v1/*. Los demás routers mantienen
su formato `{"detail": "..."}` por compatibilidad.
"""

from enum import Enum

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException


# ============================================================
# CÓDIGOS DE ERROR
# ============================================================

class ErrorCode(str, Enum):
    # Autenticación
    INVALID_API_KEY = "INVALID_API_KEY"
    REVOKED_API_KEY = "REVOKED_API_KEY"
    EXPIRED_API_KEY = "EXPIRED_API_KEY"

    # Estado del bot
    BOT_NOT_PUBLISHED = "BOT_NOT_PUBLISHED"
    NO_ACTIVE_WORKFLOW = "NO_ACTIVE_WORKFLOW"

    # Request
    INVALID_REQUEST = "INVALID_REQUEST"
    MESSAGE_TOO_LONG = "MESSAGE_TOO_LONG"

    # Sesión
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    SESSION_EXPIRED = "SESSION_EXPIRED"

    # Genéricos
    NOT_FOUND = "NOT_FOUND"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# Mapeo de ErrorCode → (status HTTP, mensaje por defecto)
ERROR_MAP = {
    ErrorCode.INVALID_API_KEY: (
        status.HTTP_401_UNAUTHORIZED, "API Key is invalid."
    ),
    ErrorCode.REVOKED_API_KEY: (
        status.HTTP_401_UNAUTHORIZED, "API Key has been revoked."
    ),
    ErrorCode.EXPIRED_API_KEY: (
        status.HTTP_401_UNAUTHORIZED, "API Key has expired."
    ),
    ErrorCode.BOT_NOT_PUBLISHED: (
        status.HTTP_409_CONFLICT, "Bot is not published."
    ),
    ErrorCode.NO_ACTIVE_WORKFLOW: (
        status.HTTP_409_CONFLICT, "Bot has no active workflow."
    ),
    ErrorCode.INVALID_REQUEST: (
        status.HTTP_400_BAD_REQUEST, "Invalid request."
    ),
    ErrorCode.MESSAGE_TOO_LONG: (
        status.HTTP_422_UNPROCESSABLE_ENTITY, "Message is too long."
    ),
    ErrorCode.SESSION_NOT_FOUND: (
        status.HTTP_404_NOT_FOUND, "Session not found."
    ),
    ErrorCode.SESSION_EXPIRED: (
        status.HTTP_404_NOT_FOUND, "Session has expired."
    ),
    ErrorCode.NOT_FOUND: (
        status.HTTP_404_NOT_FOUND, "Resource not found."
    ),
    ErrorCode.RATE_LIMITED: (
        status.HTTP_429_TOO_MANY_REQUESTS, "Too many requests."
    ),
    ErrorCode.INTERNAL_ERROR: (
        status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error."
    ),
}


# ============================================================
# EXCEPCIÓN CUSTOM
# ============================================================

class ApiError(HTTPException):
    """
    Excepción para errores de /api/v1/*.

    Hereda de HTTPException para que FastAPI la capte como error HTTP.
    El handler global la serializa con el formato uniforme.
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str = None,
        status_code: int = None,
        headers: dict = None,
    ):
        default_status, default_message = ERROR_MAP.get(
            code, (500, "Internal server error.")
        )
        self.code = code
        self.message = message or default_message
        self.status_code = status_code or default_status
        self.headers = headers

        # HTTPException espera "detail"; ponemos el mensaje
        super().__init__(status_code=self.status_code, detail=self.message, headers=headers)


# ============================================================
# HANDLER GLOBAL
# ============================================================

def api_exception_handler(request: Request, exc: ApiError) -> JSONResponse:
    """
    Serializa ApiError con el formato uniforme.
    Solo se activa cuando el error lo lanza un endpoint /api/v1/*.
    """
    body = {
        "error": {
            "code": exc.code.value,
            "message": exc.message,
        }
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=body,
        headers=exc.headers,
    )


# ============================================================
# REGISTRO
# ============================================================

def register_api_error_handlers(app) -> None:
    """
    Registra el handler de ApiError en la app FastAPI.

    Uso:
        from app.core.api_errors import register_api_error_handlers
        register_api_error_handlers(app)
    """
    app.add_exception_handler(ApiError, api_exception_handler)


__all__ = [
    "ErrorCode",
    "ApiError",
    "api_exception_handler",
    "register_api_error_handlers",
    "ERROR_MAP",
]
