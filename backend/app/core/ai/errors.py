"""
Nuvora Core — AI: Errors
==========================
Errores estructurados de la capa de IA.

Cada error tiene un tipo claro para que los tests y el router puedan
distinguirlos programáticamente.
"""


class AIError(Exception):
    """Base de todos los errores de la capa de IA."""
    pass


class AIProviderError(AIError):
    """
    Error de comunicación con el provider (red, timeout, 5xx, etc.).
    """
    def __init__(self, provider: str, message: str):
        self.provider = provider
        self.message = message
        super().__init__(f"[{provider}] {message}")


class AIInvalidOutputError(AIError):
    """
    El provider devolvió algo que no es JSON válido o no cumple el schema.
    """
    def __init__(self, message: str, raw_output: str | None = None):
        self.message = message
        self.raw_output = raw_output
        super().__init__(message)


class AIConfigError(AIError):
    """
    Configuración inválida (provider desconocido, API key ausente, etc.).
    """
    pass


class AIUnavailableError(AIError):
    """
    La capa de IA está deshabilitada (feature flag AI_ENABLED=false).
    """
    pass
