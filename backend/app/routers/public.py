"""
Nuvora — Router /public/bots/{identifier}/*
==============================================
Endpoints PÚBLICOS (sin JWT) para bots publicados.

REGLA DE ORO:
    - El visitante NO conoce el panel privado.
    - Solo recibe: respuesta del bot + metadatos públicos.
    - NUNCA: workflow, nodes, variables, keys, owner.

Ejecuta el MISMO WorkflowEngine de 14.5. Cero duplicación.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.public import (
    PublicBotInfo,
    PublicationConfig,
    PublicSessionCreateRequest,
    PublicSessionResponse,
    PublicMessageRequest,
    PublicMessageResponse,
)
from app.services.public_resolver import (
    resolve_public_bot_by_identifier,
    get_active_workflow,
    build_public_workflow_dict,
    parse_public_config,
)
from app.services.public_session import (
    create_session,
    get_session,
    append_user_message,
    append_bot_message,
    get_session_messages,
    close_session,
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


router = APIRouter(prefix="/public", tags=["public"])


# ============================================================
# CONSTANTES
# ============================================================

PUBLIC_MAX_STEPS = 50          # límite de pasos por ejecución pública
PUBLIC_TIMEOUT_SECONDS = 30    # (no aplicado todavía; el engine no timeout-a)


# ============================================================
# HELPERS
# ============================================================

def _get_client_ip(request: Request) -> str:
    """
    Obtiene la IP del visitante.
    Prioriza X-Forwarded-For (Render/proxies) → request.client.host.
    """
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        # "cliente, proxy1, proxy2" → primera IP
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _handle_public_rate_limit(exc: PublicRateLimitExceeded) -> HTTPException:
    """Convierte PublicRateLimitExceeded en HTTPException 429 con Retry-After."""
    return HTTPException(
        status_code=429,
        detail=str(exc),
        headers={"Retry-After": str(exc.retry_after)},
    )


def _extract_reply(result) -> str:
    """
    Extrae la respuesta pública del resultado del WorkflowEngine.

    Estrategia:
        1. Último output tipo "response" (nodo response)
        2. Último output tipo "message" (nodo message)
        3. Fallback: último output no vacío
        4. Fallback final: mensaje genérico

    Nota: response → preferencia (nodos response suelen ser finales).
    """
    outputs = result.outputs or []

    # 1. último response
    for out in reversed(outputs):
        if out.get("type") == "response" and out.get("text"):
            return out["text"]

    # 2. último message
    for out in reversed(outputs):
        if out.get("type") == "message" and out.get("text"):
            return out["text"]

    # 3. último output no vacío
    for out in reversed(outputs):
        if out.get("text"):
            return out["text"]

    # 4. fallback
    return "Lo siento, no he podido generar una respuesta."


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/bots/{identifier}", response_model=PublicBotInfo)
def get_public_bot(
    identifier: str,
    db: Session = Depends(get_db),
):
    """
    Info pública de un bot publicado.
    `identifier` puede ser public_id (UUID) o public_slug.
    """
    bot = resolve_public_bot_by_identifier(identifier, db)
    cfg_dict = parse_public_config(bot)
    try:
        cfg = PublicationConfig(**cfg_dict)
    except Exception:
        cfg = PublicationConfig()

    return PublicBotInfo(
        public_id=bot.public_id,
        name=bot.name,
        description=bot.description,
        nicho_id=bot.nicho_id or "otro",
        business_name=bot.business_name or bot.restaurant_name,
        config=cfg,
    )


@router.post(
    "/bots/{identifier}/session",
    response_model=PublicSessionResponse,
)
def create_public_session(
    identifier: str,
    data: PublicSessionCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Crea una sesión anónima para el bot."""
    # Rate limiting por IP
    ip = _get_client_ip(request)
    try:
        check_public_rate_limit(key=ip, bucket="public_session_create")
    except PublicRateLimitExceeded as e:
        raise _handle_public_rate_limit(e)

    bot = resolve_public_bot_by_identifier(identifier, db)
    sess = create_session(bot, db)
    return PublicSessionResponse(
        session_id=sess.public_id,
        bot_public_id=bot.public_id,
        expires_at=sess.expires_at,
    )


@router.post(
    "/bots/{identifier}/message",
    response_model=PublicMessageResponse,
)
def send_public_message(
    identifier: str,
    data: PublicMessageRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Envía un mensaje al bot publicado y devuelve la respuesta.

    Flujo:
        1. Rate limiting (por IP + por session_id).
        2. Resolver bot.
        3. Recuperar sesión (verificar pertenencia + TTL).
        4. Guardar mensaje del usuario.
        5. Cargar workflow activo.
        6. Ejecutar WorkflowEngine.run().
        7. Extraer respuesta.
        8. Guardar respuesta del bot.
        9. Devolver.
    """
    # 1. Rate limiting (IP + session)
    ip = _get_client_ip(request)
    try:
        check_public_rate_limit(key=ip, bucket="public_message")
        check_public_rate_limit(key=data.session_id, bucket="public_message_session")
    except PublicRateLimitExceeded as e:
        raise _handle_public_rate_limit(e)

    # 2. Bot
    bot = resolve_public_bot_by_identifier(identifier, db)

    # 3. Sesión
    sess = get_session(data.session_id, bot, db)

    # 4. Guardar mensaje del usuario
    append_user_message(sess, data.message, db)

    # 5. Workflow activo
    wf = get_active_workflow(bot.id, db)
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

    # 7. Extraer respuesta
    reply = _extract_reply(result)

    # 8. Guardar respuesta del bot
    append_bot_message(sess, reply, db)

    # 9. Devolver
    status_map = {
        "completed": "completed",
        "waiting_input": "waiting_input",
        "running": "completed",   # solo ocurre si falla el engine; lo mapeamos
        "failed": "error",
    }
    public_status = status_map.get(result.status.value, "completed")

    return PublicMessageResponse(
        reply=reply,
        session_id=sess.public_id,
        status=public_status,
    )


@router.delete("/bots/{identifier}/session")
def delete_public_session(
    identifier: str,
    session_id: str,
    db: Session = Depends(get_db),
):
    """
    Cierra una sesión.

    `session_id` va como query param: DELETE /public/bots/{id}/session?session_id=...
    """
    bot = resolve_public_bot_by_identifier(identifier, db)
    sess = get_session(session_id, bot, db)
    close_session(sess, db)
    return {"detail": "Sesión cerrada", "session_id": sess.public_id}
