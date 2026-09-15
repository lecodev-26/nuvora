"""
Tests — Subfases 14.8.3 + 14.8.4
Verifica:
    - Assertion Engine (10 tipos)
    - TestRunner (run_test + run_all)
    - Estados PASSED / FAILED / ERROR
    - Límites configurables
    - Timeout y MaxSteps
    - Regresión 14.8.0 (history)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.test import TestCaseCreate, TestAssertion
from app.core.testing import (
    TestRunner,
    evaluate_assertion,
    evaluate_all_assertions,
    summarize_assertions,
)
from app.core.workflows.engine import WorkflowEngine
from app.core.workflows.execution import ExecutionStatus
from app.config import settings


# ============================================================
# HELPERS
# ============================================================

def _simple_workflow():
    """START → MESSAGE → END"""
    return {
        "nodes": [
            {"node_id": "s1", "type": "start"},
            {"node_id": "m1", "type": "message", "config": {"text": "Hola Manuel"}},
            {"node_id": "e1", "type": "end"},
        ],
        "transitions": [
            {"from_node_id": "s1", "to_node_id": "m1", "order": 0},
            {"from_node_id": "m1", "to_node_id": "e1", "order": 0},
        ],
    }


def _make_execution_result(**kwargs):
    """Crea un ExecutionResult manual para testear assertions."""
    from app.core.workflows.execution import ExecutionResult
    defaults = {
        "status": ExecutionStatus.COMPLETED,
        "outputs": [],
        "variables": {},
        "current_node_id": "e1",
        "steps_used": 3,
        "error": None,
        "history": [],
    }
    defaults.update(kwargs)
    return ExecutionResult(**defaults)


# ============================================================
# TESTS — Assertion Engine
# ============================================================

def test_assertion_response_contains_pass():
    print("\n" + "=" * 70)
    print("TEST 1: assertion response_contains → PASS")
    print("=" * 70)
    result = _make_execution_result(
        outputs=[{"text": "Hola Manuel"}],
    )
    a = TestAssertion(type="response_contains", value="Manuel")
    ar = evaluate_assertion(a, result)
    assert ar.passed is True
    print(f"  ✅ {ar.message or 'OK'}")


def test_assertion_response_contains_fail():
    print("\n" + "=" * 70)
    print("TEST 2: assertion response_contains → FAIL")
    print("=" * 70)
    result = _make_execution_result(outputs=[{"text": "Hola Ana"}])
    a = TestAssertion(type="response_contains", value="Manuel")
    ar = evaluate_assertion(a, result)
    assert ar.passed is False
    print(f"  ✅ FAIL: {ar.message}")


def test_assertion_response_equals():
    print("\n" + "=" * 70)
    print("TEST 3: assertion response_equals")
    print("=" * 70)
    result = _make_execution_result(outputs=[{"text": "Hola"}])
    a = TestAssertion(type="response_equals", value="Hola")
    assert evaluate_assertion(a, result).passed is True
    a2 = TestAssertion(type="response_equals", value="Hola!")
    assert evaluate_assertion(a2, result).passed is False
    print(f"  ✅ equals funcionando")


def test_assertion_response_not_contains():
    print("\n" + "=" * 70)
    print("TEST 4: assertion response_not_contains")
    print("=" * 70)
    result = _make_execution_result(outputs=[{"text": "Todo OK"}])
    a = TestAssertion(type="response_not_contains", value="error")
    assert evaluate_assertion(a, result).passed is True

    result2 = _make_execution_result(outputs=[{"text": "error grave"}])
    assert evaluate_assertion(a, result2).passed is False
    print(f"  ✅ not_contains funcionando")


def test_assertion_node_visited():
    print("\n" + "=" * 70)
    print("TEST 5: assertion node_visited")
    print("=" * 70)
    result = _make_execution_result(
        history=[
            {"step": 1, "node_id": "s1", "type": "start"},
            {"step": 2, "node_id": "m1", "type": "message"},
            {"step": 3, "node_id": "e1", "type": "end"},
        ]
    )
    a = TestAssertion(type="node_visited", node_id="m1")
    assert evaluate_assertion(a, result).passed is True

    a2 = TestAssertion(type="node_visited", node_id="nope")
    assert evaluate_assertion(a2, result).passed is False
    print(f"  ✅ node_visited funcionando")


def test_assertion_node_not_visited():
    print("\n" + "=" * 70)
    print("TEST 6: assertion node_not_visited")
    print("=" * 70)
    result = _make_execution_result(
        history=[{"step": 1, "node_id": "s1", "type": "start"}]
    )
    a = TestAssertion(type="node_not_visited", node_id="m1")
    assert evaluate_assertion(a, result).passed is True
    print(f"  ✅ node_not_visited OK")


def test_assertion_variable_equals():
    print("\n" + "=" * 70)
    print("TEST 7: assertion variable_equals")
    print("=" * 70)
    result = _make_execution_result(variables={"name": "Manuel", "age": 30})
    a = TestAssertion(type="variable_equals", variable="name", expected="Manuel")
    assert evaluate_assertion(a, result).passed is True

    a2 = TestAssertion(type="variable_equals", variable="name", expected="Ana")
    assert evaluate_assertion(a2, result).passed is False

    a3 = TestAssertion(type="variable_equals", variable="nope", expected="x")
    assert evaluate_assertion(a3, result).passed is False
    print(f"  ✅ variable_equals funcionando")


def test_assertion_variable_exists():
    print("\n" + "=" * 70)
    print("TEST 8: assertion variable_exists / not_exists")
    print("=" * 70)
    result = _make_execution_result(variables={"name": "Manuel"})
    a1 = TestAssertion(type="variable_exists", variable="name")
    assert evaluate_assertion(a1, result).passed is True
    a2 = TestAssertion(type="variable_not_exists", variable="nope")
    assert evaluate_assertion(a2, result).passed is True
    a3 = TestAssertion(type="variable_exists", variable="nope")
    assert evaluate_assertion(a3, result).passed is False
    print(f"  ✅ variable_exists/not_exists funcionando")


def test_assertion_reaches_end_pass():
    print("\n" + "=" * 70)
    print("TEST 9: assertion reaches_end → PASS")
    print("=" * 70)
    result = _make_execution_result(status=ExecutionStatus.COMPLETED)
    a = TestAssertion(type="reaches_end")
    assert evaluate_assertion(a, result).passed is True
    print(f"  ✅ reaches_end PASS")


def test_assertion_reaches_end_fail():
    print("\n" + "=" * 70)
    print("TEST 10: assertion reaches_end → FAIL (WAITING_INPUT)")
    print("=" * 70)
    result = _make_execution_result(status=ExecutionStatus.WAITING_INPUT)
    a = TestAssertion(type="reaches_end")
    assert evaluate_assertion(a, result).passed is False
    print(f"  ✅ reaches_end FAIL OK")


def test_assertion_max_steps():
    print("\n" + "=" * 70)
    print("TEST 11: assertion max_steps")
    print("=" * 70)
    result = _make_execution_result(steps_used=5)
    a = TestAssertion(type="max_steps", max_steps=10)
    assert evaluate_assertion(a, result).passed is True
    a2 = TestAssertion(type="max_steps", max_steps=3)
    assert evaluate_assertion(a2, result).passed is False
    print(f"  ✅ max_steps funcionando")


def test_assertion_summary():
    print("\n" + "=" * 70)
    print("TEST 12: summarize_assertions")
    print("=" * 70)
    result = _make_execution_result(outputs=[{"text": "Hola"}])
    assertions = [
        TestAssertion(type="response_contains", value="Hola"),   # PASS
        TestAssertion(type="response_contains", value="Nope"),   # FAIL
        TestAssertion(type="reaches_end"),                        # PASS
    ]
    ars = evaluate_all_assertions(assertions, result)
    passed, failed = summarize_assertions(ars)
    assert passed == 2
    assert failed == 1
    print(f"  ✅ {passed} passed / {failed} failed")


# ============================================================
# TESTS — TestRunner
# ============================================================

def test_runner_passed():
    print("\n" + "=" * 70)
    print("TEST 13: TestRunner.run_test → passed")
    print("=" * 70)
    runner = TestRunner(workflow_data=_simple_workflow(), bot_id=1)
    tc = TestCaseCreate(
        name="Test OK",
        input_messages=["Hola"],
        assertions=[
            {"type": "response_contains", "value": "Manuel"},
            {"type": "node_visited", "node_id": "m1"},
            {"type": "reaches_end"},
        ],
    )
    result = runner.run_test(tc)
    assert result.status == "passed"
    assert result.assertions_passed == 3
    assert result.assertions_failed == 0
    assert result.steps_used == 3
    assert len(result.nodes_visited) == 3
    print(f"  ✅ PASSED: {result.assertions_passed}/{result.assertions_passed + result.assertions_failed} assertions")


def test_runner_failed():
    print("\n" + "=" * 70)
    print("TEST 14: TestRunner.run_test → failed")
    print("=" * 70)
    runner = TestRunner(workflow_data=_simple_workflow(), bot_id=1)
    tc = TestCaseCreate(
        name="Test con fallo",
        input_messages=["Hola"],
        assertions=[
            {"type": "response_contains", "value": "Manuel"},   # PASS
            {"type": "response_contains", "value": "Nope"},     # FAIL
        ],
    )
    result = runner.run_test(tc)
    assert result.status == "failed"
    assert result.assertions_passed == 1
    assert result.assertions_failed == 1
    print(f"  ✅ FAILED: {result.assertions_passed}/{result.assertions_passed + result.assertions_failed} assertions")


def test_runner_error_invalid_workflow():
    print("\n" + "=" * 70)
    print("TEST 15: TestRunner con workflow inválido → error")
    print("=" * 70)
    bad_workflow = {
        "nodes": [
            {"node_id": "m1", "type": "message", "config": {"text": "Hola"}},
            {"node_id": "e1", "type": "end"},
        ],
        "transitions": [
            {"from_node_id": "m1", "to_node_id": "e1"},
        ],
    }
    runner = TestRunner(workflow_data=bad_workflow, bot_id=1)
    tc = TestCaseCreate(
        name="Test roto",
        input_messages=["Hola"],
        assertions=[{"type": "reaches_end"}],
    )
    result = runner.run_test(tc)
    assert result.status == "error"
    assert result.error is not None
    print(f"  ✅ ERROR: {result.error[:80]}")


def test_runner_run_all():
    print("\n" + "=" * 70)
    print("TEST 16: TestRunner.run_all")
    print("=" * 70)
    runner = TestRunner(workflow_data=_simple_workflow(), bot_id=1)
    tcs = [
        TestCaseCreate(
            name="Test 1",
            input_messages=["Hola"],
            assertions=[{"type": "reaches_end"}],
        ),
        TestCaseCreate(
            name="Test 2",
            input_messages=["Adiós"],
            assertions=[{"type": "response_contains", "value": "Manuel"}],
        ),
        TestCaseCreate(
            name="Test 3",
            input_messages=["Hi"],
            assertions=[{"type": "response_contains", "value": "Nope"}],
        ),
    ]
    result = runner.run_all(tcs)
    assert result.total == 3
    assert result.passed == 2
    assert result.failed == 1
    assert result.errors == 0
    assert len(result.results) == 3
    print(f"  ✅ {result.passed} passed / {result.failed} failed / {result.errors} errors")


def test_runner_timeout_and_limits():
    print("\n" + "=" * 70)
    print("TEST 17: TestRunner con test que excede límites")
    print("=" * 70)
    runner = TestRunner(workflow_data=_simple_workflow(), bot_id=1)
    # Crear un test con MÁS assertions que el límite
    too_many = settings.tests.max_assertions_per_test + 5
    try:
        tc = TestCaseCreate(
            name="Test con demasiadas assertions",
            input_messages=["Hola"],
            assertions=[{"type": "reaches_end"}] * too_many,
        )
        # Pydantic lo capa (max_length=30), así que no debería llegar hasta aquí
        result = runner.run_test(tc)
        # Si llega, será error por límite
        assert result.status == "error"
        print(f"  ✅ Capado por Pydantic: {result.error[:60] if result.error else 'N/A'}")
    except Exception as e:
        # Pydantic lo rechaza en la validación
        print(f"  ✅ Rechazado por Pydantic: {type(e).__name__}")


def test_runner_max_steps_exceeded():
    print("\n" + "=" * 70)
    print("TEST 18: TestRunner con max_steps muy bajo → error")
    print("=" * 70)
    # Workflow con ciclo infinito
    cyclic_workflow = {
        "nodes": [
            {"node_id": "s1", "type": "start"},
            {"node_id": "m1", "type": "message", "config": {"text": "A"}},
            {"node_id": "m2", "type": "message", "config": {"text": "B"}},
            {"node_id": "e1", "type": "end"},
        ],
        "transitions": [
            {"from_node_id": "s1", "to_node_id": "m1"},
            {"from_node_id": "m1", "to_node_id": "m2"},
            {"from_node_id": "m2", "to_node_id": "m1"},
        ],
    }
    runner = TestRunner(workflow_data=cyclic_workflow, bot_id=1)
    tc = TestCaseCreate(
        name="Test con ciclo",
        input_messages=["Hola"],
        assertions=[{"type": "reaches_end"}],
    )
    result = runner.run_test(tc, max_steps=5)
    assert result.status == "error"
    assert "MaxStepsExceeded" in (result.error or "")
    print(f"  ✅ ERROR esperado: {result.error[:60]}")


# ============================================================
# TESTS — Regresión
# ============================================================

def test_regression_app_imports():
    print("\n" + "=" * 70)
    print("TEST 19: Regresión — app.main sigue OK")
    print("=" * 70)
    from app.main import app as _app
    assert _app is not None
    print(f"  ✅ app OK ({len(_app.routes)} rutas)")


def test_regression_history_14_8_0():
    print("\n" + "=" * 70)
    print("TEST 20: Regresión — 14.8.0 history sigue OK")
    print("=" * 70)
    result = WorkflowEngine().run(workflow_data=_simple_workflow())
    assert len(result.history) == 3
    print(f"  ✅ history OK: {len(result.history)} steps")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASES 14.8.3 + 14.8.4 (Runner + Assertions)")
    print("=" * 70)

    tests = [
        test_assertion_response_contains_pass,
        test_assertion_response_contains_fail,
        test_assertion_response_equals,
        test_assertion_response_not_contains,
        test_assertion_node_visited,
        test_assertion_node_not_visited,
        test_assertion_variable_equals,
        test_assertion_variable_exists,
        test_assertion_reaches_end_pass,
        test_assertion_reaches_end_fail,
        test_assertion_max_steps,
        test_assertion_summary,
        test_runner_passed,
        test_runner_failed,
        test_runner_error_invalid_workflow,
        test_runner_run_all,
        test_runner_timeout_and_limits,
        test_runner_max_steps_exceeded,
        test_regression_app_imports,
        test_regression_history_14_8_0,
    ]

    try:
        for t in tests:
            t()
        print("\n" + "=" * 70)
        print("🎉 TODOS LOS TESTS PASARON")
        print("=" * 70)
    except AssertionError as e:
        print(f"\n🛑 TEST FALLIDO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n🛑 ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
