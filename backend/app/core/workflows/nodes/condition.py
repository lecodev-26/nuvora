"""
CONDITION — Evalúa una condición y decide el siguiente nodo.

Config esperada:
    {
        "condition": "age > 18"
    }

IMPORTANTE:
    - El nodo NO resuelve las transiciones. Solo expone que es un nodo
      de tipo CONDITION. La resolución de `true` / `false` la hará el
      engine en 14.5.6 usando la tabla `workflow_transitions`.

    - Este handler NO ejecuta la condición. Solo deja pasar.
      El engine se encarga en 14.5.6.
"""

from app.core.workflows.nodes.base import BaseNode
from app.core.workflows.execution import ExecutionContext, NodeResult, ExecutionStatus


class ConditionNode(BaseNode):
    node_type = "condition"

    def execute(self, node, context: ExecutionContext) -> NodeResult:
        # La evaluación real de la condición se hará en el engine
        # cuando llegue 14.5.6 (transitions.py + conditions.py).
        return NodeResult(
            output=None,
            next_node_id=None,
            variables_update={},
            status=ExecutionStatus.RUNNING,
        )
