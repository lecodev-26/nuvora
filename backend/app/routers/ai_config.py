"""
Nuvora — Router /ai/config (Fase 14.7.4b — BYOK)
===================================================
Endpoints para gestionar las API keys propias del usuario.

REGLAS:
    - Autenticación JWT obligatoria.
    - Aislamiento: cada usuario solo ve/gestiona sus propias configs.
    - La API key NUNCA se devuelve en responses.
    - Solo providers válidos: gemini | groq | deepseek.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.db_models import User
from app.models.ai_config import (
    AIConfigCreate,
    AIConfigItem,
    AIConfigListResponse,
    AIConfigDeleteResponse,
    VALID_PROVIDERS,
)
from app.services.auth import get_current_user
from app.services.ai_config_service import (
    list_user_configs,
    set_user_config,
    delete_user_config,
)
from app.config import settings


router = APIRouter(prefix="/ai/config", tags=["ai-config"])


# ============================================================
# HELPERS
# ============================================================

def _validate_provider(provider: str) -> str:
    p = provider.lower().strip()
    if p not in VALID_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider inválido: '{provider}'. Válidos: {list(VALID_PROVIDERS)}",
        )
    return p


def _config_to_item(config) -> AIConfigItem:
    return AIConfigItem(
        provider=config.provider,
        has_key=True,
        updated_at=config.updated_at or config.created_at,
    )


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("", response_model=AIConfigListResponse)
def get_ai_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lista las configs del usuario (una por provider configurado).
    NUNCA devuelve la API key. Solo indica has_key=True/False.
    """
    configs = list_user_configs(db, current_user.id)
    return AIConfigListResponse(
        configs=[_config_to_item(c) for c in configs],
        system_provider=settings.ai.provider,
    )


@router.post("", response_model=AIConfigItem, status_code=status.HTTP_201_CREATED)
def create_or_update_ai_config(
    data: AIConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Crea o actualiza la API key del usuario para un provider.

    Si ya existía → se sobreescribe.
    """
    provider = _validate_provider(data.provider)

    config = set_user_config(
        db=db,
        user_id=current_user.id,
        provider=provider,
        api_key=data.api_key,
    )
    return _config_to_item(config)


@router.delete("/{provider}", response_model=AIConfigDeleteResponse)
def delete_ai_config(
    provider: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Borra la API key del usuario para un provider.
    Si no existía → devuelve deleted=False.
    """
    provider = _validate_provider(provider)

    deleted = delete_user_config(
        db=db,
        user_id=current_user.id,
        provider=provider,
    )
    return AIConfigDeleteResponse(provider=provider, deleted=deleted)
