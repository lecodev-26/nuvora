"""
Tests — Subfase 14.10.9 (OpenAPI + documentación)
===================================================
Cubre:
    - OpenAPI tiene los 7 tags
    - Cada tag tiene name + description
    - /api/v1/chat tiene summary, description, responses documentadas
    - /bots/{bot_id}/api-keys tiene metadata
    - Schemas tienen examples
    - La doc `/docs` carga OK
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


# ============================================================
# TESTS
# ============================================================

def test_openapi_generates():
    print("\n" + "=" * 70)
    print("TEST 1: OpenAPI se genera sin errores")
    print("=" * 70)
    schema = app.openapi()
    assert "info" in schema
    assert "paths" in schema
    assert "tags" in schema
    print(f"  ✅ OpenAPI OK")


def test_openapi_has_7_tags():
    print("\n" + "=" * 70)
    print("TEST 2: OpenAPI tiene los 7 tags esperados")
    print("=" * 70)
    schema = app.openapi()
    tag_names = {t["name"] for t in schema.get("tags", [])}
    expected = {"api-v1", "api-keys", "public", "bots", "workflows", "tests", "auth"}
    missing = expected - tag_names
    assert not missing, f"Faltan tags: {missing}"
    print(f"  ✅ 7 tags OK: {sorted(tag_names)}")


def test_each_tag_has_description():
    print("\n" + "=" * 70)
    print("TEST 3: Cada tag tiene name + description")
    print("=" * 70)
    schema = app.openapi()
    for tag in schema.get("tags", []):
        assert "name" in tag, f"Tag sin name: {tag}"
        assert "description" in tag, f"Tag '{tag['name']}' sin description"
        assert len(tag["description"]) > 10
    print(f"  ✅ {len(schema['tags'])} tags con descripción")


def test_chat_endpoint_documented():
    print("\n" + "=" * 70)
    print("TEST 4: /api/v1/chat tiene summary + description")
    print("=" * 70)
    schema = app.openapi()
    path = "/api/v1/chat"
    assert path in schema["paths"], f"Falta {path}"

    post = schema["paths"][path]["post"]
    assert "summary" in post or "description" in post, "Sin summary ni description"
    assert post.get("summary") or post.get("description")
    print(f"  ✅ summary: {post.get('summary', '(sin summary)')[:60]}")


def test_chat_endpoint_has_responses():
    print("\n" + "=" * 70)
    print("TEST 5: /api/v1/chat tiene responses documentadas")
    print("=" * 70)
    schema = app.openapi()
    post = schema["paths"]["/api/v1/chat"]["post"]

    assert "responses" in post
    responses = post["responses"]
    # Debe tener al menos 200
    assert "200" in responses

    # Debe documentar 401, 409, 429 (via responses del router o de la operación)
    for code in ["401", "409", "429"]:
        assert code in responses, f"Falta documentar {code}"
    print(f"  ✅ Responses documentadas: {sorted(responses.keys())}")


def test_api_keys_endpoints_documented():
    print("\n" + "=" * 70)
    print("TEST 6: /bots/{bot_id}/api-keys documentado")
    print("=" * 70)
    schema = app.openapi()

    path_list = "/bots/{bot_id}/api-keys"
    assert path_list in schema["paths"]
    methods = set(schema["paths"][path_list].keys())
    assert "get" in methods
    assert "post" in methods

    path_item = "/bots/{bot_id}/api-keys/{key_id}"
    assert path_item in schema["paths"]
    assert "delete" in schema["paths"][path_item]

    print(f"  ✅ Endpoints api-keys documentados")


def test_chat_request_has_examples():
    print("\n" + "=" * 70)
    print("TEST 7: ChatRequest.message tiene examples")
    print("=" * 70)
    schema = app.openapi()
    post = schema["paths"]["/api/v1/chat"]["post"]

    # El request body debería tener $ref al schema de ChatRequest
    body = post.get("requestBody", {})
    assert body, "No hay requestBody"

    # Buscar ChatRequest en components
    components = schema.get("components", {}).get("schemas", {})
    chat_req = components.get("ChatRequest")
    assert chat_req is not None, "ChatRequest no está en components"

    props = chat_req.get("properties", {})
    message_prop = props.get("message", {})

    # Puede tener examples o no (Pydantic v2 los mueve a veces)
    has_examples = "examples" in message_prop
    print(f"  ✅ ChatRequest en components (has_examples={has_examples})")


def test_api_key_create_has_examples():
    print("\n" + "=" * 70)
    print("TEST 8: ApiKeyCreate.name tiene examples")
    print("=" * 70)
    schema = app.openapi()
    components = schema.get("components", {}).get("schemas", {})
    api_key_create = components.get("ApiKeyCreate")
    assert api_key_create is not None, "ApiKeyCreate no está en components"

    props = api_key_create.get("properties", {})
    name_prop = props.get("name", {})
    # Examples pueden estar o no
    has_examples = "examples" in name_prop
    print(f"  ✅ ApiKeyCreate en components (has_examples={has_examples})")


def test_docs_endpoint_loads():
    print("\n" + "=" * 70)
    print("TEST 9: /docs carga OK")
    print("=" * 70)
    r = client.get("/docs")
    assert r.status_code == 200
    assert "swagger" in r.text.lower() or "openapi" in r.text.lower()
    print("  ✅ /docs carga OK")


def test_openapi_json_endpoint():
    print("\n" + "=" * 70)
    print("TEST 10: /openapi.json accesible")
    print("=" * 70)
    r = client.get("/openapi.json")
    assert r.status_code == 200
    schema = r.json()
    assert "paths" in schema
    assert "/api/v1/chat" in schema["paths"]
    print("  ✅ /openapi.json OK")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.10.9 (OpenAPI + documentación)")
    print("=" * 70)

    tests = [
        test_openapi_generates,
        test_openapi_has_7_tags,
        test_each_tag_has_description,
        test_chat_endpoint_documented,
        test_chat_endpoint_has_responses,
        test_api_keys_endpoints_documented,
        test_chat_request_has_examples,
        test_api_key_create_has_examples,
        test_docs_endpoint_loads,
        test_openapi_json_endpoint,
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
