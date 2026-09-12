"""
Tests — Subfase 14.5.6
Verifica que el engine evalúa condiciones en nodos CONDITION.

Casos cubiertos:
    1.  CONDITION con age > 18 → age=21 → rama True
    2.  CONDITION con age > 18 → age=15 → rama False
    3.  CONDITION con múltiples ramas (if/elif/else)
    4.  CONDITION con else implícito (transición sin condition)
    5.  CONDITION sin match → WorkflowExecutionError
    6.  CONDITION con variable inexistente → ConditionError
    7.  CONDITION con expresión inválida → ConditionError
    8.  CONDITION con string igual
    9.  CONDITION dentro de flujo más grande
    10. Regresión: workflows sin CONDITION siguen funcionando
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.workflows.engine import run_workflow
from app.core.workflows.execution import ExecutionStatus
from app.core.workflows.errors import (
    WorkflowValidationError,
    WorkflowExecutionError,
    ConditionError,
)


# ============================================================
# HELPERS
# ============================================================

def _node(node_id, type_, **config):
    return {
        "node_id": node_id,
        "type": type_,
        "config": config if config else None,
    }


def _trans(from_, to_, order=0, condition=None, label=None):
    return {
        "from_node_id": from_,
        "to_node_id": to_,
        "order": order,
        "condition": condition,
        "label": label,
    }


def _wf(nodes, transitions):
    return {"nodes": nodes, "transitions": transitions}


# ============================================================
# TEST 1 — CONDITION con age > 18 → rama True
# ============================================================

def test_condition_true_branch():
    print("\n" + "=" * 70)
    print("TEST 1: CONDITION age > 18 → rama True")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("c1", "condition", condition="age > 18"),
            _node("m_true", "message", text="Eres mayor de edad"),
            _node("m_false", "message", text="Eres menor de edad"),
            _node("e1", "end"),
        ],
        transitions=[
            _trans("s1", "c1"),
            _trans("c1", "m_true", order=1, condition="age > 18", label="true"),
            _trans("c1", "m_false", order=2, condition="age <= 18", label="false"),
            _trans("m_true", "e1"),
            _trans("m_false", "e1"),
        ],
    )

    result = run_workflow(workflow, initial_variables={"age": 21})

    assert result.status == ExecutionStatus.COMPLETED
    assert len(result.outputs) == 1
    assert result.outputs[0]["text"] == "Eres mayor de edad"
    print(f"✅ Rama True: '{result.outputs[0]['text']}'")


# ============================================================
# TEST 2 — CONDITION con age > 18 → rama False
# ============================================================

def test_condition_false_branch():
    print("\n" + "=" * 70)
    print("TEST 2: CONDITION age > 18 → rama False")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("c1", "condition", condition="age > 18"),
            _node("m_true", "message", text="Eres mayor de edad"),
            _node("m_false", "message", text="Eres menor de edad"),
            _node("e1", "end"),
        ],
        transitions=[
            _trans("s1", "c1"),
            _trans("c1", "m_true", order=1, condition="age > 18", label="true"),
            _trans("c1", "m_false", order=2, condition="age <= 18", label="false"),
            _trans("m_true", "e1"),
            _trans("m_false", "e1"),
        ],
    )

    result = run_workflow(workflow, initial_variables={"age": 15})

    assert result.status == ExecutionStatus.COMPLETED
    assert len(result.outputs) == 1
    assert result.outputs[0]["text"] == "Eres menor de edad"
    print(f"✅ Rama False: '{result.outputs[0]['text']}'")


# ============================================================
# TEST 3 — CONDITION con múltiples ramas (if/elif/else)
# ============================================================

def test_condition_multiple_branches():
    print("\n" + "=" * 70)
    print("TEST 3: CONDITION múltiples ramas (score)")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("c1", "condition", condition="score >= 90"),
            _node("m_a", "message", text="Excelente"),
            _node("m_b", "message", text="Notable"),
            _node("m_c", "message", text="Aprobado"),
            _node("m_d", "message", text="Suspenso"),
            _node("e1", "end"),
        ],
        transitions=[
            _trans("s1", "c1"),
            _trans("c1", "m_a", order=1, condition="score >= 90"),
            _trans("c1", "m_b", order=2, condition="score >= 70"),
            _trans("c1", "m_c", order=3, condition="score >= 50"),
            _trans("c1", "m_d", order=4),  # else implícito
            _trans("m_a", "e1"),
            _trans("m_b", "e1"),
            _trans("m_c", "e1"),
            _trans("m_d", "e1"),
        ],
    )

    # score = 95 → Excelente
    result = run_workflow(workflow, initial_variables={"score": 95})
    assert result.outputs[0]["text"] == "Excelente"
    print(f"   score=95 → '{result.outputs[0]['text']}' ✅")

    # score = 75 → Notable
    result = run_workflow(workflow, initial_variables={"score": 75})
    assert result.outputs[0]["text"] == "Notable"
    print(f"   score=75 → '{result.outputs[0]['text']}' ✅")

    # score = 55 → Aprobado
    result = run_workflow(workflow, initial_variables={"score": 55})
    assert result.outputs[0]["text"] == "Aprobado"
    print(f"   score=55 → '{result.outputs[0]['text']}' ✅")

    # score = 30 → Suspenso
    result = run_workflow(workflow, initial_variables={"score": 30})
    assert result.outputs[0]["text"] == "Suspenso"
    print(f"   score=30 → '{result.outputs[0]['text']}' ✅")

    print("✅ 4 ramas (if/elif/elif/else) evaluadas correctamente")


# ============================================================
# TEST 4 — CONDITION con else implícito (sin condition)
# ============================================================

def test_condition_else_implicit():
    print("\n" + "=" * 70)
    print("TEST 4: CONDITION con else implícito")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("c1", "condition", condition="active == true"),
            _node("m_on", "message", text="Servicio activo"),
            _node("m_off", "message", text="Servicio inactivo"),
            _node("e1", "end"),
        ],
        transitions=[
            _trans("s1", "c1"),
            _trans("c1", "m_on", order=1, condition="active == true"),
            _trans("c1", "m_off", order=2),  # else sin condition
            _trans("m_on", "e1"),
            _trans("m_off", "e1"),
        ],
    )

    result = run_workflow(workflow, initial_variables={"active": False})
    assert result.outputs[0]["text"] == "Servicio inactivo"
    print(f"✅ Else implícito: '{result.outputs[0]['text']}'")


# ============================================================
# TEST 5 — CONDITION sin match → WorkflowExecutionError
# ============================================================

def test_condition_no_match():
    print("\n" + "=" * 70)
    print("TEST 5: CONDITION sin match → WorkflowExecutionError")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("c1", "condition", condition="age > 18"),
            _node("m_true", "message", text="True"),
            _node("m_false", "message", text="False"),
            _node("e1", "end"),
        ],
        transitions=[
            _trans("s1", "c1"),
            _trans("c1", "m_true", order=1, condition="age > 18"),
            _trans("c1", "m_false", order=2, condition="age == 0"),  # nunca True
            _trans("m_true", "e1"),
            _trans("m_false", "e1"),
        ],
    )

    try:
        run_workflow(workflow, initial_variables={"age": 15})
        assert False, "Debería haber lanzado WorkflowExecutionError"
    except WorkflowExecutionError as e:
        assert "no devolvió True" in str(e) or "Ninguna" in str(e)
        print(f"✅ WorkflowExecutionError detectado")


# ============================================================
# TEST 6 — CONDITION con variable inexistente → ConditionError
# ============================================================

def test_condition_variable_missing():
    print("\n" + "=" * 70)
    print("TEST 6: CONDITION variable inexistente → ConditionError")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("c1", "condition", condition="no_existe > 18"),
            _node("m_true", "message", text="True"),
            _node("m_false", "message", text="False"),
            _node("e1", "end"),
        ],
        transitions=[
            _trans("s1", "c1"),
            _trans("c1", "m_true", order=1, condition="no_existe > 18"),
            _trans("c1", "m_false", order=2, condition="age <= 18"),
            _trans("m_true", "e1"),
            _trans("m_false", "e1"),
        ],
    )

    try:
        run_workflow(workflow, initial_variables={"age": 15})
        assert False, "Debería haber lanzado ConditionError"
    except ConditionError as e:
        assert "no_existe" in str(e)
        print(f"✅ ConditionError detectado")


# ============================================================
# TEST 7 — CONDITION con expresión inválida → ConditionError
# ============================================================

def test_condition_invalid_expression():
    print("\n" + "=" * 70)
    print("TEST 7: CONDITION expresión inválida → ConditionError")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("c1", "condition", condition="age > 18"),
            _node("m_true", "message", text="True"),
            _node("m_false", "message", text="False"),
            _node("e1", "end"),
        ],
        transitions=[
            _trans("s1", "c1"),
            _trans("c1", "m_true", order=1, condition="age 18"),  # inválida
            _trans("c1", "m_false", order=2, condition="age == 0"),
            _trans("m_true", "e1"),
            _trans("m_false", "e1"),
        ],
    )

    try:
        run_workflow(workflow, initial_variables={"age": 15})
        assert False, "Debería haber lanzado ConditionError"
    except ConditionError as e:
        print(f"✅ ConditionError detectado")


# ============================================================
# TEST 8 — CONDITION con string igual
# ============================================================

def test_condition_string_match():
    print("\n" + "=" * 70)
    print("TEST 8: CONDITION con string igual")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("c1", "condition", condition='role == "admin"'),
            _node("m_admin", "message", text="Acceso admin"),
            _node("m_user", "message", text="Acceso usuario"),
            _node("e1", "end"),
        ],
        transitions=[
            _trans("s1", "c1"),
            _trans("c1", "m_admin", order=1, condition='role == "admin"'),
            _trans("c1", "m_user", order=2, condition='role != "admin"'),
            _trans("m_admin", "e1"),
            _trans("m_user", "e1"),
        ],
    )

    result = run_workflow(workflow, initial_variables={"role": "admin"})
    assert result.outputs[0]["text"] == "Acceso admin"
    print(f"✅ String match: '{result.outputs[0]['text']}'")


# ============================================================
# TEST 9 — CONDITION dentro de flujo más grande
# ============================================================

def test_condition_in_larger_flow():
    print("\n" + "=" * 70)
    print("TEST 9: CONDITION dentro de flujo más grande")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("m_welcome", "message", text="Bienvenido"),
            _node("v1", "variable", name="is_adult", value="yes"),
            _node("c1", "condition", condition="age > 18"),
            _node("m_adult", "message", text="Puedes pasar"),
            _node("m_minor", "message", text="Eres menor"),
            _node("r1", "response", text="Fin del proceso"),
            _node("e1", "end"),
        ],
        transitions=[
            _trans("s1", "m_welcome"),
            _trans("m_welcome", "v1"),
            _trans("v1", "c1"),
            _trans("c1", "m_adult", order=1, condition="age > 18"),
            _trans("c1", "m_minor", order=2, condition="age <= 18"),
            _trans("m_adult", "r1"),
            _trans("m_minor", "r1"),
            _trans("r1", "e1"),
        ],
    )

    result = run_workflow(workflow, initial_variables={"age": 30})

    assert result.status == ExecutionStatus.COMPLETED
    assert result.variables.get("is_adult") == "yes"
    texts = [o["text"] for o in result.outputs]
    assert texts == ["Bienvenido", "Puedes pasar", "Fin del proceso"]
    print(f"✅ Flujo completo: {texts}")


# ============================================================
# TEST 10 — Regresión: workflows sin CONDITION siguen funcionando
# ============================================================

def test_regression_no_condition():
    print("\n" + "=" * 70)
    print("TEST 10: Regresión — sin CONDITION")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("m1", "message", text="Hola"),
            _node("q1", "question", text="¿Nombre?", variable="nombre"),
            _node("e1", "end"),
        ],
        transitions=[
            _trans("s1", "m1"),
            _trans("m1", "q1"),
            _trans("q1", "e1"),
        ],
    )

    result = run_workflow(workflow)
    assert result.status == ExecutionStatus.WAITING_INPUT
    assert result.outputs[0]["text"] == "Hola"
    assert result.outputs[1]["text"] == "¿Nombre?"
    print(f"✅ Flujo sin CONDITION sigue OK (WAITING_INPUT en QUESTION)")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.5.6 (Engine + Conditions)")
    print("=" * 70)

    tests = [
        test_condition_true_branch,
        test_condition_false_branch,
        test_condition_multiple_branches,
        test_condition_else_implicit,
        test_condition_no_match,
        test_condition_variable_missing,
        test_condition_invalid_expression,
        test_condition_string_match,
        test_condition_in_larger_flow,
        test_regression_no_condition,
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
