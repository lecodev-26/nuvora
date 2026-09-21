"""
Nuvora - Migracion 14.11 (Fase 14.11.2 - Telegram Channel)
============================================================
Crea las tablas `telegram_integrations` y `telegram_updates` si no
existen.

Idempotente: se puede ejecutar multiples veces sin efectos secundarios.

Uso:
    python migrations/migrate_prod_14_11.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from app.database.config import engine


def table_exists(table_name: str) -> bool:
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def run_migration():
    print("=" * 70)
    print("Migracion 14.11 - Telegram Channel")
    print("=" * 70)

    from app.models.db_models import TelegramIntegration, TelegramUpdate  # noqa: F401

    # ---------- 1. Tabla telegram_integrations ----------
    print("\nPaso 1: Tabla `telegram_integrations`")

    if table_exists("telegram_integrations"):
        print("  Tabla 'telegram_integrations' ya existe")
    else:
        TelegramIntegration.__table__.create(engine, checkfirst=True)
        print("  Tabla 'telegram_integrations' creada")

    # ---------- 2. Tabla telegram_updates ----------
    print("\nPaso 2: Tabla `telegram_updates`")

    if table_exists("telegram_updates"):
        print("  Tabla 'telegram_updates' ya existe")
    else:
        TelegramUpdate.__table__.create(engine, checkfirst=True)
        print("  Tabla 'telegram_updates' creada")

    # ---------- 3. Verificacion ----------
    print("\nPaso 3: Verificacion")

    if not table_exists("telegram_integrations"):
        print("  ERROR: telegram_integrations NO existe")
        sys.exit(1)
    if not table_exists("telegram_updates"):
        print("  ERROR: telegram_updates NO existe")
        sys.exit(1)

    inspector = inspect(engine)

    cols_int = [c["name"] for c in inspector.get_columns("telegram_integrations")]
    expected_int = {
        "id", "bot_id", "telegram_bot_id", "telegram_username",
        "encrypted_token", "webhook_secret", "webhook_url",
        "status", "is_active", "created_at", "updated_at",
        "last_event_at", "last_error",
    }
    missing_int = expected_int - set(cols_int)
    if missing_int:
        print(f"  ERROR: faltan columnas en telegram_integrations: {missing_int}")
        sys.exit(1)
    print(f"  telegram_integrations: {cols_int}")

    cols_upd = [c["name"] for c in inspector.get_columns("telegram_updates")]
    expected_upd = {"id", "integration_id", "update_id", "created_at"}
    missing_upd = expected_upd - set(cols_upd)
    if missing_upd:
        print(f"  ERROR: faltan columnas en telegram_updates: {missing_upd}")
        sys.exit(1)
    print(f"  telegram_updates: {cols_upd}")

    # Indices y constraints
    idx_int = [i["name"] for i in inspector.get_indexes("telegram_integrations")]
    print(f"  Indices telegram_integrations: {idx_int}")

    idx_upd = [i["name"] for i in inspector.get_indexes("telegram_updates")]
    print(f"  Indices telegram_updates: {idx_upd}")

    print("\n" + "=" * 70)
    print("Migracion 14.11 completada correctamente")
    print("=" * 70)


if __name__ == "__main__":
    run_migration()
