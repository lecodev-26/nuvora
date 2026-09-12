"""
RESPONSE — Respuesta final al usuario.

Config esperada:
    {
        "text": "Gracias, {{name}}. Te esperamos."
    }

Diferencia con MESSAGE:
    - MESSAGE puede aparecer en cualquier punto del workflow.
    - RESPONSE está pensado como cierre visual antes de END.

Las variables se interpolan contra context.variables:
    {{name}} → context.variables["name"]
"""

from app.core.workflows.nodes.base import BaseNode
from app.core.workflows.execution import ExecutionContext, NodeResult, ExecutionStatus
from app.core.workflows.variables import interpolate


class ResponseNode(BaseNode):
    node_type = "response"

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
