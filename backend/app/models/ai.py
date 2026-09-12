"""
Nuvora — Schemas Pydantic para la capa IA (Fase 14.7)
======================================================
Contratos HTTP de entrada/salida para el AI Workflow Designer.

REGLAS:
    - Reutiliza WorkflowNodeCreate / WorkflowTransitionCreate de 14.5.2.
    - El bot_context está MUY limitado para evitar token explosion.
    - Estos schemas NO contienen lógica de IA. Solo definen la forma.

FILOSOFÍA:
    La IA genera JSON estructurado. El WorkflowValidator (14.5.4)
    sigue siendo la autoridad estructural. Estos schemas solo
    definen el contrato HTTP del router /ai/*.
"""

from pydantic import BaseModel, Field
from typing import Optional

from app.models.workflow import (
    WorkflowNodeCreate,
    WorkflowTransitionCreate,
)


# ============================================================
# BOT CONTEXT (limitado)
# ============================================================

class BotContext(BaseModel):
    """
    Contexto opcional del bot para personalizar la generación.

    IMPORTANTE: NO incluye conocimiento, memoria, documentos ni
    conversaciones. Solo metadatos ligeros. Esto evita que la IA
    reciba "todo el bot" y dispare tokens/coste.

    Límites duros:
        - Máx 5 campos
        - Cada valor máx 500 chars
    """
    bot_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    business_type: Optional[str] = Field(None, max_length=100)
    language: str = Field("es", max_length=10)
    tone: Optional[str] = Field(None, max_length=50)


# ============================================================
# WORKFLOW GENERADO
# ============================================================

class GeneratedWorkflow(BaseModel):
    """
    Workflow generado por la IA.
    Estructura idéntica a lo que acepta el Builder (14.6).
    """
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    nodes: list[WorkflowNodeCreate] = Field(default_factory=list)
    transitions: list[WorkflowTransitionCreate] = Field(default_factory=list)


# ============================================================
# GENERATE
# ============================================================

class GenerateWorkflowRequest(BaseModel):
    """Petición de generación desde lenguaje natural."""
    prompt: str = Field(..., min_length=10, max_length=2000)
    bot_context: Optional[BotContext] = None


class GenerateWorkflowResponse(BaseModel):
    """Respuesta con el workflow generado + explicación."""
    workflow: GeneratedWorkflow
    explanation: str = Field(..., max_length=2000)
    warnings: list[str] = Field(default_factory=list)
    provider_used: str
    tokens_used: Optional[int] = None


# ============================================================
# MODIFY
# ============================================================

class ModifyWorkflowRequest(BaseModel):
    """Petición de modificación de un workflow existente."""
    workflow: GeneratedWorkflow
    instruction: str = Field(..., min_length=5, max_length=1000)


class ModifyWorkflowResponse(BaseModel):
    """Respuesta con el workflow modificado + explicación del cambio."""
    workflow: GeneratedWorkflow
    explanation: str = Field(..., max_length=2000)
    warnings: list[str] = Field(default_factory=list)
    provider_used: str
    tokens_used: Optional[int] = None


# ============================================================
# EXPLAIN
# ============================================================

class ExplainWorkflowRequest(BaseModel):
    """Petición de explicación de un workflow."""
    workflow: GeneratedWorkflow


class ExplainWorkflowResponse(BaseModel):
    """Explicación en lenguaje natural."""
    explanation: str = Field(..., max_length=4000)
    provider_used: str


# ============================================================
# ANALYZE
# ============================================================

class AnalyzeWorkflowRequest(BaseModel):
    """Petición de análisis de un workflow."""
    workflow: GeneratedWorkflow


class AnalyzeWorkflowResponse(BaseModel):
    """Análisis con warnings + sugerencias."""
    warnings: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    provider_used: str


# ============================================================
# TEMPLATES (sin IA)
# ============================================================

class TemplateInfo(BaseModel):
    """Metadatos de una plantilla."""
    id: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    icon: str = Field("📋", max_length=10)


class TemplatesListResponse(BaseModel):
    """Lista de plantillas disponibles."""
    templates: list[TemplateInfo]


class InstantiateTemplateResponse(BaseModel):
    """Workflow generado desde una plantilla (sin IA)."""
    workflow: GeneratedWorkflow
    template_id: str


__all__ = [
    "BotContext",
    "GeneratedWorkflow",
    "GenerateWorkflowRequest",
    "GenerateWorkflowResponse",
    "ModifyWorkflowRequest",
    "ModifyWorkflowResponse",
    "ExplainWorkflowRequest",
    "ExplainWorkflowResponse",
    "AnalyzeWorkflowRequest",
    "AnalyzeWorkflowResponse",
    "TemplateInfo",
    "TemplatesListResponse",
    "InstantiateTemplateResponse",
]
