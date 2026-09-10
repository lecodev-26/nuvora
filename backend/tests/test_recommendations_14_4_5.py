"""
Tests — Subfase 14.4.5
Verifica Recommendation Engine (generate_recommendations).
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.config import SessionLocal
from app.models.db_models import Bot, User
from app.models.training import (
    TopicCoverage,
    TopicCoverageStatus,
    UnansweredQuestionGroup,
    Recommendation,
    RecommendationType,
)
from app.core.training.recommendations import (
    generate_recommendations,
    MIN_QUESTION_COUNT,
    MAX_RECOMMENDATIONS,
    CRITICAL_QUESTION_COUNT,
)


# ============================================================
# HELPERS
# ============================================================

def setup_test_user_bot(suffix: str) -> tuple[int, int]:
    """Crea un usuario y un bot de prueba (solo para tener un Bot real)."""
    db = SessionLocal()
    try:
        from app.services.auth import get_password_hash

        email = f"test_rec_{suffix}@nuvora.com"
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                hashed_password=get_password_hash("123456"),
                full_name=f"Test Rec {suffix}",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        bot_name = f"Bot Rec {suffix}"
        bot = db.query(Bot).filter(Bot.name == bot_name).first()
        if not bot:
            bot = Bot(
                user_id=user.id,
                name=bot_name,
                business_name=f"Test {suffix}",
                nicho_id="otro",
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


def cleanup_bot(bot_id: int):
    db = SessionLocal()
    try:
        db.query(Bot).filter(Bot.id == bot_id).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def make_coverage(
    topic_id: str,
    status: TopicCoverageStatus,
    label: str = None,
    description: str = None,
) -> TopicCoverage:
    """Helper para crear TopicCoverage sintético."""
    return TopicCoverage(
        topic_id=topic_id,
        label=label or topic_id.capitalize(),
        description=description or f"Información sobre {topic_id}",
        icon="",
        status=status,
        evidence_count=0,
        best_score=0.0,
    )


def make_group(representative: str, count: int) -> UnansweredQuestionGroup:
    """Helper para crear UnansweredQuestionGroup sintético."""
    return UnansweredQuestionGroup(
        representative=representative,
        variants=[representative],
        count=count,
        conversation_ids=list(range(1, count + 1)),
    )


# ============================================================
# TESTS
# ============================================================

def test_no_data():
    print("\n" + "=" * 70)
    print("TEST 1: Sin coverages ni preguntas → []")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("empty")
    try:
        db = SessionLocal()
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        result = generate_recommendations(bot, [], [])
        db.close()

        assert result == []
        print(f"✅ []")
    finally:
        cleanup_bot(bot_id)


def test_missing_topic_generates_rec():
    print("\n" + "=" * 70)
    print("TEST 2: 1 missing → 1 recomendación")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("missing")
    try:
        db = SessionLocal()
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        coverages = [make_coverage("horarios", TopicCoverageStatus.MISSING)]
        result = generate_recommendations(bot, coverages, [])
        db.close()

        assert len(result) == 1
        rec = result[0]
        assert rec.type == RecommendationType.MISSING_TOPIC
        assert rec.id == "rec_missing_topic_horarios"
        assert "horarios" in rec.title.lower()
        print(f"✅ 1 rec: '{rec.title}'")
    finally:
        cleanup_bot(bot_id)


def test_partial_topic_generates_rec():
    print("\n" + "=" * 70)
    print("TEST 3: 1 partial → 1 recomendación")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("partial")
    try:
        db = SessionLocal()
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        coverages = [make_coverage("precios", TopicCoverageStatus.PARTIAL)]
        result = generate_recommendations(bot, coverages, [])
        db.close()

        assert len(result) == 1
        rec = result[0]
        assert rec.type == RecommendationType.PARTIAL_TOPIC
        assert rec.id == "rec_partial_topic_precios"
        print(f"✅ 1 rec: '{rec.title}'")
    finally:
        cleanup_bot(bot_id)


def test_frequent_question_generates_rec():
    print("\n" + "=" * 70)
    print("TEST 4: 1 pregunta count=2 → 1 recomendación")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("freq")
    try:
        db = SessionLocal()
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        groups = [make_group("¿Tenéis parking?", count=2)]
        result = generate_recommendations(bot, [], groups)
        db.close()

        assert len(result) == 1
        rec = result[0]
        assert rec.type == RecommendationType.FREQUENT_QUESTION
        assert rec.id.startswith("rec_frequent_question_")
        assert "2 veces" in rec.reason
        print(f"✅ 1 rec: '{rec.title}'")
        print(f"   reason: {rec.reason}")
    finally:
        cleanup_bot(bot_id)


def test_single_question_no_rec():
    print("\n" + "=" * 70)
    print("TEST 5: 1 pregunta count=1 → NO recomendación")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("single")
    try:
        db = SessionLocal()
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        groups = [make_group("¿Tenéis parking?", count=1)]
        result = generate_recommendations(bot, [], groups)
        db.close()

        assert result == []
        print(f"✅ [] (count=1 no genera rec)")
    finally:
        cleanup_bot(bot_id)


def test_ordering_missing_first():
    print("\n" + "=" * 70)
    print("TEST 6: Missing antes que partial")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("order_missing")
    try:
        db = SessionLocal()
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        coverages = [
            make_coverage("precios", TopicCoverageStatus.PARTIAL),
            make_coverage("horarios", TopicCoverageStatus.MISSING),
            make_coverage("menu", TopicCoverageStatus.PARTIAL),
        ]
        result = generate_recommendations(bot, coverages, [])
        db.close()

        assert len(result) == 3
        # El primero debe ser missing
        assert result[0].type == RecommendationType.MISSING_TOPIC
        assert result[0].id == "rec_missing_topic_horarios"
        # Los siguientes son partial
        assert result[1].type == RecommendationType.PARTIAL_TOPIC
        assert result[2].type == RecommendationType.PARTIAL_TOPIC
        print(f"✅ Orden: missing → partial → partial")
    finally:
        cleanup_bot(bot_id)


def test_ordering_frequent_questions_by_count():
    print("\n" + "=" * 70)
    print("TEST 7: Preguntas ordenadas por count DESC")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("order_freq")
    try:
        db = SessionLocal()
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        groups = [
            make_group("¿Tenéis parking?", count=2),
            make_group("¿Aceptáis reservas?", count=5),
            make_group("¿Cuál es el horario?", count=3),
        ]
        result = generate_recommendations(bot, [], groups)
        db.close()

        assert len(result) == 3
        # Deben estar ordenadas por count DESC
        counts = [r.action_payload["count"] for r in result]
        assert counts == [5, 3, 2], f"Orden incorrecto: {counts}"
        print(f"✅ Orden por count: {counts}")
    finally:
        cleanup_bot(bot_id)


def test_ordering_critical_questions_before_partial():
    print("\n" + "=" * 70)
    print("TEST 8: Preguntas count≥3 antes que partial")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("order_crit")
    try:
        db = SessionLocal()
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        coverages = [
            make_coverage("precios", TopicCoverageStatus.PARTIAL),
        ]
        groups = [
            make_group("¿Tenéis parking?", count=3),  # crítico
            make_group("¿Aceptáis reservas?", count=2),  # normal
        ]
        result = generate_recommendations(bot, coverages, groups)
        db.close()

        assert len(result) == 3
        # Orden esperado: freq(critical) → partial → freq(normal)
        assert result[0].type == RecommendationType.FREQUENT_QUESTION
        assert result[0].action_payload["count"] == 3
        assert result[1].type == RecommendationType.PARTIAL_TOPIC
        assert result[2].type == RecommendationType.FREQUENT_QUESTION
        assert result[2].action_payload["count"] == 2
        print(f"✅ Orden: freq(3) → partial → freq(2)")
    finally:
        cleanup_bot(bot_id)


def test_max_recommendations_limit():
    print("\n" + "=" * 70)
    print("TEST 9: Máximo 10 recomendaciones")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("limit")
    try:
        db = SessionLocal()
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        # 20 missing topics
        coverages = [
            make_coverage(f"topic_{i}", TopicCoverageStatus.MISSING)
            for i in range(20)
        ]
        result = generate_recommendations(bot, coverages, [])
        db.close()

        assert len(result) == MAX_RECOMMENDATIONS
        print(f"✅ Máximo respetado: {len(result)} recs (límite {MAX_RECOMMENDATIONS})")
    finally:
        cleanup_bot(bot_id)


def test_rec_id_is_deterministic():
    print("\n" + "=" * 70)
    print("TEST 10: IDs son deterministas")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("det")
    try:
        db = SessionLocal()
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        coverages = [make_coverage("horarios", TopicCoverageStatus.MISSING)]
        groups = [make_group("¿Tenéis parking?", count=2)]

        result1 = generate_recommendations(bot, coverages, groups)
        result2 = generate_recommendations(bot, coverages, groups)
        db.close()

        ids1 = [r.id for r in result1]
        ids2 = [r.id for r in result2]
        assert ids1 == ids2
        print(f"✅ IDs deterministas: {ids1}")
    finally:
        cleanup_bot(bot_id)


def test_rec_id_unique():
    print("\n" + "=" * 70)
    print("TEST 11: IDs únicos dentro del mismo reporte")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("uniq")
    try:
        db = SessionLocal()
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        coverages = [
            make_coverage("horarios", TopicCoverageStatus.MISSING),
            make_coverage("precios", TopicCoverageStatus.MISSING),
            make_coverage("contacto", TopicCoverageStatus.PARTIAL),
        ]
        groups = [
            make_group("¿Tenéis parking?", count=2),
            make_group("¿Aceptáis reservas?", count=3),
        ]
        result = generate_recommendations(bot, coverages, groups)
        db.close()

        ids = [r.id for r in result]
        assert len(ids) == len(set(ids)), f"IDs duplicados: {ids}"
        print(f"✅ {len(ids)} IDs únicos")
    finally:
        cleanup_bot(bot_id)


def test_action_payload_missing_topic():
    print("\n" + "=" * 70)
    print("TEST 12: action_payload de missing_topic")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("payload_missing")
    try:
        db = SessionLocal()
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        coverages = [make_coverage("horarios", TopicCoverageStatus.MISSING, label="Horarios")]
        result = generate_recommendations(bot, coverages, [])
        db.close()

        rec = result[0]
        payload = rec.action_payload
        assert payload["topic_id"] == "horarios"
        assert payload["topic_label"] == "Horarios"
        assert payload["suggested_keyword"] == "horarios"
        assert rec.action_type == "add_memory"
        print(f"✅ Payload: {payload}")
    finally:
        cleanup_bot(bot_id)


def test_action_payload_frequent_question():
    print("\n" + "=" * 70)
    print("TEST 13: action_payload de frequent_question")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("payload_freq")
    try:
        db = SessionLocal()
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        groups = [
            UnansweredQuestionGroup(
                representative="¿Tenéis parking?",
                variants=["¿Tenéis parking?", "¿Hay parking?"],
                count=3,
                conversation_ids=[10, 11, 12],
            )
        ]
        result = generate_recommendations(bot, [], groups)
        db.close()

        rec = result[0]
        payload = rec.action_payload
        assert payload["question"] == "¿Tenéis parking?"
        assert payload["count"] == 3
        assert payload["variants"] == ["¿Tenéis parking?", "¿Hay parking?"]
        assert payload["conversation_ids"] == [10, 11, 12]
        assert rec.action_type == "answer_question"
        print(f"✅ Payload: {payload}")
    finally:
        cleanup_bot(bot_id)


def test_recommendation_title_and_reason():
    print("\n" + "=" * 70)
    print("TEST 14: title y reason correctos")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("texts")
    try:
        db = SessionLocal()
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        coverages = [
            make_coverage("horarios", TopicCoverageStatus.MISSING, label="Horarios", description="Horarios de apertura"),
            make_coverage("precios", TopicCoverageStatus.PARTIAL, label="Precios", description="Precios y tarifas"),
        ]
        groups = [make_group("¿Tenéis parking?", count=2)]
        result = generate_recommendations(bot, coverages, groups)
        db.close()

        # Missing
        rec_missing = result[0]
        assert rec_missing.title == "Añade información sobre horarios"
        assert "horarios de apertura" in rec_missing.reason.lower()

        # Partial
        rec_partial = next(r for r in result if r.type == RecommendationType.PARTIAL_TOPIC)
        assert rec_partial.title == "Mejora la información sobre precios"
        assert "precios y tarifas" in rec_partial.reason.lower()

        # Question
        rec_q = result[-1]
        assert 'Responde a: "¿Tenéis parking?"' in rec_q.title
        assert "2 veces" in rec_q.reason

        print(f"✅ Texts correctos")
    finally:
        cleanup_bot(bot_id)


def test_no_side_effects():
    print("\n" + "=" * 70)
    print("TEST 15: Sin side effects en BD")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("sideeffects")
    try:
        db = SessionLocal()
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        before_count = db.query(Bot).count()

        coverages = [make_coverage("horarios", TopicCoverageStatus.MISSING)]
        groups = [make_group("¿Tenéis parking?", count=2)]
        generate_recommendations(bot, coverages, groups)

        after_count = db.query(Bot).count()
        db.close()

        assert before_count == after_count
        print(f"✅ Sin side effects")
    finally:
        cleanup_bot(bot_id)


def test_mixed_scenario():
    print("\n" + "=" * 70)
    print("TEST 16: Escenario completo (los 3 tipos)")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("mixed")
    try:
        db = SessionLocal()
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        coverages = [
            make_coverage("horarios", TopicCoverageStatus.MISSING),
            make_coverage("precios", TopicCoverageStatus.PARTIAL),
        ]
        groups = [
            make_group("¿Tenéis parking?", count=5),     # critical
            make_group("¿Aceptáis mascotas?", count=2),  # normal
        ]
        result = generate_recommendations(bot, coverages, groups)
        db.close()

        assert len(result) == 4
        # Orden: missing → freq(5) → partial → freq(2)
        assert result[0].type == RecommendationType.MISSING_TOPIC
        assert result[1].type == RecommendationType.FREQUENT_QUESTION
        assert result[1].action_payload["count"] == 5
        assert result[2].type == RecommendationType.PARTIAL_TOPIC
        assert result[3].type == RecommendationType.FREQUENT_QUESTION
        assert result[3].action_payload["count"] == 2

        print(f"✅ Orden correcto: missing → freq(5) → partial → freq(2)")
    finally:
        cleanup_bot(bot_id)


def test_multiple_missing_topics_order_stable():
    print("\n" + "=" * 70)
    print("TEST 17: Múltiples missing ordenados por topic_id")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("multi_missing")
    try:
        db = SessionLocal()
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        coverages = [
            make_coverage("zeta", TopicCoverageStatus.MISSING),
            make_coverage("alpha", TopicCoverageStatus.MISSING),
            make_coverage("beta", TopicCoverageStatus.MISSING),
        ]
        result = generate_recommendations(bot, coverages, [])
        db.close()

        ids = [r.action_payload["topic_id"] for r in result]
        assert ids == ["alpha", "beta", "zeta"], f"Orden incorrecto: {ids}"
        print(f"✅ Orden estable: {ids}")
    finally:
        cleanup_bot(bot_id)


def test_performance():
    print("\n" + "=" * 70)
    print("TEST 18: Rendimiento (informativo)")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("perf")
    try:
        db = SessionLocal()
        bot = db.query(Bot).filter(Bot.id == bot_id).first()

        # 20 missing + 20 partial + 30 questions
        coverages = (
            [make_coverage(f"missing_{i}", TopicCoverageStatus.MISSING) for i in range(20)] +
            [make_coverage(f"partial_{i}", TopicCoverageStatus.PARTIAL) for i in range(20)]
        )
        groups = [
            make_group(f"¿Pregunta {i}?", count=(i % 10) + 1)
            for i in range(30)
        ]

        start = time.monotonic()
        result = generate_recommendations(bot, coverages, groups)
        elapsed_ms = int((time.monotonic() - start) * 1000)
        db.close()

        print(f"✅ {len(result)} recs generadas en {elapsed_ms} ms")
        print(f"   (input: {len(coverages)} coverages + {len(groups)} groups)")

    finally:
        cleanup_bot(bot_id)


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.4.5 (Recommendation Engine)")
    print("=" * 70)

    tests = [
        test_no_data,
        test_missing_topic_generates_rec,
        test_partial_topic_generates_rec,
        test_frequent_question_generates_rec,
        test_single_question_no_rec,
        test_ordering_missing_first,
        test_ordering_frequent_questions_by_count,
        test_ordering_critical_questions_before_partial,
        test_max_recommendations_limit,
        test_rec_id_is_deterministic,
        test_rec_id_unique,
        test_action_payload_missing_topic,
        test_action_payload_frequent_question,
        test_recommendation_title_and_reason,
        test_no_side_effects,
        test_mixed_scenario,
        test_multiple_missing_topics_order_stable,
        test_performance,
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
