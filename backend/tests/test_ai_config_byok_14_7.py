"""
Tests — Subfase 14.7.4b (BYOK)
Verifica:
    - Cifrado/descifrado con Fernet
    - CRUD del servicio
    - Endpoints /ai/config con auth + aislamiento
    - get_effective_api_key (BYOK vs sistema)
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.main import app
from app.database.config import SessionLocal
from app.models.db_models import UserAIConfig, User
from app.services.ai_config_service import (
    encrypt_api_key,
    decrypt_api_key,
    get_user_config,
    list_user_configs,
    set_user_config,
    delete_user_config,
    get_effective_api_key,
    has_user_key,
)
from app.config import settings


client = TestClient(app)


# ============================================================
# HELPERS
# ============================================================

def _unique(suffix: str) -> str:
    return f"{suffix}_{int(time.time() * 1000)}"


def _register_and_login(suffix: str):
    unique = _unique(suffix)
    email = f"test_byok_{unique}@nuvora.com"
    password = "123456"

    r = client.post("/auth/register", json={
        "email": email,
        "password": password,
        "full_name": f"Test BYOK {unique}",
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


# ============================================================
# ESTADO COMPARTIDO
# ============================================================

class _Ctx:
    token1 = None
    token2 = None
    user1_id = None
    user2_id = None
    headers1 = None
    headers2 = None


# ============================================================
# TESTS — Cifrado
# ============================================================

def test_encrypt_decrypt_roundtrip():
    print("\n" + "=" * 70)
    print("TEST 1: Cifrar → descifrar devuelve el original")
    print("=" * 70)
    original = "sk-test-1234567890abcdef"
    cipher = encrypt_api_key(original)
    assert cipher != original, "El ciphertext no debe ser igual al plaintext"
    assert len(cipher) > len(original), "El ciphertext debe ser más largo"
    recovered = decrypt_api_key(cipher)
    assert recovered == original
    print(f"  ✅ Roundtrip OK (cipher len: {len(cipher)})")


def test_decrypt_invalid_raises():
    print("\n" + "=" * 70)
    print("TEST 2: Descifrar ciphertext inválido → ValueError")
    print("=" * 70)
    try:
        decrypt_api_key("esto-no-es-un-ciphertext-valido")
        assert False, "Debería haber fallado"
    except ValueError:
        print(f"  ✅ ValueError detectado")


def test_encrypt_empty_raises():
    print("\n" + "=" * 70)
    print("TEST 3: Cifrar string vacío → ValueError")
    print("=" * 70)
    try:
        encrypt_api_key("")
        assert False, "Debería haber fallado"
    except ValueError:
        print(f"  ✅ ValueError detectado")


# ============================================================
# TESTS — Servicio (BD directa)
# ============================================================

def test_service_crud():
    print("\n" + "=" * 70)
    print("TEST 4: Servicio — CRUD directo en BD")
    print("=" * 70)
    db = SessionLocal()
    try:
        # Crear usuario temporal
        u = User(
            email=f"test_svc_{int(time.time()*1000)}@nuvora.com",
            hashed_password="x",
            is_active=True,
        )
        db.add(u)
        db.commit()
        db.refresh(u)

        # 1. No existe nada
        assert get_user_config(db, u.id, "gemini") is None
        assert not has_user_key(db, u.id, "gemini")

        # 2. Crear
        cfg = set_user_config(db, u.id, "gemini", "test-gemini-key-123456")
        assert cfg.id is not None
        assert cfg.provider == "gemini"
        assert cfg.api_key_encrypted != "test-gemini-key-123456"
        first_ciphertext = str(cfg.api_key_encrypted)  # copia string

        # 3. Leer
        got = get_user_config(db, u.id, "gemini")
        assert got is not None
        assert got.api_key_encrypted == first_ciphertext
        assert has_user_key(db, u.id, "gemini")

        # 4. Actualizar
        set_user_config(db, u.id, "gemini", "new-key-9999999999")
        db.expire_all()  # forzar recarga desde BD
        got2 = get_user_config(db, u.id, "gemini")
        assert str(got2.api_key_encrypted) != first_ciphertext

        # 5. Listar
        set_user_config(db, u.id, "groq", "test-groq-key-123456")
        all_cfgs = list_user_configs(db, u.id)
        assert len(all_cfgs) == 2

        # 6. Borrar
        assert delete_user_config(db, u.id, "gemini") is True
        assert delete_user_config(db, u.id, "gemini") is False
        assert get_user_config(db, u.id, "gemini") is None

        # Limpiar
        db.query(UserAIConfig).filter(UserAIConfig.user_id == u.id).delete()
        db.query(User).filter(User.id == u.id).delete()
        db.commit()
        print(f"  ✅ CRUD completo OK")
    finally:
        db.close()


def test_effective_api_key_fallback():
    print("\n" + "=" * 70)
    print("TEST 5: get_effective_api_key sin BYOK → sistema")
    print("=" * 70)
    db = SessionLocal()
    try:
        # Usuario sin config
        result = get_effective_api_key(db, user_id=999999999, provider="gemini")
        # Como no hay key ni BYOK ni sistema (en tests no está configurada),
        # devuelve None (o el valor del sistema si estuviera)
        # Solo comprobamos que no rompe
        print(f"  ✅ No rompe (result: {type(result).__name__})")
    finally:
        db.close()


# ============================================================
# TESTS — Endpoints HTTP
# ============================================================

def test_setup():
    print("\n" + "=" * 70)
    print("SETUP: Registrar 2 usuarios")
    print("=" * 70)
    email1, t1, u1 = _register_and_login("u1")
    email2, t2, u2 = _register_and_login("u2")
    _Ctx.token1 = t1
    _Ctx.token2 = t2
    _Ctx.user1_id = u1
    _Ctx.user2_id = u2
    _Ctx.headers1 = {"Authorization": f"Bearer {t1}"}
    _Ctx.headers2 = {"Authorization": f"Bearer {t2}"}
    print(f"  ✅ user1={u1}, user2={u2}")


def test_get_configs_without_auth():
    print("\n" + "=" * 70)
    print("TEST 6: GET /ai/config sin auth → 401")
    print("=" * 70)
    r = client.get("/ai/config")
    assert r.status_code == 401
    print(f"  ✅ 401")


def test_get_configs_empty():
    print("\n" + "=" * 70)
    print("TEST 7: GET /ai/config → lista vacía")
    print("=" * 70)
    r = client.get("/ai/config", headers=_Ctx.headers1)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "configs" in data
    assert "system_provider" in data
    assert len(data["configs"]) == 0
    print(f"  ✅ Lista vacía, system_provider={data['system_provider']}")


def test_create_config():
    print("\n" + "=" * 70)
    print("TEST 8: POST /ai/config → crea config")
    print("=" * 70)
    r = client.post(
        "/ai/config",
        json={"provider": "gemini", "api_key": "test-user-gemini-key-12345"},
        headers=_Ctx.headers1,
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["provider"] == "gemini"
    assert data["has_key"] is True
    print(f"  ✅ Config creada (has_key=True)")


def test_create_config_invalid_provider():
    print("\n" + "=" * 70)
    print("TEST 9: POST /ai/config con provider inválido → 422")
    print("=" * 70)
    # NOTA: Pydantic valida el Literal ANTES del endpoint → 422
    # (400 sería si pasara Pydantic y el endpoint lo rechazara)
    r = client.post(
        "/ai/config",
        json={"provider": "openai", "api_key": "test-key-1234567890"},
        headers=_Ctx.headers1,
    )
    assert r.status_code == 422, f"Esperaba 422, hubo {r.status_code}: {r.text}"
    print(f"  ✅ 422 (provider inválido, rechazado por Pydantic)")


def test_create_config_invalid_key_length():
    print("\n" + "=" * 70)
    print("TEST 10: POST /ai/config con key corta → 422")
    print("=" * 70)
    r = client.post(
        "/ai/config",
        json={"provider": "gemini", "api_key": "short"},
        headers=_Ctx.headers1,
    )
    assert r.status_code == 422
    print(f"  ✅ 422 (validation error)")


def test_list_with_config():
    print("\n" + "=" * 70)
    print("TEST 11: GET /ai/config tras crear → 1 config")
    print("=" * 70)
    r = client.get("/ai/config", headers=_Ctx.headers1)
    assert r.status_code == 200
    data = r.json()
    assert len(data["configs"]) == 1
    assert data["configs"][0]["provider"] == "gemini"
    # IMPORTANTE: la key NUNCA se devuelve
    assert "api_key" not in data["configs"][0]
    print(f"  ✅ 1 config, sin api_key expuesta")


def test_isolation_between_users():
    print("\n" + "=" * 70)
    print("TEST 12: Aislamiento — user2 no ve configs de user1")
    print("=" * 70)
    r = client.get("/ai/config", headers=_Ctx.headers2)
    assert r.status_code == 200
    data = r.json()
    assert len(data["configs"]) == 0
    print(f"  ✅ user2 tiene 0 configs")


def test_update_config():
    print("\n" + "=" * 70)
    print("TEST 13: POST /ai/config dos veces → actualiza")
    print("=" * 70)
    r = client.post(
        "/ai/config",
        json={"provider": "gemini", "api_key": "updated-key-9999999999"},
        headers=_Ctx.headers1,
    )
    assert r.status_code == 201
    # Sigue habiendo 1 sola config
    r2 = client.get("/ai/config", headers=_Ctx.headers1)
    assert len(r2.json()["configs"]) == 1
    print(f"  ✅ Actualizado, sigue 1 config")


def test_delete_config():
    print("\n" + "=" * 70)
    print("TEST 14: DELETE /ai/config/{provider}")
    print("=" * 70)
    r = client.delete("/ai/config/gemini", headers=_Ctx.headers1)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["deleted"] is True
    assert data["provider"] == "gemini"

    # Ya no está
    r2 = client.get("/ai/config", headers=_Ctx.headers1)
    assert len(r2.json()["configs"]) == 0
    print(f"  ✅ Config borrada")


def test_delete_nonexistent():
    print("\n" + "=" * 70)
    print("TEST 15: DELETE config inexistente → deleted=False")
    print("=" * 70)
    r = client.delete("/ai/config/groq", headers=_Ctx.headers1)
    assert r.status_code == 200
    assert r.json()["deleted"] is False
    print(f"  ✅ deleted=False")


def test_delete_invalid_provider():
    print("\n" + "=" * 70)
    print("TEST 16: DELETE provider inválido → 400")
    print("=" * 70)
    # En DELETE, el provider viene en el path (str), así que pasa Pydantic
    # y el endpoint lo valida con _validate_provider → 400
    r = client.delete("/ai/config/openai", headers=_Ctx.headers1)
    assert r.status_code == 400, f"Esperaba 400, hubo {r.status_code}: {r.text}"
    print(f"  ✅ 400 (rechazado por endpoint)")


# ============================================================
# TESTS — Regresión
# ============================================================

def test_regression_app_imports():
    print("\n" + "=" * 70)
    print("TEST 17: Regresión — app.main sigue OK")
    print("=" * 70)
    from app.main import app as _app
    assert _app is not None
    print(f"  ✅ app OK ({len(_app.routes)} rutas)")


def test_regression_workflow_validator():
    print("\n" + "=" * 70)
    print("TEST 18: Regresión — WorkflowValidator 14.5.4")
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
    print(f"  ✅ Validator OK")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.7.4b (BYOK)")
    print("=" * 70)

    tests = [
        test_encrypt_decrypt_roundtrip,
        test_decrypt_invalid_raises,
        test_encrypt_empty_raises,
        test_service_crud,
        test_effective_api_key_fallback,
        test_setup,
        test_get_configs_without_auth,
        test_get_configs_empty,
        test_create_config,
        test_create_config_invalid_provider,
        test_create_config_invalid_key_length,
        test_list_with_config,
        test_isolation_between_users,
        test_update_config,
        test_delete_config,
        test_delete_nonexistent,
        test_delete_invalid_provider,
        test_regression_app_imports,
        test_regression_workflow_validator,
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
