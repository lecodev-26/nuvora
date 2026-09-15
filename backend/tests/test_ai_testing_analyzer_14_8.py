"""
Tests — Subfase 14.8.5
Verifica el WorkflowAnalyzer: 10 checks estáticos.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.testing import WorkflowAnalyzer


# ============================================================
# HELPERS
# ============================================================

def _wf(nodes, transitions):
    return {"nodes": nodes, "transitions": transitions}


def _codes(response):
    """Devuelve el set de códigos de todos los issues."""
    return {issue.code for issue in response.issues}


# ============================================================
# TESTS
# ============================================================

def test_good_workflow_no_issues():
    print("\n" + "=" * 70)
    print("TEST 1: Workflow bueno → sin issues")
    print("=" * 70)
    wf = _wf(
        nodes=[
            {"node_id": "s1", "type": "start"},
            {"node_id": "m1", "type": "message", "config": {"text": "Hola"}},
            {"node_id": "e1", "type": "end"},
        ],
        transitions=[
            {"from_node_id": "s1", "to_node_id": "m1"},
            {"from_node_id": "m1", "to_node_id": "e1"},
        ],
    )
    r = WorkflowAnalyzer(wf).analyze()
    assert r.summary["error"] == 0
    assert r.summary["warning"] == 0
    assert r.summary["info"] == 0
    print(f"  ✅ Sin issues")


def test_missing_start():
    print("\n" + "=" * 70)
    print("TEST 2: Falta START → error")
    print("=" * 70)
    wf = _wf(
        nodes=[
            {"node_id": "m1", "type": "message", "config": {"text": "Hola"}},
            {"node_id": "e1", "type": "end"},
        ],
        transitions=[{"from_node_id": "m1", "to_node_id": "e1"}],
    )
    r = WorkflowAnalyzer(wf).analyze()
    assert "missing_start" in _codes(r)
    print(f"  ✅ missing_start detectado")


def test_multiple_starts():
    print("\n" + "=" * 70)
    print("TEST 3: Múltiples START → error")
    print("=" * 70)
    wf = _wf(
        nodes=[
            {"node_id": "s1", "type": "start"},
            {"node_id": "s2", "type": "start"},
            {"node_id": "e1", "type": "end"},
        ],
        transitions=[
            {"from_node_id": "s1", "to_node_id": "e1"},
            {"from_node_id": "s2", "to_node_id": "e1"},
        ],
    )
    r = WorkflowAnalyzer(wf).analyze()
    assert "multiple_starts" in _codes(r)
    print(f"  ✅ multiple_starts detectado")


def test_missing_end():
    print("\n" + "=" * 70)
    print("TEST 4: Falta END → error")
    print("=" * 70)
    wf = _wf(
        nodes=[{"node_id": "s1", "type": "start"}],
        transitions=[],
    )
    r = WorkflowAnalyzer(wf).analyze()
    assert "missing_end" in _codes(r)
    print(f"  ✅ missing_end detectado")


def test_orphan_node():
    print("\n" + "=" * 70)
    print("TEST 5: Nodo huérfano → warning")
    print("=" * 70)
    wf = _wf(
        nodes=[
            {"node_id": "s1", "type": "start"},
            {"node_id": "orphan", "type": "message", "config": {"text": "x"}},
            {"node_id": "e1", "type": "end"},
        ],
        transitions=[{"from_node_id": "s1", "to_node_id": "e1"}],
    )
    r = WorkflowAnalyzer(wf).analyze()
    assert "orphan_node" in _codes(r)
    print(f"  ✅ orphan_node detectado")


def test_unreachable_node():
    print("\n" + "=" * 70)
    print("TEST 6: Nodo inalcanzable → warning")
    print("=" * 70)
    wf = _wf(
        nodes=[
            {"node_id": "s1", "type": "start"},
            {"node_id": "m1", "type": "message", "config": {"text": "x"}},
            {"node_id": "orphan", "type": "message", "config": {"text": "y"}},
            {"node_id": "e1", "type": "end"},
        ],
        transitions=[
            {"from_node_id": "s1", "to_node_id": "m1"},
            {"from_node_id": "m1", "to_node_id": "e1"},
            {"from_node_id": "orphan", "to_node_id": "orphan"},
        ],
    )
    r = WorkflowAnalyzer(wf).analyze()
    assert "unreachable_node" in _codes(r)
    print(f"  ✅ unreachable_node detectado")


def test_condition_few_outputs():
    print("\n" + "=" * 70)
    print("TEST 7: CONDITION con 1 salida → error")
    print("=" * 70)
    wf = _wf(
        nodes=[
            {"node_id": "s1", "type": "start"},
            {"node_id": "c1", "type": "condition", "config": {"condition": "x > 0"}},
            {"node_id": "e1", "type": "end"},
        ],
        transitions=[
            {"from_node_id": "s1", "to_node_id": "c1"},
            {"from_node_id": "c1", "to_node_id": "e1"},
        ],
    )
    r = WorkflowAnalyzer(wf).analyze()
    assert "condition_few_outputs" in _codes(r)
    print(f"  ✅ condition_few_outputs detectado")


def test_invalid_condition_syntax():
    print("\n" + "=" * 70)
    print("TEST 8: Condición inválida → error")
    print("=" * 70)
    wf = _wf(
        nodes=[
            {"node_id": "s1", "type": "start"},
            {"node_id": "c1", "type": "condition", "config": {"condition": "esto no es valido"}},
            {"node_id": "e1", "type": "end"},
            {"node_id": "e2", "type": "end"},
        ],
        transitions=[
            {"from_node_id": "s1", "to_node_id": "c1"},
            {"from_node_id": "c1", "to_node_id": "e1", "condition": "x > 0"},
            {"from_node_id": "c1", "to_node_id": "e2", "condition": "x <= 0"},
        ],
    )
    r = WorkflowAnalyzer(wf).analyze()
    assert "invalid_condition_syntax" in _codes(r)
    print(f"  ✅ invalid_condition_syntax detectado")


def test_dead_end():
    print("\n" + "=" * 70)
    print("TEST 9: Dead-end (nodo sin camino a END) → warning")
    print("=" * 70)
    wf = _wf(
        nodes=[
            {"node_id": "s1", "type": "start"},
            {"node_id": "m1", "type": "message", "config": {"text": "x"}},
            {"node_id": "m_dead", "type": "message", "config": {"text": "y"}},
            {"node_id": "e1", "type": "end"},
        ],
        transitions=[
            {"from_node_id": "s1", "to_node_id": "m1"},
            {"from_node_id": "m1", "to_node_id": "e1"},
            {"from_node_id": "m_dead", "to_node_id": "m_dead"},  # solo se apunta a sí mismo
        ],
    )
    r = WorkflowAnalyzer(wf).analyze()
    assert "dead_end" in _codes(r)
    print(f"  ✅ dead_end detectado")


def test_cycle_info():
    print("\n" + "=" * 70)
    print("TEST 10: Ciclo → info (no error)")
    print("=" * 70)
    wf = _wf(
        nodes=[
            {"node_id": "s1", "type": "start"},
            {"node_id": "m1", "type": "message", "config": {"text": "x"}},
            {"node_id": "m2", "type": "message", "config": {"text": "y"}},
            {"node_id": "e1", "type": "end"},
        ],
        transitions=[
            {"from_node_id": "s1", "to_node_id": "m1"},
            {"from_node_id": "m1", "to_node_id": "m2"},
            {"from_node_id": "m2", "to_node_id": "m1"},  # ciclo
        ],
    )
    r = WorkflowAnalyzer(wf).analyze()
    assert "cycles_detected" in _codes(r)
    cycles_issue = next(i for i in r.issues if i.code == "cycles_detected")
    assert cycles_issue.severity == "info"
    print(f"  ✅ cycles_detected (info)")


def test_variable_used_before_created():
    print("\n" + "=" * 70)
    print("TEST 11: Variable usada antes de crearse → warning")
    print("=" * 70)
    wf = _wf(
        nodes=[
            {"node_id": "s1", "type": "start"},
            {"node_id": "m1", "type": "message", "config": {"text": "Hola {{name}}"}},  # name no creada aún
            {"node_id": "q1", "type": "question", "config": {"text": "¿?", "variable": "name"}},  # name se crea aquí
            {"node_id": "e1", "type": "end"},
        ],
        transitions=[
            {"from_node_id": "s1", "to_node_id": "m1"},
            {"from_node_id": "m1", "to_node_id": "q1"},
            {"from_node_id": "q1", "to_node_id": "e1"},
        ],
    )
    r = WorkflowAnalyzer(wf).analyze()
    assert "variable_used_before_created" in _codes(r)
    print(f"  ✅ variable_used_before_created detectado")


def test_variable_correctly_used():
    print("\n" + "=" * 70)
    print("TEST 12: Variable creada antes de usarse → sin warning")
    print("=" * 70)
    wf = _wf(
        nodes=[
            {"node_id": "s1", "type": "start"},
            {"node_id": "q1", "type": "question", "config": {"text": "¿?", "variable": "name"}},
            {"node_id": "m1", "type": "message", "config": {"text": "Hola {{name}}"}},  # OK, ya creada
            {"node_id": "e1", "type": "end"},
        ],
        transitions=[
            {"from_node_id": "s1", "to_node_id": "q1"},
            {"from_node_id": "q1", "to_node_id": "m1"},
            {"from_node_id": "m1", "to_node_id": "e1"},
        ],
    )
    r = WorkflowAnalyzer(wf).analyze()
    assert "variable_used_before_created" not in _codes(r)
    print(f"  ✅ Sin warning de variables")


def test_variable_created_by_variable_node():
    print("\n" + "=" * 70)
    print("TEST 13: VariableNode crea variable para uso posterior")
    print("=" * 70)
    wf = _wf(
        nodes=[
            {"node_id": "s1", "type": "start"},
            {"node_id": "v1", "type": "variable", "config": {"name": "greeting", "value": "Hola"}},
            {"node_id": "m1", "type": "message", "config": {"text": "{{greeting}} mundo"}},
            {"node_id": "e1", "type": "end"},
        ],
        transitions=[
            {"from_node_id": "s1", "to_node_id": "v1"},
            {"from_node_id": "v1", "to_node_id": "m1"},
            {"from_node_id": "m1", "to_node_id": "e1"},
        ],
    )
    r = WorkflowAnalyzer(wf).analyze()
    assert "variable_used_before_created" not in _codes(r)
    print(f"  ✅ Sin warning")


def test_multiple_issues_at_once():
    print("\n" + "=" * 70)
    print("TEST 14: Múltiples issues a la vez")
    print("=" * 70)
    wf = _wf(
        nodes=[
            {"node_id": "orphan1", "type": "message", "config": {"text": "x"}},
        ],
        transitions=[],
    )
    r = WorkflowAnalyzer(wf).analyze()
    # Debe detectar: missing_start, missing_end, orphan_node
    codes = _codes(r)
    assert "missing_start" in codes
    assert "missing_end" in codes
    print(f"  ✅ {r.summary}")


def test_analyzer_severity_distribution():
    print("\n" + "=" * 70)
    print("TEST 15: Distribución de severidades")
    print("=" * 70)
    wf = _wf(
        nodes=[
            {"node_id": "s1", "type": "start"},
            {"node_id": "m1", "type": "message", "config": {"text": "x"}},
            {"node_id": "orphan", "type": "message", "config": {"text": "y"}},
            {"node_id": "e1", "type": "end"},
        ],
        transitions=[
            {"from_node_id": "s1", "to_node_id": "m1"},
            {"from_node_id": "m1", "to_node_id": "e1"},
        ],
    )
    r = WorkflowAnalyzer(wf).analyze()
    # Debe tener al menos: orphan_node (warning) + unreachable_node (warning)
    assert r.summary["warning"] >= 2
    assert r.summary["error"] == 0
    print(f"  ✅ {r.summary}")


# ============================================================
# REGRESIÓN
# ============================================================

def test_regression_app_imports():
    print("\n" + "=" * 70)
    print("TEST 16: Regresión — app.main sigue OK")
    print("=" * 70)
    from app.main import app as _app
    assert _app is not None
    print(f"  ✅ app OK ({len(_app.routes)} rutas)")


def test_regression_runner_still_works():
    print("\n" + "=" * 70)
    print("TEST 17: Regresión — TestRunner sigue OK")
    print("=" * 70)
    from app.core.testing import TestRunner
    from app.models.test import TestCaseCreate
    wf = _wf(
        nodes=[
            {"node_id": "s1", "type": "start"},
            {"node_id": "m1", "type": "message", "config": {"text": "Hola"}},
            {"node_id": "e1", "type": "end"},
        ],
        transitions=[
            {"from_node_id": "s1", "to_node_id": "m1"},
            {"from_node_id": "m1", "to_node_id": "e1"},
        ],
    )
    runner = TestRunner(workflow_data=wf)
    tc = TestCaseCreate(
        name="t",
        input_messages=["hi"],
        assertions=[{"type": "reaches_end"}],
    )
    r = runner.run_test(tc)
    assert r.status == "passed"
    print(f"  ✅ Runner OK")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.8.5 (WorkflowAnalyzer)")
    print("=" * 70)

    tests = [
        test_good_workflow_no_issues,
        test_missing_start,
        test_multiple_starts,
        test_missing_end,
        test_orphan_node,
        test_unreachable_node,
        test_condition_few_outputs,
        test_invalid_condition_syntax,
        test_dead_end,
        test_cycle_info,
        test_variable_used_before_created,
        test_variable_correctly_used,
        test_variable_created_by_variable_node,
        test_multiple_issues_at_once,
        test_analyzer_severity_distribution,
        test_regression_app_imports,
        test_regression_runner_still_works,
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
