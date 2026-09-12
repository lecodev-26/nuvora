"""
Pre-Deploy Script para Render
================================
Ejecuta ANTES de arrancar la API en Render.

Responsabilidades:
    1. Crear todas las tablas en PostgreSQL (si no existen)
    2. Ejecutar migración 14.1.1 (Core Universal)
    3. Ejecutar migración 14.3 (Knowledge Engine 2.0)
    4. Ejecutar migración 14.5 (Workflow Engine)
    5. Ejecutar migración 14.7 (BYOK - user_ai_configs)
    6. NO borra datos. Idempotente.
    7. NUNCA falla el arranque si las tablas base están OK.
"""

import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.config import engine, Base
from app.models.db_models import (
    Bot, Memory, User, Conversation, MemoryCategory,
    Source, SourceChunk,
    Workflow, WorkflowNode, WorkflowTransition,
    UserAIConfig,
)


def create_tables() -> bool:
    """Crea todas las tablas si no existen. Idempotente."""
    print("\n" + "=" * 70)
    print("🔧 PASO 1: Creando tablas si no existen...")
    print("=" * 70)
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas verificadas/creadas correctamente")
        return True
    except Exception as e:
        print(f"🛑 ERROR CRÍTICO creando tablas: {e}")
        traceback.print_exc()
        return False


def run_migration_14_1_1():
    print("\n" + "=" * 70)
    print("📦 PASO 2: Migración 14.1.1 (Core Universal)...")
    print("=" * 70)
    try:
        from migrations import migrate_prod_14_1_1
        migrate_prod_14_1_1.migrate()
        print("✅ Migración 14.1.1 completada")
    except SystemExit:
        print("⚠️  Migración 14.1.1 omitida (SQLite o ya migrada)")
    except Exception as e:
        print(f"⚠️  Migración 14.1.1 falló: {e}")
        print("   (La API arrancará igualmente)")


def run_migration_14_3():
    print("\n" + "=" * 70)
    print("📦 PASO 3: Migración 14.3 (Knowledge Engine 2.0)...")
    print("=" * 70)
    try:
        from migrations import migrate_prod_14_3
        migrate_prod_14_3.migrate()
        print("✅ Migración 14.3 completada")
    except SystemExit:
        print("⚠️  Migración 14.3 omitida (SQLite o ya migrada)")
    except Exception as e:
        print(f"⚠️  Migración 14.3 falló: {e}")
        print("   (La API arrancará igualmente)")


def run_migration_14_5():
    print("\n" + "=" * 70)
    print("📦 PASO 4: Migración 14.5 (Workflow Engine)...")
    print("=" * 70)
    try:
        from migrations import migrate_prod_14_5
        migrate_prod_14_5.migrate()
        print("✅ Migración 14.5 completada")
    except SystemExit:
        print("⚠️  Migración 14.5 omitida (SQLite o ya migrada)")
    except Exception as e:
        print(f"⚠️  Migración 14.5 falló: {e}")
        print("   (La API arrancará igualmente)")


def run_migration_14_7():
    print("\n" + "=" * 70)
    print("📦 PASO 5: Migración 14.7 (BYOK - user_ai_configs)...")
    print("=" * 70)
    try:
        from migrations import migrate_prod_14_7
        migrate_prod_14_7.run_migration()
        print("✅ Migración 14.7 completada")
    except SystemExit:
        print("⚠️  Migración 14.7 omitida (SQLite o ya migrada)")
    except Exception as e:
        print(f"⚠️  Migración 14.7 falló: {e}")
        print("   (La API arrancará igualmente)")


def main():
    print("\n" + "=" * 70)
    print("🚀 PRE-DEPLOY NUVORA")
    print("=" * 70)

    db_url = str(engine.url)
    if db_url.startswith("sqlite"):
        print("⚠️  Motor detectado: SQLite (entorno local)")
    else:
        safe_url = db_url.split("@")[-1] if "@" in db_url else "postgresql"
        print(f"✅ Motor detectado: PostgreSQL ({safe_url})")

    if not create_tables():
        print("\n🛑 ABORTANDO: No se pudieron crear las tablas.")
        sys.exit(1)

    run_migration_14_1_1()
    run_migration_14_3()
    run_migration_14_5()
    run_migration_14_7()

    print("\n" + "=" * 70)
    print("🎉 PRE-DEPLOY COMPLETADO")
    print("=" * 70)


if __name__ == "__main__":
    main()
