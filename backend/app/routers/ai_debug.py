"""
Router temporal SOLO para debug (Fase 14.7.14).
Eliminar después de la verificación.
"""
from fastapi import APIRouter, Depends
from app.config import settings
from app.models.db_models import User
from app.services.auth import get_current_user


router = APIRouter(prefix="/ai/debug", tags=["ai-debug"])


@router.get("/settings")
def get_ai_settings(current_user: User = Depends(get_current_user)):
    """
    DEBUG: Devuelve la configuración efectiva de IA que está viendo
    el proceso de Render. NUNCA exponer esto en producción real.
    """
    return {
        "enabled": settings.ai.enabled,
        "provider": settings.ai.provider,
        "gemini_model": settings.ai.gemini_model,
        "max_tokens_output": settings.ai.max_tokens_output,
        "timeout_seconds": settings.ai.timeout_seconds,
        "max_retries": settings.ai.max_retries,
        "rate_limit_enabled": settings.ai.rate_limit_enabled,
        "gemini_api_key_present": bool(settings.ai.gemini_api_key),
        "gemini_api_key_prefix": (
            settings.ai.gemini_api_key[:8]
            if settings.ai.gemini_api_key else None
        ),
    }
