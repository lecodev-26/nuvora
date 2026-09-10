"""
Tests de integridad — Subfase 14.3.1
Verifica que las tablas sources y source_chunks existen y se comportan bien.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database.config import SessionLocal, engine, Base
from app.models.db_models import (
    Bot, User, Source, SourceChunk
)


def setup_test_data():
    """Crea un usuario y bot para pruebas."""
    db = SessionLocal()
    try:
        # Usuario
        user = db.query(User).filter(User.email == "test_integrity@nuvora.com").first()
        if not user:
            from app.services.auth import get_password_hash
            user = User(
                email="test_integrity@nuvora.com",
                hashed_password=get_password_hash("123456"),
                full_name="Test Integrity",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Bot
        bot = db.query(Bot).filter(Bot.name == "Bot Integrity Test").first()
        if not bot:
            bot = Bot(
                user_id=user.id,
                name="Bot Integrity Test",
                business_name="Test Business",
                nicho_id="desde_cero",
                is_active=True,
                is_published=False,
                answer_mode="strict",
            )
            db.add(bot)
            db.commit()
            db.refresh(bot)

        return user.id, bot.id
    finally:
        db.close()


def test_source_creation():
    """Test 1: Crear una Source."""
    print("\n" + "=" * 70)
    print("TEST 1: Crear una Source")
    print("=" * 70)

    user_id, bot_id = setup_test_data()
    db = SessionLocal()
    try:
        source = Source(
            bot_id=bot_id,
            user_id=user_id,
            type="text",
            title="Test Source",
            content_raw="Contenido de prueba",
            status="pending",
            chunks_count=0,
        )
        db.add(source)
        db.commit()
        db.refresh(source)

        assert source.id is not None
        assert source.status == "pending"
        assert source.chunks_count == 0
        print(f"✅ Source creada: id={source.id}, title='{source.title}'")
        return source.id
    finally:
        db.close()


def test_source_chunk_creation(source_id):
    """Test 2: Crear un SourceChunk."""
    print("\n" + "=" * 70)
    print("TEST 2: Crear un SourceChunk")
    print("=" * 70)

    db = SessionLocal()
    try:
        source = db.query(Source).filter(Source.id == source_id).first()
        chunk = SourceChunk(
            source_id=source.id,
            bot_id=source.bot_id,
            chunk_index=0,
            content="Contenido del chunk de prueba",
            section="Test Section",
            tokens_estimate=10,
        )
        db.add(chunk)
        db.commit()
        db.refresh(chunk)

        assert chunk.id is not None
        assert chunk.source_id == source_id
        assert chunk.chunk_index == 0
        print(f"✅ Chunk creado: id={chunk.id}, source_id={chunk.source_id}")
    finally:
        db.close()


def test_cascade_delete(source_id):
    """Test 3: Eliminar Source debe eliminar sus chunks (CASCADE)."""
    print("\n" + "=" * 70)
    print("TEST 3: Verificar CASCADE al eliminar Source")
    print("=" * 70)

    db = SessionLocal()
    try:
        # Contar chunks antes
        chunks_before = db.query(SourceChunk).filter(
            SourceChunk.source_id == source_id
        ).count()
        print(f"   Chunks antes: {chunks_before}")

        # Eliminar source
        source = db.query(Source).filter(Source.id == source_id).first()
        db.delete(source)
        db.commit()

        # Contar chunks después
        chunks_after = db.query(SourceChunk).filter(
            SourceChunk.source_id == source_id
        ).count()
        print(f"   Chunks después: {chunks_after}")

        assert chunks_after == 0, "CASCADE no funcionó"
        print(f"✅ CASCADE funciona correctamente")
    finally:
        db.close()


def test_status_values():
    """Test 4: Verificar que se pueden usar todos los estados."""
    print("\n" + "=" * 70)
    print("TEST 4: Verificar estados válidos")
    print("=" * 70)

    user_id, bot_id = setup_test_data()
    db = SessionLocal()
    try:
        valid_statuses = ["pending", "processing", "ready", "failed"]
        for status in valid_statuses:
            source = Source(
                bot_id=bot_id,
                user_id=user_id,
                type="text",
                title=f"Test {status}",
                status=status,
                chunks_count=0,
            )
            db.add(source)
            db.commit()
            db.refresh(source)
            assert source.status == status
            print(f"   ✅ Estado '{status}' guardado correctamente")
            db.delete(source)
            db.commit()

        print(f"✅ Todos los estados funcionan")
    finally:
        db.close()


def test_indexes():
    """Test 5: Verificar que los índices existen."""
    print("\n" + "=" * 70)
    print("TEST 5: Verificar índices")
    print("=" * 70)

    db = SessionLocal()
    try:
        db_url = str(engine.url)
        if db_url.startswith("sqlite"):
            # SQLite: consultar sqlite_master (con text())
            result = db.execute(text(
                "SELECT name FROM sqlite_master "
                "WHERE type='index' AND tbl_name IN ('sources', 'source_chunks')"
            )).fetchall()
            index_names = [r[0] for r in result if r[0] is not None]
        else:
            # PostgreSQL
            result = db.execute(text(
                "SELECT indexname FROM pg_indexes "
                "WHERE tablename IN ('sources', 'source_chunks')"
            )).fetchall()
            index_names = [r[0] for r in result]

        print(f"   Índices encontrados: {len(index_names)}")
        for name in index_names:
            print(f"      - {name}")

        # Verificar que existen los índices clave (buscar por substrings)
        expected_substrings = ["sources_bot_id", "chunks_source_id"]
        for sub in expected_substrings:
            found = any(sub in name for name in index_names)
            assert found, f"Índice que contiene '{sub}' no encontrado"
            print(f"   ✅ Índice con '{sub}' existe")

        print(f"✅ Índices verificados")
    finally:
        db.close()


def cleanup():
    """Limpieza final."""
    print("\n" + "=" * 70)
    print("LIMPIANDO DATOS DE TEST")
    print("=" * 70)

    db = SessionLocal()
    try:
        # Eliminar sources de test
        db.query(Source).filter(Source.title.like("Test %")).delete(
            synchronize_session=False
        )
        db.query(Source).filter(Source.title == "Test Source").delete(
            synchronize_session=False
        )
        # Eliminar bot de test
        db.query(Bot).filter(Bot.name == "Bot Integrity Test").delete(
            synchronize_session=False
        )
        db.commit()
        print("✅ Datos de test eliminados")
    finally:
        db.close()


def main():
    print("=" * 70)
    print("🧪 TESTS DE INTEGRIDAD — SUBFASE 14.3.1")
    print("=" * 70)

    try:
        # Test 1
        source_id = test_source_creation()

        # Test 2
        test_source_chunk_creation(source_id)

        # Test 3 (elimina la source del test 1)
        test_cascade_delete(source_id)

        # Test 4
        test_status_values()

        # Test 5
        test_indexes()

        # Cleanup
        cleanup()

        print("\n" + "=" * 70)
        print("🎉 TODOS LOS TESTS PASARON")
        print("=" * 70)

    except AssertionError as e:
        print(f"\n🛑 TEST FALLIDO: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n🛑 ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
