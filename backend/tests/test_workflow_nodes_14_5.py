"""
Tests — Subfase 14.5.3
Verifica Node architecture + ExecutionContext.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dataclasses import dataclass

from app.core.workflows import (
    ExecutionStatus,
    ExecutionContext,
    ExecutionResult,
    NodeResult,
)
from app.core.workflows.nodes import (
    NODE_REGISTRY,
    get_node_handler,
    BaseNode,
)
from app.core.workflows.nodes.start import StartNode
from app.core.workflows.nodes.message import MessageNode
from app.core.workflows.nodes.question import QuestionNode
from app.core.workflows.nodes.condition import ConditionNode
from app.core.workflows.nodes.variable import VariableNode
from app.core.workflows.nodes.response import ResponseNode
from app.core.workflows.nodes.end import EndNode
from app.core.workflows.errors import (
    WorkflowError,
    MaxStepsExceeded,
    NodeExecutionError,
    ConditionError,
    WorkflowValidationError,
)


# ============================================================
# Stub de nodo para tests (simula WorkflowNode de SQLAlchemy)
# ============================================================

@dataclass
class NodeStub:
    node_id: str
    type: str
    config: str = None


# ============================================================
# TESTS — ExecutionStatus
# ============================================================

def test_execution_status_values():
    print("\n" + "=" * 70)
    print("TEST 1: ExecutionStatus tiene 4 valores")
    print("=" * 70)
    assert ExecutionStatus.RUNNING.value == "running"
    assert ExecutionStatus.WAITING_INPUT.value == "waiting_input"
    assert ExecutionStatus.COMPLETED.value == "completed"
    assert ExecutionStatus.FAILED.value == "failed"
    print(f"✅ 4 estados: running, waiting_input, completed, failed")


# ============================================================
# TESTS — ExecutionContext
# ============================================================

def test_execution_context_creation():
    print("\n" + "=" * 70)
    print("TEST 2: ExecutionContext se crea correctamente")
    print("=" * 70)
    ctx = ExecutionContext(bot_id=1, workflow_id=2)
    assert ctx.bot_id == 1
    assert ctx.workflow_id == 2
    assert ctx.variables == {}
    assert ctx.steps == 0
    assert ctx.history == []
    assert ctx.current_node_id is None
    print(f"✅ Context creado: bot_id={ctx.bot_id}, workflow_id={ctx.workflow_id}")


def test_execution_context_register_step():
    print("\n" + "=" * 70)
    print("TEST 3: register_step acumula pasos")
    print("=" * 70)
    ctx = ExecutionContext(bot_id=1, workflow_id=1)
    ctx.register_step("start_1", "start")
    ctx.register_step("msg_1", "message", "Hola")
    ctx.register_step("end_1", "end")

    assert ctx.steps == 3
    assert ctx.current_node_id == "end_1"
    assert len(ctx.history) == 3
    assert ctx.history[0]["node_id"] == "start_1"
    assert ctx.history[1]["output"] == "Hola"
    print(f"✅ 3 pasos registrados, current={ctx.current_node_id}")


# ============================================================
# TESTS — NodeResult
# ============================================================

def test_node_result_defaults():
    print("\n" + "=" * 70)
    print("TEST 4: NodeResult defaults")
    print("=" * 70)
    r = NodeResult()
    assert r.output is None
    assert r.next_node_id is None
    assert r.variables_update == {}
    assert r.status == ExecutionStatus.RUNNING
    print(f"✅ NodeResult defaults OK")


# ============================================================
# TESTS — ExecutionResult
# ============================================================

def test_execution_result_to_dict():
    print("\n" + "=" * 70)
    print("TEST 5: ExecutionResult.to_dict()")
    print("=" * 70)
    r = ExecutionResult(
        status=ExecutionStatus.COMPLETED,
        outputs=[{"node_id": "msg_1", "type": "message", "text": "Hola"}],
        variables={"name": "Manuel"},
        current_node_id="end_1",
        steps_used=3,
    )
    d = r.to_dict()
    assert d["status"] == "completed"
    assert len(d["outputs"]) == 1
    assert d["variables"] == {"name": "Manuel"}
    assert d["steps_used"] == 3
    print(f"✅ to_dict OK: {list(d.keys())}")


# ============================================================
# TESTS — NODE_REGISTRY
# ============================================================

def test_registry_has_all_node_types():
    print("\n" + "=" * 70)
    print("TEST 6: NODE_REGISTRY tiene los 7 tipos")
    print("=" * 70)
    expected = {"start", "message", "question", "condition", "variable", "response", "end"}
    assert set(NODE_REGISTRY.keys()) == expected
    print(f"✅ {len(NODE_REGISTRY)} tipos: {sorted(NODE_REGISTRY.keys())}")


def test_get_node_handler_ok():
    print("\n" + "=" * 70)
    print("TEST 7: get_node_handler devuelve el handler correcto")
    print("=" * 70)
    assert isinstance(get_node_handler("start"), StartNode)
    assert isinstance(get_node_handler("message"), MessageNode)
    assert isinstance(get_node_handler("question"), QuestionNode)
    assert isinstance(get_node_handler("condition"), ConditionNode)
    assert isinstance(get_node_handler("variable"), VariableNode)
    assert isinstance(get_node_handler("response"), ResponseNode)
    assert isinstance(get_node_handler("end"), EndNode)
    print(f"✅ Todos los handlers devueltos correctamente")


def test_get_node_handler_unknown():
    print("\n" + "=" * 70)
    print("TEST 8: get_node_handler con tipo desconocido → ValueError")
    print("=" * 70)
    try:
        get_node_handler("nope")
        assert False, "Debería haber fallado"
    except ValueError as e:
        assert "desconocido" in str(e).lower() or "unknown" in str(e).lower()
        print(f"✅ ValueError correcto: {e}")


def test_all_handlers_are_basenode():
    print("\n" + "=" * 70)
    print("TEST 9: Todos los handlers heredan de BaseNode")
    print("=" * 70)
    for node_type, handler in NODE_REGISTRY.items():
        assert isinstance(handler, BaseNode)
        assert handler.node_type == node_type
    print(f"✅ Todos heredan de BaseNode")


# ============================================================
# TESTS — Node handlers individuales
# ============================================================

def test_start_node_executes():
    print("\n" + "=" * 70)
    print("TEST 10: StartNode.execute")
    print("=" * 70)
    node = NodeStub(node_id="start_1", type="start")
    ctx = ExecutionContext(bot_id=1, workflow_id=1)
    result = StartNode().execute(node, ctx)
    assert result.status == ExecutionStatus.RUNNING
    assert result.output is None
    assert result.next_node_id is None
    print(f"✅ StartNode OK")


def test_message_node_executes():
    print("\n" + "=" * 70)
    print("TEST 11: MessageNode.execute")
    print("=" * 70)
    node = NodeStub(
        node_id="msg_1",
        type="message",
        config='{"text": "Hola mundo"}',
    )
    ctx = ExecutionContext(bot_id=1, workflow_id=1)
    result = MessageNode().execute(node, ctx)
    assert result.status == ExecutionStatus.RUNNING
    assert result.output == "Hola mundo"
    print(f"✅ MessageNode OK: '{result.output}'")


def test_message_node_empty_config():
    print("\n" + "=" * 70)
    print("TEST 12: MessageNode sin config")
    print("=" * 70)
    node = NodeStub(node_id="msg_1", type="message", config=None)
    ctx = ExecutionContext(bot_id=1, workflow_id=1)
    result = MessageNode().execute(node, ctx)
    assert result.output == ""
    print(f"✅ MessageNode sin config OK")


def test_message_node_invalid_json():
    print("\n" + "=" * 70)
    print("TEST 13: MessageNode con JSON inválido")
    print("=" * 70)
    node = NodeStub(node_id="msg_1", type="message", config="not json")
    ctx = ExecutionContext(bot_id=1, workflow_id=1)
    result = MessageNode().execute(node, ctx)
    assert result.output == ""
    print(f"✅ MessageNode con JSON inválido no rompe")


def test_question_node_executes():
    print("\n" + "=" * 70)
    print("TEST 14: QuestionNode.execute → WAITING_INPUT")
    print("=" * 70)
    node = NodeStub(
        node_id="q_1",
        type="question",
        config='{"text": "¿Cómo te llamas?", "variable": "name"}',
    )
    ctx = ExecutionContext(bot_id=1, workflow_id=1)
    result = QuestionNode().execute(node, ctx)
    assert result.status == ExecutionStatus.WAITING_INPUT
    assert result.output == "¿Cómo te llamas?"
    assert result.variables_update == {"name": None}
    print(f"✅ QuestionNode OK: status={result.status.value}")


def test_condition_node_executes_stub():
    print("\n" + "=" * 70)
    print("TEST 15: ConditionNode.execute (stub, lógica real en 14.5.6)")
    print("=" * 70)
    node = NodeStub(
        node_id="cond_1",
        type="condition",
        config='{"condition": "age > 18"}',
    )
    ctx = ExecutionContext(bot_id=1, workflow_id=1)
    result = ConditionNode().execute(node, ctx)
    assert result.status == ExecutionStatus.RUNNING
    assert result.output is None
    print(f"✅ ConditionNode stub OK (lógica en 14.5.6)")


def test_variable_node_executes():
    print("\n" + "=" * 70)
    print("TEST 16: VariableNode.execute")
    print("=" * 70)
    node = NodeStub(
        node_id="var_1",
        type="variable",
        config='{"name": "service", "value": "peluquería"}',
    )
    ctx = ExecutionContext(bot_id=1, workflow_id=1)
    result = VariableNode().execute(node, ctx)
    assert result.variables_update == {"service": "peluquería"}
    print(f"✅ VariableNode OK: {result.variables_update}")


def test_response_node_executes():
    print("\n" + "=" * 70)
    print("TEST 17: ResponseNode.execute")
    print("=" * 70)
    node = NodeStub(
        node_id="resp_1",
        type="response",
        config='{"text": "Gracias por tu tiempo."}',
    )
    ctx = ExecutionContext(bot_id=1, workflow_id=1)
    result = ResponseNode().execute(node, ctx)
    assert result.output == "Gracias por tu tiempo."
    print(f"✅ ResponseNode OK")


def test_end_node_executes():
    print("\n" + "=" * 70)
    print("TEST 18: EndNode.execute → COMPLETED")
    print("=" * 70)
    node = NodeStub(node_id="end_1", type="end")
    ctx = ExecutionContext(bot_id=1, workflow_id=1)
    result = EndNode().execute(node, ctx)
    assert result.status == ExecutionStatus.COMPLETED
    print(f"✅ EndNode OK: status={result.status.value}")


# ============================================================
# TESTS — Errors
# ============================================================

def test_max_steps_exceeded_error():
    print("\n" + "=" * 70)
    print("TEST 19: MaxStepsExceeded")
    print("=" * 70)
    e = MaxStepsExceeded(100)
    assert e.max_steps == 100
    assert isinstance(e, WorkflowError)
    print(f"✅ MaxStepsExceeded: {e}")


def test_node_execution_error():
    print("\n" + "=" * 70)
    print("TEST 20: NodeExecutionError")
    print("=" * 70)
    e = NodeExecutionError("msg_1", "config inválida")
    assert e.node_id == "msg_1"
    assert e.message == "config inválida"
    print(f"✅ NodeExecutionError: {e}")


def test_condition_error():
    print("\n" + "=" * 70)
    print("TEST 21: ConditionError")
    print("=" * 70)
    e = ConditionError("age >", "expresión incompleta")
    assert e.expression == "age >"
    assert e.message == "expresión incompleta"
    print(f"✅ ConditionError: {e}")


def test_validation_error():
    print("\n" + "=" * 70)
    print("TEST 22: WorkflowValidationError")
    print("=" * 70)
    e = WorkflowValidationError(["falta START", "END huérfano"])
    assert len(e.errors) == 2
    assert "falta START" in e.errors
    print(f"✅ ValidationError: {e}")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.5.3 (Nodes + ExecutionContext)")
    print("=" * 70)

    tests = [
        test_execution_status_values,
        test_execution_context_creation,
        test_execution_context_register_step,
        test_node_result_defaults,
        test_execution_result_to_dict,
        test_registry_has_all_node_types,
        test_get_node_handler_ok,
        test_get_node_handler_unknown,
        test_all_handlers_are_basenode,
        test_start_node_executes,
        test_message_node_executes,
        test_message_node_empty_config,
        test_message_node_invalid_json,
        test_question_node_executes,
        test_condition_node_executes_stub,
        test_variable_node_executes,
        test_response_node_executes,
        test_end_node_executes,
        test_max_steps_exceeded_error,
        test_node_execution_error,
        test_condition_error,
        test_validation_error,
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
