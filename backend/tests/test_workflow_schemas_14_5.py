"""
Tests — Subfase 14.5.2
Verifica los schemas Pydantic de workflows.
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import ValidationError

from app.models.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowListResponse,
    WorkflowDetailResponse,
    WorkflowNodeCreate,
    WorkflowNodeUpdate,
    WorkflowNodeResponse,
    WorkflowTransitionCreate,
    WorkflowTransitionUpdate,
    WorkflowTransitionResponse,
    WorkflowRunRequest,
    WorkflowRunResponse,
    WorkflowRunOutput,
)


# ============================================================
# TESTS — WorkflowNodeCreate
# ============================================================

def test_node_create_minimal():
    print("\n" + "=" * 70)
    print("TEST 1: WorkflowNodeCreate mínimo")
    print("=" * 70)
    node = WorkflowNodeCreate(node_id="start_1", type="start")
    assert node.node_id == "start_1"
    assert node.type == "start"
    assert node.name is None
    assert node.config is None
    print(f"✅ Node creado: {node.node_id} ({node.type})")


def test_node_create_with_config():
    print("\n" + "=" * 70)
    print("TEST 2: WorkflowNodeCreate con config")
    print("=" * 70)
    node = WorkflowNodeCreate(
        node_id="msg_1",
        type="message",
        name="Mensaje bienvenida",
        config={"text": "Hola {{name}}"},
    )
    assert node.config == {"text": "Hola {{name}}"}
    print(f"✅ Node con config: {node.config}")


def test_node_create_invalid_type():
    print("\n" + "=" * 70)
    print("TEST 3: WorkflowNodeCreate con tipo inválido")
    print("=" * 70)
    try:
        WorkflowNodeCreate(node_id="x", type="invalid_type")
        assert False, "Debería haber fallado"
    except ValidationError as e:
        assert "type" in str(e).lower() or "literal" in str(e).lower()
        print(f"✅ Tipo inválido detectado correctamente")


def test_node_create_missing_required():
    print("\n" + "=" * 70)
    print("TEST 4: WorkflowNodeCreate sin campos obligatorios")
    print("=" * 70)
    try:
        WorkflowNodeCreate(type="start")  # sin node_id
        assert False, "Debería haber fallado"
    except ValidationError:
        print(f"✅ Campo obligatorio detectado")


# ============================================================
# TESTS — WorkflowTransitionCreate
# ============================================================

def test_transition_create_minimal():
    print("\n" + "=" * 70)
    print("TEST 5: WorkflowTransitionCreate mínimo")
    print("=" * 70)
    t = WorkflowTransitionCreate(from_node_id="start_1", to_node_id="end_1")
    assert t.from_node_id == "start_1"
    assert t.to_node_id == "end_1"
    assert t.condition is None
    assert t.label is None
    assert t.order == 0
    print(f"✅ Transition: {t.from_node_id} → {t.to_node_id}")


def test_transition_create_with_condition():
    print("\n" + "=" * 70)
    print("TEST 6: WorkflowTransitionCreate con condición")
    print("=" * 70)
    t = WorkflowTransitionCreate(
        from_node_id="cond_1",
        to_node_id="msg_ok",
        condition='name == "Manuel"',
        label="true",
        order=1,
    )
    assert t.condition == 'name == "Manuel"'
    assert t.label == "true"
    assert t.order == 1
    print(f"✅ Transition con condición: {t.condition}")


# ============================================================
# TESTS — WorkflowCreate
# ============================================================

def test_workflow_create_minimal():
    print("\n" + "=" * 70)
    print("TEST 7: WorkflowCreate mínimo")
    print("=" * 70)
    wf = WorkflowCreate(name="Mi workflow")
    assert wf.name == "Mi workflow"
    assert wf.status == "draft"
    assert wf.trigger == "manual"
    assert wf.nodes == []
    assert wf.transitions == []
    print(f"✅ Workflow mínimo: {wf.name} (status={wf.status})")


def test_workflow_create_full():
    print("\n" + "=" * 70)
    print("TEST 8: WorkflowCreate completo")
    print("=" * 70)
    wf = WorkflowCreate(
        name="WF completo",
        description="Test",
        status="active",
        trigger="message",
        entry_node_id="start_1",
        meta={"key": "value"},
        nodes=[
            WorkflowNodeCreate(node_id="start_1", type="start"),
            WorkflowNodeCreate(
                node_id="msg_1",
                type="message",
                config={"text": "Hola"},
            ),
            WorkflowNodeCreate(node_id="end_1", type="end"),
        ],
        transitions=[
            WorkflowTransitionCreate(from_node_id="start_1", to_node_id="msg_1"),
            WorkflowTransitionCreate(from_node_id="msg_1", to_node_id="end_1"),
        ],
    )
    assert len(wf.nodes) == 3
    assert len(wf.transitions) == 2
    assert wf.entry_node_id == "start_1"
    print(f"✅ Workflow completo: {len(wf.nodes)} nodos, {len(wf.transitions)} transiciones")


def test_workflow_create_invalid_status():
    print("\n" + "=" * 70)
    print("TEST 9: WorkflowCreate con status inválido")
    print("=" * 70)
    try:
        WorkflowCreate(name="x", status="invalid")
        assert False, "Debería haber fallado"
    except ValidationError:
        print(f"✅ Status inválido detectado")


# ============================================================
# TESTS — WorkflowUpdate
# ============================================================

def test_workflow_update_partial():
    print("\n" + "=" * 70)
    print("TEST 10: WorkflowUpdate parcial")
    print("=" * 70)
    wf = WorkflowUpdate(name="Nuevo nombre")
    assert wf.name == "Nuevo nombre"
    assert wf.status is None
    assert wf.trigger is None
    print(f"✅ Update parcial: solo name")


def test_workflow_update_empty():
    print("\n" + "=" * 70)
    print("TEST 11: WorkflowUpdate vacío (todos opcionales)")
    print("=" * 70)
    wf = WorkflowUpdate()
    assert wf.name is None
    assert wf.status is None
    print(f"✅ Update vacío válido")


# ============================================================
# TESTS — WorkflowRunRequest / Response
# ============================================================

def test_run_request_defaults():
    print("\n" + "=" * 70)
    print("TEST 12: WorkflowRunRequest defaults")
    print("=" * 70)
    req = WorkflowRunRequest()
    assert req.initial_variables == {}
    assert req.max_steps == 100
    print(f"✅ RunRequest: max_steps={req.max_steps}")


def test_run_request_custom():
    print("\n" + "=" * 70)
    print("TEST 13: WorkflowRunRequest con datos")
    print("=" * 70)
    req = WorkflowRunRequest(
        initial_variables={"name": "Manuel"},
        max_steps=50,
    )
    assert req.initial_variables == {"name": "Manuel"}
    assert req.max_steps == 50
    print(f"✅ RunRequest custom OK")


def test_run_request_invalid_max_steps():
    print("\n" + "=" * 70)
    print("TEST 14: WorkflowRunRequest con max_steps inválido")
    print("=" * 70)
    try:
        WorkflowRunRequest(max_steps=0)
        assert False, "Debería haber fallado"
    except ValidationError:
        print(f"✅ max_steps=0 rechazado")

    try:
        WorkflowRunRequest(max_steps=99999)
        assert False, "Debería haber fallado"
    except ValidationError:
        print(f"✅ max_steps=99999 rechazado")


def test_run_response_completed():
    print("\n" + "=" * 70)
    print("TEST 15: WorkflowRunResponse completed")
    print("=" * 70)
    res = WorkflowRunResponse(
        status="completed",
        outputs=[
            WorkflowRunOutput(node_id="msg_1", type="message", text="Hola"),
            WorkflowRunOutput(node_id="end_1", type="end"),
        ],
        variables={"name": "Manuel"},
        current_node_id="end_1",
        steps_used=3,
    )
    assert res.status == "completed"
    assert len(res.outputs) == 2
    assert res.steps_used == 3
    print(f"✅ RunResponse completed OK")


def test_run_response_waiting_input():
    print("\n" + "=" * 70)
    print("TEST 16: WorkflowRunResponse waiting_input")
    print("=" * 70)
    res = WorkflowRunResponse(
        status="waiting_input",
        outputs=[WorkflowRunOutput(node_id="q_1", type="question", text="¿Cómo te llamas?")],
        current_node_id="q_1",
        steps_used=2,
    )
    assert res.status == "waiting_input"
    assert res.current_node_id == "q_1"
    print(f"✅ RunResponse waiting_input OK")


def test_run_response_invalid_status():
    print("\n" + "=" * 70)
    print("TEST 17: WorkflowRunResponse con status inválido")
    print("=" * 70)
    try:
        WorkflowRunResponse(status="invalid")
        assert False, "Debería haber fallado"
    except ValidationError:
        print(f"✅ Status inválido rechazado")


# ============================================================
# TESTS — Modelos de respuesta
# ============================================================

def test_workflow_response_basic():
    print("\n" + "=" * 70)
    print("TEST 18: WorkflowResponse básica")
    print("=" * 70)
    res = WorkflowResponse(
        id=1,
        bot_id=2,
        name="WF test",
        status="draft",
        trigger="manual",
        created_at=datetime.now(),
    )
    assert res.id == 1
    assert res.bot_id == 2
    assert res.version == 1
    print(f"✅ WorkflowResponse: id={res.id}, bot_id={res.bot_id}")


def test_workflow_list_response():
    print("\n" + "=" * 70)
    print("TEST 19: WorkflowListResponse")
    print("=" * 70)
    wf1 = WorkflowResponse(
        id=1, bot_id=1, name="WF1", status="draft", trigger="manual",
        created_at=datetime.now(),
    )
    wf2 = WorkflowResponse(
        id=2, bot_id=1, name="WF2", status="active", trigger="message",
        created_at=datetime.now(),
    )
    lst = WorkflowListResponse(workflows=[wf1, wf2], total=2)
    assert lst.total == 2
    assert len(lst.workflows) == 2
    print(f"✅ ListResponse: {lst.total} workflows")


def test_workflow_detail_response():
    print("\n" + "=" * 70)
    print("TEST 20: WorkflowDetailResponse con nodos y transiciones")
    print("=" * 70)
    node = WorkflowNodeResponse(
        id=1, workflow_id=1, node_id="start_1", type="start",
        created_at=datetime.now(),
    )
    trans = WorkflowTransitionResponse(
        id=1, workflow_id=1, from_node_id="start_1", to_node_id="end_1",
        order=0, created_at=datetime.now(),
    )
    detail = WorkflowDetailResponse(
        id=1, bot_id=1, name="WF detail", status="draft", trigger="manual",
        created_at=datetime.now(),
        nodes=[node],
        transitions=[trans],
    )
    assert len(detail.nodes) == 1
    assert len(detail.transitions) == 1
    print(f"✅ DetailResponse: 1 nodo, 1 transición")


# ============================================================
# TESTS — Node/Transition Update
# ============================================================

def test_node_update_partial():
    print("\n" + "=" * 70)
    print("TEST 21: WorkflowNodeUpdate parcial")
    print("=" * 70)
    n = WorkflowNodeUpdate(name="Nuevo nombre")
    assert n.name == "Nuevo nombre"
    assert n.type is None
    assert n.config is None
    print(f"✅ NodeUpdate parcial")


def test_transition_update_partial():
    print("\n" + "=" * 70)
    print("TEST 22: WorkflowTransitionUpdate parcial")
    print("=" * 70)
    t = WorkflowTransitionUpdate(condition='x > 5')
    assert t.condition == 'x > 5'
    assert t.label is None
    assert t.order is None
    print(f"✅ TransitionUpdate parcial")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.5.2 (Workflow Schemas)")
    print("=" * 70)

    tests = [
        test_node_create_minimal,
        test_node_create_with_config,
        test_node_create_invalid_type,
        test_node_create_missing_required,
        test_transition_create_minimal,
        test_transition_create_with_condition,
        test_workflow_create_minimal,
        test_workflow_create_full,
        test_workflow_create_invalid_status,
        test_workflow_update_partial,
        test_workflow_update_empty,
        test_run_request_defaults,
        test_run_request_custom,
        test_run_request_invalid_max_steps,
        test_run_response_completed,
        test_run_response_waiting_input,
        test_run_response_invalid_status,
        test_workflow_response_basic,
        test_workflow_list_response,
        test_workflow_detail_response,
        test_node_update_partial,
        test_transition_update_partial,
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
