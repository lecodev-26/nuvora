"""
Nuvora — Router /bots/{bot_id}/publication + /publish + /unpublish
====================================================================
Endpoints PRIVADOS de Publicación Universal (Fase 14.9).

Reglas:
    - Autenticación JWT obligatoria.
    - Multi-tenant estricto: 401 sin auth, 403 bot ajeno, 404 inexistente.
    - Validación: al publicar, el bot debe tener 1 workflow activo válido.
    - Idempotencia: publicar 2 veces no rompe.
"""

import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.db_models import Bot, User, Workflow
from app.models.public import (
    PublicationConfig,
    PublicationResponse,
    PublicationUpdate,
    PublishResponse,
)
from app.services.auth import get_current_user
from app.services.publication import (
    generate_public_id,
    generate_public_slug,
    build_public_url,
)
from app.core.workflows.validator import WorkflowValidator
from app.core.workflows.errors import WorkflowValidationError


router = APIRouter(prefix="/bots", tags=["publication"])


# ============================================================
# HELPERS
# ============================================================

def _get_bot_or_404(db: Session, bot_id: int) -> Bot:
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")
    return bot


def _verify_bot_ownership(bot: Bot, current_user: User) -> None:
    if bot.user_id is not None:
        if bot.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="No tienes permiso para este bot")
        return
    if bot.owner_email != current_user.email:
        raise HTTPException(status_code=403, detail="No tienes permiso para este bot")


def _parse_public_config(bot: Bot) -> PublicationConfig:
    """Lee public_config (JSON TEXT) → PublicationConfig. Fallback a default."""
    if not bot.public_config:
        return PublicationConfig()
    try:
        data = json.loads(bot.public_config)
        return PublicationConfig(**data)
    except Exception:
        return PublicationConfig()


def _get_active_workflow(db: Session, bot_id: int) -> Workflow:
    """Devuelve el workflow con status='active'. 400 si no hay o hay varios."""
    actives = db.query(Workflow).filter(
        Workflow.bot_id == bot_id,
        Workflow.status == "active",
    ).all()

    if len(actives) == 0:
        raise HTTPException(
            status_code=400,
            detail="El bot no tiene ningún workflow activo. Activa uno antes de publicar."
        )
    if len(actives) > 1:
        raise HTTPException(
            status_code=400,
            detail=f"El bot tiene {len(actives)} workflows activos. Debe haber exactamente 1."
        )
    return actives[0]


def _workflow_to_dict(wf: Workflow) -> dict:
    """Convierte Workflow SQLAlchemy → dict para el validador."""
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


def _validate_active_workflow(wf: Workflow) -> None:
    """Valida el workflow activo. Lanza 400 si inválido."""
    payload = _workflow_to_dict(wf)
    try:
        WorkflowValidator().validate(payload)
    except WorkflowValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=f"El workflow activo no es válido: {e.errors}"
        )


def _build_publication_response(bot: Bot) -> PublicationResponse:
    """Construye la respuesta de estado de publicación."""
    url = None
    if bot.public_id:
        url = build_public_url(bot.public_id, bot.public_slug)

    return PublicationResponse(
        bot_id=bot.id,
        is_published=bool(bot.is_published),
        public_id=bot.public_id,
        public_slug=bot.public_slug,
        published_at=bot.published_at,
        public_url=url,
        config=_parse_public_config(bot),
    )


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/{bot_id}/publication", response_model=PublicationResponse)
def get_publication(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Estado de publicación + config del bot."""
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)
    return _build_publication_response(bot)


@router.put("/{bot_id}/publication", response_model=PublicationResponse)
def update_publication(
    bot_id: int,
    data: PublicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Actualiza la config de publicación (visual/textos)."""
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)

    bot.public_config = data.config.model_dump_json(exclude_none=False)
    db.commit()
    db.refresh(bot)

    return _build_publication_response(bot)


@router.post("/{bot_id}/publish", response_model=PublishResponse)
def publish_bot(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Publica el bot.

    Requisitos:
        - Bot con 1 workflow activo (status="active").
        - Ese workflow pasa WorkflowValidator.

    Idempotente: si ya está publicado, no cambia public_id ni public_slug,
    solo refresca published_at.
    """
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)

    # 1. Validar que hay 1 workflow activo y es válido
    wf = _get_active_workflow(db, bot_id)
    _validate_active_workflow(wf)

    # 2. Generar public_id (solo si no existe → idempotente)
    if not bot.public_id:
        bot.public_id = generate_public_id()

    # 3. Generar public_slug (solo si no existe)
    if not bot.public_slug:
        bot.public_slug = generate_public_slug(bot.name, db)

    # 4. Marcar como publicado
    bot.published_at = datetime.now(timezone.utc)
    bot.is_published = True

    db.commit()
    db.refresh(bot)

    url = build_public_url(bot.public_id, bot.public_slug)

    return PublishResponse(
        bot_id=bot.id,
        is_published=True,
        public_id=bot.public_id,
        public_slug=bot.public_slug,
        published_at=bot.published_at,
        public_url=url,
    )


@router.post("/{bot_id}/unpublish", response_model=PublicationResponse)
def unpublish_bot(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Despublica el bot.

    - is_published = False
    - Mantiene public_id y public_slug (para republicar sin cambiar URL)
    - Idempotente: si ya está despublicado, no falla
    """
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)

    bot.is_published = False
    db.commit()
    db.refresh(bot)

    return _build_publication_response(bot)
