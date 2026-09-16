"""
Nuvora — Router /bots/{bot_id}/tests (Fase 14.8.7)
=====================================================
Bot Tester: CRUD de tests + ejecución + análisis.

REGLAS:
    - Auth JWT obligatoria.
    - Multi-tenant estricto (401 / 403 / 404).
    - Solo el dueño del bot puede gestionar sus tests.
    - Los tests NO modifican el workflow.
    - El Runner reutiliza WorkflowEngine (14.5) sin duplicar lógica.
    - Los resultados de ejecución son TEMPORALES (no se guardan).

Endpoints:
    POST   /bots/{bot_id}/tests                    → crear
    GET    /bots/{bot_id}/tests                    → listar
    GET    /bots/{bot_id}/tests/{test_id}          → ver
    PUT    /bots/{bot_id}/tests/{test_id}          → actualizar
    DELETE /bots/{bot_id}/tests/{test_id}          → borrar
    POST   /bots/{bot_id}/tests/{test_id}/run      → ejecutar 1
    POST   /bots/{bot_id}/tests/run-all            → ejecutar todos
    POST   /bots/{bot_id}/tests/analyze            → static analysis
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.db_models import Bot, User, Workflow, WorkflowTest
from app.models.test import (
    TestCaseCreate,
    TestCaseUpdate,
    TestCaseResponse,
    TestListResponse,
    TestRunResult,
    TestRunAllResult,
    AnalyzeResponse,
    TestAssertion,
    GenerateAITestsResponse,
    GenerateBasicTestsResponse,
)
from app.services.auth import get_current_user
from app.core.testing import (
    TestRunner,
    WorkflowAnalyzer,
    AITestGenerator,
    BasicTestGenerator,
    TestNotFoundError,
    TestLimitExceededError,
)
from app.core.ai.rate_limit import check_rate_limit, RateLimitExceeded
from app.config import settings


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/bots", tags=["tests"])


# ============================================================
# HELPERS
# ============================================================

def _get_bot_or_404(db: Session, bot_id: int) -> Bot:
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")
    return bot


def _verify_bot_ownership(bot: Bot, current_user: User) -> None:
    if bot.user_id is not None:
        if bot.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="No tienes permiso para acceder a este bot")
        return
    if bot.owner_email != current_user.email:
        raise HTTPException(status_code=403, detail="No tienes permiso para acceder a este bot")


def _check_test_rate(user_id: int, bucket: str, limit: int) -> None:
    """Aplica rate limiting y convierte RateLimitExceeded en HTTP 429."""
    try:
        check_rate_limit(user_id=user_id, bucket=bucket, max_per_hour=limit)
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Has superado el límite de {e.limit} peticiones por hora "
                f"para esta operación. Reintenta en {e.retry_after} segundos."
            ),
            headers={"Retry-After": str(e.retry_after)},
        )


def _get_test_or_404(db: Session, bot_id: int, test_id: int) -> WorkflowTest:
    t = (
        db.query(WorkflowTest)
        .filter(WorkflowTest.id == test_id, WorkflowTest.bot_id == bot_id)
        .first()
    )
    if not t:
        raise HTTPException(status_code=404, detail="Test no encontrado")
    return t


def _get_workflow_of_bot(db: Session, bot_id: int, workflow_id: int) -> Workflow:
    wf = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.bot_id == bot_id,
    ).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow no encontrado")
    return wf


def _load_workflow_with_relations(db: Session, workflow_id: int) -> Workflow:
    from sqlalchemy.orm import selectinload
    return (
        db.query(Workflow)
        .options(selectinload(Workflow.nodes), selectinload(Workflow.transitions))
        .filter(Workflow.id == workflow_id)
        .first()
    )


def _workflow_to_dict(wf: Workflow) -> dict:
    """Convierte Workflow SQLAlchemy al dict que espera el engine."""
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


def _serialize_assertions(assertions: list[TestAssertion]) -> str:
    return json.dumps([a.model_dump() for a in assertions])


def _deserialize_assertions(raw: str | None) -> list[TestAssertion]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return [TestAssertion(**a) for a in data]
    except Exception:
        return []


def _deserialize_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _deserialize_dict(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _test_to_response(t: WorkflowTest) -> TestCaseResponse:
    return TestCaseResponse(
        id=t.id,
        workflow_id=t.workflow_id,
        bot_id=t.bot_id,
        name=t.name,
        description=t.description,
        input_messages=_deserialize_list(t.input_messages),
        initial_variables=_deserialize_dict(t.initial_vars),
        assertions=_deserialize_assertions(t.assertions),
        enabled=t.enabled,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


def _test_to_case_create(t: WorkflowTest) -> TestCaseCreate:
    """Convierte un WorkflowTest guardado en TestCaseCreate (para el Runner)."""
    return TestCaseCreate(
        name=t.name,
        description=t.description,
        input_messages=_deserialize_list(t.input_messages),
        initial_variables=_deserialize_dict(t.initial_vars),
        assertions=_deserialize_assertions(t.assertions),
        enabled=t.enabled,
    )


# ============================================================
# CRUD
# ============================================================

@router.post(
    "/{bot_id}/tests",
    response_model=TestCaseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_test(
    bot_id: int,
    data: TestCaseCreate,
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Crea un test para un workflow del bot.

    Query params:
        workflow_id: el workflow al que pertenece el test.
    """
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)
    _get_workflow_of_bot(db, bot_id, workflow_id)  # valida 404

    wt = WorkflowTest(
        workflow_id=workflow_id,
        bot_id=bot_id,
        name=data.name,
        description=data.description,
        input_messages=json.dumps(data.input_messages),
        initial_vars=json.dumps(data.initial_variables) if data.initial_variables else None,
        assertions=_serialize_assertions(data.assertions),
        enabled=data.enabled,
    )
    db.add(wt)
    db.commit()
    db.refresh(wt)
    return _test_to_response(wt)


@router.get("/{bot_id}/tests", response_model=TestListResponse)
def list_tests(
    bot_id: int,
    workflow_id: int | None = None,
    enabled_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista los tests del bot (opcionalmente filtrando por workflow)."""
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)

    q = db.query(WorkflowTest).filter(WorkflowTest.bot_id == bot_id)
    if workflow_id is not None:
        q = q.filter(WorkflowTest.workflow_id == workflow_id)
    if enabled_only:
        q = q.filter(WorkflowTest.enabled == True)

    tests = q.order_by(WorkflowTest.id).all()
    return TestListResponse(
        tests=[_test_to_response(t) for t in tests],
        total=len(tests),
    )


@router.get("/{bot_id}/tests/{test_id}", response_model=TestCaseResponse)
def get_test(
    bot_id: int,
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)
    t = _get_test_or_404(db, bot_id, test_id)
    return _test_to_response(t)


@router.put("/{bot_id}/tests/{test_id}", response_model=TestCaseResponse)
def update_test(
    bot_id: int,
    test_id: int,
    data: TestCaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)
    t = _get_test_or_404(db, bot_id, test_id)

    update_data = data.model_dump(exclude_unset=True)

    if "name" in update_data:
        t.name = update_data["name"]
    if "description" in update_data:
        t.description = update_data["description"]
    if "input_messages" in update_data:
        t.input_messages = json.dumps(update_data["input_messages"])
    if "initial_variables" in update_data:
        t.initial_vars = json.dumps(update_data["initial_variables"]) if update_data["initial_variables"] else None
    if "assertions" in update_data:
        t.assertions = json.dumps([a.model_dump() for a in data.assertions])
    if "enabled" in update_data:
        t.enabled = update_data["enabled"]

    db.commit()
    db.refresh(t)
    return _test_to_response(t)


@router.delete("/{bot_id}/tests/{test_id}")
def delete_test(
    bot_id: int,
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)
    t = _get_test_or_404(db, bot_id, test_id)

    db.delete(t)
    db.commit()
    return {"detail": "Test eliminado", "id": test_id}


# ============================================================
# EJECUCIÓN
# ============================================================

@router.post("/{bot_id}/tests/{test_id}/run", response_model=TestRunResult)
def run_test(
    bot_id: int,
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ejecuta un test individual."""
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)

    _check_test_rate(
        user_id=current_user.id,
        bucket="test_run",
        limit=settings.tests.rate_limit_test_run,
    )

    t = _get_test_or_404(db, bot_id, test_id)

    wf = _load_workflow_with_relations(db, t.workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow del test no encontrado")

    wf_dict = _workflow_to_dict(wf)
    runner = TestRunner(workflow_data=wf_dict, bot_id=bot_id)

    try:
        result = runner.run_test(_test_to_case_create(t))
    except TestNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Rellenar test_id/nombre en el resultado
    result.test_id = t.id
    result.test_name = t.name
    return result


@router.post("/{bot_id}/tests/run-all", response_model=TestRunAllResult)
def run_all_tests(
    bot_id: int,
    workflow_id: int,
    enabled_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Ejecuta todos los tests de un workflow.

    Query params:
        workflow_id: workflow a testear (obligatorio).
        enabled_only: si True (default), solo tests enabled.
    """
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)

    _check_test_rate(
        user_id=current_user.id,
        bucket="test_run_all",
        limit=settings.tests.rate_limit_test_run_all,
    )

    _get_workflow_of_bot(db, bot_id, workflow_id)

    q = db.query(WorkflowTest).filter(
        WorkflowTest.bot_id == bot_id,
        WorkflowTest.workflow_id == workflow_id,
    )
    if enabled_only:
        q = q.filter(WorkflowTest.enabled == True)
    tests = q.order_by(WorkflowTest.id).all()

    wf = _load_workflow_with_relations(db, workflow_id)
    wf_dict = _workflow_to_dict(wf)
    runner = TestRunner(workflow_data=wf_dict, bot_id=bot_id)

    test_cases = [_test_to_case_create(t) for t in tests]
    result = runner.run_all(test_cases)

    # Rellenar info por test
    result.workflow_id = workflow_id
    for i, r in enumerate(result.results):
        if i < len(tests):
            r.test_id = tests[i].id
            r.test_name = tests[i].name

    return result


# ============================================================
# ANÁLISIS
# ============================================================

@router.post("/{bot_id}/tests/analyze", response_model=AnalyzeResponse)
def analyze_workflow(
    bot_id: int,
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Análisis estático del workflow (no ejecuta nada).

    Query params:
        workflow_id: workflow a analizar.
    """
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)

    _check_test_rate(
        user_id=current_user.id,
        bucket="test_analyze",
        limit=settings.tests.rate_limit_test_analyze,
    )

    _get_workflow_of_bot(db, bot_id, workflow_id)

    wf = _load_workflow_with_relations(db, workflow_id)
    wf_dict = _workflow_to_dict(wf)

    analyzer = WorkflowAnalyzer(wf_dict)
    response = analyzer.analyze()
    response.workflow_id = workflow_id
    return response


# ============================================================
# AI TEST GENERATOR (14.8.12)
# ============================================================

@router.post("/{bot_id}/tests/generate", response_model=GenerateAITestsResponse)
def generate_tests_with_ai(
    bot_id: int,
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Genera DEFINICIONES de tests usando IA (reutiliza 14.7).

    La IA NO ejecuta workflows. Solo genera JSON de tests.
    El usuario decide si los guarda.

    Query params:
        workflow_id: workflow sobre el que generar tests.
    """
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)

    # Reutilizamos el bucket 'test_analyze' (operación ligera, 100/h)
    _check_test_rate(
        user_id=current_user.id,
        bucket="test_analyze",
        limit=settings.tests.rate_limit_test_analyze,
    )

    _get_workflow_of_bot(db, bot_id, workflow_id)

    wf = _load_workflow_with_relations(db, workflow_id)
    wf_dict = _workflow_to_dict(wf)

    try:
        generator = AITestGenerator(db=db, user_id=current_user.id)
        result = generator.generate(workflow_data=wf_dict)
        return result
    except Exception as e:
        logger.warning(
            f"[tests.generate] user={current_user.id}: {type(e).__name__}: {e}"
        )
        # Reutilizamos el mapeo de errores del router de IA
        from app.routers.ai_workflows import _handle_ai_error
        try:
            raise _handle_ai_error(e)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=500,
                detail=f"Error generando tests con IA: {type(e).__name__}",
            )


# ============================================================
# BASIC TEST GENERATOR (14.8.13) — SIN IA
# ============================================================

@router.post(
    "/{bot_id}/tests/generate-basic",
    response_model=GenerateBasicTestsResponse,
)
def generate_basic_tests(
    bot_id: int,
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Genera DEFINICIONES de tests básicos (100% determinista, SIN IA).

    Tipos de tests generados:
        1. Happy path (reaches_end)
        2. Nodo visitado (hasta 5 nodos)
        3. No excede MAX_STEPS
        4. Sin 'error' en output (si hay message/response)

    NO usa IA. NO gasta tokens. NO llama a ningún provider.
    NO guarda en BD. El usuario decide si guardarlos.

    Query params:
        workflow_id: workflow sobre el que generar tests.
    """
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)

    # Rate limit ligero (mismo bucket que analyze, 100/h)
    _check_test_rate(
        user_id=current_user.id,
        bucket="test_analyze",
        limit=settings.tests.rate_limit_test_analyze,
    )

    _get_workflow_of_bot(db, bot_id, workflow_id)

    wf = _load_workflow_with_relations(db, workflow_id)
    wf_dict = _workflow_to_dict(wf)

    generator = BasicTestGenerator()
    return generator.generate(workflow_data=wf_dict)
