"""
Tests — Subfase 14.5.6
Verifica la interpolación {{variables}} end-to-end en el engine.

Casos cubiertos:
    1.  MESSAGE con {{name}} interpolado
    2.  MESSAGE con variable inexistente → placeholder intacto
    3.  QUESTION con {{name}} interpolado
    4.  VARIABLE con value interpolado
    5.  VARIABLE asigna valor literal (sin placeholders)
    6.  Encadenado: variable → message que la usa
    7.  Interpolación en flujo con CONDITION
    8.  Múltiples interpolaciones en el mismo texto
    9.  Regresión: textos sin placeholders siguen igual
    10. Regresión: WAITING_INPUT sigue funcionando con interpolar
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.workflows.engine import run_workflow
from app.core.workflows.execution import ExecutionStatus


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
# TEST 1 — MESSAGE con {{name}} interpolado
# ============================================================

def test_message_interpolation():
    print("\n" + "=" * 70)
    print("TEST 1: MESSAGE con {{name}}")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("m1", "message", text="Hola {{name}}, bienvenido"),
            _node("e1", "end"),
        ],
        transitions=[_trans("s1", "m1"), _trans("m1", "e1")],
    )

    result = run_workflow(workflow, initial_variables={"name": "Manuel"})
    assert result.outputs[0]["text"] == "Hola Manuel, bienvenido"
    print(f"✅ '{result.outputs[0]['text']}'")


# ============================================================
# TEST 2 — Variable inexistente → placeholder intacto
# ============================================================

def test_missing_variable_placeholder():
    print("\n" + "=" * 70)
    print("TEST 2: Variable inexistente → placeholder intacto")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("m1", "message", text="Hola {{no_existe}}"),
            _node("e1", "end"),
        ],
        transitions=[_trans("s1", "m1"), _trans("m1", "e1")],
    )

    result = run_workflow(workflow, initial_variables={})
    assert result.outputs[0]["text"] == "Hola {{no_existe}}"
    print(f"✅ '{result.outputs[0]['text']}'")


# ============================================================
# TEST 3 — QUESTION con {{name}} interpolado
# ============================================================

def test_question_interpolation():
    print("\n" + "=" * 70)
    print("TEST 3: QUESTION con {{name}}")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("q1", "question", text="Hola {{name}}, ¿cuántos años tienes?", variable="age"),
            _node("e1", "end"),
        ],
        transitions=[_trans("s1", "q1"), _trans("q1", "e1")],
    )

    result = run_workflow(workflow, initial_variables={"name": "Manuel"})
    assert result.status == ExecutionStatus.WAITING_INPUT
    assert result.outputs[0]["text"] == "Hola Manuel, ¿cuántos años tienes?"
    print(f"✅ '{result.outputs[0]['text']}'")


# ============================================================
# TEST 4 — VARIABLE con value interpolado
# ============================================================

def test_variable_value_interpolation():
    print("\n" + "=" * 70)
    print("TEST 4: VARIABLE value interpolado")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("v1", "variable", name="greeting", value="Hola {{name}}"),
            _node("e1", "end"),
        ],
        transitions=[_trans("s1", "v1"), _trans("v1", "e1")],
    )

    result = run_workflow(workflow, initial_variables={"name": "Manuel"})
    assert result.variables["greeting"] == "Hola Manuel"
    print(f"✅ greeting = '{result.variables['greeting']}'")


# ============================================================
# TEST 5 — VARIABLE asigna valor literal
# ============================================================

def test_variable_literal():
    print("\n" + "=" * 70)
    print("TEST 5: VARIABLE valor literal (sin placeholders)")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("v1", "variable", name="status", value="active"),
            _node("e1", "end"),
        ],
        transitions=[_trans("s1", "v1"), _trans("v1", "e1")],
    )

    result = run_workflow(workflow, initial_variables={})
    assert result.variables["status"] == "active"
    print(f"✅ status = '{result.variables['status']}'")


# ============================================================
# TEST 6 — Encadenado: variable → message que la usa
# ============================================================

def test_chained_interpolation():
    print("\n" + "=" * 70)
    print("TEST 6: Encadenado variable → message")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("v1", "variable", name="full_name", value="{{first}} {{last}}"),
            _node("m1", "message", text="Bienvenido, {{full_name}}!"),
            _node("e1", "end"),
        ],
        transitions=[
            _trans("s1", "v1"),
            _trans("v1", "m1"),
            _trans("m1", "e1"),
        ],
    )

    result = run_workflow(
        workflow,
        initial_variables={"first": "Manuel", "last": "García"},
    )
    assert result.variables["full_name"] == "Manuel García"
    assert result.outputs[0]["text"] == "Bienvenido, Manuel García!"
    print(f"✅ full_name = '{result.variables['full_name']}'")
    print(f"✅ output = '{result.outputs[0]['text']}'")


# ============================================================
# TEST 7 — Interpolación + CONDITION
# ============================================================

def test_interpolation_with_condition():
    print("\n" + "=" * 70)
    print("TEST 7: Interpolación con CONDITION")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("m1", "message", text="Hola {{name}}"),
            _node("c1", "condition", condition="age > 18"),
            _node("m_adult", "message", text="{{name}}, eres mayor de edad"),
            _node("m_minor", "message", text="{{name}}, eres menor de edad"),
            _node("e1", "end"),
        ],
        transitions=[
            _trans("s1", "m1"),
            _trans("m1", "c1"),
            _trans("c1", "m_adult", order=1, condition="age > 18"),
            _trans("c1", "m_minor", order=2, condition="age <= 18"),
            _trans("m_adult", "e1"),
            _trans("m_minor", "e1"),
        ],
    )

    result = run_workflow(
        workflow,
        initial_variables={"name": "Manuel", "age": 30},
    )
    texts = [o["text"] for o in result.outputs]
    assert texts == ["Hola Manuel", "Manuel, eres mayor de edad"]
    print(f"✅ Texts: {texts}")


# ============================================================
# TEST 8 — Múltiples interpolaciones en el mismo texto
# ============================================================

def test_multiple_interpolations_in_text():
    print("\n" + "=" * 70)
    print("TEST 8: Múltiples interpolaciones")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("m1", "message", text="{{greeting}}, {{name}}! Tienes {{age}} años."),
            _node("e1", "end"),
        ],
        transitions=[_trans("s1", "m1"), _trans("m1", "e1")],
    )

    result = run_workflow(
        workflow,
        initial_variables={"greeting": "Hola", "name": "Manuel", "age": 30},
    )
    assert result.outputs[0]["text"] == "Hola, Manuel! Tienes 30 años."
    print(f"✅ '{result.outputs[0]['text']}'")


# ============================================================
# TEST 9 — Regresión: textos sin placeholders
# ============================================================

def test_regression_plain_text():
    print("\n" + "=" * 70)
    print("TEST 9: Regresión — texto sin placeholders")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("m1", "message", text="Texto sin variables"),
            _node("e1", "end"),
        ],
        transitions=[_trans("s1", "m1"), _trans("m1", "e1")],
    )

    result = run_workflow(workflow)
    assert result.outputs[0]["text"] == "Texto sin variables"
    print(f"✅ '{result.outputs[0]['text']}'")


# ============================================================
# TEST 10 — WAITING_INPUT con interpolación
# ============================================================

def test_waiting_input_with_interpolation():
    print("\n" + "=" * 70)
    print("TEST 10: WAITING_INPUT con interpolación")
    print("=" * 70)

    workflow = _wf(
        nodes=[
            _node("s1", "start"),
            _node("m1", "message", text="Bienvenido {{name}}"),
            _node("q1", "question", text="{{name}}, ¿qué servicio quieres?", variable="servicio"),
            _node("e1", "end"),
        ],
        transitions=[
            _trans("s1", "m1"),
            _trans("m1", "q1"),
            _trans("q1", "e1"),
        ],
    )

    result = run_workflow(workflow, initial_variables={"name": "Manuel"})
    assert result.status == ExecutionStatus.WAITING_INPUT
    assert result.outputs[0]["text"] == "Bienvenido Manuel"
    assert result.outputs[1]["text"] == "Manuel, ¿qué servicio quieres?"
    assert "servicio" in result.variables
    print(f"✅ Status: WAITING_INPUT")
    print(f"✅ Outputs: {[o['text'] for o in result.outputs]}")
    print(f"✅ Variable 'servicio' esperada")


def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.5.6 (Interpolación end-to-end)")
    print("=" * 70)

    tests = [
        test_message_interpolation,
        test_missing_variable_placeholder,
        test_question_interpolation,
        test_variable_value_interpolation,
        test_variable_literal,
        test_chained_interpolation,
        test_interpolation_with_condition,
        test_multiple_interpolations_in_text,
        test_regression_plain_text,
        test_waiting_input_with_interpolation,
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
