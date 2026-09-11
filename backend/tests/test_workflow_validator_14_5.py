"""
Tests — Subfase 14.5.4
Verifica el Workflow Validator.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.workflows import (
    WorkflowValidator,
    validate_workflow,
    WorkflowValidationError,
    VALID_NODE_TYPES,
)


# ============================================================
# HELPERS
# ============================================================

def _wf(nodes, transitions):
    """Crea un dict de workflow."""
    return {"nodes": nodes, "transitions": transitions}


def _node(node_id, type_, **config):
    return {"node_id": node_id, "type": type_, "config": config or None}


def _trans(from_, to_, condition=None, label=None, order=0):
    return {
        "from_node_id": from_,
        "to_node_id": to_,
        "condition": condition,
        "label": label,
        "order": order,
    }


# ============================================================
# TESTS — Validación correcta
# ============================================================

def test_minimal_valid_workflow():
    print("\n" + "=" * 70)
    print("TEST 1: Workflow mínimo válido (START → END)")
    print("=" * 70)
    wf = _wf(
        nodes=[_node("s1", "start"), _node("e1", "end")],
        transitions=[_trans("s1", "e1")],
    )
    validate_workflow(wf)
    print(f"✅ Validación OK")


def test_full_valid_workflow():
    print("\n" + "=" * 70)
    print("TEST 2: Workflow completo válido")
    print("=" * 70)
    wf = _wf(
        nodes=[
            _node("s1", "start"),
            _node("m1", "message", text="Hola"),
            _node("q1", "question", text="¿Nombre?", variable="name"),
            _node("v1", "variable", name="x", value="1"),
            _node("c1", "condition", condition="x > 0"),
            _node("r1", "response", text="Fin OK"),
            _node("e1", "end"),
        ],
        transitions=[
            _trans("s1", "m1"),
            _trans("m1", "q1"),
            _trans("q1", "v1"),
            _trans("v1", "c1"),
            _trans("c1", "r1", condition="x > 0", label="true"),
            _trans("c1", "e1", condition="x <= 0", label="false"),
            _trans("r1", "e1"),
        ],
    )
    validate_workflow(wf)
    print(f"✅ Validación OK (7 nodos, 7 transiciones)")


def test_valid_types_set():
    print("\n" + "=" * 70)
    print("TEST 3: VALID_NODE_TYPES tiene los 7 tipos")
    print("=" * 70)
    expected = {"start", "message", "question", "condition", "variable", "response", "end"}
    assert VALID_NODE_TYPES == expected
    print(f"✅ {len(VALID_NODE_TYPES)} tipos: {sorted(VALID_NODE_TYPES)}")


# ============================================================
# TESTS — Falta START
# ============================================================

def test_no_start():
    print("\n" + "=" * 70)
    print("TEST 4: Falta START")
    print("=" * 70)
    wf = _wf(
        nodes=[_node("e1", "end")],
        transitions=[],
    )
    try:
        validate_workflow(wf)
        assert False, "Debería haber fallado"
    except WorkflowValidationError as e:
        assert any("START" in err for err in e.errors)
        print(f"✅ Detectado: {e.errors}")


def test_multiple_starts():
    print("\n" + "=" * 70)
    print("TEST 5: Múltiples START")
    print("=" * 70)
    wf = _wf(
        nodes=[_node("s1", "start"), _node("s2", "start"), _node("e1", "end")],
        transitions=[_trans("s1", "e1"), _trans("s2", "e1")],
    )
    try:
        validate_workflow(wf)
        assert False, "Debería haber fallado"
    except WorkflowValidationError as e:
        assert any("START" in err and "exactamente 1" in err for err in e.errors)
        print(f"✅ Detectado: {e.errors}")


# ============================================================
# TESTS — Falta END
# ============================================================

def test_no_end():
    print("\n" + "=" * 70)
    print("TEST 6: Falta END")
    print("=" * 70)
    wf = _wf(
        nodes=[_node("s1", "start")],
        transitions=[],
    )
    try:
        validate_workflow(wf)
        assert False, "Debería haber fallado"
    except WorkflowValidationError as e:
        assert any("END" in err for err in e.errors)
        print(f"✅ Detectado: {e.errors}")


# ============================================================
# TESTS — node_id duplicados
# ============================================================

def test_duplicate_node_ids():
    print("\n" + "=" * 70)
    print("TEST 7: node_id duplicados")
    print("=" * 70)
    wf = _wf(
        nodes=[
            _node("s1", "start"),
            _node("dup", "message", text="A"),
            _node("dup", "message", text="B"),
            _node("e1", "end"),
        ],
        transitions=[
            _trans("s1", "dup"),
            _trans("dup", "e1"),
        ],
    )
    try:
        validate_workflow(wf)
        assert False, "Debería haber fallado"
    except WorkflowValidationError as e:
        assert any("duplicado" in err for err in e.errors)
        print(f"✅ Detectado: {e.errors}")


# ============================================================
# TESTS — Tipos inválidos
# ============================================================

def test_invalid_node_type():
    print("\n" + "=" * 70)
    print("TEST 8: Tipo de nodo inválido")
    print("=" * 70)
    wf = _wf(
        nodes=[_node("s1", "start"), _node("x1", "weird_type"), _node("e1", "end")],
        transitions=[_trans("s1", "e1")],
    )
    try:
        validate_workflow(wf)
        assert False, "Debería haber fallado"
    except WorkflowValidationError as e:
        assert any("tipo inválido" in err for err in e.errors)
        print(f"✅ Detectado: {e.errors}")


# ============================================================
# TESTS — Config según tipo
# ============================================================

def test_message_without_text():
    print("\n" + "=" * 70)
    print("TEST 9: MESSAGE sin text")
    print("=" * 70)
    wf = _wf(
        nodes=[_node("s1", "start"), _node("m1", "message"), _node("e1", "end")],
        transitions=[_trans("s1", "m1"), _trans("m1", "e1")],
    )
    try:
        validate_workflow(wf)
        assert False, "Debería haber fallado"
    except WorkflowValidationError as e:
        assert any("'text'" in err for err in e.errors)
        print(f"✅ Detectado: {e.errors}")


def test_question_without_variable():
    print("\n" + "=" * 70)
    print("TEST 10: QUESTION sin variable")
    print("=" * 70)
    wf = _wf(
        nodes=[
            _node("s1", "start"),
            _node("q1", "question", text="¿?"),
            _node("e1", "end"),
        ],
        transitions=[_trans("s1", "q1"), _trans("q1", "e1")],
    )
    try:
        validate_workflow(wf)
        assert False, "Debería haber fallado"
    except WorkflowValidationError as e:
        assert any("'variable'" in err for err in e.errors)
        print(f"✅ Detectado: {e.errors}")


def test_variable_without_name():
    print("\n" + "=" * 70)
    print("TEST 11: VARIABLE sin name")
    print("=" * 70)
    wf = _wf(
        nodes=[
            _node("s1", "start"),
            _node("v1", "variable", value="x"),
            _node("e1", "end"),
        ],
        transitions=[_trans("s1", "v1"), _trans("v1", "e1")],
    )
    try:
        validate_workflow(wf)
        assert False, "Debería haber fallado"
    except WorkflowValidationError as e:
        assert any("'name'" in err for err in e.errors)
        print(f"✅ Detectado: {e.errors}")


def test_condition_without_condition():
    print("\n" + "=" * 70)
    print("TEST 12: CONDITION sin condition")
    print("=" * 70)
    wf = _wf(
        nodes=[
            _node("s1", "start"),
            _node("c1", "condition"),
            _node("e1", "end"),
            _node("e2", "end"),
        ],
        transitions=[
            _trans("s1", "c1"),
            _trans("c1", "e1", label="true"),
            _trans("c1", "e2", label="false"),
        ],
    )
    try:
        validate_workflow(wf)
        assert False, "Debería haber fallado"
    except WorkflowValidationError as e:
        assert any("'condition'" in err for err in e.errors)
        print(f"✅ Detectado: {e.errors}")


# ============================================================
# TESTS — Transiciones rotas
# ============================================================

def test_transition_from_missing_node():
    print("\n" + "=" * 70)
    print("TEST 13: Transición desde nodo inexistente")
    print("=" * 70)
    wf = _wf(
        nodes=[_node("s1", "start"), _node("e1", "end")],
        transitions=[_trans("s1", "e1"), _trans("nope", "e1")],
    )
    try:
        validate_workflow(wf)
        assert False, "Debería haber fallado"
    except WorkflowValidationError as e:
        assert any("inexistente" in err for err in e.errors)
        print(f"✅ Detectado: {e.errors}")


def test_transition_to_missing_node():
    print("\n" + "=" * 70)
    print("TEST 14: Transición hacia nodo inexistente")
    print("=" * 70)
    wf = _wf(
        nodes=[_node("s1", "start"), _node("e1", "end")],
        transitions=[_trans("s1", "nope")],
    )
    try:
        validate_workflow(wf)
        assert False, "Debería haber fallado"
    except WorkflowValidationError as e:
        assert any("inexistente" in err for err in e.errors)
        print(f"✅ Detectado: {e.errors}")


# ============================================================
# TESTS — CONDITION ≥ 2 transiciones
# ============================================================

def test_condition_with_one_transition():
    print("\n" + "=" * 70)
    print("TEST 15: CONDITION con 1 transición (mínimo 2)")
    print("=" * 70)
    wf = _wf(
        nodes=[
            _node("s1", "start"),
            _node("c1", "condition", condition="x > 0"),
            _node("e1", "end"),
        ],
        transitions=[_trans("s1", "c1"), _trans("c1", "e1", label="true")],
    )
    try:
        validate_workflow(wf)
        assert False, "Debería haber fallado"
    except WorkflowValidationError as e:
        assert any("CONDITION" in err and "mínimo 2" in err for err in e.errors)
        print(f"✅ Detectado: {e.errors}")


# ============================================================
# TESTS — END sin transiciones salientes
# ============================================================

def test_end_with_outgoing_transition():
    print("\n" + "=" * 70)
    print("TEST 16: END con transición saliente")
    print("=" * 70)
    wf = _wf(
        nodes=[_node("s1", "start"), _node("e1", "end"), _node("e2", "end")],
        transitions=[_trans("s1", "e1"), _trans("e1", "e2")],
    )
    try:
        validate_workflow(wf)
        assert False, "Debería haber fallado"
    except WorkflowValidationError as e:
        assert any("END" in err and "salientes" in err for err in e.errors)
        print(f"✅ Detectado: {e.errors}")


# ============================================================
# TESTS — START sin transiciones entrantes
# ============================================================

def test_start_with_incoming_transition():
    print("\n" + "=" * 70)
    print("TEST 17: START con transición entrante")
    print("=" * 70)
    wf = _wf(
        nodes=[_node("s1", "start"), _node("m1", "message", text="x"), _node("e1", "end")],
        transitions=[_trans("s1", "m1"), _trans("m1", "s1"), _trans("m1", "e1")],
    )
    try:
        validate_workflow(wf)
        assert False, "Debería haber fallado"
    except WorkflowValidationError as e:
        assert any("START" in err and "entrantes" in err for err in e.errors)
        print(f"✅ Detectado: {e.errors}")


# ============================================================
# TESTS — Múltiples errores a la vez
# ============================================================

def test_multiple_errors():
    print("\n" + "=" * 70)
    print("TEST 18: Workflow con múltiples errores")
    print("=" * 70)
    wf = _wf(
        nodes=[
            # Falta START
            # Falta END
            _node("m1", "message"),  # sin text
            _node("x1", "weird"),    # tipo inválido
        ],
        transitions=[
            _trans("m1", "nope"),    # to inexistente
        ],
    )
    try:
        validate_workflow(wf)
        assert False, "Debería haber fallado"
    except WorkflowValidationError as e:
        assert len(e.errors) >= 4
        print(f"✅ Detectados {len(e.errors)} errores:")
        for err in e.errors:
            print(f"     - {err}")


# ============================================================
# TESTS — Empty workflow
# ============================================================

def test_empty_workflow():
    print("\n" + "=" * 70)
    print("TEST 19: Workflow vacío")
    print("=" * 70)
    wf = _wf(nodes=[], transitions=[])
    try:
        validate_workflow(wf)
        assert False, "Debería haber fallado"
    except WorkflowValidationError as e:
        assert any("START" in err for err in e.errors)
        assert any("END" in err for err in e.errors)
        print(f"✅ Detectado: {e.errors}")


# ============================================================
# TESTS — WorkflowValidator explícito
# ============================================================

def test_validator_instance_direct():
    print("\n" + "=" * 70)
    print("TEST 20: WorkflowValidator instancia directa")
    print("=" * 70)
    validator = WorkflowValidator()
    wf = _wf(
        nodes=[_node("s1", "start"), _node("e1", "end")],
        transitions=[_trans("s1", "e1")],
    )
    validator.validate(wf)  # No debe lanzar
    print(f"✅ WorkflowValidator.validate() OK")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.5.4 (Workflow Validator)")
    print("=" * 70)

    tests = [
        test_minimal_valid_workflow,
        test_full_valid_workflow,
        test_valid_types_set,
        test_no_start,
        test_multiple_starts,
        test_no_end,
        test_duplicate_node_ids,
        test_invalid_node_type,
        test_message_without_text,
        test_question_without_variable,
        test_variable_without_name,
        test_condition_without_condition,
        test_transition_from_missing_node,
        test_transition_to_missing_node,
        test_condition_with_one_transition,
        test_end_with_outgoing_transition,
        test_start_with_incoming_transition,
        test_multiple_errors,
        test_empty_workflow,
        test_validator_instance_direct,
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
