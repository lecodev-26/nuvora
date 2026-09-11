"""
Tests — Subfase 14.5.5
Verifica el Workflow Engine (bucle de ejecución).

Casos cubiertos:
    1. START → END (mínimo)
    2. START → MESSAGE → END
    3. START → MESSAGE → RESPONSE → END
    4. START → QUESTION → END → WAITING_INPUT
    5. START → VARIABLE → END (variables en contexto)
    6. Ciclo infinito → MaxStepsExceeded
    7. Workflow sin START → WorkflowValidationError
    8. Nodo inexistente → WorkflowValidationError
    9. Workflow inválido (END sin transición) → WorkflowValidationError
    10. Multi-tenant (bot_id en contexto)
    11. Nodo con next_node_id explícito
    12. start_node_id explícito
    13. Output acumulado correctamente
    14. steps_used correcto
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.workflows.engine import WorkflowEngine, run_workflow
from app.core.workflows.execution import ExecutionStatus
from app.core.workflows.errors import (
    WorkflowValidationError,
    MaxStepsExceeded,
    WorkflowExecutionError,
)


# ============================================================
# HELPERS
# ============================================================

def _node(node_id, type_, **config):
    """Crea un dict de nodo. config se pasa como kwargs."""
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
# TEST 1 — START → END (mínimo)
# ============================================================

def test_minimal_flow():
    print("\n" + "=" * 70)
    print("TEST 1: START → END (mínimo)")
    print("=" * 70)

    workflow = _wf(
        nodes=[_node("s1", "start"), _node("e1", "end")],
        transitions=[_trans("s1", "e1")],
    )

    result = run_workflow(workflow)

    assert result.status == ExecutionStatus.COMPLETED, f"Status: {result.status}"
    assert result.current_node_id == "e1"
    assert result.steps_used == 2
    assert result.outputs == []
    print(f"✅ COMPLETED en 2 pasos. current_node_id={result.current_node_id}")


# ============================================================
# TEST 2 — START → MESSAGE → END
# ============================================================

def test_message_flow():
    print("\n" + "=" * 70)
    print("TEST 2: START → MESSAGE → END")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("m1", "message", text="¡Hola desde Nuvora!"),
            _node("e1", "end"),
        ],
        transitions=[_trans("s1", "m1"), _trans("m1", "e1")],
    )

    result = run_workflow(workflow)

    assert result.status == ExecutionStatus.COMPLETED
    assert result.steps_used == 3
    assert len(result.outputs) == 1
    assert result.outputs[0]["text"] == "¡Hola desde Nuvora!"
    assert result.outputs[0]["node_id"] == "m1"
    assert result.outputs[0]["type"] == "message"
    print(f"✅ COMPLETED en 3 pasos, 1 output: '{result.outputs[0]['text']}'")


# ============================================================
# TEST 3 — START → MESSAGE → RESPONSE → END
# ============================================================

def test_message_response_flow():
    print("\n" + "=" * 70)
    print("TEST 3: START → MESSAGE → RESPONSE → END")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("m1", "message", text="Bienvenido"),
            _node("r1", "response", text="Gracias por venir"),
            _node("e1", "end"),
        ],
        transitions=[
            _trans("s1", "m1"),
            _trans("m1", "r1"),
            _trans("r1", "e1"),
        ],
    )

    result = run_workflow(workflow)

    assert result.status == ExecutionStatus.COMPLETED
    assert result.steps_used == 4
    assert len(result.outputs) == 2
    assert result.outputs[0]["text"] == "Bienvenido"
    assert result.outputs[1]["text"] == "Gracias por venir"
    print(f"✅ COMPLETED en 4 pasos, 2 outputs")


# ============================================================
# TEST 4 — QUESTION → WAITING_INPUT
# ============================================================

def test_question_waiting_input():
    print("\n" + "=" * 70)
    print("TEST 4: START → QUESTION → WAITING_INPUT")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("q1", "question", text="¿Cuál es tu nombre?", variable="nombre"),
            _node("e1", "end"),
        ],
        transitions=[_trans("s1", "q1"), _trans("q1", "e1")],
    )

    result = run_workflow(workflow)

    assert result.status == ExecutionStatus.WAITING_INPUT
    assert result.current_node_id == "q1"
    assert result.steps_used == 2
    assert len(result.outputs) == 1
    assert result.outputs[0]["text"] == "¿Cuál es tu nombre?"
    print(f"✅ WAITING_INPUT en 2 pasos, pregunta: '{result.outputs[0]['text']}'")


# ============================================================
# TEST 5 — VARIABLE aplica al contexto
# ============================================================

def test_variable_assignment():
    print("\n" + "=" * 70)
    print("TEST 5: START → VARIABLE → END (variables)")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("v1", "variable", name="role", value="admin"),
            _node("e1", "end"),
        ],
        transitions=[_trans("s1", "v1"), _trans("v1", "e1")],
    )

    result = run_workflow(workflow)

    assert result.status == ExecutionStatus.COMPLETED
    assert result.variables.get("role") == "admin", f"Variables: {result.variables}"
    print(f"✅ Variable 'role' = 'admin' aplicada")


# ============================================================
# TEST 6 — Ciclo infinito → MaxStepsExceeded
# ============================================================

def test_max_steps_exceeded():
    print("\n" + "=" * 70)
    print("TEST 6: Ciclo infinito → MaxStepsExceeded")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("m1", "message", text="A"),
            _node("m2", "message", text="B"),
            _node("e1", "end"),
        ],
        transitions=[
            _trans("s1", "m1"),
            _trans("m1", "m2"),
            _trans("m2", "m1"),  # ← ciclo infinito
        ],
    )

    try:
        run_workflow(workflow, max_steps=10)
        assert False, "Debería haber lanzado MaxStepsExceeded"
    except MaxStepsExceeded as e:
        assert e.max_steps == 10
        print(f"✅ MaxStepsExceeded detectado: {e}")


# ============================================================
# TEST 7 — Workflow sin START → WorkflowValidationError
# ============================================================

def test_no_start():
    print("\n" + "=" * 70)
    print("TEST 7: Sin START → WorkflowValidationError")
    print("=" * 70)

    workflow = _wf(
        nodes=[_node("e1", "end")],
        transitions=[],
    )

    try:
        run_workflow(workflow)
        assert False, "Debería haber lanzado WorkflowValidationError"
    except WorkflowValidationError as e:
        assert any("START" in err for err in e.errors)
        print(f"✅ WorkflowValidationError detectado: {e.errors}")


# ============================================================
# TEST 8 — Nodo inexistente en transición → error
# ============================================================

def test_missing_node_in_transition():
    print("\n" + "=" * 70)
    print("TEST 8: Transición a nodo inexistente → WorkflowValidationError")
    print("=" * 70)

    workflow = _wf(
        nodes=[_node("s1", "start"), _node("e1", "end")],
        transitions=[_trans("s1", "no_existe")],
    )

    try:
        run_workflow(workflow)
        assert False, "Debería haber lanzado WorkflowValidationError"
    except WorkflowValidationError as e:
        assert any("inexistente" in err for err in e.errors)
        print(f"✅ WorkflowValidationError detectado: {e.errors}")


# ============================================================
# TEST 9 — Workflow inválido (END sin transición)
# ============================================================

def test_invalid_workflow_missing_end_transition():
    print("\n" + "=" * 70)
    print("TEST 9: Workflow inválido (falta END) → WorkflowValidationError")
    print("=" * 70)

    workflow = _wf(
        nodes=[_node("s1", "start"), _node("m1", "message", text="hola")],
        transitions=[_trans("s1", "m1")],
    )

    try:
        run_workflow(workflow)
        assert False, "Debería haber lanzado WorkflowValidationError"
    except WorkflowValidationError as e:
        assert any("END" in err for err in e.errors)
        print(f"✅ WorkflowValidationError detectado: {e.errors}")


# ============================================================
# TEST 10 — Multi-tenant (bot_id en contexto)
# ============================================================

def test_multi_tenant_bot_id():
    print("\n" + "=" * 70)
    print("TEST 10: Multi-tenant — bot_id en contexto")
    print("=" * 70)

    workflow = _wf(
        nodes=[_node("s1", "start"), _node("e1", "end")],
        transitions=[_trans("s1", "e1")],
    )

    engine = WorkflowEngine()
    result = engine.run(
        workflow_data=workflow,
        bot_id=42,
        workflow_id=7,
        initial_variables={"user": "Manuel"},
    )

    assert result.status == ExecutionStatus.COMPLETED
    assert result.variables.get("user") == "Manuel"
    print(f"✅ Ejecutado con bot_id=42, workflow_id=7, user='Manuel'")


# ============================================================
# TEST 11 — next_node_id explícito del nodo
# ============================================================

def test_explicit_next_node_id():
    print("\n" + "=" * 70)
    print("TEST 11: start_node_id explícito")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("m1", "message", text="skipped"),
            _node("m2", "message", text="directo"),
            _node("e1", "end"),
        ],
        transitions=[
            _trans("s1", "m1"),
            _trans("m1", "e1"),
            _trans("m2", "e1"),
        ],
    )

    result = run_workflow(workflow, start_node_id="m2")

    assert result.status == ExecutionStatus.COMPLETED
    assert result.outputs[0]["text"] == "directo"
    print(f"✅ start_node_id='m2' usado → output '{result.outputs[0]['text']}'")


# ============================================================
# TEST 12 — start_node_id inexistente → error
# ============================================================

def test_start_node_id_missing():
    print("\n" + "=" * 70)
    print("TEST 12: start_node_id inexistente → WorkflowExecutionError")
    print("=" * 70)

    workflow = _wf(
        nodes=[_node("s1", "start"), _node("e1", "end")],
        transitions=[_trans("s1", "e1")],
    )

    try:
        run_workflow(workflow, start_node_id="no_existe")
        assert False, "Debería haber lanzado WorkflowExecutionError"
    except WorkflowExecutionError as e:
        assert "no_existe" in str(e)
        print(f"✅ WorkflowExecutionError detectado: {e}")


# ============================================================
# TEST 13 — Output acumulado correctamente
# ============================================================

def test_outputs_accumulated():
    print("\n" + "=" * 70)
    print("TEST 13: Outputs acumulados")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("m1", "message", text="Uno"),
            _node("m2", "message", text="Dos"),
            _node("m3", "message", text="Tres"),
            _node("e1", "end"),
        ],
        transitions=[
            _trans("s1", "m1"),
            _trans("m1", "m2"),
            _trans("m2", "m3"),
            _trans("m3", "e1"),
        ],
    )

    result = run_workflow(workflow)

    assert result.status == ExecutionStatus.COMPLETED
    assert len(result.outputs) == 3
    texts = [o["text"] for o in result.outputs]
    assert texts == ["Uno", "Dos", "Tres"], f"Texts: {texts}"
    print(f"✅ 3 outputs en orden: {texts}")


# ============================================================
# TEST 14 — steps_used correcto
# ============================================================

def test_steps_count():
    print("\n" + "=" * 70)
    print("TEST 14: steps_used correcto")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("m1", "message", text="a"),
            _node("m2", "message", text="b"),
            _node("m3", "message", text="c"),
            _node("e1", "end"),
        ],
        transitions=[
            _trans("s1", "m1"),
            _trans("m1", "m2"),
            _trans("m2", "m3"),
            _trans("m3", "e1"),
        ],
    )

    result = run_workflow(workflow)

    assert result.steps_used == 5, f"steps_used={result.steps_used}, esperado 5"
    print(f"✅ steps_used={result.steps_used}")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.5.5 (Workflow Engine)")
    print("=" * 70)

    tests = [
        test_minimal_flow,
        test_message_flow,
        test_message_response_flow,
        test_question_waiting_input,
        test_variable_assignment,
        test_max_steps_exceeded,
        test_no_start,
        test_missing_node_in_transition,
        test_invalid_workflow_missing_end_transition,
        test_multi_tenant_bot_id,
        test_explicit_next_node_id,
        test_start_node_id_missing,
        test_outputs_accumulated,
        test_steps_count,
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
