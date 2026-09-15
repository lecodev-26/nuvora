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
    }


def _test_gemini(model: str, api_key: str, max_tokens: int = 16384):
    """Ejecuta un test con el prompt REAL del generate y devuelve diagnóstico."""
    # Importar aquí para evitar circular
    from app.core.ai.prompts import SYSTEM_PROMPT_BASE, build_generate_prompt

    user_prompt = build_generate_prompt(
        "Quiero un bot que salude, pida el nombre, el día de la cita y confirme la reserva.",
        None,
    )

    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT_BASE}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "maxOutputTokens": max_tokens,
            "temperature": 0.2,
        },
    }

    url = f"{GEMINI_API_BASE}/models/{model}:generateContent?key={api_key}"
    try:
        r = requests.post(url, json=payload, timeout=120)
    except Exception as e:
        return {"error": str(e)}

    if r.status_code != 200:
        return {"http_status": r.status_code, "response": r.text[:500]}

    data = r.json()
    candidate = (data.get("candidates") or [{}])[0]
    parts = candidate.get("content", {}).get("parts", [])
    text = parts[0].get("text", "") if parts else ""

    usage = data.get("usageMetadata", {})

    return {
        "model": model,
        "http_status": 200,
        "finishReason": candidate.get("finishReason"),
        "text_length": len(text),
        "text_first_100": text[:100],
        "text_last_100": text[-100:] if len(text) > 100 else text,
        "promptTokens": usage.get("promptTokenCount"),
        "candidatesTokens": usage.get("candidatesTokenCount"),
        "thoughtsTokens": usage.get("thoughtsTokenCount"),
        "totalTokens": usage.get("totalTokenCount"),
    }


@router.get("/compare-models")
def compare_models(current_user: User = Depends(get_current_user)):
    """
    DEBUG: Prueba varios modelos con el prompt REAL del generate.
    Devuelve diagnóstico comparativo.
    """
    api_key = settings.ai.gemini_api_key
    if not api_key:
        return {"error": "no api key"}

    models = [
        "gemini-3.5-flash-lite",
        "gemini-flash-lite-latest",
        "gemini-2.5-flash",
        "gemini-flash-latest",
    ]

    results = []
    for model in models:
        try:
            result = _test_gemini(model, api_key, max_tokens=16384)
            results.append(result)
        except Exception as e:
            results.append({"model": model, "error": str(e)})

    return {"results": results}
