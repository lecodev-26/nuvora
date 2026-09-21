"""
Tests — Subfase 14.10.6 (Router /bots/{bot_id}/api-keys)
==========================================================
Cubre:
    - GET:  401 / 403 / 404 / OK (vacío) / OK (2 keys, sin secret)
    - POST: 401 / 403 / 404 / 422 / OK (con secret + warning) / secret solo 1 vez
    - DELETE: 401 / 403 / 404 / 404 (key de otro bot) / OK
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


# ============================================================
# HELPERS
# ============================================================

def _unique(suffix):
    return f"{suffix}_{int(time.time() * 1000000)}"


def _register_and_login(suffix="apik"):
    unique = _unique(suffix)
    email = f"apik_{unique}@nuvora.com"
    r = client.post("/auth/register", json={
        "email": email, "password": "123456", "full_name": "ApiKeys Test",
    })
    assert r.status_code == 200, r.text
    token = client.post(
        "/auth/login",
        data={"username": email, "password": "123456"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, email


def _create_bot(headers, name=None):
    r = client.post("/bots/", json={
        "name": name or f"Bot {_unique('b')}",
        "business_name": "Test", "nicho_id": "otro",
    }, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["id"]


# ============================================================
# ESTADO COMPARTIDO
# ============================================================

class _Ctx:
    headers1 = None
    headers2 = None
    email1 = None
    email2 = None
    bot1 = None
    bot2 = None
    key1_id = None
    key1_secret = None


# ============================================================
# SETUP
# ============================================================

def test_setup():
    print("\n" + "=" * 70)
    print("SETUP: 2 usuarios, 1 bot cada uno")
    print("=" * 70)
    _Ctx.headers1, _Ctx.email1 = _register_and_login("u1")
    _Ctx.headers2, _Ctx.email2 = _register_and_login("u2")
    _Ctx.bot1 = _create_bot(_Ctx.headers1)
    _Ctx.bot2 = _create_bot(_Ctx.headers2)
    print(f"  ✅ bot1={_Ctx.bot1}, bot2={_Ctx.bot2}")


# ============================================================
# GET /bots/{bot_id}/api-keys
# ============================================================

def test_get_401_no_token():
    print("\n" + "=" * 70)
    print("TEST 1: GET sin token → 401")
    print("=" * 70)
    r = client.get(f"/bots/{_Ctx.bot1}/api-keys")
    assert r.status_code == 401
    print("  ✅ 401")


def test_get_403_other_user():
    print("\n" + "=" * 70)
    print("TEST 2: GET bot ajeno → 403")
    print("=" * 70)
    r = client.get(f"/bots/{_Ctx.bot1}/api-keys", headers=_Ctx.headers2)
    assert r.status_code == 403
    print("  ✅ 403")


def test_get_404_bot_not_found():
    print("\n" + "=" * 70)
    print("TEST 3: GET bot inexistente → 404")
    print("=" * 70)
    r = client.get("/bots/999999999/api-keys", headers=_Ctx.headers1)
    assert r.status_code == 404
    print("  ✅ 404")


def test_get_empty():
    print("\n" + "=" * 70)
    print("TEST 4: GET sin keys → lista vacía")
    print("=" * 70)
    r = client.get(f"/bots/{_Ctx.bot1}/api-keys", headers=_Ctx.headers1)
    assert r.status_code == 200
    data = r.json()
    assert data["keys"] == []
    assert data["total"] == 0
    print("  ✅ Lista vacía")


# ============================================================
# POST /bots/{bot_id}/api-keys
# ============================================================

def test_post_401_no_token():
    print("\n" + "=" * 70)
    print("TEST 5: POST sin token → 401")
    print("=" * 70)
    r = client.post(f"/bots/{_Ctx.bot1}/api-keys", json={"name": "X"})
    assert r.status_code == 401
    print("  ✅ 401")


def test_post_403_other_user():
    print("\n" + "=" * 70)
    print("TEST 6: POST bot ajeno → 403")
    print("=" * 70)
    r = client.post(
        f"/bots/{_Ctx.bot1}/api-keys",
        json={"name": "X"},
        headers=_Ctx.headers2,
    )
    assert r.status_code == 403
    print("  ✅ 403")


def test_post_404_bot_not_found():
    print("\n" + "=" * 70)
    print("TEST 7: POST bot inexistente → 404")
    print("=" * 70)
    r = client.post(
        "/bots/999999999/api-keys",
        json={"name": "X"},
        headers=_Ctx.headers1,
    )
    assert r.status_code == 404
    print("  ✅ 404")


def test_post_422_empty_name():
    print("\n" + "=" * 70)
    print("TEST 8: POST name vacío → 422")
    print("=" * 70)
    r = client.post(
        f"/bots/{_Ctx.bot1}/api-keys",
        json={"name": ""},
        headers=_Ctx.headers1,
    )
    assert r.status_code == 422
    print("  ✅ 422")


def test_post_422_long_name():
    print("\n" + "=" * 70)
    print("TEST 9: POST name > 100 → 422")
    print("=" * 70)
    r = client.post(
        f"/bots/{_Ctx.bot1}/api-keys",
        json={"name": "x" * 101},
        headers=_Ctx.headers1,
    )
    assert r.status_code == 422
    print("  ✅ 422")


def test_post_ok_returns_secret_once():
    print("\n" + "=" * 70)
    print("TEST 10: POST OK — devuelve secret + warning (solo aquí)")
    print("=" * 70)
    r = client.post(
        f"/bots/{_Ctx.bot1}/api-keys",
        json={"name": "Mi web"},
        headers=_Ctx.headers1,
    )
    assert r.status_code == 201, r.text
    data = r.json()

    assert data["name"] == "Mi web"
    assert data["key"].startswith("nvr_live_")
    assert data["key_prefix"] == data["key"][:len("nvr_live_") + 8]
    assert "Guarda esta clave" in data["warning"]
    assert "id" in data
    assert "created_at" in data

    _Ctx.key1_id = data["id"]
    _Ctx.key1_secret = data["key"]
    print(f"  ✅ Key #{_Ctx.key1_id} creada, prefix={data['key_prefix']}")


def test_get_after_post_does_not_leak_secret():
    print("\n" + "=" * 70)
    print("TEST 11: GET después NO devuelve el secret")
    print("=" * 70)
    r = client.get(f"/bots/{_Ctx.bot1}/api-keys", headers=_Ctx.headers1)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    key = data["keys"][0]
    assert "key" not in key, "❌ GET está filtrando el secret"
    assert "key_hash" not in key, "❌ GET está filtrando el hash"
    assert key["key_prefix"].startswith("nvr_live_")
    assert key["is_active"] is True
    print("  ✅ Sin secret en GET")


# ============================================================
# DELETE /bots/{bot_id}/api-keys/{key_id}
# ============================================================

def test_delete_401_no_token():
    print("\n" + "=" * 70)
    print("TEST 12: DELETE sin token → 401")
    print("=" * 70)
    r = client.delete(f"/bots/{_Ctx.bot1}/api-keys/{_Ctx.key1_id}")
    assert r.status_code == 401
    print("  ✅ 401")


def test_delete_403_other_user():
    print("\n" + "=" * 70)
    print("TEST 13: DELETE key ajena → 403")
    print("=" * 70)
    r = client.delete(
        f"/bots/{_Ctx.bot1}/api-keys/{_Ctx.key1_id}",
        headers=_Ctx.headers2,
    )
    assert r.status_code == 403
    print("  ✅ 403")


def test_delete_404_key_not_found():
    print("\n" + "=" * 70)
    print("TEST 14: DELETE key inexistente → 404")
    print("=" * 70)
    r = client.delete(
        f"/bots/{_Ctx.bot1}/api-keys/999999999",
        headers=_Ctx.headers1,
    )
    assert r.status_code == 404
    print("  ✅ 404")


def test_delete_ok():
    print("\n" + "=" * 70)
    print("TEST 15: DELETE OK — revoca la key")
    print("=" * 70)
    r = client.delete(
        f"/bots/{_Ctx.bot1}/api-keys/{_Ctx.key1_id}",
        headers=_Ctx.headers1,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["id"] == _Ctx.key1_id
    print(f"  ✅ Key #{_Ctx.key1_id} revocada")


def test_get_after_delete_shows_inactive():
    print("\n" + "=" * 70)
    print("TEST 16: GET después de DELETE → is_active=False")
    print("=" * 70)
    r = client.get(f"/bots/{_Ctx.bot1}/api-keys", headers=_Ctx.headers1)
    assert r.status_code == 200
    key = r.json()["keys"][0]
    assert key["is_active"] is False
    assert key["revoked_at"] is not None
    print("  ✅ Key revocada visible con is_active=False")




# ============================================================
# CLEANUP
# ============================================================

def test_cleanup():
    print("\n" + "=" * 70)
    print("TEST CLEANUP: borrar datos residuales de este test file")
    print("=" * 70)
    from sqlalchemy import text
    from app.database.config import engine

    pattern = "apik_%"
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys=OFF"))
        for sql in [
            "DELETE FROM public_sessions WHERE bot_id IN (SELECT id FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p))",
            "DELETE FROM workflow_tests WHERE bot_id IN (SELECT id FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p))",
            "DELETE FROM workflow_transitions WHERE workflow_id IN (SELECT id FROM workflows WHERE bot_id IN (SELECT id FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p)))",
            "DELETE FROM workflow_nodes WHERE workflow_id IN (SELECT id FROM workflows WHERE bot_id IN (SELECT id FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p)))",
            "DELETE FROM workflows WHERE bot_id IN (SELECT id FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p))",
            "DELETE FROM conversations WHERE bot_id IN (SELECT id FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p))",
            "DELETE FROM source_chunks WHERE bot_id IN (SELECT id FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p))",
            "DELETE FROM sources WHERE bot_id IN (SELECT id FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p))",
            "DELETE FROM memories WHERE bot_id IN (SELECT id FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p))",
            "DELETE FROM memory_categories WHERE bot_id IN (SELECT id FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p))",
            "DELETE FROM api_keys WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p)",
            "DELETE FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p)",
            "DELETE FROM users WHERE email LIKE :p",
        ]:
            conn.execute(text(sql), {"p": pattern})
        conn.execute(text("PRAGMA foreign_keys=ON"))
    print(f"  ✅ Datos limpiados (pattern={pattern})")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.10.6 (Router api-keys)")
    print("=" * 70)

    tests = [
        test_setup,
        # GET
        test_get_401_no_token,
        test_get_403_other_user,
        test_get_404_bot_not_found,
        test_get_empty,
        # POST
        test_post_401_no_token,
        test_post_403_other_user,
        test_post_404_bot_not_found,
        test_post_422_empty_name,
        test_post_422_long_name,
        test_post_ok_returns_secret_once,
        test_get_after_post_does_not_leak_secret,
        # DELETE
        test_delete_401_no_token,
        test_delete_403_other_user,
        test_delete_404_key_not_found,
        test_delete_ok,
        test_get_after_delete_shows_inactive,
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
