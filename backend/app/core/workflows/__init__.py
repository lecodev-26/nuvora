"""
Nuvora Core — Workflows (Fase 14.5)
=====================================
Motor interno de workflows.

NO conoce el frontend.
NO conoce canales externos.
NO usa IA.
"""

from app.core.workflows.execution import (
    ExecutionStatus,
    ExecutionContext,
    ExecutionResult,
    NodeResult,
)
from app.core.workflows.errors import (
    WorkflowError,
    WorkflowNotFoundError,
    WorkflowValidationError,
    WorkflowExecutionError,
    MaxStepsExceeded,
    ConditionError,
    NodeExecutionError,
)
from app.core.workflows.validator import (
    WorkflowValidator,
    validate_workflow,
    VALID_NODE_TYPES,
)


__all__ = [
    # Execution
    "ExecutionStatus",
    "ExecutionContext",
    "ExecutionResult",
    "NodeResult",
    # Errors
    "WorkflowError",
    "WorkflowNotFoundError",
    "WorkflowValidationError",
    "WorkflowExecutionError",
    "MaxStepsExceeded",
    "ConditionError",
    "NodeExecutionError",
    # Validator
    "WorkflowValidator",
    "validate_workflow",
    "VALID_NODE_TYPES",
]
