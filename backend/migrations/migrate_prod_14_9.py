"""
Nuvora — Migración 14.9 (Fase 14.9.2 — Publicación Universal)
==============================================================
1. Añade columnas public_* a `bots` (idempotente).
2. Crea índices UNIQUE en public_id / public_slug (compatible SQLite + PostgreSQL).
3. Crea la tabla `public_sessions` si no existe.
4. Crea índice UNIQUE en `public_sessions.public_id`.

IMPORTANTE:
    - En SQLite, `ALTER TABLE ADD COLUMN` NO aplica los UNIQUE / index=True
      del modelo Python. Por eso creamos los índices explícitamente.
    - Si ya existen duplicados en public_id/public_slug (por datos viejos),
      la migración lo detecta, avisa, y NO explota (mantiene el arranque).
    - Idempotente: se puede ejecutar múltiples veces.

Uso:
    python migrations/migrate_prod_14_9.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from app.database.config import engine


def table_exists(table_name: str) -> bool:
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def column_exists(table_name: str, column_name: str) -> bool:
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return False
    return column_name in [c["name"] for c in inspector.get_columns(table_name)]


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


def count_duplicates(table: str, column: str) -> int:
    """Cuenta valores duplicados no-null en (table, column)."""
    try:
        with engine.connect() as conn:
            r = conn.execute(text(
                f"SELECT COUNT(*) FROM ("
                f"  SELECT {column} FROM {table} "
                f"  WHERE {column} IS NOT NULL "
                f"  GROUP BY {column} HAVING COUNT(*) > 1"
                f")"
            )).fetchone()
            return r[0] if r else 0
    except Exception:
        return -1  # tabla/columna no existe


def create_unique_index(index_name: str, table: str, column: str) -> bool:
    """
    Crea un índice UNIQUE. Devuelve True si lo creó o ya existía.
    Si hay duplicados, avisa y devuelve False (no explota).
    """
    if index_exists(index_name):
        print(f"  ℹ️  Índice '{index_name}' ya existe")
        return True

    dup_count = count_duplicates(table, column)
    if dup_count > 0:
        print(f"  ⚠️  Índice '{index_name}' NO creado: "
              f"{dup_count} valor(es) duplicado(s) en {table}.{column}")
        return False
    if dup_count < 0:
        print(f"  ⚠️  Índice '{index_name}' NO creado: tabla/columna no existe")
        return False

    is_sqlite = engine.url.drivername.startswith("sqlite")
    with engine.begin() as conn:
        if is_sqlite:
            conn.execute(text(
                f"CREATE UNIQUE INDEX IF NOT EXISTS {index_name} "
                f"ON {table} ({column})"
            ))
        else:
            conn.execute(text(
                f"CREATE UNIQUE INDEX IF NOT EXISTS {index_name} "
                f"ON {table} ({column}) WHERE {column} IS NOT NULL"
            ))
    print(f"  ✅ Índice '{index_name}' creado")
    return True


def run_migration():
    print("=" * 70)
    print("🚀 Migración 14.9 — Publicación Universal")
    print("=" * 70)

    from app.models.db_models import Bot, PublicSession  # noqa: F401

    # ---------- 1. Columnas nuevas en `bots` ----------
    print("\n📦 Paso 1: Columnas public_* en `bots`")

    new_columns = [
        ("public_id", "VARCHAR(36)"),
        ("public_slug", "VARCHAR(100)"),
        ("published_at", "TIMESTAMP"),
        ("public_config", "TEXT"),
    ]

    for col_name, col_type in new_columns:
        if column_exists("bots", col_name):
            print(f"  ℹ️  Columna 'bots.{col_name}' ya existe")
            continue
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE bots ADD COLUMN {col_name} {col_type}"))
        print(f"  ✅ Columna 'bots.{col_name}' creada")

    # ---------- 2. Índices UNIQUE en bots ----------
    print("\n📦 Paso 2: Índices UNIQUE en `bots`")
    ok_id = create_unique_index("ix_bots_public_id", "bots", "public_id")
    ok_slug = create_unique_index("ix_bots_public_slug", "bots", "public_slug")

    # ---------- 3. Tabla public_sessions ----------
    print("\n📦 Paso 3: Tabla `public_sessions`")
    if table_exists("public_sessions"):
        print("  ℹ️  Tabla 'public_sessions' ya existe")
    else:
        PublicSession.__table__.create(engine, checkfirst=True)
        print("  ✅ Tabla 'public_sessions' creada")

    # ---------- 4. Índices UNIQUE en public_sessions ----------
    print("\n📦 Paso 4: Índices UNIQUE en `public_sessions`")
    ok_sess = create_unique_index("ix_public_sessions_public_id", "public_sessions", "public_id")

    # ---------- 5. Verificación ----------
    print("\n📦 Paso 5: Verificación")
    inspector = inspect(engine)
    bot_cols = [c["name"] for c in inspector.get_columns("bots")]
    for col_name, _ in new_columns:
        if col_name in bot_cols:
            print(f"  ✅ bots.{col_name}")
        else:
            print(f"  ❌ bots.{col_name} FALTA")
            sys.exit(1)

    if table_exists("public_sessions"):
        print(f"  ✅ public_sessions OK")
    else:
        print("  ❌ public_sessions NO existe")
        sys.exit(1)

    # Los índices pueden faltar legítimamente si había duplicados
    if ok_id and ok_slug and ok_sess:
        print("  ✅ Todos los índices UNIQUE creados")
    else:
        print("  ⚠️  Algunos índices NO se crearon (había duplicados). Revisa logs.")

    print("\n" + "=" * 70)
    print("✅ Migración 14.9 completada")
    print("=" * 70)


if __name__ == "__main__":
    run_migration()
