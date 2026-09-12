"""
MESSAGE — Envía un mensaje al usuario.

Config esperada:
    {
        "text": "Hola {{name}}"
    }

Las variables se interpolan contra context.variables:
    {{name}} → context.variables["name"]

Si la variable no existe, se deja el placeholder original (no rompe).
"""

from app.core.workflows.nodes.base import BaseNode
from app.core.workflows.execution import ExecutionContext, NodeResult, ExecutionStatus
from app.core.workflows.variables import interpolate


class MessageNode(BaseNode):
    node_type = "message"

    def execute(self, node, context: ExecutionContext) -> NodeResult:
        config = self._parse_config(node)
        text = config.get("text", "")

        # Interpolar {{variables}} con el contexto
        text = interpolate(text, context.variables)

        return NodeResult(
            output=text,
            next_node_id=None,
            variables_update={},
            status=ExecutionStatus.RUNNING,
        )
