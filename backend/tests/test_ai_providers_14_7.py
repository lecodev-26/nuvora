"""
Tests — Subfase 14.7.5a (Providers base)
Verifica:
    - Registry + factory
    - GeminiProvider (parseo + errores)
    - BaseOpenAICompatibleProvider (Groq / DeepSeek)
    - Parseo tolerante de JSON (markdown, texto extra)
    - Mapeo de errores HTTP
"""

import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.ai.providers import (
    get_provider,
    list_available_providers,
)
from app.core.ai.providers.gemini import GeminiProvider
from app.core.ai.providers.groq import GroqProvider
from app.core.ai.providers.deepseek import DeepSeekProvider
from app.core.ai.provider import AIRequest
from app.core.ai.errors import AIProviderError, AIInvalidOutputError, AIConfigError
from app.config import settings


# ============================================================
# HELPERS
# ============================================================

def _make_request() -> AIRequest:
    return AIRequest(
        system_prompt="Eres un diseñador de workflows.",
        user_prompt="Genera un workflow para saludar.",
        max_tokens=1000,
        timeout=10,
    )


def _mock_response(status_code: int, json_data: dict | None = None, text: str = ""):
    """Crea un mock de requests.Response."""
    m = MagicMock()
    m.status_code = status_code
    if json_data is not None:
        m.json.return_value = json_data
    else:
        m.json.side_effect = ValueError("no json")
    m.text = text
    return m


# ============================================================
# TESTS — Registry / Factory
# ============================================================

def test_list_providers():
    print("\n" + "=" * 70)
    print("TEST 1: list_available_providers")
    print("=" * 70)
    providers = list_available_providers()
    assert "gemini" in providers
    assert "groq" in providers
    assert "deepseek" in providers
    print(f"  ✅ {providers}")


def test_get_provider_ok():
    print("\n" + "=" * 70)
    print("TEST 2: get_provider devuelve instancias correctas")
    print("=" * 70)
    assert isinstance(get_provider("gemini"), GeminiProvider)
    assert isinstance(get_provider("groq"), GroqProvider)
    assert isinstance(get_provider("deepseek"), DeepSeekProvider)
    print(f"  ✅ Los 3 providers devueltos correctamente")


def test_get_provider_unknown():
    print("\n" + "=" * 70)
    print("TEST 3: get_provider desconocido → AIConfigError")
    print("=" * 70)
    try:
        get_provider("inventado")
        assert False, "Debería haber fallado"
    except AIConfigError as e:
        assert "inventado" in str(e)
        print(f"  ✅ AIConfigError: {e}")


# ============================================================
# TESTS — GeminiProvider
# ============================================================

def test_gemini_no_api_key():
    print("\n" + "=" * 70)
    print("TEST 4: Gemini sin API key → AIProviderError")
    print("=" * 70)
    # Forzar sin key
    original = settings.ai.gemini_api_key
    try:
        object.__setattr__(settings.ai, "gemini_api_key", None)
        p = GeminiProvider()
        try:
            p.generate_json(_make_request())
            assert False, "Debería haber fallado"
        except AIProviderError as e:
            assert "no configurada" in str(e).lower()
            print(f"  ✅ AIProviderError: {e}")
    finally:
        object.__setattr__(settings.ai, "gemini_api_key", original)


def test_gemini_success():
    print("\n" + "=" * 70)
    print("TEST 5: Gemini éxito (mock)")
    print("=" * 70)
    original = settings.ai.gemini_api_key
    try:
        object.__setattr__(settings.ai, "gemini_api_key", "fake-gemini-key")

        mock_json = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": '{"workflow": {"name": "Test"}, "explanation": "ok"}'}
                        ]
                    }
                }
            ],
            "usageMetadata": {"totalTokenCount": 123},
        }
        with patch("app.core.ai.providers.gemini.requests.post") as mock_post:
            mock_post.return_value = _mock_response(200, mock_json)

            p = GeminiProvider()
            resp = p.generate_json(_make_request())

            assert resp.provider == "gemini"
            assert resp.data["workflow"]["name"] == "Test"
            assert resp.tokens_used == 123
            print(f"  ✅ Gemini OK: provider={resp.provider}, tokens={resp.tokens_used}")
    finally:
        object.__setattr__(settings.ai, "gemini_api_key", original)


def test_gemini_401():
    print("\n" + "=" * 70)
    print("TEST 6: Gemini 401 → AIProviderError (no retry)")
    print("=" * 70)
    original = settings.ai.gemini_api_key
    try:
        object.__setattr__(settings.ai, "gemini_api_key", "fake-gemini-key")

        with patch("app.core.ai.providers.gemini.requests.post") as mock_post:
            mock_post.return_value = _mock_response(401, {"error": "invalid key"})

            p = GeminiProvider()
            try:
                p.generate_json(_make_request())
                assert False, "Debería haber fallado"
            except AIProviderError as e:
                assert "401" in str(e) or "inválida" in str(e).lower()
                # Solo 1 intento (no reintenta en 401)
                assert mock_post.call_count == 1
                print(f"  ✅ 401 sin retry: {e}")
    finally:
        object.__setattr__(settings.ai, "gemini_api_key", original)


def test_gemini_invalid_json():
    print("\n" + "=" * 70)
    print("TEST 7: Gemini devuelve JSON inválido → AIInvalidOutputError")
    print("=" * 70)
    original = settings.ai.gemini_api_key
    try:
        object.__setattr__(settings.ai, "gemini_api_key", "fake-gemini-key")

        mock_json = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "esto no es JSON"}]
                    }
                }
            ]
        }
        with patch("app.core.ai.providers.gemini.requests.post") as mock_post:
            mock_post.return_value = _mock_response(200, mock_json)

            p = GeminiProvider()
            try:
                p.generate_json(_make_request())
                assert False, "Debería haber fallado"
            except AIInvalidOutputError as e:
                print(f"  ✅ AIInvalidOutputError: {e.message}")
    finally:
        object.__setattr__(settings.ai, "gemini_api_key", original)


def test_gemini_json_with_markdown():
    print("\n" + "=" * 70)
    print("TEST 8: Gemini tolera bloques markdown ```json ... ```")
    print("=" * 70)
    original = settings.ai.gemini_api_key
    try:
        object.__setattr__(settings.ai, "gemini_api_key", "fake-gemini-key")

        content = '```json\n{"workflow": {"name": "Test"}}\n```'
        mock_json = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": content}]
                    }
                }
            ]
        }
        with patch("app.core.ai.providers.gemini.requests.post") as mock_post:
            mock_post.return_value = _mock_response(200, mock_json)

            p = GeminiProvider()
            resp = p.generate_json(_make_request())
            assert resp.data["workflow"]["name"] == "Test"
            print(f"  ✅ Markdown parseado correctamente")
    finally:
        object.__setattr__(settings.ai, "gemini_api_key", original)


def test_gemini_json_with_padding():
    print("\n" + "=" * 70)
    print("TEST 9: Gemini tolera texto antes/después del JSON")
    print("=" * 70)
    original = settings.ai.gemini_api_key
    try:
        object.__setattr__(settings.ai, "gemini_api_key", "fake-gemini-key")

        content = 'Aquí tienes el JSON:\n{"workflow": {"name": "Test"}}\nEspero que sirva.'
        mock_json = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": content}]
                    }
                }
            ]
        }
        with patch("app.core.ai.providers.gemini.requests.post") as mock_post:
            mock_post.return_value = _mock_response(200, mock_json)

            p = GeminiProvider()
            resp = p.generate_json(_make_request())
            assert resp.data["workflow"]["name"] == "Test"
            print(f"  ✅ JSON extraído correctamente")
    finally:
        object.__setattr__(settings.ai, "gemini_api_key", original)


# ============================================================
# TESTS — GroqProvider
# ============================================================

def test_groq_no_api_key():
    print("\n" + "=" * 70)
    print("TEST 10: Groq sin API key → AIProviderError")
    print("=" * 70)
    original = settings.ai.groq_api_key
    try:
        object.__setattr__(settings.ai, "groq_api_key", None)
        p = GroqProvider()
        try:
            p.generate_json(_make_request())
            assert False, "Debería haber fallado"
        except AIProviderError as e:
            assert "no configurada" in str(e).lower()
            print(f"  ✅ AIProviderError: {e}")
    finally:
        object.__setattr__(settings.ai, "groq_api_key", original)


def test_groq_success():
    print("\n" + "=" * 70)
    print("TEST 11: Groq éxito (mock)")
    print("=" * 70)
    original = settings.ai.groq_api_key
    try:
        object.__setattr__(settings.ai, "groq_api_key", "fake-groq-key")

        mock_json = {
            "choices": [
                {
                    "message": {
                        "content": '{"workflow": {"name": "GroqTest"}}'
                    }
                }
            ],
            "usage": {"total_tokens": 456},
        }
        with patch("app.core.ai.providers.base_openai_compatible.requests.post") as mock_post:
            mock_post.return_value = _mock_response(200, mock_json)

            p = GroqProvider()
            resp = p.generate_json(_make_request())

            assert resp.provider == "groq"
            assert resp.data["workflow"]["name"] == "GroqTest"
            assert resp.tokens_used == 456
            print(f"  ✅ Groq OK: provider={resp.provider}, tokens={resp.tokens_used}")
    finally:
        object.__setattr__(settings.ai, "groq_api_key", original)


def test_groq_401():
    print("\n" + "=" * 70)
    print("TEST 12: Groq 401 → AIProviderError (no retry)")
    print("=" * 70)
    original = settings.ai.groq_api_key
    try:
        object.__setattr__(settings.ai, "groq_api_key", "fake-groq-key")

        with patch("app.core.ai.providers.base_openai_compatible.requests.post") as mock_post:
            mock_post.return_value = _mock_response(401, {"error": "invalid key"})

            p = GroqProvider()
            try:
                p.generate_json(_make_request())
                assert False, "Debería haber fallado"
            except AIProviderError:
                assert mock_post.call_count == 1
                print(f"  ✅ 401 sin retry")
    finally:
        object.__setattr__(settings.ai, "groq_api_key", original)


def test_groq_500_retry():
    print("\n" + "=" * 70)
    print("TEST 13: Groq 500 → retry (hasta max_retries)")
    print("=" * 70)
    original = settings.ai.groq_api_key
    try:
        object.__setattr__(settings.ai, "groq_api_key", "fake-groq-key")

        with patch("app.core.ai.providers.base_openai_compatible.requests.post") as mock_post:
            mock_post.return_value = _mock_response(500, {"error": "server"})

            p = GroqProvider()
            try:
                p.generate_json(_make_request())
                assert False, "Debería haber fallado"
            except AIProviderError:
                # 1 intento + max_retries (2 por defecto) = 3
                expected = 1 + settings.ai.max_retries
                assert mock_post.call_count == expected, f"Esperaba {expected}, hubo {mock_post.call_count}"
                print(f"  ✅ Retry OK ({mock_post.call_count} intentos)")
    finally:
        object.__setattr__(settings.ai, "groq_api_key", original)


# ============================================================
# TESTS — DeepSeekProvider
# ============================================================

def test_deepseek_no_api_key():
    print("\n" + "=" * 70)
    print("TEST 14: DeepSeek sin API key → AIProviderError")
    print("=" * 70)
    original = settings.ai.deepseek_api_key
    try:
        object.__setattr__(settings.ai, "deepseek_api_key", None)
        p = DeepSeekProvider()
        try:
            p.generate_json(_make_request())
            assert False, "Debería haber fallado"
        except AIProviderError as e:
            assert "no configurada" in str(e).lower()
            print(f"  ✅ AIProviderError: {e}")
    finally:
        object.__setattr__(settings.ai, "deepseek_api_key", original)


def test_deepseek_success():
    print("\n" + "=" * 70)
    print("TEST 15: DeepSeek éxito (mock)")
    print("=" * 70)
    original = settings.ai.deepseek_api_key
    try:
        object.__setattr__(settings.ai, "deepseek_api_key", "fake-deepseek-key")

        mock_json = {
            "choices": [
                {
                    "message": {
                        "content": '{"workflow": {"name": "DS"}}'
                    }
                }
            ],
            "usage": {"total_tokens": 789},
        }
        with patch("app.core.ai.providers.base_openai_compatible.requests.post") as mock_post:
            mock_post.return_value = _mock_response(200, mock_json)

            p = DeepSeekProvider()
            resp = p.generate_json(_make_request())

            assert resp.provider == "deepseek"
            assert resp.tokens_used == 789
            print(f"  ✅ DeepSeek OK: provider={resp.provider}, tokens={resp.tokens_used}")
    finally:
        object.__setattr__(settings.ai, "deepseek_api_key", original)


# ============================================================
# TESTS — Regresión
# ============================================================

def test_regression_app_imports():
    print("\n" + "=" * 70)
    print("TEST 16: Regresión — app.main sigue OK")
    print("=" * 70)
    from app.main import app as _app
    assert _app is not None
    print(f"  ✅ app OK ({len(_app.routes)} rutas)")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.7.5a (Providers)")
    print("=" * 70)

    tests = [
        test_list_providers,
        test_get_provider_ok,
        test_get_provider_unknown,
        test_gemini_no_api_key,
        test_gemini_success,
        test_gemini_401,
        test_gemini_invalid_json,
        test_gemini_json_with_markdown,
        test_gemini_json_with_padding,
        test_groq_no_api_key,
        test_groq_success,
        test_groq_401,
        test_groq_500_retry,
        test_deepseek_no_api_key,
        test_deepseek_success,
        test_regression_app_imports,
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
