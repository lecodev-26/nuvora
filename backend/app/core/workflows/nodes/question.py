"""
QUESTION — Solicita información al usuario.

Config esperada:
    {
        "text": "¿Cómo te llamas?",
        "variable": "name"
    }

Comportamiento:
    - Genera output (la pregunta), con {{variables}} interpoladas.
    - Marca status=WAITING_INPUT.
    - El engine se detiene aquí hasta que llegue una entrada
      (persistencia real de ejecuciones en 14.13).
    - La respuesta del usuario se asignará a `variable` en context.variables.
"""

from app.core.workflows.nodes.base import BaseNode
from app.core.workflows.execution import ExecutionContext, NodeResult, ExecutionStatus
from app.core.workflows.variables import interpolate


class QuestionNode(BaseNode):
    node_type = "question"

    def execute(self, node, context: ExecutionContext) -> NodeResult:
        config = self._parse_config(node)
        text = config.get("text", "")
        variable_name = config.get("variable", "")

        # Interpolar {{variables}} en el texto de la pregunta
        text = interpolate(text, context.variables)

        # Guardamos la variable esperada en el contexto (sin valor aún)
        variables_update = {}
        if variable_name:
            variables_update[variable_name] = None

        return NodeResult(
            output=text,
            next_node_id=None,
            variables_update=variables_update,
            status=ExecutionStatus.WAITING_INPUT,
        )
