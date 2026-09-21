"""
Nuvora - Telegram Service (Fase 14.11.7)
==========================================
Lógica de negocio de la integración Telegram.

RESPONSABILIDADES:
    - connect()            conectar un bot Nuvora a un bot de Telegram
    - disconnect()         desconectar + deleteWebhook
    - get_status()         estado actual de la integración
    - test_connection()    prueba getMe() con el token guardado
    - resolve_by_secret()  usado por el webhook (sin JWT)
    - touch_last_event()   actualiza last_event_at

SEGURIDAD:
    - El token se cifra con encrypt_api_key (mismo que BYOK, 14.7).
    - El token NUNCA se devuelve por API.
    - Ownership verificado en todas las operaciones privadas.

ROLLBACK EN CONNECT:
    Si setWebhook() falla después de getMe() OK, NO se guarda
    nada en BD. La operación es atómica.

NO TOCA:
    - Core
    - WorkflowEngine
    - public_sessions
    - Conversation
"""

import logging
import secrets
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.config import settings
from app.models.db_models import Bot, TelegramIntegration
from app.services.ai_config_service import encrypt_api_key, decrypt_api_key
from app.channels.telegram.client import TelegramClient
from app.channels.telegram.errors import (
    TelegramError,
    TelegramAuthError,
    TelegramIntegrationError,
    TelegramAlreadyConnectedError,
    TelegramNotConnectedError,
)


logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTES
# ============================================================

# Duración del webhook_secret en caracteres (token_urlsafe(32) ~ 43).
WEBHOOK_SECRET_BYTES = 32

# Endpoint base del webhook (relativo al backend público).
WEBHOOK_PATH = "/webhooks/telegram"

# Timeout para llamadas a Telegram en operaciones de conexión.
CONNECT_TIMEOUT_SECONDS = 15


# ============================================================
# HELPERS DE OWNERSHIP (mismo patrón que api_keys)
# ============================================================

def _get_bot_or_404(db: Session, bot_id: int) -> Bot:
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")
    return bot


def _verify_bot_ownership(bot: Bot, user_id: int) -> None:
    if bot.user_id is not None:
        if bot.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para este bot",
            )
        return
    # Fallback: bots sin user_id (legacy) no pueden gestionarse
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para este bot",
    )


# ============================================================
# HELPERS INTERNOS
# ============================================================

def _build_webhook_url(secret: str) -> str:
    """Construye la URL completa del webhook."""
    base = settings.backend_public_url.rstrip("/")
    return f"{base}{WEBHOOK_PATH}/{secret}"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================
# CONNECT
# ============================================================

def connect(
    db: Session,
    user_id: int,
    bot_id: int,
    token: str,
) -> TelegramIntegration:
    """
    Conecta un bot Nuvora a un bot de Telegram.

    Pasos:
        1. Verifica ownership del bot.
        2. Comprueba que no hay integración activa (si la hay, error).
        3. Llama getMe(token) → valida token + obtiene telegram_bot_id/username.
        4. Genera webhook_secret.
        5. Cifra token.
        6. Construye webhook_url.
        7. Llama setWebhook(url, secret) → configura Telegram.
        8. Si TODO OK → guarda integración con status="connected".
        9. Si algo falla → NO guarda nada → rollback natural.

    Args:
        db: sesión SQLAlchemy.
        user_id: propietario del bot (JWT).
        bot_id: ID del bot Nuvora.
        token: token del bot de Telegram (formato "123456:ABC...").

    Returns:
        TelegramIntegration persistida.

    Raises:
        HTTPException 404: bot no existe.
        HTTPException 403: bot ajeno.
        TelegramAlreadyConnectedError: ya hay integración activa.
        TelegramAuthError: token inválido.
        TelegramAPIError: error de Telegram al configurar webhook.
        TelegramNetworkError: fallo de red.
    """
    # 1. Ownership
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, user_id)

    # 2. Integración existente
    existing = (
        db.query(TelegramIntegration)
        .filter(TelegramIntegration.bot_id == bot_id)
        .first()
    )
    if existing and existing.is_active:
        raise TelegramAlreadyConnectedError(
            f"El bot ya tiene una integración Telegram activa (@{existing.telegram_username or '?'})"
        )

    # 3. Validar token con getMe
    client = TelegramClient(token=token, timeout=CONNECT_TIMEOUT_SECONDS)
    try:
        bot_info = client.get_me()
    except TelegramAuthError as e:
        raise TelegramAuthError(f"Token inválido: {e}") from e
    except TelegramError as e:
        logger.warning("connect(): getMe falló: %s", e)
        raise

    telegram_bot_id = str(bot_info.get("id", ""))
    telegram_username = bot_info.get("username")

    # 4-5. Cifrar token + generar secret
    encrypted = encrypt_api_key(token)
    webhook_secret = secrets.token_urlsafe(WEBHOOK_SECRET_BYTES)

    # 6. Construir URL del webhook
    webhook_url = _build_webhook_url(webhook_secret)

    # 7. setWebhook en Telegram (si falla, NO guardamos nada)
    try:
        client.set_webhook(url=webhook_url, secret=webhook_secret)
    except TelegramError as e:
        logger.warning("connect(): setWebhook falló: %s", e)
        raise

    # 8. Guardar integración (todo OK hasta aquí)
    if existing:
        # Reutilizar el registro existente (no duplicar)
        existing.encrypted_token = encrypted
        existing.telegram_bot_id = telegram_bot_id
        existing.telegram_username = telegram_username
        existing.webhook_secret = webhook_secret
        existing.webhook_url = webhook_url
        existing.status = "connected"
        existing.is_active = True
        existing.last_error = None
        integration = existing
    else:
        integration = TelegramIntegration(
            bot_id=bot_id,
            telegram_bot_id=telegram_bot_id,
            telegram_username=telegram_username,
            encrypted_token=encrypted,
            webhook_secret=webhook_secret,
            webhook_url=webhook_url,
            status="connected",
            is_active=True,
        )
        db.add(integration)

    db.commit()
    db.refresh(integration)

    logger.info(
        "Telegram conectado: bot_id=%s telegram=@%s",
        bot_id, telegram_username,
    )
    return integration


# ============================================================
# DISCONNECT
# ============================================================

def disconnect(db: Session, user_id: int, bot_id: int) -> TelegramIntegration:
    """
    Desconecta el bot de Telegram.

    Pasos:
        1. Verifica ownership.
        2. Busca integración (debe existir).
        3. deleteWebhook() con token descifrado (best-effort).
        4. Marca status="disconnected", is_active=False.

    Nota: deleteWebhook() es best-effort. Si falla (token inválido,
    red), igualmente desactivamos la integración en Nuvora.
    """
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, user_id)

    integration = (
        db.query(TelegramIntegration)
        .filter(TelegramIntegration.bot_id == bot_id)
        .first()
    )
    if not integration:
        raise TelegramNotConnectedError("No hay integración Telegram para este bot")

    # Intentar deleteWebhook (best-effort)
    try:
        token = decrypt_api_key(integration.encrypted_token)
        client = TelegramClient(token=token, timeout=CONNECT_TIMEOUT_SECONDS)
        client.delete_webhook()
    except Exception as e:
        logger.warning(
            "disconnect(): deleteWebhook falló (ignorado): %s", e,
        )

    integration.status = "disconnected"
    integration.is_active = False
    integration.last_error = None
    db.commit()
    db.refresh(integration)

    logger.info("Telegram desconectado: bot_id=%s", bot_id)
    return integration


# ============================================================
# GET STATUS
# ============================================================

def get_status(db: Session, user_id: int, bot_id: int) -> Optional[TelegramIntegration]:
    """
    Devuelve el estado actual de la integración (o None si no existe).
    NUNCA devuelve el token.
    """
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, user_id)

    return (
        db.query(TelegramIntegration)
        .filter(TelegramIntegration.bot_id == bot_id)
        .first()
    )


# ============================================================
# TEST CONNECTION
# ============================================================

def test_connection(db: Session, user_id: int, bot_id: int) -> dict:
    """
    Prueba la conexión con Telegram usando el token guardado.

    Devuelve dict con info del bot (id, username, first_name).
    """
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, user_id)

    integration = (
        db.query(TelegramIntegration)
        .filter(TelegramIntegration.bot_id == bot_id)
        .first()
    )
    if not integration:
        raise TelegramNotConnectedError("No hay integración Telegram para este bot")

    token = decrypt_api_key(integration.encrypted_token)
    client = TelegramClient(token=token, timeout=CONNECT_TIMEOUT_SECONDS)
    bot_info = client.get_me()

    return {
        "id": bot_info.get("id"),
        "username": bot_info.get("username"),
        "first_name": bot_info.get("first_name"),
    }


# ============================================================
# RESOLVER POR SECRET (webhook, sin JWT)
# ============================================================

def resolve_by_secret(db: Session, secret: str) -> Optional[TelegramIntegration]:
    """
    Busca una integración activa por webhook_secret.

    Usado por el webhook entrante de Telegram. Devuelve None si:
        - No existe ninguna integración con ese secret.
        - La integración está inactiva o desconectada.
    """
    if not secret or not isinstance(secret, str):
        return None

    integration = (
        db.query(TelegramIntegration)
        .filter(
            TelegramIntegration.webhook_secret == secret,
            TelegramIntegration.is_active.is_(True),
            TelegramIntegration.status == "connected",
        )
        .first()
    )
    return integration


# ============================================================
# TOUCH LAST EVENT
# ============================================================

def touch_last_event(db: Session, integration: TelegramIntegration) -> None:
    """
    Actualiza last_event_at. Silencioso si falla (no debe romper el flujo).
    """
    try:
        integration.last_event_at = _now_utc()
        db.commit()
    except Exception as e:
        logger.warning("touch_last_event falló: %s", e)
        db.rollback()


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "connect",
    "disconnect",
    "get_status",
    "test_connection",
    "resolve_by_secret",
    "touch_last_event",
    "WEBHOOK_SECRET_BYTES",
    "WEBHOOK_PATH",
]
