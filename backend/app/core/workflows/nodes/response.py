"""
RESPONSE — Respuesta final al usuario.

Config esperada:
    {
        "text": "Gracias, {{name}}. Te esperamos."
    }

Diferencia con MESSAGE:
    - MESSAGE puede aparecer en cualquier punto del workflow.
    - RESPONSE está pensado como cierre visual antes de END.
"""

from app.core.workflows.nodes.base import BaseNode
from app.core.workflows.execution import ExecutionContext, NodeResult, ExecutionStatus


class ResponseNode(BaseNode):
    node_type = "response"

    def execute(self, node, context: ExecutionContext) -> NodeResult:
        config = self._parse_config(node)
        text = config.get("text", "")

        # TODO 14.5.6: interpolar

        return NodeResult(
            output=text,
            next_node_id=None,
            variables_update={},
            status=ExecutionStatus.RUNNING,
        )
