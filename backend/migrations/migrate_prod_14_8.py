"""
Nuvora — Migración 14.8 (Fase 14.8.6 — Bot Tester)
=====================================================
Crea la tabla workflow_tests si no existe.

Idempotente: se puede ejecutar múltiples veces sin efectos secundarios.

Uso:
    python migrations/migrate_prod_14_8.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect
from app.database.config import engine


def table_exists(table_name: str) -> bool:
    """Comprueba si una tabla existe."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def run_migration():
    print("=" * 70)
    print("🚀 Migración 14.8 — workflow_tests (Bot Tester)")
    print("=" * 70)

    # Importar el modelo para asegurar que está registrado en Base
    from app.models.db_models import WorkflowTest  # noqa

    # 1. Comprobar si ya existe
    if table_exists("workflow_tests"):
        print("ℹ️  La tabla 'workflow_tests' ya existe. Nada que hacer.")
        return

    # 2. Crear la tabla
    print("📦 Creando tabla 'workflow_tests'...")
    WorkflowTest.__table__.create(engine, checkfirst=True)
    print("✅ Tabla 'workflow_tests' creada")

    # 3. Verificar
    if table_exists("workflow_tests"):
        inspector = inspect(engine)
        columns = inspector.get_columns("workflow_tests")
        print(f"✅ Verificación OK — columnas: {[c['name'] for c in columns]}")
    else:
        print("❌ ERROR: la tabla no existe después de crearla")
        sys.exit(1)

    print("=" * 70)
    print("✅ Migración 14.8 completada correctamente")
    print("=" * 70)


if __name__ == "__main__":
    run_migration()
