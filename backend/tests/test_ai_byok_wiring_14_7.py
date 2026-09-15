"""
Tests — Subfase 14.7.5c (Wiring BYOK)
Verifica:
    - get_provider() sin db/user_id → modo sistema
    - get_provider() con db/user_id + BYOK → usa la key propia
    - get_provider() con db/user_id sin BYOK → fallback al sistema
    - Providers respetan api_key_override en get_api_key()
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.ai.providers import get_provider, list_available_providers
from app.core.ai.providers.gemini import GeminiProvider
from app.core.ai.providers.openai import OpenAIProvider
from app.core.ai.providers.anthropic import AnthropicProvider
from app.core.ai.providers.ollama import OllamaProvider
from app.database.config import SessionLocal
from app.models.db_models import User, UserAIConfig
from app.services.ai_config_service import set_user_config


# ============================================================
# TESTS
# ============================================================

def test_provider_sistema_no_override():
    print("\n" + "=" * 70)
    print("TEST 1: get_provider sin db/user_id → modo sistema")
    print("=" * 70)
    p = get_provider("gemini")
    assert isinstance(p, GeminiProvider)
    assert p.api_key_override is None
    print(f"  ✅ override=None (modo sistema)")


def test_provider_byok_manual_override():
    print("\n" + "=" * 70)
    print("TEST 2: get_provider con api_key_override manual")
    print("=" * 70)
    p = get_provider("openai")
    p.api_key_override = "manual-byok-key"
    assert p.get_api_key() == "manual-byok-key"
    assert p._resolve_api_key() == "manual-byok-key"
    print(f"  ✅ override respetado: {p.get_api_key()}")


def test_provider_byok_with_db():
    print("\n" + "=" * 70)
    print("TEST 3: get_provider con db/user_id + BYOK configurado")
    print("=" * 70)
    db = SessionLocal()
    try:
        # Crear usuario temporal
        u = User(
            email=f"test_wiring_{int(time.time()*1000)}@nuvora.com",
            hashed_password="x",
            is_active=True,
        )
        db.add(u)
        db.commit()
        db.refresh(u)

        # Configurar BYOK
        set_user_config(db, u.id, "openai", "byok-test-key-12345")

        # get_provider con db + user_id → debe usar la BYOK
        p = get_provider("openai", db=db, user_id=u.id)
        assert isinstance(p, OpenAIProvider)
        assert p.api_key_override == "byok-test-key-12345"
        assert p.get_api_key() == "byok-test-key-12345"
        print(f"  ✅ BYOK usado: {p.get_api_key()}")

        # Limpieza
        db.query(UserAIConfig).filter(UserAIConfig.user_id == u.id).delete()
        db.query(User).filter(User.id == u.id).delete()
        db.commit()
    finally:
        db.close()


def test_provider_fallback_when_no_byok():
    print("\n" + "=" * 70)
    print("TEST 4: get_provider con db/user_id sin BYOK → fallback sistema")
    print("=" * 70)
    from app.config import settings

    db = SessionLocal()
    try:
        # Crear usuario SIN BYOK
        u = User(
            email=f"test_wiring_{int(time.time()*1000)}@nuvora.com",
            hashed_password="x",
            is_active=True,
        )
        db.add(u)
        db.commit()
        db.refresh(u)

        # get_provider con db + user_id pero SIN BYOK
        p = get_provider("gemini", db=db, user_id=u.id)
        assert isinstance(p, GeminiProvider)

        # Sin BYOK → el override NO debe ser None (cae al sistema),
        # o debe ser None si el sistema tampoco tiene key configurada.
        # En cualquier caso: `get_api_key()` debe devolver algo coherente.
        system_key = settings.ai.gemini_api_key
        if system_key:
            # Hay key del sistema → el override debe ser esa key
            assert p.api_key_override == system_key
            print(f"  ✅ Fallback al sistema: override=SÍ (key del sistema)")
        else:
            # No hay key del sistema → override=None
            assert p.api_key_override is None
            print(f"  ✅ Fallback al sistema: override=None (sin key)")

        # Limpieza
        db.query(User).filter(User.id == u.id).delete()
        db.commit()
    finally:
        db.close()


def test_provider_default_from_settings():
    print("\n" + "=" * 70)
    print("TEST 5: get_provider() sin name usa settings.ai.provider")
    print("=" * 70)
    from app.config import settings
    p = get_provider()
    # Debe coincidir con settings.ai.provider
    expected = settings.ai.provider
    assert p.name == expected
    print(f"  ✅ Provider default: {p.name} (settings.ai.provider={expected})")


def test_all_7_providers_support_override():
    print("\n" + "=" * 70)
    print("TEST 6: Los 7 providers respetan api_key_override")
    print("=" * 70)
    for name in list_available_providers():
        p = get_provider(name)
        p.api_key_override = f"test-override-{name}"
        # Todos deben devolver el override (excepto Ollama que
        # también lo respeta ahora por consistencia)
        key = p.get_api_key()
        assert key == f"test-override-{name}", f"{name}: esperaba override, obtuve {key}"
    print(f"  ✅ Los 7 providers respetan api_key_override")


def test_anthropic_override():
    print("\n" + "=" * 70)
    print("TEST 7: AnthropicProvider respeta override")
    print("=" * 70)
    p = get_provider("anthropic")
    p.api_key_override = "anthropic-byok-key"
    assert p.get_api_key() == "anthropic-byok-key"
    print(f"  ✅ Anthropic override: {p.get_api_key()}")


def test_ollama_override():
    print("\n" + "=" * 70)
    print("TEST 8: OllamaProvider respeta override (aunque no lo necesite)")
    print("=" * 70)
    p = get_provider("ollama")
    p.api_key_override = "ollama-custom-placeholder"
    assert p.get_api_key() == "ollama-custom-placeholder"

    # Sin override → placeholder por defecto
    p2 = get_provider("ollama")
    assert p2.get_api_key() == "ollama-local-no-key-required"
    print(f"  ✅ Ollama respeta override y fallback")


# ============================================================
# REGRESIÓN
# ============================================================

def test_regression_providers_still_ok():
    print("\n" + "=" * 70)
    print("TEST 9: Regresión — los 7 providers siguen registrados")
    print("=" * 70)
    providers = list_available_providers()
    assert len(providers) == 7
    print(f"  ✅ {providers}")


def test_regression_app_imports():
    print("\n" + "=" * 70)
    print("TEST 10: Regresión — app.main sigue OK")
    print("=" * 70)
    from app.main import app as _app
    assert _app is not None
    print(f"  ✅ app OK ({len(_app.routes)} rutas)")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.7.5c (Wiring BYOK)")
    print("=" * 70)

    tests = [
        test_provider_sistema_no_override,
        test_provider_byok_manual_override,
        test_provider_byok_with_db,
        test_provider_fallback_when_no_byok,
        test_provider_default_from_settings,
        test_all_7_providers_support_override,
        test_anthropic_override,
        test_ollama_override,
        test_regression_providers_still_ok,
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
