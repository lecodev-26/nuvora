"""
Tests — Subfase 14.8.7 (Router /bots/{bot_id}/tests)
"""

import sys
import os
import time
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.database.config import SessionLocal


client = TestClient(app)


# ============================================================
# HELPERS
# ============================================================

def _unique(suffix):
    return f"{suffix}_{int(time.time() * 1000)}"


def _setup_user_bot_workflow():
    """Crea usuario + bot + workflow via API."""
    unique = _unique("u")
    email = f"test_{unique}@nuvora.com"
    password = "123456"

    r = client.post("/auth/register", json={
        "email": email, "password": password, "full_name": "Test",
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
    assert r.status_code == 200, r.text
    bot_id = r.json()["id"]

    # Crear workflow con START → MESSAGE → END
    r = client.post(f"/workflows/{bot_id}", json={
        "name": "WF Test",
        "nodes": [
            {"node_id": "s1", "type": "start"},
            {"node_id": "m1", "type": "message", "config": {"text": "Hola Manuel"}},
            {"node_id": "e1", "type": "end"},
        ],
        "transitions": [
            {"from_node_id": "s1", "to_node_id": "m1", "order": 0},
            {"from_node_id": "m1", "to_node_id": "e1", "order": 0},
        ],
    }, headers=headers)
    assert r.status_code == 200, r.text
    wf_id = r.json()["id"]

    return headers, bot_id, wf_id


def _test_payload():
    return {
        "name": "Test saludo",
        "description": "Verifica que el bot saluda",
        "input_messages": ["Hola"],
        "initial_variables": {},
        "assertions": [
            {"type": "response_contains", "value": "Manuel"},
            {"type": "reaches_end"},
        ],
        "enabled": True,
    }


# ============================================================
# ESTADO COMPARTIDO
# ============================================================

class _Ctx:
    headers = None
    bot_id = None
    workflow_id = None
    test_id = None


# ============================================================
# TESTS
# ============================================================

def test_setup():
    print("\n" + "=" * 70)
    print("SETUP: usuario + bot + workflow")
    print("=" * 70)
    headers, bot_id, wf_id = _setup_user_bot_workflow()
    _Ctx.headers = headers
    _Ctx.bot_id = bot_id
    _Ctx.workflow_id = wf_id
    print(f"  ✅ bot_id={bot_id}, workflow_id={wf_id}")


def test_create_test_no_auth():
    print("\n" + "=" * 70)
    print("TEST 1: POST /tests sin auth → 401")
    print("=" * 70)
    r = client.post(
        f"/bots/{_Ctx.bot_id}/tests?workflow_id={_Ctx.workflow_id}",
        json=_test_payload(),
    )
    assert r.status_code == 401
    print(f"  ✅ 401")


def test_create_test_bot_not_found():
    print("\n" + "=" * 70)
    print("TEST 2: POST bot inexistente → 404")
    print("=" * 70)
    r = client.post(
        "/bots/999999/tests?workflow_id=1",
        json=_test_payload(),
        headers=_Ctx.headers,
    )
    assert r.status_code == 404
    print(f"  ✅ 404")


def test_create_test():
    print("\n" + "=" * 70)
    print("TEST 3: POST /tests válido")
    print("=" * 70)
    r = client.post(
        f"/bots/{_Ctx.bot_id}/tests?workflow_id={_Ctx.workflow_id}",
        json=_test_payload(),
        headers=_Ctx.headers,
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["name"] == "Test saludo"
    assert len(data["input_messages"]) == 1
    assert len(data["assertions"]) == 2
    _Ctx.test_id = data["id"]
    print(f"  ✅ Test creado id={data['id']}")


def test_list_tests():
    print("\n" + "=" * 70)
    print("TEST 4: GET /tests")
    print("=" * 70)
    r = client.get(f"/bots/{_Ctx.bot_id}/tests", headers=_Ctx.headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    print(f"  ✅ {data['total']} tests")


def test_get_test():
    print("\n" + "=" * 70)
    print("TEST 5: GET /tests/{test_id}")
    print("=" * 70)
    r = client.get(
        f"/bots/{_Ctx.bot_id}/tests/{_Ctx.test_id}",
        headers=_Ctx.headers,
    )
    assert r.status_code == 200
    assert r.json()["id"] == _Ctx.test_id
    print(f"  ✅ Test obtenido")


def test_run_test():
    print("\n" + "=" * 70)
    print("TEST 6: POST /tests/{test_id}/run")
    print("=" * 70)
    r = client.post(
        f"/bots/{_Ctx.bot_id}/tests/{_Ctx.test_id}/run",
        headers=_Ctx.headers,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "passed", data
    assert data["assertions_passed"] == 2
    assert data["assertions_failed"] == 0
    assert len(data["nodes_visited"]) == 3
    assert "Hola Manuel" in data["responses"]
    print(f"  ✅ PASSED: {data['assertions_passed']} assertions, {data['steps_used']} steps")


def test_run_all():
    print("\n" + "=" * 70)
    print("TEST 7: POST /tests/run-all")
    print("=" * 70)
    r = client.post(
        f"/bots/{_Ctx.bot_id}/tests/run-all?workflow_id={_Ctx.workflow_id}",
        headers=_Ctx.headers,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["total"] >= 1
    assert data["passed"] >= 1
    print(f"  ✅ {data['passed']}/{data['total']} passed")


def test_analyze():
    print("\n" + "=" * 70)
    print("TEST 8: POST /tests/analyze")
    print("=" * 70)
    r = client.post(
        f"/bots/{_Ctx.bot_id}/tests/analyze?workflow_id={_Ctx.workflow_id}",
        headers=_Ctx.headers,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "summary" in data
    assert data["summary"]["error"] == 0
    print(f"  ✅ {data['summary']}")


def test_update_test():
    print("\n" + "=" * 70)
    print("TEST 9: PUT /tests/{test_id}")
    print("=" * 70)
    r = client.put(
        f"/bots/{_Ctx.bot_id}/tests/{_Ctx.test_id}",
        json={"name": "Test renombrado", "enabled": False},
        headers=_Ctx.headers,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["name"] == "Test renombrado"
    assert data["enabled"] is False
    print(f"  ✅ Actualizado")


def test_run_all_excludes_disabled():
    print("\n" + "=" * 70)
    print("TEST 10: run-all no ejecuta tests deshabilitados")
    print("=" * 70)
    r = client.post(
        f"/bots/{_Ctx.bot_id}/tests/run-all?workflow_id={_Ctx.workflow_id}&enabled_only=true",
        headers=_Ctx.headers,
    )
    data = r.json()
    # Como el único test está disabled, total debe ser 0
    assert data["total"] == 0
    print(f"  ✅ 0 tests ejecutados (todos disabled)")


def test_delete_test():
    print("\n" + "=" * 70)
    print("TEST 11: DELETE /tests/{test_id}")
    print("=" * 70)
    r = client.delete(
        f"/bots/{_Ctx.bot_id}/tests/{_Ctx.test_id}",
        headers=_Ctx.headers,
    )
    assert r.status_code == 200
    print(f"  ✅ Eliminado")


def test_get_after_delete():
    print("\n" + "=" * 70)
    print("TEST 12: GET tras DELETE → 404")
    print("=" * 70)
    r = client.get(
        f"/bots/{_Ctx.bot_id}/tests/{_Ctx.test_id}",
        headers=_Ctx.headers,
    )
    assert r.status_code == 404
    print(f"  ✅ 404")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.8.7 (Router /bots/{bot_id}/tests)")
    print("=" * 70)

    tests = [
        test_setup,
        test_create_test_no_auth,
        test_create_test_bot_not_found,
        test_create_test,
        test_list_tests,
        test_get_test,
        test_run_test,
        test_run_all,
        test_analyze,
        test_update_test,
        test_run_all_excludes_disabled,
        test_delete_test,
        test_get_after_delete,
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
