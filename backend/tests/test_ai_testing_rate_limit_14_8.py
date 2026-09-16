"""
Tests — Subfase 14.8.8 (Rate limiting del Tester)
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.core.ai.rate_limit import (
    VALID_BUCKETS,
    reset_all,
    reset_bucket,
    get_remaining,
    check_rate_limit,
    RateLimitExceeded,
)


client = TestClient(app)


# ============================================================
# HELPERS
# ============================================================

def _unique(suffix):
    return f"{suffix}_{int(time.time() * 1000)}"


def _setup():
    unique = _unique("u")
    email = f"test_rl_{unique}@nuvora.com"
    password = "123456"

    r = client.post("/auth/register", json={
        "email": email, "password": password, "full_name": "Test RL",
    })
    assert r.status_code == 200, r.text
    token = client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post("/bots/", json={
        "name": f"Bot {unique}", "business_name": "Test", "nicho_id": "otro",
    }, headers=headers)
    bot_id = r.json()["id"]

    r = client.post(f"/workflows/{bot_id}", json={
        "name": "WF",
        "nodes": [
            {"node_id": "s1", "type": "start"},
            {"node_id": "e1", "type": "end"},
        ],
        "transitions": [
            {"from_node_id": "s1", "to_node_id": "e1", "order": 0},
        ],
    }, headers=headers)
    wf_id = r.json()["id"]

    r = client.post(
        f"/bots/{bot_id}/tests?workflow_id={wf_id}",
        json={
            "name": "Test",
            "input_messages": ["Hola"],
            "assertions": [{"type": "reaches_end"}],
        },
        headers=headers,
    )
    test_id = r.json()["id"]

    return headers, bot_id, wf_id, test_id


class _Ctx:
    headers = None
    bot_id = None
    wf_id = None
    test_id = None
    user_id = None


# ============================================================
# TESTS
# ============================================================

def test_valid_buckets_includes_test_buckets():
    print("\n" + "=" * 70)
    print("TEST 1: VALID_BUCKETS incluye los 3 buckets del Tester")
    print("=" * 70)
    assert "test_run" in VALID_BUCKETS
    assert "test_run_all" in VALID_BUCKETS
    assert "test_analyze" in VALID_BUCKETS
    print(f"  ✅ {len(VALID_BUCKETS)} buckets")


def test_config_has_test_limits():
    print("\n" + "=" * 70)
    print("TEST 2: settings.tests tiene los 3 límites")
    print("=" * 70)
    assert settings.tests.rate_limit_test_run == 60
    assert settings.tests.rate_limit_test_run_all == 20
    assert settings.tests.rate_limit_test_analyze == 100
    print(f"  ✅ test_run=60, test_run_all=20, test_analyze=100")


def test_setup():
    print("\n" + "=" * 70)
    print("SETUP")
    print("=" * 70)
    headers, bot_id, wf_id, test_id = _setup()
    _Ctx.headers = headers
    _Ctx.bot_id = bot_id
    _Ctx.wf_id = wf_id
    _Ctx.test_id = test_id

    # Obtener user_id desde /auth/me
    r = client.get("/auth/me", headers=headers)
    _Ctx.user_id = r.json()["id"]
    reset_bucket(_Ctx.user_id)  # limpiar

    print(f"  ✅ user_id={_Ctx.user_id}, bot_id={bot_id}")


def test_rate_limit_test_run():
    print("\n" + "=" * 70)
    print("TEST 3: rate limit en /tests/{id}/run")
    print("=" * 70)
    reset_all()
    original = settings.tests.rate_limit_test_run
    try:
        object.__setattr__(settings.tests, "rate_limit_test_run", 2)

        # 2 OK
        for i in range(2):
            r = client.post(
                f"/bots/{_Ctx.bot_id}/tests/{_Ctx.test_id}/run",
                headers=_Ctx.headers,
            )
            assert r.status_code == 200, f"Call {i+1}: {r.status_code} {r.text}"

        # 3ª → 429
        r = client.post(
            f"/bots/{_Ctx.bot_id}/tests/{_Ctx.test_id}/run",
            headers=_Ctx.headers,
        )
        assert r.status_code == 429, f"Esperaba 429, hubo {r.status_code}: {r.text}"
        assert "Retry-After" in r.headers
        print(f"  ✅ 429 + Retry-After={r.headers['Retry-After']}s")
    finally:
        object.__setattr__(settings.tests, "rate_limit_test_run", original)
        reset_all()


def test_rate_limit_run_all():
    print("\n" + "=" * 70)
    print("TEST 4: rate limit en /tests/run-all")
    print("=" * 70)
    reset_all()
    original = settings.tests.rate_limit_test_run_all
    try:
        object.__setattr__(settings.tests, "rate_limit_test_run_all", 2)

        for i in range(2):
            r = client.post(
                f"/bots/{_Ctx.bot_id}/tests/run-all?workflow_id={_Ctx.wf_id}",
                headers=_Ctx.headers,
            )
            assert r.status_code == 200, f"Call {i+1}: {r.status_code} {r.text}"

        r = client.post(
            f"/bots/{_Ctx.bot_id}/tests/run-all?workflow_id={_Ctx.wf_id}",
            headers=_Ctx.headers,
        )
        assert r.status_code == 429, f"Esperaba 429, hubo {r.status_code}"
        print(f"  ✅ 429")
    finally:
        object.__setattr__(settings.tests, "rate_limit_test_run_all", original)
        reset_all()


def test_rate_limit_analyze():
    print("\n" + "=" * 70)
    print("TEST 5: rate limit en /tests/analyze")
    print("=" * 70)
    reset_all()
    original = settings.tests.rate_limit_test_analyze
    try:
        object.__setattr__(settings.tests, "rate_limit_test_analyze", 2)

        for i in range(2):
            r = client.post(
                f"/bots/{_Ctx.bot_id}/tests/analyze?workflow_id={_Ctx.wf_id}",
                headers=_Ctx.headers,
            )
            assert r.status_code == 200, f"Call {i+1}: {r.status_code} {r.text}"

        r = client.post(
            f"/bots/{_Ctx.bot_id}/tests/analyze?workflow_id={_Ctx.wf_id}",
            headers=_Ctx.headers,
        )
        assert r.status_code == 429
        print(f"  ✅ 429")
    finally:
        object.__setattr__(settings.tests, "rate_limit_test_analyze", original)
        reset_all()


def test_buckets_are_isolated():
    print("\n" + "=" * 70)
    print("TEST 6: Buckets aislados entre sí")
    print("=" * 70)
    reset_all()
    original_run = settings.tests.rate_limit_test_run
    original_analyze = settings.tests.rate_limit_test_analyze
    try:
        # Agotar test_run
        object.__setattr__(settings.tests, "rate_limit_test_run", 1)
        r = client.post(
            f"/bots/{_Ctx.bot_id}/tests/{_Ctx.test_id}/run",
            headers=_Ctx.headers,
        )
        assert r.status_code == 200

        # test_run agotado
        r = client.post(
            f"/bots/{_Ctx.bot_id}/tests/{_Ctx.test_id}/run",
            headers=_Ctx.headers,
        )
        assert r.status_code == 429

        # Pero analyze sigue funcionando
        r = client.post(
            f"/bots/{_Ctx.bot_id}/tests/analyze?workflow_id={_Ctx.wf_id}",
            headers=_Ctx.headers,
        )
        assert r.status_code == 200
        print(f"  ✅ Buckets aislados OK")
    finally:
        object.__setattr__(settings.tests, "rate_limit_test_run", original_run)
        object.__setattr__(settings.tests, "rate_limit_test_analyze", original_analyze)
        reset_all()


def test_rate_limit_disabled_globally():
    print("\n" + "=" * 70)
    print("TEST 7: AI_RATE_LIMIT_ENABLED=false → sin 429")
    print("=" * 70)
    original_enabled = settings.ai.rate_limit_enabled
    original_run = settings.tests.rate_limit_test_run
    try:
        object.__setattr__(settings.ai, "rate_limit_enabled", False)
        object.__setattr__(settings.tests, "rate_limit_test_run", 1)
        reset_all()

        # 5 llamadas → todas OK
        for i in range(5):
            r = client.post(
                f"/bots/{_Ctx.bot_id}/tests/{_Ctx.test_id}/run",
                headers=_Ctx.headers,
            )
            assert r.status_code == 200, f"Call {i+1}: {r.status_code}"
        print(f"  ✅ 5 llamadas OK (deshabilitado)")
    finally:
        object.__setattr__(settings.ai, "rate_limit_enabled", original_enabled)
        object.__setattr__(settings.tests, "rate_limit_test_run", original_run)
        reset_all()


def test_regression_app_imports():
    print("\n" + "=" * 70)
    print("TEST 8: Regresión — app.main sigue OK")
    print("=" * 70)
    from app.main import app as _app
    assert _app is not None
    print(f"  ✅ app OK ({len(_app.routes)} rutas)")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.8.8 (Rate limiting del Tester)")
    print("=" * 70)

    tests = [
        test_valid_buckets_includes_test_buckets,
        test_config_has_test_limits,
        test_setup,
        test_rate_limit_test_run,
        test_rate_limit_run_all,
        test_rate_limit_analyze,
        test_buckets_are_isolated,
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
