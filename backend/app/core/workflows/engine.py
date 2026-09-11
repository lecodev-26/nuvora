"""
Nuvora Core — Workflows: Engine
==================================
Motor de ejecución de workflows.

RESPONSABILIDADES:
    - Cargar workflow (dict con nodes + transitions).
    - Validar con WorkflowValidator antes de ejecutar.
    - Localizar nodo START (o start_node_id explícito).
    - Bucle: ejecutar nodo → resolver transición → siguiente nodo.
    - Protección contra bucles con MAX_STEPS.
    - Manejar WAITING_INPUT (nodo QUESTION pausa la ejecución).
    - Manejar COMPLETED (nodo END).
    - Devolver ExecutionResult.

DISEÑO:
    - El engine NO conoce el frontend ni canales externos.
    - El engine NO evalúa condiciones (eso es 14.5.6).
    - El engine NO persiste ejecuciones (eso es 14.13).
    - El engine NO usa IA.

RESOLUCIÓN DE TRANSICIONES (14.5.5 — temporal):
    - Si el nodo devuelve next_node_id → usarlo.
    - Si no, tomar la primera transición saliente ordenada por 'order'.
    - En 14.5.6 se sustituye por evaluación real de conditions.

NOTA SOBRE EL FORMATO DE NODOS:
    El engine acepta nodos en formato dict (para tests en memoria y para
    el router de 14.5.7/14.5.8 que convertirá SQLAlchemy → dict).
    Antes de pasarlos a los handlers (que esperan objetos con atributos
    .node_id, .type, .config), los envuelve con _NodeView.
"""

from typing import Optional, Any
from types import SimpleNamespace

from app.core.workflows.execution import (
    ExecutionContext,
    ExecutionResult,
    ExecutionStatus,
)
from app.core.workflows.errors import (
    WorkflowValidationError,
    WorkflowExecutionError,
    MaxStepsExceeded,
    NodeExecutionError,
)
from app.core.workflows.validator import WorkflowValidator
from app.core.workflows.nodes import get_node_handler


def _node_view(node_dict: dict) -> SimpleNamespace:
    """
    Envuelve un dict de nodo en un objeto con atributos.

    Los handlers de 14.5.3 esperan:
        node.node_id
        node.type
        node.config  (str JSON o None)

    El engine trabaja con dicts (más fácil de testear y de serializar).
    Esta función hace la conversión.

    IMPORTANTE: node.config se deja como JSON string si viene dict,
    porque BaseNode._parse_config() espera un string JSON o None.
    """
    import json

    config = node_dict.get("config")
    if isinstance(config, dict):
        config = json.dumps(config)

    return SimpleNamespace(
        node_id=node_dict["node_id"],
        type=node_dict["type"],
        config=config,
    )


class WorkflowEngine:
    """
    Motor de ejecución determinista de workflows.

    Uso:
        engine = WorkflowEngine()
        result = engine.run(workflow_dict, initial_variables={"x": 1})
    """

    MAX_STEPS_DEFAULT = 100

    def __init__(self):
        self.validator = WorkflowValidator()

    def run(
        self,
        workflow_data: dict,
        bot_id: int = 0,
        workflow_id: int = 0,
        initial_variables: Optional[dict[str, Any]] = None,
        max_steps: int = MAX_STEPS_DEFAULT,
        start_node_id: Optional[str] = None,
    ) -> ExecutionResult:
        """
        Ejecuta un workflow.

        Args:
            workflow_data: dict con 'nodes' y 'transitions'.
            bot_id: id del bot (para contexto, futura persistencia).
            workflow_id: id del workflow (para contexto, futura persistencia).
            initial_variables: variables iniciales del contexto.
            max_steps: límite de pasos (protección contra bucles).
            start_node_id: si se pasa, se usa como nodo inicial en vez de buscar START.

        Returns:
            ExecutionResult

        Raises:
            WorkflowValidationError: workflow inválido.
            MaxStepsExceeded: se superó max_steps.
            WorkflowExecutionError: error estructural.
            NodeExecutionError: error al ejecutar un nodo.
        """
        # 1. Validación estática
        self.validator.validate(workflow_data)

        # 2. Indexar nodos por node_id
        nodes = workflow_data.get("nodes") or []
        transitions = workflow_data.get("transitions") or []
        nodes_map = {n["node_id"]: n for n in nodes}

        # 3. Determinar nodo inicial
        if start_node_id is not None:
            if start_node_id not in nodes_map:
                raise WorkflowExecutionError(
                    f"Nodo inicial '{start_node_id}' no existe en el workflow."
                )
            current_node_id = start_node_id
        else:
            start_node = next((n for n in nodes if n.get("type") == "start"), None)
            if start_node is None:
                raise WorkflowExecutionError("No se encontró nodo START en el workflow.")
            current_node_id = start_node["node_id"]

        # 4. Contexto de ejecución
        context = ExecutionContext(
            bot_id=bot_id,
            workflow_id=workflow_id,
            current_node_id=current_node_id,
            variables=dict(initial_variables) if initial_variables else {},
        )

        outputs: list[dict[str, Any]] = []

        # 5. Bucle principal
        while True:
            # Protección contra bucles
            if context.steps >= max_steps:
                raise MaxStepsExceeded(max_steps=max_steps)

            node = nodes_map.get(current_node_id)
            if node is None:
                raise WorkflowExecutionError(
                    f"Nodo '{current_node_id}' no encontrado durante la ejecución."
                )

            node_type = node.get("type")
            handler = get_node_handler(node_type)  # Lanza ValueError si desconoce

            # Envolver el dict en un objeto con atributos (.node_id, .type, .config)
            node_obj = _node_view(node)

            # Ejecutar nodo
            try:
                node_result = handler.execute(node_obj, context)
            except Exception as e:
                raise NodeExecutionError(
                    node_id=current_node_id,
                    message=str(e),
                ) from e

            # Registrar paso en contexto
            context.register_step(
                node_id=current_node_id,
                node_type=node_type,
                output=node_result.output,
            )

            # Acumular output si hay
            if node_result.output is not None:
                outputs.append({
                    "step": context.steps,
                    "node_id": current_node_id,
                    "type": node_type,
                    "text": node_result.output,
                })

            # Actualizar variables
            if node_result.variables_update:
                context.variables.update(node_result.variables_update)

            # ¿El nodo pide pausa? (QUESTION)
            if node_result.status == ExecutionStatus.WAITING_INPUT:
                return ExecutionResult(
                    status=ExecutionStatus.WAITING_INPUT,
                    outputs=outputs,
                    variables=context.variables,
                    current_node_id=current_node_id,
                    steps_used=context.steps,
                )

            # ¿El nodo indica COMPLETED? (END)
            if node_result.status == ExecutionStatus.COMPLETED:
                return ExecutionResult(
                    status=ExecutionStatus.COMPLETED,
                    outputs=outputs,
                    variables=context.variables,
                    current_node_id=current_node_id,
                    steps_used=context.steps,
                )

            # Resolver siguiente nodo
            next_id = self._resolve_next_node(
                node_result=node_result,
                current_node_id=current_node_id,
                transitions=transitions,
                nodes_map=nodes_map,
            )

            if next_id is None:
                return ExecutionResult(
                    status=ExecutionStatus.COMPLETED,
                    outputs=outputs,
                    variables=context.variables,
                    current_node_id=current_node_id,
                    steps_used=context.steps,
                )

            current_node_id = next_id

    def _resolve_next_node(
        self,
        node_result,
        current_node_id: str,
        transitions: list[dict],
        nodes_map: dict,
    ) -> Optional[str]:
        """
        Resuelve el siguiente nodo.

        Prioridad:
            1. node_result.next_node_id (si el nodo lo forzó explícitamente).
            2. Primera transición saliente ordenada por 'order'.

        NOTA: En 14.5.6 se añadirá evaluación de 'condition'.
        """
        # 1. Salto explícito del nodo
        if node_result.next_node_id:
            if node_result.next_node_id not in nodes_map:
                raise WorkflowExecutionError(
                    f"Nodo '{current_node_id}' devolvió next_node_id "
                    f"'{node_result.next_node_id}' que no existe."
                )
            return node_result.next_node_id

        # 2. Buscar transiciones salientes
        outgoing = [
            t for t in transitions
            if t.get("from_node_id") == current_node_id
        ]

        if not outgoing:
            return None

        # Ordenar por 'order' (por defecto 0)
        outgoing.sort(key=lambda t: t.get("order", 0) or 0)

        # 14.5.5: primera transición (placeholder)
        # 14.5.6: evaluará condition y elegirá la correcta
        return outgoing[0]["to_node_id"]


def run_workflow(
    workflow_data: dict,
    bot_id: int = 0,
    workflow_id: int = 0,
    initial_variables: Optional[dict[str, Any]] = None,
    max_steps: int = WorkflowEngine.MAX_STEPS_DEFAULT,
    start_node_id: Optional[str] = None,
) -> ExecutionResult:
    """Wrapper de conveniencia."""
    return WorkflowEngine().run(
        workflow_data=workflow_data,
        bot_id=bot_id,
        workflow_id=workflow_id,
        initial_variables=initial_variables,
        max_steps=max_steps,
        start_node_id=start_node_id,
    )
