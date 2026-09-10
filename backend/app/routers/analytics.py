from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from app.database.config import get_db
from app.models.db_models import Bot, Conversation, User
from app.services.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ============================================================
# HELPER — Obtener bots del usuario (compatible nuevo/antiguo)
# ============================================================

def get_user_bots(db: Session, current_user: User):
    """
    Devuelve todos los bots del usuario autenticado.
    Compatible con user_id (nuevo) y owner_email (deprecado).
    """
    bots = db.query(Bot).filter(
        (Bot.user_id == current_user.id) | (Bot.owner_email == current_user.email)
    ).all()
    return bots


def verify_bot_ownership(bot: Bot, current_user: User):
    """Valida que el usuario es dueño del bot."""
    if bot.user_id is not None:
        if bot.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="No tienes permiso para ver este bot")
        return
    if bot.owner_email != current_user.email:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver este bot")


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/overview")
def get_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Resumen general del usuario.
    """
    bots = get_user_bots(db, current_user)
    bot_ids = [bot.id for bot in bots]

    if not bot_ids:
        return {
            "total_bots": 0,
            "total_conversations": 0,
            "answered": 0,
            "unanswered": 0,
            "response_rate": 0.0
        }

    total = db.query(Conversation).filter(Conversation.bot_id.in_(bot_ids)).count()
    answered = db.query(Conversation).filter(
        Conversation.bot_id.in_(bot_ids),
        Conversation.was_answered == True
    ).count()
    unanswered = total - answered
    response_rate = (answered / total * 100) if total > 0 else 0.0

    return {
        "total_bots": len(bots),
        "total_conversations": total,
        "answered": answered,
        "unanswered": unanswered,
        "response_rate": round(response_rate, 2)
    }


@router.get("/by-bot/{bot_id}")
def get_bot_stats(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Estadísticas de un bot específico.
    """
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")

    verify_bot_ownership(bot, current_user)

    total = db.query(Conversation).filter(Conversation.bot_id == bot_id).count()
    answered = db.query(Conversation).filter(
        Conversation.bot_id == bot_id,
        Conversation.was_answered == True
    ).count()
    unanswered = total - answered
    response_rate = (answered / total * 100) if total > 0 else 0.0

    last_activity = db.query(Conversation).filter(
        Conversation.bot_id == bot_id
    ).order_by(desc(Conversation.created_at)).first()

    top_questions = db.query(
        Conversation.question,
        func.count(Conversation.id).label('count')
    ).filter(
        Conversation.bot_id == bot_id
    ).group_by(
        Conversation.question
    ).order_by(
        desc('count')
    ).limit(5).all()

    return {
        "bot_id": bot_id,
        "bot_name": bot.name,
        "total_conversations": total,
        "answered": answered,
        "unanswered": unanswered,
        "response_rate": round(response_rate, 2),
        "last_activity": last_activity.created_at.isoformat() if last_activity else None,
        "top_questions": [
            {"question": q.question, "count": q.count}
            for q in top_questions
        ]
    }


@router.get("/top-questions")
def get_top_questions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 10
):
    """
    Preguntas más frecuentes de todos los bots del usuario.
    """
    bots = get_user_bots(db, current_user)
    bot_ids = [bot.id for bot in bots]

    if not bot_ids:
        return {"top_questions": []}

    top_questions = db.query(
        Conversation.question,
        func.count(Conversation.id).label('count')
    ).filter(
        Conversation.bot_id.in_(bot_ids)
    ).group_by(
        Conversation.question
    ).order_by(
        desc('count')
    ).limit(limit).all()

    return {
        "top_questions": [
            {"question": q.question, "count": q.count}
            for q in top_questions
        ]
    }


@router.get("/unanswered")
def get_unanswered_questions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20
):
    """
    Preguntas sin respuesta de todos los bots del usuario.
    """
    bots = get_user_bots(db, current_user)
    bot_ids = [bot.id for bot in bots]

    if not bot_ids:
        return {"unanswered_questions": []}

    unanswered = db.query(
        Conversation.question,
        Conversation.bot_id,
        func.count(Conversation.id).label('count')
    ).filter(
        Conversation.bot_id.in_(bot_ids),
        Conversation.was_answered == False
    ).group_by(
        Conversation.question,
        Conversation.bot_id
    ).order_by(
        desc('count')
    ).limit(limit).all()

    return {
        "unanswered_questions": [
            {
                "question": q.question,
                "bot_id": q.bot_id,
                "count": q.count
            }
            for q in unanswered
        ]
    }


@router.get("/activity")
def get_activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = 7
):
    """
    Actividad por día (últimos N días).
    """
    bots = get_user_bots(db, current_user)
    bot_ids = [bot.id for bot in bots]

    if not bot_ids:
        return {"activity": []}

    start_date = datetime.utcnow() - timedelta(days=days)
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

    activity = db.query(
        func.date(Conversation.created_at).label('day'),
        func.count(Conversation.id).label('count')
    ).filter(
        Conversation.bot_id.in_(bot_ids),
        Conversation.created_at >= start_date
    ).group_by(
        func.date(Conversation.created_at)
    ).order_by(
        func.date(Conversation.created_at)
    ).all()

    return {
        "activity": [
            {"day": a.day, "count": a.count}
            for a in activity
        ]
    }
