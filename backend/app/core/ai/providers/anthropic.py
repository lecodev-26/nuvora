"""
Nuvora Core — AI: Anthropic Provider
=======================================
Implementación del provider Anthropic (Claude).

Anthropic usa su propia API (no OpenAI-compatible):
    POST https://api.anthropic.com/v1/messages

Headers:
    - x-api-key: <key>
    - anthropic-version: 2023-06-01

Payload:
    {
        "model": "claude-3-5-haiku-latest",
        "max_tokens": 4000,
        "system": "...",
        "messages": [{"role": "user", "content": "..."}]
    }

Structured output: Anthropic no tiene un response_format nativo
para JSON. Usamos técnica de "prefill" forzando respuesta con "{":
    messages: [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "{"}
    ]
Y leemos la respuesta con el "{" prefijado.
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


ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


@register_provider("anthropic")
class AnthropicProvider(AIProvider):
    """Provider Anthropic (Claude, API propia)."""

    name = "anthropic"

    # ============================================================
    # API PÚBLICA
    # ============================================================

    def generate_json(self, request: AIRequest) -> AIResponse:
        api_key = self.get_api_key()
        if not api_key:
            raise AIProviderError(
                provider=self.name,
                message=(
                    "API key de Anthropic no configurada. "
                    "Configura ANTHROPIC_API_KEY o tu propia key (BYOK)."
                ),
            )

        model = self._get_model()
        headers = {
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "Content-Type": "application/json",
        }
        payload = self._build_payload(request, model)

        max_attempts = 1 + max(0, settings.ai.max_retries)
        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.post(
                    ANTHROPIC_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=request.timeout,
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
        return settings.ai.anthropic_api_key

    def _get_model(self) -> str:
        return settings.ai.anthropic_model

    def _build_payload(self, request: AIRequest, model: str) -> dict:
        """
        Payload para Anthropic.

        Truco de prefill: pedimos al assistant que empiece la respuesta con
        "{", y luego leemos la respuesta con el "{" añadido al principio.
        Esto fuerza salida JSON sin necesidad de response_format.
        """
        # Añadir instrucción de JSON al system prompt
        system_prompt = (
            request.system_prompt
            + "\n\nDevuelve EXCLUSIVAMENTE un objeto JSON válido. "
            "Sin markdown, sin explicaciones, solo el JSON."
        )

        messages = [
            {"role": "user", "content": request.user_prompt},
            # Prefill: forzamos el inicio del JSON
            {"role": "assistant", "content": "{"},
        ]

        return {
            "model": model,
            "max_tokens": request.max_tokens,
            "temperature": 0.2,
            "system": system_prompt,
            "messages": messages,
        }

    def _parse_response(self, response: requests.Response, model: str) -> AIResponse:
        try:
            data = response.json()
        except (ValueError, TypeError) as e:
            raise AIInvalidOutputError(
                message=f"Respuesta no es JSON válido: {e}",
                raw_output=response.text[:500],
            )

        # Estructura Anthropic: content[0].text
        try:
            content_blocks = data.get("content") or []
            if not content_blocks:
                raise ValueError("No hay 'content' en la respuesta")
            text = content_blocks[0].get("text")
            if not text:
                raise ValueError("Texto vacío en la respuesta")
        except (KeyError, IndexError, ValueError) as e:
            raise AIInvalidOutputError(
                message=f"Estructura de respuesta inesperada: {e}",
                raw_output=json.dumps(data)[:500],
            )

        # Reconstruir el JSON: Anthropic devuelve el texto SIN el "{" inicial
        # porque se lo pasamos como prefill. Se lo re-añadimos.
        full_text = "{" + text

        parsed = self._parse_json_content(full_text)

        # Tokens
        usage = data.get("usage") or {}
        input_tokens = usage.get("input_tokens") or 0
        output_tokens = usage.get("output_tokens") or 0
        tokens_used = input_tokens + output_tokens if (input_tokens or output_tokens) else None

        return AIResponse(
            data=parsed,
            provider=self.name,
            model=model,
            tokens_used=tokens_used,
            raw_text=full_text,
        )

    def _parse_json_content(self, content: str) -> dict:
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
