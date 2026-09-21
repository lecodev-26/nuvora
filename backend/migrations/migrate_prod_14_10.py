"""
Nuvora — Migración 14.10 (Fase 14.10.2 — Nuvora API)
======================================================
Crea la tabla `api_keys` si no existe.

Idempotente: se puede ejecutar múltiples veces sin efectos secundarios.

Uso:
    python migrations/migrate_prod_14_10.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from app.database.config import engine


def table_exists(table_name: str) -> bool:
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def index_exists(index_name: str) -> bool:
    is_sqlite = engine.url.drivername.startswith("sqlite")
    with engine.connect() as conn:
        if is_sqlite:
            r = conn.execute(text(
                f"SELECT name FROM sqlite_master WHERE type='index' AND name='{index_name}'"
            )).fetchone()
        else:
            r = conn.execute(text(
                f"SELECT indexname FROM pg_indexes WHERE indexname='{index_name}'"
            )).fetchone()
        return r is not None


def run_migration():
    print("=" * 70)
    print("🚀 Migración 14.10 — Nuvora API (api_keys)")
    print("=" * 70)

    from app.models.db_models import ApiKey  # noqa: F401

    # ---------- 1. Tabla api_keys ----------
    print("\n📦 Paso 1: Tabla `api_keys`")

    if table_exists("api_keys"):
        print("  ℹ️  Tabla 'api_keys' ya existe")
    else:
        ApiKey.__table__.create(engine, checkfirst=True)
        print("  ✅ Tabla 'api_keys' creada")

    # ---------- 2. Verificación ----------
    print("\n📦 Paso 2: Verificación")

    if not table_exists("api_keys"):
        print("  ❌ api_keys NO existe")
        sys.exit(1)

    inspector = inspect(engine)
    cols = [c["name"] for c in inspector.get_columns("api_keys")]
    expected = {
        "id", "user_id", "bot_id", "name", "key_prefix", "key_hash",
        "created_at", "last_used_at", "revoked_at", "expires_at", "is_active",
    }
    missing = expected - set(cols)
    if missing:
        print(f"  ❌ Faltan columnas: {missing}")
        sys.exit(1)

    print(f"  ✅ api_keys: {cols}")

    # Índices
    indexes = inspector.get_indexes("api_keys")
    index_names = [i["name"] for i in indexes]
    print(f"  ✅ Índices: {index_names}")

    print("\n" + "=" * 70)
    print("✅ Migración 14.10 completada correctamente")
    print("=" * 70)


if __name__ == "__main__":
    run_migration()
