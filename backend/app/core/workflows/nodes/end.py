"""
END — Finaliza la ejecución del workflow.
"""

from app.core.workflows.nodes.base import BaseNode
from app.core.workflows.execution import ExecutionContext, NodeResult, ExecutionStatus


class EndNode(BaseNode):
    node_type = "end"

    def execute(self, node, context: ExecutionContext) -> NodeResult:
        return NodeResult(
            output=None,
            next_node_id=None,
            variables_update={},
            status=ExecutionStatus.COMPLETED,
        )
