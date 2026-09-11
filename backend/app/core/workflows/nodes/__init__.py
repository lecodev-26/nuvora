"""
Nuvora Core — Workflows: Nodes
================================
Cada tipo de nodo tiene una clase que implementa su comportamiento.

Añadir un nodo nuevo en el futuro (API, Webhook, Form, Memory, Tool,
Loop, Delay, Event) es:
    1. Crear una clase que herede de BaseNode.
    2. Registrarla en NODE_REGISTRY.

El engine NO se toca.
"""

from app.core.workflows.nodes.base import BaseNode
from app.core.workflows.nodes.start import StartNode
from app.core.workflows.nodes.message import MessageNode
from app.core.workflows.nodes.question import QuestionNode
from app.core.workflows.nodes.condition import ConditionNode
from app.core.workflows.nodes.variable import VariableNode
from app.core.workflows.nodes.response import ResponseNode
from app.core.workflows.nodes.end import EndNode


# ============================================================
# REGISTRY
# ============================================================
# Mapea node_type → instancia del handler.
# El engine consulta este diccionario para despachar nodos.

NODE_REGISTRY: dict[str, BaseNode] = {
    "start": StartNode(),
    "message": MessageNode(),
    "question": QuestionNode(),
    "condition": ConditionNode(),
    "variable": VariableNode(),
    "response": ResponseNode(),
    "end": EndNode(),
}


def get_node_handler(node_type: str) -> BaseNode:
    """
    Devuelve el handler para un tipo de nodo.
    Lanza ValueError si el tipo no está registrado.
    """
    handler = NODE_REGISTRY.get(node_type)
    if handler is None:
        raise ValueError(f"Tipo de nodo desconocido: {node_type}")
    return handler


__all__ = [
    "BaseNode",
    "NODE_REGISTRY",
    "get_node_handler",
]
