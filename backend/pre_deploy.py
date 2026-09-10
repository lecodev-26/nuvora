"""
Pre-Deploy Script para Render
================================
Se ejecuta ANTES de arrancar la API en Render.

Responsabilidades:
1. Crear todas las tablas en PostgreSQL (si no existen)
2. Ejecutar la migración de datos 14.1.1 (idempotente)
3. NO borra datos
4. Es idempotente (se puede ejecutar varias veces)
5. NUNCA falla el arranque si las tablas están bien (aunque la migración tenga problemas)

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
from app.models.db_models import Bot, Memory, User, Conversation, MemoryCategory


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


def run_migration():
    """
    Ejecuta la migración de datos 14.1.1. NO crítico si falla.
    La migración se salta sola si detecta SQLite.
    """
    print("\n" + "=" * 70)
    print("📦 PASO 2: Ejecutando migración 14.1.1...")
    print("=" * 70)

    try:
        # Importar el módulo de migración
        from migrations import migrate_prod_14_1_1

        # Ejecutar la migración
        migrate_prod_14_1_1.migrate()
        print("✅ Migración completada")

    except SystemExit:
        # La migración llama a sys.exit(0) en SQLite — lo ignoramos
        print("⚠️  Migración omitida (SQLite detectado o ya migrada)")

    except Exception as e:
        # Cualquier otro error: NO bloqueamos el arranque
        print(f"⚠️  Migración falló pero no bloquea el arranque: {e}")
        print("   (La API arrancará de todas formas)")
        # NO re-lanzamos la excepción


def main():
    print("\n" + "=" * 70)
    print("🚀 PRE-DEPLOY NUVORA")
    print("=" * 70)

    # Detectar motor de BD
    db_url = str(engine.url)
    if db_url.startswith("sqlite"):
        print("⚠️  Motor detectado: SQLite (entorno local)")
    else:
        # Ocultar credenciales en el log
        safe_url = db_url.split("@")[-1] if "@" in db_url else "postgresql"
        print(f"✅ Motor detectado: PostgreSQL ({safe_url})")

    # 1. Crear tablas (CRÍTICO — si esto falla, no arrancamos)
    tables_ok = create_tables()
    if not tables_ok:
        print("\n🛑 ABORTANDO: No se pudieron crear las tablas.")
        print("   El arranque de la API fallará para que se pueda diagnosticar.")
        sys.exit(1)

    # 2. Ejecutar migración de datos (NO crítico)
    run_migration()

    print("\n" + "=" * 70)
    print("🎉 PRE-DEPLOY COMPLETADO")
    print("=" * 70)


if __name__ == "__main__":
    main()
