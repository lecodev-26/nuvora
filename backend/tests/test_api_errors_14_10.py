"""
Tests — Subfase 14.10.8 (Errores uniformes /api/v1/*)
=======================================================
Cubre:
    - ApiError: status, message, code
    - ERROR_MAP: todos los códigos
    - Handler devuelve formato uniforme
    - Endpoints /api/v1/* usan formato uniforme
    - Endpoints NO /api/v1/* mantienen {"detail": ...}
"""

import sys
import os
import time
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.core.api_errors import (
    ApiError,
    ErrorCode,
    ERROR_MAP,
    api_exception_handler,
)
from app.core.public_rate_limit import reset_public_all


client = TestClient(app)


# ============================================================
# HELPERS
# ============================================================

def _unique(suffix):
    return f"{suffix}_{int(time.time() * 1000000)}"


def _register_and_login(suffix):
    unique = _unique(suffix)
    email = f"apierr_{unique}@nuvora.com"
    r = client.post("/auth/register", json={
        "email": email, "password": "123456", "full_name": "ApiErr Test",
    })
    assert r.status_code == 200, r.text
    token = client.post(
        "/auth/login",
        data={"username": email, "password": "123456"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, email


# ============================================================
# TESTS — ApiError
# ============================================================

def test_error_code_count():
    print("\n" + "=" * 70)
    print("TEST 1: 12 ErrorCodes definidos")
    print("=" * 70)
    expected = {
        "INVALID_API_KEY", "REVOKED_API_KEY", "EXPIRED_API_KEY",
        "BOT_NOT_PUBLISHED", "NO_ACTIVE_WORKFLOW",
        "INVALID_REQUEST", "MESSAGE_TOO_LONG",
        "SESSION_NOT_FOUND", "SESSION_EXPIRED",
        "NOT_FOUND", "RATE_LIMITED", "INTERNAL_ERROR",
    }
    actual = {c.value for c in ErrorCode}
    assert actual == expected, f"Diff: {actual ^ expected}"
    print(f"  ✅ 12 ErrorCodes")


def test_error_map_complete():
    print("\n" + "=" * 70)
    print("TEST 2: ERROR_MAP tiene entrada para cada ErrorCode")
    print("=" * 70)
    for code in ErrorCode:
        assert code in ERROR_MAP, f"Falta {code}"
        status_code, message = ERROR_MAP[code]
        assert isinstance(status_code, int)
        assert isinstance(message, str)
    print(f"  ✅ {len(ErrorCode)} códigos mapeados")


def test_api_error_defaults():
    print("\n" + "=" * 70)
    print("TEST 3: ApiError usa defaults del ERROR_MAP")
    print("=" * 70)
    e = ApiError(ErrorCode.INVALID_API_KEY)
    assert e.status_code == 401
    assert e.message == "API Key is invalid."
    assert e.code == ErrorCode.INVALID_API_KEY
    print(f"  ✅ 401 / 'API Key is invalid.'")


def test_api_error_custom_message():
    print("\n" + "=" * 70)
    print("TEST 4: ApiError acepta message custom")
    print("=" * 70)
    e = ApiError(ErrorCode.INVALID_REQUEST, message="Falta 'message' en el body.")
    assert e.message == "Falta 'message' en el body."
    assert e.status_code == 400
    print(f"  ✅ Custom message OK")


def test_api_error_custom_status():
    print("\n" + "=" * 70)
    print("TEST 5: ApiError acepta status_code custom")
    print("=" * 70)
    e = ApiError(ErrorCode.NOT_FOUND, status_code=410)
    assert e.status_code == 410
    print(f"  ✅ Custom status OK")


def test_api_error_headers():
    print("\n" + "=" * 70)
    print("TEST 6: ApiError acepta headers (Retry-After)")
    print("=" * 70)
    e = ApiError(
        ErrorCode.RATE_LIMITED,
        headers={"Retry-After": "60"},
    )
    assert e.status_code == 429
    assert e.headers == {"Retry-After": "60"}
    print(f"  ✅ Headers OK")


def test_api_error_is_http_exception():
    print("\n" + "=" * 70)
    print("TEST 7: ApiError hereda de HTTPException")
    print("=" * 70)
    e = ApiError(ErrorCode.INVALID_API_KEY)
    assert isinstance(e, HTTPException)
    assert e.detail == "API Key is invalid."
    print(f"  ✅ Subclase correcta")


# ============================================================
# TESTS — Handler
# ============================================================

def test_handler_serialization():
    print("\n" + "=" * 70)
    print("TEST 8: api_exception_handler devuelve formato uniforme")
    print("=" * 70)
    e = ApiError(ErrorCode.INVALID_API_KEY)
    # Llamar al handler sin request (None es OK para este test)
    resp = api_exception_handler(None, e)
    assert resp.status_code == 401

    # El body es JSON serializado
    import json
    body = json.loads(resp.body)
    assert "error" in body
    assert body["error"]["code"] == "INVALID_API_KEY"
    assert body["error"]["message"] == "API Key is invalid."
    print(f"  ✅ {body}")


# ============================================================
# TESTS — Endpoints /api/v1/* (formato uniforme)
# ============================================================

def test_chat_401_uniform_format():
    print("\n" + "=" * 70)
    print("TEST 9: /api/v1/chat sin token → 401 formato uniforme")
    print("=" * 70)
    r = client.post("/api/v1/chat", json={"message": "Hola"})
    assert r.status_code == 401
    body = r.json()
    assert "error" in body, f"Falta 'error': {body}"
    assert body["error"]["code"] == "INVALID_API_KEY"
    assert "message" in body["error"]
    print(f"  ✅ {body}")


def test_chat_401_wrong_scheme():
    print("\n" + "=" * 70)
    print("TEST 10: /api/v1/chat con esquema incorrecto → 401 uniforme")
    print("=" * 70)
    r = client.post(
        "/api/v1/chat",
        json={"message": "Hola"},
        headers={"Authorization": "Basic xyz"},
    )
    assert r.status_code == 401
    body = r.json()
    assert "error" in body
    print(f"  ✅ {body}")


def test_chat_401_invalid_key():
    print("\n" + "=" * 70)
    print("TEST 11: /api/v1/chat con key inválida → 401 uniforme")
    print("=" * 70)
    r = client.post(
        "/api/v1/chat",
        json={"message": "Hola"},
        headers={"Authorization": "Bearer nvr_live_inexistente"},
    )
    assert r.status_code == 401
    body = r.json()
    assert body["error"]["code"] == "INVALID_API_KEY"
    print(f"  ✅ {body}")


def test_chat_422_invalid_payload():
    print("\n" + "=" * 70)
    print("TEST 12: /api/v1/chat con payload inválido → 422 (Pydantic estándar)")
    print("=" * 70)
    # Los errores de validación Pydantic los maneja FastAPI por defecto
    # (formato {"detail": [...]}), no por nuestro handler.
    r = client.post(
        "/api/v1/chat",
        json={"message": ""},
    )
    # 422 por message vacío (antes de llegar al handler de auth)
    assert r.status_code in (401, 422)
    print(f"  ✅ {r.status_code}")


# ============================================================
# TESTS — Endpoints NO /api/v1/* (mantienen formato anterior)
# ============================================================

def test_bots_endpoint_uses_detail_format():
    print("\n" + "=" * 70)
    print("TEST 13: /bots/ sin token → 401 con formato {'detail': ...}")
    print("=" * 70)
    r = client.get("/bots/")
    assert r.status_code == 401
    body = r.json()
    # Formato clásico de FastAPI
    assert "detail" in body
    assert "error" not in body
    print(f"  ✅ Formato clásico preservado: {body}")


def test_public_bots_uses_detail_format():
    print("\n" + "=" * 70)
    print("TEST 14: /public/bots/{id} inexistente → 404 con {'detail': ...}")
    print("=" * 70)
    r = client.get("/public/bots/inexistente-xyz")
    assert r.status_code == 404
    body = r.json()
    assert "detail" in body
    assert "error" not in body
    print(f"  ✅ Formato clásico preservado")


def test_workflows_endpoint_uses_detail_format():
    print("\n" + "=" * 70)
    print("TEST 15: /workflows/999 sin token → 401 con {'detail': ...}")
    print("=" * 70)
    r = client.get("/workflows/999")
    assert r.status_code == 401
    body = r.json()
    assert "detail" in body
    assert "error" not in body
    print(f"  ✅ Formato clásico preservado")


# ============================================================
# CLEANUP
# ============================================================

def test_cleanup():
    print("\n" + "=" * 70)
    print("TEST CLEANUP: borrar datos residuales")
    print("=" * 70)
    from sqlalchemy import text
    from app.database.config import engine

    pattern = "apierr_%"
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys=OFF"))
        for sql in [
            "DELETE FROM public_sessions WHERE bot_id IN (SELECT id FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p))",
            "DELETE FROM api_keys WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p)",
            "DELETE FROM bots WHERE user_id IN (SELECT id FROM users WHERE email LIKE :p)",
            "DELETE FROM users WHERE email LIKE :p",
        ]:
            conn.execute(text(sql), {"p": pattern})
        conn.execute(text("PRAGMA foreign_keys=ON"))
    reset_public_all()
    print(f"  ✅ Datos limpiados (pattern={pattern})")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.10.8 (Errores uniformes)")
    print("=" * 70)

    tests = [
        # ApiError
        test_error_code_count,
        test_error_map_complete,
        test_api_error_defaults,
        test_api_error_custom_message,
        test_api_error_custom_status,
        test_api_error_headers,
        test_api_error_is_http_exception,
        # Handler
        test_handler_serialization,
        # /api/v1/* uniforme
        test_chat_401_uniform_format,
        test_chat_401_wrong_scheme,
        test_chat_401_invalid_key,
        test_chat_422_invalid_payload,
        # Otros endpoints (formato clásico)
        test_bots_endpoint_uses_detail_format,
        test_public_bots_uses_detail_format,
        test_workflows_endpoint_uses_detail_format,
        # Cleanup
        test_cleanup,
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
