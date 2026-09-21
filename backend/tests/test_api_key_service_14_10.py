"""
Tests — Subfase 14.10.3 (ApiKeyService)
=========================================
Cubre:
    - generate_api_key / hash_key / verify_key
    - create_api_key (OK + 404 + 403)
    - list_api_keys
    - revoke_api_key (OK + idempotente + 404/403)
    - resolve_api_key (OK + 401 formato + 401 no existe + 401 revocada + 401 expirada)
    - touch_last_used (throttle)
"""

import sys
import os
import time
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import HTTPException

from app.database.config import SessionLocal
from app.models.db_models import User, Bot, ApiKey
from app.services.api_key_service import (
    generate_api_key,
    hash_key,
    verify_key,
    create_api_key,
    list_api_keys,
    revoke_api_key,
    resolve_api_key,
    touch_last_used,
    KEY_PREFIX,
    TOUCH_INTERVAL_SECONDS,
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
    email = f"{_unique('svc_user')}@nuvora.com"
    u = User(email=email, hashed_password="x", full_name="Service Test")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u, email


def _create_bot(db, user_id):
    b = Bot(
        user_id=user_id,
        name=f"Bot {_unique('svc')}",
        business_name="Test",
        nicho_id="otro",
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


# ============================================================
# TESTS — Generación y hash
# ============================================================

def test_generate_api_key_format():
    print("\n" + "=" * 70)
    print("TEST 1: generate_api_key — formato correcto")
    print("=" * 70)
    full, prefix, h = generate_api_key()
    assert full.startswith(KEY_PREFIX), f"Key sin prefijo: {full[:20]}"
    assert len(h) == 64, f"Hash no es 64 chars: {len(h)}"
    assert prefix.startswith(KEY_PREFIX)
    assert prefix == full[:len(KEY_PREFIX) + 8]
    print(f"  ✅ full={full[:20]}... prefix={prefix} hash_len={len(h)}")


def test_generate_api_key_unique():
    print("\n" + "=" * 70)
    print("TEST 2: generate_api_key — 100 keys únicas")
    print("=" * 70)
    keys = {generate_api_key()[0] for _ in range(100)}
    assert len(keys) == 100
    print("  ✅ 100 keys únicas")


def test_hash_key_deterministic():
    print("\n" + "=" * 70)
    print("TEST 3: hash_key — determinista")
    print("=" * 70)
    key = "nvr_live_test123"
    h1 = hash_key(key)
    h2 = hash_key(key)
    assert h1 == h2
    assert len(h1) == 64
    print(f"  ✅ hash estable: {h1[:16]}...")


def test_verify_key():
    print("\n" + "=" * 70)
    print("TEST 4: verify_key — True/False correctos")
    print("=" * 70)
    full, _, h = generate_api_key()
    assert verify_key(full, h) is True
    assert verify_key("otra-key", h) is False
    assert verify_key("", h) is False
    assert verify_key(full, "") is False
    print("  ✅ verify_key OK")


# ============================================================
# TESTS — Crear
# ============================================================

def test_create_api_key_ok():
    print("\n" + "=" * 70)
    print("TEST 5: create_api_key — OK")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)

        obj, full = create_api_key(db, u.id, b.id, "Mi integración")
        assert obj.id is not None
        assert obj.name == "Mi integración"
        assert obj.user_id == u.id
        assert obj.bot_id == b.id
        assert obj.is_active is True
        assert full.startswith(KEY_PREFIX)
        assert obj.key_hash == hash_key(full)
        assert obj.key_hash != full  # ¡NUNCA guardar la key completa!
        print(f"  ✅ ApiKey #{obj.id} creada")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_create_api_key_bot_not_found():
    print("\n" + "=" * 70)
    print("TEST 6: create_api_key — bot inexistente → 404")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        try:
            create_api_key(db, u.id, 999999999, "X")
            raise AssertionError("Debería lanzar 404")
        except HTTPException as e:
            assert e.status_code == 404
            print("  ✅ 404")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_create_api_key_wrong_user():
    print("\n" + "=" * 70)
    print("TEST 7: create_api_key — bot de otro user → 403")
    print("=" * 70)
    db = SessionLocal()
    u1 = None
    u2 = None
    try:
        u1, e1 = _create_user(db)
        u2, e2 = _create_user(db)
        bot1 = _create_bot(db, u1.id)

        try:
            create_api_key(db, u2.id, bot1.id, "Intento")
            raise AssertionError("Debería lanzar 403")
        except HTTPException as e:
            assert e.status_code == 403
            print("  ✅ 403")
    finally:
        if u1:
            _cleanup_user(db, u1.email)
        if u2:
            _cleanup_user(db, u2.email)
        db.close()


# ============================================================
# TESTS — Listar
# ============================================================

def test_list_api_keys_empty():
    print("\n" + "=" * 70)
    print("TEST 8: list_api_keys — vacío")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        keys = list_api_keys(db, u.id, b.id)
        assert keys == []
        print("  ✅ Lista vacía")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_list_api_keys_isolated():
    print("\n" + "=" * 70)
    print("TEST 9: list_api_keys — solo keys del bot correcto")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b1 = _create_bot(db, u.id)
        b2 = _create_bot(db, u.id)

        create_api_key(db, u.id, b1.id, "key-b1-a")
        create_api_key(db, u.id, b1.id, "key-b1-b")
        create_api_key(db, u.id, b2.id, "key-b2")

        keys_b1 = list_api_keys(db, u.id, b1.id)
        keys_b2 = list_api_keys(db, u.id, b2.id)
        assert len(keys_b1) == 2
        assert len(keys_b2) == 1
        print(f"  ✅ b1={len(keys_b1)} keys, b2={len(keys_b2)} keys")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


# ============================================================
# TESTS — Revocar
# ============================================================

def test_revoke_api_key():
    print("\n" + "=" * 70)
    print("TEST 10: revoke_api_key — OK")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        obj, _ = create_api_key(db, u.id, b.id, "revoke-test")

        revoked = revoke_api_key(db, obj.id, u.id)
        assert revoked.is_active is False
        assert revoked.revoked_at is not None
        print(f"  ✅ ApiKey #{revoked.id} revocada")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_revoke_api_key_idempotent():
    print("\n" + "=" * 70)
    print("TEST 11: revoke_api_key — idempotente")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        obj, _ = create_api_key(db, u.id, b.id, "idem-test")

        rev1 = revoke_api_key(db, obj.id, u.id)
        first_date = rev1.revoked_at
        time.sleep(0.01)
        rev2 = revoke_api_key(db, obj.id, u.id)
        # No cambia revoked_at
        assert rev2.revoked_at == first_date
        print("  ✅ Idempotente (no cambia revoked_at)")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_revoke_api_key_not_found():
    print("\n" + "=" * 70)
    print("TEST 12: revoke_api_key — inexistente → 404")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        try:
            revoke_api_key(db, 999999999, u.id)
            raise AssertionError("Debería lanzar 404")
        except HTTPException as e:
            assert e.status_code == 404
            print("  ✅ 404")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_revoke_api_key_wrong_user():
    print("\n" + "=" * 70)
    print("TEST 13: revoke_api_key — otro user → 403")
    print("=" * 70)
    db = SessionLocal()
    u1 = None
    u2 = None
    try:
        u1, e1 = _create_user(db)
        u2, e2 = _create_user(db)
        b1 = _create_bot(db, u1.id)
        obj, _ = create_api_key(db, u1.id, b1.id, "X")

        try:
            revoke_api_key(db, obj.id, u2.id)
            raise AssertionError("Debería lanzar 403")
        except HTTPException as e:
            assert e.status_code == 403
            print("  ✅ 403")
    finally:
        if u1:
            _cleanup_user(db, u1.email)
        if u2:
            _cleanup_user(db, u2.email)
        db.close()


# ============================================================
# TESTS — Resolver (Bearer → key + bot)
# ============================================================

def test_resolve_api_key_ok():
    print("\n" + "=" * 70)
    print("TEST 14: resolve_api_key — OK")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        obj, full = create_api_key(db, u.id, b.id, "resolve")

        resolved_key, resolved_bot = resolve_api_key(db, full)
        assert resolved_key.id == obj.id
        assert resolved_bot.id == b.id
        print(f"  ✅ Key #{resolved_key.id} → Bot #{resolved_bot.id}")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_resolve_api_key_invalid_format():
    print("\n" + "=" * 70)
    print("TEST 15: resolve_api_key — formato incorrecto → 401")
    print("=" * 70)
    db = SessionLocal()
    try:
        for bad in ["", "abc", "nvr_live", "Bearer xyz"]:
            try:
                resolve_api_key(db, bad)
                raise AssertionError(f"Debería lanzar 401 con '{bad}'")
            except HTTPException as e:
                assert e.status_code == 401
        print("  ✅ 4 formatos inválidos → 401")
    finally:
        db.close()


def test_resolve_api_key_not_found():
    print("\n" + "=" * 70)
    print("TEST 16: resolve_api_key — key no existe → 401")
    print("=" * 70)
    db = SessionLocal()
    try:
        try:
            resolve_api_key(db, "nvr_live_inexistente_xyz")
            raise AssertionError("Debería lanzar 401")
        except HTTPException as e:
            assert e.status_code == 401
        print("  ✅ 401")
    finally:
        db.close()


def test_resolve_api_key_revoked():
    print("\n" + "=" * 70)
    print("TEST 17: resolve_api_key — key revocada → 401")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        obj, full = create_api_key(db, u.id, b.id, "revoke-resolve")

        revoke_api_key(db, obj.id, u.id)

        try:
            resolve_api_key(db, full)
            raise AssertionError("Debería lanzar 401")
        except HTTPException as e:
            assert e.status_code == 401
            assert "revocada" in e.detail.lower()
        print("  ✅ 401 (revocada)")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_resolve_api_key_expired():
    print("\n" + "=" * 70)
    print("TEST 18: resolve_api_key — key expirada → 401")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        obj, full = create_api_key(db, u.id, b.id, "expired")

        # Forzar expiración al pasado
        obj.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        db.commit()

        try:
            resolve_api_key(db, full)
            raise AssertionError("Debería lanzar 401")
        except HTTPException as e:
            assert e.status_code == 401
            assert "expirada" in e.detail.lower()
        print("  ✅ 401 (expirada)")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


# ============================================================
# TESTS — Touch last_used_at
# ============================================================

def test_touch_first_time():
    print("\n" + "=" * 70)
    print("TEST 19: touch_last_used — primera vez")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        obj, _ = create_api_key(db, u.id, b.id, "touch")
        assert obj.last_used_at is None

        touch_last_used(db, obj)
        db.refresh(obj)
        assert obj.last_used_at is not None
        print(f"  ✅ last_used_at: {obj.last_used_at}")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_touch_throttled():
    print("\n" + "=" * 70)
    print("TEST 20: touch_last_used — throttled (<60s)")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        obj, _ = create_api_key(db, u.id, b.id, "touch2")

        # Primer touch
        touch_last_used(db, obj)
        db.refresh(obj)
        first_used = obj.last_used_at

        # Segundo touch inmediato → NO debe actualizar
        time.sleep(0.01)
        touch_last_used(db, obj)
        db.refresh(obj)
        assert obj.last_used_at == first_used
        print(f"  ✅ No actualizado (<{TOUCH_INTERVAL_SECONDS}s)")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_touch_after_interval():
    print("\n" + "=" * 70)
    print("TEST 21: touch_last_used — sí actualiza (>60s)")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        obj, _ = create_api_key(db, u.id, b.id, "touch3")

        # Forzar last_used_at al pasado (>60s)
        obj.last_used_at = datetime.now(timezone.utc) - timedelta(seconds=120)
        db.commit()
        first_used = obj.last_used_at

        touch_last_used(db, obj)
        db.refresh(obj)
        assert obj.last_used_at > first_used
        print("  ✅ Actualizado tras >60s")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()




# ============================================================
# CLEANUP
# ============================================================

def test_cleanup():
    print("\n" + "=" * 70)
    print("TEST CLEANUP: borrar datos residuales de este test file")
    print("=" * 70)
    from sqlalchemy import text
    from app.database.config import engine

    pattern = "svc_user_%"
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys=OFF"))
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
    print(f"  ✅ Datos limpiados (pattern={pattern})")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.10.3 (ApiKeyService)")
    print("=" * 70)

    tests = [
        # Generación
        test_generate_api_key_format,
        test_generate_api_key_unique,
        test_hash_key_deterministic,
        test_verify_key,
        # Crear
        test_create_api_key_ok,
        test_create_api_key_bot_not_found,
        test_create_api_key_wrong_user,
        # Listar
        test_list_api_keys_empty,
        test_list_api_keys_isolated,
        # Revocar
        test_revoke_api_key,
        test_revoke_api_key_idempotent,
        test_revoke_api_key_not_found,
        test_revoke_api_key_wrong_user,
        # Resolver
        test_resolve_api_key_ok,
        test_resolve_api_key_invalid_format,
        test_resolve_api_key_not_found,
        test_resolve_api_key_revoked,
        test_resolve_api_key_expired,
        # Touch
        test_touch_first_time,
        test_touch_throttled,
        test_touch_after_interval,
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
