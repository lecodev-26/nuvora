"""
Nuvora — Servicio Public Resolver (Fase 14.9)
===============================================
Resuelve datos de un bot PUBLICADO para endpoints públicos (sin JWT).

RESPONSABILIDADES:
    - resolve_public_bot(public_id): bot + verifica is_published
    - get_active_workflow(bot_id): workflow con status="active"
    - build_public_workflow_dict(wf): dict para WorkflowEngine
    - validate_public_bot_ready(bot): comprueba que está listo para servir

FILOSOFÍA:
    - Este servicio es la única puerta para obtener datos públicos.
    - NO expone datos internos (workflow_id numérico, nodes, variables).
    - Solo devuelve lo necesario para ejecutar un workflow publicado.
"""

import json
from typing import Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.db_models import Bot, Workflow


# ============================================================
# RESOLVER BOT PÚBLICO
# ============================================================

def resolve_public_bot(public_id: str, db: Session) -> Bot:
    """
    Obtiene un bot por public_id (UUID) y verifica que está publicado.

    Args:
        public_id: UUID del bot (identidad técnica estable).
        db: sesión SQLAlchemy.

    Returns:
        Bot: el bot si existe y está publicado.

    Raises:
        HTTPException 404: si no existe.
        HTTPException 404: si existe pero NO está publicado.
            (Devolvemos 404 en ambos casos para no filtrar
             qué public_ids existen y cuáles no.)
    """
    if not public_id or not isinstance(public_id, str):
        raise HTTPException(status_code=404, detail="Bot no encontrado")

    bot = db.query(Bot).filter(Bot.public_id == public_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")

    if not bot.is_published:
        # No revelamos que el bot existe: 404 siempre.
        raise HTTPException(status_code=404, detail="Bot no encontrado")

    return bot


# ============================================================
# RESOLVER SLUG (fallback)
# ============================================================

def resolve_public_bot_by_identifier(identifier: str, db: Session) -> Bot:
    """
    Acepta public_id (UUID) O public_slug (humano).
    Prioriza public_id; si no encuentra, prueba public_slug.

    Misma política: 404 si no existe o no está publicado.
    """
    if not identifier:
        raise HTTPException(status_code=404, detail="Bot no encontrado")

    # Intentar por public_id
    bot = db.query(Bot).filter(Bot.public_id == identifier).first()

    # Si no, por public_slug
    if not bot:
        bot = db.query(Bot).filter(Bot.public_slug == identifier).first()

    if not bot or not bot.is_published:
        raise HTTPException(status_code=404, detail="Bot no encontrado")

    return bot


# ============================================================
# WORKFLOW ACTIVO
# ============================================================

def get_active_workflow(bot_id: int, db: Session) -> Workflow:
    """
    Devuelve el workflow activo del bot.

    Raises:
        HTTPException 500: si el bot no tiene exactamente 1 workflow activo.
            (Es un estado inconsistente: se supone que publish lo garantizó.)
    """
    actives = db.query(Workflow).filter(
        Workflow.bot_id == bot_id,
        Workflow.status == "active",
    ).all()

    if len(actives) != 1:
        # Estado inconsistente: bot publicado sin workflow activo único.
        # Es un error del servidor (no del visitante).
        raise HTTPException(
            status_code=500,
            detail="Bot en estado inconsistente (workflow activo no encontrado)",
        )
    return actives[0]


def build_public_workflow_dict(wf: Workflow) -> dict:
    """
    Convierte un Workflow SQLAlchemy → dict para el WorkflowEngine.

    Mismo formato que usa el endpoint /workflows/{bot_id}/{wf_id}/run.
    """
    nodes = []
    for n in wf.nodes:
        cfg = None
        if n.config:
            try:
                cfg = json.loads(n.config)
            except (ValueError, TypeError):
                cfg = None
        nodes.append({
            "node_id": n.node_id,
            "type": n.type,
            "name": n.name,
            "config": cfg,
        })

    transitions = []
    for t in wf.transitions:
        transitions.append({
            "from_node_id": t.from_node_id,
            "to_node_id": t.to_node_id,
            "condition": t.condition,
            "label": t.label,
            "order": t.order or 0,
        })

    return {"nodes": nodes, "transitions": transitions}


# ============================================================
# UTILIDADES
# ============================================================

def parse_public_config(bot: Bot) -> dict:
    """
    Lee public_config (JSON TEXT) → dict.
    Fallback a {} si no existe o está corrupto.
    """
    if not bot.public_config:
        return {}
    try:
        return json.loads(bot.public_config)
    except (ValueError, TypeError):
        return {}


def is_publicly_accessible(bot: Bot) -> bool:
    """True si el bot puede servirse públicamente."""
    return bool(bot.is_published and bot.public_id)


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "resolve_public_bot",
    "resolve_public_bot_by_identifier",
    "get_active_workflow",
    "build_public_workflow_dict",
    "parse_public_config",
    "is_publicly_accessible",
]
