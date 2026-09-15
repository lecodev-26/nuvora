"""
Nuvora Core — AI: Gemini Provider
====================================
Implementación del provider Gemini (Google).

Gemini NO es OpenAI-compatible. Usa su propia API:
    POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent

Soporta structured output con responseMimeType + responseSchema.
"""

import json
import time
import logging

import requests

from app.config import settings
from app.core.ai.provider import AIProvider, AIRequest, AIResponse
from app.core.ai.errors import AIProviderError, AIInvalidOutputError
from app.core.ai.providers import register_provider


logger = logging.getLogger(__name__)


GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


@register_provider("gemini")
class GeminiProvider(AIProvider):
    """Provider Gemini (Google)."""

    name = "gemini"

    # ============================================================
    # API PÚBLICA
    # ============================================================

    def generate_json(self, request: AIRequest) -> AIResponse:
        api_key = self.get_api_key()
        if not api_key:
            raise AIProviderError(
                provider=self.name,
                message=(
                    "API key de Gemini no configurada. "
                    "Configura GEMINI_API_KEY o tu propia key (BYOK)."
                ),
            )

        model = self._get_model()
        url = f"{GEMINI_API_BASE}/models/{model}:generateContent?key={api_key}"
        payload = self._build_payload(request)

        max_attempts = 1 + max(0, settings.ai.max_retries)
        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    timeout=request.timeout,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code >= 500:
                    raise AIProviderError(
                        provider=self.name,
                        message=f"HTTP {response.status_code} del provider (server error)",
                    )
                if response.status_code in (401, 403):
                    raise AIProviderError(
                        provider=self.name,
                        message="API key inválida o sin permisos (401/403)",
                    )
                if response.status_code == 429:
                    raise AIProviderError(
                        provider=self.name,
                        message="Rate limit alcanzado (429). Inténtalo más tarde.",
                    )
                if response.status_code >= 400:
                    raise AIProviderError(
                        provider=self.name,
                        message=f"HTTP {response.status_code}: {response.text[:200]}",
                    )

                return self._parse_response(response, model)

            except requests.exceptions.Timeout:
                last_error = AIProviderError(
                    provider=self.name,
                    message=f"Timeout tras {request.timeout}s",
                )
            except requests.exceptions.RequestException as e:
                last_error = AIProviderError(
                    provider=self.name,
                    message=f"Error de red: {e}",
                )
            except AIProviderError as e:
                last_error = e
                if "40" in e.message or "429" in e.message:
                    raise

            if attempt < max_attempts:
                logger.warning(
                    f"[{self.name}] Intento {attempt}/{max_attempts} falló. "
                    f"Reintentando en 1s..."
                )
                time.sleep(1)

        raise last_error or AIProviderError(
            provider=self.name,
            message="Error desconocido tras múltiples intentos",
        )

    # ============================================================
    # HELPERS
    # ============================================================

    def get_api_key(self) -> str | None:
        if self.api_key_override:
            return self.api_key_override
        return settings.ai.gemini_api_key

    def _get_model(self) -> str:
        return settings.ai.gemini_model

    def _build_payload(self, request: AIRequest) -> dict:
        """
        Construye el payload para Gemini.

        Gemini usa:
            - systemInstruction: {parts: [{text}]}
            - contents: [{role: "user", parts: [{text}]}]
            - generationConfig: {responseMimeType, maxOutputTokens, temperature}
        """
        payload = {
            "systemInstruction": {
                "parts": [{"text": request.system_prompt}],
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": request.user_prompt}],
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "maxOutputTokens": request.max_tokens,
                "temperature": 0.2,
            },
        }

        # Si el caller pasó un JSON schema, lo añadimos
        if request.json_schema:
            payload["generationConfig"]["responseSchema"] = request.json_schema

        return payload

    def _parse_response(self, response: requests.Response, model: str) -> AIResponse:
        try:
            data = response.json()
        except (ValueError, TypeError) as e:
            raise AIInvalidOutputError(
                message=f"Respuesta no es JSON válido: {e}",
                raw_output=response.text[:500],
            )

        # Estructura Gemini: candidates[0].content.parts[0].text
        # (Gemini 3.x añade `thoughtSignature` pero lo ignoramos)
        try:
            candidates = data.get("candidates") or []
            if not candidates:
                # A veces Gemini devuelve promptFeedback con blockReason
                feedback = data.get("promptFeedback") or {}
                block = feedback.get("blockReason")
                if block:
                    raise ValueError(f"Contenido bloqueado por Gemini: {block}")
                raise ValueError("No hay 'candidates' en la respuesta")

            candidate = candidates[0]
            finish_reason = candidate.get("finishReason", "")

            content = candidate.get("content") or {}
            parts = content.get("parts") or []
            if not parts:
                raise ValueError(
                    f"No hay 'parts' en la respuesta (finishReason={finish_reason})"
                )

            # Gemini 3.x puede devolver VARIOS parts:
            #   - parts con "text" (respuesta real)
            #   - parts con "thoughtSignature" (thinking interno, IGNORAR)
            # Recorremos TODOS y nos quedamos con los que tienen "text".
            text_chunks: list[str] = []
            for part in parts:
                part_text = part.get("text")
                if part_text:
                    text_chunks.append(part_text)

            text = "".join(text_chunks)

            if not text:
                raise ValueError(
                    f"Texto vacío en la respuesta (finishReason={finish_reason}, "
                    f"parts con thoughtSignature={sum(1 for p in parts if 'thoughtSignature' in p)})"
                )

            # Detectar truncado por MAX_TOKENS
            if finish_reason == "MAX_TOKENS":
                logger.warning(
                    f"[gemini] Respuesta truncada por MAX_TOKENS. "
                    f"Texto parcial: {text[:100]!r}"
                )

        except (KeyError, IndexError, ValueError) as e:
            raise AIInvalidOutputError(
                message=f"Estructura de respuesta inesperada: {e}",
                raw_output=json.dumps(data)[:500],
            )

        parsed = self._parse_json_content(text)

        # Tokens (usageMetadata)
        usage = data.get("usageMetadata") or {}
        tokens_used = usage.get("totalTokenCount")

        return AIResponse(
            data=parsed,
            provider=self.name,
            model=model,
            tokens_used=tokens_used,
            raw_text=text,
        )

    def _parse_json_content(self, content: str) -> dict:
        """Parsea el contenido como JSON (tolerante a markdown)."""
        text = content.strip()

        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        try:
            result = json.loads(text)
            if not isinstance(result, dict):
                raise AIInvalidOutputError(
                    message=f"El JSON no es un objeto (es {type(result).__name__})",
                    raw_output=text[:500],
                )
            return result
        except json.JSONDecodeError:
            pass

        first = text.find("{")
        last = text.rfind("}")
        if first != -1 and last != -1 and last > first:
            candidate = text[first : last + 1]
            try:
                result = json.loads(candidate)
                if isinstance(result, dict):
                    return result
            except json.JSONDecodeError:
                pass

        raise AIInvalidOutputError(
            message="No se pudo extraer JSON válido del contenido",
            raw_output=text[:500],
        )
