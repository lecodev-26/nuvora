"""
Tests — Subfase 14.6.2
Backend Save Contract: PUT workflow completo transaccional.

Semántica:
    - PUT sin nodes → mantiene nodes existentes
    - PUT con nodes=[] → borra todos los nodes
    - PUT con nodes=[...] → replace-all
    - Igual para transitions
    - Validación completa ANTES de tocar la BD
    - Rollback total si falla
    - Multi-tenant estricto
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.main import app
from app.database.config import SessionLocal
from app.models.db_models import Workflow, WorkflowNode, WorkflowTransition


client = TestClient(app)


# ============================================================
# HELPERS
# ============================================================

def _unique(suffix: str) -> str:
    return f"{suffix}_{int(time.time() * 1000)}"


def _register_and_login(suffix: str):
    unique = _unique(suffix)
    email = f"test_put_{unique}@nuvora.com"
    password = "123456"

    r = client.post("/auth/register", json={
        "email": email,
        "password": password,
        "full_name": f"Test PUT {unique}",
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


def _create_bot(token: str, suffix: str) -> int:
    r = client.post(
        "/bots/",
        json={"name": f"Bot PUT {suffix}", "business_name": f"Test {suffix}", "nicho_id": "otro"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _valid_workflow():
    return {
        "name": "WF Original",
        "description": "desc",
        "status": "draft",
        "trigger": "manual",
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


def _count_db(workflow_id: int) -> tuple[int, int]:
    """Devuelve (num_nodes, num_transitions) directo de la BD."""
    db = SessionLocal()
    try:
        n = db.query(WorkflowNode).filter(WorkflowNode.workflow_id == workflow_id).count()
        t = db.query(WorkflowTransition).filter(WorkflowTransition.workflow_id == workflow_id).count()
        return n, t
    finally:
        db.close()


# ============================================================
# ESTADO COMPARTIDO
# ============================================================

class _Ctx:
    token1 = None
    token2 = None
    bot1 = None
    bot2 = None
    headers1 = None
    headers2 = None
    workflow_id = None


# ============================================================
# TESTS
# ============================================================

def test_setup():
    print("\n" + "=" * 70)
    print("SETUP")
    print("=" * 70)
    email1, t1, _ = _register_and_login("u1")
    email2, t2, _ = _register_and_login("u2")
    _Ctx.token1 = t1
    _Ctx.token2 = t2
    _Ctx.headers1 = {"Authorization": f"Bearer {t1}"}
    _Ctx.headers2 = {"Authorization": f"Bearer {t2}"}
    _Ctx.bot1 = _create_bot(t1, "bot1")
    _Ctx.bot2 = _create_bot(t2, "bot2")

    # Crear workflow base
    r = client.post(
        f"/workflows/{_Ctx.bot1}",
        json=_valid_workflow(),
        headers=_Ctx.headers1,
    )
    assert r.status_code == 200, r.text
    _Ctx.workflow_id = r.json()["id"]
    print(f"  ✅ bot1={_Ctx.bot1}, bot2={_Ctx.bot2}, wf={_Ctx.workflow_id}")


def test_put_metadata_only():
    """1. PUT solo metadata → mantiene nodes/transitions."""
    print("\n" + "=" * 70)
    print("TEST 1: PUT solo metadata → mantiene nodes/transitions")
    print("=" * 70)

    n_before, t_before = _count_db(_Ctx.workflow_id)

    r = client.put(
        f"/workflows/{_Ctx.bot1}/{_Ctx.workflow_id}",
        json={"name": "WF Renombrado", "status": "active"},
        headers=_Ctx.headers1,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["name"] == "WF Renombrado"
    assert data["status"] == "active"
    assert len(data["nodes"]) == n_before
    assert len(data["transitions"]) == t_before

    n_after, t_after = _count_db(_Ctx.workflow_id)
    assert n_after == n_before, f"nodes cambiaron: {n_before} → {n_after}"
    assert t_after == t_before, f"transitions cambiaron: {t_before} → {t_after}"
    print(f"  ✅ Metadata actualizada, nodes={n_after}, transitions={t_after} (intactos)")


def test_put_full_replace():
    """2. PUT completo → sustituye nodes/transitions."""
    print("\n" + "=" * 70)
    print("TEST 2: PUT completo → replace-all")
    print("=" * 70)

    new_payload = {
        "name": "WF Reemplazado",
        "nodes": [
            {"node_id": "a1", "type": "start"},
            {"node_id": "a2", "type": "message", "config": {"text": "Nuevo"}},
            {"node_id": "a3", "type": "response", "config": {"text": "Fin"}},
            {"node_id": "a4", "type": "end"},
        ],
        "transitions": [
            {"from_node_id": "a1", "to_node_id": "a2", "order": 0},
            {"from_node_id": "a2", "to_node_id": "a3", "order": 0},
            {"from_node_id": "a3", "to_node_id": "a4", "order": 0},
        ],
    }

    r = client.put(
        f"/workflows/{_Ctx.bot1}/{_Ctx.workflow_id}",
        json=new_payload,
        headers=_Ctx.headers1,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["name"] == "WF Reemplazado"
    assert len(data["nodes"]) == 4
    assert len(data["transitions"]) == 3
    node_ids = {n["node_id"] for n in data["nodes"]}
    assert node_ids == {"a1", "a2", "a3", "a4"}

    n_db, t_db = _count_db(_Ctx.workflow_id)
    assert n_db == 4
    assert t_db == 3
    print(f"  ✅ Replace-all OK: 4 nodos, 3 transiciones")


def test_put_nodes_empty():
    """3. PUT nodes=[] → borra todos los nodes."""
    print("\n" + "=" * 70)
    print("TEST 3: PUT nodes=[] → borra todos los nodes")
    print("=" * 70)

    r = client.put(
        f"/workflows/{_Ctx.bot1}/{_Ctx.workflow_id}",
        json={"nodes": [], "transitions": []},
        headers=_Ctx.headers1,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data["nodes"]) == 0
    assert len(data["transitions"]) == 0

    n_db, t_db = _count_db(_Ctx.workflow_id)
    assert n_db == 0, f"Deberían quedar 0 nodes, hay {n_db}"
    assert t_db == 0, f"Deberían quedar 0 transitions, hay {t_db}"
    print(f"  ✅ nodes=[] y transitions=[] → 0 nodos, 0 transiciones en BD")


def test_put_recreate():
    """Preparar el resto de tests: recrear workflow."""
    print("\n" + "=" * 70)
    print("SETUP 2: Recrear workflow")
    print("=" * 70)
    r = client.put(
        f"/workflows/{_Ctx.bot1}/{_Ctx.workflow_id}",
        json=_valid_workflow(),
        headers=_Ctx.headers1,
    )
    assert r.status_code == 200, r.text
    n_db, t_db = _count_db(_Ctx.workflow_id)
    assert n_db == 3 and t_db == 2
    print(f"  ✅ Workflow recreado: 3 nodos, 2 transiciones")


def test_put_transitions_empty():
    """4. PUT transitions=[] → borra solo transitions (mantiene nodes)."""
    print("\n" + "=" * 70)
    print("TEST 4: PUT transitions=[] → borra transitions, mantiene nodes")
    print("=" * 70)

    n_before, t_before = _count_db(_Ctx.workflow_id)
    assert t_before == 2

    r = client.put(
        f"/workflows/{_Ctx.bot1}/{_Ctx.workflow_id}",
        json={"transitions": []},
        headers=_Ctx.headers1,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data["nodes"]) == n_before
    assert len(data["transitions"]) == 0

    n_db, t_db = _count_db(_Ctx.workflow_id)
    assert n_db == n_before, f"nodes deberían seguir {n_before}, hay {n_db}"
    assert t_db == 0, f"transitions deberían ser 0, hay {t_db}"
    print(f"  ✅ transitions=[] → 0 transiciones, {n_db} nodos intactos")


def test_put_invalid_rollback():
    """5. PUT inválido → 400 y BD intacta."""
    print("\n" + "=" * 70)
    print("TEST 5: PUT inválido → 400 + BD intacta")
    print("=" * 70)

    # Estado actual: 3 nodos, 0 transiciones
    n_before, t_before = _count_db(_Ctx.workflow_id)
    assert n_before == 3

    # Payload inválido: nodos sin START
    invalid = {
        "name": "DEBERIA FALLAR",
        "nodes": [
            {"node_id": "x1", "type": "message", "config": {"text": "hola"}},
            {"node_id": "x2", "type": "end"},
        ],
        "transitions": [
            {"from_node_id": "x1", "to_node_id": "x2", "order": 0},
        ],
    }

    r = client.put(
        f"/workflows/{_Ctx.bot1}/{_Ctx.workflow_id}",
        json=invalid,
        headers=_Ctx.headers1,
    )
    assert r.status_code == 400, f"Esperaba 400, hubo {r.status_code}: {r.text}"
    assert "START" in r.text or "inválido" in r.text.lower()

    # Verificar que la BD NO cambió
    n_after, t_after = _count_db(_Ctx.workflow_id)
    assert n_after == n_before, f"nodes cambiaron: {n_before} → {n_after} (rollback falló)"
    assert t_after == t_before, f"transitions cambiaron: {t_before} → {t_after} (rollback falló)"

    # Verificar que el nombre NO cambió
    wf = client.get(
        f"/workflows/{_Ctx.bot1}/{_Ctx.workflow_id}",
        headers=_Ctx.headers1,
    ).json()
    assert wf["name"] != "DEBERIA FALLAR", f"El nombre cambió a {wf['name']} (rollback falló)"

    print(f"  ✅ 400 + BD intacta: {n_after} nodos, {t_after} transiciones, nombre='{wf['name']}'")


def test_put_condition_invalid_rollback():
    """6. PUT con condición inválida → 400 + BD intacta."""
    print("\n" + "=" * 70)
    print("TEST 6: PUT con condición inválida → 400 + BD intacta")
    print("=" * 70)

    n_before, t_before = _count_db(_Ctx.workflow_id)

    # Condición sintácticamente inválida
    invalid = {
        "nodes": [
            {"node_id": "s1", "type": "start"},
            {"node_id": "c1", "type": "condition", "config": {"condition": "age > 18"}},
            {"node_id": "ma", "type": "message", "config": {"text": "A"}},
            {"node_id": "mb", "type": "message", "config": {"text": "B"}},
            {"node_id": "e1", "type": "end"},
        ],
        "transitions": [
            {"from_node_id": "s1", "to_node_id": "c1"},
            {"from_node_id": "c1", "to_node_id": "ma", "condition": "age 18"},  # MAL
            {"from_node_id": "c1", "to_node_id": "mb", "condition": "age <= 18"},
            {"from_node_id": "ma", "to_node_id": "e1"},
            {"from_node_id": "mb", "to_node_id": "e1"},
        ],
    }

    r = client.put(
        f"/workflows/{_Ctx.bot1}/{_Ctx.workflow_id}",
        json=invalid,
        headers=_Ctx.headers1,
    )
    assert r.status_code == 400, f"Esperaba 400, hubo {r.status_code}: {r.text}"

    n_after, t_after = _count_db(_Ctx.workflow_id)
    assert n_after == n_before
    assert t_after == t_before
    print(f"  ✅ 400 por condición inválida + BD intacta")


def test_put_multi_tenant():
    """7. PUT con user distinto → 403."""
    print("\n" + "=" * 70)
    print("TEST 7: PUT multi-tenant → 403")
    print("=" * 70)

    r = client.put(
        f"/workflows/{_Ctx.bot1}/{_Ctx.workflow_id}",
        json={"name": "Intento"},
        headers=_Ctx.headers2,  # user2 intentando tocar workflow de user1
    )
    assert r.status_code == 403, f"Esperaba 403, hubo {r.status_code}"
    print(f"  ✅ 403")


def test_put_not_found():
    """8. PUT workflow inexistente → 404."""
    print("\n" + "=" * 70)
    print("TEST 8: PUT workflow inexistente → 404")
    print("=" * 70)

    r = client.put(
        f"/workflows/{_Ctx.bot1}/999999",
        json={"name": "no existe"},
        headers=_Ctx.headers1,
    )
    assert r.status_code == 404, f"Esperaba 404, hubo {r.status_code}"
    print(f"  ✅ 404")


def test_put_no_auth():
    """9. PUT sin auth → 401."""
    print("\n" + "=" * 70)
    print("TEST 9: PUT sin auth → 401")
    print("=" * 70)

    r = client.put(
        f"/workflows/{_Ctx.bot1}/{_Ctx.workflow_id}",
        json={"name": "sin token"},
    )
    assert r.status_code == 401, f"Esperaba 401, hubo {r.status_code}"
    print(f"  ✅ 401")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.6.2 (PUT workflow completo)")
    print("=" * 70)

    tests = [
        test_setup,
        test_put_metadata_only,
        test_put_full_replace,
        test_put_nodes_empty,
        test_put_recreate,
        test_put_transitions_empty,
        test_put_invalid_rollback,
        test_put_condition_invalid_rollback,
        test_put_multi_tenant,
        test_put_not_found,
        test_put_no_auth,
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
