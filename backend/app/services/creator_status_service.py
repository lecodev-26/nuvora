"""
Nuvora - Creator Status Service (Fase 14.12.3)
================================================
Calcula el estado del bot para Creator Mode.

FILOSOFÍA:
    - Endpoint de SOLO LECTURA. No efectos secundarios.
    - Contrato MINIMALISTA (solo lo que la UI necesita).
    - Determinista. Sin IA. Sin puntuaciones.
    - Reutiliza la autoridad existente de validación.

DEFINICIÓN DE READY:
    READY = configuration.ok AND workflow.ok AND publication.ok

    - NO exige knowledge (memorias/sources).
    - NO exige tests.
    - NO exige canales adicionales (API/Telegram).
    - nicho_id=null es válido.

NEXT_STEP DETERMINISTA:
    if not configuration.ok → "configuration"
    elif not workflow.ok    → "workflow"
    elif not publication.ok → "publication"
    else                    → None
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.db_models import Bot, ApiKey, TelegramIntegration
from app.services.workflow_validator_service import (
    get_active_workflow_or_none,
    is_workflow_valid,
)


logger = logging.getLogger(__name__)


# ============================================================
# HELPERS DE OWNERSHIP
# ============================================================

def _get_bot_or_404(db: Session, bot_id: int, user_id: int) -> Bot:
    """
    Recupera el bot verificando ownership.

    Raises:
        HTTPException 404 si no existe.
        HTTPException 403 si existe pero es de otro usuario.
    """
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")

    if bot.user_id is not None:
        if bot.user_id != user_id:
            raise HTTPException(status_code=403, detail="No tienes permiso para este bot")
    else:
        # Bot legacy sin user_id → no accesible por ownership
        raise HTTPException(status_code=403, detail="No tienes permiso para este bot")

    return bot


# ============================================================
# CÁLCULO DE SUB-ESTADOS
# ============================================================

def _calc_configuration(bot: Bot) -> dict:
    """
    Configuration.ok = true si:
        - bot.name existe y no está vacío

    nicho_id=null es VÁLIDO.
    """
    has_name = bool(bot.name and bot.name.strip())
    return {"ok": has_name}


def _calc_workflow(db: Session, bot_id: int) -> dict:
    """
    Workflow.ok = true si:
        - Existe exactamente 1 workflow con status="active"
        - Ese workflow pasa la validación estructural (WorkflowValidator)

    Devuelve id/name del workflow si todo OK.
    """
    wf = get_active_workflow_or_none(db, bot_id)
    if wf is None:
        return {"ok": False, "id": None, "name": None}

    is_valid, _errors = is_workflow_valid(wf)
    if not is_valid:
        return {"ok": False, "id": None, "name": None}

    return {"ok": True, "id": wf.id, "name": wf.name}


def _calc_publication(bot: Bot) -> dict:
    """
    Publication.ok = true si:
        - bot.is_published == True
        - bot.public_id existe (no None)
    """
    is_pub = bool(bot.is_published and bot.public_id)
    url = None
    if is_pub:
        # Construir URL pública (mismo formato que publication.py)
        identifier = bot.public_slug or bot.public_id
        url = f"https://nuvora-chi.vercel.app/b/{identifier}"
    return {"ok": is_pub, "public_url": url}


def _calc_channels(db: Session, bot: Bot) -> dict:
    """
    channels = {web, api, telegram}
        - web:      = publication.ok (activado al publicar)
        - api:      = existe ≥1 ApiKey activa, no revocada, no expirada
        - telegram: = existe TelegramIntegration status="connected" y activa
    """
    # Web
    web = bool(bot.is_published and bot.public_id)

    # API
    now = datetime.now(timezone.utc)
    api_count = db.query(ApiKey).filter(
        ApiKey.bot_id == bot.id,
        ApiKey.is_active.is_(True),
        ApiKey.revoked_at.is_(None),
    ).count()
    # Filtrar expiradas (SQLite no tiene NOW() en query, filtramos en Python)
    api_active = False
    if api_count > 0:
        keys = db.query(ApiKey).filter(
            ApiKey.bot_id == bot.id,
            ApiKey.is_active.is_(True),
            ApiKey.revoked_at.is_(None),
        ).all()
        for k in keys:
            if k.expires_at is None:
                api_active = True
                break
            exp = k.expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if now < exp:
                api_active = True
                break

    # Telegram
    tg = db.query(TelegramIntegration).filter(
        TelegramIntegration.bot_id == bot.id,
        TelegramIntegration.status == "connected",
        TelegramIntegration.is_active.is_(True),
    ).first()
    telegram = tg is not None

    return {"web": web, "api": api_active, "telegram": telegram}


def _calc_ready(config_ok: bool, workflow_ok: bool, pub_ok: bool) -> bool:
    """READY = configuración + workflow + publicación."""
    return config_ok and workflow_ok and pub_ok


def _calc_next_step(config_ok: bool, workflow_ok: bool, pub_ok: bool):
    """
    Reglas deterministas de next_step.
    Sin IA. Sin nichos. Sin puntuaciones.
    """
    if not config_ok:
        return "configuration"
    if not workflow_ok:
        return "workflow"
    if not pub_ok:
        return "publication"
    return None


# ============================================================
# API PÚBLICA
# ============================================================

def get_creator_status(db: Session, bot_id: int, user_id: int) -> dict:
    """
    Calcula el estado completo del bot para Creator Mode.

    Returns:
        dict con el contrato definido en 14.12.2.
    """
    bot = _get_bot_or_404(db, bot_id, user_id)

    configuration = _calc_configuration(bot)
    workflow = _calc_workflow(db, bot.id)
    publication = _calc_publication(bot)
    channels = _calc_channels(db, bot)

    ready = _calc_ready(
        configuration["ok"],
        workflow["ok"],
        publication["ok"],
    )
    next_step = _calc_next_step(
        configuration["ok"],
        workflow["ok"],
        publication["ok"],
    )

    return {
        "bot_id": bot.id,
        "configuration": configuration,
        "workflow": workflow,
        "publication": publication,
        "channels": channels,
        "ready": ready,
        "next_step": next_step,
    }


__all__ = ["get_creator_status"]
