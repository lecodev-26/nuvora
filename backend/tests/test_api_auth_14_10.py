"""
Tests — Subfase 14.10.5 (api_auth)
=====================================
Cubre:
    - extract_bearer_token: formatos válidos e inválidos
    - get_api_key_context: integración con ApiKeyService
"""

import sys
import os
import time
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import HTTPException

from app.database.config import SessionLocal
from app.models.db_models import User, Bot, ApiKey
from app.core.api_auth import (
    ApiKeyContext,
    extract_bearer_token,
    get_api_key_context,
)
from app.services.api_key_service import create_api_key, revoke_api_key


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
    email = f"{_unique('auth_user')}@nuvora.com"
    u = User(email=email, hashed_password="x", full_name="Auth Test")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u, email


def _create_bot(db, user_id):
    b = Bot(
        user_id=user_id,
        name=f"Bot {_unique('auth')}",
        business_name="Test",
        nicho_id="otro",
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


# ============================================================
# TESTS — extract_bearer_token
# ============================================================

def test_extract_valid():
    print("\n" + "=" * 70)
    print("TEST 1: extract_bearer_token — válido")
    print("=" * 70)
    assert extract_bearer_token("Bearer nvr_live_abc") == "nvr_live_abc"
    print("  ✅ OK")


def test_extract_case_insensitive():
    print("\n" + "=" * 70)
    print("TEST 2: extract_bearer_token — case-insensitive")
    print("=" * 70)
    assert extract_bearer_token("bearer nvr_live_abc") == "nvr_live_abc"
    assert extract_bearer_token("BEARER nvr_live_abc") == "nvr_live_abc"
    assert extract_bearer_token("BeArEr nvr_live_abc") == "nvr_live_abc"
    print("  ✅ Case-insensitive OK")


def test_extract_extra_spaces():
    print("\n" + "=" * 70)
    print("TEST 3: extract_bearer_token — espacios extra")
    print("=" * 70)
    # strip() tolera espacios alrededor, pero internos se detectan
    assert extract_bearer_token("  Bearer nvr_live_abc  ") == "nvr_live_abc"
    print("  ✅ Espacios externos tolerados")


def test_extract_missing_header():
    print("\n" + "=" * 70)
    print("TEST 4: extract_bearer_token — header ausente → 401")
    print("=" * 70)
    try:
        extract_bearer_token(None)
        raise AssertionError("Debería haber fallado")
    except HTTPException as e:
        assert e.status_code == 401
    print("  ✅ 401")


def test_extract_empty_header():
    print("\n" + "=" * 70)
    print("TEST 5: extract_bearer_token — header vacío → 401")
    print("=" * 70)
    try:
        extract_bearer_token("")
        raise AssertionError("Debería haber fallado")
    except HTTPException as e:
        assert e.status_code == 401
    print("  ✅ 401")


def test_extract_no_bearer():
    print("\n" + "=" * 70)
    print("TEST 6: extract_bearer_token — sin Bearer → 401")
    print("=" * 70)
    for bad in ["nvr_live_abc", "Basic xyz", "Digest abc"]:
        try:
            extract_bearer_token(bad)
            raise AssertionError(f"Debería fallar con {bad!r}")
        except HTTPException as e:
            assert e.status_code == 401
    print("  ✅ 3 esquemas inválidos → 401")


def test_extract_empty_token():
    print("\n" + "=" * 70)
    print("TEST 7: extract_bearer_token — token vacío → 401")
    print("=" * 70)
    try:
        extract_bearer_token("Bearer ")
        raise AssertionError("Debería haber fallado")
    except HTTPException as e:
        assert e.status_code == 401
    print("  ✅ 401")


def test_extract_too_many_parts():
    print("\n" + "=" * 70)
    print("TEST 8: extract_bearer_token — más de 2 partes → 401")
    print("=" * 70)
    try:
        extract_bearer_token("Bearer nvr_live_abc extra")
        raise AssertionError("Debería haber fallado")
    except HTTPException as e:
        assert e.status_code == 401
    print("  ✅ 401")


# ============================================================
# TESTS — get_api_key_context
# ============================================================

def test_get_context_ok():
    print("\n" + "=" * 70)
    print("TEST 9: get_api_key_context — OK")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        obj, full = create_api_key(db, u.id, b.id, "auth-test")

        ctx = get_api_key_context(authorization=f"Bearer {full}", db=db)
        assert isinstance(ctx, ApiKeyContext)
        assert ctx.api_key.id == obj.id
        assert ctx.bot.id == b.id
        print(f"  ✅ Key #{ctx.api_key.id} → Bot #{ctx.bot.id}")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_get_context_missing_header():
    print("\n" + "=" * 70)
    print("TEST 10: get_api_key_context — sin header → 401")
    print("=" * 70)
    db = SessionLocal()
    try:
        try:
            get_api_key_context(authorization=None, db=db)
            raise AssertionError("Debería haber fallado")
        except HTTPException as e:
            assert e.status_code == 401
        print("  ✅ 401")
    finally:
        db.close()


def test_get_context_invalid_key():
    print("\n" + "=" * 70)
    print("TEST 11: get_api_key_context — key inexistente → 401")
    print("=" * 70)
    db = SessionLocal()
    try:
        try:
            get_api_key_context(
                authorization="Bearer nvr_live_inexistente_xyz",
                db=db,
            )
            raise AssertionError("Debería haber fallado")
        except HTTPException as e:
            assert e.status_code == 401
        print("  ✅ 401")
    finally:
        db.close()


def test_get_context_revoked_key():
    print("\n" + "=" * 70)
    print("TEST 12: get_api_key_context — key revocada → 401")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        obj, full = create_api_key(db, u.id, b.id, "revoked")

        revoke_api_key(db, obj.id, u.id)

        try:
            get_api_key_context(authorization=f"Bearer {full}", db=db)
            raise AssertionError("Debería haber fallado")
        except HTTPException as e:
            assert e.status_code == 401
        print("  ✅ 401")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_get_context_expired_key():
    print("\n" + "=" * 70)
    print("TEST 13: get_api_key_context — key expirada → 401")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        obj, full = create_api_key(db, u.id, b.id, "expired")

        obj.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        db.commit()

        try:
            get_api_key_context(authorization=f"Bearer {full}", db=db)
            raise AssertionError("Debería haber fallado")
        except HTTPException as e:
            assert e.status_code == 401
        print("  ✅ 401")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_get_context_bot_deleted():
    print("\n" + "=" * 70)
    print("TEST 14: get_api_key_context — bot borrado → 404")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        obj, full = create_api_key(db, u.id, b.id, "deleted")

        # Borrar bot (CASCADE borra la key también, pero forzamos manual)
        # En realidad, si el bot se borra, la key también por CASCADE.
        # Aquí simulamos un estado inconsistente borrando solo el bot.
        # (No pasa en producción porque CASCADE funciona, pero testeamos el path)
        bot_id = b.id
        db.delete(b)
        db.commit()

        # La key también se ha borrado por CASCADE → 401 (no 404)
        # Este test verifica que no explota
        status_code = None
        try:
            get_api_key_context(authorization=f"Bearer {full}", db=db)
            raise AssertionError("Debería haber fallado")
        except HTTPException as exc:
            status_code = exc.status_code
            assert status_code in (401, 404)
        print(f"  ✅ {status_code} (CASCADE borra key)")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.10.5 (api_auth)")
    print("=" * 70)

    tests = [
        # extract_bearer_token
        test_extract_valid,
        test_extract_case_insensitive,
        test_extract_extra_spaces,
        test_extract_missing_header,
        test_extract_empty_header,
        test_extract_no_bearer,
        test_extract_empty_token,
        test_extract_too_many_parts,
        # get_api_key_context
        test_get_context_ok,
        test_get_context_missing_header,
        test_get_context_invalid_key,
        test_get_context_revoked_key,
        test_get_context_expired_key,
        test_get_context_bot_deleted,
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
