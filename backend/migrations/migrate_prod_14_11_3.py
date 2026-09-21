"""
Nuvora - Migracion 14.11.3 (Fase 14.11 - Telegram Channel)
============================================================
Añade las columnas `channel` y `external_id` a la tabla
`public_sessions`.

CONTEXTO:
    - public_sessions pasa a ser multicanal (widget/api/telegram).
    - channel: canal de la sesión, default "widget".
    - external_id: identificador externo (ej: chat_id Telegram),
                   NULL para widget/api.

COMPATIBILIDAD:
    - Columnas añadidas con valores por defecto no destructivos.
    - Filas existentes → channel = "widget", external_id = NULL.
    - El código actual sigue funcionando sin cambios.

Idempotente: se puede ejecutar multiples veces sin efectos secundarios.

Uso:
    python migrations/migrate_prod_14_11_3.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from app.database.config import engine


def column_exists(table_name: str, column_name: str) -> bool:
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return False
    cols = [c["name"] for c in inspector.get_columns(table_name)]
    return column_name in cols


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
    print("Migracion 14.11.3 - public_sessions multicanal")
    print("=" * 70)

    inspector = inspect(engine)
    if "public_sessions" not in inspector.get_table_names():
        print("\nERROR: tabla public_sessions no existe.")
        print("Ejecuta primero las migraciones anteriores (14.9).")
        sys.exit(1)

    # ---------- Paso 1: columna channel ----------
    print("\nPaso 1: Columna `channel`")

    if column_exists("public_sessions", "channel"):
        print("  Columna 'channel' ya existe")
    else:
        with engine.begin() as conn:
            conn.execute(text(
                "ALTER TABLE public_sessions "
                "ADD COLUMN channel VARCHAR(20) NOT NULL DEFAULT 'widget'"
            ))
        print("  Columna 'channel' añadida (default 'widget')")

    # ---------- Paso 2: columna external_id ----------
    print("\nPaso 2: Columna `external_id`")

    if column_exists("public_sessions", "external_id"):
        print("  Columna 'external_id' ya existe")
    else:
        with engine.begin() as conn:
            conn.execute(text(
                "ALTER TABLE public_sessions "
                "ADD COLUMN external_id VARCHAR(100) NULL"
            ))
        print("  Columna 'external_id' añadida (nullable)")

    # ---------- Paso 3: indices ----------
    print("\nPaso 3: Indices")

    if index_exists("ix_public_sessions_channel"):
        print("  Indice 'ix_public_sessions_channel' ya existe")
    else:
        with engine.begin() as conn:
            conn.execute(text(
                "CREATE INDEX ix_public_sessions_channel "
                "ON public_sessions (channel)"
            ))
        print("  Indice 'ix_public_sessions_channel' creado")

    if index_exists("ix_public_sessions_external_id"):
        print("  Indice 'ix_public_sessions_external_id' ya existe")
    else:
        with engine.begin() as conn:
            conn.execute(text(
                "CREATE INDEX ix_public_sessions_external_id "
                "ON public_sessions (external_id)"
            ))
        print("  Indice 'ix_public_sessions_external_id' creado")

    # ---------- Paso 4: verificacion ----------
    print("\nPaso 4: Verificacion")

    inspector = inspect(engine)
    cols = [c["name"] for c in inspector.get_columns("public_sessions")]

    if "channel" not in cols:
        print("  ERROR: 'channel' NO existe")
        sys.exit(1)
    if "external_id" not in cols:
        print("  ERROR: 'external_id' NO existe")
        sys.exit(1)

    print(f"  Columnas actuales: {cols}")

    idx = [i["name"] for i in inspector.get_indexes("public_sessions")]
    print(f"  Indices actuales: {idx}")

    print("\n" + "=" * 70)
    print("Migracion 14.11.3 completada correctamente")
    print("=" * 70)


if __name__ == "__main__":
    run_migration()
