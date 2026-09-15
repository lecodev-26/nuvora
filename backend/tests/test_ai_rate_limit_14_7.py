"""
Tests — Subfase 14.7.13 (Rate limiting)
"""

import sys
import os
import time
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.core.ai.rate_limit import (
    check_rate_limit,
    get_remaining,
    reset_bucket,
    reset_all,
    get_stats,
    RateLimitExceeded,
    VALID_BUCKETS,
    WINDOW_SECONDS,
)
from app.core.ai.provider import AIResponse
from app.config import settings


client = TestClient(app)


# ============================================================
# HELPERS
# ============================================================

def _unique(suffix: str) -> str:
    return f"{suffix}_{int(time.time() * 1000)}"


def _register_and_login(suffix: str):
    unique = _unique(suffix)
    email = f"test_rl_{unique}@nuvora.com"
    password = "123456"

    r = client.post("/auth/register", json={
        "email": email,
        "password": password,
        "full_name": f"Test RL {unique}",
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


def _make_ai_response(data: dict) -> AIResponse:
    return AIResponse(
        data=data,
        provider="gemini",
        model="test",
        tokens_used=10,
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
# TESTS — Unitarios de rate_limit
# ============================================================

def test_valid_buckets():
    print("\n" + "=" * 70)
    print("TEST 1: VALID_BUCKETS contiene los 6 buckets")
    print("=" * 70)
    assert VALID_BUCKETS == {
        "generate", "modify", "explain", "analyze",
        "templates_list", "templates_instantiate",
    }
    print(f"  ✅ {sorted(VALID_BUCKETS)}")


def test_check_rate_limit_basic():
    print("\n" + "=" * 70)
    print("TEST 2: check_rate_limit respeta el límite")
    print("=" * 70)
    reset_all()
    user, bucket, limit = 1, "generate", 3
    for i in range(limit):
        check_rate_limit(user, bucket, limit)
    assert get_remaining(user, bucket, limit) == 0

    try:
        check_rate_limit(user, bucket, limit)
        assert False, "Debería haber fallado"
    except RateLimitExceeded as e:
        assert e.retry_after > 0
        assert e.limit == 3
        print(f"  ✅ RateLimitExceeded: retry={e.retry_after}s")
    reset_all()


def test_invalid_bucket():
    print("\n" + "=" * 70)
    print("TEST 3: Bucket inválido → ValueError")
    print("=" * 70)
    try:
        check_rate_limit(1, "inventado", 10)
        assert False, "Debería haber fallado"
    except ValueError as e:
        assert "inventado" in str(e)
        print(f"  ✅ ValueError: {e}")


def test_get_remaining_when_disabled():
    print("\n" + "=" * 70)
    print("TEST 4: get_remaining con rate_limit_enabled=false")
    print("=" * 70)
    original = settings.ai.rate_limit_enabled
    try:
        object.__setattr__(settings.ai, "rate_limit_enabled", False)
        remaining = get_remaining(999, "generate", 10)
        assert remaining == 10
        print(f"  ✅ remaining={remaining} (deshabilitado)")
    finally:
        object.__setattr__(settings.ai, "rate_limit_enabled", original)


def test_reset_bucket():
    print("\n" + "=" * 70)
    print("TEST 5: reset_bucket limpia los timestamps")
    print("=" * 70)
    reset_all()
    user = 2
    check_rate_limit(user, "generate", 5)
    check_rate_limit(user, "generate", 5)
    assert get_remaining(user, "generate", 5) == 3
    reset_bucket(user, "generate")
    assert get_remaining(user, "generate", 5) == 5
    print(f"  ✅ reset_bucket OK")


def test_stats():
    print("\n" + "=" * 70)
    print("TEST 6: get_stats devuelve info coherente")
    print("=" * 70)
    reset_all()
    check_rate_limit(1, "generate", 10)
    check_rate_limit(2, "modify", 10)
    stats = get_stats()
    assert stats["active_buckets"] == 2
    assert stats["total_timestamps"] == 2
    assert stats["window_seconds"] == WINDOW_SECONDS
    print(f"  ✅ {stats}")
    reset_all()


def test_isolation_between_users():
    print("\n" + "=" * 70)
    print("TEST 7: Aislamiento entre usuarios")
    print("=" * 70)
    reset_all()
    # user1 agota su límite
    for _ in range(3):
        check_rate_limit(1, "generate", 3)
    # user2 sigue teniendo todo
    assert get_remaining(2, "generate", 3) == 3
    check_rate_limit(2, "generate", 3)
    assert get_remaining(2, "generate", 3) == 2
    print(f"  ✅ Aislamiento OK")
    reset_all()


def test_isolation_between_buckets():
    print("\n" + "=" * 70)
    print("TEST 8: Aislamiento entre buckets del mismo usuario")
    print("=" * 70)
    reset_all()
    for _ in range(3):
        check_rate_limit(1, "generate", 3)
    # Otro bucket no se ve afectado
    assert get_remaining(1, "modify", 5) == 5
    print(f"  ✅ Buckets aislados")
    reset_all()


# ============================================================
# TESTS — Integración HTTP
# ============================================================

def test_setup():
    print("\n" + "=" * 70)
    print("SETUP")
    print("=" * 70)
    email, token, user_id = _register_and_login("u1")
    _Ctx.token = token
    _Ctx.user_id = user_id
    _Ctx.headers = {"Authorization": f"Bearer {token}"}
    reset_bucket(user_id)  # limpiar por si acaso
    print(f"  ✅ user_id={user_id}")


def test_generate_rate_limit_http():
    print("\n" + "=" * 70)
    print("TEST 9: POST /ai/workflows/generate respeta rate limit (HTTP 429)")
    print("=" * 70)

    # Bajar el límite temporalmente a 2
    original = settings.ai.rate_limit_generate
    try:
        object.__setattr__(settings.ai, "rate_limit_generate", 2)
        reset_bucket(_Ctx.user_id)

        ai_resp = _make_ai_response({
            "workflow": _valid_workflow_dict(),
            "explanation": "ok",
            "warnings": [],
        })

        with patch("app.core.ai.designer.get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.generate_json.return_value = ai_resp
            mock_get.return_value = mock_provider

            # 2 OK
            for i in range(2):
                r = client.post(
                    "/ai/workflows/generate",
                    json={"prompt": "Genera un workflow de prueba largo"},
                    headers=_Ctx.headers,
                )
                assert r.status_code == 200, f"Call {i+1}: {r.status_code} {r.text}"

            # 3ª → 429
            r = client.post(
                "/ai/workflows/generate",
                json={"prompt": "Genera un workflow de prueba largo"},
                headers=_Ctx.headers,
            )
            assert r.status_code == 429, f"Esperaba 429, hubo {r.status_code}: {r.text}"
            assert "Retry-After" in r.headers
            assert "límite" in r.text.lower() or "limite" in r.text.lower()
            print(f"  ✅ 429 + Retry-After={r.headers['Retry-After']}s")
    finally:
        object.__setattr__(settings.ai, "rate_limit_generate", original)
        reset_bucket(_Ctx.user_id)


def test_templates_rate_limit_http():
    print("\n" + "=" * 70)
    print("TEST 10: GET /ai/templates respeta rate limit")
    print("=" * 70)
    original = settings.ai.rate_limit_templates_list
    try:
        object.__setattr__(settings.ai, "rate_limit_templates_list", 2)
        reset_bucket(_Ctx.user_id)

        for _ in range(2):
            r = client.get("/ai/templates", headers=_Ctx.headers)
            assert r.status_code == 200

        r = client.get("/ai/templates", headers=_Ctx.headers)
        assert r.status_code == 429, f"Esperaba 429, hubo {r.status_code}"
        print(f"  ✅ 429 OK")
    finally:
        object.__setattr__(settings.ai, "rate_limit_templates_list", original)
        reset_bucket(_Ctx.user_id)


def test_rate_limit_disabled_globally():
    print("\n" + "=" * 70)
    print("TEST 11: AI_RATE_LIMIT_ENABLED=false → sin 429")
    print("=" * 70)
    original_enabled = settings.ai.rate_limit_enabled
    original_gen = settings.ai.rate_limit_generate
    try:
        object.__setattr__(settings.ai, "rate_limit_enabled", False)
        object.__setattr__(settings.ai, "rate_limit_generate", 1)
        reset_bucket(_Ctx.user_id)

        ai_resp = _make_ai_response({
            "workflow": _valid_workflow_dict(),
            "explanation": "ok",
            "warnings": [],
        })

        with patch("app.core.ai.designer.get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.generate_json.return_value = ai_resp
            mock_get.return_value = mock_provider

            # 5 llamadas → todas OK
            for i in range(5):
                r = client.post(
                    "/ai/workflows/generate",
                    json={"prompt": "Genera un workflow de prueba largo"},
                    headers=_Ctx.headers,
                )
                assert r.status_code == 200, f"Call {i+1}: {r.status_code}"
            print(f"  ✅ 5 llamadas OK con rate limit deshabilitado")
    finally:
        object.__setattr__(settings.ai, "rate_limit_enabled", original_enabled)
        object.__setattr__(settings.ai, "rate_limit_generate", original_gen)
        reset_bucket(_Ctx.user_id)


# ============================================================
# REGRESIÓN
# ============================================================

def test_regression_app_imports():
    print("\n" + "=" * 70)
    print("TEST 12: Regresión — app.main sigue OK")
    print("=" * 70)
    from app.main import app as _app
    assert _app is not None
    print(f"  ✅ app OK ({len(_app.routes)} rutas)")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.7.13 (Rate limiting)")
    print("=" * 70)

    tests = [
        test_valid_buckets,
        test_check_rate_limit_basic,
        test_invalid_bucket,
        test_get_remaining_when_disabled,
        test_reset_bucket,
        test_stats,
        test_isolation_between_users,
        test_isolation_between_buckets,
        test_setup,
        test_generate_rate_limit_http,
        test_templates_rate_limit_http,
        test_rate_limit_disabled_globally,
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
