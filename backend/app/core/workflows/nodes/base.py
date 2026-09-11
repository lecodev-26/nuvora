"""
Nuvora Core — Workflows: BaseNode
====================================
Interfaz común para todos los nodos.
"""

from abc import ABC, abstractmethod

from app.core.workflows.execution import ExecutionContext, NodeResult


class BaseNode(ABC):
    """
    Clase base de todos los nodos.

    Atributos:
        node_type: tipo de nodo (coincide con el campo `type` del modelo).

    Métodos:
        execute(node, context) → NodeResult

    El engine coordina; el nodo ejecuta su comportamiento.
    El nodo NO resuelve transiciones (eso es responsabilidad del engine).
    """

    node_type: str = "base"

    @abstractmethod
    def execute(self, node, context: ExecutionContext) -> NodeResult:
        """
        Ejecuta el nodo.

        Args:
            node: instancia del modelo WorkflowNode (SQLAlchemy).
                  Solo leemos node.node_id, node.type, node.config.
            context: ExecutionContext en curso.

        Returns:
            NodeResult con output, next_node_id (opcional), variables_update.
        """
        pass

    # Helper común
    def _parse_config(self, node) -> dict:
        """Parsea node.config (TEXT JSON) a dict. Devuelve {} si vacío."""
        import json
        if not node.config:
            return {}
        try:
            return json.loads(node.config)
        except (ValueError, TypeError):
            return {}
