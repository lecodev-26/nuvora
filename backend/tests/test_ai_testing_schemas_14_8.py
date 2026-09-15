"""
Tests — Subfase 14.8.2
Verifica:
    - app/config.py: TestConfig + límites
    - app/models/test.py: schemas Pydantic
    - app/core/testing/errors.py: 7 errores
    - app/core/testing/__init__.py: exports
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import ValidationError

from app.config import settings, TestConfig
from app.models.test import (
    TestAssertion,
    TestCaseCreate,
    TestCaseUpdate,
    TestCaseResponse,
    TestListResponse,
    TestRunRequest,
    TestAdHocRunRequest,
    AssertionResult,
    TestStepTrace,
    TestRunResult,
    TestRunAllResult,
    StructuralIssue,
    AnalyzeResponse,
    GenerateBasicTestsResponse,
    GenerateAITestsRequest,
    GenerateAITestsResponse,
)
from app.core.testing import (
    TestingError,
    TestNotFoundError,
    TestDefinitionError,
    TestExecutionError,
    TestAssertionError,
    TestTimeoutError,
    TestLimitExceededError,
)


# ============================================================
# TESTS — Config
# ============================================================

def test_testconfig_defaults():
    print("\n" + "=" * 70)
    print("TEST 1: TestConfig defaults")
    print("=" * 70)
    cfg = TestConfig()
    assert cfg.timeout_seconds == 30
    assert cfg.max_messages_per_test == 20
    assert cfg.max_assertions_per_test == 30
    assert cfg.max_steps_per_test == 200
    assert cfg.max_tests_per_workflow == 100
    assert cfg.max_tests_per_run_all == 50
    print(f"  ✅ timeout={cfg.timeout_seconds}s, max_msgs={cfg.max_messages_per_test}, max_assertions={cfg.max_assertions_per_test}")


def test_settings_has_tests():
    print("\n" + "=" * 70)
    print("TEST 2: settings.tests existe")
    print("=" * 70)
    assert settings.tests is not None
    assert settings.tests.timeout_seconds == 30
    print(f"  ✅ settings.tests.timeout_seconds={settings.tests.timeout_seconds}")


# ============================================================
# TESTS — Errores
# ============================================================

def test_errors_hierarchy():
    print("\n" + "=" * 70)
    print("TEST 3: Jerarquía de errores")
    print("=" * 70)
    assert issubclass(TestNotFoundError, TestingError)
    assert issubclass(TestDefinitionError, TestingError)
    assert issubclass(TestExecutionError, TestingError)
    assert issubclass(TestAssertionError, TestingError)
    assert issubclass(TestTimeoutError, TestingError)
    assert issubclass(TestLimitExceededError, TestingError)
    print(f"  ✅ 7 errores, jerarquía OK")


def test_timeout_error():
    print("\n" + "=" * 70)
    print("TEST 4: TestTimeoutError")
    print("=" * 70)
    e = TestTimeoutError(timeout_seconds=30)
    assert e.timeout_seconds == 30
    assert "30" in str(e)
    print(f"  ✅ {e}")


def test_limit_error():
    print("\n" + "=" * 70)
    print("TEST 5: TestLimitExceededError")
    print("=" * 70)
    e = TestLimitExceededError(limit_name="max_messages_per_test", limit_value=20)
    assert e.limit_name == "max_messages_per_test"
    assert e.limit_value == 20
    assert "20" in str(e)
    print(f"  ✅ {e}")


# ============================================================
# TESTS — TestAssertion
# ============================================================

def test_assertion_response_contains():
    print("\n" + "=" * 70)
    print("TEST 6: TestAssertion response_contains")
    print("=" * 70)
    a = TestAssertion(type="response_contains", value="reserva")
    assert a.type == "response_contains"
    assert a.value == "reserva"
    print(f"  ✅ {a.type} → '{a.value}'")


def test_assertion_response_contains_missing_value():
    print("\n" + "=" * 70)
    print("TEST 7: TestAssertion response_contains sin value → error")
    print("=" * 70)
    try:
        TestAssertion(type="response_contains")
        assert False, "Debería haber fallado"
    except ValidationError:
        print(f"  ✅ Validación OK")


def test_assertion_node_visited():
    print("\n" + "=" * 70)
    print("TEST 8: TestAssertion node_visited")
    print("=" * 70)
    a = TestAssertion(type="node_visited", node_id="question_1")
    assert a.node_id == "question_1"
    print(f"  ✅ node_visited → {a.node_id}")


def test_assertion_node_visited_missing_node_id():
    print("\n" + "=" * 70)
    print("TEST 9: TestAssertion node_visited sin node_id → error")
    print("=" * 70)
    try:
        TestAssertion(type="node_visited")
        assert False, "Debería haber fallado"
    except ValidationError:
        print(f"  ✅ Validación OK")


def test_assertion_variable_equals():
    print("\n" + "=" * 70)
    print("TEST 10: TestAssertion variable_equals")
    print("=" * 70)
    a = TestAssertion(type="variable_equals", variable="name", expected="Manuel")
    assert a.variable == "name"
    assert a.expected == "Manuel"
    print(f"  ✅ variable_equals → {a.variable} == '{a.expected}'")


def test_assertion_variable_equals_missing_expected():
    print("\n" + "=" * 70)
    print("TEST 11: TestAssertion variable_equals sin expected → error")
    print("=" * 70)
    try:
        TestAssertion(type="variable_equals", variable="name")
        assert False, "Debería haber fallado"
    except ValidationError:
        print(f"  ✅ Validación OK")


def test_assertion_max_steps():
    print("\n" + "=" * 70)
    print("TEST 12: TestAssertion max_steps")
    print("=" * 70)
    a = TestAssertion(type="max_steps", max_steps=20)
    assert a.max_steps == 20
    print(f"  ✅ max_steps → {a.max_steps}")


def test_assertion_reaches_end():
    print("\n" + "=" * 70)
    print("TEST 13: TestAssertion reaches_end (sin campos extra)")
    print("=" * 70)
    a = TestAssertion(type="reaches_end")
    assert a.type == "reaches_end"
    print(f"  ✅ reaches_end OK")


def test_assertion_invalid_type():
    print("\n" + "=" * 70)
    print("TEST 14: TestAssertion tipo inválido → error")
    print("=" * 70)
    try:
        TestAssertion(type="invalid_type", value="x")
        assert False, "Debería haber fallado"
    except ValidationError:
        print(f"  ✅ Validación OK")


# ============================================================
# TESTS — TestCaseCreate
# ============================================================

def _valid_test_dict():
    return {
        "name": "Reserva válida",
        "description": "El cliente reserva correctamente",
        "input_messages": ["Hola", "Quiero reservar", "Manuel"],
        "initial_variables": {},
        "assertions": [
            {"type": "response_contains", "value": "reserva"},
            {"type": "node_visited", "node_id": "question_1"},
            {"type": "reaches_end"},
        ],
        "enabled": True,
    }


def test_testcase_create_valid():
    print("\n" + "=" * 70)
    print("TEST 15: TestCaseCreate válido")
    print("=" * 70)
    tc = TestCaseCreate(**_valid_test_dict())
    assert tc.name == "Reserva válida"
    assert len(tc.input_messages) == 3
    assert len(tc.assertions) == 3
    print(f"  ✅ TestCaseCreate OK: {len(tc.assertions)} assertions, {len(tc.input_messages)} mensajes")


def test_testcase_create_empty_messages():
    print("\n" + "=" * 70)
    print("TEST 16: TestCaseCreate sin input_messages → error")
    print("=" * 70)
    d = _valid_test_dict()
    d["input_messages"] = []
    try:
        TestCaseCreate(**d)
        assert False, "Debería haber fallado"
    except ValidationError:
        print(f"  ✅ Validación OK")


def test_testcase_create_empty_assertions():
    print("\n" + "=" * 70)
    print("TEST 17: TestCaseCreate sin assertions → error")
    print("=" * 70)
    d = _valid_test_dict()
    d["assertions"] = []
    try:
        TestCaseCreate(**d)
        assert False, "Debería haber fallado"
    except ValidationError:
        print(f"  ✅ Validación OK")


def test_testcase_create_too_many_messages():
    print("\n" + "=" * 70)
    print("TEST 18: TestCaseCreate con > 20 mensajes → error")
    print("=" * 70)
    d = _valid_test_dict()
    d["input_messages"] = ["msg"] * 25
    try:
        TestCaseCreate(**d)
        assert False, "Debería haber fallado"
    except ValidationError:
        print(f"  ✅ Validación OK")


def test_testcase_create_blank_message():
    print("\n" + "=" * 70)
    print("TEST 19: TestCaseCreate con mensaje vacío → error")
    print("=" * 70)
    d = _valid_test_dict()
    d["input_messages"] = ["Hola", "   "]
    try:
        TestCaseCreate(**d)
        assert False, "Debería haber fallado"
    except ValidationError:
        print(f"  ✅ Validación OK")


def test_testcase_create_name_too_long():
    print("\n" + "=" * 70)
    print("TEST 20: TestCaseCreate con name > 200 chars → error")
    print("=" * 70)
    d = _valid_test_dict()
    d["name"] = "x" * 300
    try:
        TestCaseCreate(**d)
        assert False, "Debería haber fallado"
    except ValidationError:
        print(f"  ✅ Validación OK")


# ============================================================
# TESTS — TestRunResult + estados
# ============================================================

def test_test_run_result_passed():
    print("\n" + "=" * 70)
    print("TEST 21: TestRunResult status=passed")
    print("=" * 70)
    r = TestRunResult(
        test_id=1,
        test_name="Reserva",
        status="passed",
        duration_ms=143,
        steps_used=7,
        nodes_visited=["s1", "m1", "e1"],
        responses=["Hola"],
        variables={"name": "Manuel"},
        workflow_status="completed",
        assertions_passed=3,
        assertions_failed=0,
    )
    assert r.status == "passed"
    assert r.assertions_passed == 3
    print(f"  ✅ passed: {r.steps_used} steps, {r.assertions_passed} assertions")


def test_test_run_result_failed():
    print("\n" + "=" * 70)
    print("TEST 22: TestRunResult status=failed")
    print("=" * 70)
    r = TestRunResult(
        test_id=2,
        test_name="Reserva sin nombre",
        status="failed",
        steps_used=5,
        assertions_passed=1,
        assertions_failed=2,
    )
    assert r.status == "failed"
    print(f"  ✅ failed")


def test_test_run_result_error():
    print("\n" + "=" * 70)
    print("TEST 23: TestRunResult status=error")
    print("=" * 70)
    r = TestRunResult(
        test_id=3,
        test_name="Test roto",
        status="error",
        error="MaxStepsExceeded",
    )
    assert r.status == "error"
    assert r.error == "MaxStepsExceeded"
    print(f"  ✅ error: {r.error}")


def test_test_run_result_invalid_status():
    print("\n" + "=" * 70)
    print("TEST 24: TestRunResult status inválido → error")
    print("=" * 70)
    try:
        TestRunResult(status="unknown")
        assert False, "Debería haber fallado"
    except ValidationError:
        print(f"  ✅ Validación OK")


# ============================================================
# TESTS — TestRunAllResult
# ============================================================

def test_test_run_all_result():
    print("\n" + "=" * 70)
    print("TEST 25: TestRunAllResult")
    print("=" * 70)
    r = TestRunAllResult(
        workflow_id=1,
        total=5,
        passed=3,
        failed=1,
        errors=1,
        duration_ms=1234,
        results=[],
    )
    assert r.total == 5
    assert r.passed == 3
    print(f"  ✅ {r.passed}/{r.total} passed")


# ============================================================
# TESTS — Análisis y generación
# ============================================================

def test_structural_issue():
    print("\n" + "=" * 70)
    print("TEST 26: StructuralIssue")
    print("=" * 70)
    i = StructuralIssue(
        severity="warning",
        code="orphan_node",
        message="Nodo huérfano",
        node_id="m1",
    )
    assert i.severity == "warning"
    assert i.node_id == "m1"
    print(f"  ✅ {i.code}")


def test_generate_basic_tests_response():
    print("\n" + "=" * 70)
    print("TEST 27: GenerateBasicTestsResponse")
    print("=" * 70)
    r = GenerateBasicTestsResponse(
        generated=[TestCaseCreate(**_valid_test_dict())],
        count=1,
        notes=["Generated from structure"],
    )
    assert r.count == 1
    print(f"  ✅ {r.count} tests generados")


def test_generate_ai_tests_request():
    print("\n" + "=" * 70)
    print("TEST 28: GenerateAITestsRequest")
    print("=" * 70)
    r = GenerateAITestsRequest(workflow={"nodes": [], "transitions": []})
    assert "nodes" in r.workflow
    print(f"  ✅ Request OK")


# ============================================================
# TESTS — Regresión
# ============================================================

def test_regression_app_imports():
    print("\n" + "=" * 70)
    print("TEST 29: Regresión — app.main sigue OK")
    print("=" * 70)
    from app.main import app as _app
    assert _app is not None
    print(f"  ✅ app OK ({len(_app.routes)} rutas)")


def test_regression_workflow_engine_history():
    print("\n" + "=" * 70)
    print("TEST 30: Regresión — 14.8.0 history sigue OK")
    print("=" * 70)
    from app.core.workflows.engine import WorkflowEngine
    workflow = {
        "nodes": [
            {"node_id": "s1", "type": "start"},
            {"node_id": "e1", "type": "end"},
        ],
        "transitions": [
            {"from_node_id": "s1", "to_node_id": "e1"},
        ],
    }
    result = WorkflowEngine().run(workflow_data=workflow)
    assert len(result.history) == 2
    assert result.history[0]["node_id"] == "s1"
    print(f"  ✅ history OK: {len(result.history)} steps")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.8.2 (Test Schemas)")
    print("=" * 70)

    tests = [
        test_testconfig_defaults,
        test_settings_has_tests,
        test_errors_hierarchy,
        test_timeout_error,
        test_limit_error,
        test_assertion_response_contains,
        test_assertion_response_contains_missing_value,
        test_assertion_node_visited,
        test_assertion_node_visited_missing_node_id,
        test_assertion_variable_equals,
        test_assertion_variable_equals_missing_expected,
        test_assertion_max_steps,
        test_assertion_reaches_end,
        test_assertion_invalid_type,
        test_testcase_create_valid,
        test_testcase_create_empty_messages,
        test_testcase_create_empty_assertions,
        test_testcase_create_too_many_messages,
        test_testcase_create_blank_message,
        test_testcase_create_name_too_long,
        test_test_run_result_passed,
        test_test_run_result_failed,
        test_test_run_result_error,
        test_test_run_result_invalid_status,
        test_test_run_all_result,
        test_structural_issue,
        test_generate_basic_tests_response,
        test_generate_ai_tests_request,
        test_regression_app_imports,
        test_regression_workflow_engine_history,
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
