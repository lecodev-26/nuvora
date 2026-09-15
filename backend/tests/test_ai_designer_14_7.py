"""
Tests — Subfase 14.7.6 (AIWorkflowDesigner)
Verifica:
    - generate() con JSON válido
    - generate() con JSON inválido → retry → error
    - generate() con retry exitoso
    - modify()
    - explain()
    - analyze()
    - Guard AI_ENABLED
    - _format_error
"""

import sys
import os
import time
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.ai.designer import AIWorkflowDesigner, MAX_VALIDATION_RETRIES
from app.core.ai.provider import AIResponse
from app.core.ai.errors import AIInvalidOutputError, AIUnavailableError
from app.models.ai import BotContext, GeneratedWorkflow
from app.config import settings
from app.database.config import SessionLocal
from app.models.db_models import User


# ============================================================
# HELPERS
# ============================================================

def _make_valid_workflow_dict():
    return {
        "name": "WF Test",
        "description": "Simple",
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


def _make_invalid_workflow_dict():
    """Workflow sin START (inválido)."""
    return {
        "name": "Bad WF",
        "nodes": [
            {"node_id": "m1", "type": "message", "config": {"text": "Hola"}},
            {"node_id": "e1", "type": "end"},
        ],
        "transitions": [
            {"from_node_id": "m1", "to_node_id": "e1"},
        ],
    }


def _make_ai_response(data: dict, provider: str = "gemini", tokens: int = 100) -> AIResponse:
    return AIResponse(
        data=data,
        provider=provider,
        model="test-model",
        tokens_used=tokens,
        raw_text="{}",
    )


def _make_designer_with_user():
    """Crea un designer con un user real (para que BYOK no falle)."""
    db = SessionLocal()
    u = User(
        email=f"test_designer_{int(time.time()*1000)}@nuvora.com",
        hashed_password="x",
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return AIWorkflowDesigner(db=db, user_id=u.id), db, u


def _cleanup_user(db, u):
    from app.models.db_models import UserAIConfig
    db.query(UserAIConfig).filter(UserAIConfig.user_id == u.id).delete()
    db.query(User).filter(User.id == u.id).delete()
    db.commit()
    db.close()


# ============================================================
# TESTS — generate()
# ============================================================

def test_generate_success():
    print("\n" + "=" * 70)
    print("TEST 1: generate() con JSON válido → OK")
    print("=" * 70)
    designer, db, u = _make_designer_with_user()
    try:
        ai_resp = _make_ai_response({
            "workflow": _make_valid_workflow_dict(),
            "explanation": "Workflow que saluda.",
            "warnings": [],
        })

        with patch.object(designer, "_get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.generate_json.return_value = ai_resp
            mock_get.return_value = mock_provider

            result = designer.generate("Quiero un bot que salude.")

            assert result.workflow.name == "WF Test"
            assert result.explanation == "Workflow que saluda."
            assert result.provider_used == "gemini"
            assert result.tokens_used == 100
            assert mock_provider.generate_json.call_count == 1
            print(f"  ✅ generate OK: {len(result.workflow.nodes)} nodos")
    finally:
        _cleanup_user(db, u)


def test_generate_retry_success():
    print("\n" + "=" * 70)
    print("TEST 2: generate() retry → 2º intento OK")
    print("=" * 70)
    designer, db, u = _make_designer_with_user()
    try:
        # Primera respuesta: inválida (sin START)
        bad_resp = _make_ai_response({
            "workflow": _make_invalid_workflow_dict(),
            "explanation": "Bad",
        })
        # Segunda respuesta: válida
        good_resp = _make_ai_response({
            "workflow": _make_valid_workflow_dict(),
            "explanation": "OK",
        })

        with patch.object(designer, "_get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.generate_json.side_effect = [bad_resp, good_resp]
            mock_get.return_value = mock_provider

            result = designer.generate("Genera algo.")

            assert result.workflow.name == "WF Test"
            assert mock_provider.generate_json.call_count == 2
            print(f"  ✅ Retry OK: 2 intentos, éxito en el 2º")
    finally:
        _cleanup_user(db, u)


def test_generate_all_retries_fail():
    print("\n" + "=" * 70)
    print("TEST 3: generate() todos los retries fallan → AIInvalidOutputError")
    print("=" * 70)
    designer, db, u = _make_designer_with_user()
    try:
        bad_resp = _make_ai_response({
            "workflow": _make_invalid_workflow_dict(),
            "explanation": "Bad",
        })

        with patch.object(designer, "_get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.generate_json.return_value = bad_resp
            mock_get.return_value = mock_provider

            try:
                designer.generate("Genera algo.")
                assert False, "Debería haber fallado"
            except AIInvalidOutputError as e:
                # 1 + MAX_VALIDATION_RETRIES intentos
                expected = 1 + MAX_VALIDATION_RETRIES
                assert mock_provider.generate_json.call_count == expected
                assert "no pasó la validación" in str(e)
                print(f"  ✅ AIInvalidOutputError tras {expected} intentos")
    finally:
        _cleanup_user(db, u)


def test_generate_missing_workflow_key():
    print("\n" + "=" * 70)
    print("TEST 4: generate() sin 'workflow' en JSON → error")
    print("=" * 70)
    designer, db, u = _make_designer_with_user()
    try:
        bad_resp = _make_ai_response({"explanation": "No workflow"})

        with patch.object(designer, "_get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.generate_json.return_value = bad_resp
            mock_get.return_value = mock_provider

            try:
                designer.generate("Genera algo.")
                assert False, "Debería haber fallado"
            except AIInvalidOutputError as e:
                assert "no pasó la validación" in str(e) or "no contiene" in str(e).lower()
                print(f"  ✅ Detectado JSON sin 'workflow'")
    finally:
        _cleanup_user(db, u)


# ============================================================
# TESTS — modify()
# ============================================================

def test_modify_success():
    print("\n" + "=" * 70)
    print("TEST 5: modify() con JSON válido → OK")
    print("=" * 70)
    designer, db, u = _make_designer_with_user()
    try:
        workflow = GeneratedWorkflow(**_make_valid_workflow_dict())
        ai_resp = _make_ai_response({
            "workflow": _make_valid_workflow_dict(),
            "explanation": "Añadida una respuesta final.",
        })

        with patch.object(designer, "_get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.generate_json.return_value = ai_resp
            mock_get.return_value = mock_provider

            result = designer.modify(workflow, "Añade un mensaje final.")

            assert result.workflow.name == "WF Test"
            assert result.explanation == "Añadida una respuesta final."
            print(f"  ✅ modify OK")
    finally:
        _cleanup_user(db, u)


# ============================================================
# TESTS — explain()
# ============================================================

def test_explain_success():
    print("\n" + "=" * 70)
    print("TEST 6: explain() con JSON válido → OK")
    print("=" * 70)
    designer, db, u = _make_designer_with_user()
    try:
        workflow = GeneratedWorkflow(**_make_valid_workflow_dict())
        ai_resp = _make_ai_response({"explanation": "Este workflow saluda y termina."})

        with patch.object(designer, "_get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.generate_json.return_value = ai_resp
            mock_get.return_value = mock_provider

            result = designer.explain(workflow)

            assert "saluda" in result.explanation
            print(f"  ✅ explain OK: {result.explanation[:40]}...")
    finally:
        _cleanup_user(db, u)


def test_explain_missing_explanation():
    print("\n" + "=" * 70)
    print("TEST 7: explain() sin 'explanation' → AIInvalidOutputError")
    print("=" * 70)
    designer, db, u = _make_designer_with_user()
    try:
        workflow = GeneratedWorkflow(**_make_valid_workflow_dict())
        ai_resp = _make_ai_response({})

        with patch.object(designer, "_get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.generate_json.return_value = ai_resp
            mock_get.return_value = mock_provider

            try:
                designer.explain(workflow)
                assert False, "Debería haber fallado"
            except AIInvalidOutputError as e:
                assert "explanation" in str(e).lower()
                print(f"  ✅ Detectado sin explanation")
    finally:
        _cleanup_user(db, u)


# ============================================================
# TESTS — analyze()
# ============================================================

def test_analyze_success():
    print("\n" + "=" * 70)
    print("TEST 8: analyze() con JSON válido → OK")
    print("=" * 70)
    designer, db, u = _make_designer_with_user()
    try:
        workflow = GeneratedWorkflow(**_make_valid_workflow_dict())
        ai_resp = _make_ai_response({
            "warnings": ["Nodo m1 sin nombre descriptivo"],
            "suggestions": ["Añadir una despedida"],
        })

        with patch.object(designer, "_get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.generate_json.return_value = ai_resp
            mock_get.return_value = mock_provider

            result = designer.analyze(workflow)

            assert len(result.warnings) == 1
            assert len(result.suggestions) == 1
            print(f"  ✅ analyze OK: {len(result.warnings)} warnings")
    finally:
        _cleanup_user(db, u)


# ============================================================
# TESTS — Guard AI_ENABLED
# ============================================================

def test_disabled_raises():
    print("\n" + "=" * 70)
    print("TEST 9: AI_ENABLED=false → AIUnavailableError")
    print("=" * 70)
    designer, db, u = _make_designer_with_user()
    original = settings.ai.enabled
    try:
        object.__setattr__(settings.ai, "enabled", False)
        try:
            designer.generate("test prompt largo")
            assert False, "Debería haber fallado"
        except AIUnavailableError as e:
            print(f"  ✅ AIUnavailableError: {e}")
    finally:
        object.__setattr__(settings.ai, "enabled", original)
        _cleanup_user(db, u)


# ============================================================
# TESTS — Helpers
# ============================================================

def test_format_error_workflow_validation():
    print("\n" + "=" * 70)
    print("TEST 10: _format_error con WorkflowValidationError")
    print("=" * 70)
    from app.core.workflows.errors import WorkflowValidationError
    designer, db, u = _make_designer_with_user()
    try:
        e = WorkflowValidationError(["Falta START", "Falta END"])
        msg = designer._format_error(e)
        assert "Falta START" in msg
        assert "Falta END" in msg
        print(f"  ✅ _format_error OK")
    finally:
        _cleanup_user(db, u)


def test_format_error_condition():
    print("\n" + "=" * 70)
    print("TEST 11: _format_error con ConditionError")
    print("=" * 70)
    from app.core.workflows.errors import ConditionError
    designer, db, u = _make_designer_with_user()
    try:
        e = ConditionError(expression="bad", message="Formato inválido")
        msg = designer._format_error(e)
        assert "Condición inválida" in msg
        print(f"  ✅ _format_error ConditionError OK")
    finally:
        _cleanup_user(db, u)


def test_augment_with_feedback():
    print("\n" + "=" * 70)
    print("TEST 12: _augment_with_feedback añade bloque de error")
    print("=" * 70)
    designer, db, u = _make_designer_with_user()
    try:
        original = "Prompt original"
        # Sin error → sin cambios
        assert designer._augment_with_feedback(original, None) == original

        # Con error → añade bloque
        augmented = designer._augment_with_feedback(original, "error X")
        assert "ATENCIÓN" in augmented
        assert "error X" in augmented
        assert original in augmented
        print(f"  ✅ _augment_with_feedback OK")
    finally:
        _cleanup_user(db, u)


# ============================================================
# REGRESIÓN
# ============================================================

def test_regression_app_imports():
    print("\n" + "=" * 70)
    print("TEST 13: Regresión — app.main sigue OK")
    print("=" * 70)
    from app.main import app as _app
    assert _app is not None
    print(f"  ✅ app OK ({len(_app.routes)} rutas)")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.7.6 (AIWorkflowDesigner)")
    print("=" * 70)

    tests = [
        test_generate_success,
        test_generate_retry_success,
        test_generate_all_retries_fail,
        test_generate_missing_workflow_key,
        test_modify_success,
        test_explain_success,
        test_explain_missing_explanation,
        test_analyze_success,
        test_disabled_raises,
        test_format_error_workflow_validation,
        test_format_error_condition,
        test_augment_with_feedback,
        test_regression_app_imports,
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
