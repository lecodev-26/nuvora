"""
START — Punto de entrada del workflow.
No produce output. Simplemente deja que el engine avance al siguiente nodo.
"""

from app.core.workflows.nodes.base import BaseNode
from app.core.workflows.execution import ExecutionContext, NodeResult, ExecutionStatus


class StartNode(BaseNode):
    node_type = "start"

    def execute(self, node, context: ExecutionContext) -> NodeResult:
        return NodeResult(
            output=None,
            next_node_id=None,
            variables_update={},
            status=ExecutionStatus.RUNNING,
        )
