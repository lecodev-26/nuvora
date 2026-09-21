"""
Nuvora Core — API Auth (Fase 14.10.5)
========================================
Dependencia FastAPI para autenticar peticiones a /api/v1/*.

FLUJO:
    Authorization: Bearer nvr_live_xxx
        ↓
    extract_bearer_token()
        ↓
    resolve_api_key() (ApiKeyService)
        ↓
    ApiKeyContext(api_key, bot)
        ↓
    endpoint

SEGURIDAD:
    - Solo acepta "Bearer <token>" (no query params ni X-API-Key).
    - Nunca revela si la key existe vs si está revocada (todas 401).
    - El endpoint nunca ve el token (solo el api_key obj).

USO:
    from app.core.api_auth import ApiKeyContext, get_api_key_context

    @router.post("/api/v1/chat")
    def chat(
        ctx: ApiKeyContext = Depends(get_api_key_context),
        ...
    ):
        bot = ctx.bot
        ...
"""

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.db_models import ApiKey, Bot
from app.services.api_key_service import resolve_api_key
from app.core.api_errors import ApiError, ErrorCode


# ============================================================
# CONTEXTO
# ============================================================

@dataclass
class ApiKeyContext:
    """
    Contexto de una petición autenticada con API Key.

    Se pasa como dependencia a los endpoints de /api/v1/*.
    """
    api_key: ApiKey
    bot: Bot


# ============================================================
# HELPER — Extraer token
# ============================================================

def extract_bearer_token(authorization: Optional[str]) -> str:
    """
    Extrae el token del header 'Authorization: Bearer xxx'.

    Args:
        authorization: valor del header (o None).

    Returns:
        El token sin "Bearer ".

    Raises:
        HTTPException 401: si no hay header, formato incorrecto, o vacío.
    """
    if not authorization:
        raise ApiError(
            code=ErrorCode.INVALID_API_KEY,
            message="Falta el header Authorization",
        )

    parts = authorization.strip().split()
    if len(parts) != 2:
        raise ApiError(
            code=ErrorCode.INVALID_API_KEY,
            message="Formato de Authorization inválido",
        )

    scheme, token = parts
    if scheme.lower() != "bearer":
        raise ApiError(
            code=ErrorCode.INVALID_API_KEY,
            message="Esquema de autorización inválido (se espera Bearer)",
        )

    if not token:
        raise ApiError(
            code=ErrorCode.INVALID_API_KEY,
            message="Token vacío",
        )

    return token


# ============================================================
# DEPENDENCIA PRINCIPAL
# ============================================================

def get_api_key_context(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> ApiKeyContext:
    """
    Dependencia FastAPI: resuelve ApiKey + Bot desde el header Authorization.

    Uso:
        @router.post("/api/v1/chat")
        def chat(ctx: ApiKeyContext = Depends(get_api_key_context)):
            bot = ctx.bot
            ...

    Raises:
        HTTPException 401: header ausente, formato incorrecto o key inválida.
    """
    token = extract_bearer_token(authorization)
    api_key, bot = resolve_api_key(db, token)
    return ApiKeyContext(api_key=api_key, bot=bot)


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "ApiKeyContext",
    "extract_bearer_token",
    "get_api_key_context",
]
