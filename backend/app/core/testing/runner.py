"""
Nuvora Core — Testing: Test Runner
=====================================
Orquestador del Bot Tester (Fase 14.8.3).

FILOSOFÍA (regla de oro):
    - El TestRunner NUNCA ejecuta workflows directamente.
    - El TestRunner SIEMPRE llama al WorkflowEngine (14.5).
    - El TestRunner NO duplica lógica del Engine.
    - El TestRunner NO modifica el workflow ni la BD.
    - El TestRunner funciona en sandbox lógico.

FLUJO:
    TestCaseCreate
        ↓
    Validar límites
        ↓
    WorkflowEngine.run(workflow_data, initial_variables, max_steps)
        ↓
    ExecutionResult (con history 14.8.0)
        ↓
    evaluate_all_assertions()
        ↓
    TestRunResult (PASSED / FAILED / ERROR)

ESTADOS:
    - passed   → todas las assertions OK
    - failed   → workflow OK pero alguna assertion falló
    - error    → error técnico (workflow inválido, timeout, etc.)
"""

import time
import logging
from typing import Optional

from app.config import settings
from app.models.test import (
    TestCaseCreate,
    TestRunResult,
    TestRunAllResult,
    TestStepTrace,
)
from app.core.testing.assertions import (
    evaluate_all_assertions,
    summarize_assertions,
)
from app.core.testing.errors import (
    TestExecutionError,
    TestTimeoutError,
    TestLimitExceededError,
)
from app.core.workflows.engine import WorkflowEngine
from app.core.workflows.execution import ExecutionStatus
from app.core.workflows.errors import (
    WorkflowValidationError,
    MaxStepsExceeded,
    WorkflowExecutionError,
    NodeExecutionError,
    ConditionError,
)


logger = logging.getLogger(__name__)


class TestRunner:
    """
    Ejecuta tests contra un workflow.

    Uso:
        runner = TestRunner(workflow_data=wf_dict, bot_id=bot.id)
        result = runner.run_test(test_case)
    """

    def __init__(self, workflow_data: dict, bot_id: int = 0):
        """
        Args:
            workflow_data: dict con 'nodes' y 'transitions' (formato engine).
            bot_id: opcional, para trazabilidad.
        """
        self.workflow_data = workflow_data
        self.bot_id = bot_id
        self.engine = WorkflowEngine()

    # ============================================================
    # API PÚBLICA
    # ============================================================

    def run_test(
        self,
        test_case: TestCaseCreate,
        max_steps: Optional[int] = None,
        timeout_seconds: Optional[int] = None,
    ) -> TestRunResult:
        """
        Ejecuta un test individual.

        Args:
            test_case: definición del test.
            max_steps: override del límite de pasos (default: settings.tests.max_steps_per_test).
            timeout_seconds: override del timeout (default: settings.tests.timeout_seconds).

        Returns:
            TestRunResult con status passed/failed/error.
        """
        # 1. Aplicar límites (con overrides)
        _max_steps = max_steps if max_steps is not None else settings.tests.max_steps_per_test
        _timeout = timeout_seconds if timeout_seconds is not None else settings.tests.timeout_seconds

        # 2. Validar límites del test (defensa en profundidad)
        try:
            self._validate_limits(test_case)
        except TestLimitExceededError as e:
            return self._error_result(test_case, error=str(e))

        # 3. Ejecutar
        start_time = time.monotonic()
        try:
            result = self._execute(test_case, _max_steps)
        except TestTimeoutError as e:
            return self._error_result(test_case, error=str(e))
        except MaxStepsExceeded as e:
            return self._error_result(test_case, error=f"MaxStepsExceeded: {e}")
        except WorkflowValidationError as e:
            return self._error_result(
                test_case,
                error=f"WorkflowValidationError: {e.errors}",
            )
        except ConditionError as e:
            return self._error_result(
                test_case,
                error=f"ConditionError: {e.message}",
            )
        except (WorkflowExecutionError, NodeExecutionError) as e:
            return self._error_result(
                test_case,
                error=f"{type(e).__name__}: {e}",
            )
        except Exception as e:
            logger.exception(f"[runner] Error inesperado ejecutando test '{test_case.name}'")
            return self._error_result(
                test_case,
                error=f"Error inesperado: {type(e).__name__}: {e}",
            )

        duration_ms = int((time.monotonic() - start_time) * 1000)

        # 4. Evaluar assertions
        try:
            assertion_results = evaluate_all_assertions(test_case.assertions, result)
            passed_count, failed_count = summarize_assertions(assertion_results)
        except Exception as e:
            logger.exception(f"[runner] Error evaluando assertions")
            return self._error_result(
                test_case,
                error=f"Error evaluando assertions: {type(e).__name__}: {e}",
            )

        # 5. Determinar estado final
        if failed_count == 0:
            status = "passed"
        else:
            status = "failed"

        # 6. Construir trace
        trace = self._build_trace(result)

        # 7. Respuestas generadas
        responses = [
            o.get("text", "")
            for o in (result.outputs or [])
            if isinstance(o, dict) and o.get("text")
        ]

        # 8. Nodes visitados (del history)
        nodes_visited = [
            h.get("node_id", "")
            for h in (result.history or [])
            if isinstance(h, dict) and h.get("node_id")
        ]

        return TestRunResult(
            test_id=None,  # el router añade el id si aplica
            test_name=test_case.name,
            status=status,
            duration_ms=duration_ms,
            steps_used=result.steps_used,
            nodes_visited=nodes_visited,
            trace=trace,
            responses=responses,
            variables=result.variables or {},
            workflow_status=result.status.value,
            assertions_passed=passed_count,
            assertions_failed=failed_count,
            assertion_results=assertion_results,
        )

    def run_all(
        self,
        test_cases: list[TestCaseCreate],
        max_tests: Optional[int] = None,
    ) -> TestRunAllResult:
        """
        Ejecuta todos los tests de un workflow.

        Args:
            test_cases: lista de definiciones.
            max_tests: override del límite (default: settings.tests.max_tests_per_run_all).

        Returns:
            TestRunAllResult con agregado + results individuales.
        """
        _max_tests = max_tests if max_tests is not None else settings.tests.max_tests_per_run_all

        if len(test_cases) > _max_tests:
            # Recortamos (el router decidirá si error o no)
            test_cases = test_cases[:_max_tests]

        start_time = time.monotonic()
        results: list[TestRunResult] = []

        for tc in test_cases:
            results.append(self.run_test(tc))

        duration_ms = int((time.monotonic() - start_time) * 1000)

        passed = sum(1 for r in results if r.status == "passed")
        failed = sum(1 for r in results if r.status == "failed")
        errors = sum(1 for r in results if r.status == "error")

        return TestRunAllResult(
            workflow_id=0,  # el router lo rellena
            total=len(results),
            passed=passed,
            failed=failed,
            errors=errors,
            duration_ms=duration_ms,
            results=results,
        )

    # ============================================================
    # INTERNOS
    # ============================================================

    def _validate_limits(self, test_case: TestCaseCreate) -> None:
        """Valida los límites configurables del Tester."""
        if len(test_case.input_messages) > settings.tests.max_messages_per_test:
            raise TestLimitExceededError(
                limit_name="max_messages_per_test",
                limit_value=settings.tests.max_messages_per_test,
            )
        if len(test_case.assertions) > settings.tests.max_assertions_per_test:
            raise TestLimitExceededError(
                limit_name="max_assertions_per_test",
                limit_value=settings.tests.max_assertions_per_test,
            )
        if len(test_case.initial_variables) > settings.tests.max_variables_per_test:
            raise TestLimitExceededError(
                limit_name="max_variables_per_test",
                limit_value=settings.tests.max_variables_per_test,
            )

    def _execute(self, test_case: TestCaseCreate, max_steps: int):
        """
        Ejecuta el workflow con las variables iniciales.

        NOTA: El Tester construye las variables iniciales a partir de
        `initial_variables`. Las `input_messages` se concatenan como una
        única "pregunta" para workflows conversacionales (por ahora).
        En el futuro, workflows con WAITING_INPUT requerirán un manejo
        diferente, pero para 14.8 nos sirve así.
        """
        # Combinar las input_messages: para el workflow, el "input" es
        # el primer mensaje. Los demás se ignoran hasta que implementemos
        # ejecución con WAITING_INPUT.
        initial_vars = dict(test_case.initial_variables or {})

        # Si hay input_messages, pasar la primera como variable 'input'
        if test_case.input_messages:
            initial_vars.setdefault("input", test_case.input_messages[0])
            initial_vars.setdefault("user_message", test_case.input_messages[0])

        return self.engine.run(
            workflow_data=self.workflow_data,
            bot_id=self.bot_id,
            workflow_id=0,
            initial_variables=initial_vars,
            max_steps=max_steps,
        )

    def _build_trace(self, result) -> list[TestStepTrace]:
        """Convierte history en lista de TestStepTrace."""
        trace: list[TestStepTrace] = []
        for h in result.history or []:
            if not isinstance(h, dict):
                continue
            trace.append(TestStepTrace(
                step=h.get("step", 0),
                node_id=h.get("node_id", ""),
                type=h.get("type", ""),
                output=h.get("output"),
            ))
        return trace

    def _error_result(self, test_case: TestCaseCreate, error: str) -> TestRunResult:
        """Construye un TestRunResult con status='error'."""
        return TestRunResult(
            test_id=None,
            test_name=test_case.name,
            status="error",
            duration_ms=0,
            steps_used=0,
            nodes_visited=[],
            trace=[],
            responses=[],
            variables={},
            workflow_status=None,
            assertions_passed=0,
            assertions_failed=0,
            assertion_results=[],
            error=error,
        )


__all__ = ["TestRunner"]
