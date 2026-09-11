"""
Nuvora — Schemas Pydantic para Workflows (Fase 14.5)
======================================================
Contratos de entrada/salida para el Workflow Engine.

Estos schemas NO contienen lógica de ejecución.
Solo definen la forma de los datos.

REGLA:
    - El campo `config` de los nodos es un dict JSON (Pydantic lo valida,
      SQLAlchemy lo serializa a TEXT en BD).
    - Los schemas de Response exponen `config` como dict (parseado desde TEXT).
    - Compatibilidad total con el patrón de Nuvora.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any, Literal


# ============================================================
# TIPOS LITERALES
# ============================================================

WorkflowStatus = Literal["draft", "active", "archived"]
WorkflowTrigger = Literal["manual", "message", "keyword"]
NodeType = Literal[
    "start",
    "message",
    "question",
    "condition",
    "variable",
    "response",
    "end",
]


# ============================================================
# NODOS
# ============================================================

class WorkflowNodeCreate(BaseModel):
    """Definición de un nodo al crear/actualizar un workflow."""
    node_id: str = Field(..., min_length=1, max_length=50)
    type: NodeType
    name: Optional[str] = Field(None, max_length=200)
    config: Optional[dict[str, Any]] = None


class WorkflowNodeUpdate(BaseModel):
    """Actualización parcial de un nodo."""
    type: Optional[NodeType] = None
    name: Optional[str] = Field(None, max_length=200)
    config: Optional[dict[str, Any]] = None


class WorkflowNodeResponse(BaseModel):
    """Respuesta con datos de un nodo."""
    id: int
    workflow_id: int
    node_id: str
    type: NodeType
    name: Optional[str] = None
    config: Optional[dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# TRANSICIONES
# ============================================================

class WorkflowTransitionCreate(BaseModel):
    """Definición de una transición entre dos nodos."""
    from_node_id: str = Field(..., min_length=1, max_length=50)
    to_node_id: str = Field(..., min_length=1, max_length=50)
    condition: Optional[str] = None
    label: Optional[str] = Field(None, max_length=50)
    order: int = 0


class WorkflowTransitionUpdate(BaseModel):
    """Actualización parcial de una transición."""
    condition: Optional[str] = None
    label: Optional[str] = Field(None, max_length=50)
    order: Optional[int] = None


class WorkflowTransitionResponse(BaseModel):
    """Respuesta con datos de una transición."""
    id: int
    workflow_id: int
    from_node_id: str
    to_node_id: str
    condition: Optional[str] = None
    label: Optional[str] = None
    order: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# WORKFLOW
# ============================================================

class WorkflowCreate(BaseModel):
    """
    Crear un workflow completo (con nodos y transiciones).
    En una sola llamada se puede crear el workflow y su contenido.
    """
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: WorkflowStatus = "draft"
    trigger: WorkflowTrigger = "manual"
    entry_node_id: Optional[str] = Field(None, max_length=50)
    meta: Optional[dict[str, Any]] = None

    nodes: list[WorkflowNodeCreate] = Field(default_factory=list)
    transitions: list[WorkflowTransitionCreate] = Field(default_factory=list)


class WorkflowUpdate(BaseModel):
    """Actualización parcial de un workflow."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[WorkflowStatus] = None
    trigger: Optional[WorkflowTrigger] = None
    entry_node_id: Optional[str] = Field(None, max_length=50)
    meta: Optional[dict[str, Any]] = None


class WorkflowResponse(BaseModel):
    """Respuesta con datos de un workflow (sin nodos ni transiciones)."""
    id: int
    bot_id: int
    name: str
    description: Optional[str] = None
    status: WorkflowStatus
    version: int = 1
    trigger: WorkflowTrigger = "manual"
    entry_node_id: Optional[str] = None
    meta: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WorkflowDetailResponse(WorkflowResponse):
    """Respuesta completa con nodos y transiciones."""
    nodes: list[WorkflowNodeResponse] = Field(default_factory=list)
    transitions: list[WorkflowTransitionResponse] = Field(default_factory=list)


class WorkflowListResponse(BaseModel):
    """Respuesta con la lista de workflows de un bot."""
    workflows: list[WorkflowResponse]
    total: int


# ============================================================
# EJECUCIÓN (para endpoint /run de testing)
# ============================================================

class WorkflowRunRequest(BaseModel):
    """Solicitud para ejecutar un workflow (testing)."""
    initial_variables: dict[str, Any] = Field(default_factory=dict)
    max_steps: int = Field(100, ge=1, le=1000)


class WorkflowRunOutput(BaseModel):
    """Un output individual del workflow."""
    node_id: str
    type: NodeType
    text: Optional[str] = None


class WorkflowRunResponse(BaseModel):
    """Respuesta de la ejecución de un workflow."""
    status: Literal["running", "waiting_input", "completed", "failed"]
    outputs: list[WorkflowRunOutput] = Field(default_factory=list)
    variables: dict[str, Any] = Field(default_factory=dict)
    current_node_id: Optional[str] = None
    steps_used: int = 0
    error: Optional[str] = None
