"""
Nuvora - Webhook publico de Telegram (Fase 14.11.9)
=====================================================
Endpoint que Telegram llama cuando un usuario escribe al bot.

ENDPOINT:
    POST /webhooks/telegram/{secret}

SEGURIDAD:
    - Verifica el secret de la URL contra el header
      `X-Telegram-Bot-Api-Secret-Token` que Telegram envia.
    - Ambos deben coincidir con TelegramIntegration.webhook_secret.
    - Sin JWT (es un webhook externo).

FLUJO:
    Update de Telegram
        |
    validar secret
        |
    idempotencia (telegram_updates UNIQUE)
        |
    mapper -> ChannelRequest
        |
    get_or_create session (channel=telegram, external_id=chat_id)
        |
    WorkflowEngine.run()
        |
    TelegramAdapter.send_response()
        |
    200 OK (SIEMPRE, salvo secret invalido)

REGLA DE ORO DE WEBHOOKS:
    Devolver 200 rapido, aunque algo falle internamente.
    Telegram reintenta si no recibe 200 → no queremos reintentos
    infinitos por errores de negocio.
    EXCEPTO si el secret es invalido → 403/404 (no es Telegram de verdad).

NO CONOCE:
    - Core logic
    - WorkflowEngine internals
    - Detalles del negocio del bot
"""

import json
import logging

from fastapi import APIRouter, Depends, Header, Request, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.db_models import TelegramIntegration, TelegramUpdate
from app.services import telegram_service
from app.services.public_session import (
    get_or_create_by_external,
    append_user_message,
    append_bot_message,
)
from app.services.public_resolver import (
    get_active_workflow,
    build_public_workflow_dict,
)
from app.core.workflows.engine import WorkflowEngine
from app.core.workflows.errors import (
    WorkflowValidationError,
    WorkflowExecutionError,
    MaxStepsExceeded,
    ConditionError,
)
from app.core.public_rate_limit import (
    check_public_rate_limit,
    PublicRateLimitExceeded,
)
from app.channels.telegram import (
    TelegramAdapter,
    TelegramUpdate as TelegramUpdateSchema,
)
from app.channels.telegram.errors import TelegramError


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/webhooks",
    tags=["telegram-webhook"],
)


# ============================================================
# CONSTANTES
# ============================================================

PUBLIC_MAX_STEPS = 50
WEBHOOK_RATE_LIMIT_INTEGRATION = 120   # por integration_id
WEBHOOK_RATE_LIMIT_IP = 240            # por IP

FALLBACK_BOT_NOT_PUBLISHED = (
    "Este bot no esta disponible en este momento. "
    "Contacta con el administrador."
)
FALLBACK_NO_WORKFLOW = (
    "Este bot no esta configurado todavia. "
    "Contacta con el administrador."
)
FALLBACK_INTERNAL_ERROR = (
    "Lo siento, ha ocurrido un error procesando tu mensaje. "
    "Intentalo de nuevo en unos segundos."
)


# ============================================================
# HELPERS
# ============================================================

def _get_client_ip(request: Request) -> str:
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _check_rate_limit(integration_id: int, request: Request) -> None:
    """Rate limiting por integration_id + por IP."""
    ip = _get_client_ip(request)
    try:
        check_public_rate_limit(
            key=f"tg:{integration_id}",
            bucket="telegram_webhook",
            max_per_window=WEBHOOK_RATE_LIMIT_INTEGRATION,
        )
        check_public_rate_limit(
            key=ip,
            bucket="telegram_webhook_ip",
            max_per_window=WEBHOOK_RATE_LIMIT_IP,
        )
    except PublicRateLimitExceeded as e:
        logger.warning("Webhook Telegram rate-limited: %s", e)
        raise HTTPException(status_code=429, detail="Rate limited")


def _save_update_idempotent(
    db: Session,
    integration: TelegramIntegration,
    update_id: int,
) -> bool:
    """
    Intenta registrar el update_id.

    Returns:
        True  → no estaba procesado, se ha registrado (procesar)
        False → ya estaba procesado (ignorar)
    """
    row = TelegramUpdate(
        integration_id=integration.id,
        update_id=update_id,
    )
    db.add(row)
    try:
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        return False


def _extract_reply(result) -> str:
    """
    Extrae el texto de respuesta del resultado del WorkflowEngine.
    Mismo patron que /public/bots/{id}/message y /api/v1/chat.
    """
    outputs = result.outputs or []
    for out in reversed(outputs):
        if out.get("type") == "response" and out.get("text"):
            return out["text"]
    for out in reversed(outputs):
        if out.get("type") == "message" and out.get("text"):
            return out["text"]
    for out in reversed(outputs):
        if out.get("text"):
            return out["text"]
    return FALLBACK_INTERNAL_ERROR


# ============================================================
# ENDPOINT
# ============================================================

@router.post("/telegram/{secret}")
async def telegram_webhook(
    secret: str,
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(None, alias="X-Telegram-Bot-Api-Secret-Token"),
    db: Session = Depends(get_db),
):
    """
    Recibe un Update de Telegram y procesa el mensaje.

    Seguridad:
        - El secret de la URL debe coincidir con el header
          `X-Telegram-Bot-Api-Secret-Token`.
        - Ambos deben coincidir con TelegramIntegration.webhook_secret.
    """
    # 1. Verificar header vs URL
    if not x_telegram_bot_api_secret_token:
        logger.warning("Webhook Telegram sin header X-Telegram-Bot-Api-Secret-Token")
        raise HTTPException(status_code=403, detail="Missing secret header")

    if x_telegram_bot_api_secret_token != secret:
        logger.warning("Webhook Telegram: header != secret de URL")
        raise HTTPException(status_code=403, detail="Secret mismatch")

    # 2. Resolver integracion por secret
    integration = telegram_service.resolve_by_secret(db, secret)
    if not integration:
        # No revelamos si existe o no
        logger.warning("Webhook Telegram: secret no corresponde a integracion activa")
        raise HTTPException(status_code=404, detail="Not found")

    # 3. Rate limiting
    _check_rate_limit(integration.id, request)

    # 4. Parsear Update
    try:
        body = await request.json()
    except Exception:
        logger.warning("Webhook Telegram: body no es JSON valido")
        return {"ok": True, "ignored": "invalid_json"}

    try:
        update = TelegramUpdateSchema.model_validate(body)
    except Exception as e:
        logger.warning("Webhook Telegram: schema invalido: %s", e)
        return {"ok": True, "ignored": "invalid_schema"}

    # 5. Idempotencia
    if not _save_update_idempotent(db, integration, update.update_id):
        logger.info(
            "Webhook Telegram: update_id=%s ya procesado (idempotencia)",
            update.update_id,
        )
        return {"ok": True, "ignored": "duplicate"}

    # 6. Descifrar token + crear adapter
    from app.services.ai_config_service import decrypt_api_key
    from app.models.db_models import Bot

    try:
        token = decrypt_api_key(integration.encrypted_token)
    except Exception as e:
        logger.error("Webhook Telegram: no se pudo descifrar token: %s", e)
        return {"ok": True, "ignored": "token_error"}

    adapter = TelegramAdapter(token=token)
    channel_request = adapter.to_request(update, bot_id=integration.bot_id)

    if channel_request is None:
        # Update ignorado (sin texto, grupo, bot...)
        telegram_service.touch_last_event(db, integration)
        return {"ok": True, "ignored": "not_processable"}

    # 7. Cargar bot + verificar estado
    bot = db.query(Bot).filter(Bot.id == integration.bot_id).first()

    if not bot:
        logger.error("Webhook Telegram: bot_id=%s no existe", integration.bot_id)
        telegram_service.touch_last_event(db, integration)
        return {"ok": True, "ignored": "bot_not_found"}

    chat_id = channel_request.metadata.get("telegram_chat_id")
    if not chat_id:
        logger.error("Webhook Telegram: sin chat_id en metadata")
        telegram_service.touch_last_event(db, integration)
        return {"ok": True, "ignored": "no_chat_id"}

    # 8. Bot no publicado → fallback
    if not bot.is_published:
        from app.core.contracts import ChannelResponse
        adapter.send_response(
            ChannelResponse(answer=FALLBACK_BOT_NOT_PUBLISHED, found=False),
            chat_id=chat_id,
        )
        telegram_service.touch_last_event(db, integration)
        return {"ok": True, "status": "bot_not_published"}

    # 9. Cargar workflow activo
    try:
        wf = get_active_workflow(bot.id, db)
    except HTTPException:
        # Sin workflow activo → fallback
        from app.core.contracts import ChannelResponse
        adapter.send_response(
            ChannelResponse(answer=FALLBACK_NO_WORKFLOW, found=False),
            chat_id=chat_id,
        )
        telegram_service.touch_last_event(db, integration)
        return {"ok": True, "status": "no_workflow"}

    wf_dict = build_public_workflow_dict(wf)

    # 10. Sesion Telegram
    external_id = str(chat_id)
    sess = get_or_create_by_external(
        bot=bot,
        channel="telegram",
        external_id=external_id,
        db=db,
    )
    append_user_message(sess, channel_request.message, db)

    # 11. Ejecutar workflow
    engine = WorkflowEngine()
    try:
        result = engine.run(
            workflow_data=wf_dict,
            bot_id=bot.id,
            workflow_id=wf.id,
            initial_variables={
                "user_message": channel_request.message,
                "input": channel_request.message,
            },
            max_steps=PUBLIC_MAX_STEPS,
        )
        reply = _extract_reply(result)
    except (WorkflowValidationError, MaxStepsExceeded, ConditionError, WorkflowExecutionError) as e:
        logger.error("Webhook Telegram: workflow fallo: %s", e)
        reply = FALLBACK_INTERNAL_ERROR

    # 12. Guardar respuesta + enviar
    append_bot_message(sess, reply, db)

    from app.core.contracts import ChannelResponse
    adapter.send_response(
        ChannelResponse(answer=reply, found=True),
        chat_id=chat_id,
    )

    # 13. Touch last_event
    telegram_service.touch_last_event(db, integration)

    # 14. Registrar analytics (channel=telegram)
    try:
        from app.models.db_models import Conversation
        conv = Conversation(
            bot_id=bot.id,
            channel="telegram",
            session_id=sess.public_id,
            question=channel_request.message,
            answer=reply,
            was_answered=True,
            workflow_id=wf.id,
            meta=None,
        )
        db.add(conv)
        db.commit()
    except Exception as e:
        logger.warning("Webhook Telegram: fallo guardando analytics: %s", e)
        db.rollback()

    return {"ok": True, "status": "processed"}


__all__ = ["router"]
