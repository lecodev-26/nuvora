"""
Tests — Subfase 14.7.3
Verifica los schemas Pydantic de la capa IA.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import ValidationError

from app.models.ai import (
    BotContext,
    GeneratedWorkflow,
    GenerateWorkflowRequest,
    GenerateWorkflowResponse,
    ModifyWorkflowRequest,
    ModifyWorkflowResponse,
    ExplainWorkflowRequest,
    ExplainWorkflowResponse,
    AnalyzeWorkflowRequest,
    AnalyzeWorkflowResponse,
    TemplateInfo,
    TemplatesListResponse,
    InstantiateTemplateResponse,
)
from app.core.ai import (
    VALID_NODE_TYPES,
    WORKFLOW_JSON_SCHEMA,
    GENERATE_RESPONSE_SCHEMA,
    MODIFY_RESPONSE_SCHEMA,
    EXPLAIN_RESPONSE_SCHEMA,
    ANALYZE_RESPONSE_SCHEMA,
)


# ============================================================
# HELPERS
# ============================================================

def _valid_workflow_dict():
    return {
        "name": "Test WF",
        "description": "Un workflow simple",
        "nodes": [
            {"node_id": "s1", "type": "start"},
            {"node_id": "m1", "type": "message", "config": {"text": "Hola"}},
            {"node_id": "e1", "type": "end"},
        ],
        "transitions": [
            {"from_node_id": "s1", "to_node_id": "m1", "order": 0},
            {"from_node_id": "m1", "to_node_id": "e1", "order": 0},
        ],
    }


# ============================================================
# TESTS — BotContext
# ============================================================

def test_bot_context_defaults():
    print("\n" + "=" * 70)
    print("TEST 1: BotContext defaults")
    print("=" * 70)
    ctx = BotContext()
    assert ctx.bot_name is None
    assert ctx.description is None
    assert ctx.language == "es"
    print(f"  ✅ language default = 'es'")


def test_bot_context_full():
    print("\n" + "=" * 70)
    print("TEST 2: BotContext completo")
    print("=" * 70)
    ctx = BotContext(
        bot_name="Soporte Nuvora",
        description="Asistente de soporte",
        business_type="SaaS",
        language="es",
        tone="profesional",
    )
    assert ctx.bot_name == "Soporte Nuvora"
    assert ctx.business_type == "SaaS"
    print(f"  ✅ bot_name={ctx.bot_name}, business_type={ctx.business_type}")


def test_bot_context_value_too_long():
    print("\n" + "=" * 70)
    print("TEST 3: BotContext rechaza valores demasiado largos")
    print("=" * 70)
    try:
        BotContext(description="x" * 1000)
        assert False, "Debería haber fallado"
    except ValidationError:
        print(f"  ✅ description > 500 rechazado")


# ============================================================
# TESTS — GeneratedWorkflow
# ============================================================

def test_generated_workflow_valid():
    print("\n" + "=" * 70)
    print("TEST 4: GeneratedWorkflow válido")
    print("=" * 70)
    wf = GeneratedWorkflow(**_valid_workflow_dict())
    assert wf.name == "Test WF"
    assert len(wf.nodes) == 3
    assert len(wf.transitions) == 2
    print(f"  ✅ {len(wf.nodes)} nodos, {len(wf.transitions)} transiciones")


def test_generated_workflow_invalid_node_type():
    print("\n" + "=" * 70)
    print("TEST 5: GeneratedWorkflow rechaza tipo inválido")
    print("=" * 70)
    bad = {
        "name": "Bad",
        "nodes": [{"node_id": "x1", "type": "invalid_type"}],
        "transitions": [],
    }
    try:
        GeneratedWorkflow(**bad)
        assert False, "Debería haber fallado"
    except ValidationError:
        print(f"  ✅ Tipo inválido rechazado")


def test_generated_workflow_empty_name():
    print("\n" + "=" * 70)
    print("TEST 6: GeneratedWorkflow rechaza name vacío")
    print("=" * 70)
    try:
        GeneratedWorkflow(name="", nodes=[], transitions=[])
        assert False, "Debería haber fallado"
    except ValidationError:
        print(f"  ✅ name vacío rechazado")


# ============================================================
# TESTS — Generate
# ============================================================

def test_generate_request_ok():
    print("\n" + "=" * 70)
    print("TEST 7: GenerateWorkflowRequest OK")
    print("=" * 70)
    req = GenerateWorkflowRequest(
        prompt="Quiero un bot que salude y pregunte el nombre",
        bot_context=BotContext(bot_name="Test"),
    )
    assert len(req.prompt) > 10
    assert req.bot_context.bot_name == "Test"
    print(f"  ✅ prompt OK, bot_context OK")


def test_generate_request_prompt_too_short():
    print("\n" + "=" * 70)
    print("TEST 8: GenerateWorkflowRequest rechaza prompt corto")
    print("=" * 70)
    try:
        GenerateWorkflowRequest(prompt="hi")
        assert False, "Debería haber fallado"
    except ValidationError:
        print(f"  ✅ prompt < 10 rechazado")


def test_generate_request_prompt_too_long():
    print("\n" + "=" * 70)
    print("TEST 9: GenerateWorkflowRequest rechaza prompt largo")
    print("=" * 70)
    try:
        GenerateWorkflowRequest(prompt="x" * 3000)
        assert False, "Debería haber fallado"
    except ValidationError:
        print(f"  ✅ prompt > 2000 rechazado")


def test_generate_response_ok():
    print("\n" + "=" * 70)
    print("TEST 10: GenerateWorkflowResponse OK")
    print("=" * 70)
    res = GenerateWorkflowResponse(
        workflow=GeneratedWorkflow(**_valid_workflow_dict()),
        explanation="He creado un workflow simple.",
        warnings=[],
        provider_used="gemini",
        tokens_used=1234,
    )
    assert res.workflow.name == "Test WF"
    assert res.provider_used == "gemini"
    print(f"  ✅ response OK, tokens_used={res.tokens_used}")


# ============================================================
# TESTS — Modify
# ============================================================

def test_modify_request_ok():
    print("\n" + "=" * 70)
    print("TEST 11: ModifyWorkflowRequest OK")
    print("=" * 70)
    req = ModifyWorkflowRequest(
        workflow=GeneratedWorkflow(**_valid_workflow_dict()),
        instruction="Añade una pregunta para el email",
    )
    assert len(req.instruction) > 5
    print(f"  ✅ instruction OK")


def test_modify_response_ok():
    print("\n" + "=" * 70)
    print("TEST 12: ModifyWorkflowResponse OK")
    print("=" * 70)
    res = ModifyWorkflowResponse(
        workflow=GeneratedWorkflow(**_valid_workflow_dict()),
        explanation="Añadida una pregunta para el email tras el nombre.",
        warnings=[],
        provider_used="groq",
    )
    assert res.provider_used == "groq"
    print(f"  ✅ modify response OK")


# ============================================================
# TESTS — Explain / Analyze
# ============================================================

def test_explain_ok():
    print("\n" + "=" * 70)
    print("TEST 13: ExplainWorkflowResponse OK")
    print("=" * 70)
    req = ExplainWorkflowRequest(workflow=GeneratedWorkflow(**_valid_workflow_dict()))
    res = ExplainWorkflowResponse(
        explanation="Este workflow saluda al usuario y termina.",
        provider_used="gemini",
    )
    assert isinstance(req.workflow, GeneratedWorkflow)
    assert req.workflow.name == "Test WF"
    assert len(res.explanation) > 0
    print(f"  ✅ explain OK")


def test_analyze_ok():
    print("\n" + "=" * 70)
    print("TEST 14: AnalyzeWorkflowResponse OK")
    print("=" * 70)
    res = AnalyzeWorkflowResponse(
        warnings=["La variable x no se usa después"],
        suggestions=["Añade una confirmación final"],
        provider_used="deepseek",
    )
    assert len(res.warnings) == 1
    assert len(res.suggestions) == 1
    print(f"  ✅ analyze OK")


# ============================================================
# TESTS — Templates
# ============================================================

def test_template_info_ok():
    print("\n" + "=" * 70)
    print("TEST 15: TemplateInfo OK")
    print("=" * 70)
    t = TemplateInfo(
        id="support",
        name="Atención al cliente",
        description="Workflow de soporte básico",
        icon="🎧",
    )
    assert t.id == "support"
    assert t.icon == "🎧"
    print(f"  ✅ template OK")


def test_templates_list_ok():
    print("\n" + "=" * 70)
    print("TEST 16: TemplatesListResponse OK")
    print("=" * 70)
    res = TemplatesListResponse(templates=[
        TemplateInfo(id="a", name="A", description="A", icon="🎯"),
        TemplateInfo(id="b", name="B", description="B", icon="💬"),
    ])
    assert len(res.templates) == 2
    print(f"  ✅ 2 templates OK")


def test_instantiate_template_ok():
    print("\n" + "=" * 70)
    print("TEST 17: InstantiateTemplateResponse OK")
    print("=" * 70)
    res = InstantiateTemplateResponse(
        workflow=GeneratedWorkflow(**_valid_workflow_dict()),
        template_id="support",
    )
    assert res.template_id == "support"
    print(f"  ✅ instantiate OK")


# ============================================================
# TESTS — JSON Schemas internos
# ============================================================

def test_valid_node_types():
    print("\n" + "=" * 70)
    print("TEST 18: VALID_NODE_TYPES coincide con 14.5.2")
    print("=" * 70)
    expected = {"start", "message", "question", "condition", "variable", "response", "end"}
    assert set(VALID_NODE_TYPES) == expected
    print(f"  ✅ {len(VALID_NODE_TYPES)} tipos: {sorted(VALID_NODE_TYPES)}")


def test_workflow_json_schema_structure():
    print("\n" + "=" * 70)
    print("TEST 19: WORKFLOW_JSON_SCHEMA tiene estructura esperada")
    print("=" * 70)
    assert WORKFLOW_JSON_SCHEMA["type"] == "object"
    assert "name" in WORKFLOW_JSON_SCHEMA["properties"]
    assert "nodes" in WORKFLOW_JSON_SCHEMA["properties"]
    assert "transitions" in WORKFLOW_JSON_SCHEMA["properties"]
    assert set(WORKFLOW_JSON_SCHEMA["required"]) == {"name", "nodes", "transitions"}

    # node.type enum coincide con VALID_NODE_TYPES
    node_type_enum = WORKFLOW_JSON_SCHEMA["properties"]["nodes"]["items"]["properties"]["type"]["enum"]
    assert node_type_enum == VALID_NODE_TYPES
    print(f"  ✅ JSON schema OK, enum coincide")


def test_response_schemas_structure():
    print("\n" + "=" * 70)
    print("TEST 20: Response schemas tienen estructura esperada")
    print("=" * 70)
    assert "workflow" in GENERATE_RESPONSE_SCHEMA["properties"]
    assert "explanation" in GENERATE_RESPONSE_SCHEMA["properties"]
    assert "workflow" in MODIFY_RESPONSE_SCHEMA["properties"]
    assert "explanation" in EXPLAIN_RESPONSE_SCHEMA["properties"]
    assert "warnings" in ANALYZE_RESPONSE_SCHEMA["properties"]
    assert "suggestions" in ANALYZE_RESPONSE_SCHEMA["properties"]
    print(f"  ✅ los 4 response schemas OK")


# ============================================================
# TESTS — Regresión
# ============================================================

def test_regression_workflow_validator():
    print("\n" + "=" * 70)
    print("TEST 21: Regresión — WorkflowValidator 14.5.4 sigue OK")
    print("=" * 70)
    from app.core.workflows.validator import WorkflowValidator
    v = WorkflowValidator()
    v.validate(_valid_workflow_dict())
    print(f"  ✅ Validator OK sobre workflow generado")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.7.3 (AI Schemas)")
    print("=" * 70)

    tests = [
        test_bot_context_defaults,
        test_bot_context_full,
        test_bot_context_value_too_long,
        test_generated_workflow_valid,
        test_generated_workflow_invalid_node_type,
        test_generated_workflow_empty_name,
        test_generate_request_ok,
        test_generate_request_prompt_too_short,
        test_generate_request_prompt_too_long,
        test_generate_response_ok,
        test_modify_request_ok,
        test_modify_response_ok,
        test_explain_ok,
        test_analyze_ok,
        test_template_info_ok,
        test_templates_list_ok,
        test_instantiate_template_ok,
        test_valid_node_types,
        test_workflow_json_schema_structure,
        test_response_schemas_structure,
        test_regression_workflow_validator,
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
