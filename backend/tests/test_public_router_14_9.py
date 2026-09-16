"""
Tests — Subfase 14.9.8 (Endpoints públicos)
=============================================
Cubre el flujo E2E real:
    Publicar bot → Crear sesión → Enviar mensaje → WorkflowEngine → Respuesta

Secciones:
    1. Setup: usuario + bot + workflow (START → MESSAGE → END) + publicar
    2. GET /public/bots/{identifier}
    3. POST /public/bots/{identifier}/session
    4. POST /public/bots/{identifier}/message  ← EL CRÍTICO (E2E real)
    5. DELETE /public/bots/{identifier}/session
    6. Seguridad: sin datos internos filtrados
"""

import sys
import os
import time
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.database.config import SessionLocal
from app.models.db_models import Bot, PublicSession


client = TestClient(app)


# ============================================================
# HELPERS
# ============================================================

def _unique(suffix):
    return f"{suffix}_{int(time.time() * 1000000)}"


def _register_and_login(suffix):
    unique = _unique(suffix)
    email = f"pubrouter_{unique}@nuvora.com"
    r = client.post("/auth/register", json={
        "email": email, "password": "123456", "full_name": "Public Router",
    })
    assert r.status_code == 200, r.text
    token = client.post(
        "/auth/login",
        data={"username": email, "password": "123456"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_bot(headers, name="Bot Público Test"):
    r = client.post("/bots/", json={
        "name": name, "business_name": "Pub Test", "nicho_id": "otro",
    }, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _create_workflow_active(headers, bot_id):
    r = client.post(f"/workflows/{bot_id}", json={
        "name": "WF Público",
        "status": "draft",
        "nodes": [
            {"node_id": "s1", "type": "start"},
            {"node_id": "m1", "type": "message",
             "config": {"text": "Hola desde el engine público"}},
            {"node_id": "e1", "type": "end"},
        ],
        "transitions": [
            {"from_node_id": "s1", "to_node_id": "m1", "order": 0},
            {"from_node_id": "m1", "to_node_id": "e1", "order": 0},
        ],
    }, headers=headers)
    assert r.status_code == 200, r.text
    wf_id = r.json()["id"]

    r = client.put(f"/workflows/{bot_id}/{wf_id}", json={
        "status": "active",
    }, headers=headers)
    assert r.status_code == 200, r.text
    return wf_id


def _publish_bot(headers, bot_id):
    r = client.post(f"/bots/{bot_id}/publish", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


# ============================================================
# ESTADO COMPARTIDO
# ============================================================

class _Ctx:
    headers = None
    bot_id = None
    wf_id = None
    public_id = None
    public_slug = None
    session_id = None


# ============================================================
# SETUP
# ============================================================

def test_setup():
    print("\n" + "=" * 70)
    print("SETUP: usuario + bot + workflow activo + publicar")
    print("=" * 70)
    _Ctx.headers = _register_and_login("u1")
    _Ctx.bot_id = _create_bot(_Ctx.headers)
    _Ctx.wf_id = _create_workflow_active(_Ctx.headers, _Ctx.bot_id)
    pub = _publish_bot(_Ctx.headers, _Ctx.bot_id)
    _Ctx.public_id = pub["public_id"]
    _Ctx.public_slug = pub["public_slug"]
    print(f"  ✅ bot={_Ctx.bot_id}, wf={_Ctx.wf_id}")
    print(f"  ✅ public_id={_Ctx.public_id[:8]}..., public_slug={_Ctx.public_slug}")


# ============================================================
# TESTS — GET /public/bots/{identifier}
# ============================================================

def test_get_public_bot_by_id():
    print("\n" + "=" * 70)
    print("TEST 1: GET /public/bots/{public_id} → info pública")
    print("=" * 70)
    r = client.get(f"/public/bots/{_Ctx.public_id}")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["public_id"] == _Ctx.public_id
    assert data["name"] == "Bot Público Test"
    assert "config" in data
    assert data["config"]["show_branding"] is True
    print(f"  ✅ {data['name']}")


def test_get_public_bot_by_slug():
    print("\n" + "=" * 70)
    print("TEST 2: GET /public/bots/{public_slug} → info pública")
    print("=" * 70)
    r = client.get(f"/public/bots/{_Ctx.public_slug}")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["public_id"] == _Ctx.public_id
    print(f"  ✅ Por slug OK")


def test_get_public_bot_not_found():
    print("\n" + "=" * 70)
    print("TEST 3: GET /public/bots/nonexistent → 404")
    print("=" * 70)
    r = client.get("/public/bots/nonexistent-xxxx-9999")
    assert r.status_code == 404
    print("  ✅ 404")


def test_get_public_bot_no_internal_data():
    print("\n" + "=" * 70)
    print("TEST 4: GET /public/bots/{id} → NO expone datos internos")
    print("=" * 70)
    r = client.get(f"/public/bots/{_Ctx.public_id}")
    data = r.json()
    # Campos prohibidos:
    forbidden = ["bot_id", "user_id", "owner_email", "public_config",
                 "workflow_id", "nodes", "transitions", "is_published",
                 "published_at", "restaurant_name"]
    for f in forbidden:
        assert f not in data, f"❌ NO debe exponer '{f}'"
    print(f"  ✅ No expone {len(forbidden)} campos internos")


# ============================================================
# TESTS — POST /public/bots/{identifier}/session
# ============================================================

def test_create_session():
    print("\n" + "=" * 70)
    print("TEST 5: POST /session → crea sesión")
    print("=" * 70)
    r = client.post(
        f"/public/bots/{_Ctx.public_id}/session",
        json={},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "session_id" in data
    assert data["bot_public_id"] == _Ctx.public_id
    assert "expires_at" in data
    _Ctx.session_id = data["session_id"]
    print(f"  ✅ session_id={data['session_id'][:8]}...")


def test_create_session_bot_not_found():
    print("\n" + "=" * 70)
    print("TEST 6: POST /session bot inexistente → 404")
    print("=" * 70)
    r = client.post("/public/bots/nonexistent-xxxx/session", json={})
    assert r.status_code == 404
    print("  ✅ 404")


# ============================================================
# TESTS — POST /public/bots/{identifier}/message
# ============================================================

def test_send_message_e2e():
    print("\n" + "=" * 70)
    print("TEST 7: POST /message → E2E real (WorkflowEngine)")
    print("=" * 70)
    r = client.post(
        f"/public/bots/{_Ctx.public_id}/message",
        json={"session_id": _Ctx.session_id, "message": "Hola"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["session_id"] == _Ctx.session_id
    assert data["status"] == "completed"
    assert "Hola desde el engine público" in data["reply"]
    print(f"  ✅ reply: {data['reply']}")
    print(f"  ✅ status: {data['status']}")


def test_message_saved_in_session():
    print("\n" + "=" * 70)
    print("TEST 8: POST /message → mensajes guardados en sesión")
    print("=" * 70)
    db = SessionLocal()
    try:
        s = db.query(PublicSession).filter(
            PublicSession.public_id == _Ctx.session_id,
        ).first()
        assert s is not None
        msgs = json.loads(s.session_data)
        # Debe haber 2 mensajes: user + bot
        assert len(msgs) >= 2, f"Mensajes: {len(msgs)}"
        roles = [m["role"] for m in msgs]
        assert "user" in roles
        assert "bot" in roles
        # Último mensaje user = "Hola"
        user_msgs = [m for m in msgs if m["role"] == "user"]
        assert user_msgs[0]["content"] == "Hola"
        print(f"  ✅ {len(msgs)} mensajes en sesión")
    finally:
        db.close()


def test_send_multiple_messages():
    print("\n" + "=" * 70)
    print("TEST 9: POST /message x3 → contexto acumulado")
    print("=" * 70)
    for i in range(3):
        r = client.post(
            f"/public/bots/{_Ctx.public_id}/message",
            json={"session_id": _Ctx.session_id, "message": f"msg{i}"},
        )
        assert r.status_code == 200, r.text
        assert r.json()["reply"] == "Hola desde el engine público"

    db = SessionLocal()
    try:
        s = db.query(PublicSession).filter(
            PublicSession.public_id == _Ctx.session_id,
        ).first()
        msgs = json.loads(s.session_data)
        # 1 user + 1 bot + 3 user + 3 bot = 8
        assert len(msgs) == 8, f"Esperaba 8, tengo {len(msgs)}"
        print(f"  ✅ {len(msgs)} mensajes acumulados")
    finally:
        db.close()


def test_send_message_invalid_session():
    print("\n" + "=" * 70)
    print("TEST 10: POST /message con session_id inválido → 404")
    print("=" * 70)
    r = client.post(
        f"/public/bots/{_Ctx.public_id}/message",
        json={"session_id": "invalid-xxx", "message": "Hola"},
    )
    assert r.status_code == 404
    print("  ✅ 404")


def test_send_message_bot_not_found():
    print("\n" + "=" * 70)
    print("TEST 11: POST /message bot inexistente → 404")
    print("=" * 70)
    r = client.post(
        "/public/bots/nonexistent-xxx/message",
        json={"session_id": _Ctx.session_id, "message": "Hola"},
    )
    assert r.status_code == 404
    print("  ✅ 404")


def test_send_message_empty():
    print("\n" + "=" * 70)
    print("TEST 12: POST /message texto vacío → 422")
    print("=" * 70)
    r = client.post(
        f"/public/bots/{_Ctx.public_id}/message",
        json={"session_id": _Ctx.session_id, "message": ""},
    )
    assert r.status_code == 422
    print("  ✅ 422")


def test_send_message_too_long():
    print("\n" + "=" * 70)
    print("TEST 13: POST /message > 2000 chars → 422")
    print("=" * 70)
    r = client.post(
        f"/public/bots/{_Ctx.public_id}/message",
        json={"session_id": _Ctx.session_id, "message": "a" * 2001},
    )
    assert r.status_code == 422
    print("  ✅ 422")


# ============================================================
# TESTS — Aislamiento multi-bot
# ============================================================

def test_session_from_other_bot_rejected():
    print("\n" + "=" * 70)
    print("TEST 14: session de OTRO bot → 404 (multi-tenant)")
    print("=" * 70)
    # Creamos otro bot publicado
    headers2 = _register_and_login("u2")
    bot2 = _create_bot(headers2, name="Otro Bot")
    _create_workflow_active(headers2, bot2)
    pub2 = _publish_bot(headers2, bot2)

    # Intentamos usar la session del bot1 con el bot2
    r = client.post(
        f"/public/bots/{pub2['public_id']}/message",
        json={"session_id": _Ctx.session_id, "message": "Hola"},
    )
    assert r.status_code == 404, f"Esperaba 404, hubo {r.status_code}: {r.text}"
    print("  ✅ 404 (aislamiento entre bots)")


# ============================================================
# TESTS — DELETE /public/bots/{identifier}/session
# ============================================================

def test_close_session():
    print("\n" + "=" * 70)
    print("TEST 15: DELETE /session → cierra sesión")
    print("=" * 70)
    r = client.delete(
        f"/public/bots/{_Ctx.public_id}/session",
        params={"session_id": _Ctx.session_id},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["session_id"] == _Ctx.session_id
    print(f"  ✅ Sesión cerrada")


def test_message_after_close_404():
    print("\n" + "=" * 70)
    print("TEST 16: POST /message tras cerrar sesión → 404")
    print("=" * 70)
    r = client.post(
        f"/public/bots/{_Ctx.public_id}/message",
        json={"session_id": _Ctx.session_id, "message": "Hola"},
    )
    assert r.status_code == 404
    print("  ✅ 404")


def test_close_session_not_found():
    print("\n" + "=" * 70)
    print("TEST 17: DELETE /session session_id inexistente → 404")
    print("=" * 70)
    r = client.delete(
        f"/public/bots/{_Ctx.public_id}/session",
        params={"session_id": "invalid-xxx"},
    )
    assert r.status_code == 404
    print("  ✅ 404")


# ============================================================
# TESTS — Regresión
# ============================================================

def test_regression_app_ok():
    print("\n" + "=" * 70)
    print("TEST 18: Regresión — app sigue OK")
    print("=" * 70)
    from app.main import app as _app
    assert _app is not None
    print(f"  ✅ app OK")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.9.8 (Endpoints públicos E2E)")
    print("=" * 70)

    tests = [
        test_setup,
        # GET
        test_get_public_bot_by_id,
        test_get_public_bot_by_slug,
        test_get_public_bot_not_found,
        test_get_public_bot_no_internal_data,
        # SESSION
        test_create_session,
        test_create_session_bot_not_found,
        # MESSAGE (E2E)
        test_send_message_e2e,
        test_message_saved_in_session,
        test_send_multiple_messages,
        test_send_message_invalid_session,
        test_send_message_bot_not_found,
        test_send_message_empty,
        test_send_message_too_long,
        # Aislamiento
        test_session_from_other_bot_rejected,
        # DELETE
        test_close_session,
        test_message_after_close_404,
        test_close_session_not_found,
        # Regresión
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
