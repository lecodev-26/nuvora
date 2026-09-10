"""
Tests — Subfase 14.4.4
Verifica Unanswered Questions (Jaccard + agrupación).
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.config import SessionLocal
from app.models.db_models import Bot, User, Conversation
from app.core.training.questions import (
    jaccard_similarity,
    get_unanswered_question_groups,
    JACCARD_THRESHOLD,
    MIN_TOKENS_VALIDOS,
)
from app.core.indexing import tokenize


# ============================================================
# HELPERS
# ============================================================

def setup_test_user_bot(suffix: str) -> tuple[int, int]:
    db = SessionLocal()
    try:
        from app.services.auth import get_password_hash

        email = f"test_q_{suffix}@nuvora.com"
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                hashed_password=get_password_hash("123456"),
                full_name=f"Test Q {suffix}",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        bot_name = f"Bot Q {suffix}"
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


def add_conversation(bot_id: int, question: str, was_answered: bool = False):
    db = SessionLocal()
    try:
        c = Conversation(
            bot_id=bot_id,
            channel="test",
            question=question,
            was_answered=was_answered,
        )
        db.add(c)
        db.commit()
        db.refresh(c)
        return c.id
    finally:
        db.close()


def cleanup_bot(bot_id: int):
    db = SessionLocal()
    try:
        db.query(Conversation).filter(Conversation.bot_id == bot_id).delete(synchronize_session=False)
        db.query(Bot).filter(Bot.id == bot_id).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


# ============================================================
# TESTS — jaccard_similarity()
# ============================================================

def test_jaccard_identical():
    print("\n" + "=" * 70)
    print("TEST 1: Jaccard(A, A) = 1.0")
    print("=" * 70)
    a = {"horario", "abrimos"}
    assert jaccard_similarity(a, a) == 1.0
    print(f"✅ 1.0")


def test_jaccard_disjoint():
    print("\n" + "=" * 70)
    print("TEST 2: Jaccard(A, B) = 0.0 si disjuntos")
    print("=" * 70)
    a = {"horario", "abrimos"}
    b = {"terraza", "parking"}
    assert jaccard_similarity(a, b) == 0.0
    print(f"✅ 0.0")


def test_jaccard_partial():
    print("\n" + "=" * 70)
    print("TEST 3: Jaccard parcial")
    print("=" * 70)
    a = {"horario", "abrimos", "lunes"}
    b = {"horario", "abrimos", "domingo"}
    sim = jaccard_similarity(a, b)
    assert abs(sim - 0.5) < 0.001
    print(f"✅ Jaccard={sim:.3f}")


def test_jaccard_empty():
    print("\n" + "=" * 70)
    print("TEST 4: Jaccard con conjunto vacío = 0.0")
    print("=" * 70)
    assert jaccard_similarity(set(), {"a"}) == 0.0
    assert jaccard_similarity({"a"}, set()) == 0.0
    assert jaccard_similarity(set(), set()) == 0.0
    print(f"✅ 0.0")


def test_jaccard_uses_tokenize():
    print("\n" + "=" * 70)
    print("TEST 5: Jaccard usa tokenize() de indexing.py")
    print("=" * 70)
    q1 = "¿Tenéis parking?"
    q2 = "TENEIS PARKING"

    t1 = set(tokenize(q1))
    t2 = set(tokenize(q2))

    assert t1 == t2, f"tokenize() inconsistente: {t1} vs {t2}"
    sim = jaccard_similarity(t1, t2)
    assert sim == 1.0
    print(f"✅ tokenize() consistente: {t1}, Jaccard={sim}")


# ============================================================
# TESTS — get_unanswered_question_groups()
# ============================================================

def test_no_conversations():
    print("\n" + "=" * 70)
    print("TEST 6: Sin conversaciones → []")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("no_conv")
    try:
        db = SessionLocal()
        result = get_unanswered_question_groups(bot_id, db)
        db.close()
        assert result == []
        print(f"✅ []")
    finally:
        cleanup_bot(bot_id)


def test_all_answered():
    print("\n" + "=" * 70)
    print("TEST 7: Todas respondidas → []")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("all_ans")
    try:
        add_conversation(bot_id, "¿A qué hora abrís?", was_answered=True)
        add_conversation(bot_id, "¿Tenéis parking?", was_answered=True)

        db = SessionLocal()
        result = get_unanswered_question_groups(bot_id, db)
        db.close()
        assert result == []
        print(f"✅ []")
    finally:
        cleanup_bot(bot_id)


def test_one_unanswered():
    print("\n" + "=" * 70)
    print("TEST 8: 1 pregunta sin responder → 1 grupo")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("one")
    try:
        add_conversation(bot_id, "¿Tenéis parking?")

        db = SessionLocal()
        result = get_unanswered_question_groups(bot_id, db)
        db.close()

        assert len(result) == 1
        assert result[0].count == 1
        assert result[0].representative == "¿Tenéis parking?"
        assert len(result[0].conversation_ids) == 1
        print(f"✅ 1 grupo: '{result[0].representative}' count={result[0].count}")
    finally:
        cleanup_bot(bot_id)


def test_identical_questions():
    print("\n" + "=" * 70)
    print("TEST 9: 3 idénticas → 1 grupo con count=3")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("identical")
    try:
        add_conversation(bot_id, "¿Tenéis parking?")
        add_conversation(bot_id, "¿Tenéis parking?")
        add_conversation(bot_id, "¿Tenéis parking?")

        db = SessionLocal()
        result = get_unanswered_question_groups(bot_id, db)
        db.close()

        assert len(result) == 1
        assert result[0].count == 3
        assert len(result[0].variants) == 1
        assert result[0].representative == "¿Tenéis parking?"
        print(f"✅ 1 grupo: count=3, variants=1")
    finally:
        cleanup_bot(bot_id)


def test_similar_questions_grouped():
    print("\n" + "=" * 70)
    print("TEST 10: Preguntas similares (Jaccard >= 0.5) → agrupadas")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("similar")
    try:
        t1 = set(tokenize("¿Tenéis parking?"))
        t2 = set(tokenize("¿Tenéis parking gratis?"))
        sim = jaccard_similarity(t1, t2)
        assert sim >= JACCARD_THRESHOLD, f"Setup del test inválido: Jaccard={sim}"

        add_conversation(bot_id, "¿Tenéis parking?")
        add_conversation(bot_id, "¿Tenéis parking gratis?")
        add_conversation(bot_id, "¿Tenéis parking?")

        db = SessionLocal()
        result = get_unanswered_question_groups(bot_id, db)
        db.close()

        assert len(result) == 1, f"Esperado 1 grupo, obtenido {len(result)}"
        assert result[0].count == 3
        assert result[0].representative == "¿Tenéis parking?"
        assert len(result[0].variants) == 2
        print(f"✅ 1 grupo: count=3, variants=2, Jaccard={sim:.3f}")
    finally:
        cleanup_bot(bot_id)


def test_jaccard_limitation_synonyms():
    """
    TEST 10b: Documenta la limitación del Jaccard MVP con sinónimos.

    "¿Tenéis parking?" vs "¿Disponéis aparcamiento?" son semánticamente
    equivalentes, pero sus tokens no se solapan porque usan sinónimos.

    El test calcula tokens y Jaccard con las funciones reales, sin asumir.
    """
    print("\n" + "=" * 70)
    print("TEST 10b: Limitación Jaccard con sinónimos (documentada)")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("jaccard_limit")
    try:
        q1 = "¿Tenéis parking?"
        q2 = "¿Disponéis aparcamiento?"

        t1 = set(tokenize(q1))
        t2 = set(tokenize(q2))

        print(f"   tokenize('{q1}') → {sorted(t1)}")
        print(f"   tokenize('{q2}') → {sorted(t2)}")

        # Ambas deben tener >= MIN_TOKENS_VALIDOS para no ser ignoradas
        assert len(t1) >= MIN_TOKENS_VALIDOS, (
            f"'{q1}' produce {len(t1)} tokens (< {MIN_TOKENS_VALIDOS}). "
            f"Elegir otra pregunta."
        )
        assert len(t2) >= MIN_TOKENS_VALIDOS, (
            f"'{q2}' produce {len(t2)} tokens (< {MIN_TOKENS_VALIDOS}). "
            f"Elegir otra pregunta."
        )

        sim = jaccard_similarity(t1, t2)
        print(f"   Jaccard = {sim:.3f} (umbral = {JACCARD_THRESHOLD})")

        assert sim < JACCARD_THRESHOLD, (
            f"Jaccard esperado < {JACCARD_THRESHOLD}, obtenido {sim}"
        )

        add_conversation(bot_id, q1)
        add_conversation(bot_id, q2)

        db = SessionLocal()
        result = get_unanswered_question_groups(bot_id, db)
        db.close()

        assert len(result) == 2, (
            f"Limitación conocida: Jaccard={sim:.3f} < {JACCARD_THRESHOLD} → 2 grupos. "
            f"Recibido: {len(result)} grupos"
        )
        print(f"✅ Limitación documentada: 2 grupos separados")
        print(f"   Se resolverá en Fase 15 con embeddings semánticos.")
    finally:
        cleanup_bot(bot_id)


def test_different_questions_separate():
    print("\n" + "=" * 70)
    print("TEST 11: Preguntas distintas → grupos separados")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("different")
    try:
        add_conversation(bot_id, "¿Tenéis parking?")
        add_conversation(bot_id, "¿Cuánto cuesta el menú?")
        add_conversation(bot_id, "¿Aceptáis mascotas?")

        db = SessionLocal()
        result = get_unanswered_question_groups(bot_id, db)
        db.close()

        assert len(result) == 3
        print(f"✅ 3 grupos distintos")
    finally:
        cleanup_bot(bot_id)


def test_short_questions_ignored():
    print("\n" + "=" * 70)
    print("TEST 12: Preguntas triviales (<2 tokens) → ignoradas")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("short")
    try:
        add_conversation(bot_id, "?")
        add_conversation(bot_id, "hola")
        add_conversation(bot_id, "ok")
        add_conversation(bot_id, "¿Tenéis parking?")

        db = SessionLocal()
        result = get_unanswered_question_groups(bot_id, db)
        db.close()

        assert len(result) == 1
        assert result[0].representative == "¿Tenéis parking?"
        print(f"✅ Solo 1 grupo (las triviales ignoradas)")
    finally:
        cleanup_bot(bot_id)


def test_multitenant_isolation():
    print("\n" + "=" * 70)
    print("TEST 13: Aislamiento multi-tenant")
    print("=" * 70)
    user1, bot1 = setup_test_user_bot("mt1")
    user2, bot2 = setup_test_user_bot("mt2")
    try:
        add_conversation(bot1, "¿Tenéis parking?")
        add_conversation(bot2, "¿Cuánto cuesta el menú?")

        db = SessionLocal()
        result1 = get_unanswered_question_groups(bot1, db)
        result2 = get_unanswered_question_groups(bot2, db)
        db.close()

        assert len(result1) == 1
        assert result1[0].representative == "¿Tenéis parking?"
        assert len(result2) == 1
        assert result2[0].representative == "¿Cuánto cuesta el menú?"
        print(f"✅ Cada bot ve solo sus conversaciones")
    finally:
        cleanup_bot(bot1)
        cleanup_bot(bot2)


def test_limit_respected():
    print("\n" + "=" * 70)
    print("TEST 14: Se respeta limit")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("limit")
    try:
        for i in range(5):
            add_conversation(bot_id, f"Pregunta {i} sobre servicios")

        db = SessionLocal()
        result = get_unanswered_question_groups(bot_id, db, limit=2)
        db.close()

        total_convs = sum(g.count for g in result)
        assert total_convs == 2
        print(f"✅ limit=2 → {total_convs} conversaciones analizadas")
    finally:
        cleanup_bot(bot_id)


def test_limit_zero():
    print("\n" + "=" * 70)
    print("TEST 15: limit=0 → []")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("limit0")
    try:
        add_conversation(bot_id, "¿Tenéis parking?")

        db = SessionLocal()
        result = get_unanswered_question_groups(bot_id, db, limit=0)
        db.close()
        assert result == []
        print(f"✅ []")
    finally:
        cleanup_bot(bot_id)


def test_limit_negative():
    print("\n" + "=" * 70)
    print("TEST 16: limit<0 → []")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("limit_neg")
    try:
        add_conversation(bot_id, "¿Tenéis parking?")

        db = SessionLocal()
        result = get_unanswered_question_groups(bot_id, db, limit=-5)
        db.close()
        assert result == []
        print(f"✅ []")
    finally:
        cleanup_bot(bot_id)


def test_ordering_by_count():
    print("\n" + "=" * 70)
    print("TEST 17: Grupos ordenados por count DESC")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("order")
    try:
        add_conversation(bot_id, "¿Tenéis terraza?")
        add_conversation(bot_id, "¿Cuánto cuesta el menú?")
        add_conversation(bot_id, "¿Cuánto cuesta el menú?")
        add_conversation(bot_id, "¿Cuánto cuesta el menú?")

        db = SessionLocal()
        result = get_unanswered_question_groups(bot_id, db)
        db.close()

        assert len(result) == 2
        assert result[0].count >= result[1].count
        assert result[0].count == 3
        print(f"✅ Ordenado: count1={result[0].count}, count2={result[1].count}")
    finally:
        cleanup_bot(bot_id)


def test_representative_most_frequent():
    print("\n" + "=" * 70)
    print("TEST 18: Representante = más frecuente textual")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("rep")
    try:
        add_conversation(bot_id, "¿Tenéis parking gratis?")
        add_conversation(bot_id, "¿Tenéis parking?")
        add_conversation(bot_id, "¿Tenéis parking?")

        db = SessionLocal()
        result = get_unanswered_question_groups(bot_id, db)
        db.close()

        assert len(result) == 1
        assert result[0].representative == "¿Tenéis parking?"
        print(f"✅ Representative: '{result[0].representative}'")
    finally:
        cleanup_bot(bot_id)


def test_representative_tie_shortest():
    print("\n" + "=" * 70)
    print("TEST 19: Empate en representante → la más corta")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("tie")
    try:
        add_conversation(bot_id, "¿Tenéis parking ya?")
        add_conversation(bot_id, "¿Tenéis parking?")

        db = SessionLocal()
        result = get_unanswered_question_groups(bot_id, db)
        db.close()

        assert len(result) == 1
        assert result[0].representative == "¿Tenéis parking?"
        print(f"✅ Tie → más corta: '{result[0].representative}'")
    finally:
        cleanup_bot(bot_id)


def test_variants_deduplicated():
    print("\n" + "=" * 70)
    print("TEST 20: Variants sin duplicados textuales")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("variants")
    try:
        add_conversation(bot_id, "¿Tenéis parking?")
        add_conversation(bot_id, "¿Tenéis parking?")
        add_conversation(bot_id, "¿Tenéis parking gratis?")

        db = SessionLocal()
        result = get_unanswered_question_groups(bot_id, db)
        db.close()

        assert len(result) == 1
        assert len(result[0].variants) == 2
        assert "¿Tenéis parking?" in result[0].variants
        assert "¿Tenéis parking gratis?" in result[0].variants
        print(f"✅ Variants: {result[0].variants}")
    finally:
        cleanup_bot(bot_id)


def test_conversation_ids_complete():
    print("\n" + "=" * 70)
    print("TEST 21: conversation_ids incluye todas (con duplicados)")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("ids")
    try:
        cid1 = add_conversation(bot_id, "¿Tenéis parking?")
        cid2 = add_conversation(bot_id, "¿Tenéis parking?")
        cid3 = add_conversation(bot_id, "¿Tenéis parking gratis?")

        db = SessionLocal()
        result = get_unanswered_question_groups(bot_id, db)
        db.close()

        assert len(result) == 1
        ids = sorted(result[0].conversation_ids)
        assert ids == sorted([cid1, cid2, cid3])
        print(f"✅ {len(ids)} IDs: {ids}")
    finally:
        cleanup_bot(bot_id)


def test_no_side_effects():
    print("\n" + "=" * 70)
    print("TEST 22: NO modifica la BD")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("nowrite")
    try:
        add_conversation(bot_id, "¿Tenéis parking?")

        db = SessionLocal()
        before = db.query(Conversation).count()
        db.close()

        db = SessionLocal()
        get_unanswered_question_groups(bot_id, db)
        db.close()

        db = SessionLocal()
        after = db.query(Conversation).count()
        db.close()

        assert before == after
        print(f"✅ Sin side effects: conversations={after}")
    finally:
        cleanup_bot(bot_id)


# ============================================================
# TEST DE RENDIMIENTO
# ============================================================

def test_performance_100_conversations():
    print("\n" + "=" * 70)
    print("TEST 23: Rendimiento con 100 conversaciones (informativo)")
    print("=" * 70)
    user_id, bot_id = setup_test_user_bot("perf")

    try:
        unique_questions = [
            "¿Tenéis parking?",
            "¿Cuánto cuesta el menú del día?",
            "¿Aceptáis mascotas en la terraza?",
            "¿A qué hora abrís los domingos?",
            "¿Hacéis reservas para grupos grandes?",
            "¿Tenéis opciones vegetarianas en el menú?",
            "¿Dónde estáis ubicados exactamente?",
            "¿Cuál es vuestro número de teléfono?",
            "¿Tenéis terraza en la azotea?",
            "¿Aceptáis pago con tarjeta?",
        ]

        for q in unique_questions:
            add_conversation(bot_id, q)
        for i in range(90):
            add_conversation(bot_id, unique_questions[i % 10])

        db = SessionLocal()
        start = time.monotonic()
        result = get_unanswered_question_groups(bot_id, db, limit=100)
        elapsed_ms = int((time.monotonic() - start) * 1000)
        db.close()

        total_convs = sum(g.count for g in result)
        print(f"✅ 100 conversaciones → {len(result)} grupos, {total_convs} conversaciones agrupadas")
        print(f"   Tiempo: {elapsed_ms} ms")

    finally:
        cleanup_bot(bot_id)


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.4.4 (Unanswered Questions)")
    print("=" * 70)

    tests = [
        test_jaccard_identical,
        test_jaccard_disjoint,
        test_jaccard_partial,
        test_jaccard_empty,
        test_jaccard_uses_tokenize,
        test_no_conversations,
        test_all_answered,
        test_one_unanswered,
        test_identical_questions,
        test_similar_questions_grouped,
        test_jaccard_limitation_synonyms,
        test_different_questions_separate,
        test_short_questions_ignored,
        test_multitenant_isolation,
        test_limit_respected,
        test_limit_zero,
        test_limit_negative,
        test_ordering_by_count,
        test_representative_most_frequent,
        test_representative_tie_shortest,
        test_variants_deduplicated,
        test_conversation_ids_complete,
        test_no_side_effects,
        test_performance_100_conversations,
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
