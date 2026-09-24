"""
Nuvora - Workflow Validator Service (Fase 14.12.3)
====================================================
Servicio común para consultar y validar workflows.

FILOSOFÍA:
    - Reutiliza la autoridad existente (WorkflowValidator 14.5.4).
    - NO introduce una segunda validación paralela.
    - Es una capa fina de conveniencia para Creator Mode.

REUTILIZABLE POR:
    - creator_status_service (14.12)
    - Futuras fases que necesiten validar workflows sin HTTP

NO TOCA:
    - publication.py (mantiene su lógica actual)
    - public_resolver.py (mantiene su lógica actual)
"""

import json
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.db_models import Workflow
from app.core.workflows.validator import WorkflowValidator
from app.core.workflows.errors import WorkflowValidationError


logger = logging.getLogger(__name__)


# ============================================================
# WORKFLOW ACTIVO
# ============================================================

def get_active_workflow_or_none(db: Session, bot_id: int) -> Optional[Workflow]:
    """
    Devuelve el workflow activo del bot si hay EXACTAMENTE 1.

    Returns:
        Workflow si hay exactamente 1 con status="active".
        None si hay 0 o si hay 2+ (estado inconsistente).
    """
    actives = db.query(Workflow).filter(
        Workflow.bot_id == bot_id,
        Workflow.status == "active",
    ).all()

    if len(actives) != 1:
        return None
    return actives[0]


# ============================================================
# PARSEO
# ============================================================

def parse_workflow_to_dict(wf: Workflow) -> dict:
    """
    Convierte un Workflow SQLAlchemy a dict para el WorkflowValidator.

    Mismo formato que usa publication.py / public_resolver.py.
    """
    nodes = []
    for n in wf.nodes:
        cfg = None
        if n.config:
            try:
                cfg = json.loads(n.config)
            except (ValueError, TypeError):
                cfg = None
        nodes.append({
            "node_id": n.node_id,
            "type": n.type,
            "name": n.name,
            "config": cfg,
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


# ============================================================
# VALIDACIÓN
# ============================================================

def is_workflow_valid(wf: Workflow) -> tuple[bool, list[str]]:
    """
    Valida estructuralmente un workflow usando la autoridad existente
    (WorkflowValidator 14.5.4).

    Returns:
        (True, []) si el workflow es válido.
        (False, [errores]) si es inválido.

    NO levanta excepción. Siempre devuelve tupla.
    """
    payload = parse_workflow_to_dict(wf)
    try:
        WorkflowValidator().validate(payload)
        return (True, [])
    except WorkflowValidationError as e:
        errors = getattr(e, "errors", []) or [str(e)]
        return (False, errors)
    except Exception as e:
        logger.warning("is_workflow_valid: error inesperado: %s", e)
        return (False, [f"Error de validación: {e}"])


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "get_active_workflow_or_none",
    "parse_workflow_to_dict",
    "is_workflow_valid",
]
