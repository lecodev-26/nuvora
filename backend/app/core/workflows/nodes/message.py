"""
MESSAGE — Envía un mensaje al usuario.

Config esperada:
    {
        "text": "Hola {{name}}"
    }

Las variables se interpolan contra context.variables.
La interpolación real se implementará en 14.5.6 (variables.py).
Por ahora, dejamos un placeholder que NO rompe nada.
"""

from app.core.workflows.nodes.base import BaseNode
from app.core.workflows.execution import ExecutionContext, NodeResult, ExecutionStatus


class MessageNode(BaseNode):
    node_type = "message"

    def execute(self, node, context: ExecutionContext) -> NodeResult:
        config = self._parse_config(node)
        text = config.get("text", "")

        # TODO 14.5.6: interpolar con {{variables}}
        # Por ahora, texto plano

        return NodeResult(
            output=text,
            next_node_id=None,
            variables_update={},
            status=ExecutionStatus.RUNNING,
        )
