"""
Tests — Subfase 14.7.2
Verifica:
    - app/config.py (settings centralizado)
    - app/core/ai/provider.py (interfaz)
    - app/core/ai/errors.py (errores)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings, AIConfig, AppConfig
from app.core.ai import (
    AIProvider,
    AIRequest,
    AIResponse,
    AIError,
    AIProviderError,
    AIInvalidOutputError,
    AIConfigError,
    AIUnavailableError,
)


# ============================================================
# TEST 1 — settings cargado
# ============================================================

def test_settings_loaded():
    print("\n" + "=" * 70)
    print("TEST 1: settings cargado con valores por defecto")
    print("=" * 70)
    assert settings is not None
    assert settings.name is not None
    assert settings.version is not None
    assert settings.ai is not None
    print(f"  ✅ settings.name = {settings.name}")
    print(f"  ✅ settings.ai.provider = {settings.ai.provider}")


# ============================================================
# TEST 2 — AIConfig por defecto
# ============================================================

def test_aiconfig_defaults():
    print("\n" + "=" * 70)
    print("TEST 2: AIConfig defaults")
    print("=" * 70)
    cfg = AIConfig()
    assert cfg.provider == "gemini"
    assert cfg.timeout_seconds == 30
    assert cfg.max_retries == 2
    assert cfg.enabled is True
    print(f"  ✅ provider={cfg.provider}, timeout={cfg.timeout_seconds}s, retries={cfg.max_retries}")


# ============================================================
# TEST 3 — get_api_key_for
# ============================================================

def test_get_api_key_for():
    print("\n" + "=" * 70)
    print("TEST 3: AIConfig.get_api_key_for()")
    print("=" * 70)
    cfg = AIConfig(
        gemini_api_key="g-key",
        groq_api_key="q-key",
        deepseek_api_key="d-key",
    )
    assert cfg.get_api_key_for("gemini") == "g-key"
    assert cfg.get_api_key_for("groq") == "q-key"
    assert cfg.get_api_key_for("deepseek") == "d-key"
    assert cfg.get_api_key_for("unknown") is None
    print(f"  ✅ Keys devueltas correctamente por provider")


# ============================================================
# TEST 4 — get_model_for
# ============================================================

def test_get_model_for():
    print("\n" + "=" * 70)
    print("TEST 4: AIConfig.get_model_for()")
    print("=" * 70)
    cfg = AIConfig()
    assert cfg.get_model_for("gemini") != "unknown"
    assert cfg.get_model_for("groq") != "unknown"
    assert cfg.get_model_for("deepseek") != "unknown"
    assert cfg.get_model_for("unknown") == "unknown"
    print(f"  ✅ Modelos devueltos correctamente")


# ============================================================
# TEST 5 — AIRequest y AIResponse
# ============================================================

def test_request_response_dataclasses():
    print("\n" + "=" * 70)
    print("TEST 5: AIRequest y AIResponse dataclasses")
    print("=" * 70)
    req = AIRequest(
        system_prompt="Eres X",
        user_prompt="Haz Y",
    )
    assert req.max_tokens == 4000
    assert req.timeout == 30

    res = AIResponse(
        data={"nodes": []},
        provider="gemini",
        model="gemini-2.5-flash",
    )
    assert res.data == {"nodes": []}
    assert res.provider == "gemini"
    print(f"  ✅ AIRequest y AIResponse OK")


# ============================================================
# TEST 6 — AIProvider es abstracta
# ============================================================

def test_ai_provider_is_abstract():
    print("\n" + "=" * 70)
    print("TEST 6: AIProvider es abstracta (no se puede instanciar)")
    print("=" * 70)
    try:
        _ = AIProvider()
        assert False, "Debería haber fallado"
    except TypeError:
        print(f"  ✅ AIProvider no se puede instanciar directamente")


# ============================================================
# TEST 7 — Errores heredan de AIError
# ============================================================

def test_errors_hierarchy():
    print("\n" + "=" * 70)
    print("TEST 7: Jerarquía de errores")
    print("=" * 70)
    assert issubclass(AIProviderError, AIError)
    assert issubclass(AIInvalidOutputError, AIError)
    assert issubclass(AIConfigError, AIError)
    assert issubclass(AIUnavailableError, AIError)

    err = AIProviderError(provider="gemini", message="timeout")
    assert err.provider == "gemini"
    assert "gemini" in str(err)
    print(f"  ✅ Jerarquía OK: {err}")


# ============================================================
# TEST 8 — AIInvalidOutputError con raw_output
# ============================================================

def test_invalid_output_error():
    print("\n" + "=" * 70)
    print("TEST 8: AIInvalidOutputError conserva raw_output")
    print("=" * 70)
    err = AIInvalidOutputError("JSON inválido", raw_output="{bad json}")
    assert err.raw_output == "{bad json}"
    print(f"  ✅ raw_output conservado")


# ============================================================
# TEST 9 — Regresión: WorkflowValidator sigue funcionando
# ============================================================

def test_workflow_validator_still_works():
    print("\n" + "=" * 70)
    print("TEST 9: Regresión — WorkflowValidator de 14.5 sigue OK")
    print("=" * 70)
    from app.core.workflows.validator import WorkflowValidator
    v = WorkflowValidator()
    v.validate({
        "nodes": [
            {"node_id": "s1", "type": "start"},
            {"node_id": "e1", "type": "end"},
        ],
        "transitions": [
            {"from_node_id": "s1", "to_node_id": "e1"},
        ],
    })
    print(f"  ✅ WorkflowValidator OK")


# ============================================================
# TEST 10 — Regresión: app importa sin errores
# ============================================================

def test_app_imports():
    print("\n" + "=" * 70)
    print("TEST 10: Regresión — app.main importa")
    print("=" * 70)
    from app.main import app
    assert app is not None
    print(f"  ✅ app.main importada ({len(app.routes)} rutas)")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.7.2 (Config + AIProvider interface)")
    print("=" * 70)

    tests = [
        test_settings_loaded,
        test_aiconfig_defaults,
        test_get_api_key_for,
        test_get_model_for,
        test_request_response_dataclasses,
        test_ai_provider_is_abstract,
        test_errors_hierarchy,
        test_invalid_output_error,
        test_workflow_validator_still_works,
        test_app_imports,
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
