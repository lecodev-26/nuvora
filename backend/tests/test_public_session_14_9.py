"""
Tests — Subfase 14.9.7 (Public Session Service)
==================================================
Cubre:
    - create_session: UUID, status, TTL, session_data inicial
    - get_session: OK, 404, input inválido, sesión ajena, cerrada, expirada
    - append_message: user, bot, múltiples, límite 50
    - get_session_messages
    - close_session: get_session después → 404
    - expire_old_sessions: marca caducadas, no toca activas
"""

import sys
import os
import time
import json
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import HTTPException

from app.database.config import SessionLocal
from app.models.db_models import Bot, User, PublicSession
from app.services.public_session import (
    create_session, get_session, get_session_messages,
    append_message, append_user_message, append_bot_message,
    close_session, expire_old_sessions,
    SESSION_TTL_SECONDS, MAX_SESSION_MESSAGES,
    STATUS_ACTIVE, STATUS_EXPIRED, STATUS_CLOSED,
)


# ============================================================
# HELPERS
# ============================================================

def _unique(suffix):
    return f"{suffix}_{int(time.time() * 1000000)}_{os.getpid()}"


def _cleanup_user(db, email):
    u = db.query(User).filter(User.email == email).first()
    if u:
        bots = db.query(Bot).filter(Bot.user_id == u.id).all()
        for b in bots:
            db.delete(b)
        db.delete(u)
        db.commit()


def _create_user(db):
    email = f"{_unique('pub_sess_user')}@nuvora.com"
    u = User(email=email, hashed_password="x", full_name="Session Test")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u, email


def _create_bot(db, user_id, name=None):
    b = Bot(
        user_id=user_id,
        name=name or f"Bot {_unique('bsess')}",
        business_name="Test",
        nicho_id="otro",
        is_published=True,
        public_id=_unique("pid"),
        public_slug=_unique("slug"),
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


# ============================================================
# TESTS — create_session
# ============================================================

def test_create_session_basic():
    print("\n" + "=" * 70)
    print("TEST 1: create_session — básico")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        s = create_session(b, db)
        assert s.id is not None
        assert s.bot_id == b.id
        assert s.status == STATUS_ACTIVE
        assert len(s.public_id) == 36
        assert s.public_id.count("-") == 4
        assert s.session_data == "[]"
        assert s.expires_at is not None
        print(f"  ✅ session #{s.id}, public_id={s.public_id[:8]}...")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_create_session_ttl():
    print("\n" + "=" * 70)
    print("TEST 2: create_session — TTL correcto (~1h)")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        before = datetime.now(timezone.utc)
        s = create_session(b, db)
        after = datetime.now(timezone.utc)

        exp = s.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)

        delta_before = (exp - before).total_seconds()
        delta_after = (exp - after).total_seconds()

        # Debe estar entre ~3599 y ~3601 segundos
        assert 3599 <= delta_before <= 3602, f"delta_before={delta_before}"
        assert 3598 <= delta_after <= 3601, f"delta_after={delta_after}"
        print(f"  ✅ TTL ~{int(delta_after)}s (esperado ~{SESSION_TTL_SECONDS})")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_create_session_unique_public_ids():
    print("\n" + "=" * 70)
    print("TEST 3: create_session — public_ids únicos")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        pids = {create_session(b, db).public_id for _ in range(10)}
        assert len(pids) == 10
        print(f"  ✅ 10 sessions con public_id únicos")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


# ============================================================
# TESTS — get_session
# ============================================================

def test_get_session_ok():
    print("\n" + "=" * 70)
    print("TEST 4: get_session — OK")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        s = create_session(b, db)
        found = get_session(s.public_id, b, db)
        assert found.id == s.id
        print(f"  ✅ Encontrada sesión #{found.id}")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_get_session_not_found():
    print("\n" + "=" * 70)
    print("TEST 5: get_session — ID inexistente → 404")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        try:
            get_session("non-existent-uuid", b, db)
            raise AssertionError("Debería haber lanzado 404")
        except HTTPException as e:
            assert e.status_code == 404
        print("  ✅ 404")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_get_session_invalid_input():
    print("\n" + "=" * 70)
    print("TEST 6: get_session — input inválido → 404")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        for bad in [None, "", 123, [], {}]:
            try:
                get_session(bad, b, db)
                raise AssertionError(f"Debería haber lanzado 404 con {bad!r}")
            except HTTPException as e:
                assert e.status_code == 404
        print("  ✅ 5 inputs inválidos → 404")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_get_session_other_bot():
    print("\n" + "=" * 70)
    print("TEST 7: get_session — sesión de OTRO bot → 404 (multi-tenant)")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        bot_a = _create_bot(db, u.id, name="Bot A")
        bot_b = _create_bot(db, u.id, name="Bot B")
        s_a = create_session(bot_a, db)

        # Intentamos acceder con bot_b
        try:
            get_session(s_a.public_id, bot_b, db)
            raise AssertionError("Debería haber lanzado 404")
        except HTTPException as e:
            assert e.status_code == 404
        print("  ✅ 404 (aislamiento multi-tenant)")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_get_session_closed():
    print("\n" + "=" * 70)
    print("TEST 8: get_session — sesión cerrada → 404")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        s = create_session(b, db)
        close_session(s, db)
        try:
            get_session(s.public_id, b, db)
            raise AssertionError("Debería haber lanzado 404")
        except HTTPException as e:
            assert e.status_code == 404
        print("  ✅ 404 (sesión cerrada)")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_get_session_expired():
    print("\n" + "=" * 70)
    print("TEST 9: get_session — sesión expirada → 404 + marca expired")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        s = create_session(b, db)

        # Forzar expires_at al pasado
        s.expires_at = datetime.now(timezone.utc) - timedelta(seconds=10)
        db.commit()

        try:
            get_session(s.public_id, b, db)
            raise AssertionError("Debería haber lanzado 404")
        except HTTPException as e:
            assert e.status_code == 404

        # Verificar que se marcó como expirada
        db.refresh(s)
        assert s.status == STATUS_EXPIRED
        print(f"  ✅ 404 + status='{s.status}'")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


# ============================================================
# TESTS — append_message
# ============================================================

def test_append_user_message():
    print("\n" + "=" * 70)
    print("TEST 10: append_user_message")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        s = create_session(b, db)
        append_user_message(s, "Hola", db)
        msgs = get_session_messages(s)
        assert len(msgs) == 1
        assert msgs[0]["role"] == "user"
        assert msgs[0]["content"] == "Hola"
        assert "ts" in msgs[0]
        print("  ✅ user message OK")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_append_bot_message():
    print("\n" + "=" * 70)
    print("TEST 11: append_bot_message")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        s = create_session(b, db)
        append_bot_message(s, "¡Hola!", db)
        msgs = get_session_messages(s)
        assert len(msgs) == 1
        assert msgs[0]["role"] == "bot"
        assert msgs[0]["content"] == "¡Hola!"
        print("  ✅ bot message OK")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_append_multiple_messages():
    print("\n" + "=" * 70)
    print("TEST 12: append múltiples → orden correcto")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        s = create_session(b, db)

        append_user_message(s, "msg1", db)
        append_bot_message(s, "resp1", db)
        append_user_message(s, "msg2", db)
        append_bot_message(s, "resp2", db)

        msgs = get_session_messages(s)
        assert len(msgs) == 4
        assert [m["role"] for m in msgs] == ["user", "bot", "user", "bot"]
        assert [m["content"] for m in msgs] == ["msg1", "resp1", "msg2", "resp2"]
        print("  ✅ 4 mensajes en orden correcto")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_append_message_limit():
    print("\n" + "=" * 70)
    print("TEST 13: append supera límite → 400")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        s = create_session(b, db)

        # Rellenamos hasta el máximo
        for i in range(MAX_SESSION_MESSAGES):
            append_user_message(s, f"m{i}", db)

        # El siguiente debe fallar
        try:
            append_user_message(s, "boom", db)
            raise AssertionError("Debería haber lanzado 400")
        except HTTPException as e:
            assert e.status_code == 400
        print(f"  ✅ 400 al superar {MAX_SESSION_MESSAGES} mensajes")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


# ============================================================
# TESTS — get_session_messages
# ============================================================

def test_get_messages_empty():
    print("\n" + "=" * 70)
    print("TEST 14: get_session_messages — vacío → []")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        s = create_session(b, db)
        assert get_session_messages(s) == []
        print("  ✅ []")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_get_messages_after_append():
    print("\n" + "=" * 70)
    print("TEST 15: get_session_messages tras append")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        s = create_session(b, db)
        append_user_message(s, "hola", db)
        msgs = get_session_messages(s)
        assert len(msgs) == 1
        assert msgs[0]["content"] == "hola"
        print("  ✅ 1 mensaje devuelto")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


# ============================================================
# TESTS — expire_old_sessions
# ============================================================

def test_expire_old_sessions():
    print("\n" + "=" * 70)
    print("TEST 16: expire_old_sessions — marca caducadas")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)

        # Una caducada, una activa
        s_old = create_session(b, db)
        s_old.expires_at = datetime.now(timezone.utc) - timedelta(hours=2)
        db.commit()

        s_new = create_session(b, db)

        n = expire_old_sessions(db)
        assert n >= 1

        db.refresh(s_old)
        db.refresh(s_new)

        assert s_old.status == STATUS_EXPIRED
        assert s_new.status == STATUS_ACTIVE
        print(f"  ✅ {n} sesión(es) expirada(s), activa intacta")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


# ============================================================
# TESTS — close_session
# ============================================================

def test_close_session():
    print("\n" + "=" * 70)
    print("TEST 17: close_session — marca closed")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        s = create_session(b, db)
        close_session(s, db)
        db.refresh(s)
        assert s.status == STATUS_CLOSED
        print("  ✅ status='closed'")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_close_session_then_get_404():
    print("\n" + "=" * 70)
    print("TEST 18: close_session → get_session lanza 404")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        s = create_session(b, db)
        close_session(s, db)
        try:
            get_session(s.public_id, b, db)
            raise AssertionError("Debería haber lanzado 404")
        except HTTPException as e:
            assert e.status_code == 404
        print("  ✅ 404 tras cerrar")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.9.7 (Public Session Service)")
    print("=" * 70)

    tests = [
        test_create_session_basic,
        test_create_session_ttl,
        test_create_session_unique_public_ids,
        test_get_session_ok,
        test_get_session_not_found,
        test_get_session_invalid_input,
        test_get_session_other_bot,
        test_get_session_closed,
        test_get_session_expired,
        test_append_user_message,
        test_append_bot_message,
        test_append_multiple_messages,
        test_append_message_limit,
        test_get_messages_empty,
        test_get_messages_after_append,
        test_expire_old_sessions,
        test_close_session,
        test_close_session_then_get_404,
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
