"""
Nuvora — Schemas Pydantic para Bot Tester (Fase 14.8)
=======================================================
Contratos HTTP de entrada/salida del Bot Tester.

FILOSOFÍA:
    - El Tester NO ejecuta workflows. Llama al WorkflowEngine (14.5).
    - Los tests se guardan como definiciones (persistencia en BD).
    - Los resultados de ejecución son TEMPORALES (no se guardan).
    - Reutiliza los schemas de 14.5 (NodeType, WorkflowNodeCreate, etc.)
      cuando aporta valor.

ESTADOS DE TEST:
    - PASSED   → todas las assertions pasaron
    - FAILED   → workflow OK pero alguna assertion falló
    - ERROR    → error técnico al ejecutar/evaluar
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from typing import Optional, Any, Literal


# ============================================================
# TIPOS LITERALES
# ============================================================

TestStatus = Literal["passed", "failed", "error"]

AssertionType = Literal[
    "response_contains",
    "response_equals",
    "response_not_contains",
    "node_visited",
    "node_not_visited",
    "variable_equals",
    "variable_exists",
    "variable_not_exists",
    "reaches_end",
    "max_steps",
]


# ============================================================
# ASSERTION
# ============================================================

class TestAssertion(BaseModel):
    """
    Una assertion individual.

    Campos según tipo:
        - response_contains / response_equals / response_not_contains → `value`
        - node_visited / node_not_visited                             → `node_id`
        - variable_equals                                            → `variable` + `expected`
        - variable_exists / variable_not_exists                      → `variable`
        - reaches_end                                                → (sin campos)
        - max_steps                                                  → `max_steps`
    """
    type: AssertionType

    # Campo polivalente: value, node_id, variable, expected, max_steps
    value: Optional[str] = Field(None, max_length=500)
    node_id: Optional[str] = Field(None, max_length=50)
    variable: Optional[str] = Field(None, max_length=50)
    expected: Optional[Any] = None
    max_steps: Optional[int] = Field(None, ge=1, le=1000)

    @model_validator(mode="after")
    def _validate_required_fields(self):
        """Valida que cada tipo de assertion tenga los campos necesarios."""
        t = self.type

        if t in ("response_contains", "response_equals", "response_not_contains"):
            if not self.value:
                raise ValueError(f"'{t}' requiere 'value'")

        elif t in ("node_visited", "node_not_visited"):
            if not self.node_id:
                raise ValueError(f"'{t}' requiere 'node_id'")

        elif t == "variable_equals":
            if not self.variable:
                raise ValueError("'variable_equals' requiere 'variable'")
            if self.expected is None:
                raise ValueError("'variable_equals' requiere 'expected'")

        elif t in ("variable_exists", "variable_not_exists"):
            if not self.variable:
                raise ValueError(f"'{t}' requiere 'variable'")

        elif t == "max_steps":
            if self.max_steps is None:
                raise ValueError("'max_steps' requiere 'max_steps'")

        # 'reaches_end' no requiere nada

        return self


# ============================================================
# TEST CASE (definición)
# ============================================================

class TestCaseCreate(BaseModel):
    """Crear un test nuevo."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)

    input_messages: list[str] = Field(..., min_length=1, max_length=20)
    initial_variables: dict[str, Any] = Field(default_factory=dict)
    assertions: list[TestAssertion] = Field(..., min_length=1, max_length=30)

    enabled: bool = True

    @field_validator("input_messages")
    @classmethod
    def _validate_messages(cls, v):
        if not v:
            raise ValueError("input_messages no puede estar vacío")
        for msg in v:
            if not msg or not msg.strip():
                raise ValueError("input_messages no puede contener strings vacíos")
            if len(msg) > 1000:
                raise ValueError("Cada mensaje debe tener max 1000 chars")
        return v

    @field_validator("initial_variables")
    @classmethod
    def _validate_variables(cls, v):
        if len(v) > 50:
            raise ValueError("Máximo 50 variables iniciales")
        return v


class TestCaseUpdate(BaseModel):
    """Actualización parcial de un test."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    input_messages: Optional[list[str]] = Field(None, min_length=1, max_length=20)
    initial_variables: Optional[dict[str, Any]] = None
    assertions: Optional[list[TestAssertion]] = Field(None, min_length=1, max_length=30)
    enabled: Optional[bool] = None


class TestCaseResponse(BaseModel):
    """Respuesta con datos de un test (definición)."""
    id: int
    workflow_id: int
    bot_id: int
    name: str
    description: Optional[str] = None
    input_messages: list[str]
    initial_variables: dict[str, Any]
    assertions: list[TestAssertion]
    enabled: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class TestListResponse(BaseModel):
    """Lista de tests de un workflow."""
    tests: list[TestCaseResponse]
    total: int


# ============================================================
# EJECUCIÓN
# ============================================================

class TestRunRequest(BaseModel):
    """
    Petición de ejecución de un test guardado.
    (No suele necesitar body, pero dejamos opciones por si acaso.)
    """
    # Placeholder para futuras opciones (por ejemplo, overrides de variables)
    override_variables: Optional[dict[str, Any]] = None


class TestAdHocRunRequest(BaseModel):
    """
    Ejecución de un test SIN guardarlo en BD.
    Útil para el Builder (botón 'Run test' con input manual).
    """
    input_messages: list[str] = Field(..., min_length=1, max_length=20)
    initial_variables: dict[str, Any] = Field(default_factory=dict)
    assertions: list[TestAssertion] = Field(default_factory=list, max_length=30)


class AssertionResult(BaseModel):
    """Resultado de una assertion individual."""
    type: AssertionType
    passed: bool
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    message: Optional[str] = None


class TestStepTrace(BaseModel):
    """Un paso del trace de ejecución."""
    step: int
    node_id: str
    type: str
    output: Optional[str] = None


class TestRunResult(BaseModel):
    """
    Resultado de ejecutar un test.

    Estados:
        - passed   → todas las assertions pasaron
        - failed   → workflow OK pero alguna assertion falló
        - error    → error técnico al ejecutar/evaluar
    """
    test_id: Optional[int] = None       # None para tests ad-hoc
    test_name: Optional[str] = None
    status: TestStatus

    duration_ms: int = 0
    steps_used: int = 0

    # Trace de ejecución (reutiliza history de ExecutionResult)
    nodes_visited: list[str] = Field(default_factory=list)
    trace: list[TestStepTrace] = Field(default_factory=list)

    # Outputs del workflow (respuestas generadas)
    responses: list[str] = Field(default_factory=list)

    # Variables finales
    variables: dict[str, Any] = Field(default_factory=dict)

    # Resultado del workflow
    workflow_status: Optional[str] = None  # 'completed', 'waiting_input', 'failed'

    # Assertions
    assertions_passed: int = 0
    assertions_failed: int = 0
    assertion_results: list[AssertionResult] = Field(default_factory=list)

    # Error técnico (solo si status='error')
    error: Optional[str] = None


class TestRunAllResult(BaseModel):
    """Resultado de ejecutar todos los tests de un workflow."""
    workflow_id: int
    total: int
    passed: int
    failed: int
    errors: int
    duration_ms: int
    results: list[TestRunResult] = Field(default_factory=list)


# ============================================================
# ANÁLISIS ESTRUCTURAL
# ============================================================

class StructuralIssue(BaseModel):
    """Un problema detectado por el análisis estructural."""
    severity: Literal["info", "warning", "error"]
    code: str           # 'orphan_node', 'multiple_start', etc.
    message: str
    node_id: Optional[str] = None
    edge_key: Optional[str] = None


class AnalyzeResponse(BaseModel):
    """Resultado del análisis estructural del workflow."""
    workflow_id: int
    issues: list[StructuralIssue] = Field(default_factory=list)
    summary: dict[str, int] = Field(default_factory=dict)  # {'error': N, 'warning': M, ...}


# ============================================================
# GENERACIÓN AUTOMÁTICA (sin IA)
# ============================================================

class GenerateBasicTestsResponse(BaseModel):
    """
    Resultado de generar tests básicos SIN IA.

    Devuelve las definiciones generadas + un resumen.
    El usuario decide si las guarda.
    """
    generated: list[TestCaseCreate]
    count: int
    notes: list[str] = Field(default_factory=list)


# ============================================================
# GENERACIÓN CON IA (14.8.13)
# ============================================================

class GenerateAITestsRequest(BaseModel):
    """
    Petición para generar tests con IA (reutiliza 14.7).

    IMPORTANTE:
        - La IA genera DEFINICIONES de tests.
        - La IA NO ejecuta workflows.
        - El usuario revisa antes de guardar.
    """
    workflow: dict[str, Any] = Field(..., description="Workflow en formato dict (nodes + transitions)")


class GenerateAITestsResponse(BaseModel):
    """Resultado de generar tests con IA."""
    generated: list[TestCaseCreate]
    count: int
    explanation: str = ""
    warnings: list[str] = Field(default_factory=list)
    provider_used: str = ""


__all__ = [
    # Tipos
    "TestStatus",
    "AssertionType",
    # Assertion
    "TestAssertion",
    # Test Case
    "TestCaseCreate",
    "TestCaseUpdate",
    "TestCaseResponse",
    "TestListResponse",
    # Ejecución
    "TestRunRequest",
    "TestAdHocRunRequest",
    "AssertionResult",
    "TestStepTrace",
    "TestRunResult",
    "TestRunAllResult",
    # Análisis
    "StructuralIssue",
    "AnalyzeResponse",
    # Generación
    "GenerateBasicTestsResponse",
    "GenerateAITestsRequest",
    "GenerateAITestsResponse",
]
