"""
Tests — Subfase 14.8.12 (AI Test Generator)
"""

import sys
import os
import time
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.core.testing import AITestGenerator
from app.core.ai.provider import AIResponse
from app.core.testing.errors import TestDefinitionError
from app.core.ai.errors import AIInvalidOutputError, AIUnavailableError
from app.config import settings
from app.core.ai.rate_limit import reset_all
from app.database.config import SessionLocal
from app.models.db_models import User


client = TestClient(app)


# ============================================================
# HELPERS
# ============================================================

def _unique(suffix):
    return f"{suffix}_{int(time.time() * 1000)}"


def _setup_user_bot_workflow():
    unique = _unique("gen")
    email = f"test_gen_{unique}@nuvora.com"
    password = "123456"

    r = client.post("/auth/register", json={
        "email": email, "password": password, "full_name": "Gen",
    })
    assert r.status_code == 200, r.text
    token = client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post("/bots/", json={
        "name": f"Bot {unique}", "business_name": "T", "nicho_id": "otro",
    }, headers=headers)
    bot_id = r.json()["id"]

    r = client.post(f"/workflows/{bot_id}", json={
        "name": "WF",
        "nodes": [
            {"node_id": "s1", "type": "start"},
            {"node_id": "m1", "type": "message", "config": {"text": "Hola"}},
            {"node_id": "e1", "type": "end"},
        ],
        "transitions": [
            {"from_node_id": "s1", "to_node_id": "m1", "order": 0},
            {"from_node_id": "m1", "to_node_id": "e1", "order": 0},
        ],
    }, headers=headers)
    wf_id = r.json()["id"]

    return headers, bot_id, wf_id


class _Ctx:
    headers = None
    bot_id = None
    wf_id = None
    user_id = None


def _make_ai_response(data: dict, provider: str = "gemini") -> AIResponse:
    return AIResponse(
        data=data,
        provider=provider,
        model="test",
        tokens_used=100,
        raw_text="{}",
    )


def _valid_ai_generated_data():
    """Simula la respuesta de la IA con 3 tests."""
    return {
        "generated": [
            {
                "name": "Test camino principal",
                "description": "Happy path",
                "input_messages": ["Hola"],
                "initial_variables": {},
                "assertions": [
                    {"type": "response_contains", "value": "Hola"},
                    {"type": "reaches_end"},
                ],
                "enabled": True,
            },
            {
                "name": "Test variables",
                "description": "Verifica variables",
                "input_messages": ["Hola"],
                "initial_variables": {"name": "Manuel"},
                "assertions": [
                    {"type": "variable_exists", "variable": "name"},
                ],
                "enabled": True,
            },
            {
                "name": "Test nodo m1",
                "description": "Verifica que pasa por m1",
                "input_messages": ["Hola"],
                "initial_variables": {},
                "assertions": [
                    {"type": "node_visited", "node_id": "m1"},
                ],
                "enabled": True,
            },
        ],
        "count": 3,
        "notes": [],
    }


# ============================================================
# TESTS — Generator (unitario)
# ============================================================

def test_generator_parse_valid():
    print("\n" + "=" * 70)
    print("TEST 1: AITestGenerator._parse_response válido")
    print("=" * 70)
    db = SessionLocal()
    try:
        u = User(email=f"test_{_unique('p')}@nuvora.com", hashed_password="x", is_active=True)
        db.add(u)
        db.commit()
        db.refresh(u)

        gen = AITestGenerator(db=db, user_id=u.id)
        result = gen._parse_response(_valid_ai_generated_data())

        assert result.count == 3
        assert len(result.generated) == 3
        assert result.generated[0].name == "Test camino principal"
        print(f"  ✅ 3 tests parseados")

        db.query(User).filter(User.id == u.id).delete()
        db.commit()
    finally:
        db.close()


def test_generator_rejects_empty_generated():
    print("\n" + "=" * 70)
    print("TEST 2: AITestGenerator sin 'generated' → error")
    print("=" * 70)
    db = SessionLocal()
    try:
        u = User(email=f"test_{_unique('p')}@nuvora.com", hashed_password="x", is_active=True)
        db.add(u)
        db.commit()
        db.refresh(u)

        gen = AITestGenerator(db=db, user_id=u.id)
        try:
            gen._parse_response({"notes": []})
            assert False, "Debería haber fallado"
        except AIInvalidOutputError:
            print(f"  ✅ AIInvalidOutputError")

        db.query(User).filter(User.id == u.id).delete()
        db.commit()
    finally:
        db.close()


def test_generator_rejects_invalid_test():
    print("\n" + "=" * 70)
    print("TEST 3: AITestGenerator con test inválido → TestDefinitionError")
    print("=" * 70)
    db = SessionLocal()
    try:
        u = User(email=f"test_{_unique('p')}@nuvora.com", hashed_password="x", is_active=True)
        db.add(u)
        db.commit()
        db.refresh(u)

        gen = AITestGenerator(db=db, user_id=u.id)
        bad = {
            "generated": [
                {
                    "name": "Sin assertions",
                    "input_messages": ["Hola"],
                    "assertions": [],  # inválido (min_length=1)
                },
            ],
            "count": 1,
        }
        try:
            gen._parse_response(bad)
            assert False, "Debería haber fallado"
        except TestDefinitionError as e:
            assert "Test #1" in str(e)
            print(f"  ✅ TestDefinitionError: {str(e)[:80]}")

        db.query(User).filter(User.id == u.id).delete()
        db.commit()
    finally:
        db.close()


def test_generator_disabled_raises():
    print("\n" + "=" * 70)
    print("TEST 4: AITestGenerator con AI_ENABLED=false → AIUnavailableError")
    print("=" * 70)
    db = SessionLocal()
    original = settings.ai.enabled
    try:
        u = User(email=f"test_{_unique('p')}@nuvora.com", hashed_password="x", is_active=True)
        db.add(u)
        db.commit()
        db.refresh(u)

        object.__setattr__(settings.ai, "enabled", False)
        gen = AITestGenerator(db=db, user_id=u.id)
        try:
            gen.generate(workflow_data={"nodes": [], "transitions": []})
            assert False, "Debería haber fallado"
        except AIUnavailableError:
            print(f"  ✅ AIUnavailableError")

        db.query(User).filter(User.id == u.id).delete()
        db.commit()
    finally:
        object.__setattr__(settings.ai, "enabled", original)
        db.close()


# ============================================================
# TESTS — Endpoint HTTP
# ============================================================

def test_setup():
    print("\n" + "=" * 70)
    print("SETUP")
    print("=" * 70)
    reset_all()
    _Ctx.headers, _Ctx.bot_id, _Ctx.wf_id = _setup_user_bot_workflow()
    r = client.get("/auth/me", headers=_Ctx.headers)
    _Ctx.user_id = r.json()["id"]
    print(f"  ✅ user_id={_Ctx.user_id}, bot_id={_Ctx.bot_id}")


def test_generate_no_auth():
    print("\n" + "=" * 70)
    print("TEST 5: POST /tests/generate sin auth → 401")
    print("=" * 70)
    r = client.post(
        f"/bots/{_Ctx.bot_id}/tests/generate?workflow_id={_Ctx.wf_id}",
    )
    assert r.status_code == 401
    print(f"  ✅ 401")


def test_generate_bot_not_found():
    print("\n" + "=" * 70)
    print("TEST 6: POST bot inexistente → 404")
    print("=" * 70)
    r = client.post(
        "/bots/999999/tests/generate?workflow_id=1",
        headers=_Ctx.headers,
    )
    assert r.status_code == 404
    print(f"  ✅ 404")


def test_generate_success():
    print("\n" + "=" * 70)
    print("TEST 7: POST /tests/generate con IA mock → OK")
    print("=" * 70)
    reset_all()

    ai_data = _valid_ai_generated_data()
    ai_resp = _make_ai_response(ai_data)

    with patch("app.core.testing.ai_generator.get_provider") as mock_get:
        mock_provider = MagicMock()
        mock_provider.generate_json.return_value = ai_resp
        mock_get.return_value = mock_provider

        r = client.post(
            f"/bots/{_Ctx.bot_id}/tests/generate?workflow_id={_Ctx.wf_id}",
            headers=_Ctx.headers,
        )

    assert r.status_code == 200, r.text
    data = r.json()
    assert data["count"] == 3
    assert len(data["generated"]) == 3
    assert data["generated"][0]["name"] == "Test camino principal"
    print(f"  ✅ 3 tests generados")


def test_generate_invalid_ai_output():
    print("\n" + "=" * 70)
    print("TEST 8: IA devuelve JSON inválido → 422")
    print("=" * 70)
    reset_all()

    bad_data = {"generated": [], "count": 0}
    ai_resp = _make_ai_response(bad_data)

    with patch("app.core.testing.ai_generator.get_provider") as mock_get:
        mock_provider = MagicMock()
        mock_provider.generate_json.return_value = ai_resp
        mock_get.return_value = mock_provider

        r = client.post(
            f"/bots/{_Ctx.bot_id}/tests/generate?workflow_id={_Ctx.wf_id}",
            headers=_Ctx.headers,
        )

    assert r.status_code == 422, f"Esperaba 422, hubo {r.status_code}: {r.text}"
    print(f"  ✅ 422")


def test_generate_does_not_save_tests():
    print("\n" + "=" * 70)
    print("TEST 9: generate NO guarda tests en BD")
    print("=" * 70)
    reset_all()

    # Antes de llamar
    r_before = client.get(
        f"/bots/{_Ctx.bot_id}/tests?workflow_id={_Ctx.wf_id}",
        headers=_Ctx.headers,
    )
    count_before = r_before.json()["total"]

    ai_data = _valid_ai_generated_data()
    ai_resp = _make_ai_response(ai_data)

    with patch("app.core.testing.ai_generator.get_provider") as mock_get:
        mock_provider = MagicMock()
        mock_provider.generate_json.return_value = ai_resp
        mock_get.return_value = mock_provider

        r = client.post(
            f"/bots/{_Ctx.bot_id}/tests/generate?workflow_id={_Ctx.wf_id}",
            headers=_Ctx.headers,
        )
        assert r.status_code == 200

    # Después de llamar
    r_after = client.get(
        f"/bots/{_Ctx.bot_id}/tests?workflow_id={_Ctx.wf_id}",
        headers=_Ctx.headers,
    )
    count_after = r_after.json()["total"]

    assert count_before == count_after, (
        f"generate NO debería guardar tests. Antes: {count_before}, "
        f"después: {count_after}"
    )
    print(f"  ✅ Tests no guardados ({count_after} en BD)")


def test_regression_app_imports():
    print("\n" + "=" * 70)
    print("TEST 10: Regresión — app.main sigue OK")
    print("=" * 70)
    from app.main import app as _app
    assert _app is not None
    print(f"  ✅ app OK ({len(_app.routes)} rutas)")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.8.12 (AI Test Generator)")
    print("=" * 70)

    tests = [
        test_generator_parse_valid,
        test_generator_rejects_empty_generated,
        test_generator_rejects_invalid_test,
        test_generator_disabled_raises,
        test_setup,
        test_generate_no_auth,
        test_generate_bot_not_found,
        test_generate_success,
        test_generate_invalid_ai_output,
        test_generate_does_not_save_tests,
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
