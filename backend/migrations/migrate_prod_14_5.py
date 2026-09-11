"""
Migración de producción 14.5 — PostgreSQL no destructiva
==========================================================
Crea las tablas:
    - workflows
    - workflow_nodes
    - workflow_transitions

- NO borra datos
- Idempotente
- Solo PostgreSQL (aborta si detecta SQLite)
"""

import sys
import os
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.config import SessionLocal, engine


def phase_create_tables(db):
    print("\n🔧 Creando tablas workflows, workflow_nodes, workflow_transitions...")

    statements = [
        # --- workflows ---
        """
        CREATE TABLE IF NOT EXISTS workflows (
            id SERIAL PRIMARY KEY,
            bot_id INTEGER NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            status VARCHAR(20) DEFAULT 'draft',
            version INTEGER DEFAULT 1,
            trigger VARCHAR(50) DEFAULT 'manual',
            entry_node_id VARCHAR(50),
            meta TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
        """,

        # --- workflow_nodes ---
        """
        CREATE TABLE IF NOT EXISTS workflow_nodes (
            id SERIAL PRIMARY KEY,
            workflow_id INTEGER NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
            node_id VARCHAR(50) NOT NULL,
            type VARCHAR(30) NOT NULL,
            name VARCHAR(200),
            config TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            CONSTRAINT uq_workflow_node UNIQUE (workflow_id, node_id)
        )
        """,

        # --- workflow_transitions ---
        """
        CREATE TABLE IF NOT EXISTS workflow_transitions (
            id SERIAL PRIMARY KEY,
            workflow_id INTEGER NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
            from_node_id VARCHAR(50) NOT NULL,
            to_node_id VARCHAR(50) NOT NULL,
            condition TEXT,
            label VARCHAR(50),
            "order" INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
        """,

        # --- Índices ---
        "CREATE INDEX IF NOT EXISTS idx_workflows_bot_id ON workflows(bot_id)",
        "CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status)",
        "CREATE INDEX IF NOT EXISTS idx_workflow_nodes_workflow_id ON workflow_nodes(workflow_id)",
        "CREATE INDEX IF NOT EXISTS idx_workflow_nodes_node_id ON workflow_nodes(node_id)",
        "CREATE INDEX IF NOT EXISTS idx_workflow_transitions_workflow_id ON workflow_transitions(workflow_id)",
        "CREATE INDEX IF NOT EXISTS idx_workflow_transitions_from_node_id ON workflow_transitions(from_node_id)",
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


def verify(db):
    print("\n🔍 Verificando tablas...")
    tables = db.execute(text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name IN ('workflows', 'workflow_nodes', 'workflow_transitions')
        ORDER BY table_name
    """)).fetchall()
    names = [t.table_name for t in tables]

    expected = {'workflow_nodes', 'workflow_transitions', 'workflows'}
    if set(names) == expected:
        print(f"   ✅ Tablas verificadas: {names}")
    else:
        raise Exception(f"Tablas incorrectas. Esperadas: {expected}. Encontradas: {names}")


def migrate():
    print("=" * 70)
    print("🚀 Migración 14.5 — PostgreSQL")
    print("=" * 70)

    db_url = str(engine.url)
    if db_url.startswith("sqlite"):
        print("\n🛑 ABORTANDO: SQLite detectado. Migración solo para PostgreSQL.")
        print("   En local, usa: python init_db.py")
        sys.exit(0)

    print("✅ Motor: PostgreSQL")
    db = SessionLocal()
    try:
        phase_create_tables(db)
        verify(db)
        print("\n" + "=" * 70)
        print("🎉 Migración 14.5 completada correctamente")
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
