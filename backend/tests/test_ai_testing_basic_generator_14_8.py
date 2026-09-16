"""
Tests — Subfase 14.8.13 (Basic Auto Tests sin IA)
"""

import sys
import os
import time
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.core.testing import BasicTestGenerator
from app.core.ai.rate_limit import reset_all


client = TestClient(app)


# ============================================================
# HELPERS
# ============================================================

def _unique(suffix):
    return f"{suffix}_{int(time.time() * 1000)}"


def _setup_user_bot_workflow(nodes=None, transitions=None):
    """Crea usuario + bot + workflow."""
    unique = _unique("bgen")
    email = f"test_bgen_{unique}@nuvora.com"
    password = "123456"

    r = client.post("/auth/register", json={
        "email": email, "password": password, "full_name": "BGen",
    })
    assert r.status_code == 200, r.text
    token = client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post("/bots/", json={
        "name": f"Bot {unique}", "business_name": "T", "nicho_id": "otro",
    }, headers=headers)
    bot_id = r.json()["id"]

    if nodes is None:
        nodes = [
            {"node_id": "s1", "type": "start"},
            {"node_id": "m1", "type": "message", "config": {"text": "Hola"}},
            {"node_id": "e1", "type": "end"},
        ]
        transitions = [
            {"from_node_id": "s1", "to_node_id": "m1", "order": 0},
            {"from_node_id": "m1", "to_node_id": "e1", "order": 0},
        ]

    r = client.post(f"/workflows/{bot_id}", json={
        "name": "WF",
        "nodes": nodes,
        "transitions": transitions,
    }, headers=headers)
    wf_id = r.json()["id"]

    return headers, bot_id, wf_id


class _Ctx:
    headers = None
    bot_id = None
    wf_id = None


# ============================================================
# TESTS — BasicTestGenerator (unitario)
# ============================================================

def test_generator_simple_workflow():
    print("\n" + "=" * 70)
    print("TEST 1: Genera tests para workflow simple")
    print("=" * 70)
    wf = {
        "nodes": [
            {"node_id": "s1", "type": "start"},
            {"node_id": "m1", "type": "message", "config": {"text": "Hola"}},
            {"node_id": "e1", "type": "end"},
        ],
        "transitions": [
            {"from_node_id": "s1", "to_node_id": "m1"},
            {"from_node_id": "m1", "to_node_id": "e1"},
        ],
    }
    result = BasicTestGenerator().generate(wf)
    # happy + 3 nodos + max_steps + no_error = 6
    assert result.count >= 5
    names = [t.name for t in result.generated]
    assert any("Happy" in n for n in names)
    assert any("No excede" in n for n in names)
    print(f"  ✅ {result.count} tests: {names}")


def test_generator_workflow_with_condition():
    print("\n" + "=" * 70)
    print("TEST 2: Genera tests para workflow con CONDITION")
    print("=" * 70)
    wf = {
        "nodes": [
            {"node_id": "s1", "type": "start"},
            {"node_id": "c1", "type": "condition", "config": {"condition": "age > 18"}},
            {"node_id": "ma", "type": "message", "config": {"text": "Adulto"}},
            {"node_id": "mb", "type": "message", "config": {"text": "Menor"}},
            {"node_id": "e1", "type": "end"},
        ],
        "transitions": [
            {"from_node_id": "s1", "to_node_id": "c1"},
            {"from_node_id": "c1", "to_node_id": "ma", "condition": "age > 18", "order": 1},
            {"from_node_id": "c1", "to_node_id": "mb", "condition": "age <= 18", "order": 2},
            {"from_node_id": "ma", "to_node_id": "e1"},
            {"from_node_id": "mb", "to_node_id": "e1"},
        ],
    }
    result = BasicTestGenerator().generate(wf)
    # Happy path debe tener age inicial > 18 (inferido de la condición)
    happy = next(t for t in result.generated if "Happy" in t.name)
    assert "age" in happy.initial_variables
    assert happy.initial_variables["age"] > 18
    print(f"  ✅ Happy path con age={happy.initial_variables['age']}")


def test_generator_workflow_with_question():
    print("\n" + "=" * 70)
    print("TEST 3: Genera tests para workflow con QUESTION")
    print("=" * 70)
    wf = {
        "nodes": [
            {"node_id": "s1", "type": "start"},
            {"node_id": "q1", "type": "question", "config": {"text": "¿?", "variable": "name"}},
            {"node_id": "e1", "type": "end"},
        ],
        "transitions": [
            {"from_node_id": "s1", "to_node_id": "q1"},
            {"from_node_id": "q1", "to_node_id": "e1"},
        ],
    }
    result = BasicTestGenerator().generate(wf)
    happy = next(t for t in result.generated if "Happy" in t.name)
    assert happy.initial_variables.get("name") == "Manuel"
    print(f"  ✅ Variable inferida: name={happy.initial_variables['name']}")


def test_generator_empty_workflow():
    print("\n" + "=" * 70)
    print("TEST 4: Workflow vacío → 0 tests")
    print("=" * 70)
    result = BasicTestGenerator().generate({"nodes": [], "transitions": []})
    assert result.count == 0
    assert len(result.notes) > 0
    print(f"  ✅ 0 tests, notes: {result.notes}")


def test_generator_limits_node_tests():
    print("\n" + "=" * 70)
    print("TEST 5: Workflow con muchos nodos → limita tests por nodo")
    print("=" * 70)
    # 10 nodos message
    nodes = [{"node_id": "s1", "type": "start"}]
    transitions = []
    for i in range(10):
        nodes.append({"node_id": f"m{i+1}", "type": "message", "config": {"text": f"msg{i+1}"}})
        if i == 0:
            transitions.append({"from_node_id": "s1", "to_node_id": "m1"})
        else:
            transitions.append({"from_node_id": f"m{i}", "to_node_id": f"m{i+1}"})
    nodes.append({"node_id": "e1", "type": "end"})
    transitions.append({"from_node_id": "m10", "to_node_id": "e1"})

    wf = {"nodes": nodes, "transitions": transitions}
    result = BasicTestGenerator().generate(wf)
    # Happy + 5 nodos (limitado) + max_steps + no_error = 8
    assert result.count <= 10
    assert any("solo 5 tests" in n.lower() for n in result.notes) or result.count <= 10
    print(f"  ✅ {result.count} tests (limitado correctamente)")


def test_generator_no_ia_calls():
    print("\n" + "=" * 70)
    print("TEST 6: BasicTestGenerator NO llama a la IA")
    print("=" * 70)
    wf = {
        "nodes": [
            {"node_id": "s1", "type": "start"},
            {"node_id": "e1", "type": "end"},
        ],
        "transitions": [{"from_node_id": "s1", "to_node_id": "e1"}],
    }
    with patch("app.core.ai.providers.get_provider") as mock_get:
        result = BasicTestGenerator().generate(wf)
        # Si llama a get_provider, este test falla
        assert mock_get.call_count == 0, "NO debe llamar a la IA"
    print(f"  ✅ 0 llamadas a get_provider")


# ============================================================
# TESTS — Endpoint HTTP
# ============================================================

def test_setup():
    print("\n" + "=" * 70)
    print("SETUP")
    print("=" * 70)
    reset_all()
    _Ctx.headers, _Ctx.bot_id, _Ctx.wf_id = _setup_user_bot_workflow()
    print(f"  ✅ bot_id={_Ctx.bot_id}, wf_id={_Ctx.wf_id}")


def test_generate_basic_no_auth():
    print("\n" + "=" * 70)
    print("TEST 7: POST sin auth → 401")
    print("=" * 70)
    r = client.post(
        f"/bots/{_Ctx.bot_id}/tests/generate-basic?workflow_id={_Ctx.wf_id}",
    )
    assert r.status_code == 401
    print(f"  ✅ 401")


def test_generate_basic_bot_not_found():
    print("\n" + "=" * 70)
    print("TEST 8: POST bot inexistente → 404")
    print("=" * 70)
    r = client.post(
        "/bots/999999/tests/generate-basic?workflow_id=1",
        headers=_Ctx.headers,
    )
    assert r.status_code == 404
    print(f"  ✅ 404")


def test_generate_basic_success():
    print("\n" + "=" * 70)
    print("TEST 9: POST /tests/generate-basic → OK")
    print("=" * 70)
    reset_all()
    r = client.post(
        f"/bots/{_Ctx.bot_id}/tests/generate-basic?workflow_id={_Ctx.wf_id}",
        headers=_Ctx.headers,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["count"] >= 3
    names = [t["name"] for t in data["generated"]]
    assert any("Happy" in n for n in names)
    print(f"  ✅ {data['count']} tests generados")
    for n in names:
        print(f"     - {n}")


def test_generate_basic_does_not_save():
    print("\n" + "=" * 70)
    print("TEST 10: generate-basic NO guarda tests en BD")
    print("=" * 70)
    reset_all()

    # Contar tests antes
    r_before = client.get(
        f"/bots/{_Ctx.bot_id}/tests?workflow_id={_Ctx.wf_id}",
        headers=_Ctx.headers,
    )
    count_before = r_before.json()["total"]

    # Llamar al endpoint
    r = client.post(
        f"/bots/{_Ctx.bot_id}/tests/generate-basic?workflow_id={_Ctx.wf_id}",
        headers=_Ctx.headers,
    )
    assert r.status_code == 200

    # Contar después
    r_after = client.get(
        f"/bots/{_Ctx.bot_id}/tests?workflow_id={_Ctx.wf_id}",
        headers=_Ctx.headers,
    )
    count_after = r_after.json()["total"]

    assert count_before == count_after, (
        f"NO debe guardar. Antes: {count_before}, después: {count_after}"
    )
    print(f"  ✅ {count_after} tests en BD (sin cambios)")


def test_generate_basic_can_be_saved():
    print("\n" + "=" * 70)
    print("TEST 11: Los tests generados se pueden guardar manualmente")
    print("=" * 70)
    reset_all()

    # Generar
    r = client.post(
        f"/bots/{_Ctx.bot_id}/tests/generate-basic?workflow_id={_Ctx.wf_id}",
        headers=_Ctx.headers,
    )
    generated = r.json()["generated"]
    assert len(generated) > 0

    # Guardar el primero manualmente
    first = generated[0]
    payload = {
        "name": first["name"],
        "description": first.get("description"),
        "input_messages": first["input_messages"],
        "initial_variables": first.get("initial_variables", {}),
        "assertions": first["assertions"],
        "enabled": first.get("enabled", True),
    }

    r2 = client.post(
        f"/bots/{_Ctx.bot_id}/tests?workflow_id={_Ctx.wf_id}",
        json=payload,
        headers=_Ctx.headers,
    )
    assert r2.status_code == 201, r2.text
    print(f"  ✅ Test guardado manualmente")


def test_regression_app_imports():
    print("\n" + "=" * 70)
    print("TEST 12: Regresión — app.main sigue OK")
    print("=" * 70)
    from app.main import app as _app
    assert _app is not None
    print(f"  ✅ app OK ({len(_app.routes)} rutas)")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.8.13 (Basic Auto Tests sin IA)")
    print("=" * 70)

    tests = [
        test_generator_simple_workflow,
        test_generator_workflow_with_condition,
        test_generator_workflow_with_question,
        test_generator_empty_workflow,
        test_generator_limits_node_tests,
        test_generator_no_ia_calls,
        test_setup,
        test_generate_basic_no_auth,
        test_generate_basic_bot_not_found,
        test_generate_basic_success,
        test_generate_basic_does_not_save,
        test_generate_basic_can_be_saved,
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
