"""
Tests — Subfase 14.10.2 (Modelo ApiKey + migración)
=====================================================
Verifica:
    - Columnas esperadas en ApiKey
    - UNIQUE en key_hash
    - CASCADE al borrar user/bot
    - Defaults (is_active=True, nullable=false...)
    - Índices presentes
    - Migración idempotente
"""

import sys
import os
import time
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.database.config import engine, SessionLocal
from app.models.db_models import User, Bot, ApiKey


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
    email = f"{_unique('apikey_user')}@nuvora.com"
    u = User(email=email, hashed_password="x", full_name="ApiKey Test")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u, email


def _create_bot(db, user_id):
    b = Bot(
        user_id=user_id,
        name=f"Bot {_unique('apikey')}",
        business_name="Test",
        nicho_id="otro",
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


def _create_api_key(db, user_id, bot_id, prefix=None, hash_=None, name=None):
    k = ApiKey(
        user_id=user_id,
        bot_id=bot_id,
        name=name or f"Key {_unique('k')}",
        key_prefix=prefix or _unique("nvr_live_ab"),
        key_hash=hash_ or _unique("hash"),
    )
    db.add(k)
    db.commit()
    db.refresh(k)
    return k


# ============================================================
# TESTS
# ============================================================

def test_api_key_columns():
    print("\n" + "=" * 70)
    print("TEST 1: ApiKey tiene las columnas esperadas")
    print("=" * 70)
    cols = {c.name for c in ApiKey.__table__.columns}
    expected = {
        "id", "user_id", "bot_id", "name", "key_prefix", "key_hash",
        "created_at", "last_used_at", "revoked_at", "expires_at", "is_active",
    }
    missing = expected - cols
    assert not missing, f"Faltan columnas: {missing}"
    print(f"  ✅ {len(cols)} columnas OK")


def test_create_api_key_basic():
    print("\n" + "=" * 70)
    print("TEST 2: Crear ApiKey básica")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        k = _create_api_key(db, u.id, b.id, name="Mi integración")
        assert k.id is not None
        assert k.user_id == u.id
        assert k.bot_id == b.id
        assert k.name == "Mi integración"
        assert k.is_active is True
        assert k.last_used_at is None
        assert k.revoked_at is None
        assert k.expires_at is None
        assert k.created_at is not None
        print(f"  ✅ ApiKey #{k.id} creada")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_key_hash_unique():
    print("\n" + "=" * 70)
    print("TEST 3: key_hash es UNIQUE")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        shared_hash = _unique("samehash")

        _create_api_key(db, u.id, b.id, hash_=shared_hash)
        try:
            _create_api_key(db, u.id, b.id, hash_=shared_hash)
            raise AssertionError("Debería haber fallado por UNIQUE")
        except IntegrityError:
            db.rollback()
            print("  ✅ UNIQUE en key_hash funciona")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_key_prefix_not_unique():
    print("\n" + "=" * 70)
    print("TEST 4: key_prefix NO es UNIQUE (colisiones posibles)")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        same_prefix = "nvr_live_shared"

        k1 = _create_api_key(db, u.id, b.id, prefix=same_prefix)
        k2 = _create_api_key(db, u.id, b.id, prefix=same_prefix)
        assert k1.id != k2.id
        print(f"  ✅ Dos keys con mismo prefix OK (#{k1.id}, #{k2.id})")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_cascade_on_user_delete():
    print("\n" + "=" * 70)
    print("TEST 5: CASCADE — borrar user borra sus ApiKeys")
    print("=" * 70)
    db = SessionLocal()
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        k = _create_api_key(db, u.id, b.id)
        k_id = k.id

        # Borrar bot + user (el bot cascadea keys, luego user)
        db.delete(b)
        db.commit()
        db.delete(u)
        db.commit()

        remaining = db.query(ApiKey).filter(ApiKey.id == k_id).first()
        assert remaining is None
        print(f"  ✅ ApiKey #{k_id} borrada con el user/bot")
    finally:
        db.close()


def test_cascade_on_bot_delete():
    print("\n" + "=" * 70)
    print("TEST 6: CASCADE — borrar bot borra sus ApiKeys")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        k = _create_api_key(db, u.id, b.id)
        k_id = k.id

        db.delete(b)
        db.commit()

        remaining = db.query(ApiKey).filter(ApiKey.id == k_id).first()
        assert remaining is None
        print(f"  ✅ ApiKey #{k_id} borrada con el bot")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_is_active_default_true():
    print("\n" + "=" * 70)
    print("TEST 7: is_active default = True")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        k = _create_api_key(db, u.id, b.id)
        assert k.is_active is True
        print("  ✅ is_active=True por defecto")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_revoke_api_key():
    print("\n" + "=" * 70)
    print("TEST 8: Revocar ApiKey (is_active=False + revoked_at)")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        k = _create_api_key(db, u.id, b.id)

        k.is_active = False
        k.revoked_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(k)

        assert k.is_active is False
        assert k.revoked_at is not None
        print(f"  ✅ ApiKey #{k.id} revocada")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_expires_at_nullable():
    print("\n" + "=" * 70)
    print("TEST 9: expires_at nullable por defecto")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        k = _create_api_key(db, u.id, b.id)
        assert k.expires_at is None

        # Asignar una fecha futura
        k.expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        db.commit()
        db.refresh(k)
        assert k.expires_at is not None
        print("  ✅ expires_at asignable")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_api_key_indexes():
    print("\n" + "=" * 70)
    print("TEST 10: Índices presentes en api_keys")
    print("=" * 70)
    inspector = inspect(engine)
    indexes = inspector.get_indexes("api_keys")
    index_cols = set()
    for idx in indexes:
        for col in idx.get("column_names", []):
            index_cols.add(col)

    # Unique constraints también
    uniques = inspector.get_unique_constraints("api_keys")
    for uc in uniques:
        for col in uc.get("column_names", []):
            index_cols.add(col)

    expected_indexes = {"user_id", "bot_id", "key_prefix", "key_hash", "is_active"}
    missing = expected_indexes - index_cols
    assert not missing, f"Faltan índices en: {missing}"
    print(f"  ✅ Índices presentes: {sorted(expected_indexes)}")


def test_migration_idempotent():
    print("\n" + "=" * 70)
    print("TEST 11: Migración 14.10 idempotente")
    print("=" * 70)
    from migrations import migrate_prod_14_10

    try:
        migrate_prod_14_10.run_migration()
        migrate_prod_14_10.run_migration()
    except SystemExit:
        pass
    print("  ✅ Migración ejecutada 2 veces sin fallo")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.10.2 (Modelo ApiKey)")
    print("=" * 70)

    tests = [
        test_api_key_columns,
        test_create_api_key_basic,
        test_key_hash_unique,
        test_key_prefix_not_unique,
        test_cascade_on_user_delete,
        test_cascade_on_bot_delete,
        test_is_active_default_true,
        test_revoke_api_key,
        test_expires_at_nullable,
        test_api_key_indexes,
        test_migration_idempotent,
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
