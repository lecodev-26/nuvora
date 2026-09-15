"""
Router temporal SOLO para debug (Fase 14.7.14).
Eliminar después de la verificación.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import requests
import json

from app.config import settings
from app.database.config import get_db
from app.models.db_models import User
from app.services.auth import get_current_user
from app.core.ai.providers.gemini import GEMINI_API_BASE


router = APIRouter(prefix="/ai/debug", tags=["ai-debug"])


@router.get("/settings")
def get_ai_settings(current_user: User = Depends(get_current_user)):
    """Devuelve la configuración efectiva de IA."""
    key = settings.ai.gemini_api_key or ""
    return {
        "enabled": settings.ai.enabled,
        "provider": settings.ai.provider,
        "gemini_model": settings.ai.gemini_model,
        "max_tokens_output": settings.ai.max_tokens_output,
        "timeout_seconds": settings.ai.timeout_seconds,
        "max_retries": settings.ai.max_retries,
        "rate_limit_enabled": settings.ai.rate_limit_enabled,
        "gemini_api_key_present": bool(key),
        "gemini_api_key_length": len(key),
        "gemini_api_key_prefix": key[:10] if key else None,
    }


@router.get("/gemini-raw")
def get_gemini_raw(current_user: User = Depends(get_current_user)):
    """
    DEBUG TEMPORAL: Llama a Gemini directamente y devuelve:
    - finishReason
    - usageMetadata (tokens desglosados)
    - text completo (sin parsear)
    - texto en caso de error
    """
    api_key = settings.ai.gemini_api_key
    if not api_key:
        return {"error": "no api key"}

    model = settings.ai.gemini_model

    # Prompt mínimo para que el JSON sea corto
    payload = {
        "systemInstruction": {
            "parts": [{"text": "Devuelve SOLO JSON válido. Sé breve."}]
        },
        "contents": [{
            "role": "user",
            "parts": [{"text": "Genera un JSON: {\"workflow\": {\"name\": \"Test\", \"nodes\": [{\"node_id\": \"s1\", \"type\": \"start\"}, {\"node_id\": \"e1\", \"type\": \"end\"}], \"transitions\": [{\"from_node_id\": \"s1\", \"to_node_id\": \"e1\"}]}, \"explanation\": \"Simple\"}"}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json",
            "maxOutputTokens": settings.ai.max_tokens_output,
            "temperature": 0.2,
        },
    }

    url = f"{GEMINI_API_BASE}/models/{model}:generateContent?key={api_key}"

    try:
        r = requests.post(url, json=payload, timeout=60)
    except Exception as e:
        return {"error": f"requests failed: {e}"}

    if r.status_code != 200:
        return {
            "http_status": r.status_code,
            "response_text": r.text[:2000],
        }

    data = r.json()
    candidate = (data.get("candidates") or [{}])[0]
    parts = candidate.get("content", {}).get("parts", [])
    text = parts[0].get("text", "") if parts else ""

    return {
        "http_status": r.status_code,
        "finishReason": candidate.get("finishReason"),
        "text_length": len(text),
        "text_preview": text[:500],
        "text_full_length_chars": len(text),
        "usageMetadata": data.get("usageMetadata"),
        "modelVersion": data.get("modelVersion"),
    }
