"""
Tests — Subfase 14.3.6
Verifica la integración del Orchestrator con HybridRetriever
y el fix de umbrales por tipo de item en ResponseBuilder.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.config import SessionLocal
from app.models.db_models import (
    Bot, User, Source, SourceChunk, Memory, Conversation,
)
from app.core.contracts import ChannelRequest
from app.core.orchestrator import Orchestrator
from app.core.indexing import invalidate_index, invalidate_all_indexes


# ============================================================
# HELPERS
# ============================================================

def setup_test_user_bot(suffix: str) -> tuple[int, int]:
    db = SessionLocal()
    try:
        from app.services.auth import get_password_hash

        email = f"test_orch_{suffix}@nuvora.com"
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                hashed_password=get_password_hash("123456"),
                full_name=f"Test Orch {suffix}",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        bot_name = f"Bot Orch {suffix}"
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

        invalidate_index(bot_id)
    finally:
        db.close()


def set_answer_mode(bot_id: int, mode: str):
    db = SessionLocal()
    try:
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        bot.answer_mode = mode
        db.commit()
    finally:
        db.close()


def set_bot_active(bot_id: int, active: bool):
    db = SessionLocal()
    try:
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        bot.is_active = active
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
        invalidate_index(bot_id)
    finally:
        db.close()


def _process(bot_id: int, question: str, session_id: str = "test_session"):
    """Helper: procesa un mensaje y devuelve la ChannelResponse."""
    db = SessionLocal()
    try:
        orch = Orchestrator(db)
        req = ChannelRequest(
            bot_id=bot_id,
            message=question,
            session_id=session_id,
            channel="test",
        )
        return orch.process(req)
    finally:
        db.close()


# ============================================================
# TESTS — COMPATIBILIDAD SOLO-MEMORIA (REGRESIÓN)
# ============================================================

def test_only_memory_regression():
    print("\n" + "=" * 70)
    print("TEST 1: REGRESIÓN — Bot solo-memoria")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("onlymem")
    try:
        add_memory(bot_id, "Abrimos de 9:00 a 18:00", "abrimos")
        add_memory(bot_id, "Aceptamos reservas por teléfono", "reservas")

        resp = _process(bot_id, "reservas")
        assert resp.found is True
        assert "reservas" in (resp.answer or "").lower()
        print(f"✅ Respuesta: '{resp.answer[:60]}...'")
        print(f"✅ metadata: {resp.metadata}")
    finally:
        cleanup_bot(bot_id)


def test_only_memory_no_source_hits():
    print("\n" + "=" * 70)
    print("TEST 2: REGRESIÓN — Sin source_hits en bot solo-memoria")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("nosrc")
    try:
        add_memory(bot_id, "Abrimos de 9:00 a 18:00", "abrimos")

        resp = _process(bot_id, "abrimos")
        assert resp.found is True
        assert "9:00" in (resp.answer or "")
        print(f"✅ Respuesta desde memory: '{resp.answer[:60]}'")
    finally:
        cleanup_bot(bot_id)


# ============================================================
# TESTS — SOLO SOURCES
# ============================================================

def test_only_sources():
    print("\n" + "=" * 70)
    print("TEST 3: Bot solo-fuentes responde desde source_chunks")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("onlysrc")
    try:
        add_source_with_chunks(bot_id, user_id, "Info", [
            "Tenemos terraza en la azotea con vistas",
            "Abrimos los domingos hasta las 20:00",
        ])

        resp = _process(bot_id, "terraza")
        assert resp.found is True
        assert "terraza" in (resp.answer or "").lower()
        print(f"✅ Respuesta desde source: '{resp.answer[:60]}'")
    finally:
        cleanup_bot(bot_id)


# ============================================================
# TESTS — MIXED
# ============================================================

def test_mixed_memory_and_sources():
    print("\n" + "=" * 70)
    print("TEST 4: Bot mixto (memorias + fuentes)")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("mixed")
    try:
        add_memory(bot_id, "Abrimos de 9:00 a 18:00", "abrimos")
        add_source_with_chunks(bot_id, user_id, "Info", [
            "Abrimos también los festivos de 10:00 a 14:00",
        ])

        resp1 = _process(bot_id, "abrimos")
        assert resp1.found is True
        print(f"✅ Query 'abrimos' → '{resp1.answer[:60]}'")

        resp2 = _process(bot_id, "festivos")
        assert resp2.found is True
        assert "festivos" in (resp2.answer or "").lower()
        print(f"✅ Query 'festivos' → '{resp2.answer[:60]}'")
    finally:
        cleanup_bot(bot_id)


# ============================================================
# TESTS — STRICT / FLEXIBLE / FALLBACK
# ============================================================

def test_strict_mode_fallback():
    print("\n" + "=" * 70)
    print("TEST 5: Modo strict → fallback si score bajo")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("strict")
    try:
        add_memory(bot_id, "Abrimos de 9:00 a 18:00", "abrimos")
        set_answer_mode(bot_id, "strict")

        resp = _process(bot_id, "física cuántica termodinámica")
        assert resp.found is False
        assert "no tengo" in (resp.answer or "").lower() or "contactar" in (resp.answer or "").lower()
        print(f"✅ Fallback: '{resp.answer[:60]}'")
    finally:
        cleanup_bot(bot_id)


def test_flexible_mode():
    print("\n" + "=" * 70)
    print("TEST 6: Modo flexible → responde aunque score bajo")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("flex")
    try:
        add_memory(bot_id, "Abrimos de 9:00 a 18:00", "abrimos")
        set_answer_mode(bot_id, "flexible")

        resp = _process(bot_id, "abrimos")
        assert resp.found is True
        print(f"✅ Flexible respondió: '{resp.answer[:60]}'")
    finally:
        cleanup_bot(bot_id)


def test_fallback_default():
    print("\n" + "=" * 70)
    print("TEST 7: Fallback con bot sin conocimiento")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("nokb")
    try:
        resp = _process(bot_id, "cualquier cosa")
        assert resp.found is False
        print(f"✅ Fallback: '{resp.answer[:60]}'")
    finally:
        cleanup_bot(bot_id)


# ============================================================
# TESTS — MULTI-TENANT
# ============================================================

def test_multitenant_isolation():
    print("\n" + "=" * 70)
    print("TEST 8: Aislamiento multi-tenant")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot1_id = setup_test_user_bot("mt1")
    _, bot2_id = setup_test_user_bot("mt2")
    try:
        add_memory(bot1_id, "Secreto confidencial de bot1", "secreto")
        add_source_with_chunks(bot2_id, user_id, "Bot2", ["Publico de bot2"])

        resp1 = _process(bot1_id, "publico")
        assert "publico" not in (resp1.answer or "").lower()
        print(f"✅ Bot1 no ve contenido de bot2")

        resp2 = _process(bot2_id, "secreto")
        assert "secreto" not in (resp2.answer or "").lower()
        print(f"✅ Bot2 no ve contenido de bot1")
    finally:
        cleanup_bot(bot1_id)
        cleanup_bot(bot2_id)


# ============================================================
# TESTS — CONVERSACIÓN GUARDADA
# ============================================================

def test_conversation_saved():
    print("\n" + "=" * 70)
    print("TEST 9: Se guarda la conversación en BD")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("conv")
    try:
        add_memory(bot_id, "Abrimos de 9:00 a 18:00", "abrimos")

        db = SessionLocal()
        before = db.query(Conversation).filter(Conversation.bot_id == bot_id).count()
        db.close()

        resp = _process(bot_id, "abrimos", session_id="test_sess_1")
        assert resp.found is True

        db = SessionLocal()
        after = db.query(Conversation).filter(Conversation.bot_id == bot_id).count()
        last = (
            db.query(Conversation)
            .filter(Conversation.bot_id == bot_id)
            .order_by(Conversation.id.desc())
            .first()
        )
        db.close()

        assert after == before + 1
        assert last.session_id == "test_sess_1"
        assert last.was_answered is True
        print(f"✅ Conversación guardada: id={last.id}, session={last.session_id}")
    finally:
        cleanup_bot(bot_id)


# ============================================================
# TESTS — BOT INACTIVO / NO ENCONTRADO
# ============================================================

def test_bot_inactive():
    print("\n" + "=" * 70)
    print("TEST 10: Bot inactivo → no responde")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("inactive")
    try:
        add_memory(bot_id, "Abrimos de 9:00 a 18:00", "abrimos")
        set_bot_active(bot_id, False)

        resp = _process(bot_id, "abrimos")
        assert resp.found is False
        print(f"✅ Bot inactivo → '{resp.answer[:60]}'")
    finally:
        cleanup_bot(bot_id)


def test_bot_not_found():
    print("\n" + "=" * 70)
    print("TEST 11: Bot inexistente → error controlado")
    print("=" * 70)
    invalidate_all_indexes()

    resp = _process(99999, "cualquier cosa")
    assert resp.found is False
    print(f"✅ Bot no encontrado → '{resp.answer[:60]}'")


# ============================================================
# TESTS — UMBRALES POR TIPO DE ITEM (fix 14.3.6)
# ============================================================

def test_source_score_above_threshold_strict():
    """
    Source con score > 0.05 debe ser aceptado en modo strict.
    (Antes del fix: rechazado porque el umbral era 2.0)
    """
    print("\n" + "=" * 70)
    print("TEST 12: Source con score > 0.05 en strict → responde")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("src_strict")
    try:
        add_source_with_chunks(bot_id, user_id, "Info", [
            "Tenemos terraza en la azotea con vistas",
        ])
        set_answer_mode(bot_id, "strict")

        resp = _process(bot_id, "terraza")
        assert resp.found is True, f"Debería responder desde source. Resp: {resp}"
        assert "terraza" in (resp.answer or "").lower()
        print(f"✅ Respuesta: '{resp.answer[:60]}'")
    finally:
        cleanup_bot(bot_id)


def test_mixed_memory_below_threshold_is_rejected():
    """
    Mixed: memory con keyword poco relacionada + source con match claro.
    El mejor item es la source → debe responder desde source.
    """
    print("\n" + "=" * 70)
    print("TEST 13: Mixed — mejor item es source → responde")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("mixed_reject")
    try:
        add_memory(bot_id, "Algo sin relación", "xyz")
        add_source_with_chunks(bot_id, user_id, "Info", [
            "Tenemos terraza en la azotea con vistas",
        ])
        set_answer_mode(bot_id, "strict")

        resp = _process(bot_id, "terraza")
        assert resp.found is True, "Debería responder desde source"
        assert "terraza" in (resp.answer or "").lower()
        print(f"✅ Respuesta desde source: '{resp.answer[:60]}'")
        print(f"   metadata: {resp.metadata}")
    finally:
        cleanup_bot(bot_id)


def test_mixed_best_item_is_memory_low_score():
    """
    Mixed: memory con score bajo + source con score bajo.
    Si el mejor item es memory con score < 2.0 → debe hacer fallback.
    """
    print("\n" + "=" * 70)
    print("TEST 14: Mixed — memory score bajo + source score bajo → fallback")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("mixed_15")
    try:
        add_memory(bot_id, "Algo ambiguo", "ab")
        add_source_with_chunks(bot_id, user_id, "Info", [
            "Abrimos los sábados y domingos",
        ])
        set_answer_mode(bot_id, "strict")

        resp = _process(bot_id, "abrimos")
        print(f"   Respuesta: '{resp.answer[:80]}'")
        print(f"   found={resp.found}")
        print(f"   metadata={resp.metadata}")

        if resp.found:
            # Si se acepta, debe ser porque el mejor item (memory) tiene score >= 2.0
            assert resp.metadata.get("best_item_type") == "memory"
            assert resp.metadata.get("confidence", 0) >= 2.0
            print(f"✅ Aceptado porque memory score >= 2.0")
        else:
            print(f"✅ Rechazado correctamente (mejor item score < umbral)")
    finally:
        cleanup_bot(bot_id)


def test_source_score_below_threshold_strict():
    """
    Source con score < 0.05 → fallback en strict.
    """
    print("\n" + "=" * 70)
    print("TEST 15: Source con score muy bajo → fallback")
    print("=" * 70)
    invalidate_all_indexes()

    user_id, bot_id = setup_test_user_bot("src_below")
    try:
        add_source_with_chunks(bot_id, user_id, "Info", [
            "Tenemos terraza en la azotea con vistas",
        ])
        set_answer_mode(bot_id, "strict")

        resp = _process(bot_id, "física cuántica termodinámica")
        assert resp.found is False
        print(f"✅ Fallback: '{resp.answer[:60]}'")
    finally:
        cleanup_bot(bot_id)


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.3.6 (Orchestrator + HybridRetriever)")
    print("=" * 70)

    tests = [
        test_only_memory_regression,
        test_only_memory_no_source_hits,
        test_only_sources,
        test_mixed_memory_and_sources,
        test_strict_mode_fallback,
        test_flexible_mode,
        test_fallback_default,
        test_multitenant_isolation,
        test_conversation_saved,
        test_bot_inactive,
        test_bot_not_found,
        # Fix 14.3.6: umbrales por tipo de item
        test_source_score_above_threshold_strict,
        test_mixed_memory_below_threshold_is_rejected,
        test_mixed_best_item_is_memory_low_score,
        test_source_score_below_threshold_strict,
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
