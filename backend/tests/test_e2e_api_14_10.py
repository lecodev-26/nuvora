"""
Tests — Subfase 14.10.11 (E2E global de la API)
=================================================
Flujo completo end-to-end de la Nuvora API:

    1.  Registrar usuario
    2.  Crear bot
    3.  Crear workflow
    4.  Activar workflow
    5.  Publicar bot
    6.  Crear API Key
    7.  POST /api/v1/chat → respuesta del WorkflowEngine
    8.  POST /api/v1/chat con session_id → contexto conservado
    9.  Verificar Conversation con channel='api'
    10. Revocar API Key
    11. POST /api/v1/chat → 401 uniforme
    12. Multi-tenant: usuario B no puede usar la key de A
    13. Errores uniformes (formato {"error": {...}})
    14. Cleanup
"""

import sys
import os
import time
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.database.config import SessionLocal
from app.models.db_models import Conversation, PublicSession
from app.core.public_rate_limit import reset_public_all


client = TestClient(app)


# ============================================================
# HELPERS
# ============================================================

def _unique(suffix):
    return f"{suffix}_{int(time.time() * 1000000)}"


def _register_and_login(suffix):
    unique = _unique(suffix)
    email = f"e2eapi_{unique}@nuvora.com"
    r = client.post("/auth/register", json={
        "email": email, "password": "123456", "full_name": "E2E API Test",
    })
    assert r.status_code == 200, r.text
    token = client.post(
        "/auth/login",
        data={"username": email, "password": "123456"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, email


def _create_published_bot_with_key(headers, name="Bot E2E API"):
    """Devuelve (bot_id, api_key_secret)."""
    # 1. Crear bot
    r = client.post("/bots/", json={
        "name": name, "business_name": "E2E", "nicho_id": "otro",
    }, headers=headers)
    assert r.status_code == 200, r.text
    bot_id = r.json()["id"]

    # 2. Crear workflow
    r = client.post(f"/workflows/{bot_id}", json={
        "name": "WF E2E API",
        "status": "draft",
        "nodes": [
            {"node_id": "s1", "type": "start"},
            {"node_id": "m1", "type": "message",
             "config": {"text": "Respuesta desde la API E2E"}},
            {"node_id": "e1", "type": "end"},
        ],
        "transitions": [
            {"from_node_id": "s1", "to_node_id": "m1", "order": 0},
            {"from_node_id": "m1", "to_node_id": "e1", "order": 0},
        ],
    }, headers=headers)
    wf_id = r.json()["id"]

    # 3. Activar
    client.put(f"/workflows/{bot_id}/{wf_id}", json={
        "status": "active",
    }, headers=headers)

    # 4. Publicar
    r = client.post(f"/bots/{bot_id}/publish", headers=headers)
    assert r.status_code == 200, r.text

    # 5. Crear API Key
    r = client.post(
        f"/bots/{bot_id}/api-keys",
        json={"name": "Mi integración"},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    key_secret = r.json()["key"]

    return bot_id, key_secret


# ============================================================
# ESTADO COMPARTIDO
# ============================================================

class _Ctx:
    headers = None
    email = None
    bot_id = None
    api_key_secret = None
    session_id = None
    # Segundo usuario para multi-tenant
    headers_b = None
    bot_id_b = None
    api_key_b = None


# ============================================================
# SETUP
# ============================================================

def test_01_setup_clean():
    print("\n" + "=" * 70)
    print("TEST 01: Setup + limpieza inicial")
    print("=" * 70)
    reset_public_all()

    # Limpieza por si quedan residuos
    from sqlalchemy import text
    from app.database.config import engine
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys=OFF"))
        pattern = "e2eapi_%"
        for sql in [
            "DELETE FROM public_sessions WHERE bot_id IN (SELECT id FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p))",
            "DELETE FROM workflow_tests WHERE bot_id IN (SELECT id FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p))",
            "DELETE FROM workflow_transitions WHERE workflow_id IN (SELECT id FROM workflows WHERE bot_id IN (SELECT id FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p)))",
            "DELETE FROM workflow_nodes WHERE workflow_id IN (SELECT id FROM workflows WHERE bot_id IN (SELECT id FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p)))",
            "DELETE FROM workflows WHERE bot_id IN (SELECT id FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p))",
            "DELETE FROM conversations WHERE bot_id IN (SELECT id FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p))",
            "DELETE FROM api_keys WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p)",
            "DELETE FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p)",
            "DELETE FROM users WHERE email LIKE :p",
        ]:
            conn.execute(text(sql), {"p": pattern})
        conn.execute(text("PRAGMA foreign_keys=ON"))

    print("  ✅ BD limpia")


def test_02_register():
    print("\n" + "=" * 70)
    print("TEST 02: Registrar usuario")
    print("=" * 70)
    _Ctx.headers, _Ctx.email = _register_and_login("main")
    print(f"  ✅ {_Ctx.email}")


def test_03_create_bot_workflow_publish_key():
    print("\n" + "=" * 70)
    print("TEST 03: Crear bot + workflow + publicar + API Key")
    print("=" * 70)
    _Ctx.bot_id, _Ctx.api_key_secret = _create_published_bot_with_key(
        _Ctx.headers, name="Bot E2E API"
    )
    print(f"  ✅ bot_id={_Ctx.bot_id}")
    print(f"  ✅ api_key={_Ctx.api_key_secret[:20]}...")


# ============================================================
# E2E — CHAT
# ============================================================

def test_04_chat_first_message():
    print("\n" + "=" * 70)
    print("TEST 04: POST /api/v1/chat → respuesta del engine")
    print("=" * 70)
    r = client.post(
        "/api/v1/chat",
        json={"message": "Hola"},
        headers={"Authorization": f"Bearer {_Ctx.api_key_secret}"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["answer"] == "Respuesta desde la API E2E"
    assert data["status"] == "completed"
    assert data["session_id"]

    _Ctx.session_id = data["session_id"]
    print(f"  ✅ answer: {data['answer']}")
    print(f"  ✅ session_id: {data['session_id'][:16]}...")


def test_05_chat_second_message_same_session():
    print("\n" + "=" * 70)
    print("TEST 05: POST /api/v1/chat con session_id → contexto")
    print("=" * 70)
    r = client.post(
        "/api/v1/chat",
        json={"message": "Segundo mensaje", "session_id": _Ctx.session_id},
        headers={"Authorization": f"Bearer {_Ctx.api_key_secret}"},
    )
    assert r.status_code == 200
    assert r.json()["session_id"] == _Ctx.session_id
    print("  ✅ Mismo session_id")


def test_06_verify_session_in_db():
    print("\n" + "=" * 70)
    print("TEST 06: Sesión guardada en BD (public_sessions)")
    print("=" * 70)
    db = SessionLocal()
    try:
        s = db.query(PublicSession).filter(
            PublicSession.public_id == _Ctx.session_id
        ).first()
        assert s is not None
        msgs = json.loads(s.session_data)
        # 2 user + 2 bot = 4
        assert len(msgs) == 4, f"Esperaba 4, tengo {len(msgs)}"
        print(f"  ✅ {len(msgs)} mensajes en sesión")
    finally:
        db.close()


def test_07_verify_conversation_analytics():
    print("\n" + "=" * 70)
    print("TEST 07: Conversaciones guardadas en analytics (channel='api')")
    print("=" * 70)
    db = SessionLocal()
    try:
        convs = db.query(Conversation).filter(
            Conversation.bot_id == _Ctx.bot_id,
            Conversation.channel == "api",
        ).all()
        assert len(convs) >= 2, f"Esperaba >=2, tengo {len(convs)}"
        for c in convs:
            assert c.answer is not None
        print(f"  ✅ {len(convs)} conversaciones en analytics")
    finally:
        db.close()


def test_08_response_no_internal_fields():
    print("\n" + "=" * 70)
    print("TEST 08: Respuesta no expone datos internos")
    print("=" * 70)
    r = client.post(
        "/api/v1/chat",
        json={"message": "Hola"},
        headers={"Authorization": f"Bearer {_Ctx.api_key_secret}"},
    )
    data = r.json()

    allowed = {"answer", "session_id", "status"}
    extra = set(data.keys()) - allowed
    assert not extra, f"❌ Campos extra: {extra}"

    # Verificar que el 'answer' NO contiene datos internos.
    # OJO: no buscar en el session_id (es un UUID aleatorio y puede
    # contener substrings como 'e1' por azar).
    answer_lower = data["answer"].lower()
    for bad in ["workflow_id", "node_id", "prompt", "user_id", "key_hash"]:
        assert bad not in answer_lower, f"❌ '{bad}' filtrado en answer"

    # Los node_id del test (s1, m1, e1) no deben aparecer como palabras
    # separadas en el answer (que es "Respuesta desde la API E2E").
    for node_id in ["s1", "m1", "e1"]:
        assert node_id not in answer_lower, f"❌ '{node_id}' filtrado en answer"
    print("  ✅ Sin campos internos")


# ============================================================
# REVOCAR API KEY
# ============================================================

def test_09_list_api_keys():
    print("\n" + "=" * 70)
    print("TEST 09: Listar API Keys (GET)")
    print("=" * 70)
    r = client.get(
        f"/bots/{_Ctx.bot_id}/api-keys",
        headers=_Ctx.headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    # Nunca expone el secret
    for k in data["keys"]:
        assert "key" not in k
        assert "key_hash" not in k
    print(f"  ✅ {data['total']} keys (sin secret)")


def test_10_revoke_api_key():
    print("\n" + "=" * 70)
    print("TEST 10: Revocar API Key")
    print("=" * 70)
    r = client.get(
        f"/bots/{_Ctx.bot_id}/api-keys",
        headers=_Ctx.headers,
    )
    key_id = r.json()["keys"][0]["id"]

    r = client.delete(
        f"/bots/{_Ctx.bot_id}/api-keys/{key_id}",
        headers=_Ctx.headers,
    )
    assert r.status_code == 200
    print(f"  ✅ Key #{key_id} revocada")


def test_11_chat_with_revoked_key_401():
    print("\n" + "=" * 70)
    print("TEST 11: POST /api/v1/chat con key revocada → 401 uniforme")
    print("=" * 70)
    r = client.post(
        "/api/v1/chat",
        json={"message": "Hola"},
        headers={"Authorization": f"Bearer {_Ctx.api_key_secret}"},
    )
    assert r.status_code == 401
    body = r.json()
    assert "error" in body
    assert body["error"]["code"] == "REVOKED_API_KEY"
    print(f"  ✅ 401: {body['error']['code']}")


# ============================================================
# MULTI-TENANT
# ============================================================

def test_12_second_user():
    print("\n" + "=" * 70)
    print("TEST 12: Segundo usuario con su propio bot + key")
    print("=" * 70)
    _Ctx.headers_b, _ = _register_and_login("second")
    _Ctx.bot_id_b, _Ctx.api_key_b = _create_published_bot_with_key(
        _Ctx.headers_b, name="Bot E2E API B"
    )
    print(f"  ✅ bot_b={_Ctx.bot_id_b}")


def test_13_cannot_use_other_users_key():
    print("\n" + "=" * 70)
    print("TEST 13: Key del usuario A no sirve para bot del usuario B")
    print("=" * 70)
    # La key A estaba revocada → usamos una nueva para este test
    r = client.post(
        f"/bots/{_Ctx.bot_id}/api-keys",
        json={"name": "Key A fresh"},
        headers=_Ctx.headers,
    )
    key_a = r.json()["key"]

    # Key A funciona en bot A
    r1 = client.post(
        "/api/v1/chat",
        json={"message": "Hola"},
        headers={"Authorization": f"Bearer {key_a}"},
    )
    assert r1.status_code == 200
    session_a = r1.json()["session_id"]

    # Pero la sesión de A no funciona con la key B
    r2 = client.post(
        "/api/v1/chat",
        json={"message": "Hola", "session_id": session_a},
        headers={"Authorization": f"Bearer {_Ctx.api_key_b}"},
    )
    assert r2.status_code == 404, f"Esperaba 404, dio {r2.status_code}"
    print("  ✅ 404 (aislamiento entre usuarios)")


def test_14_invalid_key_401_uniform():
    print("\n" + "=" * 70)
    print("TEST 14: Key inexistente → 401 uniforme")
    print("=" * 70)
    r = client.post(
        "/api/v1/chat",
        json={"message": "Hola"},
        headers={"Authorization": "Bearer nvr_live_inexistente_xyz"},
    )
    assert r.status_code == 401
    body = r.json()
    assert body["error"]["code"] == "INVALID_API_KEY"
    print("  ✅ 401 uniforme")


# ============================================================
# CLEANUP
# ============================================================

def test_15_cleanup():
    print("\n" + "=" * 70)
    print("TEST 15: Cleanup completo")
    print("=" * 70)
    from sqlalchemy import text
    from app.database.config import engine

    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys=OFF"))
        pattern = "e2eapi_%"
        for sql in [
            "DELETE FROM public_sessions WHERE bot_id IN (SELECT id FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p))",
            "DELETE FROM workflow_tests WHERE bot_id IN (SELECT id FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p))",
            "DELETE FROM workflow_transitions WHERE workflow_id IN (SELECT id FROM workflows WHERE bot_id IN (SELECT id FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p)))",
            "DELETE FROM workflow_nodes WHERE workflow_id IN (SELECT id FROM workflows WHERE bot_id IN (SELECT id FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p)))",
            "DELETE FROM workflows WHERE bot_id IN (SELECT id FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p))",
            "DELETE FROM conversations WHERE bot_id IN (SELECT id FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p))",
            "DELETE FROM api_keys WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p)",
            "DELETE FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p)",
            "DELETE FROM users WHERE email LIKE :p",
        ]:
            conn.execute(text(sql), {"p": pattern})
        conn.execute(text("PRAGMA foreign_keys=ON"))
    reset_public_all()
    print("  ✅ Datos limpiados")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.10.11 (E2E API)")
    print("=" * 70)

    tests = [
        test_01_setup_clean,
        test_02_register,
        test_03_create_bot_workflow_publish_key,
        test_04_chat_first_message,
        test_05_chat_second_message_same_session,
        test_06_verify_session_in_db,
        test_07_verify_conversation_analytics,
        test_08_response_no_internal_fields,
        test_09_list_api_keys,
        test_10_revoke_api_key,
        test_11_chat_with_revoked_key_401,
        test_12_second_user,
        test_13_cannot_use_other_users_key,
        test_14_invalid_key_401_uniform,
        test_15_cleanup,
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
