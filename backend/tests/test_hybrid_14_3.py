"""
Tests — Subfase 14.3.4
Verifica HybridRetriever.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.config import SessionLocal
from app.models.db_models import Bot, User, Source, SourceChunk, Memory
from app.core.hybrid_retriever import HybridRetriever
from app.core.indexing import invalidate_index, invalidate_all_indexes


# ============================================================
# HELPERS
# ============================================================

def setup_test_user_bot(suffix: str) -> tuple[int, int]:
    db = SessionLocal()
    try:
        from app.services.auth import get_password_hash

        email = f"test_hybrid_{suffix}@nuvora.com"
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                hashed_password=get_password_hash("123456"),
                full_name=f"Test Hybrid {suffix}",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        bot_name = f"Bot Hybrid {suffix}"
        bot = db.query(Bot).filter(Bot.name == bot_name).first()
        if not bot:
            bot = Bot(
                user_id=user.id,
                name=bot_name,
                business_name=f"Test {suffix}",
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


def add_source_with_chunks(bot_id: int, user_id: int, title: str, chunk_texts: list[str]):
    db = SessionLocal()
    try:
        source = Source(
            bot_id=bot_id,
            user_id=user_id,
            type="text",
            title=title,
            content_raw=" ".join(chunk_texts),
            status="ready",
            chunks_count=len(chunk_texts),
        )
        db.add(source)
        db.commit()
        db.refresh(source)

        for i, text in enumerate(chunk_texts):
            chunk = SourceChunk(
                source_id=source.id,
                bot_id=bot_id,
                chunk_index=i,
                content=text,
            )
            db.add(chunk)
        db.commit()

        invalidate_index(bot_id)
    finally:
        db.close()


def cleanup_bot(bot_id: int):
    db = SessionLocal()
    try:
        db.query(Memory).filter(Memory.bot_id == bot_id).delete(synchronize_session=False)
        db.query(SourceChunk).filter(SourceChunk.bot_id == bot_id).delete(synchronize_session=False)
        db.query(Source).filter(Source.bot_id == bot_id).delete(synchronize_session=False)
        db.query(Bot).filter(Bot.id == bot_id).delete(synchronize_session=False)
        db.commit()
        invalidate_index(bot_id)
    finally:
        db.close()


# ============================================================
# TESTS
# ============================================================

def test_hybrid_only_memory():
    print("\n" + "=" * 70)
    print("TEST 1: Solo memorias → source_type='memory'")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("onlymem")
    try:
        add_memory(bot_id, "Abrimos de 9:00 a 18:00", "horario")
        add_memory(bot_id, "Aceptamos reservas", "reservas")

        db = SessionLocal()
        retriever = HybridRetriever(db)
        result = retriever.retrieve(bot_id, "reservas")
        assert result.source_type == "memory"
        assert len(result.items) > 0
        assert result.metadata["memory_hits"] > 0
        assert result.metadata["source_hits"] == 0
        print(f"✅ source_type='{result.source_type}', items={len(result.items)}")
        db.close()
    finally:
        cleanup_bot(bot_id)


def test_hybrid_only_sources():
    print("\n" + "=" * 70)
    print("TEST 2: Solo fuentes → source_type='source'")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("onlysrc")
    try:
        add_source_with_chunks(bot_id, user_id, "Info", [
            "Abrimos de 9:00 a 18:00 todos los días",
            "Tenemos terraza en la azotea",
        ])

        db = SessionLocal()
        retriever = HybridRetriever(db)
        result = retriever.retrieve(bot_id, "terraza")
        assert result.source_type == "source"
        assert len(result.items) > 0
        assert result.metadata["memory_hits"] == 0
        assert result.metadata["source_hits"] > 0
        print(f"✅ source_type='{result.source_type}', items={len(result.items)}")
        db.close()
    finally:
        cleanup_bot(bot_id)


def test_hybrid_both():
    print("\n" + "=" * 70)
    print("TEST 3: Memorias + fuentes → source_type='mixed'")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("mixed")
    try:
        # Memory keyword = "abrimos" para que la query "abrimos" matchee
        add_memory(bot_id, "Abrimos de 9:00 a 18:00", "abrimos")
        # Source content contiene "abrimos" para que la query "abrimos" matchee
        add_source_with_chunks(bot_id, user_id, "Info", [
            "Abrimos también los festivos de 10:00 a 14:00",
        ])

        db = SessionLocal()
        retriever = HybridRetriever(db)

        # Query que matchea AMBOS (memory keyword + source content)
        result = retriever.retrieve(bot_id, "abrimos")
        print(f"   memory_hits={result.metadata['memory_hits']}, source_hits={result.metadata['source_hits']}")
        assert result.metadata["memory_hits"] > 0, "Debería matchear la memory"
        assert result.metadata["source_hits"] > 0, "Debería matchear la source"
        assert result.source_type == "mixed"
        print(f"✅ source_type='{result.source_type}'")

        db.close()
    finally:
        cleanup_bot(bot_id)


def test_hybrid_empty():
    print("\n" + "=" * 70)
    print("TEST 4: Sin memorias ni fuentes → vacío")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("empty")
    try:
        db = SessionLocal()
        retriever = HybridRetriever(db)
        result = retriever.retrieve(bot_id, "cualquier cosa")
        assert len(result.items) == 0
        assert result.source_type == "memory"
        assert result.metadata["memory_hits"] == 0
        assert result.metadata["source_hits"] == 0
        print(f"✅ Resultado vacío: source_type='{result.source_type}'")
        db.close()
    finally:
        cleanup_bot(bot_id)


def test_hybrid_ranking():
    print("\n" + "=" * 70)
    print("TEST 5: Ranking por score DESC")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("ranking")
    try:
        add_memory(bot_id, "Abrimos todos los días", "abrimos")
        add_source_with_chunks(bot_id, user_id, "Info", [
            "Abrimos los sábados de 10:00 a 14:00",
            "Abrimos los domingos de 10:00 a 14:00",
        ])

        db = SessionLocal()
        retriever = HybridRetriever(db)
        result = retriever.retrieve(bot_id, "abrimos", top_k=5)
        assert len(result.items) > 0
        for i in range(len(result.items) - 1):
            assert result.items[i].score >= result.items[i + 1].score
        print(f"✅ {len(result.items)} items ordenados por score DESC")
        for item in result.items:
            print(f"   score={item.score:.3f} | {item.content[:50]}")
        db.close()
    finally:
        cleanup_bot(bot_id)


def test_hybrid_tie_break():
    print("\n" + "=" * 70)
    print("TEST 6: Tie-break — memory gana sobre source con mismo score")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("tie")
    try:
        add_memory(bot_id, "Abrimos de 9:00 a 18:00", "abrimos")
        add_source_with_chunks(bot_id, user_id, "Info", [
            "Abrimos de 9:00 a 18:00",
        ])

        db = SessionLocal()
        retriever = HybridRetriever(db)
        result = retriever.retrieve(bot_id, "abrimos", top_k=5)
        assert len(result.items) >= 2
        assert result.metadata["top_source_type"] == "memory"
        print(f"✅ top_source_type='{result.metadata['top_source_type']}' (memory gana en empate)")
        db.close()
    finally:
        cleanup_bot(bot_id)


def test_hybrid_top_k():
    print("\n" + "=" * 70)
    print("TEST 7: Respetar top_k")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("topk")
    try:
        for i in range(5):
            add_memory(bot_id, f"Contenido {i} de prueba", "contenido")

        db = SessionLocal()
        retriever = HybridRetriever(db)
        result = retriever.retrieve(bot_id, "contenido", top_k=2)
        assert len(result.items) <= 2
        print(f"✅ top_k=2 → {len(result.items)} items devueltos")

        result0 = retriever.retrieve(bot_id, "contenido", top_k=0)
        assert len(result0.items) == 0
        result_neg = retriever.retrieve(bot_id, "contenido", top_k=-1)
        assert len(result_neg.items) == 0
        print(f"✅ top_k<=0 → vacío")
        db.close()
    finally:
        cleanup_bot(bot_id)


def test_hybrid_multitenant():
    print("\n" + "=" * 70)
    print("TEST 8: Aislamiento multi-tenant")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot1_id = setup_test_user_bot("mt1")
    _, bot2_id = setup_test_user_bot("mt2")
    try:
        add_memory(bot1_id, "Contenido secreto de bot1", "secreto")
        add_source_with_chunks(bot2_id, user_id, "Bot2", ["Contenido publico de bot2"])

        db = SessionLocal()
        retriever = HybridRetriever(db)

        result1 = retriever.retrieve(bot1_id, "secreto")
        for item in result1.items:
            assert "bot2" not in item.content.lower()
        print(f"✅ Bot1 no ve datos de bot2")

        result2 = retriever.retrieve(bot2_id, "publico")
        for item in result2.items:
            assert "bot1" not in item.content.lower()
        print(f"✅ Bot2 no ve datos de bot1")

        db.close()
    finally:
        cleanup_bot(bot1_id)
        cleanup_bot(bot2_id)


def test_hybrid_compatible_memory():
    print("\n" + "=" * 70)
    print("TEST 9: Compatibilidad con bot que solo usaba memoria")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("compat")
    try:
        add_memory(bot_id, "Abrimos de 9:00 a 18:00", "horario")
        add_memory(bot_id, "Aceptamos reservas por teléfono", "reservas")

        db = SessionLocal()
        retriever = HybridRetriever(db)

        result = retriever.retrieve(bot_id, "reservas")
        assert result.source_type == "memory"
        assert len(result.items) > 0
        assert "reservas" in result.items[0].content.lower()
        print(f"✅ Bot solo-memoria funciona igual: {result.items[0].content[:50]}")

        db.close()
    finally:
        cleanup_bot(bot_id)


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.3.4 (HybridRetriever)")
    print("=" * 70)

    tests = [
        test_hybrid_only_memory,
        test_hybrid_only_sources,
        test_hybrid_both,
        test_hybrid_empty,
        test_hybrid_ranking,
        test_hybrid_tie_break,
        test_hybrid_top_k,
        test_hybrid_multitenant,
        test_hybrid_compatible_memory,
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
