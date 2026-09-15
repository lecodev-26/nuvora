"""
Nuvora — Router /ai/workflows + /ai/templates (Fase 14.7.7 + 14.7.13)
========================================================================
Expone el AIWorkflowDesigner vía HTTP con rate limiting.

Endpoints:
    POST   /ai/workflows/generate       → generar workflow desde prompt
    POST   /ai/workflows/modify         → modificar workflow existente
    POST   /ai/workflows/explain        → explicar workflow
    POST   /ai/workflows/analyze        → analizar workflow
    GET    /ai/templates                → listar plantillas (sin IA)
    POST   /ai/templates/{id}/instantiate → instanciar plantilla (sin IA)

Reglas:
    - Auth JWT obligatoria en todos los endpoints.
    - Rate limiting por usuario y endpoint (14.7.13).
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
from app.core.ai.rate_limit import check_rate_limit, RateLimitExceeded
from app.config import settings


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
        return HTTPException(status_code=503, detail=str(e))
    if isinstance(e, AIProviderError):
        return HTTPException(
            status_code=502,
            detail=f"Error del proveedor de IA: {e.message}",
        )
    if isinstance(e, AIInvalidOutputError):
        return HTTPException(
            status_code=422,
            detail=f"El workflow generado no es válido: {e.message}",
        )
    if isinstance(e, AIConfigError):
        return HTTPException(
            status_code=500,
            detail=f"Error de configuración de IA: {e}",
        )
    if isinstance(e, AIError):
        return HTTPException(status_code=500, detail=f"Error de IA: {e}")
    return HTTPException(status_code=500, detail="Error inesperado en la capa IA")


def _handle_rate_limit(e: RateLimitExceeded) -> HTTPException:
    """Convierte RateLimitExceeded en HTTPException 429 con Retry-After."""
    return HTTPException(
        status_code=429,
        detail=(
            f"Has superado el límite de {e.limit} peticiones por hora "
            f"para esta operación. Reintenta en {e.retry_after} segundos."
        ),
        headers={"Retry-After": str(e.retry_after)},
    )


def _check_rate(user_id: int, bucket: str, limit: int) -> None:
    """
    Envuelve check_rate_limit convirtiendo la excepción en HTTPException.
    """
    try:
        check_rate_limit(user_id=user_id, bucket=bucket, max_per_hour=limit)
    except RateLimitExceeded as e:
        raise _handle_rate_limit(e)


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
    Rate limit: AI_RATE_LIMIT_GENERATE (default 10/hora).
    """
    # 1. Rate limit ANTES de llamar al provider
    _check_rate(
        user_id=current_user.id,
        bucket="generate",
        limit=settings.ai.rate_limit_generate,
    )

    # 2. Ejecutar designer
    try:
        designer = AIWorkflowDesigner(db=db, user_id=current_user.id)
        return designer.generate(
            prompt=data.prompt,
            bot_context=data.bot_context,
        )
    except Exception as e:
        logger.warning(
            f"[ai_workflows.generate] user={current_user.id}: "
            f"{type(e).__name__}: {e}"
        )
        raise _handle_ai_error(e)


@router.post("/workflows/modify", response_model=ModifyWorkflowResponse)
def modify_workflow(
    data: ModifyWorkflowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Modifica un workflow existente según una instrucción.
    Rate limit: AI_RATE_LIMIT_MODIFY (default 20/hora).
    """
    _check_rate(
        user_id=current_user.id,
        bucket="modify",
        limit=settings.ai.rate_limit_modify,
    )

    try:
        designer = AIWorkflowDesigner(db=db, user_id=current_user.id)
        return designer.modify(
            workflow=data.workflow,
            instruction=data.instruction,
        )
    except Exception as e:
        logger.warning(
            f"[ai_workflows.modify] user={current_user.id}: "
            f"{type(e).__name__}: {e}"
        )
        raise _handle_ai_error(e)


@router.post("/workflows/explain", response_model=ExplainWorkflowResponse)
def explain_workflow(
    data: ExplainWorkflowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Explica un workflow en lenguaje humano.
    Rate limit: AI_RATE_LIMIT_EXPLAIN (default 30/hora).
    """
    _check_rate(
        user_id=current_user.id,
        bucket="explain",
        limit=settings.ai.rate_limit_explain,
    )

    try:
        designer = AIWorkflowDesigner(db=db, user_id=current_user.id)
        return designer.explain(workflow=data.workflow)
    except Exception as e:
        logger.warning(
            f"[ai_workflows.explain] user={current_user.id}: "
            f"{type(e).__name__}: {e}"
        )
        raise _handle_ai_error(e)


@router.post("/workflows/analyze", response_model=AnalyzeWorkflowResponse)
def analyze_workflow(
    data: AnalyzeWorkflowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Analiza un workflow: warnings + sugerencias de mejora.
    Rate limit: AI_RATE_LIMIT_ANALYZE (default 30/hora).
    """
    _check_rate(
        user_id=current_user.id,
        bucket="analyze",
        limit=settings.ai.rate_limit_analyze,
    )

    try:
        designer = AIWorkflowDesigner(db=db, user_id=current_user.id)
        return designer.analyze(workflow=data.workflow)
    except Exception as e:
        logger.warning(
            f"[ai_workflows.analyze] user={current_user.id}: "
            f"{type(e).__name__}: {e}"
        )
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
    Rate limit: AI_RATE_LIMIT_TEMPLATES_LIST (default 100/hora).
    """
    _check_rate(
        user_id=current_user.id,
        bucket="templates_list",
        limit=settings.ai.rate_limit_templates_list,
    )
    return TemplatesListResponse(templates=list_templates())


@router.post("/templates/{template_id}/instantiate", response_model=InstantiateTemplateResponse)
def instantiate_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Devuelve el workflow de una plantilla concreta.
    NO usa IA. El usuario puede importarlo directamente en el Builder.
    Rate limit: AI_RATE_LIMIT_TEMPLATES_INSTANTIATE (default 50/hora).
    """
    _check_rate(
        user_id=current_user.id,
        bucket="templates_instantiate",
        limit=settings.ai.rate_limit_templates_instantiate,
    )

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
