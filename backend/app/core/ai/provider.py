"""
Nuvora Core — AI: Provider
============================
Interfaz abstracta de la capa de proveedores de IA.

CONTRATO:
    - Cada provider implementa generate_json().
    - La entrada es SIEMPRE texto (system_prompt + user_prompt).
    - La salida es SIEMPRE un dict (JSON parseado).
    - Si el provider falla → lanza AIProviderError.
    - Si el provider devuelve algo no parseable → lanza AIInvalidOutputError.

NO duplica lógica de Nuvora. NO ejecuta workflows.
Solo habla con la API externa y devuelve JSON.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class AIRequest:
    """Payload normalizado que recibe un provider."""
    system_prompt: str
    user_prompt: str
    json_schema: Optional[dict] = None   # JSON Schema esperado (opcional)
    max_tokens: int = 4000
    timeout: int = 30


@dataclass
class AIResponse:
    """Respuesta normalizada de un provider."""
    data: dict                # JSON parseado
    provider: str             # "gemini" | "groq" | "deepseek"
    model: str
    tokens_used: Optional[int] = None
    raw_text: Optional[str] = None   # útil para debug


class AIProvider(ABC):
    """
    Interfaz común de providers.
    """

    #: Nombre corto del provider (para logs y response)
    name: str = "unknown"

    @abstractmethod
    def generate_json(self, request: AIRequest) -> AIResponse:
        """
        Envía el prompt al provider y devuelve la respuesta como JSON parseado.

        Args:
            request: AIRequest con system/user prompt + opciones.

        Returns:
            AIResponse con data (dict), provider, model, tokens.

        Raises:
            AIProviderError: fallo de red/timeout/HTTP/API.
            AIInvalidOutputError: respuesta no parseable o schema inválido.
        """
        ...


__all__ = ["AIProvider", "AIRequest", "AIResponse"]
