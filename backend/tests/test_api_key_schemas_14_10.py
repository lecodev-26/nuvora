"""
Tests — Subfase 14.10.4 (Schemas Pydantic)
============================================
Cubre:
    - ApiKeyCreate: validaciones nombre
    - ApiKeyResponse: 8 campos, sin secret
    - ApiKeyCreatedResponse: con key + warning
    - ApiKeyListResponse: lista + total
    - ChatRequest: message 1-2000, session_id opcional 1-64
    - ChatResponse: answer + session_id + status enum
"""

import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import ValidationError

from app.models.api_key import (
    ApiKeyCreate,
    ApiKeyResponse,
    ApiKeyCreatedResponse,
    ApiKeyListResponse,
    ChatRequest,
    ChatResponse,
)


# ============================================================
# TESTS — ApiKeyCreate
# ============================================================

def test_api_key_create_valid():
    print("\n" + "=" * 70)
    print("TEST 1: ApiKeyCreate — válido")
    print("=" * 70)
    c = ApiKeyCreate(name="Mi web")
    assert c.name == "Mi web"
    print("  ✅ OK")


def test_api_key_create_name_required():
    print("\n" + "=" * 70)
    print("TEST 2: ApiKeyCreate — name obligatorio")
    print("=" * 70)
    try:
        ApiKeyCreate()
        raise AssertionError("Debería haber fallado")
    except ValidationError:
        print("  ✅ 422 (name required)")


def test_api_key_create_name_empty():
    print("\n" + "=" * 70)
    print("TEST 3: ApiKeyCreate — name vacío")
    print("=" * 70)
    try:
        ApiKeyCreate(name="")
        raise AssertionError("Debería haber fallado")
    except ValidationError:
        print("  ✅ 422 (min_length=1)")


def test_api_key_create_name_too_long():
    print("\n" + "=" * 70)
    print("TEST 4: ApiKeyCreate — name > 100 chars")
    print("=" * 70)
    try:
        ApiKeyCreate(name="x" * 101)
        raise AssertionError("Debería haber fallado")
    except ValidationError:
        print("  ✅ 422 (max_length=100)")


# ============================================================
# TESTS — ApiKeyResponse
# ============================================================

def test_api_key_response_valid():
    print("\n" + "=" * 70)
    print("TEST 5: ApiKeyResponse — válido (sin secret)")
    print("=" * 70)
    now = datetime.now(timezone.utc)
    r = ApiKeyResponse(
        id=1,
        name="Mi web",
        key_prefix="nvr_live_ab12",
        created_at=now,
        is_active=True,
    )
    assert r.id == 1
    assert r.key_prefix == "nvr_live_ab12"
    assert r.is_active is True
    assert r.last_used_at is None
    assert r.revoked_at is None
    assert r.expires_at is None
    assert not hasattr(r, "key"), "❌ ApiKeyResponse NO debe tener 'key'"
    assert not hasattr(r, "key_hash"), "❌ NO debe exponer key_hash"
    print("  ✅ Sin secret, sin hash")


# ============================================================
# TESTS — ApiKeyCreatedResponse
# ============================================================

def test_api_key_created_response():
    print("\n" + "=" * 70)
    print("TEST 6: ApiKeyCreatedResponse — con key + warning")
    print("=" * 70)
    now = datetime.now(timezone.utc)
    r = ApiKeyCreatedResponse(
        id=1,
        name="Mi web",
        key="nvr_live_test123456789",
        key_prefix="nvr_live_ab12",
        created_at=now,
    )
    assert r.key == "nvr_live_test123456789"
    assert "Guarda esta clave" in r.warning
    print(f"  ✅ warning: {r.warning}")


# ============================================================
# TESTS — ApiKeyListResponse
# ============================================================

def test_api_key_list_response():
    print("\n" + "=" * 70)
    print("TEST 7: ApiKeyListResponse — lista + total")
    print("=" * 70)
    now = datetime.now(timezone.utc)
    keys = [
        ApiKeyResponse(
            id=i, name=f"key-{i}", key_prefix=f"nvr_live_ab{i}",
            created_at=now, is_active=True,
        )
        for i in range(3)
    ]
    r = ApiKeyListResponse(keys=keys, total=3)
    assert len(r.keys) == 3
    assert r.total == 3
    print("  ✅ Lista + total OK")


def test_api_key_list_response_empty():
    print("\n" + "=" * 70)
    print("TEST 8: ApiKeyListResponse — vacío")
    print("=" * 70)
    r = ApiKeyListResponse(keys=[], total=0)
    assert r.keys == []
    assert r.total == 0
    print("  ✅ Lista vacía OK")


# ============================================================
# TESTS — ChatRequest
# ============================================================

def test_chat_request_valid():
    print("\n" + "=" * 70)
    print("TEST 9: ChatRequest — válido con session_id")
    print("=" * 70)
    r = ChatRequest(message="Hola", session_id="sess-123")
    assert r.message == "Hola"
    assert r.session_id == "sess-123"
    print("  ✅ OK")


def test_chat_request_no_session():
    print("\n" + "=" * 70)
    print("TEST 10: ChatRequest — sin session_id")
    print("=" * 70)
    r = ChatRequest(message="Hola")
    assert r.session_id is None
    print("  ✅ session_id opcional")


def test_chat_request_message_required():
    print("\n" + "=" * 70)
    print("TEST 11: ChatRequest — message obligatorio")
    print("=" * 70)
    try:
        ChatRequest()
        raise AssertionError("Debería haber fallado")
    except ValidationError:
        print("  ✅ 422 (message required)")


def test_chat_request_message_empty():
    print("\n" + "=" * 70)
    print("TEST 12: ChatRequest — message vacío")
    print("=" * 70)
    try:
        ChatRequest(message="")
        raise AssertionError("Debería haber fallado")
    except ValidationError:
        print("  ✅ 422 (min_length=1)")


def test_chat_request_message_too_long():
    print("\n" + "=" * 70)
    print("TEST 13: ChatRequest — message > 2000")
    print("=" * 70)
    try:
        ChatRequest(message="x" * 2001)
        raise AssertionError("Debería haber fallado")
    except ValidationError:
        print("  ✅ 422 (max_length=2000)")


def test_chat_request_session_too_long():
    print("\n" + "=" * 70)
    print("TEST 14: ChatRequest — session_id > 64")
    print("=" * 70)
    try:
        ChatRequest(message="Hola", session_id="s" * 65)
        raise AssertionError("Debería haber fallado")
    except ValidationError:
        print("  ✅ 422 (session_id max_length=64)")


# ============================================================
# TESTS — ChatResponse
# ============================================================

def test_chat_response_valid():
    print("\n" + "=" * 70)
    print("TEST 15: ChatResponse — válido")
    print("=" * 70)
    r = ChatResponse(answer="¡Hola!", session_id="sess-123")
    assert r.answer == "¡Hola!"
    assert r.session_id == "sess-123"
    assert r.status == "completed"
    print("  ✅ OK")


def test_chat_response_statuses():
    print("\n" + "=" * 70)
    print("TEST 16: ChatResponse — 3 status válidos")
    print("=" * 70)
    for st in ["completed", "waiting_input", "error"]:
        r = ChatResponse(answer="x", session_id="s", status=st)
        assert r.status == st

    try:
        ChatResponse(answer="x", session_id="s", status="invalid")
        raise AssertionError("Debería haber fallado")
    except ValidationError:
        print("  ✅ 3 status válidos + 1 inválido rechazado")


def test_chat_response_no_extra_fields():
    print("\n" + "=" * 70)
    print("TEST 17: ChatResponse — sin campos internos")
    print("=" * 70)
    r = ChatResponse(answer="x", session_id="s")
    # Campos prohibidos
    forbidden = ["workflow_id", "node_id", "variables", "api_key", "user_id", "bot_id"]
    for f in forbidden:
        assert not hasattr(r, f), f"❌ NO debe tener '{f}'"
    print(f"  ✅ Sin {len(forbidden)} campos internos")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.10.4 (Schemas Pydantic)")
    print("=" * 70)

    tests = [
        # ApiKeyCreate
        test_api_key_create_valid,
        test_api_key_create_name_required,
        test_api_key_create_name_empty,
        test_api_key_create_name_too_long,
        # ApiKeyResponse
        test_api_key_response_valid,
        # ApiKeyCreatedResponse
        test_api_key_created_response,
        # ApiKeyListResponse
        test_api_key_list_response,
        test_api_key_list_response_empty,
        # ChatRequest
        test_chat_request_valid,
        test_chat_request_no_session,
        test_chat_request_message_required,
        test_chat_request_message_empty,
        test_chat_request_message_too_long,
        test_chat_request_session_too_long,
        # ChatResponse
        test_chat_response_valid,
        test_chat_response_statuses,
        test_chat_response_no_extra_fields,
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
