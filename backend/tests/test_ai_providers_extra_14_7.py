"""
Tests — Subfase 14.7.5b (Providers extra)
Verifica:
    - OpenAIProvider (OpenAI-compatible)
    - MistralProvider (OpenAI-compatible)
    - AnthropicProvider (API propia, prefill)
    - OllamaProvider (local, sin key)
    - Registry total: 7 providers
    - Config: 7 modelos + keys
"""

import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.ai.providers import get_provider, list_available_providers
from app.core.ai.providers.openai import OpenAIProvider
from app.core.ai.providers.mistral import MistralProvider
from app.core.ai.providers.anthropic import AnthropicProvider
from app.core.ai.providers.ollama import OllamaProvider
from app.core.ai.provider import AIRequest
from app.core.ai.errors import AIProviderError, AIInvalidOutputError
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
    m = MagicMock()
    m.status_code = status_code
    if json_data is not None:
        m.json.return_value = json_data
    else:
        m.json.side_effect = ValueError("no json")
    m.text = text
    return m


# ============================================================
# TESTS — Registry (los 7)
# ============================================================

def test_all_7_providers_registered():
    print("\n" + "=" * 70)
    print("TEST 1: Los 7 providers están registrados")
    print("=" * 70)
    providers = list_available_providers()
    expected = {"gemini", "groq", "deepseek", "openai", "mistral", "anthropic", "ollama"}
    assert set(providers) == expected, f"Esperaba {expected}, obtuve {providers}"
    print(f"  ✅ {providers}")


def test_get_provider_extra():
    print("\n" + "=" * 70)
    print("TEST 2: get_provider devuelve los 4 nuevos correctamente")
    print("=" * 70)
    assert isinstance(get_provider("openai"), OpenAIProvider)
    assert isinstance(get_provider("mistral"), MistralProvider)
    assert isinstance(get_provider("anthropic"), AnthropicProvider)
    assert isinstance(get_provider("ollama"), OllamaProvider)
    print(f"  ✅ Los 4 providers extra devueltos correctamente")


# ============================================================
# TESTS — OpenAIProvider
# ============================================================

def test_openai_no_api_key():
    print("\n" + "=" * 70)
    print("TEST 3: OpenAI sin API key → AIProviderError")
    print("=" * 70)
    original = settings.ai.openai_api_key
    try:
        object.__setattr__(settings.ai, "openai_api_key", None)
        p = OpenAIProvider()
        try:
            p.generate_json(_make_request())
            assert False, "Debería haber fallado"
        except AIProviderError as e:
            assert "no configurada" in str(e).lower()
            print(f"  ✅ AIProviderError: {e}")
    finally:
        object.__setattr__(settings.ai, "openai_api_key", original)


def test_openai_success():
    print("\n" + "=" * 70)
    print("TEST 4: OpenAI éxito (mock)")
    print("=" * 70)
    original = settings.ai.openai_api_key
    try:
        object.__setattr__(settings.ai, "openai_api_key", "fake-openai-key")

        mock_json = {
            "choices": [{"message": {"content": '{"workflow": {"name": "OAI"}}'}}],
            "usage": {"total_tokens": 111},
        }
        with patch("app.core.ai.providers.base_openai_compatible.requests.post") as mock_post:
            mock_post.return_value = _mock_response(200, mock_json)

            p = OpenAIProvider()
            resp = p.generate_json(_make_request())

            assert resp.provider == "openai"
            assert resp.data["workflow"]["name"] == "OAI"
            assert resp.tokens_used == 111
            print(f"  ✅ OpenAI OK: provider={resp.provider}, tokens={resp.tokens_used}")
    finally:
        object.__setattr__(settings.ai, "openai_api_key", original)


# ============================================================
# TESTS — MistralProvider
# ============================================================

def test_mistral_no_api_key():
    print("\n" + "=" * 70)
    print("TEST 5: Mistral sin API key → AIProviderError")
    print("=" * 70)
    original = settings.ai.mistral_api_key
    try:
        object.__setattr__(settings.ai, "mistral_api_key", None)
        p = MistralProvider()
        try:
            p.generate_json(_make_request())
            assert False, "Debería haber fallado"
        except AIProviderError as e:
            assert "no configurada" in str(e).lower()
            print(f"  ✅ AIProviderError: {e}")
    finally:
        object.__setattr__(settings.ai, "mistral_api_key", original)


def test_mistral_success():
    print("\n" + "=" * 70)
    print("TEST 6: Mistral éxito (mock)")
    print("=" * 70)
    original = settings.ai.mistral_api_key
    try:
        object.__setattr__(settings.ai, "mistral_api_key", "fake-mistral-key")

        mock_json = {
            "choices": [{"message": {"content": '{"workflow": {"name": "Mistral"}}'}}],
            "usage": {"total_tokens": 222},
        }
        with patch("app.core.ai.providers.base_openai_compatible.requests.post") as mock_post:
            mock_post.return_value = _mock_response(200, mock_json)

            p = MistralProvider()
            resp = p.generate_json(_make_request())

            assert resp.provider == "mistral"
            assert resp.tokens_used == 222
            print(f"  ✅ Mistral OK: provider={resp.provider}, tokens={resp.tokens_used}")
    finally:
        object.__setattr__(settings.ai, "mistral_api_key", original)


# ============================================================
# TESTS — AnthropicProvider
# ============================================================

def test_anthropic_no_api_key():
    print("\n" + "=" * 70)
    print("TEST 7: Anthropic sin API key → AIProviderError")
    print("=" * 70)
    original = settings.ai.anthropic_api_key
    try:
        object.__setattr__(settings.ai, "anthropic_api_key", None)
        p = AnthropicProvider()
        try:
            p.generate_json(_make_request())
            assert False, "Debería haber fallado"
        except AIProviderError as e:
            assert "no configurada" in str(e).lower()
            print(f"  ✅ AIProviderError: {e}")
    finally:
        object.__setattr__(settings.ai, "anthropic_api_key", original)


def test_anthropic_success_prefill():
    print("\n" + "=" * 70)
    print("TEST 8: Anthropic éxito con prefill de '{' (mock)")
    print("=" * 70)
    original = settings.ai.anthropic_api_key
    try:
        object.__setattr__(settings.ai, "anthropic_api_key", "fake-anthropic-key")

        # Anthropic devuelve el texto SIN el "{" inicial (por el prefill)
        mock_json = {
            "content": [
                {"type": "text", "text": '"workflow": {"name": "Claude"}}'}
            ],
            "usage": {"input_tokens": 100, "output_tokens": 50},
        }
        with patch("app.core.ai.providers.anthropic.requests.post") as mock_post:
            mock_post.return_value = _mock_response(200, mock_json)

            p = AnthropicProvider()
            resp = p.generate_json(_make_request())

            assert resp.provider == "anthropic"
            assert resp.data["workflow"]["name"] == "Claude"
            # 100 + 50 = 150 tokens
            assert resp.tokens_used == 150
            print(f"  ✅ Anthropic OK (prefill): provider={resp.provider}, tokens={resp.tokens_used}")
    finally:
        object.__setattr__(settings.ai, "anthropic_api_key", original)


def test_anthropic_payload_has_prefill():
    print("\n" + "=" * 70)
    print("TEST 9: Anthropic payload incluye prefill con '{'")
    print("=" * 70)
    p = AnthropicProvider()
    payload = p._build_payload(_make_request(), "claude-3-5-haiku-latest")

    assert payload["system"].endswith("solo el JSON.")
    messages = payload["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "{"
    print(f"  ✅ Prefill OK: assistant inicia con '{{'")


# ============================================================
# TESTS — OllamaProvider
# ============================================================

def test_ollama_uses_placeholder_key():
    print("\n" + "=" * 70)
    print("TEST 10: Ollama usa placeholder key (no requiere real)")
    print("=" * 70)
    p = OllamaProvider()
    key = p.get_api_key()
    assert key == "ollama-local-no-key-required"
    print(f"  ✅ Placeholder OK: '{key}'")


def test_ollama_base_url_from_settings():
    print("\n" + "=" * 70)
    print("TEST 11: Ollama lee base_url de settings")
    print("=" * 70)
    original = settings.ai.ollama_base_url
    try:
        object.__setattr__(settings.ai, "ollama_base_url", "http://test-ollama:11434/v1")
        p = OllamaProvider()
        assert p.base_url == "http://test-ollama:11434/v1"
        print(f"  ✅ base_url dinámica OK: {p.base_url}")
    finally:
        object.__setattr__(settings.ai, "ollama_base_url", original)


def test_ollama_no_authorization_header():
    print("\n" + "=" * 70)
    print("TEST 12: Ollama no envía Authorization")
    print("=" * 70)
    p = OllamaProvider()
    headers = p._build_headers("fake")
    assert "Authorization" not in headers
    assert headers["Content-Type"] == "application/json"
    print(f"  ✅ Sin Authorization OK: {headers}")


def test_ollama_success():
    print("\n" + "=" * 70)
    print("TEST 13: Ollama éxito (mock)")
    print("=" * 70)
    mock_json = {
        "choices": [{"message": {"content": '{"workflow": {"name": "Local"}}'}}],
        "usage": {"total_tokens": 333},
    }
    with patch("app.core.ai.providers.base_openai_compatible.requests.post") as mock_post:
        mock_post.return_value = _mock_response(200, mock_json)

        p = OllamaProvider()
        resp = p.generate_json(_make_request())

        assert resp.provider == "ollama"
        assert resp.data["workflow"]["name"] == "Local"
        assert resp.tokens_used == 333
        print(f"  ✅ Ollama OK: provider={resp.provider}, tokens={resp.tokens_used}")


# ============================================================
# TESTS — Config
# ============================================================

def test_config_models_for_all_providers():
    print("\n" + "=" * 70)
    print("TEST 14: settings.ai.get_model_for devuelve modelos para los 7")
    print("=" * 70)
    for p in ["gemini", "groq", "deepseek", "openai", "mistral", "anthropic", "ollama"]:
        model = settings.ai.get_model_for(p)
        assert model != "unknown", f"Sin modelo para {p}"
    print(f"  ✅ Los 7 providers tienen modelo por defecto")


def test_config_api_key_for_all_providers():
    print("\n" + "=" * 70)
    print("TEST 15: settings.ai.get_api_key_for responde para los 7")
    print("=" * 70)
    # Ollama devuelve un placeholder
    ollama_key = settings.ai.get_api_key_for("ollama")
    assert ollama_key == "ollama-local-no-key-required"
    # Los demás devuelven None si no están configurados (o el valor)
    for p in ["gemini", "groq", "deepseek", "openai", "mistral", "anthropic"]:
        _ = settings.ai.get_api_key_for(p)  # no debe romper
    print(f"  ✅ Los 7 providers responden a get_api_key_for")


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
    print("🧪 TESTS — SUBFASE 14.7.5b (Providers extra)")
    print("=" * 70)

    tests = [
        test_all_7_providers_registered,
        test_get_provider_extra,
        test_openai_no_api_key,
        test_openai_success,
        test_mistral_no_api_key,
        test_mistral_success,
        test_anthropic_no_api_key,
        test_anthropic_success_prefill,
        test_anthropic_payload_has_prefill,
        test_ollama_uses_placeholder_key,
        test_ollama_base_url_from_settings,
        test_ollama_no_authorization_header,
        test_ollama_success,
        test_config_models_for_all_providers,
        test_config_api_key_for_all_providers,
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
