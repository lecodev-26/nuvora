"""
Nuvora Core — Workflows: Execution
====================================
Estructuras de ejecución.

SEPARACIÓN:
    - Workflow     → definición estática (en BD)
    - ExecutionContext → estado en memoria durante una ejecución
    - ExecutionResult  → resultado de una ejecución

Preparado para persistencia futura (14.13) sin romper el diseño:
    - ExecutionContext es serializable (todo dict/str/int).
    - ExecutionStatus cubre todas las fases.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any


class ExecutionStatus(str, Enum):
    """
    Estado de una ejecución de workflow.

    - RUNNING:        El engine está ejecutando nodos.
    - WAITING_INPUT:  El engine se ha detenido esperando entrada del usuario
                      (ej: nodo QUESTION).
    - COMPLETED:      Se alcanzó un nodo END correctamente.
    - FAILED:         Error durante la ejecución.
    """
    RUNNING = "running"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class NodeResult:
    """
    Resultado de ejecutar un único nodo.

    - output:            Texto que se muestra al usuario (opcional).
    - next_node_id:      Nodo siguiente si el propio nodo decide un salto
                         (ej: CONDITION puede resolver aquí, aunque en 14.5
                         las transiciones se resuelven en el engine).
    - variables_update:  Actualización de variables del contexto.
    - status:            Estado del workflow tras este nodo.
    """
    output: Optional[str] = None
    next_node_id: Optional[str] = None
    variables_update: dict[str, Any] = field(default_factory=dict)
    status: ExecutionStatus = ExecutionStatus.RUNNING


@dataclass
class ExecutionContext:
    """
    Estado en memoria de una ejecución.

    En 14.5 no se persiste.
    En 14.13 podrá serializarse y persistirse en tabla workflow_executions.
    """
    bot_id: int
    workflow_id: int
    conversation_id: Optional[int] = None

    # Nodo actual (lógico, no PK)
    current_node_id: Optional[str] = None

    # Variables de ejecución (interpolables como {{name}})
    variables: dict[str, Any] = field(default_factory=dict)

    # Contador de pasos ejecutados (para protección contra bucles)
    steps: int = 0

    # Historial de nodos visitados (útil para debugging)
    history: list[dict[str, Any]] = field(default_factory=list)

    def register_step(self, node_id: str, node_type: str, output: Optional[str] = None) -> None:
        """Registra un paso en el historial."""
        self.steps += 1
        self.current_node_id = node_id
        self.history.append({
            "step": self.steps,
            "node_id": node_id,
            "type": node_type,
            "output": output,
        })


@dataclass
class ExecutionResult:
    """
    Resultado final de una ejecución.

    Contiene el estado, los outputs generados, las variables finales
    y la información de dónde se detuvo.
    """
    status: ExecutionStatus
    outputs: list[dict[str, Any]] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    current_node_id: Optional[str] = None
    steps_used: int = 0
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Serializa para respuesta JSON."""
        return {
            "status": self.status.value,
            "outputs": self.outputs,
            "variables": self.variables,
            "current_node_id": self.current_node_id,
            "steps_used": self.steps_used,
            "error": self.error,
        }
