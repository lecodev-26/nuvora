"""
Nuvora — Router /training
===========================
Endpoint administrativo del Training Assistant.

- Autenticación JWT.
- Aislamiento multi-tenant estricto.
- No modifica la BD (solo lee).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.db_models import Bot, User
from app.models.training import TrainingReport
from app.services.auth import get_current_user
from app.core.training import TrainingAnalyzer
from app.core.bot_loader import BotNotFoundError


router = APIRouter(prefix="/training", tags=["training"])


# ============================================================
# HELPERS — Ownership
# ============================================================

def _verify_bot_ownership(bot: Bot, current_user: User):
    """
    Valida que el usuario autenticado es dueño del bot.
    Compatible con user_id (nuevo) y owner_email (deprecado).
    """
    if bot.user_id is not None:
        if bot.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para ver este bot",
            )
        return
    # Fallback: validar por owner_email (compatibilidad)
    if bot.owner_email != current_user.email:
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para ver este bot",
        )


def _get_bot_or_404(db: Session, bot_id: int) -> Bot:
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")
    return bot


# ============================================================
# ENDPOINT
# ============================================================

@router.get("/{bot_id}", response_model=TrainingReport)
def get_training_report(
    bot_id: int,
    conversation_limit: int = Query(
        100,
        ge=1,
        le=500,
        description="Nº máximo de conversaciones recientes a analizar",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Devuelve el estado de preparación del bot:
    progreso, cobertura por tema, preguntas sin responder y recomendaciones.
    """
    # 1. Bot existe (404 si no)
    bot = _get_bot_or_404(db, bot_id)

    # 2. Ownership (403 si no es del usuario)
    _verify_bot_ownership(bot, current_user)

    # 3. Delegar en el Analyzer
    analyzer = TrainingAnalyzer(db)
    try:
        report = analyzer.analyze(
            bot_id=bot_id,
            conversation_limit=conversation_limit,
        )
    except BotNotFoundError:
        # En caso de carrera (bot borrado entre el check y el analyze)
        raise HTTPException(status_code=404, detail="Bot no encontrado")

    return report
