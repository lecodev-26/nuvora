"""
Tests — Subfase 14.9.14 (E2E global)
======================================
Flujo completo end-to-end de Nuvora:

    Registrar usuario
      ↓
    Crear bot
      ↓
    Crear workflow (START → MESSAGE → END)
      ↓
    Activar workflow
      ↓
    Publicar bot
      ↓
    Verificar URL pública
      ↓
    Crear sesión anónima
      ↓
    Enviar mensaje → WorkflowEngine → respuesta
      ↓
    Verificar contexto (varios mensajes)
      ↓
    Editar config (apariencia)
      ↓
    Despublicar
      ↓
    URL pública deja de funcionar
"""

import sys
import os
import time
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.core.public_rate_limit import reset_public_all


client = TestClient(app)


# ============================================================
# HELPERS
# ============================================================

def _unique(suffix):
    return f"{suffix}_{int(time.time() * 1000000)}"


def _register_and_login(suffix="e2e"):
    unique = _unique(suffix)
    email = f"e2e_{unique}@nuvora.com"
    r = client.post("/auth/register", json={
        "email": email, "password": "123456", "full_name": "E2E Test",
    })
    assert r.status_code == 200, r.text
    token = client.post(
        "/auth/login",
        data={"username": email, "password": "123456"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, email


# ============================================================
# ESTADO COMPARTIDO
# ============================================================

class _Ctx:
    headers = None
    email = None
    bot_id = None
    wf_id = None
    public_id = None
    public_slug = None
    public_url = None
    session_id = None


# ============================================================
# 1. REGISTRO
# ============================================================

def test_01_register_user():
    print("\n" + "=" * 70)
    print("TEST 01: Registrar usuario")
    print("=" * 70)
    reset_public_all()
    _Ctx.headers, _Ctx.email = _register_and_login("setup")
    print(f"  ✅ Usuario: {_Ctx.email}")


def test_02_list_bots_empty():
    print("\n" + "=" * 70)
    print("TEST 02: Listar bots → 0 inicialmente")
    print("=" * 70)
    r = client.get("/bots/", headers=_Ctx.headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 0
    print("  ✅ 0 bots")


# ============================================================
# 2. CREAR BOT
# ============================================================

def test_03_create_bot():
    print("\n" + "=" * 70)
    print("TEST 03: Crear bot")
    print("=" * 70)
    r = client.post("/bots/", json={
        "name": "Clínica E2E Test",
        "business_name": "Clínica E2E",
        "nicho_id": "clinicas",
    }, headers=_Ctx.headers)
    assert r.status_code == 200, r.text
    _Ctx.bot_id = r.json()["id"]
    assert _Ctx.bot_id is not None
    print(f"  ✅ Bot ID: {_Ctx.bot_id}")


def test_04_get_bot():
    print("\n" + "=" * 70)
    print("TEST 04: Obtener bot")
    print("=" * 70)
    r = client.get(f"/bots/{_Ctx.bot_id}", headers=_Ctx.headers)
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Clínica E2E Test"
    assert data["business_name"] == "Clínica E2E"
    print(f"  ✅ {data['name']}")


# ============================================================
# 3. CREAR WORKFLOW
# ============================================================

def test_05_create_workflow():
    print("\n" + "=" * 70)
    print("TEST 05: Crear workflow START → MESSAGE → END")
    print("=" * 70)
    r = client.post(f"/workflows/{_Ctx.bot_id}", json={
        "name": "WF E2E",
        "status": "draft",
        "nodes": [
            {"node_id": "s1", "type": "start"},
            {"node_id": "m1", "type": "message",
             "config": {"text": "Bienvenido a Clínica E2E"}},
            {"node_id": "e1", "type": "end"},
        ],
        "transitions": [
            {"from_node_id": "s1", "to_node_id": "m1", "order": 0},
            {"from_node_id": "m1", "to_node_id": "e1", "order": 0},
        ],
    }, headers=_Ctx.headers)
    assert r.status_code == 200, r.text
    _Ctx.wf_id = r.json()["id"]
    print(f"  ✅ Workflow ID: {_Ctx.wf_id}")


def test_06_run_workflow_privately():
    print("\n" + "=" * 70)
    print("TEST 06: Ejecutar workflow privadamente (testing)")
    print("=" * 70)
    r = client.post(
        f"/workflows/{_Ctx.bot_id}/{_Ctx.wf_id}/run",
        json={"initial_variables": {}, "max_steps": 10},
        headers=_Ctx.headers,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "completed"
    assert len(data["outputs"]) >= 1
    # Buscar el texto en el campo 'text' de cada output (no usar json.dumps,
    # que escapa caracteres no-ASCII a \uXXXX)
    texts = [o.get("text", "") for o in data["outputs"]]
    assert any("Bienvenido a Clínica E2E" in t for t in texts)
    print("  ✅ Workflow ejecutado OK")


# ============================================================
# 4. PUBLICAR BOT
# ============================================================

def test_07_publish_fails_without_active_workflow():
    print("\n" + "=" * 70)
    print("TEST 07: Publicar SIN workflow activo → 400")
    print("=" * 70)
    r = client.post(f"/bots/{_Ctx.bot_id}/publish", headers=_Ctx.headers)
    assert r.status_code == 400
    print(f"  ✅ 400: {r.json()['detail'][:60]}")


def test_08_activate_workflow():
    print("\n" + "=" * 70)
    print("TEST 08: Activar workflow")
    print("=" * 70)
    r = client.put(f"/workflows/{_Ctx.bot_id}/{_Ctx.wf_id}", json={
        "status": "active",
    }, headers=_Ctx.headers)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "active"
    print("  ✅ Workflow activo")


def test_09_publish_bot():
    print("\n" + "=" * 70)
    print("TEST 09: Publicar bot")
    print("=" * 70)
    r = client.post(f"/bots/{_Ctx.bot_id}/publish", headers=_Ctx.headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["is_published"] is True
    assert data["public_id"] is not None
    assert data["public_slug"] is not None
    assert data["public_url"].startswith("https://")
    _Ctx.public_id = data["public_id"]
    _Ctx.public_slug = data["public_slug"]
    _Ctx.public_url = data["public_url"]
    print(f"  ✅ Publicado: {_Ctx.public_url}")


# ============================================================
# 5. ACCESO PÚBLICO
# ============================================================

def test_10_get_public_bot():
    print("\n" + "=" * 70)
    print("TEST 10: GET público del bot (por slug)")
    print("=" * 70)
    r = client.get(f"/public/bots/{_Ctx.public_slug}")
    assert r.status_code == 200
    data = r.json()
    assert data["public_id"] == _Ctx.public_id
    assert data["name"] == "Clínica E2E Test"
    assert data["business_name"] == "Clínica E2E"
    print(f"  ✅ {data['name']} ({data['business_name']})")


def test_11_create_public_session():
    print("\n" + "=" * 70)
    print("TEST 11: Crear sesión pública")
    print("=" * 70)
    r = client.post(f"/public/bots/{_Ctx.public_id}/session", json={})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "session_id" in data
    assert data["bot_public_id"] == _Ctx.public_id
    _Ctx.session_id = data["session_id"]
    print(f"  ✅ session_id={_Ctx.session_id[:8]}...")


# ============================================================
# 6. CHAT E2E
# ============================================================

def test_12_send_message_e2e():
    print("\n" + "=" * 70)
    print("TEST 12: Enviar mensaje → WorkflowEngine → respuesta")
    print("=" * 70)
    r = client.post(
        f"/public/bots/{_Ctx.public_id}/message",
        json={"session_id": _Ctx.session_id, "message": "Hola"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["session_id"] == _Ctx.session_id
    assert data["status"] == "completed"
    assert "Bienvenido a Clínica E2E" in data["reply"]
    print(f"  ✅ reply: {data['reply'][:60]}")


def test_13_send_multiple_messages():
    print("\n" + "=" * 70)
    print("TEST 13: Enviar varios mensajes → contexto acumulado")
    print("=" * 70)
    for i in range(3):
        r = client.post(
            f"/public/bots/{_Ctx.public_id}/message",
            json={"session_id": _Ctx.session_id, "message": f"msg{i}"},
        )
        assert r.status_code == 200
    print("  ✅ 3 mensajes adicionales OK")


def test_14_verify_session_messages_in_db():
    print("\n" + "=" * 70)
    print("TEST 14: Verificar mensajes guardados en sesión (BD)")
    print("=" * 70)
    from app.database.config import SessionLocal
    from app.models.db_models import PublicSession

    db = SessionLocal()
    try:
        s = db.query(PublicSession).filter(
            PublicSession.public_id == _Ctx.session_id
        ).first()
        assert s is not None
        msgs = json.loads(s.session_data)
        # 1 user + 1 bot + 3 user + 3 bot = 8 mensajes
        assert len(msgs) == 8, f"Esperaba 8, tengo {len(msgs)}"
        user_msgs = [m for m in msgs if m["role"] == "user"]
        assert user_msgs[0]["content"] == "Hola"
        print(f"  ✅ {len(msgs)} mensajes en sesión")
    finally:
        db.close()


# ============================================================
# 7. CONFIG VISUAL
# ============================================================

def test_15_update_publication_config():
    print("\n" + "=" * 70)
    print("TEST 15: Editar config de publicación (apariencia)")
    print("=" * 70)
    r = client.put(
        f"/bots/{_Ctx.bot_id}/publication",
        json={
            "config": {
                "welcome_message": "¡Bienvenido a E2E!",
                "placeholder": "Cuéntame...",
                "primary_color": "#00C6FF",
                "show_branding": False,
            }
        },
        headers=_Ctx.headers,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["config"]["welcome_message"] == "¡Bienvenido a E2E!"
    assert data["config"]["primary_color"] == "#00C6FF"
    assert data["config"]["show_branding"] is False
    print("  ✅ Config actualizada")


def test_16_public_bot_reflects_new_config():
    print("\n" + "=" * 70)
    print("TEST 16: Bot público refleja la nueva config")
    print("=" * 70)
    r = client.get(f"/public/bots/{_Ctx.public_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["config"]["welcome_message"] == "¡Bienvenido a E2E!"
    assert data["config"]["primary_color"] == "#00C6FF"
    assert data["config"]["show_branding"] is False
    print("  ✅ Config pública reflejada")


# ============================================================
# 8. DESPUBLICAR
# ============================================================

def test_17_unpublish_bot():
    print("\n" + "=" * 70)
    print("TEST 17: Despublicar bot")
    print("=" * 70)
    r = client.post(f"/bots/{_Ctx.bot_id}/unpublish", headers=_Ctx.headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["is_published"] is False
    # Mantiene public_id y public_slug
    assert data["public_id"] == _Ctx.public_id
    print(f"  ✅ Despublicado (mantiene public_id)")


def test_18_public_url_blocked_after_unpublish():
    print("\n" + "=" * 70)
    print("TEST 18: URL pública deja de funcionar tras despublicar → 404")
    print("=" * 70)
    r = client.get(f"/public/bots/{_Ctx.public_id}")
    assert r.status_code == 404

    r = client.post(f"/public/bots/{_Ctx.public_id}/session", json={})
    assert r.status_code == 404

    r = client.post(
        f"/public/bots/{_Ctx.public_id}/message",
        json={"session_id": _Ctx.session_id, "message": "Hola"},
    )
    assert r.status_code == 404

    print("  ✅ Todos los endpoints públicos → 404")


# ============================================================
# 9. REPUBLICAR
# ============================================================

def test_19_republish_maintains_public_id():
    print("\n" + "=" * 70)
    print("TEST 19: Republicar mantiene el mismo public_id")
    print("=" * 70)
    r = client.post(f"/bots/{_Ctx.bot_id}/publish", headers=_Ctx.headers)
    assert r.status_code == 200
    data = r.json()
    assert data["public_id"] == _Ctx.public_id, "public_id cambió"
    assert data["is_published"] is True
    print(f"  ✅ Republicado con mismo public_id")


# ============================================================
# 10. LIMPIEZA
# ============================================================

def test_20_cleanup():
    print("\n" + "=" * 70)
    print("TEST 20: Cleanup (borrar bot + workflows + sesiones)")
    print("=" * 70)
    from app.database.config import SessionLocal
    from app.models.db_models import Bot, User

    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == _Ctx.email).first()
        if u:
            bots = db.query(Bot).filter(Bot.user_id == u.id).all()
            for b in bots:
                db.delete(b)
            db.delete(u)
            db.commit()
        print("  ✅ Datos limpiados")
    finally:
        db.close()


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.9.14 (E2E global)")
    print("=" * 70)

    tests = [
        test_01_register_user,
        test_02_list_bots_empty,
        test_03_create_bot,
        test_04_get_bot,
        test_05_create_workflow,
        test_06_run_workflow_privately,
        test_07_publish_fails_without_active_workflow,
        test_08_activate_workflow,
        test_09_publish_bot,
        test_10_get_public_bot,
        test_11_create_public_session,
        test_12_send_message_e2e,
        test_13_send_multiple_messages,
        test_14_verify_session_messages_in_db,
        test_15_update_publication_config,
        test_16_public_bot_reflects_new_config,
        test_17_unpublish_bot,
        test_18_public_url_blocked_after_unpublish,
        test_19_republish_maintains_public_id,
        test_20_cleanup,
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
