"""
Nuvora Core — Workflows: Errors
=================================
Errores estructurados del Workflow Engine.

Cada error tiene un tipo claro para que el engine y los tests puedan
distinguirlos programáticamente.
"""


class WorkflowError(Exception):
    """Base de todos los errores de workflows."""
    pass


class WorkflowNotFoundError(WorkflowError):
    """Workflow no existe."""
    pass


class WorkflowValidationError(WorkflowError):
    """
    Workflow inválido (falla la validación estática).

    Contiene una lista de errores concretos.
    """
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"Validación fallida: {len(errors)} error(es)")

    def __str__(self):
        return "WorkflowValidationError:\n  - " + "\n  - ".join(self.errors)


class WorkflowExecutionError(WorkflowError):
    """Error durante la ejecución."""
    pass


class MaxStepsExceeded(WorkflowExecutionError):
    """Se superó el límite de pasos (protección contra bucles)."""
    def __init__(self, max_steps: int):
        self.max_steps = max_steps
        super().__init__(f"MaxStepsExceeded: se superaron {max_steps} pasos")


class NodeExecutionError(WorkflowExecutionError):
    """Error al ejecutar un nodo específico."""
    def __init__(self, node_id: str, message: str):
        self.node_id = node_id
        self.message = message
        super().__init__(f"Error en nodo '{node_id}': {message}")


class ConditionError(WorkflowError):
    """Error al evaluar una condición."""
    def __init__(self, expression: str, message: str):
        self.expression = expression
        self.message = message
        super().__init__(f"ConditionError en '{expression}': {message}")
