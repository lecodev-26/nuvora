"""
VARIABLE — Crea o modifica una variable en el contexto.

Config esperada:
    {
        "name": "service",
        "value": "peluquería"
    }

Efecto:
    context.variables["service"] = "peluquería"
"""

from app.core.workflows.nodes.base import BaseNode
from app.core.workflows.execution import ExecutionContext, NodeResult, ExecutionStatus


class VariableNode(BaseNode):
    node_type = "variable"

    def execute(self, node, context: ExecutionContext) -> NodeResult:
        config = self._parse_config(node)
        name = config.get("name", "")
        value = config.get("value", "")

        # TODO 14.5.6: interpolar value con {{variables}}

        variables_update = {}
        if name:
            variables_update[name] = value

        return NodeResult(
            output=None,
            next_node_id=None,
            variables_update=variables_update,
            status=ExecutionStatus.RUNNING,
        )
