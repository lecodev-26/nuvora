"""
Nuvora — Migración 14.7 (Fase 14.7.4b — BYOK)
================================================
Crea la tabla user_ai_configs si no existe.

Idempotente: se puede ejecutar múltiples veces sin efectos secundarios.

Uso:
    python migrations/migrate_prod_14_7.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from app.database.config import engine, Base


def table_exists(table_name: str) -> bool:
    """Comprueba si una tabla existe."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def run_migration():
    print("=" * 70)
    print("🚀 Migración 14.7 — user_ai_configs (BYOK)")
    print("=" * 70)

    # Importar los modelos para asegurar que están registrados en Base
    from app.models.db_models import UserAIConfig  # noqa

    # 1. Comprobar si ya existe
    if table_exists("user_ai_configs"):
        print("ℹ️  La tabla 'user_ai_configs' ya existe. Nada que hacer.")
        return

    # 2. Crear la tabla
    print("📦 Creando tabla 'user_ai_configs'...")
    UserAIConfig.__table__.create(engine, checkfirst=True)
    print("✅ Tabla 'user_ai_configs' creada")

    # 3. Verificar
    if table_exists("user_ai_configs"):
        inspector = inspect(engine)
        columns = inspector.get_columns("user_ai_configs")
        print(f"✅ Verificación OK — columnas: {[c['name'] for c in columns]}")
    else:
        print("❌ ERROR: la tabla no existe después de crearla")
        sys.exit(1)

    print("=" * 70)
    print("✅ Migración 14.7 completada correctamente")
    print("=" * 70)


if __name__ == "__main__":
    run_migration()
