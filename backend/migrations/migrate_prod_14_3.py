"""
Migración de producción 14.3 — PostgreSQL no destructiva
==========================================================
Crea las tablas `sources` y `source_chunks`.
Idempotente. Solo PostgreSQL.
"""

import sys
import os
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.config import SessionLocal, engine


def phase_create_tables(db):
    print("\n🔧 Creando tablas sources y source_chunks...")

    statements = [
        """
        CREATE TABLE IF NOT EXISTS sources (
            id SERIAL PRIMARY KEY,
            bot_id INTEGER NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            type VARCHAR(20) NOT NULL,
            title VARCHAR(200) NOT NULL,
            origin TEXT,
            content_raw TEXT,
            content_processed TEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            error_message TEXT,
            chunks_count INTEGER NOT NULL DEFAULT 0,
            size_bytes INTEGER,
            meta TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            processed_at TIMESTAMP WITH TIME ZONE
        )
        """,
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
        "CREATE INDEX IF NOT EXISTS idx_sources_bot_id ON sources(bot_id)",
        "CREATE INDEX IF NOT EXISTS idx_sources_user_id ON sources(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_sources_status ON sources(status)",
        "CREATE INDEX IF NOT EXISTS idx_chunks_source_id ON source_chunks(source_id)",
        "CREATE INDEX IF NOT EXISTS idx_chunks_bot_id ON source_chunks(bot_id)",
        "CREATE INDEX IF NOT EXISTS idx_chunks_source_chunk ON source_chunks(source_id, chunk_index)",
    ]

    for stmt in statements:
        try:
            db.execute(text(stmt))
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
            raise

    # Añadir content_processed si no existe (por si la tabla ya existía)
    try:
        db.execute(text("ALTER TABLE sources ADD COLUMN IF NOT EXISTS content_processed TEXT"))
    except Exception as e:
        print(f"   ⚠️  ALTER TABLE falló (probablemente ya existe): {e}")

    db.commit()
    print(f"   ✅ {len(statements)} sentencias aplicadas")


def verify(db):
    print("\n🔍 Verificando tablas...")
    tables = db.execute(text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
          AND table_name IN ('sources', 'source_chunks')
    """)).fetchall()
    names = [t.table_name for t in tables]
    if 'sources' in names and 'source_chunks' in names:
        print("   ✅ Tablas verificadas")
    else:
        raise Exception(f"Faltan tablas: {names}")


def migrate():
    print("=" * 70)
    print("🚀 Migración 14.3 — PostgreSQL")
    print("=" * 70)

    db_url = str(engine.url)
    if db_url.startswith("sqlite"):
        print("\n🛑 ABORTANDO: SQLite detectado. Esta migración es solo PostgreSQL.")
        sys.exit(0)

    print("✅ Motor: PostgreSQL")
    db = SessionLocal()
    try:
        phase_create_tables(db)
        verify(db)
        print("\n🎉 Migración 14.3 completada")
    except Exception as e:
        print(f"\n🛑 MIGRACIÓN FALLIDA: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
