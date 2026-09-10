"""
Tests — Subfase 14.4.2
Verifica el esqueleto del Training Analyzer.

NOTA ARQUITECTÓNICA (nicho_id):
    - "restaurantes" → plantilla de restaurantes
    - "otro"         → plantilla genérica "Otro negocio"
    - None           → "Desde cero" (concepto definitivo, aún NO implementado)

    Actualmente Bot.nicho_id tiene default="otro", así que un bot creado
    sin especificar nicho acaba almacenando "otro". En una fase futura se
    revisará el modelo para permitir nicho_id=None en bots "desde cero".

    TODO (futuro): retirar default="otro" del modelo Bot y permitir None.
    NO modificar en 14.4.2.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.config import SessionLocal
from app.models.db_models import (
    Bot, User, Memory, Source, SourceChunk, Conversation,
)
from app.core.training import TrainingAnalyzer
from app.core.bot_loader import BotNotFoundError
from app.models.training import (
    TrainingReport,
    TopicCoverageStatus,
)


# ============================================================
# HELPERS
# ============================================================

def setup_test_user_bot(suffix: str, nicho_id: str = "restaurantes") -> tuple[int, int]:
    db = SessionLocal()
    try:
        from app.services.auth import get_password_hash

        email = f"test_analyzer_{suffix}@nuvora.com"
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                hashed_password=get_password_hash("123456"),
                full_name=f"Test Analyzer {suffix}",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        bot_name = f"Bot Analyzer {suffix}"
        bot = db.query(Bot).filter(Bot.name == bot_name).first()
        if not bot:
            bot = Bot(
                user_id=user.id,
                name=bot_name,
                business_name=f"Test {suffix}",
                nicho_id=nicho_id,
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


def add_memory(bot_id: int, fact: str, keyword: str):
    db = SessionLocal()
    try:
        m = Memory(
            bot_id=bot_id,
            fact=fact,
            keyword=keyword.lower(),
            source="manual",
            is_confirmed=True,
        )
        db.add(m)
        db.commit()
    finally:
        db.close()


def add_source(bot_id: int, user_id: int, title: str, status: str = "ready"):
    db = SessionLocal()
    try:
        s = Source(
            bot_id=bot_id,
            user_id=user_id,
            type="text",
            title=title,
            content_raw="Contenido de prueba",
            content_processed="Contenido de prueba",
            status=status,
            chunks_count=1,
        )
        db.add(s)
        db.commit()
        db.refresh(s)
        if status == "ready":
            c = SourceChunk(
                source_id=s.id,
                bot_id=bot_id,
                chunk_index=0,
                content="Contenido de prueba",
            )
            db.add(c)
            db.commit()
    finally:
        db.close()


def cleanup_bot(bot_id: int):
    db = SessionLocal()
    try:
        db.query(Conversation).filter(Conversation.bot_id == bot_id).delete(synchronize_session=False)
        db.query(Memory).filter(Memory.bot_id == bot_id).delete(synchronize_session=False)
        db.query(SourceChunk).filter(SourceChunk.bot_id == bot_id).delete(synchronize_session=False)
        db.query(Source).filter(Source.bot_id == bot_id).delete(synchronize_session=False)
        db.query(Bot).filter(Bot.id == bot_id).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


# ============================================================
# TESTS
# ============================================================

def test_analyzer_bot_not_found():
    print("\n" + "=" * 70)
    print("TEST 1: Bot inexistente → BotNotFoundError")
    print("=" * 70)
    db = SessionLocal()
    try:
        analyzer = TrainingAnalyzer(db)
        try:
            analyzer.analyze(999999)
            assert False, "Debería haber lanzado BotNotFoundError"
        except BotNotFoundError as e:
            print(f"✅ BotNotFoundError: {e}")
    finally:
        db.close()


def test_analyzer_empty_bot():
    print("\n" + "=" * 70)
    print("TEST 2: Bot vacío → reporte válido con progress=0")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("empty")
    try:
        db = SessionLocal()
        analyzer = TrainingAnalyzer(db)
        report = analyzer.analyze(bot_id)

        assert isinstance(report, TrainingReport)
        assert report.bot_id == bot_id
        assert report.bot_name == "Bot Analyzer empty"
        assert report.progress == 0.0
        assert report.total_topics > 0
        assert report.has_memories is False
        assert report.has_sources is False
        assert report.memories_count == 0
        assert report.ready_sources_count == 0
        assert report.conversations_analyzed == 0
        print(f"✅ Reporte válido: topics={report.total_topics}, progress={report.progress}")
        db.close()
    finally:
        cleanup_bot(bot_id)


def test_analyzer_returns_all_fields():
    print("\n" + "=" * 70)
    print("TEST 3: Reporte tiene todos los campos")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("fields")
    try:
        db = SessionLocal()
        analyzer = TrainingAnalyzer(db)
        report = analyzer.analyze(bot_id)

        required_attrs = [
            "bot_id", "bot_name", "nicho_id",
            "progress", "total_topics", "covered_count",
            "partial_count", "missing_count",
            "topics", "missing_topics", "partial_topics",
            "unanswered_questions", "recommendations",
            "analyzed_at", "has_memories", "has_sources",
            "memories_count", "ready_sources_count", "conversations_analyzed",
        ]
        for attr in required_attrs:
            assert hasattr(report, attr), f"Falta campo: {attr}"

        print(f"✅ Todos los campos presentes")
        db.close()
    finally:
        cleanup_bot(bot_id)


def test_analyzer_nicho_fallback_unknown():
    print("\n" + "=" * 70)
    print("TEST 4: Nicho desconocido → usa catálogo 'otro'")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("unknown", nicho_id="inexistente")
    try:
        db = SessionLocal()
        analyzer = TrainingAnalyzer(db)
        report = analyzer.analyze(bot_id)
        assert report.nicho_id == "inexistente"
        assert report.total_topics == 8
        print(f"✅ nicho_id={report.nicho_id}, topics={report.total_topics} (fallback otro)")
        db.close()
    finally:
        cleanup_bot(bot_id)


def test_analyzer_nicho_default_otro():
    """
    TEST 5 — Comportamiento ACTUAL del modelo (no arquitectura definitiva).
    """
    print("\n" + "=" * 70)
    print("TEST 5: nicho_id=None → default actual aplica 'otro'")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("none", nicho_id=None)
    try:
        db = SessionLocal()
        analyzer = TrainingAnalyzer(db)
        report = analyzer.analyze(bot_id)

        assert report.nicho_id == "otro"
        assert report.total_topics == 8
        print(f"✅ nicho_id={report.nicho_id!r} (default aplicado), topics={report.total_topics}")
        print(f"   TODO: en una fase futura, nicho_id debería poder ser None para 'Desde cero'")
        db.close()
    finally:
        cleanup_bot(bot_id)


def test_analyzer_counts_memories():
    print("\n" + "=" * 70)
    print("TEST 6: Cuenta memorias correctamente")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("mem")
    try:
        add_memory(bot_id, "Abrimos de 9:00 a 18:00", "horario")
        add_memory(bot_id, "Aceptamos reservas", "reservas")
        add_memory(bot_id, "Tenemos terraza", "terraza")

        db = SessionLocal()
        analyzer = TrainingAnalyzer(db)
        report = analyzer.analyze(bot_id)
        assert report.memories_count == 3
        assert report.has_memories is True
        print(f"✅ memories_count={report.memories_count}")
        db.close()
    finally:
        cleanup_bot(bot_id)


def test_analyzer_counts_ready_sources_only():
    print("\n" + "=" * 70)
    print("TEST 7: Solo cuenta sources con status=ready")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("src")
    try:
        add_source(bot_id, user_id, "Ready source", status="ready")
        add_source(bot_id, user_id, "Pending source", status="pending")
        add_source(bot_id, user_id, "Failed source", status="failed")

        db = SessionLocal()
        analyzer = TrainingAnalyzer(db)
        report = analyzer.analyze(bot_id)
        assert report.ready_sources_count == 1
        assert report.has_sources is True
        print(f"✅ ready_sources_count={report.ready_sources_count} (de 3 sources)")
        db.close()
    finally:
        cleanup_bot(bot_id)


def test_analyzer_topics_from_nicho():
    print("\n" + "=" * 70)
    print("TEST 8: Topics vienen del catálogo del nicho")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("topics", nicho_id="restaurantes")
    try:
        db = SessionLocal()
        analyzer = TrainingAnalyzer(db)
        report = analyzer.analyze(bot_id)
        assert report.total_topics == 11
        menu_topic = next((t for t in report.topics if t.topic_id == "menu"), None)
        assert menu_topic is not None
        assert menu_topic.label == "Menú"
        print(f"✅ {report.total_topics} topics de restaurantes, incluye 'menu'")
        db.close()
    finally:
        cleanup_bot(bot_id)


def test_analyzer_bot_without_knowledge_all_missing():
    """
    TEST 9 (actualizado en 14.4.3):
    Un bot SIN conocimiento (sin memories ni sources) → todos los topics MISSING.

    (Antes de 14.4.3 este test era un "STUB → todos MISSING".
    Ahora es real: comprueba el comportamiento con bot vacío.)
    """
    print("\n" + "=" * 70)
    print("TEST 9: Bot sin conocimiento → todos MISSING")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("stub")
    try:
        db = SessionLocal()
        analyzer = TrainingAnalyzer(db)
        report = analyzer.analyze(bot_id)

        assert all(
            t.status == TopicCoverageStatus.MISSING
            for t in report.topics
        )
        assert report.covered_count == 0
        assert report.partial_count == 0
        assert report.missing_count == report.total_topics
        print(f"✅ Bot sin conocimiento: todos MISSING, missing_count={report.missing_count}")
        db.close()
    finally:
        cleanup_bot(bot_id)


def test_analyzer_bot_without_knowledge_progress_zero():
    """
    TEST 10 (actualizado en 14.4.3):
    Un bot SIN conocimiento → progress = 0.0
    """
    print("\n" + "=" * 70)
    print("TEST 10: Bot sin conocimiento → progress=0.0")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("progress")
    try:
        db = SessionLocal()
        analyzer = TrainingAnalyzer(db)
        report = analyzer.analyze(bot_id)
        assert report.progress == 0.0
        print(f"✅ progress={report.progress}")
        db.close()
    finally:
        cleanup_bot(bot_id)


def test_analyzer_conversation_limit_param():
    print("\n" + "=" * 70)
    print("TEST 11: conversation_limit aceptado pero no usado en 14.4.2")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("limit")
    try:
        db = SessionLocal()
        analyzer = TrainingAnalyzer(db)
        report = analyzer.analyze(bot_id, conversation_limit=50)
        assert report.conversations_analyzed == 0
        print(f"✅ conversation_limit aceptado, conversations_analyzed=0 (stub)")
        db.close()
    finally:
        cleanup_bot(bot_id)


def test_analyzer_no_side_effects():
    print("\n" + "=" * 70)
    print("TEST 12: Analyzer NO modifica datos en BD")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("sideeffects")
    try:
        add_memory(bot_id, "Test", "test")

        db = SessionLocal()
        before_bots = db.query(Bot).count()
        before_memories = db.query(Memory).count()
        before_sources = db.query(Source).count()
        before_convs = db.query(Conversation).count()
        db.close()

        db = SessionLocal()
        analyzer = TrainingAnalyzer(db)
        analyzer.analyze(bot_id)
        db.close()

        db = SessionLocal()
        after_bots = db.query(Bot).count()
        after_memories = db.query(Memory).count()
        after_sources = db.query(Source).count()
        after_convs = db.query(Conversation).count()
        db.close()

        assert before_bots == after_bots
        assert before_memories == after_memories
        assert before_sources == after_sources
        assert before_convs == after_convs
        print(f"✅ Sin side effects: todos los conteos idénticos")
    finally:
        cleanup_bot(bot_id)


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.4.2 (Training Analyzer esqueleto)")
    print("=" * 70)

    tests = [
        test_analyzer_bot_not_found,
        test_analyzer_empty_bot,
        test_analyzer_returns_all_fields,
        test_analyzer_nicho_fallback_unknown,
        test_analyzer_nicho_default_otro,
        test_analyzer_counts_memories,
        test_analyzer_counts_ready_sources_only,
        test_analyzer_topics_from_nicho,
        test_analyzer_bot_without_knowledge_all_missing,
        test_analyzer_bot_without_knowledge_progress_zero,
        test_analyzer_conversation_limit_param,
        test_analyzer_no_side_effects,
    ]

    try:
        for t in tests:
            t()
        print("\n" + "=" * 70)
        print("🎉 TODOS LOS TESTS PASARON")
        print("=" * 70)
    except AssertionError as e:
        print(f"\n🛑 TEST FALLIDO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n🛑 ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
