"""
Tests — Subfase 14.3.5
Verifica el router /sources/.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.main import app
from app.database.config import SessionLocal
from app.models.db_models import Bot, User, Source, SourceChunk, Memory
from app.core.indexing import invalidate_all_indexes


client = TestClient(app)


# ============================================================
# HELPERS
# ============================================================

def _register_and_login(suffix: str) -> str:
    """Registra un usuario y devuelve su token."""
    email = f"test_router_{suffix}@nuvora.com"
    password = "123456"

    client.post("/auth/register", json={
        "email": email,
        "password": password,
        "full_name": f"Test Router {suffix}",
    })

    r = client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return r.json()["access_token"]


def _create_bot(token: str, suffix: str) -> int:
    r = client.post(
        "/bots/",
        json={
            "name": f"Bot Router {suffix}",
            "business_name": f"Test {suffix}",
            "nicho_id": "desde_cero",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    return r.json()["id"]


def _cleanup_bot(bot_id: int):
    db = SessionLocal()
    try:
        db.query(SourceChunk).filter(SourceChunk.bot_id == bot_id).delete(synchronize_session=False)
        db.query(Source).filter(Source.bot_id == bot_id).delete(synchronize_session=False)
        db.query(Memory).filter(Memory.bot_id == bot_id).delete(synchronize_session=False)
        db.query(Bot).filter(Bot.id == bot_id).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _cleanup_user(email: str):
    db = SessionLocal()
    try:
        db.query(User).filter(User.email == email).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


# ============================================================
# TESTS
# ============================================================

def test_create_text_source():
    print("\n" + "=" * 70)
    print("TEST 1: Crear fuente de texto")
    print("=" * 70)
    invalidate_all_indexes()

    token = _register_and_login("t1")
    bot_id = _create_bot(token, "t1")
    try:
        r = client.post(
            "/sources/text",
            json={
                "bot_id": bot_id,
                "title": "Info",
                "content": "Abrimos de 9:00 a 18:00.\n\nAceptamos reservas.",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ready"
        assert data["chunks_count"] >= 1
        assert data["type"] == "text"
        print(f"✅ Source creada: id={data['id']}, chunks={data['chunks_count']}")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user("test_router_t1@nuvora.com")


def test_create_text_empty():
    print("\n" + "=" * 70)
    print("TEST 2: Texto vacío → error")
    print("=" * 70)
    invalidate_all_indexes()

    token = _register_and_login("t2")
    bot_id = _create_bot(token, "t2")
    try:
        r = client.post(
            "/sources/text",
            json={"bot_id": bot_id, "title": "Vacío", "content": "   \n\n   "},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 400
        print(f"✅ Error 400 correcto: {r.json()['detail'][:60]}")

        # Verificar que la Source quedó como failed
        db = SessionLocal()
        sources = db.query(Source).filter(Source.bot_id == bot_id).all()
        assert len(sources) == 1
        assert sources[0].status == "failed"
        print(f"✅ Source marcada como failed")
        db.close()
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user("test_router_t2@nuvora.com")


def test_create_text_too_large():
    print("\n" + "=" * 70)
    print("TEST 3: Texto > 100 KB → error")
    print("=" * 70)
    invalidate_all_indexes()

    token = _register_and_login("t3")
    bot_id = _create_bot(token, "t3")
    try:
        big = "a" * (200 * 1024)
        r = client.post(
            "/sources/text",
            json={"bot_id": bot_id, "title": "Grande", "content": big},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 400
        print(f"✅ Error 400 correcto: {r.json()['detail'][:60]}")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user("test_router_t3@nuvora.com")


def test_create_text_no_auth():
    print("\n" + "=" * 70)
    print("TEST 4: Sin autenticación → 401")
    print("=" * 70)

    r = client.post(
        "/sources/text",
        json={"bot_id": 1, "title": "Test", "content": "Contenido"},
    )
    assert r.status_code == 401
    print(f"✅ Error 401 correcto")


def test_create_text_not_owner():
    print("\n" + "=" * 70)
    print("TEST 5: Usuario ajeno → 403")
    print("=" * 70)
    invalidate_all_indexes()

    token1 = _register_and_login("t5a")
    bot_id = _create_bot(token1, "t5a")
    token2 = _register_and_login("t5b")
    try:
        r = client.post(
            "/sources/text",
            json={"bot_id": bot_id, "title": "Hack", "content": "Contenido"},
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert r.status_code == 403
        print(f"✅ Error 403 correcto")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user("test_router_t5a@nuvora.com")
        _cleanup_user("test_router_t5b@nuvora.com")


def test_list_sources():
    print("\n" + "=" * 70)
    print("TEST 6: Listar fuentes")
    print("=" * 70)
    invalidate_all_indexes()

    token = _register_and_login("t6")
    bot_id = _create_bot(token, "t6")
    try:
        for i in range(3):
            client.post(
                "/sources/text",
                json={"bot_id": bot_id, "title": f"Info {i}", "content": f"Contenido {i}"},
                headers={"Authorization": f"Bearer {token}"},
            )

        r = client.get(
            f"/sources/list/{bot_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 3
        assert len(data["sources"]) == 3
        print(f"✅ Listadas {data['total']} fuentes")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user("test_router_t6@nuvora.com")


def test_list_sources_empty():
    print("\n" + "=" * 70)
    print("TEST 7: Listar bot sin fuentes")
    print("=" * 70)
    invalidate_all_indexes()

    token = _register_and_login("t7")
    bot_id = _create_bot(token, "t7")
    try:
        r = client.get(
            f"/sources/list/{bot_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert r.json()["total"] == 0
        print(f"✅ 0 fuentes correctamente")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user("test_router_t7@nuvora.com")


def test_get_source_detail():
    print("\n" + "=" * 70)
    print("TEST 8: Ver detalle de fuente")
    print("=" * 70)
    invalidate_all_indexes()

    token = _register_and_login("t8")
    bot_id = _create_bot(token, "t8")
    try:
        r = client.post(
            "/sources/text",
            json={"bot_id": bot_id, "title": "Info", "content": "Contenido de prueba"},
            headers={"Authorization": f"Bearer {token}"},
        )
        source_id = r.json()["id"]

        r2 = client.get(
            f"/sources/{source_id}/detail",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.status_code == 200
        data = r2.json()
        assert data["id"] == source_id
        assert data["content_raw"] == "Contenido de prueba"
        assert data["content_processed"] is not None
        print(f"✅ Detalle con content_raw y content_processed")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user("test_router_t8@nuvora.com")


def test_get_source_404():
    print("\n" + "=" * 70)
    print("TEST 9: Detalle de fuente inexistente → 404")
    print("=" * 70)

    token = _register_and_login("t9")
    try:
        r = client.get(
            "/sources/99999/detail",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 404
        print(f"✅ Error 404 correcto")
    finally:
        _cleanup_user("test_router_t9@nuvora.com")


def test_delete_source():
    print("\n" + "=" * 70)
    print("TEST 10: Eliminar fuente")
    print("=" * 70)
    invalidate_all_indexes()

    token = _register_and_login("t10")
    bot_id = _create_bot(token, "t10")
    try:
        r = client.post(
            "/sources/text",
            json={"bot_id": bot_id, "title": "Borrar", "content": "Contenido"},
            headers={"Authorization": f"Bearer {token}"},
        )
        source_id = r.json()["id"]

        r2 = client.delete(
            f"/sources/{source_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.status_code == 200
        assert r2.json()["success"] is True

        # Verificar que ya no existe
        r3 = client.get(
            f"/sources/{source_id}/detail",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r3.status_code == 404
        print(f"✅ Fuente eliminada correctamente")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user("test_router_t10@nuvora.com")


def test_delete_source_not_owner():
    print("\n" + "=" * 70)
    print("TEST 11: Eliminar fuente ajena → 403")
    print("=" * 70)
    invalidate_all_indexes()

    token1 = _register_and_login("t11a")
    bot_id = _create_bot(token1, "t11a")
    token2 = _register_and_login("t11b")
    try:
        r = client.post(
            "/sources/text",
            json={"bot_id": bot_id, "title": "Info", "content": "Contenido"},
            headers={"Authorization": f"Bearer {token1}"},
        )
        source_id = r.json()["id"]

        r2 = client.delete(
            f"/sources/{source_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert r2.status_code == 403
        print(f"✅ Error 403 correcto")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user("test_router_t11a@nuvora.com")
        _cleanup_user("test_router_t11b@nuvora.com")


def test_reindex_source():
    print("\n" + "=" * 70)
    print("TEST 12: Reindexar fuente")
    print("=" * 70)
    invalidate_all_indexes()

    token = _register_and_login("t12")
    bot_id = _create_bot(token, "t12")
    try:
        r = client.post(
            "/sources/text",
            json={"bot_id": bot_id, "title": "Info", "content": "Abrimos de 9:00 a 18:00.\n\nAceptamos reservas."},
            headers={"Authorization": f"Bearer {token}"},
        )
        source_id = r.json()["id"]
        original_chunks = r.json()["chunks_count"]

        r2 = client.post(
            f"/sources/{source_id}/reindex",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.status_code == 200
        assert r2.json()["chunks_count"] == original_chunks
        assert r2.json()["status"] == "ready"
        print(f"✅ Reindexado correcto: chunks={r2.json()['chunks_count']}")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user("test_router_t12@nuvora.com")


def test_reindex_all():
    print("\n" + "=" * 70)
    print("TEST 13: Reindexar todas las fuentes de un bot")
    print("=" * 70)
    invalidate_all_indexes()

    token = _register_and_login("t13")
    bot_id = _create_bot(token, "t13")
    try:
        for i in range(3):
            client.post(
                "/sources/text",
                json={"bot_id": bot_id, "title": f"Info {i}", "content": f"Contenido {i}"},
                headers={"Authorization": f"Bearer {token}"},
            )

        r = client.post(
            f"/sources/reindex-all/{bot_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["metadata"]["reindexed"] == 3
        assert data["metadata"]["failed"] == 0
        print(f"✅ Reindexadas {data['metadata']['reindexed']}, fallidas {data['metadata']['failed']}")
    finally:
        _cleanup_bot(bot_id)
        _cleanup_user("test_router_t13@nuvora.com")


def test_multi_tenant_isolation():
    print("\n" + "=" * 70)
    print("TEST 14: Aislamiento multi-tenant")
    print("=" * 70)
    invalidate_all_indexes()

    token1 = _register_and_login("t14a")
    bot1_id = _create_bot(token1, "t14a")
    token2 = _register_and_login("t14b")
    bot2_id = _create_bot(token2, "t14b")
    try:
        client.post(
            "/sources/text",
            json={"bot_id": bot1_id, "title": "Info bot1", "content": "Contenido bot1"},
            headers={"Authorization": f"Bearer {token1}"},
        )

        # Bot2 intenta listar fuentes de bot1
        r = client.get(
            f"/sources/list/{bot1_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert r.status_code == 403
        print(f"✅ Bot2 no puede listar fuentes de bot1 (403)")

        # Bot1 sí puede
        r2 = client.get(
            f"/sources/list/{bot1_id}",
            headers={"Authorization": f"Bearer {token1}"},
        )
        assert r2.status_code == 200
        assert r2.json()["total"] == 1
        print(f"✅ Bot1 sí puede listar sus fuentes")
    finally:
        _cleanup_bot(bot1_id)
        _cleanup_bot(bot2_id)
        _cleanup_user("test_router_t14a@nuvora.com")
        _cleanup_user("test_router_t14b@nuvora.com")


def test_reindex_preserves_chunks_on_failure():
    print("\n" + "=" * 70)
    print("TEST 15: Reindexado fallido preserva chunks antiguos")
    print("=" * 70)
    invalidate_all_indexes()

    token = _register_and_login("t15")
    bot_id = _create_bot(token, "t15")
    try:
        r = client.post(
            "/sources/text",
            json={"bot_id": bot_id, "title": "Info", "content": "Contenido original"},
            headers={"Authorization": f"Bearer {token}"},
        )
        source_id = r.json()["id"]
        original_chunks = r.json()["chunks_count"]
        print(f"   Chunks originales: {original_chunks}")

        # Alterar content_raw para que falle el reindexado
        db = SessionLocal()
        source = db.query(Source).filter(Source.id == source_id).first()
        source.content_raw = ""  # Forzar fallo
        db.commit()
        db.close()

        # Intentar reindexar
        r2 = client.post(
            f"/sources/{source_id}/reindex",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.status_code == 400
        print(f"✅ Reindexado falló con 400")

        # Verificar que los chunks originales siguen intactos
        db = SessionLocal()
        chunks = db.query(SourceChunk).filter(SourceChunk.source_id == source_id).all()
        assert len(chunks) == original_chunks, f"Chunks originales destruidos: {len(chunks)} vs {original_chunks}"
        print(f"✅ Chunks originales preservados: {len(chunks)}")
        db.close()

    finally:
        _cleanup_bot(bot_id)
        _cleanup_user("test_router_t15@nuvora.com")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.3.5 (Router /sources/)")
    print("=" * 70)

    tests = [
        test_create_text_source,
        test_create_text_empty,
        test_create_text_too_large,
        test_create_text_no_auth,
        test_create_text_not_owner,
        test_list_sources,
        test_list_sources_empty,
        test_get_source_detail,
        test_get_source_404,
        test_delete_source,
        test_delete_source_not_owner,
        test_reindex_source,
        test_reindex_all,
        test_multi_tenant_isolation,
        test_reindex_preserves_chunks_on_failure,
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
