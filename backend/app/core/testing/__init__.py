"""
Nuvora Core — Testing (Fase 14.8)
====================================
Bot Tester / Automated Bot Testing.

FILOSOFÍA:
    - El Tester NO ejecuta workflows. Llama al WorkflowEngine (14.5).
    - El Tester NO modifica el Engine.
    - El Tester NO tiene side effects.
    - Los tests se ejecutan en un sandbox lógico.

ARQUITECTURA:
    TestRunner → WorkflowEngine (14.5) → ExecutionResult
                                        ↓
                                    Assertions
                                        ↓
                                    TestRunResult

Público:
    - TestRunner (en 14.8.3)
    - Assertions (en 14.8.4)
    - Analyzer (en 14.8.5)
"""

from app.core.testing.errors import (
    TestingError,
    TestNotFoundError,
    TestDefinitionError,
    TestExecutionError,
    TestAssertionError,
    TestTimeoutError,
    TestLimitExceededError,
)


__all__ = [
    # Errors
    "TestingError",
    "TestNotFoundError",
    "TestDefinitionError",
    "TestExecutionError",
    "TestAssertionError",
    "TestTimeoutError",
    "TestLimitExceededError",
]
