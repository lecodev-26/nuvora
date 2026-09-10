"""
Tests — Subfase 14.4.9
Integración end-to-end del Training Assistant.
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.main import app
from app.database.config import SessionLocal
from app.models.db_models import (
    Bot, User, Memory, Source, SourceChunk, Conversation, MemoryCategory,
)
from app.core.training import TrainingAnalyzer
from app.core.training.topics import get_topics_for_nicho
from app.models.training import (
    TopicCoverageStatus,
    RecommendationType,
)
from app.core.indexing import invalidate_all_indexes


client = TestClient(app)


# ============================================================
# HELPERS
# ============================================================

def _unique(suffix: str) -> str:
    return f"{suffix}_{int(time.time() * 1000)}"


def _register_and_login(suffix: str) -> tuple[str, str, int]:
    unique = _unique(suffix)
    email = f"test_int_{unique}@nuvora.com"
    password = "123456"

    r = client.post("/auth/register", json={
        "email": email,
        "password": password,
        "full_name": f"Test Int {unique}",
    })
    assert r.status_code == 200, r.text
    user_id = r.json()["id"]

    r = client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return email, token, user_id


def _create_bot(token: str, name_suffix: str, nicho_id: str = "restaurantes") -> int:
    unique = _unique(name_suffix)
    r = client.post(
        "/bots/",
        json={
            "name": f"Bot Int {unique}",
            "business_name": f"Test {unique}",
            "nicho_id": nicho_id,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _add_memory_direct(bot_id: int, fact: str, keyword: str):
    db = SessionLocal()
    try:
        db.add(Memory(
            bot_id=bot_id,
            fact=fact,
            keyword=keyword.lower(),
            source="manual",
            is_confirmed=True,
        ))
        db.commit()
    finally:
        db.close()


def _add_source_direct(bot_id: int, user_id: int, chunks: list, title: str = "Info"):
    db = SessionLocal()
    try:
        src = Source(
            bot_id=bot_id,
            user_id=user_id,
            type="text",
            title=title,
            content_raw=" ".join(chunks),
            content_processed=" ".join(chunks),
            status="ready",
            chunks_count=len(chunks),
        )
        db.add(src)
        db.commit()
        db.refresh(src)
        for i, text in enumerate(chunks):
            db.add(SourceChunk(
                source_id=src.id,
                bot_id=bot_id,
                chunk_index=i,
                content=text,
            ))
        db.commit()
        invalidate_all_indexes()
    finally:
        db.close()


def _add_conversation_direct(bot_id: int, question: str, was_answered: bool = False):
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


def _cleanup_bot(bot_id: int):
    """
    Limpia todos los datos asociados a un bot, respetando el orden
    para evitar FOREIGN KEY constraint failed.
    Orden: conversations → memories → source_chunks → sources → memory_categories → bot.
    """
    db = SessionLocal()
    try:
        # 1. Conversaciones
        db.query(Conversation).filter(
            Conversation.bot_id == bot_id
        ).delete(synchronize_session=False)

        # 2. Memorias (antes de categorías, porque Memory.category_id es FK)
        db.query(Memory).filter(
            Memory.bot_id == bot_id
        ).delete(synchronize_session=False)

        # 3. Chunks de fuentes (CASCADE lo haría, pero por claridad)
        db.query(SourceChunk).filter(
            SourceChunk.bot_id == bot_id
        ).delete(synchronize_session=False)

        # 4. Fuentes
        db.query(Source).filter(
            Source.bot_id == bot_id
        ).delete(synchronize_session=False)

        # 5. Categorías de memoria (NUEVO)
        db.query(MemoryCategory).filter(
            MemoryCategory.bot_id == bot_id
        ).delete(synchronize_session=False)

        # 6. Bot
        db.query(Bot).filter(
            Bot.id == bot_id
        ).delete(synchronize_session=False)

        db.commit()
        invalidate_all_indexes()
    finally:
        db.close()


def _cleanup_user(email: str):
    db = SessionLocal()
    try:
        db.query(User).filter(User.email == email).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _analyze(bot_id: int):
    db = SessionLocal()
    try:
        analyzer = TrainingAnalyzer(db)
        return analyzer.analyze(bot_id, conversation_limit=100)
    finally:
        db.close()


def _find_topic(report, topic_id: str):
    for t in report.topics:
        if t.topic_id == topic_id:
            return t
    return None


# ============================================================
# 1. INTEGRACIÓN END-TO-END
# ============================================================

def test_full_flow_empty_bot():
    print("\n" + "=" * 70)
    print("TEST 1: Flujo completo con bot vacío")
    print("=" * 70)
    invalidate_all_indexes()
    email, token, user_id = _register_and_login("flow_empty")
    bot_id = _create_bot(token, "flow_empty", nicho_id="restaurantes")
    try:
        report = _analyze(bot_id)
        assert all(t.status == TopicCoverageStatus.MISSING for t in report.topics)
        assert report.progress == 0.0
        assert report.covered_count == 0
        assert report.partial_count == 0
        assert report.missing_count == report.total_topics
        assert report.has_memories is False
        assert report.has_sources is False
        assert len(report.recommendations) > 0
        assert all(
            r.type == RecommendationType.MISSING_TOPIC
            for r in report.recommendations[:5]
        )
        print(f"✅ progress=0, {len(report.recommendations)} recs, "
              f"{report.missing_count}/{report.total_topics} missing")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user(email)


def test_full_flow_with_memory():
    print("\n" + "=" * 70)
    print("TEST 2: Añadir memoria → análisis → topic cambia de estado")
    print("=" * 70)
    invalidate_all_indexes()
    email, token, user_id = _register_and_login("flow_mem")
    bot_id = _create_bot(token, "flow_mem", nicho_id="restaurantes")
    try:
        report_before = _analyze(bot_id)
        horarios_before = _find_topic(report_before, "horarios")
        assert horarios_before is not None
        assert horarios_before.status == TopicCoverageStatus.MISSING
        print(f"   Antes: horarios={horarios_before.status.value}")

        _add_memory_direct(
            bot_id,
            fact="Abrimos de 9:00 a 18:00 de lunes a domingo",
            keyword="horarios",
        )

        report_after = _analyze(bot_id)
        horarios_after = _find_topic(report_after, "horarios")
        assert horarios_after.status != TopicCoverageStatus.MISSING
        assert report_after.memories_count == 1
        print(f"   Después: horarios={horarios_after.status.value} "
              f"(evidence={horarios_after.evidence_count})")
        print(f"✅ El topic cambió de estado tras añadir memoria")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user(email)


def test_full_flow_with_source():
    print("\n" + "=" * 70)
    print("TEST 3: Añadir fuente → análisis → topic cambia de estado")
    print("=" * 70)
    invalidate_all_indexes()
    email, token, user_id = _register_and_login("flow_src")
    bot_id = _create_bot(token, "flow_src", nicho_id="restaurantes")
    try:
        report_before = _analyze(bot_id)
        horarios_before = _find_topic(report_before, "horarios")
        assert horarios_before.status == TopicCoverageStatus.MISSING

        _add_source_direct(bot_id, user_id, [
            "Nuestro horario de apertura es de 9:00 a 18:00 de lunes a domingo.",
            "Los domingos cerramos a las 15:00.",
        ], title="Horarios 2026")

        report_after = _analyze(bot_id)
        horarios_after = _find_topic(report_after, "horarios")
        assert report_after.ready_sources_count == 1
        assert horarios_after.status != TopicCoverageStatus.MISSING
        print(f"   Después: horarios={horarios_after.status.value} "
              f"(evidence={horarios_after.evidence_count})")
        print(f"✅ El topic cambió de estado tras añadir fuente")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user(email)


def test_full_flow_with_conversations():
    print("\n" + "=" * 70)
    print("TEST 4: Conversaciones sin responder → recomendaciones frecuentes")
    print("=" * 70)
    invalidate_all_indexes()
    email, token, user_id = _register_and_login("flow_conv")
    bot_id = _create_bot(token, "flow_conv", nicho_id="otro")
    try:
        all_topics = get_topics_for_nicho("otro")
        total_topics = len(all_topics)
        topics_to_cover = max(0, total_topics - 2)

        print(f"   Catálogo 'otro' tiene {total_topics} topics")
        print(f"   Cubriremos {topics_to_cover} con memorias "
              f"(dejamos {total_topics - topics_to_cover} missing)")

        for t in all_topics[:topics_to_cover]:
            _add_memory_direct(
                bot_id,
                fact=f"Información de {t.label}",
                keyword=t.id,
            )

        _add_conversation_direct(bot_id, "¿Tenéis parking?", was_answered=False)
        _add_conversation_direct(bot_id, "¿Tenéis parking?", was_answered=False)
        _add_conversation_direct(bot_id, "¿Tenéis parking?", was_answered=False)
        _add_conversation_direct(bot_id, "¿A qué hora abrís?", was_answered=True)

        report = _analyze(bot_id)

        group = next(
            (g for g in report.unanswered_questions
             if "parking" in g.representative.lower()),
            None,
        )
        assert group is not None, "No se detectó el grupo de parking"
        assert group.count == 3, f"count esperado 3, obtenido {group.count}"
        print(f"   ✔ Grupo detectado: '{group.representative}' (count={group.count})")

        missing_recs = [
            r for r in report.recommendations
            if r.type == RecommendationType.MISSING_TOPIC
        ]
        assert len(missing_recs) <= 10
        print(f"   ✔ {len(missing_recs)} recomendaciones missing_topic")

        freq_recs = [
            r for r in report.recommendations
            if r.type == RecommendationType.FREQUENT_QUESTION
        ]
        assert len(freq_recs) >= 1, (
            f"Se esperaba frequent_question. "
            f"Tipos obtenidos: {[r.type.value for r in report.recommendations]}"
        )
        assert any("parking" in r.title.lower() for r in freq_recs)
        print(f"   ✔ {len(freq_recs)} recomendación(es) frequent_question")
        print(f"✅ Flujo completo: preguntas sin responder → recomendación frecuente")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user(email)


def test_full_flow_progressive():
    print("\n" + "=" * 70)
    print("TEST 5: Flujo progresivo (bot vacío → añadir info → progreso sube)")
    print("=" * 70)
    invalidate_all_indexes()
    email, token, user_id = _register_and_login("flow_prog")
    bot_id = _create_bot(token, "flow_prog", nicho_id="otro")
    try:
        r0 = _analyze(bot_id)
        assert r0.progress == 0.0
        assert r0.missing_count == r0.total_topics
        print(f"   Inicial: progress={r0.progress}, missing={r0.missing_count}/{r0.total_topics}")

        _add_memory_direct(
            bot_id,
            fact="Abrimos de lunes a domingo de 9:00 a 18:00",
            keyword="horarios",
        )
        r1 = _analyze(bot_id)
        assert r1.progress > r0.progress, "El progreso debería subir"
        assert r1.missing_count < r0.missing_count
        print(f"   Tras 1 memory: progress={r1.progress}, "
              f"covered={r1.covered_count}, partial={r1.partial_count}, "
              f"missing={r1.missing_count}")

        _add_memory_direct(
            bot_id,
            fact="Puedes contactarnos en el 900 123 456",
            keyword="contacto",
        )
        r2 = _analyze(bot_id)
        assert r2.progress >= r1.progress
        print(f"   Tras 2 memories: progress={r2.progress}, missing={r2.missing_count}")

        _add_memory_direct(
            bot_id,
            fact="Estamos en la calle Principal 1",
            keyword="ubicacion",
        )
        r3 = _analyze(bot_id)
        assert r3.progress >= r2.progress
        print(f"   Tras 3 memories: progress={r3.progress}, missing={r3.missing_count}")

        changed = [
            t.topic_id for t in r3.topics
            if t.status != TopicCoverageStatus.MISSING
        ]
        assert len(changed) > 0, "Se esperaba al menos un topic no-MISSING"
        print(f"   Topics no-MISSING: {changed}")
        print(f"✅ Progreso sube progresivamente")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user(email)


# ============================================================
# 2. AISLAMIENTO MULTI-TENANT
# ============================================================

def test_multitenant_analyzer_isolated():
    print("\n" + "=" * 70)
    print("TEST 6: Analyzer de bot A no incluye datos de bot B")
    print("=" * 70)
    invalidate_all_indexes()
    email_a, token_a, user_a = _register_and_login("mt_analyzer_a")
    email_b, token_b, user_b = _register_and_login("mt_analyzer_b")
    bot_a = _create_bot(token_a, "mt_a", nicho_id="otro")
    bot_b = _create_bot(token_b, "mt_b", nicho_id="otro")
    try:
        _add_memory_direct(bot_a, "Abrimos A a las 9:00", "horarios")
        _add_memory_direct(bot_a, "Contacto A: 111", "contacto")
        _add_memory_direct(bot_b, "Abrimos B a las 10:00", "horarios")
        _add_memory_direct(bot_b, "Contacto B: 222", "contacto")
        _add_memory_direct(bot_b, "Ubicación B", "ubicacion")

        report_a = _analyze(bot_a)
        report_b = _analyze(bot_b)

        assert report_a.memories_count == 2
        assert report_b.memories_count == 3

        db = SessionLocal()
        mems_a = db.query(Memory).filter(Memory.bot_id == bot_a).all()
        mems_b = db.query(Memory).filter(Memory.bot_id == bot_b).all()
        db.close()

        facts_a = {m.fact for m in mems_a}
        facts_b = {m.fact for m in mems_b}
        assert "Abrimos A a las 9:00" in facts_a
        assert "Abrimos A a las 9:00" not in facts_b
        assert "Abrimos B a las 10:00" in facts_b
        assert "Abrimos B a las 10:00" not in facts_a

        print(f"✅ Aislamiento confirmado: A={len(facts_a)} mems, B={len(facts_b)} mems")
    finally:
        _cleanup_bot(bot_a)
        _cleanup_bot(bot_b)
        _cleanup_user(email_a)
        _cleanup_user(email_b)


def test_multitenant_coverage_isolated():
    print("\n" + "=" * 70)
    print("TEST 7: Coverage de bot A no ve memorias/fuentes de bot B")
    print("=" * 70)
    invalidate_all_indexes()
    email_a, token_a, user_a = _register_and_login("mt_cov_a")
    email_b, token_b, user_b = _register_and_login("mt_cov_b")
    bot_a = _create_bot(token_a, "mt_cov_a", nicho_id="otro")
    bot_b = _create_bot(token_b, "mt_cov_b", nicho_id="otro")
    try:
        _add_memory_direct(bot_b, "B abre 24h", "horarios")

        report_a = _analyze(bot_a)
        report_b = _analyze(bot_b)

        horarios_a = _find_topic(report_a, "horarios")
        assert horarios_a.status == TopicCoverageStatus.MISSING
        assert horarios_a.evidence_count == 0

        horarios_b = _find_topic(report_b, "horarios")
        assert horarios_b.status != TopicCoverageStatus.MISSING
        assert horarios_b.evidence_count > 0

        print(f"✅ A: horarios={horarios_a.status.value}, "
              f"B: horarios={horarios_b.status.value}")
    finally:
        _cleanup_bot(bot_a)
        _cleanup_bot(bot_b)
        _cleanup_user(email_a)
        _cleanup_user(email_b)


def test_multitenant_questions_isolated():
    print("\n" + "=" * 70)
    print("TEST 8: Preguntas sin responder aisladas por bot")
    print("=" * 70)
    invalidate_all_indexes()
    email_a, token_a, user_a = _register_and_login("mt_q_a")
    email_b, token_b, user_b = _register_and_login("mt_q_b")
    bot_a = _create_bot(token_a, "mt_q_a", nicho_id="otro")
    bot_b = _create_bot(token_b, "mt_q_b", nicho_id="otro")
    try:
        _add_conversation_direct(bot_a, "Pregunta solo de A", was_answered=False)
        _add_conversation_direct(bot_a, "Pregunta solo de A", was_answered=False)
        _add_conversation_direct(bot_b, "Pregunta solo de B", was_answered=False)

        report_a = _analyze(bot_a)
        report_b = _analyze(bot_b)

        for g in report_a.unanswered_questions:
            assert "solo de b" not in g.representative.lower()
        for g in report_b.unanswered_questions:
            assert "solo de a" not in g.representative.lower()

        group_a = next((g for g in report_a.unanswered_questions
                        if "solo de a" in g.representative.lower()), None)
        assert group_a is not None
        assert group_a.count == 2

        print(f"✅ A: {len(report_a.unanswered_questions)} grupos; "
              f"B: {len(report_b.unanswered_questions)} grupos")
    finally:
        _cleanup_bot(bot_a)
        _cleanup_bot(bot_b)
        _cleanup_user(email_a)
        _cleanup_user(email_b)


def test_multitenant_recommendations_isolated():
    print("\n" + "=" * 70)
    print("TEST 9: Recomendaciones no se mezclan entre bots")
    print("=" * 70)
    invalidate_all_indexes()
    email_a, token_a, user_a = _register_and_login("mt_rec_a")
    email_b, token_b, user_b = _register_and_login("mt_rec_b")
    bot_a = _create_bot(token_a, "mt_rec_a", nicho_id="otro")
    bot_b = _create_bot(token_b, "mt_rec_b", nicho_id="otro")
    try:
        _add_conversation_direct(bot_a, "Solo A pregunta esto", was_answered=False)
        _add_conversation_direct(bot_a, "Solo A pregunta esto", was_answered=False)
        _add_conversation_direct(bot_b, "Solo B pregunta aquello", was_answered=False)
        _add_conversation_direct(bot_b, "Solo B pregunta aquello", was_answered=False)

        report_a = _analyze(bot_a)
        report_b = _analyze(bot_b)

        for r in report_a.recommendations:
            if r.type == RecommendationType.FREQUENT_QUESTION:
                assert "solo a" in r.title.lower()
                assert "solo b" not in r.title.lower()
        for r in report_b.recommendations:
            if r.type == RecommendationType.FREQUENT_QUESTION:
                assert "solo b" in r.title.lower()
                assert "solo a" not in r.title.lower()

        print(f"✅ Recs aisladas: A={len(report_a.recommendations)}, "
              f"B={len(report_b.recommendations)}")
    finally:
        _cleanup_bot(bot_a)
        _cleanup_bot(bot_b)
        _cleanup_user(email_a)
        _cleanup_user(email_b)


def test_multitenant_two_users_parallel():
    print("\n" + "=" * 70)
    print("TEST 10: Dos usuarios en paralelo, sin interferencias")
    print("=" * 70)
    invalidate_all_indexes()
    email_a, token_a, user_a = _register_and_login("mt_par_a")
    email_b, token_b, user_b = _register_and_login("mt_par_b")
    bot_a = _create_bot(token_a, "mt_par_a", nicho_id="otro")
    bot_b = _create_bot(token_b, "mt_par_b", nicho_id="otro")
    try:
        _add_memory_direct(bot_a, "Memoria A1", "horarios")
        _add_memory_direct(bot_a, "Memoria A2", "contacto")
        _add_memory_direct(bot_b, "Memoria B1", "precios")

        ra1 = _analyze(bot_a)
        rb1 = _analyze(bot_b)
        ra2 = _analyze(bot_a)

        assert ra1.memories_count == 2
        assert rb1.memories_count == 1
        assert ra2.memories_count == 2
        assert ra1.memories_count == ra2.memories_count

        print(f"✅ A: {ra1.memories_count} memories; "
              f"B: {rb1.memories_count} memories")
    finally:
        _cleanup_bot(bot_a)
        _cleanup_bot(bot_b)
        _cleanup_user(email_a)
        _cleanup_user(email_b)


# ============================================================
# 3. REGRESIÓN DE INTEGRACIÓN
# ============================================================

def test_orchestrator_not_affected():
    print("\n" + "=" * 70)
    print("TEST 11: /ask sigue funcionando tras Training")
    print("=" * 70)
    invalidate_all_indexes()
    email, token, user_id = _register_and_login("reg_ask")
    bot_id = _create_bot(token, "reg_ask", nicho_id="otro")
    try:
        _add_memory_direct(bot_id, "Abrimos de 9:00 a 18:00", "horarios")
        _ = _analyze(bot_id)

        r = client.post(
            "/ask/public",
            json={"bot_id": bot_id, "question": "horarios"},
        )
        assert r.status_code == 200, r.text
        assert r.json().get("found") is True

        print(f"✅ /ask/public OK: {r.json()['answer'][:40]}")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user(email)


def test_sources_not_affected():
    print("\n" + "=" * 70)
    print("TEST 12: CRUD /sources sigue OK tras Training")
    print("=" * 70)
    invalidate_all_indexes()
    email, token, user_id = _register_and_login("reg_src")
    bot_id = _create_bot(token, "reg_src", nicho_id="otro")
    try:
        r = client.post(
            "/sources/text",
            json={
                "bot_id": bot_id,
                "title": "Test",
                "content": "Contenido de prueba para sources",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200, r.text

        _ = _analyze(bot_id)

        r2 = client.get(
            f"/sources/list/{bot_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.status_code == 200
        assert r2.json()["total"] == 1
        print(f"✅ /sources OK: 1 source")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user(email)


def test_memories_not_affected():
    print("\n" + "=" * 70)
    print("TEST 13: CRUD /memories sigue OK tras Training")
    print("=" * 70)
    invalidate_all_indexes()
    email, token, user_id = _register_and_login("reg_mem")
    bot_id = _create_bot(token, "reg_mem", nicho_id="otro")
    try:
        r = client.post(
            "/memories/",
            json={
                "bot_id": bot_id,
                "fact": "Test memory",
                "keyword": "test",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200, r.text

        _ = _analyze(bot_id)

        r2 = client.get(
            f"/memories/{bot_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.status_code == 200
        assert len(r2.json()) >= 1
        print(f"✅ /memories OK: {len(r2.json())} memories")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user(email)


def test_analytics_not_affected():
    print("\n" + "=" * 70)
    print("TEST 14: /analytics sigue OK tras Training")
    print("=" * 70)
    invalidate_all_indexes()
    email, token, user_id = _register_and_login("reg_ana")
    bot_id = _create_bot(token, "reg_ana", nicho_id="otro")
    try:
        _add_conversation_direct(bot_id, "test question", was_answered=True)
        _ = _analyze(bot_id)

        r = client.get(
            f"/analytics/by-bot/{bot_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert r.json()["total_conversations"] >= 1
        print(f"✅ /analytics OK")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user(email)


def test_categories_not_affected():
    print("\n" + "=" * 70)
    print("TEST 15: /categories sigue OK tras Training")
    print("=" * 70)
    invalidate_all_indexes()
    email, token, user_id = _register_and_login("reg_cat")
    bot_id = _create_bot(token, "reg_cat", nicho_id="otro")
    try:
        r = client.post(
            "/categories/",
            json={
                "bot_id": bot_id,
                "name": "Test Cat",
                "description": "Test",
                "icon": "🧪",
                "order": 1,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200, r.text

        _ = _analyze(bot_id)

        r2 = client.get(
            f"/categories/{bot_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.status_code == 200
        assert len(r2.json()) >= 1
        print(f"✅ /categories OK")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user(email)


# ============================================================
# 4. RENDIMIENTO (INFORMATIVO)
# ============================================================

def test_full_flow_performance():
    print("\n" + "=" * 70)
    print("TEST 16: Rendimiento flujo completo (informativo)")
    print("=" * 70)
    invalidate_all_indexes()
    email, token, user_id = _register_and_login("perf_flow")
    bot_id = _create_bot(token, "perf_flow", nicho_id="restaurantes")
    try:
        for i in range(5):
            _add_memory_direct(bot_id, f"Memory {i}", f"kw{i}")
        for i in range(3):
            _add_conversation_direct(bot_id, f"¿Pregunta {i}?", was_answered=False)

        t0 = time.monotonic()
        report = _analyze(bot_id)
        elapsed_ms = int((time.monotonic() - t0) * 1000)

        print(f"✅ Análisis completo en {elapsed_ms} ms")
        print(f"   {report.total_topics} topics, "
              f"{report.memories_count} memories, "
              f"{len(report.unanswered_questions)} grupos, "
              f"{len(report.recommendations)} recs")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user(email)


def test_large_bot_performance():
    print("\n" + "=" * 70)
    print("TEST 17: Rendimiento bot grande (informativo)")
    print("=" * 70)
    invalidate_all_indexes()
    email, token, user_id = _register_and_login("perf_large")
    bot_id = _create_bot(token, "perf_large", nicho_id="restaurantes")
    try:
        for i in range(50):
            _add_memory_direct(bot_id, f"Memory {i}", f"kw{i}")
        for s in range(20):
            _add_source_direct(
                bot_id, user_id,
                [f"Chunk {s}-{j}" for j in range(3)],
                title=f"Source {s}"
            )
        for i in range(30):
            _add_conversation_direct(bot_id, f"Pregunta {i} sin resolver", was_answered=False)

        t0 = time.monotonic()
        report = _analyze(bot_id)
        elapsed_ms = int((time.monotonic() - t0) * 1000)

        print(f"✅ Bot grande (50 mem + 20 src + 30 conv) en {elapsed_ms} ms")
        print(f"   Topics: {report.total_topics}, "
              f"Memorias: {report.memories_count}, "
              f"Fuentes: {report.ready_sources_count}, "
              f"Grupos: {len(report.unanswered_questions)}")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user(email)


# ============================================================
# 5. CASOS BORDE
# ============================================================

def test_bot_with_only_memories():
    print("\n" + "=" * 70)
    print("TEST 18: Bot solo con memorias")
    print("=" * 70)
    invalidate_all_indexes()
    email, token, user_id = _register_and_login("only_mem")
    bot_id = _create_bot(token, "only_mem", nicho_id="otro")
    try:
        _add_memory_direct(bot_id, "Memoria única", "kw")
        report = _analyze(bot_id)
        assert report.has_memories is True
        assert report.has_sources is False
        assert report.memories_count == 1
        assert report.ready_sources_count == 0
        print(f"✅ Solo memories OK")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user(email)


def test_bot_with_only_sources():
    print("\n" + "=" * 70)
    print("TEST 19: Bot solo con fuentes")
    print("=" * 70)
    invalidate_all_indexes()
    email, token, user_id = _register_and_login("only_src")
    bot_id = _create_bot(token, "only_src", nicho_id="otro")
    try:
        _add_source_direct(bot_id, user_id, ["Contenido uno"], "S1")
        report = _analyze(bot_id)
        assert report.has_memories is False
        assert report.has_sources is True
        assert report.memories_count == 0
        assert report.ready_sources_count == 1
        print(f"✅ Solo sources OK")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user(email)


def test_bot_with_mixed_knowledge():
    print("\n" + "=" * 70)
    print("TEST 20: Bot con memorias + fuentes")
    print("=" * 70)
    invalidate_all_indexes()
    email, token, user_id = _register_and_login("mixed_kb")
    bot_id = _create_bot(token, "mixed_kb", nicho_id="otro")
    try:
        _add_memory_direct(bot_id, "Memoria uno", "horarios")
        _add_source_direct(bot_id, user_id, ["Fuente uno"], "S1")
        report = _analyze(bot_id)
        assert report.has_memories is True
        assert report.has_sources is True
        assert report.memories_count == 1
        assert report.ready_sources_count == 1
        print(f"✅ Mixto OK")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user(email)


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.4.9 (Integración end-to-end)")
    print("=" * 70)

    tests = [
        test_full_flow_empty_bot,
        test_full_flow_with_memory,
        test_full_flow_with_source,
        test_full_flow_with_conversations,
        test_full_flow_progressive,
        test_multitenant_analyzer_isolated,
        test_multitenant_coverage_isolated,
        test_multitenant_questions_isolated,
        test_multitenant_recommendations_isolated,
        test_multitenant_two_users_parallel,
        test_orchestrator_not_affected,
        test_sources_not_affected,
        test_memories_not_affected,
        test_analytics_not_affected,
        test_categories_not_affected,
        test_full_flow_performance,
        test_large_bot_performance,
        test_bot_with_only_memories,
        test_bot_with_only_sources,
        test_bot_with_mixed_knowledge,
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
