"""
Pre-Deploy Script para Render
================================
Se ejecuta ANTES del deploy de la API.

Responsabilidades:
1. Crear todas las tablas en PostgreSQL (si no existen)
2. Ejecutar la migración de datos 14.1.1 (idempotente)
3. NO borra datos
4. Es idempotente (se puede ejecutar varias veces)

Uso:
    python pre_deploy.py

Se configura como Pre-Deploy Command en Render.
"""

import sys
import os

# Asegurar que el path incluye la raíz del backend
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.config import engine, Base
from app.models.db_models import Bot, Memory, User, Conversation, MemoryCategory


def create_tables():
    """Crea todas las tablas si no existen. Idempotente."""
    print("=" * 70)
    print("🔧 PASO 1: Creando tablas si no existen...")
    print("=" * 70)

    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas verificadas/creadas correctamente")
    except Exception as e:
        print(f"🛑 ERROR creando tablas: {e}")
        raise


def run_migration():
    """Ejecuta la migración de datos 14.1.1. Idempotente."""
    print("\n" + "=" * 70)
    print("📦 PASO 2: Ejecutando migración 14.1.1...")
    print("=" * 70)

    try:
        # Importar dinámicamente la migración
        from migrations.migrate_prod_14_1_1 import migrate
        migrate()
    except Exception as e:
        print(f"\n⚠️  Migración omitida o fallida: {e}")
        print("   (No es crítico si la BD está vacía o ya migrada)")
        # No fallamos el deploy si la migración no es necesaria


def main():
    print("\n" + "=" * 70)
    print("🚀 PRE-DEPLOY NUVORA")
    print("=" * 70)

    # Detectar motor de BD
    db_url = str(engine.url)
    if db_url.startswith("sqlite"):
        print("⚠️  Motor detectado: SQLite (entorno local)")
    else:
        print("✅ Motor detectado: PostgreSQL (entorno de producción)")

    # 1. Crear tablas
    create_tables()

    # 2. Ejecutar migración de datos
    run_migration()

    print("\n" + "=" * 70)
    print("🎉 PRE-DEPLOY COMPLETADO")
    print("=" * 70)


if __name__ == "__main__":
    main()
