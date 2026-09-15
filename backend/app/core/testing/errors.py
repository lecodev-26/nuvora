"""
Nuvora Core — Testing: Errors
================================
Errores específicos del Bot Tester (Fase 14.8).

Jerarquía:
    TestingError (base)
    ├── TestNotFoundError         → test no existe
    ├── TestDefinitionError       → definición inválida del test
    ├── TestExecutionError        → error técnico al ejecutar
    ├── TestAssertionError        → assertion mal formada (no fallida)
    ├── TestTimeoutError          → timeout del test
    └── TestLimitExceededError    → se superó un límite configurable
"""


class TestingError(Exception):
    """Base de todos los errores del Bot Tester."""
    pass


class TestNotFoundError(TestingError):
    """El test solicitado no existe."""
    pass


class TestDefinitionError(TestingError):
    """
    La definición del test es inválida:
        - sin input_messages
        - sin assertions
        - tipo de assertion desconocido
        - etc.
    """
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class TestExecutionError(TestingError):
    """
    Error técnico al ejecutar el test.
    NO es un FAIL de assertion. Es un ERROR real.
    """
    def __init__(self, message: str, original: Exception | None = None):
        self.message = message
        self.original = original
        super().__init__(message)


class TestAssertionError(TestingError):
    """
    La assertion está mal formada (a nivel de esquema).
    NO confundir con 'assertion failed' (que es un resultado esperado).
    """
    def __init__(self, assertion_type: str, message: str):
        self.assertion_type = assertion_type
        self.message = message
        super().__init__(f"[{assertion_type}] {message}")


class TestTimeoutError(TestingError):
    """El test superó el timeout configurado."""
    def __init__(self, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Timeout del test: {timeout_seconds}s")


class TestLimitExceededError(TestingError):
    """Se superó un límite configurable del Tester."""
    def __init__(self, limit_name: str, limit_value: int):
        self.limit_name = limit_name
        self.limit_value = limit_value
        super().__init__(
            f"Límite excedido en {limit_name}: máximo {limit_value}"
        )


__all__ = [
    "TestingError",
    "TestNotFoundError",
    "TestDefinitionError",
    "TestExecutionError",
    "TestAssertionError",
    "TestTimeoutError",
    "TestLimitExceededError",
]
