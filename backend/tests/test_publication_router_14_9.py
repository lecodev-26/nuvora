"""
Tests — Subfase 14.9.5 (Endpoints privados de Publicación)
============================================================
Cubre:
    1. 401 sin token (todos los endpoints)
    2. 404 bot inexistente
    3. 403 bot ajeno (multi-tenant)
    4. GET /publication → bot sin publicar (is_published=false)
    5. PUT /publication → guarda config
    6. POST /publish sin workflow activo → 400
    7. POST /publish con 2 workflows activos → 400
    8. POST /publish con workflow activo INVÁLIDO → 400
    9. POST /publish OK → is_published=true, public_id, public_slug, URL
    10. POST /publish idempotente → mismo public_id
    11. POST /unpublish OK → is_published=false, mantiene public_id
    12. POST /unpublish idempotente
    13. Regresión: app sigue OK
"""

import sys
import os
import time
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.database.config import SessionLocal
from app.models.db_models import Bot


client = TestClient(app)


# ============================================================
# HELPERS
# ============================================================

def _unique(suffix):
    return f"{suffix}_{int(time.time() * 1000000)}"


def _register_and_login(suffix):
    unique = _unique(suffix)
    email = f"pub_{unique}@nuvora.com"
    password = "123456"
    r = client.post("/auth/register", json={
        "email": email, "password": password, "full_name": "Pub Test",
    })
    assert r.status_code == 200, r.text
    token = client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, email


def _create_bot(headers, suffix="bot"):
    unique = _unique(suffix)
    r = client.post("/bots/", json={
        "name": f"Bot Pub {unique}", "business_name": "T", "nicho_id": "otro",
    }, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _create_workflow(headers, bot_id, status="draft"):
    r = client.post(f"/workflows/{bot_id}", json={
        "name": "WF Pub",
        "status": status,
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
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _set_workflow_status(headers, bot_id, wf_id, new_status):
    r = client.put(f"/workflows/{bot_id}/{wf_id}", json={
        "status": new_status,
    }, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


# ============================================================
# ESTADO COMPARTIDO
# ============================================================

class _Ctx:
    headers1 = None
    headers2 = None
    bot1 = None
    bot2 = None
    wf1 = None


# ============================================================
# SETUP
# ============================================================

def test_setup():
    print("\n" + "=" * 70)
    print("SETUP: 2 usuarios, bot1 (user1), bot2 (user2), wf1 (draft)")
    print("=" * 70)
    _Ctx.headers1, _ = _register_and_login("u1")
    _Ctx.headers2, _ = _register_and_login("u2")
    _Ctx.bot1 = _create_bot(_Ctx.headers1, "b1")
    _Ctx.bot2 = _create_bot(_Ctx.headers2, "b2")
    _Ctx.wf1 = _create_workflow(_Ctx.headers1, _Ctx.bot1, status="draft")
    print(f"  ✅ bot1={_Ctx.bot1}, bot2={_Ctx.bot2}, wf1={_Ctx.wf1}")


# ============================================================
# 401 sin token
# ============================================================

def test_401_get_publication():
    print("\n" + "=" * 70)
    print("TEST 1: GET /publication sin token → 401")
    print("=" * 70)
    r = client.get(f"/bots/{_Ctx.bot1}/publication")
    assert r.status_code == 401, f"Esperaba 401, hubo {r.status_code}"
    print("  ✅ 401")


def test_401_put_publication():
    print("\n" + "=" * 70)
    print("TEST 2: PUT /publication sin token → 401")
    print("=" * 70)
    r = client.put(f"/bots/{_Ctx.bot1}/publication", json={"config": {}})
    assert r.status_code == 401
    print("  ✅ 401")


def test_401_post_publish():
    print("\n" + "=" * 70)
    print("TEST 3: POST /publish sin token → 401")
    print("=" * 70)
    r = client.post(f"/bots/{_Ctx.bot1}/publish")
    assert r.status_code == 401
    print("  ✅ 401")


def test_401_post_unpublish():
    print("\n" + "=" * 70)
    print("TEST 4: POST /unpublish sin token → 401")
    print("=" * 70)
    r = client.post(f"/bots/{_Ctx.bot1}/unpublish")
    assert r.status_code == 401
    print("  ✅ 401")


# ============================================================
# 404 bot inexistente
# ============================================================

def test_404_get_publication():
    print("\n" + "=" * 70)
    print("TEST 5: GET /publication bot inexistente → 404")
    print("=" * 70)
    r = client.get("/bots/999999999/publication", headers=_Ctx.headers1)
    assert r.status_code == 404
    print("  ✅ 404")


def test_404_post_publish():
    print("\n" + "=" * 70)
    print("TEST 6: POST /publish bot inexistente → 404")
    print("=" * 70)
    r = client.post("/bots/999999999/publish", headers=_Ctx.headers1)
    assert r.status_code == 404
    print("  ✅ 404")


# ============================================================
# 403 multi-tenant
# ============================================================

def test_403_get_publication_other_user():
    print("\n" + "=" * 70)
    print("TEST 7: GET /publication de bot ajeno → 403")
    print("=" * 70)
    r = client.get(f"/bots/{_Ctx.bot1}/publication", headers=_Ctx.headers2)
    assert r.status_code == 403
    print("  ✅ 403")


def test_403_put_publication_other_user():
    print("\n" + "=" * 70)
    print("TEST 8: PUT /publication de bot ajeno → 403")
    print("=" * 70)
    r = client.put(
        f"/bots/{_Ctx.bot1}/publication",
        json={"config": {"welcome_message": "hack"}},
        headers=_Ctx.headers2,
    )
    assert r.status_code == 403
    print("  ✅ 403")


def test_403_publish_other_user():
    print("\n" + "=" * 70)
    print("TEST 9: POST /publish de bot ajeno → 403")
    print("=" * 70)
    r = client.post(f"/bots/{_Ctx.bot1}/publish", headers=_Ctx.headers2)
    assert r.status_code == 403
    print("  ✅ 403")


def test_403_unpublish_other_user():
    print("\n" + "=" * 70)
    print("TEST 10: POST /unpublish de bot ajeno → 403")
    print("=" * 70)
    r = client.post(f"/bots/{_Ctx.bot1}/unpublish", headers=_Ctx.headers2)
    assert r.status_code == 403
    print("  ✅ 403")


# ============================================================
# GET /publication (bot sin publicar)
# ============================================================

def test_get_publication_not_published():
    print("\n" + "=" * 70)
    print("TEST 11: GET /publication bot sin publicar")
    print("=" * 70)
    r = client.get(f"/bots/{_Ctx.bot1}/publication", headers=_Ctx.headers1)
    assert r.status_code == 200
    data = r.json()
    assert data["bot_id"] == _Ctx.bot1
    assert data["is_published"] is False
    assert data["public_id"] is None
    assert data["public_slug"] is None
    assert data["published_at"] is None
    assert data["public_url"] is None
    assert data["config"]["show_branding"] is True
    print(f"  ✅ is_published=False, config default OK")


# ============================================================
# PUT /publication
# ============================================================

def test_put_publication():
    print("\n" + "=" * 70)
    print("TEST 12: PUT /publication guarda config")
    print("=" * 70)
    r = client.put(
        f"/bots/{_Ctx.bot1}/publication",
        json={
            "config": {
                "welcome_message": "¡Hola desde el test!",
                "placeholder": "Escribe aquí...",
                "primary_color": "#FF00AA",
                "show_branding": False,
            }
        },
        headers=_Ctx.headers1,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["config"]["welcome_message"] == "¡Hola desde el test!"
    assert data["config"]["primary_color"] == "#FF00AA"
    assert data["config"]["show_branding"] is False
    print(f"  ✅ Config guardada")


def test_put_publication_invalid_color():
    print("\n" + "=" * 70)
    print("TEST 13: PUT /publication con color inválido → 422")
    print("=" * 70)
    r = client.put(
        f"/bots/{_Ctx.bot1}/publication",
        json={"config": {"primary_color": "not-a-color"}},
        headers=_Ctx.headers1,
    )
    assert r.status_code == 422
    print("  ✅ 422")


# ============================================================
# POST /publish — errores
# ============================================================

def test_publish_without_active_workflow():
    print("\n" + "=" * 70)
    print("TEST 14: POST /publish sin workflow activo → 400")
    print("=" * 70)
    # El bot1 solo tiene wf1 en "draft"
    r = client.post(f"/bots/{_Ctx.bot1}/publish", headers=_Ctx.headers1)
    assert r.status_code == 400, f"Esperaba 400, hubo {r.status_code}: {r.text}"
    assert "no tiene ningún workflow activo" in r.json()["detail"].lower() or "workflow activo" in r.json()["detail"].lower()
    print(f"  ✅ 400: {r.json()['detail'][:60]}")


def test_publish_with_two_active_workflows():
    print("\n" + "=" * 70)
    print("TEST 15: POST /publish con 2 workflows activos → 400")
    print("=" * 70)
    # Activamos wf1 + creamos otro activo
    _set_workflow_status(_Ctx.headers1, _Ctx.bot1, _Ctx.wf1, "active")
    wf_extra = _create_workflow(_Ctx.headers1, _Ctx.bot1, status="draft")
    _set_workflow_status(_Ctx.headers1, _Ctx.bot1, wf_extra, "active")

    r = client.post(f"/bots/{_Ctx.bot1}/publish", headers=_Ctx.headers1)
    assert r.status_code == 400, f"Esperaba 400, hubo {r.status_code}: {r.text}"
    assert "workflows activos" in r.json()["detail"].lower()

    # Limpieza: archivar wf_extra
    _set_workflow_status(_Ctx.headers1, _Ctx.bot1, wf_extra, "archived")
    print(f"  ✅ 400: {r.json()['detail'][:60]}")


def test_publish_with_invalid_workflow():
    print("\n" + "=" * 70)
    print("TEST 16: POST /publish con workflow activo INVÁLIDO → 400")
    print("=" * 70)
    # Creamos un bot nuevo con workflow activo inválido (sin START)
    # Nota: el router no permite crear workflows inválidos, así que
    # forzamos uno directamente en BD.
    headers_test, _ = _register_and_login("invalid")
    bot_test = _create_bot(headers_test, "inv")

    db = SessionLocal()
    try:
        from app.models.db_models import Workflow, WorkflowNode, WorkflowTransition

        wf = Workflow(bot_id=bot_test, name="Invalid", status="active")
        db.add(wf)
        db.flush()
        # Sin START (solo message + end)
        db.add(WorkflowNode(
            workflow_id=wf.id, node_id="m1", type="message",
            config=json.dumps({"text": "x"}),
        ))
        db.add(WorkflowNode(
            workflow_id=wf.id, node_id="e1", type="end",
        ))
        db.add(WorkflowTransition(
            workflow_id=wf.id, from_node_id="m1", to_node_id="e1", order=0,
        ))
        db.commit()

        r = client.post(f"/bots/{bot_test}/publish", headers=headers_test)
        assert r.status_code == 400, f"Esperaba 400, hubo {r.status_code}: {r.text}"
        assert "no es válido" in r.json()["detail"].lower() or "inválido" in r.json()["detail"].lower()
        print(f"  ✅ 400: {r.json()['detail'][:80]}")
    finally:
        db.close()
        # Limpieza
        db = SessionLocal()
        try:
            b = db.query(Bot).filter(Bot.id == bot_test).first()
            if b:
                db.delete(b)
                db.commit()
        finally:
            db.close()


# ============================================================
# POST /publish OK
# ============================================================

def test_publish_ok():
    print("\n" + "=" * 70)
    print("TEST 17: POST /publish OK → is_published=true + URL")
    print("=" * 70)
    # Aseguramos que wf1 está activo y es el único
    _set_workflow_status(_Ctx.headers1, _Ctx.bot1, _Ctx.wf1, "active")

    r = client.post(f"/bots/{_Ctx.bot1}/publish", headers=_Ctx.headers1)
    assert r.status_code == 200, f"Esperaba 200, hubo {r.status_code}: {r.text}"
    data = r.json()

    assert data["bot_id"] == _Ctx.bot1
    assert data["is_published"] is True
    assert data["public_id"]
    assert len(data["public_id"]) == 36
    assert data["public_slug"]
    assert data["published_at"]
    assert data["public_url"].startswith("https://")
    assert "/b/" in data["public_url"]

    _Ctx.public_id = data["public_id"]
    _Ctx.public_slug = data["public_slug"]
    _Ctx.public_url = data["public_url"]

    print(f"  ✅ public_url: {data['public_url']}")
    print(f"  ✅ public_id: {data['public_id']}")
    print(f"  ✅ public_slug: {data['public_slug']}")


# ============================================================
# POST /publish idempotente
# ============================================================

def test_publish_idempotent():
    print("\n" + "=" * 70)
    print("TEST 18: POST /publish de nuevo → mismo public_id/slug")
    print("=" * 70)
    r = client.post(f"/bots/{_Ctx.bot1}/publish", headers=_Ctx.headers1)
    assert r.status_code == 200
    data = r.json()
    assert data["public_id"] == _Ctx.public_id, f"public_id cambió: {data['public_id']} ≠ {_Ctx.public_id}"
    assert data["public_slug"] == _Ctx.public_slug
    print("  ✅ public_id y public_slug no cambian (idempotente)")


# ============================================================
# POST /unpublish
# ============================================================

def test_unpublish_ok():
    print("\n" + "=" * 70)
    print("TEST 19: POST /unpublish → is_published=false, mantiene public_id")
    print("=" * 70)
    r = client.post(f"/bots/{_Ctx.bot1}/unpublish", headers=_Ctx.headers1)
    assert r.status_code == 200
    data = r.json()
    assert data["is_published"] is False
    assert data["public_id"] == _Ctx.public_id, "public_id no debe cambiar al despublicar"
    assert data["public_slug"] == _Ctx.public_slug
    print(f"  ✅ is_published=False, public_id mantenido")


def test_unpublish_idempotent():
    print("\n" + "=" * 70)
    print("TEST 20: POST /unpublish de nuevo → idempotente")
    print("=" * 70)
    r = client.post(f"/bots/{_Ctx.bot1}/unpublish", headers=_Ctx.headers1)
    assert r.status_code == 200
    data = r.json()
    assert data["is_published"] is False
    print("  ✅ idempotente")


# ============================================================
# Regresión
# ============================================================

def test_regression_app_ok():
    print("\n" + "=" * 70)
    print("TEST 21: Regresión — app.main sigue OK")
    print("=" * 70)
    from app.main import app as _app
    assert _app is not None
    print(f"  ✅ app OK ({len(_app.routes)} rutas contenedoras)")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.9.5 (Endpoints privados de Publicación)")
    print("=" * 70)

    tests = [
        test_setup,
        # 401
        test_401_get_publication,
        test_401_put_publication,
        test_401_post_publish,
        test_401_post_unpublish,
        # 404
        test_404_get_publication,
        test_404_post_publish,
        # 403
        test_403_get_publication_other_user,
        test_403_put_publication_other_user,
        test_403_publish_other_user,
        test_403_unpublish_other_user,
        # GET
        test_get_publication_not_published,
        # PUT
        test_put_publication,
        test_put_publication_invalid_color,
        # publish errores
        test_publish_without_active_workflow,
        test_publish_with_two_active_workflows,
        test_publish_with_invalid_workflow,
        # publish OK
        test_publish_ok,
        test_publish_idempotent,
        # unpublish
        test_unpublish_ok,
        test_unpublish_idempotent,
        # regresión
        test_regression_app_ok,
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
