"""
Pre-Deploy Script para Render
================================
Se ejecuta ANTES de arrancar la API en Render.

Responsabilidades:
1. Crear todas las tablas en PostgreSQL (si no existen)
2. Ejecutar la migración 14.1.1 (Core Universal)
3. Ejecutar la migración 14.3 (Knowledge Engine 2.0)
4. NO borra datos
5. Es idempotente (se puede ejecutar varias veces)
6. NUNCA falla el arranque si las tablas base están OK

Uso:
    python pre_deploy.py

Configurado como parte del Start Command en Render:
    python pre_deploy.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT
"""

import sys
import os
import traceback

# Asegurar que el path incluye la raíz del backend
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.config import engine, Base
from app.models.db_models import (
    Bot, Memory, User, Conversation, MemoryCategory,
    Source, SourceChunk,
)


# ============================================================
# PASO 1 — CREAR TABLAS
# ============================================================

def create_tables() -> bool:
    """Crea todas las tablas si no existen. Idempotente. Devuelve True si OK."""
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


# ============================================================
# PASO 2 — MIGRACIÓN 14.1.1
# ============================================================

def run_migration_14_1_1():
    """Ejecuta la migración 14.1.1. NO crítico si falla."""
    print("\n" + "=" * 70)
    print("📦 PASO 2: Ejecutando migración 14.1.1 (Core Universal)...")
    print("=" * 70)

    try:
        from migrations import migrate_prod_14_1_1
        migrate_prod_14_1_1.migrate()
        print("✅ Migración 14.1.1 completada")
        return True

    except SystemExit:
        print("⚠️  Migración 14.1.1 omitida (SQLite detectado o ya migrada)")
        return True

    except Exception as e:
        print(f"⚠️  Migración 14.1.1 falló: {e}")
        print("   (La API arrancará de todas formas)")
        return False


# ============================================================
# PASO 3 — MIGRACIÓN 14.3
# ============================================================

def run_migration_14_3():
    """Ejecuta la migración 14.3 (Knowledge Engine 2.0). NO crítico si falla."""
    print("\n" + "=" * 70)
    print("📦 PASO 3: Ejecutando migración 14.3 (Knowledge Engine 2.0)...")
    print("=" * 70)

    try:
        from migrations import migrate_prod_14_3
        migrate_prod_14_3.migrate()
        print("✅ Migración 14.3 completada")
        return True

    except SystemExit:
        print("⚠️  Migración 14.3 omitida (SQLite detectado o ya migrada)")
        return True

    except Exception as e:
        print(f"⚠️  Migración 14.3 falló: {e}")
        print("   (La API arrancará de todas formas)")
        return False


# ============================================================
# MAIN
# ============================================================

def main():
    print("\n" + "=" * 70)
    print("🚀 PRE-DEPLOY NUVORA")
    print("=" * 70)

    # Detectar motor de BD
    db_url = str(engine.url)
    if db_url.startswith("sqlite"):
        print("⚠️  Motor detectado: SQLite (entorno local)")
    else:
        safe_url = db_url.split("@")[-1] if "@" in db_url else "postgresql"
        print(f"✅ Motor detectado: PostgreSQL ({safe_url})")

    # 1. Crear tablas (CRÍTICO — si esto falla, no arrancamos)
    tables_ok = create_tables()
    if not tables_ok:
        print("\n🛑 ABORTANDO: No se pudieron crear las tablas.")
        print("   El arranque de la API fallará para que se pueda diagnosticar.")
        sys.exit(1)

    # 2. Migración 14.1.1 (NO crítico)
    run_migration_14_1_1()

    # 3. Migración 14.3 (NO crítico)
    run_migration_14_3()

    print("\n" + "=" * 70)
    print("🎉 PRE-DEPLOY COMPLETADO")
    print("=" * 70)


if __name__ == "__main__":
    main()
