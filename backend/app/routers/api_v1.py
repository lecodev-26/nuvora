"""
Nuvora — Router /api/v1/*
==========================
API pública de Nuvora para integraciones externas.

AUTENTICACIÓN:
    Authorization: Bearer nvr_live_...

ENDPOINTS:
    POST /api/v1/chat → enviar mensaje al bot asociado a la API key

REUTILIZA:
    - WorkflowEngine (14.5) como único motor de ejecución.
    - public_sessions (14.9) como sistema de sesiones.
    - Conversation (analytics) con channel="api".

NO DEVUELVE:
    - workflow_id, node_id, variables internas, prompts, IDs de BD.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.db_models import Conversation, PublicSession
from app.models.api_key import ChatRequest, ChatResponse
from app.core.api_auth import ApiKeyContext, get_api_key_context
from app.services.public_resolver import (
    get_active_workflow,
    build_public_workflow_dict,
)
from app.services.public_session import (
    create_session,
    get_session,
    append_user_message,
    append_bot_message,
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


router = APIRouter(prefix="/api/v1", tags=["api-v1"])


# ============================================================
# CONSTANTES
# ============================================================

PUBLIC_MAX_STEPS = 50
API_RATE_LIMIT_MESSAGE = 60    # por API key
API_RATE_LIMIT_IP = 120        # por IP


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


def _handle_rate_limit(exc: PublicRateLimitExceeded) -> HTTPException:
    return HTTPException(
        status_code=429,
        detail=str(exc),
        headers={"Retry-After": str(exc.retry_after)},
    )


def _extract_reply(result) -> str:
    """
    Igual que /public/bots/{id}/message:
    último response > message > output > fallback.
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
    return "Lo siento, no he podido generar una respuesta."


def _save_conversation_analytics(
    db: Session,
    bot_id: int,
    session_id: str,
    question: str,
    answer: str,
    was_answered: bool,
) -> None:
    """Registra la conversación en analytics (channel='api')."""
    try:
        conv = Conversation(
            bot_id=bot_id,
            channel="api",
            session_id=session_id,
            question=question,
            answer=answer,
            was_answered=was_answered,
            workflow_id=None,
            meta=None,
        )
        db.add(conv)
        db.commit()
    except Exception:
        db.rollback()


# ============================================================
# ENDPOINT
# ============================================================

@router.post("/chat", response_model=ChatResponse)
def api_chat(
    data: ChatRequest,
    request: Request,
    ctx: ApiKeyContext = Depends(get_api_key_context),
    db: Session = Depends(get_db),
):
    """
    Envía un mensaje al bot asociado a la API key.

    Si no se pasa `session_id` → crea sesión nueva.
    Si se pasa → recupera sesión (verifica pertenencia al bot).
    """
    bot = ctx.bot

    # 1. Verificar que el bot está publicado
    if not bot.is_published:
        raise HTTPException(
            status_code=409,
            detail="El bot no está publicado. Publícalo antes de usar la API.",
        )

    # 2. Rate limiting (por API key + por IP)
    ip = _get_client_ip(request)
    try:
        check_public_rate_limit(
            key=f"apikey:{ctx.api_key.id}",
            bucket="api_chat",
            max_per_window=API_RATE_LIMIT_MESSAGE,
        )
        check_public_rate_limit(
            key=ip,
            bucket="api_chat_ip",
            max_per_window=API_RATE_LIMIT_IP,
        )
    except PublicRateLimitExceeded as e:
        raise _handle_rate_limit(e)

    # 3. Sesión (crear o recuperar)
    if data.session_id:
        # Recuperar y validar que pertenece al bot de la key
        sess = get_session(data.session_id, bot, db)
    else:
        sess = create_session(bot, db)

    # 4. Guardar mensaje del usuario
    append_user_message(sess, data.message, db)

    # 5. Cargar workflow activo
    try:
        wf = get_active_workflow(bot.id, db)
    except HTTPException as e:
        raise HTTPException(
            status_code=409,
            detail="El bot no tiene un workflow activo. Publícalo correctamente antes de usar la API.",
        )
    wf_dict = build_public_workflow_dict(wf)

    # 6. Ejecutar el engine
    engine = WorkflowEngine()
    try:
        result = engine.run(
            workflow_data=wf_dict,
            bot_id=bot.id,
            workflow_id=wf.id,
            initial_variables={
                "user_message": data.message,
                "input": data.message,
            },
            max_steps=PUBLIC_MAX_STEPS,
        )
    except WorkflowValidationError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Workflow inválido: {e.errors}",
        )
    except MaxStepsExceeded:
        raise HTTPException(
            status_code=500,
            detail="El workflow ha superado el máximo de pasos",
        )
    except ConditionError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en condición: {e.message}",
        )
    except WorkflowExecutionError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error de ejecución: {str(e)}",
        )

    # 7. Extraer reply + guardar respuesta
    reply = _extract_reply(result)
    append_bot_message(sess, reply, db)

    # 8. Registrar en analytics (channel="api")
    _save_conversation_analytics(
        db=db,
        bot_id=bot.id,
        session_id=sess.public_id,
        question=data.message,
        answer=reply,
        was_answered=True,
    )

    # 9. Devolver respuesta pública
    status_map = {
        "completed": "completed",
        "waiting_input": "waiting_input",
        "running": "completed",
        "failed": "error",
    }
    public_status = status_map.get(result.status.value, "completed")

    return ChatResponse(
        answer=reply,
        session_id=sess.public_id,
        status=public_status,
    )
