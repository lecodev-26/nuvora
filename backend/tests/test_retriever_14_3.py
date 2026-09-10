"""
Tests — Subfase 14.3.3
Verifica indexación TF-IDF y SourceRetriever.
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.config import SessionLocal
from app.models.db_models import Bot, User, Source, SourceChunk
from app.core.indexing import (
    tokenize,
    IndexBuilder,
    score_query_against_documents,
    invalidate_index,
    invalidate_all_indexes,
    get_cached_index,
    set_cached_index,
)
from app.core.source_retriever import SourceRetriever


# ============================================================
# HELPERS
# ============================================================

def setup_test_user_bot(suffix: str) -> tuple[int, int]:
    """Crea un usuario y bot únicos para pruebas."""
    db = SessionLocal()
    try:
        from app.services.auth import get_password_hash

        email = f"test_retriever_{suffix}@nuvora.com"
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                hashed_password=get_password_hash("123456"),
                full_name=f"Test Retriever {suffix}",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        bot_name = f"Bot Retriever {suffix}"
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


def create_source_with_chunks(bot_id: int, user_id: int, title: str, chunk_texts: list[str]) -> int:
    """Crea una Source y sus chunks. Devuelve el source_id."""
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

        return source.id
    finally:
        db.close()


def cleanup_bot(bot_id: int):
    """Elimina un bot y sus sources/chunks."""
    db = SessionLocal()
    try:
        db.query(SourceChunk).filter(SourceChunk.bot_id == bot_id).delete(synchronize_session=False)
        db.query(Source).filter(Source.bot_id == bot_id).delete(synchronize_session=False)
        db.query(Bot).filter(Bot.id == bot_id).delete(synchronize_session=False)
        db.commit()
        invalidate_index(bot_id)
    finally:
        db.close()


# ============================================================
# TESTS — INDEXING
# ============================================================

def test_tokenize_basic():
    print("\n" + "=" * 70)
    print("TEST 1: tokenize básico")
    print("=" * 70)
    tokens = tokenize("Restaurante abre los domingos, gracias.")
    assert "restaurante" in tokens
    assert "abre" in tokens
    assert "domingos" in tokens
    assert "gracias" in tokens
    assert "los" not in tokens
    assert "el" not in tokens
    assert "la" not in tokens
    print(f"✅ Tokens: {tokens}")


def test_tokenize_accents():
    print("\n" + "=" * 70)
    print("TEST 2: tokenize con acentos")
    print("=" * 70)
    tokens1 = tokenize("café corazón música")
    tokens2 = tokenize("cafe corazon musica")
    assert tokens1 == tokens2
    print(f"✅ Acentos normalizados: {tokens1}")


def test_index_builder():
    print("\n" + "=" * 70)
    print("TEST 3: IndexBuilder")
    print("=" * 70)
    docs = [
        "El restaurante abre de 9:00 a 18:00",
        "Aceptamos reservas por teléfono",
        "Tenemos opciones vegetarianas",
    ]
    builder = IndexBuilder(docs)
    index = builder.build()
    assert index["num_docs"] == 3
    assert "idf" in index
    assert len(index["doc_tfs"]) == 3
    assert len(index["doc_norms"]) == 3
    print(f"✅ Índice construido: {len(index['idf'])} tokens únicos")


def test_score_query():
    print("\n" + "=" * 70)
    print("TEST 4: score_query_against_documents")
    print("=" * 70)
    docs = [
        "El restaurante abre de 9:00 a 18:00",
        "Aceptamos reservas por teléfono",
        "Tenemos opciones vegetarianas",
    ]
    builder = IndexBuilder(docs)
    index = builder.build()

    scores = score_query_against_documents("¿A qué hora abre?", index)
    assert len(scores) == 3
    # El doc 0 contiene "abre" → debe ganar
    assert scores[0] > 0
    assert scores[0] > scores[1]
    assert scores[0] > scores[2]
    print(f"✅ Scores: {[f'{s:.3f}' for s in scores]}")
    print(f"   Ganador: doc 0 (contiene 'abre')")


def test_score_variants():
    """
    Documenta explícitamente las LIMITACIONES del TF-IDF MVP:
    - NO hace stemming/lemmatización
    - Solo encuentra coincidencias EXACTAS de tokens

    Por eso:
    - "abre" → match ✅ (el doc contiene "abre")
    - "abierto" → NO match (el doc no contiene "abierto")
    - "hora" → NO match si el doc no contiene "hora" literal
    """
    print("\n" + "=" * 70)
    print("TEST 5: variantes de preguntas (LIMITACIONES del TF-IDF MVP)")
    print("=" * 70)
    docs = [
        "El restaurante abre de 9:00 a 18:00",
        "Aceptamos reservas por teléfono",
    ]
    builder = IndexBuilder(docs)
    index = builder.build()

    # Caso 1: match exacto
    scores_abre = score_query_against_documents("abre", index)
    print(f"   Query 'abre' (match exacto) → scores: {[f'{s:.3f}' for s in scores_abre]}")
    assert scores_abre[0] > 0, "Debería encontrar 'abre' por coincidencia exacta"

    # Caso 2: sin stemming (NO match, comportamiento esperado)
    scores_abierto = score_query_against_documents("abierto", index)
    print(f"   Query 'abierto' (sin stemming) → scores: {[f'{s:.3f}' for s in scores_abierto]}")
    assert scores_abierto[0] == 0, "Sin stemming, 'abierto' no debe coincidir con 'abre'"

    # Caso 3: sinónimos (NO match, comportamiento esperado)
    scores_hora = score_query_against_documents("hora", index)
    print(f"   Query 'hora' (sin sinónimos) → scores: {[f'{s:.3f}' for s in scores_hora]}")
    assert scores_hora[0] == 0, "Sin sinónimos, 'hora' no debe coincidir con '9:00'"

    # Caso 4: otra palabra presente en el doc
    scores_restaurante = score_query_against_documents("restaurante", index)
    print(f"   Query 'restaurante' (match exacto) → scores: {[f'{s:.3f}' for s in scores_restaurante]}")
    assert scores_restaurante[0] > 0, "Debería encontrar 'restaurante'"

    print(f"✅ Limitaciones del TF-IDF MVP documentadas correctamente")


# ============================================================
# TESTS — CACHÉ
# ============================================================

def test_cache_basic():
    print("\n" + "=" * 70)
    print("TEST 6: Caché de índices")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("cache")
    try:
        create_source_with_chunks(bot_id, user_id, "Test Cache", [
            "Abrimos de 9:00 a 18:00",
            "Aceptamos reservas",
        ])

        db = SessionLocal()
        retriever = SourceRetriever(db)
        result = retriever.retrieve(bot_id, "reservas")
        assert len(result.items) > 0

        cached = get_cached_index(bot_id)
        assert cached is not None
        print(f"✅ Índice cacheado para bot {bot_id}")

        db.close()
    finally:
        cleanup_bot(bot_id)


def test_cache_invalidation():
    print("\n" + "=" * 70)
    print("TEST 7: Invalidación de caché")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("invalidation")
    try:
        create_source_with_chunks(bot_id, user_id, "Test Inv", ["Contenido inicial"])

        db = SessionLocal()
        retriever = SourceRetriever(db)
        retriever.retrieve(bot_id, "contenido")

        assert get_cached_index(bot_id) is not None
        print(f"   ✅ Índice cacheado")

        invalidate_index(bot_id)
        assert get_cached_index(bot_id) is None
        print(f"   ✅ Índice invalidado")

        db.close()
    finally:
        cleanup_bot(bot_id)


def test_cache_isolation():
    print("\n" + "=" * 70)
    print("TEST 8: Aislamiento de caché por bot_id")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot1_id = setup_test_user_bot("iso1")
    _, bot2_id = setup_test_user_bot("iso2")
    try:
        create_source_with_chunks(bot1_id, user_id, "Bot1", ["Contenido del bot 1"])
        create_source_with_chunks(bot2_id, user_id, "Bot2", ["Contenido del bot 2"])

        db = SessionLocal()
        retriever = SourceRetriever(db)
        retriever.retrieve(bot1_id, "contenido")
        retriever.retrieve(bot2_id, "contenido")

        idx1 = get_cached_index(bot1_id)
        idx2 = get_cached_index(bot2_id)
        assert idx1 is not None
        assert idx2 is not None
        assert idx1 is not idx2
        print(f"✅ Cachés aislados por bot_id")

        db.close()
    finally:
        cleanup_bot(bot1_id)
        cleanup_bot(bot2_id)


# ============================================================
# TESTS — SOURCE RETRIEVER
# ============================================================

def test_retriever_empty():
    print("\n" + "=" * 70)
    print("TEST 9: SourceRetriever sin chunks")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("empty")
    try:
        db = SessionLocal()
        retriever = SourceRetriever(db)
        result = retriever.retrieve(bot_id, "cualquier cosa")
        assert len(result.items) == 0
        assert result.source_type == "source"
        print(f"✅ KnowledgeResult vacío cuando no hay chunks")
        db.close()
    finally:
        cleanup_bot(bot_id)


def test_retriever_basic():
    print("\n" + "=" * 70)
    print("TEST 10: SourceRetriever básico")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("basic")
    try:
        create_source_with_chunks(bot_id, user_id, "Info", [
            "Abrimos de 9:00 a 18:00 todos los días",
            "Tenemos terraza y parking gratuito",
            "Aceptamos reservas por teléfono o web",
        ])

        db = SessionLocal()
        retriever = SourceRetriever(db)
        result = retriever.retrieve(bot_id, "reservas")
        assert len(result.items) > 0
        assert "reservas" in result.items[0].content.lower()
        print(f"✅ Encontrado: '{result.items[0].content[:60]}...'")
        print(f"   Score: {result.items[0].score:.3f}")
        db.close()
    finally:
        cleanup_bot(bot_id)


def test_retriever_ranking():
    print("\n" + "=" * 70)
    print("TEST 11: SourceRetriever ranking")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("ranking")
    try:
        create_source_with_chunks(bot_id, user_id, "Info", [
            "Abrimos de 9:00 a 18:00",
            "Cerramos los domingos",
            "Abrimos los sábados con horario especial",
        ])

        db = SessionLocal()
        retriever = SourceRetriever(db)
        result = retriever.retrieve(bot_id, "abrimos")
        assert len(result.items) >= 1
        for i in range(len(result.items) - 1):
            assert result.items[i].score >= result.items[i + 1].score
        print(f"✅ {len(result.items)} items ordenados por score")
        for item in result.items:
            print(f"   score={item.score:.3f} | {item.content[:50]}")
        db.close()
    finally:
        cleanup_bot(bot_id)


def test_retriever_metadata():
    print("\n" + "=" * 70)
    print("TEST 12: SourceRetriever metadatos")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("metadata")
    try:
        create_source_with_chunks(bot_id, user_id, "Info", ["Abrimos de 9:00 a 18:00"])

        db = SessionLocal()
        retriever = SourceRetriever(db)
        result = retriever.retrieve(bot_id, "abrimos")
        assert len(result.items) > 0
        item = result.items[0]
        assert item.source_id.startswith("source:")
        assert ":chunk:" in item.source_id
        assert item.category is not None
        assert item.metadata["chunk_id"] is not None
        print(f"✅ Item: source_id='{item.source_id}', category='{item.category}'")
        db.close()
    finally:
        cleanup_bot(bot_id)


def test_retriever_multitenant():
    print("\n" + "=" * 70)
    print("TEST 13: SourceRetriever aislamiento multi-tenant")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot1_id = setup_test_user_bot("mt1")
    _, bot2_id = setup_test_user_bot("mt2")
    try:
        create_source_with_chunks(bot1_id, user_id, "Bot1", ["Contenido confidencial bot1"])
        create_source_with_chunks(bot2_id, user_id, "Bot2", ["Contenido público bot2"])

        db = SessionLocal()
        retriever = SourceRetriever(db)

        result1 = retriever.retrieve(bot1_id, "público")
        for item in result1.items:
            assert "bot2" not in item.content.lower()
        print(f"✅ Bot 1 no ve contenido del bot 2")

        result2 = retriever.retrieve(bot2_id, "confidencial")
        for item in result2.items:
            assert "bot1" not in item.content.lower()
        print(f"✅ Bot 2 no ve contenido del bot 1")

        db.close()
    finally:
        cleanup_bot(bot1_id)
        cleanup_bot(bot2_id)


def test_retriever_irrelevant_query():
    print("\n" + "=" * 70)
    print("TEST 14: SourceRetriever con query irrelevante")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("irrelevant")
    try:
        create_source_with_chunks(bot_id, user_id, "Info", [
            "Abrimos de 9:00 a 18:00",
            "Tenemos terraza",
        ])

        db = SessionLocal()
        retriever = SourceRetriever(db)
        result = retriever.retrieve(bot_id, "física cuántica termodinámica")
        assert len(result.items) == 0
        print(f"✅ Query irrelevante devuelve vacío")
        db.close()
    finally:
        cleanup_bot(bot_id)


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.3.3 (Indexing + SourceRetriever)")
    print("=" * 70)

    tests = [
        test_tokenize_basic,
        test_tokenize_accents,
        test_index_builder,
        test_score_query,
        test_score_variants,
        test_cache_basic,
        test_cache_invalidation,
        test_cache_isolation,
        test_retriever_empty,
        test_retriever_basic,
        test_retriever_ranking,
        test_retriever_metadata,
        test_retriever_multitenant,
        test_retriever_irrelevant_query,
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
