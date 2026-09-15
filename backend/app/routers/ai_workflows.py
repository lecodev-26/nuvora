"""
Nuvora — Router /ai/workflows + /ai/templates (Fase 14.7.7)
==============================================================
Expone el AIWorkflowDesigner vía HTTP.

Endpoints:
    POST   /ai/workflows/generate       → generar workflow desde prompt
    POST   /ai/workflows/modify         → modificar workflow existente
    POST   /ai/workflows/explain        → explicar workflow
    POST   /ai/workflows/analyze        → analizar workflow
    GET    /ai/templates                → listar plantillas (sin IA)
    POST   /ai/templates/{id}/instantiate → instanciar plantilla (sin IA)

Reglas:
    - Auth JWT obligatoria en todos los endpoints.
    - Mapeo de errores IA → HTTP status coherente.
    - No persiste nada en BD. Solo genera / valida.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.db_models import User
from app.models.ai import (
    GenerateWorkflowRequest,
    GenerateWorkflowResponse,
    ModifyWorkflowRequest,
    ModifyWorkflowResponse,
    ExplainWorkflowRequest,
    ExplainWorkflowResponse,
    AnalyzeWorkflowRequest,
    AnalyzeWorkflowResponse,
    TemplatesListResponse,
    InstantiateTemplateResponse,
)
from app.services.auth import get_current_user
from app.core.ai.designer import AIWorkflowDesigner
from app.core.ai.templates import list_templates, get_template_workflow
from app.core.ai.errors import (
    AIError,
    AIUnavailableError,
    AIProviderError,
    AIInvalidOutputError,
    AIConfigError,
)


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/ai", tags=["ai"])


# ============================================================
# HELPERS — mapeo de errores IA → HTTP
# ============================================================

def _handle_ai_error(e: Exception) -> HTTPException:
    """
    Convierte un error de IA en un HTTPException con status coherente.
    """
    if isinstance(e, AIUnavailableError):
        # Feature flag global deshabilitado
        return HTTPException(status_code=503, detail=str(e))
    if isinstance(e, AIProviderError):
        # Error del provider externo (red, 5xx, timeout)
        return HTTPException(
            status_code=502,
            detail=f"Error del proveedor de IA: {e.message}",
        )
    if isinstance(e, AIInvalidOutputError):
        # El provider devolvió algo que no cumple el schema/validator
        return HTTPException(
            status_code=422,
            detail=f"El workflow generado no es válido: {e.message}",
        )
    if isinstance(e, AIConfigError):
        # Configuración interna (provider inexistente, etc.)
        return HTTPException(
            status_code=500,
            detail=f"Error de configuración de IA: {e}",
        )
    if isinstance(e, AIError):
        # Cualquier otro AIError genérico
        return HTTPException(status_code=500, detail=f"Error de IA: {e}")
    # Error inesperado
    return HTTPException(status_code=500, detail="Error inesperado en la capa IA")


# ============================================================
# ENDPOINTS — WORKFLOWS
# ============================================================

@router.post("/workflows/generate", response_model=GenerateWorkflowResponse)
def generate_workflow(
    data: GenerateWorkflowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Genera un workflow desde una descripción en lenguaje natural.

    Retry automático hasta 2 veces si el JSON no pasa el validador.
    """
    try:
        designer = AIWorkflowDesigner(db=db, user_id=current_user.id)
        return designer.generate(
            prompt=data.prompt,
            bot_context=data.bot_context,
        )
    except Exception as e:
        logger.warning(f"[ai_workflows.generate] user={current_user.id}: {type(e).__name__}: {e}")
        raise _handle_ai_error(e)


@router.post("/workflows/modify", response_model=ModifyWorkflowResponse)
def modify_workflow(
    data: ModifyWorkflowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Modifica un workflow existente según una instrucción.
    Preserva los nodos/transiciones no afectados.
    """
    try:
        designer = AIWorkflowDesigner(db=db, user_id=current_user.id)
        return designer.modify(
            workflow=data.workflow,
            instruction=data.instruction,
        )
    except Exception as e:
        logger.warning(f"[ai_workflows.modify] user={current_user.id}: {type(e).__name__}: {e}")
        raise _handle_ai_error(e)


@router.post("/workflows/explain", response_model=ExplainWorkflowResponse)
def explain_workflow(
    data: ExplainWorkflowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Explica un workflow en lenguaje humano.
    """
    try:
        designer = AIWorkflowDesigner(db=db, user_id=current_user.id)
        return designer.explain(workflow=data.workflow)
    except Exception as e:
        logger.warning(f"[ai_workflows.explain] user={current_user.id}: {type(e).__name__}: {e}")
        raise _handle_ai_error(e)


@router.post("/workflows/analyze", response_model=AnalyzeWorkflowResponse)
def analyze_workflow(
    data: AnalyzeWorkflowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Analiza un workflow: warnings + sugerencias de mejora.

    NOTA: el análisis es informativo, no autoritativo. El validador
    estructural real (14.5.4) se ejecuta por separado al guardar.
    """
    try:
        designer = AIWorkflowDesigner(db=db, user_id=current_user.id)
        return designer.analyze(workflow=data.workflow)
    except Exception as e:
        logger.warning(f"[ai_workflows.analyze] user={current_user.id}: {type(e).__name__}: {e}")
        raise _handle_ai_error(e)


# ============================================================
# ENDPOINTS — TEMPLATES (sin IA)
# ============================================================

@router.get("/templates", response_model=TemplatesListResponse)
def get_templates(
    current_user: User = Depends(get_current_user),
):
    """
    Lista las plantillas de workflows predefinidas.

    NO usa IA. Es instantáneo y gratis.
    """
    return TemplatesListResponse(templates=list_templates())


@router.post("/templates/{template_id}/instantiate", response_model=InstantiateTemplateResponse)
def instantiate_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Devuelve el workflow de una plantilla concreta.

    NO usa IA. El usuario puede importarlo directamente en el Builder.
    """
    workflow = get_template_workflow(template_id)
    if not workflow:
        raise HTTPException(
            status_code=404,
            detail=f"Plantilla '{template_id}' no encontrada",
        )
    return InstantiateTemplateResponse(
        workflow=workflow,
        template_id=template_id,
    )
