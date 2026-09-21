"""
Tests — Subfase 14.10.7 (POST /api/v1/chat)
=============================================
Cubre:
    - Autenticación: sin header, sin Bearer, sin nvr_live_, key inexistente/
      revocada/expirada
    - Creación/recuperación de sesión
    - Chat E2E con WorkflowEngine
    - Multi-turno con contexto
    - Aislamiento entre bots
    - Analytics (channel="api")
    - Estados del bot (no publicado / sin workflow activo)
    - Rate limiting
    - Validación de payload
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
    email = f"apichat_{unique}@nuvora.com"
    r = client.post("/auth/register", json={
        "email": email, "password": "123456", "full_name": "ApiChat Test",
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


def _setup_published_bot(headers, name=None, publish=True):
    """Crea bot + workflow + publica (si publish). Devuelve bot_id."""
    bot_id = _create_bot(headers, name)

    r = client.post(f"/workflows/{bot_id}", json={
        "name": "WF ApiChat",
        "status": "draft",
        "nodes": [
            {"node_id": "s1", "type": "start"},
            {"node_id": "m1", "type": "message",
             "config": {"text": "Hola desde API"}},
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

    if publish:
        r = client.post(f"/bots/{bot_id}/publish", headers=headers)
        assert r.status_code == 200, r.text

    return bot_id


def _create_api_key(headers, bot_id, name="Mi integración"):
    r = client.post(
        f"/bots/{bot_id}/api-keys",
        json={"name": name},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


# ============================================================
# ESTADO COMPARTIDO
# ============================================================

class _Ctx:
    headers = None
    headers2 = None
    bot_id = None
    api_key = None
    api_key_secret = None
    bot2_id = None
    api_key2_secret = None
    email1 = None

    @classmethod
    def get_email(cls):
        return cls.email1


# ============================================================
# SETUP
# ============================================================

def test_setup():
    print("\n" + "=" * 70)
    print("SETUP: 2 users + bot publicado cada uno + API keys")
    print("=" * 70)
    reset_public_all()

    # Limpiar cualquier residuo de ejecuciones anteriores
    from sqlalchemy import text
    from app.database.config import engine
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys=OFF"))
        pattern = "apichat_%"
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

    # User 1 (para bot1 y todas las pruebas)
    _Ctx.headers, _Ctx.email1 = _register_and_login("setup1")
    _Ctx.bot_id = _setup_published_bot(_Ctx.headers, name="Bot API Chat")
    key_data = _create_api_key(_Ctx.headers, _Ctx.bot_id)
    _Ctx.api_key = key_data
    _Ctx.api_key_secret = key_data["key"]

    # User 2 (solo para bot2 de aislamiento)
    _Ctx.headers2, _ = _register_and_login("setup2")
    _Ctx.bot2_id = _setup_published_bot(_Ctx.headers2, name="Bot API Chat 2")
    key_data2 = _create_api_key(_Ctx.headers2, _Ctx.bot2_id, name="Key 2")
    _Ctx.api_key2_secret = key_data2["key"]

    print(f"  ✅ bot1={_Ctx.bot_id} (user1), bot2={_Ctx.bot2_id} (user2)")
    print(f"  ✅ key1={_Ctx.api_key_secret[:20]}...")
    print(f"  ✅ key2={_Ctx.api_key2_secret[:20]}...")


# ============================================================
# AUTENTICACIÓN
# ============================================================

def test_auth_no_header():
    print("\n" + "=" * 70)
    print("TEST 1: sin header → 401")
    print("=" * 70)
    r = client.post("/api/v1/chat", json={"message": "Hola"})
    assert r.status_code == 401, r.text
    print("  ✅ 401")


def test_auth_wrong_scheme():
    print("\n" + "=" * 70)
    print("TEST 2: Bearer sin nvr_live_ → 401")
    print("=" * 70)
    r = client.post(
        "/api/v1/chat",
        json={"message": "Hola"},
        headers={"Authorization": "Bearer xyz_no_es_nvr"},
    )
    assert r.status_code == 401
    print("  ✅ 401")


def test_auth_basic_scheme():
    print("\n" + "=" * 70)
    print("TEST 3: esquema Basic → 401")
    print("=" * 70)
    r = client.post(
        "/api/v1/chat",
        json={"message": "Hola"},
        headers={"Authorization": "Basic nvr_live_xxx"},
    )
    assert r.status_code == 401
    print("  ✅ 401")


def test_auth_nonexistent_key():
    print("\n" + "=" * 70)
    print("TEST 4: key inexistente → 401")
    print("=" * 70)
    r = client.post(
        "/api/v1/chat",
        json={"message": "Hola"},
        headers={"Authorization": "Bearer nvr_live_inexistente_xyz"},
    )
    assert r.status_code == 401
    print("  ✅ 401")


def test_auth_revoked_key():
    print("\n" + "=" * 70)
    print("TEST 5: key revocada → 401")
    print("=" * 70)
    # Crear key y revocarla
    key_data = _create_api_key(_Ctx.headers, _Ctx.bot_id, name="revoked")
    client.delete(
        f"/bots/{_Ctx.bot_id}/api-keys/{key_data['id']}",
        headers=_Ctx.headers,
    )

    r = client.post(
        "/api/v1/chat",
        json={"message": "Hola"},
        headers={"Authorization": f"Bearer {key_data['key']}"},
    )
    assert r.status_code == 401
    print("  ✅ 401")


def test_auth_expired_key():
    print("\n" + "=" * 70)
    print("TEST 6: key expirada → 401")
    print("=" * 70)
    # Crear key y forzar expiración en BD
    key_data = _create_api_key(_Ctx.headers, _Ctx.bot_id, name="expired")

    db = SessionLocal()
    try:
        from app.models.db_models import ApiKey
        from datetime import datetime, timezone, timedelta
        k = db.query(ApiKey).filter(ApiKey.id == key_data["id"]).first()
        k.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        db.commit()
    finally:
        db.close()

    r = client.post(
        "/api/v1/chat",
        json={"message": "Hola"},
        headers={"Authorization": f"Bearer {key_data['key']}"},
    )
    assert r.status_code == 401
    print("  ✅ 401")


# ============================================================
# SESIONES
# ============================================================

def test_chat_creates_session():
    print("\n" + "=" * 70)
    print("TEST 7: sin session_id → crea sesión")
    print("=" * 70)
    r = client.post(
        "/api/v1/chat",
        json={"message": "Hola"},
        headers={"Authorization": f"Bearer {_Ctx.api_key_secret}"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "session_id" in data
    assert data["session_id"]
    assert data["answer"] == "Hola desde API"
    print(f"  ✅ session_id={data['session_id'][:16]}...")


def test_chat_recovers_session():
    print("\n" + "=" * 70)
    print("TEST 8: con session_id → recupera sesión")
    print("=" * 70)
    # Primer mensaje
    r1 = client.post(
        "/api/v1/chat",
        json={"message": "Hola"},
        headers={"Authorization": f"Bearer {_Ctx.api_key_secret}"},
    )
    sid = r1.json()["session_id"]

    # Segundo mensaje con el mismo session_id
    r2 = client.post(
        "/api/v1/chat",
        json={"message": "¿Qué más?", "session_id": sid},
        headers={"Authorization": f"Bearer {_Ctx.api_key_secret}"},
    )
    assert r2.status_code == 200
    assert r2.json()["session_id"] == sid
    print(f"  ✅ Mismo session_id reutilizado")


# ============================================================
# CHAT E2E
# ============================================================

def test_chat_e2e_response():
    print("\n" + "=" * 70)
    print("TEST 9: respuesta viene del WorkflowEngine")
    print("=" * 70)
    r = client.post(
        "/api/v1/chat",
        json={"message": "Cualquier cosa"},
        headers={"Authorization": f"Bearer {_Ctx.api_key_secret}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["answer"] == "Hola desde API"
    assert data["status"] == "completed"
    print(f"  ✅ answer: {data['answer']}")


def test_chat_multi_turno():
    print("\n" + "=" * 70)
    print("TEST 10: multi-turno → contexto acumulado en BD")
    print("=" * 70)
    r1 = client.post(
        "/api/v1/chat",
        json={"message": "msg1"},
        headers={"Authorization": f"Bearer {_Ctx.api_key_secret}"},
    )
    sid = r1.json()["session_id"]

    for i in range(2, 4):
        client.post(
            "/api/v1/chat",
            json={"message": f"msg{i}", "session_id": sid},
            headers={"Authorization": f"Bearer {_Ctx.api_key_secret}"},
        )

    db = SessionLocal()
    try:
        s = db.query(PublicSession).filter(
            PublicSession.public_id == sid
        ).first()
        assert s is not None
        msgs = json.loads(s.session_data)
        # 3 user + 3 bot = 6
        assert len(msgs) == 6, f"Esperaba 6, tengo {len(msgs)}"
        print(f"  ✅ {len(msgs)} mensajes en sesión")
    finally:
        db.close()


def test_chat_session_not_other_bot():
    print("\n" + "=" * 70)
    print("TEST 11: session_id de OTRO bot → 404")
    print("=" * 70)
    # Sesión del bot 1
    r1 = client.post(
        "/api/v1/chat",
        json={"message": "Hola"},
        headers={"Authorization": f"Bearer {_Ctx.api_key_secret}"},
    )
    sid = r1.json()["session_id"]

    # Intentar usarla con key del bot 2
    r2 = client.post(
        "/api/v1/chat",
        json={"message": "Hola", "session_id": sid},
        headers={"Authorization": f"Bearer {_Ctx.api_key2_secret}"},
    )
    assert r2.status_code == 404, f"Esperaba 404, dio {r2.status_code}"
    print("  ✅ 404 (aislamiento entre bots)")


def test_chat_does_not_leak_internals():
    print("\n" + "=" * 70)
    print("TEST 12: respuesta NO expone datos internos")
    print("=" * 70)
    r = client.post(
        "/api/v1/chat",
        json={"message": "Hola"},
        headers={"Authorization": f"Bearer {_Ctx.api_key_secret}"},
    )
    data = r.json()

    # Solo 3 campos permitidos
    allowed = {"answer", "session_id", "status"}
    extra = set(data.keys()) - allowed
    assert not extra, f"❌ Campos extra: {extra}"

    # Verificar que los valores no contienen datos internos
    raw = json.dumps(data)
    for bad in ["workflow_id", "node_id", "s1", "e1", "prompt"]:
        assert bad not in raw, f"❌ '{bad}' filtrado en respuesta"
    print("  ✅ Sin campos internos")


def test_chat_analytics_saved():
    print("\n" + "=" * 70)
    print("TEST 13: se guarda en Conversation (channel='api')")
    print("=" * 70)
    # Contar antes
    db = SessionLocal()
    try:
        before = db.query(Conversation).filter(
            Conversation.bot_id == _Ctx.bot_id,
            Conversation.channel == "api",
        ).count()

        r = client.post(
            "/api/v1/chat",
            json={"message": "analytics-test"},
            headers={"Authorization": f"Bearer {_Ctx.api_key_secret}"},
        )
        assert r.status_code == 200

        after = db.query(Conversation).filter(
            Conversation.bot_id == _Ctx.bot_id,
            Conversation.channel == "api",
        ).count()

        assert after == before + 1
        print(f"  ✅ Conversation count: {before} → {after}")
    finally:
        db.close()


# ============================================================
# ESTADOS DEL BOT
# ============================================================

def test_chat_bot_not_published():
    print("\n" + "=" * 70)
    print("TEST 14: bot NO publicado → 409")
    print("=" * 70)
    # User nuevo para poder crear otro bot (regla: 1 bot por user)
    headers_new, _ = _register_and_login("nopub")
    bot_id = _setup_published_bot(headers_new, name="Bot no publicado", publish=False)
    key_data = _create_api_key(headers_new, bot_id, name="key-nopub")

    r = client.post(
        "/api/v1/chat",
        json={"message": "Hola"},
        headers={"Authorization": f"Bearer {key_data['key']}"},
    )
    assert r.status_code == 409
    # Formato uniforme /api/v1/* (14.10.8)
    body = r.json()
    assert "error" in body
    assert body["error"]["code"] == "BOT_NOT_PUBLISHED"
    print(f"  ✅ 409: {body['error']['message'][:60]}")


# ============================================================
# RATE LIMITING
# ============================================================

def test_rate_limit_429():
    print("\n" + "=" * 70)
    print("TEST 15: rate limit → 429 + Retry-After")
    print("=" * 70)
    reset_public_all()

    # El endpoint pasa max_per_window explícitamente → parchear la constante
    # del router, no _get_limit_for.
    import app.routers.api_v1 as av1
    orig = av1.API_RATE_LIMIT_MESSAGE
    av1.API_RATE_LIMIT_MESSAGE = 2  # límite bajo para el test

    try:
        for i in range(2):
            r = client.post(
                "/api/v1/chat",
                json={"message": f"m{i}"},
                headers={"Authorization": f"Bearer {_Ctx.api_key_secret}"},
            )
            assert r.status_code == 200, f"#{i+1}: {r.status_code}: {r.text}"

        r = client.post(
            "/api/v1/chat",
            json={"message": "overflow"},
            headers={"Authorization": f"Bearer {_Ctx.api_key_secret}"},
        )
        assert r.status_code == 429, f"Esperaba 429, dio {r.status_code}: {r.text}"
        assert "Retry-After" in r.headers
        print(f"  ✅ 429 (Retry-After={r.headers['Retry-After']}s)")
    finally:
        av1.API_RATE_LIMIT_MESSAGE = orig
        reset_public_all()


# ============================================================
# VALIDACIÓN PAYLOAD
# ============================================================

def test_payload_empty_message():
    print("\n" + "=" * 70)
    print("TEST 16: mensaje vacío → 422")
    print("=" * 70)
    r = client.post(
        "/api/v1/chat",
        json={"message": ""},
        headers={"Authorization": f"Bearer {_Ctx.api_key_secret}"},
    )
    assert r.status_code == 422
    print("  ✅ 422")


def test_payload_too_long():
    print("\n" + "=" * 70)
    print("TEST 17: mensaje > 2000 → 422")
    print("=" * 70)
    r = client.post(
        "/api/v1/chat",
        json={"message": "x" * 2001},
        headers={"Authorization": f"Bearer {_Ctx.api_key_secret}"},
    )
    assert r.status_code == 422
    print("  ✅ 422")


# ============================================================
# CLEANUP
# ============================================================

def test_cleanup():
    print("\n" + "=" * 70)
    print("TEST 18: Cleanup (borrar users/bots/keys/sessions)")
    print("=" * 70)
    from sqlalchemy import text
    from app.database.config import engine

    # Usar SQL directo con session_replication_role para saltar FKs no-CASCADE
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys=OFF"))

        pattern = "apichat_%"

        # Borrar todo lo que apunta a bots/users del test
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

    print("  ✅ Datos limpiados")
    reset_public_all()


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.10.7 (POST /api/v1/chat)")
    print("=" * 70)

    tests = [
        test_setup,
        # Auth
        test_auth_no_header,
        test_auth_wrong_scheme,
        test_auth_basic_scheme,
        test_auth_nonexistent_key,
        test_auth_revoked_key,
        test_auth_expired_key,
        # Sesiones
        test_chat_creates_session,
        test_chat_recovers_session,
        # Chat E2E
        test_chat_e2e_response,
        test_chat_multi_turno,
        test_chat_session_not_other_bot,
        test_chat_does_not_leak_internals,
        test_chat_analytics_saved,
        # Estados
        test_chat_bot_not_published,
        # Rate limiting
        test_rate_limit_429,
        # Validación
        test_payload_empty_message,
        test_payload_too_long,
        # Cleanup
        test_cleanup,
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
