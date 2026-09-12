"""
VARIABLE — Crea o modifica una variable en el contexto.

Config esperada:
    {
        "name": "greeting",
        "value": "Hola {{name}}"
    }

Efecto:
    context.variables["greeting"] = "Hola Manuel"

NOTA: el valor se interpola contra las variables ACTUALES del contexto
antes de asignar. Si quieres asignar literal "{{x}}", usa escape (futuro).
"""

from app.core.workflows.nodes.base import BaseNode
from app.core.workflows.execution import ExecutionContext, NodeResult, ExecutionStatus
from app.core.workflows.variables import interpolate


class VariableNode(BaseNode):
    node_type = "variable"

    def execute(self, node, context: ExecutionContext) -> NodeResult:
        config = self._parse_config(node)
        name = config.get("name", "")
        value = config.get("value", "")

        # Interpolar {{variables}} en el valor
        if isinstance(value, str):
            value = interpolate(value, context.variables)

        variables_update = {}
        if name:
            variables_update[name] = value

        return NodeResult(
            output=None,
            next_node_id=None,
            variables_update=variables_update,
            status=ExecutionStatus.RUNNING,
        )
