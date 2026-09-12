"""
Nuvora — Router /workflows
=============================
CRUD de workflows + endpoint /run para testing.

Reglas:
    - Autenticación JWT obligatoria.
    - Multi-tenant estricto: 401 sin auth, 403 bot/workflow de otro user, 404 inexistente.
    - Validación estática con WorkflowValidator ANTES de guardar.
    - Validación de condiciones con validate_condition_expression ANTES de guardar.
    - Los nodos y transiciones se guardan en tablas relacionadas.
    - El endpoint /run es solo para testing (no es el sistema productivo de ejecución).
"""

import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.db_models import Bot, User, Workflow, WorkflowNode, WorkflowTransition
from app.models.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowDetailResponse,
    WorkflowListResponse,
    WorkflowRunRequest,
    WorkflowRunResponse,
)
from app.services.auth import get_current_user
from app.core.workflows.validator import WorkflowValidator
from app.core.workflows.conditions import validate_condition_expression
from app.core.workflows.engine import WorkflowEngine
from app.core.workflows.errors import (
    WorkflowValidationError,
    WorkflowExecutionError,
    MaxStepsExceeded,
    ConditionError,
)


router = APIRouter(prefix="/workflows", tags=["workflows"])


# ============================================================
# HELPERS — Ownership y 404
# ============================================================

def _get_bot_or_404(db: Session, bot_id: int) -> Bot:
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")
    return bot


def _verify_bot_ownership(bot: Bot, current_user: User) -> None:
    if bot.user_id is not None:
        if bot.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para acceder a este bot",
            )
        return
    if bot.owner_email != current_user.email:
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para acceder a este bot",
        )


def _get_workflow_or_404(db: Session, bot_id: int, workflow_id: int) -> Workflow:
    wf = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.bot_id == bot_id,
    ).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow no encontrado")
    return wf


def _workflow_to_dict(wf: Workflow) -> dict:
    """Convierte Workflow SQLAlchemy (con nodes y transitions) al dict que espera el engine."""
    nodes = []
    for n in wf.nodes:
        config = None
        if n.config:
            try:
                config = json.loads(n.config)
            except (ValueError, TypeError):
                config = None
        nodes.append({
            "node_id": n.node_id,
            "type": n.type,
            "name": n.name,
            "config": config,
        })

    transitions = []
    for t in wf.transitions:
        transitions.append({
            "from_node_id": t.from_node_id,
            "to_node_id": t.to_node_id,
            "condition": t.condition,
            "label": t.label,
            "order": t.order or 0,
        })

    return {"nodes": nodes, "transitions": transitions}


def _validate_workflow_payload(payload: dict) -> None:
    try:
        WorkflowValidator().validate(payload)
    except WorkflowValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Workflow inválido: {e.errors}",
        )

    for t in payload.get("transitions") or []:
        cond = t.get("condition")
        if cond:
            try:
                validate_condition_expression(cond)
            except ConditionError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Condición inválida en transición: {e.message}",
                )


def _load_workflow_with_relations(db: Session, workflow_id: int) -> Workflow:
    """
    Recarga el workflow asegurando que nodes y transitions estén cargados.
    Necesario para que WorkflowDetailResponse se serialice bien.
    """
    from sqlalchemy.orm import selectinload
    return (
        db.query(Workflow)
        .options(selectinload(Workflow.nodes), selectinload(Workflow.transitions))
        .filter(Workflow.id == workflow_id)
        .first()
    )


# ============================================================
# ENDPOINTS CRUD
# ============================================================

@router.post("/{bot_id}", response_model=WorkflowDetailResponse)
def create_workflow(
    bot_id: int,
    data: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crea un workflow completo con nodos y transiciones."""
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)

    payload = {
        "nodes": [n.model_dump() for n in data.nodes],
        "transitions": [t.model_dump() for t in data.transitions],
    }
    _validate_workflow_payload(payload)

    wf = Workflow(
        bot_id=bot_id,
        name=data.name,
        description=data.description,
        status=data.status,
        version=1,
        trigger=data.trigger,
        entry_node_id=data.entry_node_id,
        meta=json.dumps(data.meta) if data.meta else None,
    )
    db.add(wf)
    db.flush()

    for n in data.nodes:
        db.add(WorkflowNode(
            workflow_id=wf.id,
            node_id=n.node_id,
            type=n.type,
            name=n.name,
            config=json.dumps(n.config) if n.config else None,
        ))

    for t in data.transitions:
        db.add(WorkflowTransition(
            workflow_id=wf.id,
            from_node_id=t.from_node_id,
            to_node_id=t.to_node_id,
            condition=t.condition,
            label=t.label,
            order=t.order,
        ))

    db.commit()

    # Recargar con relaciones cargadas
    wf = _load_workflow_with_relations(db, wf.id)
    return wf


@router.get("/{bot_id}", response_model=WorkflowListResponse)
def list_workflows(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)

    wfs = db.query(Workflow).filter(Workflow.bot_id == bot_id).all()
    return WorkflowListResponse(
        workflows=[WorkflowResponse.model_validate(w) for w in wfs],
        total=len(wfs),
    )


@router.get("/{bot_id}/{workflow_id}", response_model=WorkflowDetailResponse)
def get_workflow(
    bot_id: int,
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)
    _get_workflow_or_404(db, bot_id, workflow_id)
    wf = _load_workflow_with_relations(db, workflow_id)
    return wf


@router.put("/{bot_id}/{workflow_id}", response_model=WorkflowDetailResponse)
def update_workflow(
    bot_id: int,
    workflow_id: int,
    data: WorkflowUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)
    wf = _get_workflow_or_404(db, bot_id, workflow_id)

    update_data = data.model_dump(exclude_unset=True)

    if "meta" in update_data:
        update_data["meta"] = json.dumps(update_data["meta"]) if update_data["meta"] else None

    for field, value in update_data.items():
        if hasattr(wf, field):
            setattr(wf, field, value)

    db.commit()

    wf = _load_workflow_with_relations(db, workflow_id)
    return wf


@router.delete("/{bot_id}/{workflow_id}")
def delete_workflow(
    bot_id: int,
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)
    wf = _get_workflow_or_404(db, bot_id, workflow_id)

    db.delete(wf)
    db.commit()
    return {"detail": "Workflow eliminado", "id": workflow_id}


# ============================================================
# ENDPOINT /run — Ejecución manual (testing)
# ============================================================

@router.post("/{bot_id}/{workflow_id}/run", response_model=WorkflowRunResponse)
def run_workflow_endpoint(
    bot_id: int,
    workflow_id: int,
    data: WorkflowRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)
    _get_workflow_or_404(db, bot_id, workflow_id)

    wf = _load_workflow_with_relations(db, workflow_id)
    wf_dict = _workflow_to_dict(wf)

    engine = WorkflowEngine()
    try:
        result = engine.run(
            workflow_data=wf_dict,
            bot_id=bot_id,
            workflow_id=workflow_id,
            initial_variables=data.initial_variables,
            max_steps=data.max_steps,
        )
    except WorkflowValidationError as e:
        raise HTTPException(status_code=400, detail=f"Workflow inválido: {e.errors}")
    except MaxStepsExceeded as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConditionError as e:
        raise HTTPException(status_code=400, detail=f"Error en condición: {e.message}")
    except WorkflowExecutionError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return WorkflowRunResponse(
        status=result.status.value,
        outputs=result.outputs,
        variables=result.variables,
        current_node_id=result.current_node_id,
        steps_used=result.steps_used,
        error=result.error,
    )
