"""
Migración de producción 14.3.1 — PostgreSQL no destructiva
============================================================
Añade las tablas `sources` y `source_chunks`.

- NO borra datos
- NO recrea tablas existentes
- Idempotente (se puede ejecutar varias veces)
- Aborta si detecta SQLite

Ejecución (Render Pre-Deploy Command):
    python migrations/migrate_prod_14_3.py
"""

import sys
import os
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.config import SessionLocal, engine


# ============================================================
# SCHEMA — Crear tablas sources y source_chunks
# ============================================================

def phase_create_tables(db):
    print("\n🔧 FASE ÚNICA — Creando tablas sources y source_chunks...")

    statements = [
        # --- sources ---
        """
        CREATE TABLE IF NOT EXISTS sources (
            id SERIAL PRIMARY KEY,
            bot_id INTEGER NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            type VARCHAR(20) NOT NULL,
            title VARCHAR(200) NOT NULL,
            origin TEXT,
            content_raw TEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            error_message TEXT,
            chunks_count INTEGER NOT NULL DEFAULT 0,
            size_bytes INTEGER,
            meta TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            processed_at TIMESTAMP WITH TIME ZONE
        )
        """,

        # --- source_chunks ---
        """
        CREATE TABLE IF NOT EXISTS source_chunks (
            id SERIAL PRIMARY KEY,
            source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
            bot_id INTEGER NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            section VARCHAR(200),
            page INTEGER,
            char_start INTEGER,
            char_end INTEGER,
            tokens_estimate INTEGER,
            meta TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
        """,

        # --- Índices de sources ---
        "CREATE INDEX IF NOT EXISTS idx_sources_bot_id ON sources(bot_id)",
        "CREATE INDEX IF NOT EXISTS idx_sources_user_id ON sources(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_sources_status ON sources(status)",

        # --- Índices de source_chunks ---
        "CREATE INDEX IF NOT EXISTS idx_chunks_source_id ON source_chunks(source_id)",
        "CREATE INDEX IF NOT EXISTS idx_chunks_bot_id ON source_chunks(bot_id)",
        """
        CREATE INDEX IF NOT EXISTS idx_chunks_source_chunk 
        ON source_chunks(source_id, chunk_index)
        """,
    ]

    for stmt in statements:
        try:
            db.execute(text(stmt))
        except Exception as e:
            print(f"   ⚠️  Error en: {stmt[:70]}...")
            print(f"       {e}")
            raise

    db.commit()
    print(f"   ✅ {len(statements)} sentencias aplicadas")


# ============================================================
# VERIFICACIÓN POST-MIGRACIÓN
# ============================================================

def verify(db):
    print("\n🔍 Verificando tablas creadas...")

    tables = db.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
          AND table_name IN ('sources', 'source_chunks')
        ORDER BY table_name
    """)).fetchall()

    table_names = [t.table_name for t in tables]
    if 'source_chunks' in table_names and 'sources' in table_names:
        print("   ✅ Tablas 'sources' y 'source_chunks' existen")
    else:
        print(f"   🛑 ERROR: Faltan tablas. Encontradas: {table_names}")
        raise Exception("Tablas no creadas correctamente")


# ============================================================
# MIGRACIÓN COMPLETA
# ============================================================

def migrate():
    print("=" * 70)
    print("🚀 Migración de producción 14.3.1 — PostgreSQL")
    print("=" * 70)

    # Detección de motor — ABORTAR si es SQLite
    db_url = str(engine.url)
    if db_url.startswith("sqlite"):
        print("\n🛑 ABORTANDO: Motor detectado = SQLite")
        print("   Esta migración está diseñada EXCLUSIVAMENTE para PostgreSQL.")
        print("   En local, usa: python init_db.py")
        print("=" * 70)
        sys.exit(0)

    print(f"✅ Motor detectado: PostgreSQL")

    db = SessionLocal()
    try:
        phase_create_tables(db)
        verify(db)

        print("\n" + "=" * 70)
        print("🎉 Migración 14.3.1 completada correctamente")
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
