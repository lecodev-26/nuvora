"""
Nuvora - Router Creator Mode (Fase 14.12.3)
=============================================
Endpoints para Creator Workspace.

REGLA:
    - Solo endpoints de SOLO LECTURA en esta fase.
    - Ownership verificado.
    - Sin lógica de negocio nueva (delega en services).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.db_models import User
from app.services.auth import get_current_user
from app.services import creator_status_service


router = APIRouter(
    prefix="/bots",
    tags=["creator"],
    responses={
        401: {"description": "No autenticado (JWT faltante o inválido)"},
        403: {"description": "Bot ajeno"},
        404: {"description": "Bot no encontrado"},
    },
)


# ============================================================
# ENDPOINT
# ============================================================

@router.get("/{bot_id}/creator-status")
def get_creator_status(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Devuelve el estado del bot para Creator Mode.

    Contrato:
        - configuration: {ok}
        - workflow:      {ok, id, name}
        - publication:   {ok, public_url}
        - channels:      {web, api, telegram}
        - ready:         bool
        - next_step:     "configuration" | "workflow" | "publication" | null

    Determinista. Sin IA. Sin puntuaciones.
    """
    return creator_status_service.get_creator_status(
        db=db,
        bot_id=bot_id,
        user_id=current_user.id,
    )


__all__ = ["router"]
