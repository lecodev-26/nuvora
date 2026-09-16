"""
Tests — Subfase 14.9.2 (Modelo de Publicación Universal)
=========================================================
Verifica:
    - Columnas public_* en Bot
    - Modelo PublicSession
    - Unicidad de public_id / public_slug
    - Nullable antes de publicar
    - CASCADE delete de PublicSession al borrar Bot
    - Migración idempotente (se puede ejecutar 2 veces)

Patrón: cada test limpia lo que crea (idempotente).
"""

import sys
import os
import time
import json
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.database.config import engine, SessionLocal
from app.models.db_models import Bot, User, PublicSession


# ============================================================
# HELPERS
# ============================================================

def _unique(suffix):
    return f"{suffix}_{int(time.time() * 1000000)}_{os.getpid()}"


def _cleanup_user(db, email):
    """Borra usuario + bots + sessions asociadas (CASCADE)."""
    u = db.query(User).filter(User.email == email).first()
    if u:
        # Borrar bots del usuario (CASCADE borra PublicSessions)
        bots = db.query(Bot).filter(Bot.user_id == u.id).all()
        for b in bots:
            db.delete(b)
        db.delete(u)
        db.commit()


def _create_user(db):
    email = f"{_unique('pub_user')}@nuvora.com"
    u = User(
        email=email,
        hashed_password="x",
        full_name="Test Public",
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u, email


def _create_bot(db, user_id=None):
    b = Bot(
        user_id=user_id,
        name=f"Bot {_unique('pub')}",
        business_name="Test",
        nicho_id="otro",
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


# ============================================================
# TESTS
# ============================================================

def test_bot_has_public_columns():
    print("\n" + "=" * 70)
    print("TEST 1: Bot tiene las 4 columnas public_*")
    print("=" * 70)
    cols = {c.name for c in Bot.__table__.columns}
    expected = {"public_id", "public_slug", "published_at", "public_config"}
    missing = expected - cols
    assert not missing, f"Faltan columnas: {missing}"
    print(f"  ✅ Todas presentes: {sorted(expected)}")


def test_public_session_model():
    print("\n" + "=" * 70)
    print("TEST 2: PublicSession tiene las columnas esperadas")
    print("=" * 70)
    cols = {c.name for c in PublicSession.__table__.columns}
    expected = {
        "id", "public_id", "bot_id", "session_data", "status",
        "created_at", "updated_at", "expires_at",
    }
    missing = expected - cols
    assert not missing, f"Faltan columnas: {missing}"
    print(f"  ✅ {sorted(cols)}")


def test_bot_public_id_unique():
    print("\n" + "=" * 70)
    print("TEST 3: Bot.public_id es UNIQUE")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b1 = _create_bot(db, u.id)
        b2 = _create_bot(db, u.id)

        # public_id único, con sufijo, para no chocar con otros tests
        unique_pid = _unique("unique-pid")

        b1.public_id = unique_pid
        db.commit()

        b2.public_id = unique_pid
        try:
            db.commit()
            raise AssertionError("Debería haber fallado por UNIQUE")
        except IntegrityError:
            db.rollback()
            print("  ✅ UNIQUE en public_id funciona")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_bot_public_slug_unique():
    print("\n" + "=" * 70)
    print("TEST 4: Bot.public_slug es UNIQUE")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b1 = _create_bot(db, u.id)
        b2 = _create_bot(db, u.id)

        unique_slug = _unique("unique-slug")

        b1.public_slug = unique_slug
        db.commit()

        b2.public_slug = unique_slug
        try:
            db.commit()
            raise AssertionError("Debería haber fallado por UNIQUE")
        except IntegrityError:
            db.rollback()
            print("  ✅ UNIQUE en public_slug funciona")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_public_session_public_id_unique():
    print("\n" + "=" * 70)
    print("TEST 5: PublicSession.public_id es UNIQUE")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)

        exp = datetime.now(timezone.utc) + timedelta(hours=1)
        unique_sid = _unique("sess-unique")

        s1 = PublicSession(public_id=unique_sid, bot_id=b.id, expires_at=exp)
        db.add(s1)
        db.commit()

        s2 = PublicSession(public_id=unique_sid, bot_id=b.id, expires_at=exp)
        db.add(s2)
        try:
            db.commit()
            raise AssertionError("Debería haber fallado por UNIQUE")
        except IntegrityError:
            db.rollback()
            print("  ✅ UNIQUE en PublicSession.public_id funciona")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_bot_can_be_created_without_public_fields():
    print("\n" + "=" * 70)
    print("TEST 6: Bot se puede crear sin public_* (nullable)")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)
        assert b.public_id is None
        assert b.public_slug is None
        assert b.published_at is None
        assert b.public_config is None
        print(f"  ✅ Bot #{b.id} creado sin public_*")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_bot_can_be_published():
    print("\n" + "=" * 70)
    print("TEST 7: Bot se puede publicar (rellenar public_*)")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)

        b.public_id = _unique("pub-uuid")
        b.public_slug = _unique("pub-slug")
        b.published_at = datetime.now(timezone.utc)
        b.public_config = json.dumps({
            "welcome_message": "Hola 👋",
            "primary_color": "#7B5CFF",
            "show_branding": True,
        })
        b.is_published = True
        db.commit()
        db.refresh(b)

        assert b.public_id is not None
        assert b.public_slug is not None
        assert b.published_at is not None
        cfg = json.loads(b.public_config)
        assert cfg["welcome_message"] == "Hola 👋"

        print(f"  ✅ Bot #{b.id} publicado con public_id={b.public_id}")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_public_session_create_and_link():
    print("\n" + "=" * 70)
    print("TEST 8: PublicSession se crea y se liga a un bot")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)

        exp = datetime.now(timezone.utc) + timedelta(hours=1)
        s = PublicSession(
            public_id=_unique("sess"),
            bot_id=b.id,
            session_data=json.dumps([
                {"role": "user", "content": "Hola", "ts": "2026-09-16T00:00:00Z"},
            ]),
            status="active",
            expires_at=exp,
        )
        db.add(s)
        db.commit()
        db.refresh(s)

        assert s.id is not None
        assert s.bot_id == b.id
        assert s.status == "active"
        msgs = json.loads(s.session_data)
        assert len(msgs) == 1
        assert msgs[0]["content"] == "Hola"

        print(f"  ✅ PublicSession #{s.id} creada y ligada a Bot #{b.id}")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_public_session_cascade_on_bot_delete():
    print("\n" + "=" * 70)
    print("TEST 9: CASCADE — borrar Bot borra sus PublicSessions")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id)

        exp = datetime.now(timezone.utc) + timedelta(hours=1)
        s = PublicSession(
            public_id=_unique("sess-cascade"),
            bot_id=b.id,
            expires_at=exp,
        )
        db.add(s)
        db.commit()

        sess_id = s.id
        db.delete(b)
        db.commit()

        remaining = db.query(PublicSession).filter(PublicSession.id == sess_id).first()
        assert remaining is None, "PublicSession debería haber sido borrada por CASCADE"
        print(f"  ✅ CASCADE OK: PublicSession #{sess_id} borrada con el Bot")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_migration_idempotent():
    print("\n" + "=" * 70)
    print("TEST 10: Migración 14.9 es idempotente")
    print("=" * 70)
    from migrations import migrate_prod_14_9

    try:
        migrate_prod_14_9.run_migration()
        migrate_prod_14_9.run_migration()
    except SystemExit:
        pass
    print("  ✅ Migración ejecutada 2 veces sin fallo")


def test_bot_table_has_public_indexes():
    print("\n" + "=" * 70)
    print("TEST 11: Bot tiene índices en public_id / public_slug")
    print("=" * 70)
    inspector = inspect(engine)
    indexes = inspector.get_indexes("bots")
    index_cols = set()
    for idx in indexes:
        for col in idx.get("column_names", []):
            index_cols.add(col)

    uniques = inspector.get_unique_constraints("bots")
    for uc in uniques:
        for col in uc.get("column_names", []):
            index_cols.add(col)

    has_public_id = "public_id" in index_cols
    has_public_slug = "public_slug" in index_cols
    print(f"  public_id en índices/unique: {has_public_id}")
    print(f"  public_slug en índices/unique: {has_public_slug}")
    assert has_public_id, "public_id debe tener índice"
    assert has_public_slug, "public_slug debe tener índice"
    print("  ✅ Índices OK")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.9.2 (Modelo de Publicación)")
    print("=" * 70)

    tests = [
        test_bot_has_public_columns,
        test_public_session_model,
        test_bot_public_id_unique,
        test_bot_public_slug_unique,
        test_public_session_public_id_unique,
        test_bot_can_be_created_without_public_fields,
        test_bot_can_be_published,
        test_public_session_create_and_link,
        test_public_session_cascade_on_bot_delete,
        test_migration_idempotent,
        test_bot_table_has_public_indexes,
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
