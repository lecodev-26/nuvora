"""
Tests — Subfase 14.9.3 (Schemas Pydantic de Publicación Universal)
===================================================================
Verifica:
    - PublicationConfig: defaults, validaciones de color, límites
    - PublicationResponse / Update / PublishResponse
    - PublicBotInfo
    - PublicSessionCreateRequest / Response
    - PublicMessageRequest / Response
    - Regla de oro: config SOLO acepta campos visuales/textos
"""

import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import ValidationError

from app.models.public import (
    PublicationConfig,
    PublicationResponse,
    PublicationUpdate,
    PublishResponse,
    PublicBotInfo,
    PublicSessionCreateRequest,
    PublicSessionResponse,
    PublicMessageRequest,
    PublicMessageResponse,
)


# ============================================================
# TESTS
# ============================================================

def test_publication_config_defaults():
    print("\n" + "=" * 70)
    print("TEST 1: PublicationConfig — defaults")
    print("=" * 70)
    cfg = PublicationConfig()
    assert cfg.welcome_message is None
    assert cfg.placeholder is None
    assert cfg.avatar_url is None
    assert cfg.primary_color is None
    assert cfg.show_branding is True
    print("  ✅ Defaults OK")


def test_publication_config_valid():
    print("\n" + "=" * 70)
    print("TEST 2: PublicationConfig — valores válidos")
    print("=" * 70)
    cfg = PublicationConfig(
        welcome_message="Hola 👋 ¿En qué puedo ayudarte?",
        placeholder="Escribe un mensaje...",
        avatar_url="https://example.com/avatar.png",
        primary_color="#7B5CFF",
        show_branding=True,
    )
    assert cfg.welcome_message == "Hola 👋 ¿En qué puedo ayudarte?"
    assert cfg.primary_color == "#7B5CFF"
    print("  ✅ Valores válidos OK")


def test_publication_config_invalid_color():
    print("\n" + "=" * 70)
    print("TEST 3: PublicationConfig — color inválido rechazado")
    print("=" * 70)
    invalids = ["red", "#FFF", "#GGGGGG", "7B5CFF", "#7b5cff00"]
    for bad in invalids:
        try:
            PublicationConfig(primary_color=bad)
            raise AssertionError(f"Debería haber rechazado: {bad}")
        except ValidationError:
            pass
    print(f"  ✅ {len(invalids)} colores inválidos rechazados")


def test_publication_config_max_lengths():
    print("\n" + "=" * 70)
    print("TEST 4: PublicationConfig — límites de longitud")
    print("=" * 70)
    # welcome_message > 500
    try:
        PublicationConfig(welcome_message="x" * 501)
        raise AssertionError("Debería haber rechazado welcome_message > 500")
    except ValidationError:
        print("  ✅ welcome_message > 500 rechazado")

    # placeholder > 100
    try:
        PublicationConfig(placeholder="x" * 101)
        raise AssertionError("Debería haber rechazado placeholder > 100")
    except ValidationError:
        print("  ✅ placeholder > 100 rechazado")

    # avatar_url > 500
    try:
        PublicationConfig(avatar_url="x" * 501)
        raise AssertionError("Debería haber rechazado avatar_url > 500")
    except ValidationError:
        print("  ✅ avatar_url > 500 rechazado")


def test_publication_config_no_extra_fields():
    print("\n" + "=" * 70)
    print("TEST 5: PublicationConfig — no acepta campos prohibidos")
    print("=" * 70)
    # pydantic v2 por defecto ignora extras → comprobamos que no estén
    cfg = PublicationConfig(
        welcome_message="Hola",
        workflow_id=999,           # NO debería aparecer
        system_prompt="..."         # NO debería aparecer
    )
    assert not hasattr(cfg, "workflow_id") or getattr(cfg, "workflow_id", None) is None
    assert not hasattr(cfg, "system_prompt") or getattr(cfg, "system_prompt", None) is None
    print("  ✅ Campos prohibidos ignorados/no presentes")


def test_publication_response():
    print("\n" + "=" * 70)
    print("TEST 6: PublicationResponse")
    print("=" * 70)
    resp = PublicationResponse(
        bot_id=9,
        is_published=True,
        public_id="abc-123",
        public_slug="clinica-salud",
        published_at=datetime.now(timezone.utc),
        public_url="https://nuvora-chi.vercel.app/b/clinica-salud",
        config=PublicationConfig(welcome_message="Hola"),
    )
    assert resp.bot_id == 9
    assert resp.is_published is True
    assert resp.public_id == "abc-123"
    print("  ✅ PublicationResponse OK")


def test_publication_response_not_published():
    print("\n" + "=" * 70)
    print("TEST 7: PublicationResponse — bot no publicado")
    print("=" * 70)
    resp = PublicationResponse(bot_id=9)
    assert resp.is_published is False
    assert resp.public_id is None
    assert resp.published_at is None
    assert resp.config is None
    print("  ✅ Estado no publicado OK")


def test_publication_update():
    print("\n" + "=" * 70)
    print("TEST 8: PublicationUpdate")
    print("=" * 70)
    upd = PublicationUpdate(
        config=PublicationConfig(welcome_message="Hola", primary_color="#00C6FF")
    )
    assert upd.config.welcome_message == "Hola"
    assert upd.config.primary_color == "#00C6FF"
    print("  ✅ PublicationUpdate OK")


def test_publish_response():
    print("\n" + "=" * 70)
    print("TEST 9: PublishResponse")
    print("=" * 70)
    resp = PublishResponse(
        bot_id=9,
        is_published=True,
        public_id="abc-123",
        public_slug="clinica-salud",
        published_at=datetime.now(timezone.utc),
        public_url="https://nuvora-chi.vercel.app/b/clinica-salud",
    )
    assert resp.public_id == "abc-123"
    assert resp.public_slug == "clinica-salud"
    print("  ✅ PublishResponse OK")


def test_public_bot_info():
    print("\n" + "=" * 70)
    print("TEST 10: PublicBotInfo")
    print("=" * 70)
    info = PublicBotInfo(
        public_id="abc-123",
        name="Clínica Salud",
        description="Tu clínica de confianza",
        nicho_id="clinicas",
        business_name="Clínica Salud",
        config=PublicationConfig(welcome_message="Hola 👋"),
    )
    assert info.public_id == "abc-123"
    assert info.nicho_id == "clinicas"
    assert info.config.welcome_message == "Hola 👋"
    print("  ✅ PublicBotInfo OK")


def test_public_session_create_request():
    print("\n" + "=" * 70)
    print("TEST 11: PublicSessionCreateRequest (vacío permitido)")
    print("=" * 70)
    req = PublicSessionCreateRequest()
    assert req is not None
    print("  ✅ PublicSessionCreateRequest OK")


def test_public_session_response():
    print("\n" + "=" * 70)
    print("TEST 12: PublicSessionResponse")
    print("=" * 70)
    resp = PublicSessionResponse(
        session_id="sess-xyz",
        bot_public_id="abc-123",
        expires_at=datetime.now(timezone.utc),
    )
    assert resp.session_id == "sess-xyz"
    assert resp.bot_public_id == "abc-123"
    print("  ✅ PublicSessionResponse OK")


def test_public_message_request_valid():
    print("\n" + "=" * 70)
    print("TEST 13: PublicMessageRequest — válido")
    print("=" * 70)
    req = PublicMessageRequest(session_id="sess-1", message="Hola")
    assert req.session_id == "sess-1"
    assert req.message == "Hola"
    print("  ✅ PublicMessageRequest OK")


def test_public_message_request_empty_message():
    print("\n" + "=" * 70)
    print("TEST 14: PublicMessageRequest — mensaje vacío rechazado")
    print("=" * 70)
    try:
        PublicMessageRequest(session_id="sess-1", message="")
        raise AssertionError("Debería haber rechazado mensaje vacío")
    except ValidationError:
        print("  ✅ Mensaje vacío rechazado")


def test_public_message_request_too_long():
    print("\n" + "=" * 70)
    print("TEST 15: PublicMessageRequest — mensaje > 2000 rechazado")
    print("=" * 70)
    try:
        PublicMessageRequest(session_id="sess-1", message="a" * 2001)
        raise AssertionError("Debería haber rechazado mensaje > 2000")
    except ValidationError:
        print("  ✅ Mensaje > 2000 rechazado")


def test_public_message_request_session_id_required():
    print("\n" + "=" * 70)
    print("TEST 16: PublicMessageRequest — session_id requerido")
    print("=" * 70)
    try:
        PublicMessageRequest(message="Hola")  # falta session_id
        raise AssertionError("Debería haber rechazado por session_id requerido")
    except ValidationError:
        print("  ✅ session_id requerido OK")


def test_public_message_response():
    print("\n" + "=" * 70)
    print("TEST 17: PublicMessageResponse")
    print("=" * 70)
    resp = PublicMessageResponse(
        reply="¡Hola! ¿En qué puedo ayudarte?",
        session_id="sess-1",
        status="completed",
    )
    assert resp.reply == "¡Hola! ¿En qué puedo ayudarte?"
    assert resp.status == "completed"
    assert resp.variables_public is None
    print("  ✅ PublicMessageResponse OK")


def test_public_message_response_status_enum():
    print("\n" + "=" * 70)
    print("TEST 18: PublicMessageResponse — status válido")
    print("=" * 70)
    for st in ["completed", "waiting_input", "error"]:
        r = PublicMessageResponse(reply="x", session_id="s", status=st)
        assert r.status == st
    print("  ✅ Los 3 status válidos OK")

    try:
        PublicMessageResponse(reply="x", session_id="s", status="invalid_status")
        raise AssertionError("Debería haber rechazado status inválido")
    except ValidationError:
        print("  ✅ status inválido rechazado")


def test_public_message_response_variables_optional():
    print("\n" + "=" * 70)
    print("TEST 19: PublicMessageResponse — variables_public opcional")
    print("=" * 70)
    r = PublicMessageResponse(
        reply="Hola",
        session_id="s",
        variables_public={"name": "Manuel"},
    )
    assert r.variables_public == {"name": "Manuel"}

    r2 = PublicMessageResponse(reply="Hola", session_id="s")
    assert r2.variables_public is None
    print("  ✅ variables_public opcional OK")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.9.3 (Schemas Pydantic)")
    print("=" * 70)

    tests = [
        test_publication_config_defaults,
        test_publication_config_valid,
        test_publication_config_invalid_color,
        test_publication_config_max_lengths,
        test_publication_config_no_extra_fields,
        test_publication_response,
        test_publication_response_not_published,
        test_publication_update,
        test_publish_response,
        test_public_bot_info,
        test_public_session_create_request,
        test_public_session_response,
        test_public_message_request_valid,
        test_public_message_request_empty_message,
        test_public_message_request_too_long,
        test_public_message_request_session_id_required,
        test_public_message_response,
        test_public_message_response_status_enum,
        test_public_message_response_variables_optional,
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
