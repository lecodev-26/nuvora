"""
Tests — Subfase 14.5.7
Verifica el router CRUD de workflows.

Patrón: igual que test_integration_14_4_9.py — usa SessionLocal real y API.
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.main import app
from app.database.config import SessionLocal
from app.models.db_models import Bot, Workflow, WorkflowNode, WorkflowTransition


client = TestClient(app)


# ============================================================
# HELPERS
# ============================================================

def _unique(suffix: str) -> str:
    return f"{suffix}_{int(time.time() * 1000)}"


def _register_and_login(suffix: str) -> tuple[str, str, int]:
    """Registra y loguea usuario. Devuelve (email, token, user_id)."""
    unique = _unique(suffix)
    email = f"test_wf_{unique}@nuvora.com"
    password = "123456"

    r = client.post("/auth/register", json={
        "email": email,
        "password": password,
        "full_name": f"Test WF {unique}",
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


def _create_bot(token: str, name_suffix: str) -> int:
    """Crea bot vía API."""
    unique = _unique(name_suffix)
    r = client.post(
        "/bots/",
        json={
            "name": f"Bot WF {unique}",
            "business_name": f"Test {unique}",
            "nicho_id": "otro",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _valid_workflow_payload():
    return {
        "name": "WF Test",
        "description": "Un workflow simple",
        "status": "draft",
        "trigger": "manual",
        "nodes": [
            {"node_id": "s1", "type": "start"},
            {"node_id": "m1", "type": "message", "config": {"text": "Hola {{name}}"}},
            {"node_id": "e1", "type": "end"},
        ],
        "transitions": [
            {"from_node_id": "s1", "to_node_id": "m1", "order": 0},
            {"from_node_id": "m1", "to_node_id": "e1", "order": 0},
        ],
    }


# ============================================================
# ESTADO COMPARTIDO
# ============================================================

class _Ctx:
    token1 = None
    token2 = None
    user1_id = None
    user2_id = None
    bot1 = None
    bot2 = None
    workflow_id = None
    headers1 = None
    headers2 = None


# ============================================================
# TESTS
# ============================================================

def test_setup():
    print("\n" + "=" * 70)
    print("SETUP: Registrar usuarios y crear bots vía API")
    print("=" * 70)
    email1, token1, user1_id = _register_and_login("u1")
    email2, token2, user2_id = _register_and_login("u2")

    _Ctx.token1 = token1
    _Ctx.token2 = token2
    _Ctx.user1_id = user1_id
    _Ctx.user2_id = user2_id
    _Ctx.headers1 = {"Authorization": f"Bearer {token1}"}
    _Ctx.headers2 = {"Authorization": f"Bearer {token2}"}

    _Ctx.bot1 = _create_bot(token1, "bot1")
    _Ctx.bot2 = _create_bot(token2, "bot2")

    print(f"  ✅ user1 id={user1_id}, user2 id={user2_id}")
    print(f"  ✅ bot1 id={_Ctx.bot1}, bot2 id={_Ctx.bot2}")


def test_create_without_auth():
    print("\n" + "=" * 70)
    print("TEST 1: POST sin auth → 401")
    print("=" * 70)
    r = client.post(f"/workflows/{_Ctx.bot1}", json=_valid_workflow_payload())
    assert r.status_code == 401, f"Status: {r.status_code} — {r.text}"
    print(f"✅ 401")


def test_list_without_auth():
    print("\n" + "=" * 70)
    print("TEST 2: GET sin auth → 401")
    print("=" * 70)
    r = client.get(f"/workflows/{_Ctx.bot1}")
    assert r.status_code == 401
    print(f"✅ 401")


def test_create_bot_missing():
    print("\n" + "=" * 70)
    print("TEST 3: POST bot inexistente → 404")
    print("=" * 70)
    r = client.post(
        "/workflows/999999",
        json=_valid_workflow_payload(),
        headers=_Ctx.headers1,
    )
    assert r.status_code == 404, f"Status: {r.status_code} — {r.text}"
    print(f"✅ 404")


def test_create_bot_not_owned():
    print("\n" + "=" * 70)
    print("TEST 4: POST bot de otro user → 403")
    print("=" * 70)
    r = client.post(
        f"/workflows/{_Ctx.bot2}",
        json=_valid_workflow_payload(),
        headers=_Ctx.headers1,
    )
    assert r.status_code == 403, f"Status: {r.status_code} — {r.text}"
    print(f"✅ 403")


def test_create_invalid_no_start():
    print("\n" + "=" * 70)
    print("TEST 5: POST workflow sin START → 400")
    print("=" * 70)
    payload = _valid_workflow_payload()
    payload["nodes"] = [
        {"node_id": "m1", "type": "message", "config": {"text": "Hola"}},
        {"node_id": "e1", "type": "end"},
    ]
    payload["transitions"] = [
        {"from_node_id": "m1", "to_node_id": "e1"},
    ]
    r = client.post(
        f"/workflows/{_Ctx.bot1}",
        json=payload,
        headers=_Ctx.headers1,
    )
    assert r.status_code == 400, f"Status: {r.status_code} — {r.text}"
    print(f"✅ 400: {r.json()['detail'][:80]}...")


def test_create_invalid_condition():
    print("\n" + "=" * 70)
    print("TEST 6: POST con condición inválida → 400")
    print("=" * 70)
    payload = _valid_workflow_payload()
    payload["nodes"] = [
        {"node_id": "s1", "type": "start"},
        {"node_id": "c1", "type": "condition", "config": {"condition": "age > 18"}},
        {"node_id": "m1", "type": "message", "config": {"text": "Adulto"}},
        {"node_id": "m2", "type": "message", "config": {"text": "Menor"}},
        {"node_id": "e1", "type": "end"},
    ]
    payload["transitions"] = [
        {"from_node_id": "s1", "to_node_id": "c1"},
        {"from_node_id": "c1", "to_node_id": "m1", "order": 1, "condition": "age 18"},
        {"from_node_id": "c1", "to_node_id": "m2", "order": 2, "condition": "age <= 18"},
        {"from_node_id": "m1", "to_node_id": "e1"},
        {"from_node_id": "m2", "to_node_id": "e1"},
    ]
    r = client.post(
        f"/workflows/{_Ctx.bot1}",
        json=payload,
        headers=_Ctx.headers1,
    )
    assert r.status_code == 400, f"Status: {r.status_code} — {r.text}"
    print(f"✅ 400: {r.json()['detail'][:80]}...")


def test_create_valid_workflow():
    print("\n" + "=" * 70)
    print("TEST 7: POST workflow válido → OK")
    print("=" * 70)
    r = client.post(
        f"/workflows/{_Ctx.bot1}",
        json=_valid_workflow_payload(),
        headers=_Ctx.headers1,
    )
    assert r.status_code == 200, f"Status: {r.status_code} — {r.text}"
    data = r.json()
    assert data["name"] == "WF Test"
    assert data["bot_id"] == _Ctx.bot1
    assert len(data["nodes"]) == 3
    assert len(data["transitions"]) == 2
    _Ctx.workflow_id = data["id"]
    print(f"✅ Workflow creado id={data['id']} con {len(data['nodes'])} nodos")


def test_list_workflows():
    print("\n" + "=" * 70)
    print("TEST 8: GET lista workflows")
    print("=" * 70)
    r = client.get(
        f"/workflows/{_Ctx.bot1}",
        headers=_Ctx.headers1,
    )
    assert r.status_code == 200, f"Status: {r.status_code} — {r.text}"
    data = r.json()
    assert "workflows" in data
    assert "total" in data
    assert data["total"] >= 1
    print(f"✅ {data['total']} workflows listados")


def test_get_workflow():
    print("\n" + "=" * 70)
    print("TEST 9: GET workflow individual")
    print("=" * 70)
    r = client.get(
        f"/workflows/{_Ctx.bot1}/{_Ctx.workflow_id}",
        headers=_Ctx.headers1,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == _Ctx.workflow_id
    assert len(data["nodes"]) == 3
    print(f"✅ Workflow {data['id']} con {len(data['nodes'])} nodos")


def test_update_workflow():
    print("\n" + "=" * 70)
    print("TEST 10: PUT actualizar workflow")
    print("=" * 70)
    r = client.put(
        f"/workflows/{_Ctx.bot1}/{_Ctx.workflow_id}",
        json={"name": "WF Renombrado", "status": "active"},
        headers=_Ctx.headers1,
    )
    assert r.status_code == 200, f"Status: {r.status_code} — {r.text}"
    data = r.json()
    assert data["name"] == "WF Renombrado"
    assert data["status"] == "active"
    print(f"✅ Actualizado: '{data['name']}', status='{data['status']}'")


def test_run_workflow():
    print("\n" + "=" * 70)
    print("TEST 11: POST /run ejecutar workflow")
    print("=" * 70)
    r = client.post(
        f"/workflows/{_Ctx.bot1}/{_Ctx.workflow_id}/run",
        json={"initial_variables": {"name": "Manuel"}, "max_steps": 50},
        headers=_Ctx.headers1,
    )
    assert r.status_code == 200, f"Status: {r.status_code} — {r.text}"
    data = r.json()
    assert data["status"] == "completed"
    assert len(data["outputs"]) == 1
    assert data["outputs"][0]["text"] == "Hola Manuel"
    print(f"✅ Run OK: {data['outputs']}")


def test_delete_workflow():
    print("\n" + "=" * 70)
    print("TEST 12: DELETE workflow")
    print("=" * 70)
    r = client.delete(
        f"/workflows/{_Ctx.bot1}/{_Ctx.workflow_id}",
        headers=_Ctx.headers1,
    )
    assert r.status_code == 200
    print(f"✅ Eliminado: {r.json()}")


def test_get_after_delete():
    print("\n" + "=" * 70)
    print("TEST 13: GET tras DELETE → 404")
    print("=" * 70)
    r = client.get(
        f"/workflows/{_Ctx.bot1}/{_Ctx.workflow_id}",
        headers=_Ctx.headers1,
    )
    assert r.status_code == 404
    print(f"✅ 404 (workflow ya no existe)")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.5.7 (Workflow Router CRUD)")
    print("=" * 70)

    tests = [
        test_setup,
        test_create_without_auth,
        test_list_without_auth,
        test_create_bot_missing,
        test_create_bot_not_owned,
        test_create_invalid_no_start,
        test_create_invalid_condition,
        test_create_valid_workflow,
        test_list_workflows,
        test_get_workflow,
        test_update_workflow,
        test_run_workflow,
        test_delete_workflow,
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
