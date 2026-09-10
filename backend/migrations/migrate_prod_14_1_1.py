"""
Migración de producción 14.1.1 — PostgreSQL no destructiva
============================================================
Ejecutar SOLO en Render (PostgreSQL).

- NO borra datos
- NO recrea tablas
- Añade columnas con IF NOT EXISTS
- Migra datos en transacción
- Idempotente (se puede ejecutar varias veces)
- Aborta si hay errores críticos
- Aborta si detecta SQLite (solo PostgreSQL)

Ejecución (Render Pre-Deploy Command):
    python migrations/migrate_prod_14_1_1.py
"""

import sys
import os
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.config import SessionLocal, engine


# ============================================================
# FASE A — SCHEMA (idempotente, no reversible pero seguro)
# ============================================================

def phase_a_schema(db):
    print("\n🔧 FASE A — Añadiendo columnas, tablas e índices...")

    statements = [
        # --- bots ---
        "ALTER TABLE bots ADD COLUMN IF NOT EXISTS user_id INTEGER",
        "ALTER TABLE bots ADD COLUMN IF NOT EXISTS description TEXT",
        "ALTER TABLE bots ADD COLUMN IF NOT EXISTS business_name VARCHAR(200)",
        "ALTER TABLE bots ADD COLUMN IF NOT EXISTS business_type VARCHAR(50)",
        "ALTER TABLE bots ADD COLUMN IF NOT EXISTS goal TEXT",
        "ALTER TABLE bots ADD COLUMN IF NOT EXISTS instructions TEXT",
        "ALTER TABLE bots ADD COLUMN IF NOT EXISTS personality VARCHAR(100)",
        "ALTER TABLE bots ADD COLUMN IF NOT EXISTS tone VARCHAR(100)",
        "ALTER TABLE bots ADD COLUMN IF NOT EXISTS greeting TEXT",
        "ALTER TABLE bots ADD COLUMN IF NOT EXISTS fallback_message TEXT",
        "ALTER TABLE bots ADD COLUMN IF NOT EXISTS answer_mode VARCHAR(20) DEFAULT 'strict'",
        "ALTER TABLE bots ADD COLUMN IF NOT EXISTS is_published BOOLEAN DEFAULT FALSE",
        "ALTER TABLE bots ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE",
        "ALTER TABLE bots ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()",

        # --- memories ---
        "ALTER TABLE memories ADD COLUMN IF NOT EXISTS category_id INTEGER",
        "ALTER TABLE memories ADD COLUMN IF NOT EXISTS source VARCHAR(20) DEFAULT 'manual'",
        "ALTER TABLE memories ADD COLUMN IF NOT EXISTS is_confirmed BOOLEAN DEFAULT TRUE",

        # --- conversations ---
        "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS channel VARCHAR(30) DEFAULT 'widget'",
        "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS workflow_id INTEGER",
        "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS meta TEXT",

        # --- memory_categories (tabla nueva) ---
        """
        CREATE TABLE IF NOT EXISTS memory_categories (
            id SERIAL PRIMARY KEY,
            bot_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            icon VARCHAR(10),
            "order" INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,

        # --- Índices ---
        "CREATE INDEX IF NOT EXISTS idx_bots_user_id ON bots(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_memories_category_id ON memories(category_id)",
        "CREATE INDEX IF NOT EXISTS idx_conversations_channel ON conversations(channel)",
        "CREATE INDEX IF NOT EXISTS idx_categories_bot_id ON memory_categories(bot_id)",
    ]

    for stmt in statements:
        try:
            db.execute(text(stmt))
        except Exception as e:
            print(f"   ⚠️  Error en: {stmt[:70]}...")
            print(f"       {e}")
            raise

    db.commit()
    print(f"   ✅ FASE A completada ({len(statements)} sentencias aplicadas)")


# ============================================================
# FASE B — DATA (reversible, todo en una transacción)
# ============================================================

def phase_b_data(db):
    print("\n📦 FASE B — Migrando datos...")

    try:
        # 1. Migrar user_id desde owner_email (solo si user_id es NULL)
        print("   📌 Migrando owner_email → user_id...")
        result = db.execute(text("""
            UPDATE bots 
            SET user_id = (
                SELECT u.id 
                FROM users u 
                WHERE LOWER(TRIM(u.email)) = LOWER(TRIM(bots.owner_email))
                LIMIT 1
            )
            WHERE user_id IS NULL 
              AND owner_email IS NOT NULL 
              AND owner_email != ''
              AND EXISTS (
                  SELECT 1 FROM users u 
                  WHERE LOWER(TRIM(u.email)) = LOWER(TRIM(bots.owner_email))
              )
        """))
        print(f"      ✅ {result.rowcount} bots actualizados con user_id")

        # 2. Migrar business_name desde restaurant_name (solo si NULL)
        print("   📌 Migrando restaurant_name → business_name...")
        result = db.execute(text("""
            UPDATE bots 
            SET business_name = restaurant_name 
            WHERE business_name IS NULL 
              AND restaurant_name IS NOT NULL 
              AND restaurant_name != ''
        """))
        print(f"      ✅ {result.rowcount} bots actualizados con business_name")

        # 3. Rellenar defaults en bots
        print("   📌 Rellenando defaults en bots...")

        r = db.execute(text("UPDATE bots SET answer_mode = 'strict' WHERE answer_mode IS NULL OR answer_mode = ''"))
        print(f"      ✅ answer_mode: {r.rowcount}")

        r = db.execute(text("UPDATE bots SET is_active = TRUE WHERE is_active IS NULL"))
        print(f"      ✅ is_active: {r.rowcount}")

        r = db.execute(text("UPDATE bots SET is_published = FALSE WHERE is_published IS NULL"))
        print(f"      ✅ is_published: {r.rowcount}")

        r = db.execute(text("UPDATE bots SET updated_at = created_at WHERE updated_at IS NULL"))
        print(f"      ✅ updated_at: {r.rowcount}")

        # 4. Rellenar defaults en memories
        print("   📌 Rellenando defaults en memories...")

        r = db.execute(text("UPDATE memories SET is_confirmed = TRUE WHERE is_confirmed IS NULL"))
        print(f"      ✅ is_confirmed: {r.rowcount}")

        r = db.execute(text("UPDATE memories SET source = 'manual' WHERE source IS NULL OR source = ''"))
        print(f"      ✅ source: {r.rowcount}")

        # 5. Rellenar defaults en conversations
        print("   📌 Rellenando defaults en conversations...")

        r = db.execute(text("UPDATE conversations SET channel = 'widget' WHERE channel IS NULL OR channel = ''"))
        print(f"      ✅ channel: {r.rowcount}")

        # Commit atómico de toda la Fase B
        db.commit()
        print("   ✅ FASE B completada (commit exitoso)")

    except Exception as e:
        db.rollback()
        print(f"   🛑 ERROR en FASE B: {e}")
        print(f"   🔄 Rollback ejecutado. Los datos NO se modificaron.")
        raise


# ============================================================
# MIGRACIÓN COMPLETA
# ============================================================

def migrate():
    print("=" * 70)
    print("🚀 Migración de producción 14.1.1 — PostgreSQL")
    print("=" * 70)

    # ------------------------------------------------------------
    # Detección de motor — ABORTAR si es SQLite
    # ------------------------------------------------------------
    db_url = str(engine.url)
    if db_url.startswith("sqlite"):
        print("\n🛑 ABORTANDO: Motor detectado = SQLite")
        print("   Esta migración está diseñada EXCLUSIVAMENTE para PostgreSQL.")
        print("   No se ejecutará en SQLite (producción usa PostgreSQL en Render).")
        print("   Si necesitas migrar en local, borra nuvora.db y ejecuta init_db.py.")
        print("=" * 70)
        sys.exit(0)

    print(f"✅ Motor detectado: PostgreSQL")

    db = SessionLocal()
    try:
        phase_a_schema(db)
        phase_b_data(db)

        print("\n" + "=" * 70)
        print("🎉 Migración completada correctamente")
        print("=" * 70)
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"🛑 MIGRACIÓN FALLIDA: {e}")
        print("=" * 70)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
