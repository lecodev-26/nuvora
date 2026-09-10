"""
Tests — Subfase 14.4.6
Verifica el router /training.
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.main import app
from app.database.config import SessionLocal
from app.models.db_models import (
    Bot, User, Memory, Conversation,
)


client = TestClient(app)


# ============================================================
# HELPERS
# ============================================================

def _register_and_login(suffix: str) -> tuple[str, str]:
    """Registra un usuario y devuelve (email, token)."""
    email = f"test_training_{suffix}@nuvora.com"
    password = "123456"

    client.post("/auth/register", json={
        "email": email,
        "password": password,
        "full_name": f"Test Training {suffix}",
    })

    r = client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return email, r.json()["access_token"]


def _create_bot(token: str, suffix: str, nicho_id: str = "otro") -> int:
    r = client.post(
        "/bots/",
        json={
            "name": f"Bot Training {suffix}",
            "business_name": f"Test {suffix}",
            "nicho_id": nicho_id,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _cleanup_bot(bot_id: int):
    db = SessionLocal()
    try:
        db.query(Conversation).filter(Conversation.bot_id == bot_id).delete(synchronize_session=False)
        db.query(Memory).filter(Memory.bot_id == bot_id).delete(synchronize_session=False)
        db.query(Bot).filter(Bot.id == bot_id).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _cleanup_user(email: str):
    db = SessionLocal()
    try:
        db.query(User).filter(User.email == email).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


# ============================================================
# TESTS
# ============================================================

def test_training_200_ok():
    print("\n" + "=" * 70)
    print("TEST 1: Endpoint devuelve 200")
    print("=" * 70)
    email, token = _register_and_login("t1")
    bot_id = _create_bot(token, "t1")
    try:
        r = client.get(
            f"/training/{bot_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["bot_id"] == bot_id
        assert "progress" in data
        assert "topics" in data
        print(f"✅ 200 OK, bot_id={bot_id}")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user(email)


def test_training_401_no_auth():
    print("\n" + "=" * 70)
    print("TEST 2: Sin token → 401")
    print("=" * 70)
    r = client.get("/training/1")
    assert r.status_code == 401
    print(f"✅ 401 correcto")


def test_training_403_not_owner():
    print("\n" + "=" * 70)
    print("TEST 3: Usuario ajeno → 403")
    print("=" * 70)
    email_a, token_a = _register_and_login("t3a")
    bot_id = _create_bot(token_a, "t3a")
    email_b, token_b = _register_and_login("t3b")
    try:
        r = client.get(
            f"/training/{bot_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert r.status_code == 403
        print(f"✅ 403 correcto")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user(email_a)
        _cleanup_user(email_b)


def test_training_404_bot_not_found():
    print("\n" + "=" * 70)
    print("TEST 4: Bot inexistente → 404")
    print("=" * 70)
    email, token = _register_and_login("t4")
    try:
        r = client.get(
            "/training/999999",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 404
        print(f"✅ 404 correcto")
    finally:
        _cleanup_user(email)


def test_training_conversation_limit_param():
    print("\n" + "=" * 70)
    print("TEST 5: conversation_limit funciona")
    print("=" * 70)
    email, token = _register_and_login("t5")
    bot_id = _create_bot(token, "t5")
    try:
        r = client.get(
            f"/training/{bot_id}?conversation_limit=50",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        print(f"✅ limit=50 OK")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user(email)


def test_training_conversation_limit_out_of_range():
    print("\n" + "=" * 70)
    print("TEST 6: conversation_limit fuera de rango → 422")
    print("=" * 70)
    email, token = _register_and_login("t6")
    bot_id = _create_bot(token, "t6")
    try:
        r0 = client.get(
            f"/training/{bot_id}?conversation_limit=0",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r0.status_code == 422

        r1000 = client.get(
            f"/training/{bot_id}?conversation_limit=1000",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r1000.status_code == 422
        print(f"✅ 422 correcto para 0 y 1000")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user(email)


def test_training_multitenant_isolation():
    print("\n" + "=" * 70)
    print("TEST 7: Aislamiento multi-tenant")
    print("=" * 70)
    email_a, token_a = _register_and_login("t7a")
    bot_a = _create_bot(token_a, "t7a")
    email_b, token_b = _register_and_login("t7b")
    bot_b = _create_bot(token_b, "t7b")
    try:
        # Cada usuario ve su propio bot
        r_a = client.get(
            f"/training/{bot_a}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        r_b = client.get(
            f"/training/{bot_b}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert r_a.status_code == 200
        assert r_b.status_code == 200
        assert r_a.json()["bot_id"] == bot_a
        assert r_b.json()["bot_id"] == bot_b

        # A no puede ver B
        r_cross = client.get(
            f"/training/{bot_b}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert r_cross.status_code == 403
        print(f"✅ Aislamiento OK")
    finally:
        _cleanup_bot(bot_a)
        _cleanup_bot(bot_b)
        _cleanup_user(email_a)
        _cleanup_user(email_b)


def test_training_response_schema():
    print("\n" + "=" * 70)
    print("TEST 8: Estructura de TrainingReport")
    print("=" * 70)
    email, token = _register_and_login("t8")
    bot_id = _create_bot(token, "t8")
    try:
        r = client.get(
            f"/training/{bot_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = r.json()
        required = [
            "bot_id", "bot_name", "nicho_id",
            "progress", "total_topics",
            "covered_count", "partial_count", "missing_count",
            "topics", "missing_topics", "partial_topics",
            "unanswered_questions", "recommendations",
            "analyzed_at", "has_memories", "has_sources",
            "memories_count", "ready_sources_count", "conversations_analyzed",
        ]
        for k in required:
            assert k in data, f"Falta: {k}"
        print(f"✅ Estructura OK: {len(required)} campos")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user(email)


def test_training_returns_progress():
    print("\n" + "=" * 70)
    print("TEST 9: Devuelve progress calculado")
    print("=" * 70)
    email, token = _register_and_login("t9")
    bot_id = _create_bot(token, "t9")
    try:
        r = client.get(
            f"/training/{bot_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = r.json()
        assert isinstance(data["progress"], (int, float))
        assert 0.0 <= data["progress"] <= 1.0
        print(f"✅ progress={data['progress']}")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user(email)


def test_training_returns_topics():
    print("\n" + "=" * 70)
    print("TEST 10: Devuelve lista de topics")
    print("=" * 70)
    email, token = _register_and_login("t10")
    bot_id = _create_bot(token, "t10", nicho_id="restaurantes")
    try:
        r = client.get(
            f"/training/{bot_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = r.json()
        assert len(data["topics"]) == 11
        assert data["total_topics"] == 11
        print(f"✅ {len(data['topics'])} topics de restaurantes")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user(email)


def test_training_returns_recommendations():
    print("\n" + "=" * 70)
    print("TEST 11: Devuelve recommendations")
    print("=" * 70)
    email, token = _register_and_login("t11")
    bot_id = _create_bot(token, "t11")
    try:
        r = client.get(
            f"/training/{bot_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = r.json()
        # Bot vacío → todos MISSING → recomendaciones
        assert isinstance(data["recommendations"], list)
        assert len(data["recommendations"]) > 0
        for rec in data["recommendations"]:
            assert "id" in rec
            assert "type" in rec
            assert "title" in rec
            assert "action_payload" in rec
        print(f"✅ {len(data['recommendations'])} recomendaciones")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user(email)


def test_training_does_not_write_db():
    print("\n" + "=" * 70)
    print("TEST 12: No modifica la BD")
    print("=" * 70)
    email, token = _register_and_login("t12")
    bot_id = _create_bot(token, "t12")
    try:
        db = SessionLocal()
        before_bots = db.query(Bot).count()
        before_mem = db.query(Memory).count()
        before_conv = db.query(Conversation).count()
        db.close()

        client.get(
            f"/training/{bot_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        db = SessionLocal()
        after_bots = db.query(Bot).count()
        after_mem = db.query(Memory).count()
        after_conv = db.query(Conversation).count()
        db.close()

        assert before_bots == after_bots
        assert before_mem == after_mem
        assert before_conv == after_conv
        print(f"✅ Sin side effects")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user(email)


def test_training_bot_inactive():
    print("\n" + "=" * 70)
    print("TEST 13: Bot inactivo → 200 con reporte")
    print("=" * 70)
    email, token = _register_and_login("t13")
    bot_id = _create_bot(token, "t13")
    try:
        # Desactivar bot directamente en BD
        db = SessionLocal()
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        bot.is_active = False
        db.commit()
        db.close()

        r = client.get(
            f"/training/{bot_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        print(f"✅ Bot inactivo devuelve 200")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user(email)


def test_training_performance():
    print("\n" + "=" * 70)
    print("TEST 14: Rendimiento (informativo)")
    print("=" * 70)
    email, token = _register_and_login("t14")
    bot_id = _create_bot(token, "t14", nicho_id="restaurantes")
    try:
        start = time.monotonic()
        r = client.get(
            f"/training/{bot_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        elapsed_ms = int((time.monotonic() - start) * 1000)
        assert r.status_code == 200
        print(f"✅ Endpoint responde en {elapsed_ms} ms")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user(email)


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.4.6 (Router /training)")
    print("=" * 70)

    tests = [
        test_training_200_ok,
        test_training_401_no_auth,
        test_training_403_not_owner,
        test_training_404_bot_not_found,
        test_training_conversation_limit_param,
        test_training_conversation_limit_out_of_range,
        test_training_multitenant_isolation,
        test_training_response_schema,
        test_training_returns_progress,
        test_training_returns_topics,
        test_training_returns_recommendations,
        test_training_does_not_write_db,
        test_training_bot_inactive,
        test_training_performance,
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
