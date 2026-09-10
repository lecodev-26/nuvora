"""
Nuvora Core — Router /ask
Endpoints públicos y privados para hacer preguntas al bot.
Este router es solo una capa fina que:
1. Valida permisos (si aplica)
2. Traduce a ChannelRequest
3. Delega en el Orchestrator
4. Devuelve AskResponse
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.bot import AskRequest, AskResponse
from app.models.db_models import Bot, User
from app.services.auth import get_current_user

from app.core.contracts import ChannelRequest, ChannelResponse
from app.core.orchestrator import Orchestrator


router = APIRouter(prefix="/ask", tags=["ask"])


# ============================================================
# HELPER — Validar ownership (compatible nuevo/antiguo)
# ============================================================

def _verify_bot_ownership(bot: Bot, current_user: User):
    """Valida que el usuario es dueño del bot."""
    if bot.user_id is not None:
        if bot.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="No tienes permiso para usar este bot")
        return
    if bot.owner_email != current_user.email:
        raise HTTPException(status_code=403, detail="No tienes permiso para usar este bot")


# ============================================================
# HELPER — Convertir respuesta del Core a AskResponse
# ============================================================

def _to_ask_response(core_response: ChannelResponse) -> AskResponse:
    """Convierte la ChannelResponse del Core al AskResponse del endpoint."""
    answer = core_response.answer or (
        "No tengo esa información en mi memoria. "
        "Te recomiendo contactar directamente con el negocio."
    )
    return AskResponse(answer=answer, found=core_response.found)


# ============================================================
# ENDPOINT PÚBLICO (WIDGET) — SIN AUTENTICACIÓN
# ============================================================

@router.post("/public", response_model=AskResponse)
def ask_question_public(
    request: AskRequest,
    db: Session = Depends(get_db),
):
    """
    Endpoint público para el widget.
    Cualquier visitante puede hacer preguntas sin autenticación.
    Delega en el Core con channel="widget".
    """
    # Verificar que el bot existe (404 si no)
    bot = db.query(Bot).filter(Bot.id == request.bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")

    # Delegar en el Core
    core_request = ChannelRequest(
        bot_id=request.bot_id,
        session_id=request.session_id,
        message=request.question,
        channel="widget",
    )

    orchestrator = Orchestrator(db)
    core_response = orchestrator.process(core_request)

    return _to_ask_response(core_response)


# ============================================================
# ENDPOINT PRIVADO (DASHBOARD) — CON AUTENTICACIÓN
# ============================================================

@router.post("/", response_model=AskResponse)
def ask_question_private(
    request: AskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint privado para el dashboard.
    Solo el dueño del bot puede hacer preguntas.
    Delega en el Core con channel="dashboard".
    """
    # Verificar que el bot existe
    bot = db.query(Bot).filter(Bot.id == request.bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")

    # Validar ownership
    _verify_bot_ownership(bot, current_user)

    # Delegar en el Core
    core_request = ChannelRequest(
        bot_id=request.bot_id,
        session_id=request.session_id,
        message=request.question,
        channel="dashboard",
    )

    orchestrator = Orchestrator(db)
    core_response = orchestrator.process(core_request)

    return _to_ask_response(core_response)
