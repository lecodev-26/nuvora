"""
Router temporal SOLO para debug (Fase 14.7.14).
Eliminar después de la verificación.
"""
from fastapi import APIRouter, Depends
import requests

from app.config import settings
from app.models.db_models import User
from app.services.auth import get_current_user
from app.core.ai.providers.gemini import GEMINI_API_BASE


router = APIRouter(prefix="/ai/debug", tags=["ai-debug"])


@router.get("/settings")
def get_ai_settings(current_user: User = Depends(get_current_user)):
    key = settings.ai.gemini_api_key or ""
    return {
        "enabled": settings.ai.enabled,
        "provider": settings.ai.provider,
        "gemini_model": settings.ai.gemini_model,
        "max_tokens_output": settings.ai.max_tokens_output,
        "gemini_api_key_present": bool(key),
        "gemini_api_key_prefix": key[:10] if key else None,
    }


@router.get("/gemini-raw")
def get_gemini_raw(current_user: User = Depends(get_current_user)):
    """Diagnóstico básico de Gemini."""
    api_key = settings.ai.gemini_api_key
    if not api_key:
        return {"error": "no api key"}

    payload = {
        "contents": [{
            "parts": [{"text": "Devuelve un JSON: {\"name\": \"Test\"}"}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json",
            "maxOutputTokens": settings.ai.max_tokens_output,
            "temperature": 0.2,
        },
    }

    url = f"{GEMINI_API_BASE}/models/{settings.ai.gemini_model}:generateContent?key={api_key}"
    r = requests.post(url, json=payload, timeout=60)
    return r.json()


@router.get("/gemini-thinking-disabled")
def get_gemini_thinking_disabled(current_user: User = Depends(get_current_user)):
    """
    DEBUG: Prueba Gemini con thinkingBudget=0 (sin pensamiento).
    """
    api_key = settings.ai.gemini_api_key
    if not api_key:
        return {"error": "no api key"}

    payload = {
        "contents": [{
            "parts": [{"text": "Devuelve un JSON: {\"name\": \"Test\"}"}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json",
            "maxOutputTokens": settings.ai.max_tokens_output,
            "temperature": 0.2,
            "thinkingConfig": {
                "thinkingBudget": 0,
            },
        },
    }

    url = f"{GEMINI_API_BASE}/models/{settings.ai.gemini_model}:generateContent?key={api_key}"
    try:
        r = requests.post(url, json=payload, timeout=60)
    except Exception as e:
        return {"error": str(e)}

    if r.status_code != 200:
        return {"http_status": r.status_code, "response": r.text[:1000]}

    data = r.json()
    return data
