"""
Nuvora — Router /bots/{bot_id}/api-keys
==========================================
Endpoints PRIVADOS para gestionar API Keys de un bot (JWT).

Reglas:
    - Autenticación JWT obligatoria.
    - Multi-tenant: 401 sin auth, 403 bot ajeno, 404 inexistente.
    - El secret de la key solo se devuelve UNA VEZ (al crear).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.db_models import Bot, User
from app.models.api_key import (
    ApiKeyCreate,
    ApiKeyResponse,
    ApiKeyCreatedResponse,
    ApiKeyListResponse,
)
from app.services.auth import get_current_user
from app.services.api_key_service import (
    create_api_key,
    list_api_keys,
    revoke_api_key,
)


router = APIRouter(prefix="/bots", tags=["api-keys"])


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
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para este bot",
            )
        return
    if bot.owner_email != current_user.email:
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para este bot",
        )


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/{bot_id}/api-keys", response_model=ApiKeyListResponse)
def get_api_keys(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lista las API Keys del bot.
    NUNCA devuelve el secret.
    """
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)

    keys = list_api_keys(db, current_user.id, bot_id)
    return ApiKeyListResponse(
        keys=[ApiKeyResponse.model_validate(k) for k in keys],
        total=len(keys),
    )


@router.post(
    "/{bot_id}/api-keys",
    response_model=ApiKeyCreatedResponse,
    status_code=201,
)
def post_api_key(
    bot_id: int,
    data: ApiKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Crea una API Key para el bot.

    ⚠️ El secret se devuelve UNA SOLA VEZ.
    Si se pierde, hay que revocar y crear otra.
    """
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)

    api_key_obj, full_key = create_api_key(
        db=db,
        user_id=current_user.id,
        bot_id=bot_id,
        name=data.name,
    )

    return ApiKeyCreatedResponse(
        id=api_key_obj.id,
        name=api_key_obj.name,
        key=full_key,
        key_prefix=api_key_obj.key_prefix,
        created_at=api_key_obj.created_at,
    )


@router.delete("/{bot_id}/api-keys/{key_id}")
def delete_api_key(
    bot_id: int,
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Revoca una API Key (is_active=False + revoked_at).
    Idempotente: revocar 2 veces no falla.
    """
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)

    key = revoke_api_key(db, key_id=key_id, user_id=current_user.id)

    # Verificar que la key revocada pertenece al bot indicado
    if key.bot_id != bot_id:
        raise HTTPException(status_code=404, detail="API Key no encontrada")

    return {"detail": "API Key revocada", "id": key_id}
