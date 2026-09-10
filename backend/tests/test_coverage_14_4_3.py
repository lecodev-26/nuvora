"""
Tests — Subfase 14.4.3
Verifica Coverage + Scoring reales.
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.config import SessionLocal
from app.models.db_models import (
    Bot, User, Memory, Source, SourceChunk,
)
from app.core.training.topics import Topic, get_topics_for_nicho
from app.core.training.coverage import compute_coverage, _item_type, _classify
from app.core.training.scoring import calculate_progress
from app.core.knowledge_retriever import KnowledgeItem
from app.models.training import TopicCoverageStatus, TopicCoverage
from app.core.indexing import invalidate_all_indexes


# ============================================================
# HELPERS
# ============================================================

def setup_test_user_bot(suffix: str, nicho_id: str = "otro") -> tuple[int, int]:
    db = SessionLocal()
    try:
        from app.services.auth import get_password_hash

        email = f"test_cov_{suffix}@nuvora.com"
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                hashed_password=get_password_hash("123456"),
                full_name=f"Test Cov {suffix}",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        bot_name = f"Bot Cov {suffix}"
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


def add_source_with_chunks(bot_id: int, user_id: int, title: str, chunk_texts: list[str]):
    db = SessionLocal()
    try:
        source = Source(
            bot_id=bot_id,
            user_id=user_id,
            type="text",
            title=title,
            content_raw=" ".join(chunk_texts),
            content_processed=" ".join(chunk_texts),
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
        invalidate_all_indexes()
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
        invalidate_all_indexes()
    finally:
        db.close()


def _make_item(source_id: str, score: float) -> KnowledgeItem:
    """Helper para crear un KnowledgeItem sintético."""
    return KnowledgeItem(
        content="test",
        source_id=source_id,
        score=score,
    )


# ============================================================
# TESTS — _item_type
# ============================================================

def test_item_type_memory():
    print("\n" + "=" * 70)
    print("TEST 1: _item_type → memory")
    print("=" * 70)
    item = _make_item("memory:42", 3.0)
    assert _item_type(item) == "memory"
    print(f"✅ memory:42 → memory")


def test_item_type_source():
    print("\n" + "=" * 70)
    print("TEST 2: _item_type → source")
    print("=" * 70)
    item = _make_item("source:7:chunk:3", 0.5)
    assert _item_type(item) == "source"
    print(f"✅ source:7:chunk:3 → source")


def test_item_type_unknown():
    print("\n" + "=" * 70)
    print("TEST 3: _item_type → unknown (NO asumir memory)")
    print("=" * 70)
    item = _make_item("weird_format", 1.0)
    assert _item_type(item) == "unknown"
    item2 = _make_item("", 1.0)
    assert _item_type(item2) == "unknown"
    item3 = _make_item(None, 1.0)
    assert _item_type(item3) == "unknown"
    print(f"✅ formato desconocido → unknown (no se asume memory)")


# ============================================================
# TESTS — _classify
# ============================================================

def test_classify_empty():
    print("\n" + "=" * 70)
    print("TEST 4: _classify([]) → MISSING")
    print("=" * 70)
    status, count, best = _classify([])
    assert status == TopicCoverageStatus.MISSING
    assert count == 0
    assert best == 0.0
    print(f"✅ MISSING, count=0")


def test_classify_single_memory_strong():
    print("\n" + "=" * 70)
    print("TEST 5: Una única memory fuerte → COVERED")
    print("=" * 70)
    items = [_make_item("memory:1", 3.0)]
    status, count, best = _classify(items)
    assert status == TopicCoverageStatus.COVERED
    assert count == 1
    assert best == 3.0
    print(f"✅ COVERED con 1 única memory score=3.0")


def test_classify_single_source_strong():
    print("\n" + "=" * 70)
    print("TEST 6: Una única source fuerte → COVERED")
    print("=" * 70)
    items = [_make_item("source:1:chunk:0", 0.15)]
    status, count, best = _classify(items)
    assert status == TopicCoverageStatus.COVERED
    assert count == 1
    print(f"✅ COVERED con 1 única source score=0.15")


def test_classify_single_memory_partial():
    print("\n" + "=" * 70)
    print("TEST 7: Una memory parcial → PARTIAL")
    print("=" * 70)
    items = [_make_item("memory:1", 0.7)]
    status, count, best = _classify(items)
    assert status == TopicCoverageStatus.PARTIAL
    print(f"✅ PARTIAL con memory score=0.7")


def test_classify_single_source_partial():
    print("\n" + "=" * 70)
    print("TEST 8: Una source parcial → PARTIAL")
    print("=" * 70)
    items = [_make_item("source:1:chunk:0", 0.04)]
    status, count, best = _classify(items)
    assert status == TopicCoverageStatus.PARTIAL
    print(f"✅ PARTIAL con source score=0.04")


def test_classify_below_threshold():
    print("\n" + "=" * 70)
    print("TEST 9: Evidencia por debajo del umbral → MISSING")
    print("=" * 70)
    items = [_make_item("memory:1", 0.3)]  # memory partial threshold es 0.5
    status, count, best = _classify(items)
    assert status == TopicCoverageStatus.MISSING
    assert best == 0.3
    print(f"✅ MISSING con memory score=0.3 (bajo el umbral parcial de 0.5)")


def test_classify_mixed_scales_not_summed():
    print("\n" + "=" * 70)
    print("TEST 10: Mixed con escalas diferentes — NO se suman")
    print("=" * 70)
    # Memory score 0.3 (por debajo de partial) + Source score 0.02 (por debajo de partial)
    # Si se sumaran darían 0.32, pero NO se suman → MISSING
    items = [
        _make_item("memory:1", 0.3),
        _make_item("source:1:chunk:0", 0.02),
    ]
    status, count, best = _classify(items)
    assert status == TopicCoverageStatus.MISSING
    print(f"✅ MISSING: no se suman escalas (memory 0.3 + source 0.02)")


def test_classify_mixed_memory_strong():
    print("\n" + "=" * 70)
    print("TEST 11: Mixed con memory fuerte → COVERED")
    print("=" * 70)
    items = [
        _make_item("memory:1", 3.0),
        _make_item("source:1:chunk:0", 0.02),
    ]
    status, count, best = _classify(items)
    assert status == TopicCoverageStatus.COVERED
    assert count == 2
    print(f"✅ COVERED (memory 3.0 fuerte + source débil)")


def test_classify_mixed_source_strong():
    print("\n" + "=" * 70)
    print("TEST 12: Mixed con source fuerte → COVERED")
    print("=" * 70)
    items = [
        _make_item("memory:1", 0.3),
        _make_item("source:1:chunk:0", 0.20),
    ]
    status, count, best = _classify(items)
    assert status == TopicCoverageStatus.COVERED
    print(f"✅ COVERED (source 0.20 fuerte + memory débil)")


def test_classify_mixed_only_partial():
    print("\n" + "=" * 70)
    print("TEST 13: Mixed con evidencia solo parcial → PARTIAL")
    print("=" * 70)
    items = [
        _make_item("memory:1", 0.7),          # partial
        _make_item("source:1:chunk:0", 0.05), # partial
    ]
    status, count, best = _classify(items)
    assert status == TopicCoverageStatus.PARTIAL
    print(f"✅ PARTIAL (memory 0.7 + source 0.05, ninguna strong)")


def test_classify_unknown_ignored():
    print("\n" + "=" * 70)
    print("TEST 14: Item con tipo 'unknown' se ignora")
    print("=" * 70)
    items = [
        _make_item("weird_format", 5.0),  # ignorado
    ]
    status, count, best = _classify(items)
    assert status == TopicCoverageStatus.MISSING
    assert count == 0
    print(f"✅ MISSING (item unknown ignorado)")


def test_classify_mixed_best_score():
    print("\n" + "=" * 70)
    print("TEST 15: best_score devuelve el mayor entre memory y source")
    print("=" * 70)
    items = [
        _make_item("memory:1", 0.7),
        _make_item("source:1:chunk:0", 0.15),
    ]
    status, count, best = _classify(items)
    # Aunque las escalas son distintas, best_score devuelve max de los dos
    assert best == 0.7
    print(f"✅ best_score={best} (mayor de memory 0.7 y source 0.15)")


# ============================================================
# TESTS — compute_coverage
# ============================================================

def test_coverage_empty_bot():
    print("\n" + "=" * 70)
    print("TEST 16: Bot vacío → todos MISSING")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("cov_empty")
    try:
        topics = get_topics_for_nicho("otro")
        db = SessionLocal()
        coverages = compute_coverage(topics, bot_id, db)
        db.close()

        assert len(coverages) == len(topics)
        assert all(c.status == TopicCoverageStatus.MISSING for c in coverages)
        print(f"✅ {len(coverages)} topics, todos MISSING")
    finally:
        cleanup_bot(bot_id)


def test_coverage_multitenant():
    print("\n" + "=" * 70)
    print("TEST 17: Aislamiento multi-tenant")
    print("=" * 70)
    invalidate_all_indexes()
    user1, bot1 = setup_test_user_bot("cov_mt1")
    user2, bot2 = setup_test_user_bot("cov_mt2")
    try:
        # Solo bot1 tiene knowledge
        add_memory(bot1, "Abrimos de 9:00 a 18:00", "horario abrimos")

        topics = get_topics_for_nicho("otro")
        db = SessionLocal()
        cov1 = compute_coverage(topics, bot1, db)
        cov2 = compute_coverage(topics, bot2, db)
        db.close()

        # bot1 debería tener algún topic no-MISSING
        # bot2 debería tener todos MISSING
        assert all(c.status == TopicCoverageStatus.MISSING for c in cov2)
        print(f"✅ bot2 (sin knowledge) → todos MISSING")
    finally:
        cleanup_bot(bot1)
        cleanup_bot(bot2)


def test_coverage_returns_one_per_topic():
    print("\n" + "=" * 70)
    print("TEST 18: Devuelve un TopicCoverage por topic")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("cov_count")
    try:
        topics = get_topics_for_nicho("restaurantes")
        db = SessionLocal()
        coverages = compute_coverage(topics, bot_id, db)
        db.close()

        assert len(coverages) == len(topics)
        for c, t in zip(coverages, topics):
            assert c.topic_id == t.id
            assert c.label == t.label
        print(f"✅ {len(coverages)} TopicCoverage, uno por topic")
    finally:
        cleanup_bot(bot_id)


def test_coverage_does_not_write_db():
    print("\n" + "=" * 70)
    print("TEST 19: compute_coverage NO modifica la BD")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("cov_nowrite")
    try:
        add_memory(bot_id, "Abrimos de 9:00 a 18:00", "horario")

        db = SessionLocal()
        before_mem = db.query(Memory).count()
        before_src = db.query(Source).count()
        before_bot = db.query(Bot).count()
        db.close()

        topics = get_topics_for_nicho("otro")
        db = SessionLocal()
        compute_coverage(topics, bot_id, db)
        db.close()

        db = SessionLocal()
        after_mem = db.query(Memory).count()
        after_src = db.query(Source).count()
        after_bot = db.query(Bot).count()
        db.close()

        assert before_mem == after_mem
        assert before_src == after_src
        assert before_bot == after_bot
        print(f"✅ Sin side effects")
    finally:
        cleanup_bot(bot_id)


# ============================================================
# TESTS — scoring
# ============================================================

def _make_coverage(status: TopicCoverageStatus) -> TopicCoverage:
    return TopicCoverage(
        topic_id="x",
        label="x",
        description="x",
        status=status,
    )


def test_scoring_empty():
    print("\n" + "=" * 70)
    print("TEST 20: calculate_progress([]) → 0.0")
    print("=" * 70)
    result = calculate_progress([])
    assert result["progress"] == 0.0
    assert result["covered_count"] == 0
    assert result["partial_count"] == 0
    assert result["missing_count"] == 0
    print(f"✅ progress=0.0")


def test_scoring_all_covered():
    print("\n" + "=" * 70)
    print("TEST 21: Todos COVERED → progress=1.0")
    print("=" * 70)
    coverages = [_make_coverage(TopicCoverageStatus.COVERED) for _ in range(5)]
    result = calculate_progress(coverages)
    assert result["progress"] == 1.0
    assert result["covered_count"] == 5
    print(f"✅ progress=1.0, covered=5")


def test_scoring_all_missing():
    print("\n" + "=" * 70)
    print("TEST 22: Todos MISSING → progress=0.0")
    print("=" * 70)
    coverages = [_make_coverage(TopicCoverageStatus.MISSING) for _ in range(5)]
    result = calculate_progress(coverages)
    assert result["progress"] == 0.0
    assert result["missing_count"] == 5
    print(f"✅ progress=0.0, missing=5")


def test_scoring_all_partial():
    print("\n" + "=" * 70)
    print("TEST 23: Todos PARTIAL → progress=0.5")
    print("=" * 70)
    coverages = [_make_coverage(TopicCoverageStatus.PARTIAL) for _ in range(4)]
    result = calculate_progress(coverages)
    assert result["progress"] == 0.5
    assert result["partial_count"] == 4
    print(f"✅ progress=0.5, partial=4")


def test_scoring_mixed_6_2_2():
    print("\n" + "=" * 70)
    print("TEST 24: 6 covered, 2 partial, 2 missing → 0.70")
    print("=" * 70)
    coverages = (
        [_make_coverage(TopicCoverageStatus.COVERED) for _ in range(6)] +
        [_make_coverage(TopicCoverageStatus.PARTIAL) for _ in range(2)] +
        [_make_coverage(TopicCoverageStatus.MISSING) for _ in range(2)]
    )
    result = calculate_progress(coverages)
    # (6 + 2*0.5) / 10 = 0.70
    assert result["progress"] == 0.70
    assert result["covered_count"] == 6
    assert result["partial_count"] == 2
    assert result["missing_count"] == 2
    print(f"✅ progress=0.70 (6 covered, 2 partial, 2 missing)")


def test_scoring_rounding():
    print("\n" + "=" * 70)
    print("TEST 25: Redondeo a 2 decimales")
    print("=" * 70)
    # 1 covered, 2 missing → 1/3 = 0.3333 → round 0.33
    coverages = (
        [_make_coverage(TopicCoverageStatus.COVERED)] +
        [_make_coverage(TopicCoverageStatus.MISSING) for _ in range(2)]
    )
    result = calculate_progress(coverages)
    assert result["progress"] == 0.33
    print(f"✅ progress=0.33 (1/3 redondeado)")


# ============================================================
# TESTS — Rendimiento
# ============================================================

def test_coverage_performance():
    print("\n" + "=" * 70)
    print("TEST 26: Medición de rendimiento (informativa)")
    print("=" * 70)
    invalidate_all_indexes()
    user_id, bot_id = setup_test_user_bot("perf")
    try:
        # Añadir 5 memorias
        for i in range(5):
            add_memory(bot_id, f"Hecho {i} sobre horarios y servicios", f"keyword{i} horario")

        topics = get_topics_for_nicho("restaurantes")  # 11 topics

        db = SessionLocal()
        start = time.monotonic()
        coverages = compute_coverage(topics, bot_id, db)
        elapsed_ms = int((time.monotonic() - start) * 1000)
        db.close()

        print(f"✅ {len(coverages)} topics analizados en {elapsed_ms} ms")
        print(f"   Rendimiento: {elapsed_ms / len(coverages):.1f} ms/topic")
        # No assert estricto, solo medición informativa
    finally:
        cleanup_bot(bot_id)


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.4.3 (Coverage + Scoring reales)")
    print("=" * 70)

    tests = [
        # _item_type
        test_item_type_memory,
        test_item_type_source,
        test_item_type_unknown,
        # _classify
        test_classify_empty,
        test_classify_single_memory_strong,
        test_classify_single_source_strong,
        test_classify_single_memory_partial,
        test_classify_single_source_partial,
        test_classify_below_threshold,
        test_classify_mixed_scales_not_summed,
        test_classify_mixed_memory_strong,
        test_classify_mixed_source_strong,
        test_classify_mixed_only_partial,
        test_classify_unknown_ignored,
        test_classify_mixed_best_score,
        # compute_coverage
        test_coverage_empty_bot,
        test_coverage_multitenant,
        test_coverage_returns_one_per_topic,
        test_coverage_does_not_write_db,
        # scoring
        test_scoring_empty,
        test_scoring_all_covered,
        test_scoring_all_missing,
        test_scoring_all_partial,
        test_scoring_mixed_6_2_2,
        test_scoring_rounding,
        # performance
        test_coverage_performance,
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
