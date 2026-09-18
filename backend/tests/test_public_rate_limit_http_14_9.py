"""
Tests — Subfase 14.9.9 (Rate limiting público — HTTP)
=======================================================
Integration tests con TestClient sobre los endpoints /public/*.

Cubre:
    - POST /session supera límite por IP → 429 + Retry-After
    - POST /session desde IPs distintas → OK
    - POST /message supera límite por IP → 429
    - POST /message supera límite por session → 429
    - GET /public/bots/{id} NO está rate-limited
    - DELETE no está rate-limited
    - Reset limpia y permite de nuevo
    - 429 incluye Retry-After
"""

import sys
import os
import time
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.core.public_rate_limit import reset_public_all


client = TestClient(app)


# ============================================================
# HELPERS
# ============================================================

def _unique(suffix):
    return f"{suffix}_{int(time.time() * 1000000)}"


def _register_and_login(suffix):
    unique = _unique(suffix)
    email = f"rate_{unique}@nuvora.com"
    r = client.post("/auth/register", json={
        "email": email, "password": "123456", "full_name": "Rate Test",
    })
    assert r.status_code == 200, r.text
    token = client.post(
        "/auth/login",
        data={"username": email, "password": "123456"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _setup_published_bot():
    """Crea user + bot + workflow activo + publish → devuelve public_id."""
    headers = _register_and_login("setup")
    r = client.post("/bots/", json={
        "name": f"Bot Rate {_unique('b')}",
        "business_name": "Rate", "nicho_id": "otro",
    }, headers=headers)
    bot_id = r.json()["id"]

    r = client.post(f"/workflows/{bot_id}", json={
        "name": "WF Rate",
        "status": "draft",
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

    client.put(f"/workflows/{bot_id}/{wf_id}", json={
        "status": "active",
    }, headers=headers)

    r = client.post(f"/bots/{bot_id}/publish", headers=headers)
    return r.json()["public_id"]


# ============================================================
# ESTADO COMPARTIDO
# ============================================================

class _Ctx:
    public_id = None
    session_id = None


# ============================================================
# SETUP
# ============================================================

def test_setup():
    print("\n" + "=" * 70)
    print("SETUP: publicar bot + crear sesión")
    print("=" * 70)
    reset_public_all()
    _Ctx.public_id = _setup_published_bot()
    r = client.post(f"/public/bots/{_Ctx.public_id}/session", json={})
    assert r.status_code == 200, r.text
    _Ctx.session_id = r.json()["session_id"]
    reset_public_all()
    print(f"  ✅ public_id={_Ctx.public_id[:8]}..., session_id={_Ctx.session_id[:8]}...")


# ============================================================
# TESTS — POST /session (por IP)
# ============================================================

def test_session_rate_limit_by_ip():
    print("\n" + "=" * 70)
    print("TEST 1: POST /session → 11 desde misma IP → 429")
    print("=" * 70)
    reset_public_all()
    limit = settings.public_rate_limit.session_create_limit  # 10

    # Simular IP vía header X-Forwarded-For
    headers = {"X-Forwarded-For": "10.20.30.40"}

    # Hacemos 'limit' peticiones → OK
    for i in range(limit):
        r = client.post(
            f"/public/bots/{_Ctx.public_id}/session",
            json={}, headers=headers,
        )
        assert r.status_code == 200, f"#{i+1} esperaba 200, hubo {r.status_code}: {r.text}"

    # La siguiente → 429
    r = client.post(
        f"/public/bots/{_Ctx.public_id}/session",
        json={}, headers=headers,
    )
    assert r.status_code == 429, f"Esperaba 429, hubo {r.status_code}: {r.text}"
    assert "Retry-After" in r.headers
    assert int(r.headers["Retry-After"]) > 0
    print(f"  ✅ 429 tras {limit} peticiones (Retry-After={r.headers['Retry-After']}s)")
    reset_public_all()


def test_session_different_ips_ok():
    print("\n" + "=" * 70)
    print("TEST 2: POST /session desde IPs distintas → OK")
    print("=" * 70)
    reset_public_all()
    limit = settings.public_rate_limit.session_create_limit

    # Superamos el límite con la IP A...
    for _ in range(limit):
        client.post(
            f"/public/bots/{_Ctx.public_id}/session",
            json={}, headers={"X-Forwarded-For": "1.1.1.1"},
        )
    r = client.post(
        f"/public/bots/{_Ctx.public_id}/session",
        json={}, headers={"X-Forwarded-For": "1.1.1.1"},
    )
    assert r.status_code == 429

    # ...pero la IP B sigue funcionando
    r = client.post(
        f"/public/bots/{_Ctx.public_id}/session",
        json={}, headers={"X-Forwarded-For": "2.2.2.2"},
    )
    assert r.status_code == 200, f"IP B esperaba 200, hubo {r.status_code}"
    print("  ✅ IP distinta → OK")
    reset_public_all()


# ============================================================
# TESTS — POST /message (por IP + por session)
# ============================================================

def test_message_rate_limit_by_ip():
    print("\n" + "=" * 70)
    print("TEST 3: POST /message → límite por IP")
    print("=" * 70)
    reset_public_all()

    # Reducimos temporalmente el límite para no hacer 60 llamadas
    original_limit = settings.public_rate_limit.message_limit
    # Nota: settings es frozen dataclass → no se puede modificar.
    # Solución: llamamos con headers para forzar y usar el límite real.
    # Pero como el límite es 60, lo hacemos con 60 llamadas (más lento pero correcto).

    # Alternativa: monkey-patch interno de config
    import app.core.public_rate_limit as prl
    original_get_limit = prl._get_limit_for

    def patched_get_limit(bucket):
        if bucket == "public_message":
            return 3
        return original_get_limit(bucket)

    prl._get_limit_for = patched_get_limit

    try:
        headers = {"X-Forwarded-For": "3.3.3.3"}
        for i in range(3):
            r = client.post(
                f"/public/bots/{_Ctx.public_id}/message",
                json={"session_id": _Ctx.session_id, "message": f"m{i}"},
                headers=headers,
            )
            assert r.status_code == 200, f"#{i+1}: {r.status_code} {r.text}"

        r = client.post(
            f"/public/bots/{_Ctx.public_id}/message",
            json={"session_id": _Ctx.session_id, "message": "boom"},
            headers=headers,
        )
        assert r.status_code == 429, f"Esperaba 429, hubo {r.status_code}"
        assert "Retry-After" in r.headers
        print(f"  ✅ 429 tras 3 peticiones con límite=3")
    finally:
        prl._get_limit_for = original_get_limit
        reset_public_all()


def test_message_rate_limit_by_session():
    print("\n" + "=" * 70)
    print("TEST 4: POST /message → límite por session_id")
    print("=" * 70)
    reset_public_all()

    import app.core.public_rate_limit as prl
    original_get_limit = prl._get_limit_for

    def patched_get_limit(bucket):
        if bucket == "public_message_session":
            return 2
        return original_get_limit(bucket)

    prl._get_limit_for = patched_get_limit

    try:
        # IPs distintas, misma session → debe limitarse por session
        for i in range(2):
            r = client.post(
                f"/public/bots/{_Ctx.public_id}/message",
                json={"session_id": _Ctx.session_id, "message": f"m{i}"},
                headers={"X-Forwarded-For": f"5.5.5.{i}"},
            )
            assert r.status_code == 200, f"#{i+1}: {r.status_code} {r.text}"

        r = client.post(
            f"/public/bots/{_Ctx.public_id}/message",
            json={"session_id": _Ctx.session_id, "message": "boom"},
            headers={"X-Forwarded-For": "5.5.5.99"},
        )
        assert r.status_code == 429, f"Esperaba 429, hubo {r.status_code}"
        print(f"  ✅ 429 por session_id (límite=2)")
    finally:
        prl._get_limit_for = original_get_limit
        reset_public_all()


# ============================================================
# TESTS — Endpoints NO rate-limited
# ============================================================

def test_get_info_not_rate_limited():
    print("\n" + "=" * 70)
    print("TEST 5: GET /public/bots/{id} NO rate-limited")
    print("=" * 70)
    reset_public_all()
    for i in range(50):
        r = client.get(
            f"/public/bots/{_Ctx.public_id}",
            headers={"X-Forwarded-For": "9.9.9.9"},
        )
        assert r.status_code == 200, f"#{i+1}: {r.status_code}"
    print("  ✅ 50 GET OK (sin rate limit)")


def test_delete_session_not_rate_limited():
    print("\n" + "=" * 70)
    print("TEST 6: DELETE /session NO rate-limited")
    print("=" * 70)
    reset_public_all()
    # Creamos sesiones y las cerramos — no debe haber límite
    for i in range(5):
        r = client.post(
            f"/public/bots/{_Ctx.public_id}/session",
            json={}, headers={"X-Forwarded-For": f"7.7.7.{i}"},
        )
        sid = r.json()["session_id"]
        r = client.delete(
            f"/public/bots/{_Ctx.public_id}/session",
            params={"session_id": sid},
        )
        assert r.status_code == 200
    print("  ✅ DELETE sin rate limit")


# ============================================================
# TESTS — Reset
# ============================================================

def test_reset_allows_again():
    print("\n" + "=" * 70)
    print("TEST 7: Reset limpia y permite de nuevo")
    print("=" * 70)
    reset_public_all()

    import app.core.public_rate_limit as prl
    original_get_limit = prl._get_limit_for

    def patched_get_limit(bucket):
        if bucket == "public_session_create":
            return 2
        return original_get_limit(bucket)

    prl._get_limit_for = patched_get_limit

    try:
        headers = {"X-Forwarded-For": "8.8.8.8"}
        for _ in range(2):
            client.post(
                f"/public/bots/{_Ctx.public_id}/session",
                json={}, headers=headers,
            )
        # 3ª → 429
        r = client.post(
            f"/public/bots/{_Ctx.public_id}/session",
            json={}, headers=headers,
        )
        assert r.status_code == 429

        # Reset
        reset_public_all()

        # De nuevo → OK
        r = client.post(
            f"/public/bots/{_Ctx.public_id}/session",
            json={}, headers=headers,
        )
        assert r.status_code == 200, f"Tras reset esperaba 200, hubo {r.status_code}"
        print("  ✅ Reset permite de nuevo")
    finally:
        prl._get_limit_for = original_get_limit
        reset_public_all()


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS HTTP — SUBFASE 14.9.9 (Rate limit en endpoints)")
    print("=" * 70)

    tests = [
        test_setup,
        test_session_rate_limit_by_ip,
        test_session_different_ips_ok,
        test_message_rate_limit_by_ip,
        test_message_rate_limit_by_session,
        test_get_info_not_rate_limited,
        test_delete_session_not_rate_limited,
        test_reset_allows_again,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"  🛑 FALLÓ: {t.__name__}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print(f"🎉 RESULTADO: {passed} pasados / {failed} fallidos")
    print("=" * 70)
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
