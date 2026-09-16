"""
Tests — Subfase 14.9.4 (Generador public_id + public_slug)
============================================================
Verifica:
    - generate_public_id: UUID v4, unicidad, formato
    - slugify: acentos, símbolos, mayúsculas, casos raros
    - generate_public_slug: colisiones, sufijos, fallback
    - build_public_url: prioridad slug > public_id
    - Idempotente
"""

import sys
import os
import time
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.config import SessionLocal
from app.models.db_models import Bot, User
from app.services.publication import (
    generate_public_id,
    slugify,
    generate_public_slug,
    build_public_url,
    PUBLIC_BASE_URL,
    SLUG_MIN_LENGTH,
    SLUG_MAX_LENGTH,
)


# ============================================================
# HELPERS
# ============================================================

def _unique(suffix):
    return f"{suffix}_{int(time.time() * 1000000)}_{os.getpid()}"


def _cleanup_user(db, email):
    """Borra usuario + bots asociados."""
    u = db.query(User).filter(User.email == email).first()
    if u:
        bots = db.query(Bot).filter(Bot.user_id == u.id).all()
        for b in bots:
            db.delete(b)
        db.delete(u)
        db.commit()


def _create_user(db):
    email = f"{_unique('pub_slug_user')}@nuvora.com"
    u = User(
        email=email,
        hashed_password="x",
        full_name="Test Slug",
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u, email


def _create_bot(db, user_id, name, public_slug=None):
    b = Bot(
        user_id=user_id,
        name=name,
        business_name="Test",
        nicho_id="otro",
        public_slug=public_slug,
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


# ============================================================
# TESTS
# ============================================================

def test_generate_public_id_format():
    print("\n" + "=" * 70)
    print("TEST 1: generate_public_id — formato UUID v4")
    print("=" * 70)
    pid = generate_public_id()
    assert len(pid) == 36
    assert pid.count("-") == 4
    # Validar con uuid
    parsed = uuid.UUID(pid)
    assert parsed.version == 4, f"Esperado v4, obtenido v{parsed.version}"
    print(f"  ✅ UUID v4 OK: {pid}")


def test_generate_public_id_unique():
    print("\n" + "=" * 70)
    print("TEST 2: generate_public_id — 1000 IDs únicos")
    print("=" * 70)
    ids = {generate_public_id() for _ in range(1000)}
    assert len(ids) == 1000, f"Solo {len(ids)} únicos de 1000"
    print("  ✅ 1000 UUIDs únicos (sin colisiones)")


def test_slugify_basic():
    print("\n" + "=" * 70)
    print("TEST 3: slugify — casos básicos")
    print("=" * 70)
    cases = [
        ("Clínica Salud", "clinica-salud"),
        ("Restaurante La Marina", "restaurante-la-marina"),
        ("Peluquería Estilo", "peluqueria-estilo"),
        ("Hotel Barcelona", "hotel-barcelona"),
        ("Gimnasio Fit", "gimnasio-fit"),
    ]
    for raw, expected in cases:
        got = slugify(raw)
        assert got == expected, f"slugify({raw!r}) = {got!r} ≠ {expected!r}"
    print(f"  ✅ {len(cases)} casos básicos OK")


def test_slugify_accents():
    print("\n" + "=" * 70)
    print("TEST 4: slugify — acentos y caracteres especiales")
    print("=" * 70)
    cases = [
        ("Café Ñandú", "cafe-nandu"),
        ("Málaga · Madrid", "malaga-madrid"),
        ("Jalapeño", "jalapeno"),
        ("Àéîõü", "aeiou"),
        ("¡Hola!", "hola"),
        ("¿Qué?", "que"),
    ]
    for raw, expected in cases:
        got = slugify(raw)
        assert got == expected, f"slugify({raw!r}) = {got!r} ≠ {expected!r}"
    print(f"  ✅ {len(cases)} casos con acentos OK")


def test_slugify_spaces_and_dashes():
    print("\n" + "=" * 70)
    print("TEST 5: slugify — espacios y guiones")
    print("=" * 70)
    cases = [
        ("  ---Hello---  ", "hello"),
        ("Hello    World", "hello-world"),
        ("Hello---World", "hello-world"),
        ("Hello - World", "hello-world"),
        ("...", ""),
        ("@#$%", ""),
    ]
    for raw, expected in cases:
        got = slugify(raw)
        assert got == expected, f"slugify({raw!r}) = {got!r} ≠ {expected!r}"
    print(f"  ✅ {len(cases)} casos de espaciado OK")


def test_slugify_numbers():
    print("\n" + "=" * 70)
    print("TEST 6: slugify — números")
    print("=" * 70)
    cases = [
        ("Restaurante 24h", "restaurante-24h"),
        ("Peluquería 2.0", "peluqueria-2-0"),
        ("Calle 42", "calle-42"),
    ]
    for raw, expected in cases:
        got = slugify(raw)
        assert got == expected, f"slugify({raw!r}) = {got!r} ≠ {expected!r}"
    print(f"  ✅ {len(cases)} casos con números OK")


def test_slugify_empty():
    print("\n" + "=" * 70)
    print("TEST 7: slugify — vacío / None")
    print("=" * 70)
    assert slugify("") == ""
    assert slugify("   ") == ""
    print("  ✅ Vacío → '' OK")


def test_generate_public_slug_no_collision():
    print("\n" + "=" * 70)
    print("TEST 8: generate_public_slug — sin colisión")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        slug = generate_public_slug("Clínica Nueva", db)
        assert slug == "clinica-nueva", f"Esperado 'clinica-nueva', obtenido {slug!r}"
        print(f"  ✅ slug único: {slug}")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_generate_public_slug_collision():
    print("\n" + "=" * 70)
    print("TEST 9: generate_public_slug — colisiones con sufijos")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)

        # Creamos el primer bot con slug "test-colision"
        _create_bot(db, u.id, "Test Colision", public_slug="test-colision")

        # Ahora pedimos slug para otro bot con el mismo nombre
        slug2 = generate_public_slug("Test Colision", db)
        assert slug2 == "test-colision-2", f"Esperado 'test-colision-2', obtenido {slug2!r}"

        # Y otro más
        _create_bot(db, u.id, "Test Colision", public_slug=slug2)
        slug3 = generate_public_slug("Test Colision", db)
        assert slug3 == "test-colision-3", f"Esperado 'test-colision-3', obtenido {slug3!r}"

        print(f"  ✅ sufijos: test-colision → test-colision-2 → test-colision-3")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_generate_public_slug_fallback():
    print("\n" + "=" * 70)
    print("TEST 10: generate_public_slug — fallback cuando el nombre no da slug")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        slug = generate_public_slug("@@@", db)
        assert slug.startswith("bot-"), f"Esperado fallback 'bot-XXXXXX', obtenido {slug!r}"
        assert len(slug) == 10, f"Esperado 'bot-' + 6 chars, obtenido {slug!r} ({len(slug)})"
        print(f"  ✅ fallback: {slug}")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_generate_public_slug_max_length():
    print("\n" + "=" * 70)
    print("TEST 11: generate_public_slug — respeta longitud máxima")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        # Nombre muy largo
        long_name = "A" * 200
        slug = generate_public_slug(long_name, db)
        assert len(slug) <= SLUG_MAX_LENGTH, f"Slug demasiado largo: {len(slug)}"
        print(f"  ✅ slug recortado a {len(slug)} chars (max {SLUG_MAX_LENGTH})")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_build_public_url_with_slug():
    print("\n" + "=" * 70)
    print("TEST 12: build_public_url — con slug (prioridad)")
    print("=" * 70)
    url = build_public_url("abc-123", "clinica-salud")
    assert url == f"{PUBLIC_BASE_URL}/clinica-salud", url
    print(f"  ✅ {url}")


def test_build_public_url_without_slug():
    print("\n" + "=" * 70)
    print("TEST 13: build_public_url — sin slug (usa public_id)")
    print("=" * 70)
    url = build_public_url("abc-123", None)
    assert url == f"{PUBLIC_BASE_URL}/abc-123", url
    print(f"  ✅ {url}")


def test_build_public_url_empty_slug():
    print("\n" + "=" * 70)
    print("TEST 14: build_public_url — slug vacío (usa public_id)")
    print("=" * 70)
    url = build_public_url("abc-123", "")
    assert url == f"{PUBLIC_BASE_URL}/abc-123", url
    print(f"  ✅ {url}")


def test_integration_publish_flow():
    print("\n" + "=" * 70)
    print("TEST 15: integración — generar id + slug + url")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id, "Clínica Integración Test")

        # Simular publicación
        b.public_id = generate_public_id()
        b.public_slug = generate_public_slug(b.name, db)
        b.published_at = datetime.now(timezone.utc)
        b.is_published = True
        db.commit()
        db.refresh(b)

        url = build_public_url(b.public_id, b.public_slug)

        assert b.public_id is not None
        assert b.public_slug == "clinica-integracion-test"
        assert url == f"{PUBLIC_BASE_URL}/clinica-integracion-test"

        print(f"  ✅ Bot publicado: {url}")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.9.4 (Generador public_id + slug)")
    print("=" * 70)

    tests = [
        test_generate_public_id_format,
        test_generate_public_id_unique,
        test_slugify_basic,
        test_slugify_accents,
        test_slugify_spaces_and_dashes,
        test_slugify_numbers,
        test_slugify_empty,
        test_generate_public_slug_no_collision,
        test_generate_public_slug_collision,
        test_generate_public_slug_fallback,
        test_generate_public_slug_max_length,
        test_build_public_url_with_slug,
        test_build_public_url_without_slug,
        test_build_public_url_empty_slug,
        test_integration_publish_flow,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"  🛑 FALLÓ: {t.__name__}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print(f"🎉 RESULTADO: {passed} pasados / {failed} fallidos")
    print("=" * 70)
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
