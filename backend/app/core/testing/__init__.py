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
                                    Assertion Engine
                                        ↓
                                    TestRunResult

    WorkflowAnalyzer → Static checks (sin ejecución)

Público:
    - TestRunner (14.8.3)
    - evaluate_assertion, evaluate_all_assertions (14.8.4)
    - WorkflowAnalyzer (14.8.5)
    - Errores del Tester
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
from app.core.testing.assertions import (
    evaluate_assertion,
    evaluate_all_assertions,
    summarize_assertions,
)
from app.core.testing.runner import TestRunner
from app.core.testing.analyzer import WorkflowAnalyzer
from app.core.testing.ai_generator import AITestGenerator


__all__ = [
    # Runner
    "TestRunner",
    # Assertions
    "evaluate_assertion",
    "evaluate_all_assertions",
    "summarize_assertions",
    # Analyzer
    "WorkflowAnalyzer",
    # AI Generator
    "AITestGenerator",
    # Errors
    "TestingError",
    "TestNotFoundError",
    "TestDefinitionError",
    "TestExecutionError",
    "TestAssertionError",
    "TestTimeoutError",
    "TestLimitExceededError",
]
