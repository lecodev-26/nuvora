"""
Tests — Subfase 14.7.7 (Router /ai/workflows/* + /ai/templates)
"""

import sys
import os
import time
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.core.ai.provider import AIResponse
from app.database.config import SessionLocal
from app.models.db_models import User


client = TestClient(app)


# ============================================================
# HELPERS
# ============================================================

def _unique(suffix: str) -> str:
    return f"{suffix}_{int(time.time() * 1000)}"


def _register_and_login(suffix: str):
    unique = _unique(suffix)
    email = f"test_aiwf_{unique}@nuvora.com"
    password = "123456"

    r = client.post("/auth/register", json={
        "email": email,
        "password": password,
        "full_name": f"Test AI WF {unique}",
    })
    assert r.status_code == 200, r.text
    user_id = r.json()["id"]

    r = client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return email, token, user_id


def _valid_workflow_dict():
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


def _make_ai_response(data: dict, provider: str = "gemini", tokens: int = 50) -> AIResponse:
    return AIResponse(
        data=data,
        provider=provider,
        model="test-model",
        tokens_used=tokens,
        raw_text="{}",
    )


# ============================================================
# ESTADO COMPARTIDO
# ============================================================

class _Ctx:
    token = None
    user_id = None
    headers = None


# ============================================================
# TESTS
# ============================================================

def test_setup():
    print("\n" + "=" * 70)
    print("SETUP")
    print("=" * 70)
    email, token, user_id = _register_and_login("u1")
    _Ctx.token = token
    _Ctx.user_id = user_id
    _Ctx.headers = {"Authorization": f"Bearer {token}"}
    print(f"  ✅ user_id={user_id}")


# ---------- Sin auth ----------

def test_generate_no_auth():
    print("\n" + "=" * 70)
    print("TEST 1: POST /ai/workflows/generate sin auth → 401")
    print("=" * 70)
    r = client.post("/ai/workflows/generate", json={"prompt": "Un prompt largo"})
    assert r.status_code == 401
    print(f"  ✅ 401")


def test_templates_no_auth():
    print("\n" + "=" * 70)
    print("TEST 2: GET /ai/templates sin auth → 401")
    print("=" * 70)
    r = client.get("/ai/templates")
    assert r.status_code == 401
    print(f"  ✅ 401")


# ---------- Templates ----------

def test_templates_list():
    print("\n" + "=" * 70)
    print("TEST 3: GET /ai/templates → lista de plantillas")
    print("=" * 70)
    r = client.get("/ai/templates", headers=_Ctx.headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "templates" in data
    assert len(data["templates"]) == 4
    ids = {t["id"] for t in data["templates"]}
    assert "customer_support" in ids
    assert "booking" in ids
    print(f"  ✅ {len(data['templates'])} plantillas: {sorted(ids)}")


def test_instantiate_template():
    print("\n" + "=" * 70)
    print("TEST 4: POST /ai/templates/{id}/instantiate → workflow")
    print("=" * 70)
    r = client.post("/ai/templates/customer_support/instantiate", headers=_Ctx.headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["template_id"] == "customer_support"
    assert data["workflow"]["name"] == "Atención al cliente"
    assert len(data["workflow"]["nodes"]) == 5
    print(f"  ✅ Plantilla instanciada: {len(data['workflow']['nodes'])} nodos")


def test_instantiate_missing_template():
    print("\n" + "=" * 70)
    print("TEST 5: POST /ai/templates/unknown/instantiate → 404")
    print("=" * 70)
    r = client.post("/ai/templates/unknown_template/instantiate", headers=_Ctx.headers)
    assert r.status_code == 404, r.text
    print(f"  ✅ 404")


# ---------- Generate ----------

def test_generate_success():
    print("\n" + "=" * 70)
    print("TEST 6: POST /ai/workflows/generate → OK")
    print("=" * 70)
    ai_resp = _make_ai_response({
        "workflow": _valid_workflow_dict(),
        "explanation": "Workflow simple",
        "warnings": [],
    })

    with patch("app.core.ai.designer.get_provider") as mock_get:
        mock_provider = MagicMock()
        mock_provider.generate_json.return_value = ai_resp
        mock_get.return_value = mock_provider

        r = client.post(
            "/ai/workflows/generate",
            json={"prompt": "Quiero un bot que salude y termine"},
            headers=_Ctx.headers,
        )

    assert r.status_code == 200, r.text
    data = r.json()
    assert data["workflow"]["name"] == "WF Test"
    assert data["provider_used"] == "gemini"
    print(f"  ✅ generate OK")


def test_generate_prompt_too_short():
    print("\n" + "=" * 70)
    print("TEST 7: POST /ai/workflows/generate con prompt corto → 422")
    print("=" * 70)
    r = client.post(
        "/ai/workflows/generate",
        json={"prompt": "hi"},
        headers=_Ctx.headers,
    )
    assert r.status_code == 422
    print(f"  ✅ 422")


def test_generate_provider_error():
    print("\n" + "=" * 70)
    print("TEST 8: generate con AIProviderError → 502")
    print("=" * 70)
    from app.core.ai.errors import AIProviderError

    with patch("app.core.ai.designer.get_provider") as mock_get:
        mock_provider = MagicMock()
        mock_provider.generate_json.side_effect = AIProviderError(
            provider="gemini", message="timeout"
        )
        mock_get.return_value = mock_provider

        r = client.post(
            "/ai/workflows/generate",
            json={"prompt": "Quiero un bot que salude"},
            headers=_Ctx.headers,
        )

    assert r.status_code == 502, r.text
    assert "timeout" in r.text.lower() or "proveedor" in r.text.lower()
    print(f"  ✅ 502")


def test_generate_invalid_output():
    print("\n" + "=" * 70)
    print("TEST 9: generate con JSON inválido → 422")
    print("=" * 70)
    bad_resp = _make_ai_response({
        "workflow": {
            "name": "Bad",
            "nodes": [
                {"node_id": "m1", "type": "message", "config": {"text": "x"}},
                {"node_id": "e1", "type": "end"},
            ],
            "transitions": [{"from_node_id": "m1", "to_node_id": "e1"}],
        },
        "explanation": "Bad",
    })

    with patch("app.core.ai.designer.get_provider") as mock_get:
        mock_provider = MagicMock()
        mock_provider.generate_json.return_value = bad_resp
        mock_get.return_value = mock_provider

        r = client.post(
            "/ai/workflows/generate",
            json={"prompt": "Genera algo válido por favor"},
            headers=_Ctx.headers,
        )

    assert r.status_code == 422, r.text
    assert "no es válido" in r.text.lower() or "validad" in r.text.lower()
    print(f"  ✅ 422")


def test_generate_ai_disabled():
    print("\n" + "=" * 70)
    print("TEST 10: generate con AI_ENABLED=false → 503")
    print("=" * 70)
    from app.config import settings

    original = settings.ai.enabled
    try:
        object.__setattr__(settings.ai, "enabled", False)
        r = client.post(
            "/ai/workflows/generate",
            json={"prompt": "Quiero un bot que salude"},
            headers=_Ctx.headers,
        )
        assert r.status_code == 503, r.text
        print(f"  ✅ 503 (IA deshabilitada)")
    finally:
        object.__setattr__(settings.ai, "enabled", original)


# ---------- Modify ----------

def test_modify_success():
    print("\n" + "=" * 70)
    print("TEST 11: POST /ai/workflows/modify → OK")
    print("=" * 70)
    ai_resp = _make_ai_response({
        "workflow": _valid_workflow_dict(),
        "explanation": "Modificado",
    })

    with patch("app.core.ai.designer.get_provider") as mock_get:
        mock_provider = MagicMock()
        mock_provider.generate_json.return_value = ai_resp
        mock_get.return_value = mock_provider

        r = client.post(
            "/ai/workflows/modify",
            json={
                "workflow": _valid_workflow_dict(),
                "instruction": "Añade un mensaje final antes del END",
            },
            headers=_Ctx.headers,
        )

    assert r.status_code == 200, r.text
    print(f"  ✅ modify OK")


# ---------- Explain ----------

def test_explain_success():
    print("\n" + "=" * 70)
    print("TEST 12: POST /ai/workflows/explain → OK")
    print("=" * 70)
    ai_resp = _make_ai_response({"explanation": "Este workflow saluda."})

    with patch("app.core.ai.designer.get_provider") as mock_get:
        mock_provider = MagicMock()
        mock_provider.generate_json.return_value = ai_resp
        mock_get.return_value = mock_provider

        r = client.post(
            "/ai/workflows/explain",
            json={"workflow": _valid_workflow_dict()},
            headers=_Ctx.headers,
        )

    assert r.status_code == 200, r.text
    assert "saluda" in r.json()["explanation"]
    print(f"  ✅ explain OK")


# ---------- Analyze ----------

def test_analyze_success():
    print("\n" + "=" * 70)
    print("TEST 13: POST /ai/workflows/analyze → OK")
    print("=" * 70)
    ai_resp = _make_ai_response({
        "warnings": ["x"],
        "suggestions": ["y"],
    })

    with patch("app.core.ai.designer.get_provider") as mock_get:
        mock_provider = MagicMock()
        mock_provider.generate_json.return_value = ai_resp
        mock_get.return_value = mock_provider

        r = client.post(
            "/ai/workflows/analyze",
            json={"workflow": _valid_workflow_dict()},
            headers=_Ctx.headers,
        )

    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data["warnings"]) == 1
    assert len(data["suggestions"]) == 1
    print(f"  ✅ analyze OK")


# ---------- Regresión ----------

def test_regression_workflows_still_ok():
    print("\n" + "=" * 70)
    print("TEST 14: Regresión — /workflows/* sigue OK")
    print("=" * 70)
    from app.main import app as _app
    schema = _app.openapi()
    paths = schema.get("paths", {})
    assert "/workflows/{bot_id}" in paths
    assert "/ai/workflows/generate" in paths
    assert "/ai/config" in paths
    print(f"  ✅ 3 grupos de rutas OK")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.7.7 (Router /ai/workflows + /ai/templates)")
    print("=" * 70)

    tests = [
        test_setup,
        test_generate_no_auth,
        test_templates_no_auth,
        test_templates_list,
        test_instantiate_template,
        test_instantiate_missing_template,
        test_generate_success,
        test_generate_prompt_too_short,
        test_generate_provider_error,
        test_generate_invalid_output,
        test_generate_ai_disabled,
        test_modify_success,
        test_explain_success,
        test_analyze_success,
        test_regression_workflows_still_ok,
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
