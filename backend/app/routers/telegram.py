"""
Nuvora - Router /bots/{bot_id}/telegram (Fase 14.11.8)
========================================================
Endpoints PRIVADOS (JWT) para gestionar la integracion Telegram.

REGLAS:
    - Autenticacion JWT obligatoria.
    - Multi-tenant: 401 sin auth, 403 bot ajeno, 404 inexistente.
    - El token NUNCA se devuelve.

MAQUEO DE ERRORES:
    TelegramAlreadyConnectedError  -> 409 Conflict
    TelegramNotConnectedError      -> 404 Not Found
    TelegramAuthError              -> 400 Bad Request
    TelegramAPIError               -> 502 Bad Gateway
    TelegramNetworkError           -> 504 Gateway Timeout
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.db_models import User
from app.models.telegram import (
    TelegramConnectRequest,
    TelegramConnectResponse,
    TelegramStatusResponse,
    TelegramTestResponse,
    TelegramDisconnectResponse,
)
from app.services.auth import get_current_user
from app.services import telegram_service
from app.channels.telegram.errors import (
    TelegramError,
    TelegramAuthError,
    TelegramAPIError,
    TelegramNetworkError,
    TelegramIntegrationError,
    TelegramAlreadyConnectedError,
    TelegramNotConnectedError,
)


router = APIRouter(
    prefix="/bots",
    tags=["telegram"],
    responses={
        401: {"description": "No autenticado (JWT faltante o invalido)"},
        403: {"description": "Bot ajeno"},
        404: {"description": "Bot o integracion no encontrada"},
        409: {"description": "Conflicto (ya hay integracion activa)"},
        502: {"description": "Error devuelto por Telegram"},
        504: {"description": "Timeout al llamar a Telegram"},
    },
)


# ============================================================
# HELPER: mapeo de excepciones del canal a HTTP
# ============================================================

def _handle_telegram_error(e: TelegramError) -> None:
    """Traduce excepciones de Telegram a HTTPException."""
    if isinstance(e, TelegramAlreadyConnectedError):
        raise HTTPException(status_code=409, detail=str(e))
    if isinstance(e, TelegramNotConnectedError):
        raise HTTPException(status_code=404, detail=str(e))
    if isinstance(e, TelegramAuthError):
        raise HTTPException(status_code=400, detail=str(e))
    if isinstance(e, TelegramNetworkError):
        raise HTTPException(status_code=504, detail=str(e))
    if isinstance(e, TelegramAPIError):
        raise HTTPException(status_code=502, detail=str(e))
    if isinstance(e, TelegramIntegrationError):
        raise HTTPException(status_code=400, detail=str(e))
    # Fallback
    raise HTTPException(status_code=500, detail=f"Error Telegram: {e}")


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/{bot_id}/telegram", response_model=TelegramStatusResponse | None)
def get_telegram_status(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Devuelve el estado actual de la integracion Telegram del bot.

    Si el bot no tiene integracion configurada, devuelve `null`.
    El token NUNCA se devuelve.
    """
    integration = telegram_service.get_status(
        db=db, user_id=current_user.id, bot_id=bot_id,
    )
    if not integration:
        return None

    return TelegramStatusResponse(
        status=integration.status,
        telegram_username=integration.telegram_username,
        telegram_bot_id=integration.telegram_bot_id,
        is_active=integration.is_active,
        token_configured=bool(integration.encrypted_token),
        created_at=integration.created_at,
        last_event_at=integration.last_event_at,
        last_error=integration.last_error,
    )


@router.post(
    "/{bot_id}/telegram/connect",
    response_model=TelegramConnectResponse,
    status_code=201,
)
def post_telegram_connect(
    bot_id: int,
    data: TelegramConnectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Conecta un bot Nuvora a un bot de Telegram.

    Pasos (delegados al service):
        1. Verifica ownership.
        2. getMe() valida el token.
        3. setWebhook() configura Telegram.
        4. Guarda la integracion cifrada.
    """
    try:
        integration = telegram_service.connect(
            db=db,
            user_id=current_user.id,
            bot_id=bot_id,
            token=data.token,
        )
    except TelegramError as e:
        _handle_telegram_error(e)

    return TelegramConnectResponse(
        status=integration.status,
        telegram_username=integration.telegram_username,
        telegram_bot_id=integration.telegram_bot_id,
        webhook_url=integration.webhook_url,
    )


@router.post(
    "/{bot_id}/telegram/test",
    response_model=TelegramTestResponse,
)
def post_telegram_test(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Prueba la conexion con Telegram usando el token guardado.
    Devuelve info del bot (getMe).
    """
    try:
        info = telegram_service.test_connection(
            db=db, user_id=current_user.id, bot_id=bot_id,
        )
    except TelegramError as e:
        _handle_telegram_error(e)

    return TelegramTestResponse(
        ok=True,
        id=info.get("id"),
        username=info.get("username"),
        first_name=info.get("first_name"),
    )


@router.post(
    "/{bot_id}/telegram/disconnect",
    response_model=TelegramDisconnectResponse,
)
def post_telegram_disconnect(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Desconecta el bot de Telegram.

    Llama deleteWebhook() en Telegram (best-effort) y marca
    la integracion como inactiva.
    """
    try:
        integration = telegram_service.disconnect(
            db=db, user_id=current_user.id, bot_id=bot_id,
        )
    except TelegramError as e:
        _handle_telegram_error(e)

    return TelegramDisconnectResponse(
        status=integration.status,
        is_active=integration.is_active,
    )


__all__ = ["router"]
