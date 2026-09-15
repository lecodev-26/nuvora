"""
Nuvora Core — AI: Base OpenAI-Compatible Provider
====================================================
Helper común para providers que exponen una API compatible con OpenAI
(Groq, DeepSeek, OpenAI, Mistral, Ollama...).

RESPONSABILIDADES:
    - Construir la petición HTTP (POST /chat/completions)
    - Enviar system + user prompt
    - Forzar respuesta JSON (response_format)
    - Parsear el JSON de salida
    - Mapear errores a AIProviderError / AIInvalidOutputError
    - Retry automático 1 vez en 5xx / timeout

NO conoce la lógica de Nuvora. Solo habla con la API externa.
"""

import json
import time
import logging
from abc import abstractmethod

import requests

from app.config import settings
from app.core.ai.provider import AIProvider, AIRequest, AIResponse
from app.core.ai.errors import AIProviderError, AIInvalidOutputError


logger = logging.getLogger(__name__)


class BaseOpenAICompatibleProvider(AIProvider):
    """
    Base abstracta para providers OpenAI-compatible.

    Subclases deben definir:
        - name:          identificador corto ("groq", "deepseek"...)
        - base_url:      URL base de la API (sin /chat/completions)
        - default_model: modelo por defecto
        - get_api_key(): devuelve la API key (o None)

    Y opcionalmente sobreescribir:
        - _build_headers(api_key) → dict de headers
        - _build_payload(request, model) → dict del body
    """

    name: str = "openai_compatible"
    base_url: str = ""
    default_model: str = ""

    # ============================================================
    # API PÚBLICA
    # ============================================================

    def generate_json(self, request: AIRequest) -> AIResponse:
        """
        Envía el prompt al provider y devuelve la respuesta como JSON parseado.
        """
        api_key = self._resolve_api_key()
        if not api_key:
            raise AIProviderError(
                provider=self.name,
                message=(
                    f"API key no configurada para '{self.name}'. "
                    f"Configura la key del sistema o tu propia key (BYOK)."
                ),
            )

        model = self.get_model()
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = self._build_headers(api_key)
        payload = self._build_payload(request, model)

        # Intentar con retry
        max_attempts = 1 + max(0, settings.ai.max_retries)
        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=request.timeout,
                )

                # HTTP error
                if response.status_code >= 500:
                    raise AIProviderError(
                        provider=self.name,
                        message=f"HTTP {response.status_code} del provider (server error)",
                    )
                if response.status_code == 401:
                    raise AIProviderError(
                        provider=self.name,
                        message="API key inválida o expirada (401)",
                    )
                if response.status_code == 429:
                    raise AIProviderError(
                        provider=self.name,
                        message="Rate limit alcanzado (429). Inténtalo más tarde.",
                    )
                if response.status_code >= 400:
                    # Error del cliente → no reintentar
                    raise AIProviderError(
                        provider=self.name,
                        message=f"HTTP {response.status_code}: {response.text[:200]}",
                    )

                # Parsear respuesta
                return self._parse_response(response, model, request)

            except requests.exceptions.Timeout as e:
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
                # Si es 401/429/400, no reintentar
                if "401" in e.message or "429" in e.message or "HTTP 4" in e.message:
                    raise

            # Reintentar con backoff (solo si quedan intentos)
            if attempt < max_attempts:
                logger.warning(
                    f"[{self.name}] Intento {attempt}/{max_attempts} falló. "
                    f"Reintentando en 1s..."
                )
                time.sleep(1)

        # Todos los intentos fallaron
        raise last_error or AIProviderError(
            provider=self.name,
            message="Error desconocido tras múltiples intentos",
        )

    # ============================================================
    # MÉTODOS A SOBREESCRIBIR
    # ============================================================

    @abstractmethod
    def get_api_key(self) -> str | None:
        """Devuelve la API key del provider (o None si no está configurada)."""
        ...

    def _resolve_api_key(self) -> str | None:
        """
        Resuelve la API key efectiva:
            1. Si hay api_key_override (BYOK) → se usa esa.
            2. Si no → se delega en get_api_key() de la subclase.
        """
        if self.api_key_override:
            return self.api_key_override
        return self.get_api_key()

    def get_model(self) -> str:
        """Devuelve el modelo a usar. Se puede sobreescribir."""
        return self.default_model

    # ============================================================
    # HELPERS INTERNOS
    # ============================================================

    def _build_headers(self, api_key: str) -> dict:
        """Headers HTTP por defecto (Bearer)."""
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _build_payload(self, request: AIRequest, model: str) -> dict:
        """
        Payload JSON por defecto (formato OpenAI chat/completions).
        Fuerza respuesta JSON con response_format.
        """
        messages = [
            {"role": "system", "content": request.system_prompt},
            {"role": "user", "content": request.user_prompt},
        ]

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": 0.2,  # baja temperatura = output más determinista
            "response_format": {"type": "json_object"},
        }

        # Nota: algunos providers aceptan json_schema, pero json_object es
        # el mínimo común denominador que soportan Groq/DeepSeek/OpenAI/Mistral.
        # Gemini NO es OpenAI-compatible y tiene su propio provider.

        return payload

    def _parse_response(
        self,
        response: requests.Response,
        model: str,
        request: AIRequest,
    ) -> AIResponse:
        """
        Parsea la respuesta JSON del provider OpenAI-compatible.
        """
        try:
            data = response.json()
        except (ValueError, TypeError) as e:
            raise AIInvalidOutputError(
                message=f"Respuesta no es JSON válido: {e}",
                raw_output=response.text[:500],
            )

        # Extraer el contenido del mensaje
        try:
            choices = data.get("choices") or []
            if not choices:
                raise ValueError("No hay 'choices' en la respuesta")
            message = choices[0].get("message") or {}
            content = message.get("content")
            if not content:
                raise ValueError("Mensaje vacío")
        except (KeyError, IndexError, ValueError) as e:
            raise AIInvalidOutputError(
                message=f"Estructura de respuesta inesperada: {e}",
                raw_output=json.dumps(data)[:500],
            )

        # Parsear el contenido como JSON
        parsed = self._parse_json_content(content)

        # Tokens usados (si el provider los devuelve)
        usage = data.get("usage") or {}
        tokens_used = usage.get("total_tokens")

        return AIResponse(
            data=parsed,
            provider=self.name,
            model=model,
            tokens_used=tokens_used,
            raw_text=content,
        )

    def _parse_json_content(self, content: str) -> dict:
        """
        Parsea el contenido como JSON. Tolera:
            - Bloques markdown ```json ... ```
            - Texto antes/después del JSON
        """
        text = content.strip()

        # Quitar bloques markdown si los hay
        if text.startswith("```"):
            lines = text.split("\n")
            # Eliminar primera línea (```json) y última (```)
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        # Intentar parsear directo
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

        # Fallback: buscar el primer { y el último }
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


__all__ = ["BaseOpenAICompatibleProvider"]
