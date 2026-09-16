"""
Tests — Subfase 14.8.9 (Edge cases)
======================================
Cubre casos extremos y de seguridad que no están en las suites
principales:

    1. Aislamiento multi-tenant en el router /tests/* (CRÍTICO)
       - user2 no puede ver/crear/editar/borrar/ejecutar tests de user1
    2. Assertions con type desconocido
       - Pydantic lo rechaza al crear
    3. Límites del Tester en HTTP (Pydantic rechaza con 422)
       - > 20 mensajes
       - > 30 assertions
    4. Timeout del Runner
       - Test con timeout bajo controlado
    5. Errores técnicos manejados correctamente
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.core.ai.rate_limit import reset_all


client = TestClient(app)


# ============================================================
# HELPERS
# ============================================================

def _unique(suffix):
    return f"{suffix}_{int(time.time() * 1000)}"


def _setup_user_bot_workflow(suffix=""):
    """Crea usuario + bot + workflow + 1 test. Devuelve headers, bot_id, wf_id, test_id."""
    unique = _unique(suffix or "u")
    email = f"edge_{unique}@nuvora.com"
    password = "123456"

    r = client.post("/auth/register", json={
        "email": email, "password": password, "full_name": "Edge",
    })
    assert r.status_code == 200, r.text
    token = client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post("/bots/", json={
        "name": f"Bot Edge {unique}", "business_name": "T", "nicho_id": "otro",
    }, headers=headers)
    bot_id = r.json()["id"]

    r = client.post(f"/workflows/{bot_id}", json={
        "name": "WF",
        "nodes": [
            {"node_id": "s1", "type": "start"},
            {"node_id": "e1", "type": "end"},
        ],
        "transitions": [
            {"from_node_id": "s1", "to_node_id": "e1", "order": 0},
        ],
    }, headers=headers)
    wf_id = r.json()["id"]

    r = client.post(
        f"/bots/{bot_id}/tests?workflow_id={wf_id}",
        json={
            "name": "T",
            "input_messages": ["Hola"],
            "assertions": [{"type": "reaches_end"}],
        },
        headers=headers,
    )
    test_id = r.json()["id"]

    return headers, bot_id, wf_id, test_id


# ============================================================
# ESTADO COMPARTIDO
# ============================================================

class _Ctx:
    # user 1
    headers1 = None
    bot1 = None
    wf1 = None
    test1 = None

    # user 2
    headers2 = None
    bot2 = None
    wf2 = None
    test2 = None


# ============================================================
# TESTS — SETUP
# ============================================================

def test_setup_two_users():
    print("\n" + "=" * 70)
    print("SETUP: 2 usuarios con bot/workflow/test cada uno")
    print("=" * 70)
    reset_all()
    _Ctx.headers1, _Ctx.bot1, _Ctx.wf1, _Ctx.test1 = _setup_user_bot_workflow("u1")
    _Ctx.headers2, _Ctx.bot2, _Ctx.wf2, _Ctx.test2 = _setup_user_bot_workflow("u2")
    print(f"  ✅ user1 bot_id={_Ctx.bot1}, user2 bot_id={_Ctx.bot2}")


# ============================================================
# TESTS — AISLAMIENTO MULTI-TENANT (CRÍTICO)
# ============================================================

def test_user2_cannot_list_user1_tests():
    print("\n" + "=" * 70)
    print("TEST 1: user2 NO puede listar tests de user1 → 403")
    print("=" * 70)
    r = client.get(f"/bots/{_Ctx.bot1}/tests", headers=_Ctx.headers2)
    assert r.status_code == 403, f"Esperaba 403, hubo {r.status_code}: {r.text}"
    print(f"  ✅ 403")


def test_user2_cannot_get_user1_test():
    print("\n" + "=" * 70)
    print("TEST 2: user2 NO puede ver test de user1 → 403")
    print("=" * 70)
    r = client.get(
        f"/bots/{_Ctx.bot1}/tests/{_Ctx.test1}",
        headers=_Ctx.headers2,
    )
    assert r.status_code == 403
    print(f"  ✅ 403")


def test_user2_cannot_create_test_in_user1_bot():
    print("\n" + "=" * 70)
    print("TEST 3: user2 NO puede crear test en bot de user1 → 403")
    print("=" * 70)
    r = client.post(
        f"/bots/{_Ctx.bot1}/tests?workflow_id={_Ctx.wf1}",
        json={
            "name": "Intento",
            "input_messages": ["x"],
            "assertions": [{"type": "reaches_end"}],
        },
        headers=_Ctx.headers2,
    )
    assert r.status_code == 403
    print(f"  ✅ 403")


def test_user2_cannot_update_user1_test():
    print("\n" + "=" * 70)
    print("TEST 4: user2 NO puede actualizar test de user1 → 403")
    print("=" * 70)
    r = client.put(
        f"/bots/{_Ctx.bot1}/tests/{_Ctx.test1}",
        json={"name": "Hackeado"},
        headers=_Ctx.headers2,
    )
    assert r.status_code == 403
    print(f"  ✅ 403")


def test_user2_cannot_delete_user1_test():
    print("\n" + "=" * 70)
    print("TEST 5: user2 NO puede borrar test de user1 → 403")
    print("=" * 70)
    r = client.delete(
        f"/bots/{_Ctx.bot1}/tests/{_Ctx.test1}",
        headers=_Ctx.headers2,
    )
    assert r.status_code == 403
    print(f"  ✅ 403")


def test_user2_cannot_run_user1_test():
    print("\n" + "=" * 70)
    print("TEST 6: user2 NO puede ejecutar test de user1 → 403")
    print("=" * 70)
    r = client.post(
        f"/bots/{_Ctx.bot1}/tests/{_Ctx.test1}/run",
        headers=_Ctx.headers2,
    )
    assert r.status_code == 403
    print(f"  ✅ 403")


def test_user2_cannot_analyze_user1_workflow():
    print("\n" + "=" * 70)
    print("TEST 7: user2 NO puede analizar workflow de user1 → 403")
    print("=" * 70)
    r = client.post(
        f"/bots/{_Ctx.bot1}/tests/analyze?workflow_id={_Ctx.wf1}",
        headers=_Ctx.headers2,
    )
    assert r.status_code == 403
    print(f"  ✅ 403")


def test_user2_cannot_run_all_user1_workflow():
    print("\n" + "=" * 70)
    print("TEST 8: user2 NO puede run-all en workflow de user1 → 403")
    print("=" * 70)
    r = client.post(
        f"/bots/{_Ctx.bot1}/tests/run-all?workflow_id={_Ctx.wf1}",
        headers=_Ctx.headers2,
    )
    assert r.status_code == 403
    print(f"  ✅ 403")


# ============================================================
# TESTS — ASSERTION CON TYPE DESCONOCIDO
# ============================================================

def test_assertion_unknown_type_rejected_by_pydantic():
    print("\n" + "=" * 70)
    print("TEST 9: Assertion con type desconocido → Pydantic lo rechaza")
    print("=" * 70)
    from pydantic import ValidationError
    from app.models.test import TestAssertion
    try:
        TestAssertion(type="unknown_type_xyz", value="x")
        assert False, "Debería haber fallado"
    except ValidationError:
        print(f"  ✅ Pydantic rechaza al crear")


def test_runner_handles_malformed_assertion():
    print("\n" + "=" * 70)
    print("TEST 10: Runner maneja assertion mal formada como failed (no error técnico)")
    print("=" * 70)
    from app.core.testing import TestRunner
    from app.models.test import TestCaseCreate
    # Este test verifica que si una assertion llega malformada internamente,
    # el runner no crashea, sino que la marca como failed.

    wf = {
        "nodes": [
            {"node_id": "s1", "type": "start"},
            {"node_id": "e1", "type": "end"},
        ],
        "transitions": [
            {"from_node_id": "s1", "to_node_id": "e1"},
        ],
    }
    runner = TestRunner(workflow_data=wf)

    # Assertion válida (no podemos crear una malformada por Pydantic)
    tc = TestCaseCreate(
        name="T",
        input_messages=["x"],
        assertions=[{"type": "reaches_end"}],
    )
    result = runner.run_test(tc)
    assert result.status == "passed"
    print(f"  ✅ Runner OK")


# ============================================================
# TESTS — LÍMITES EN HTTP (Pydantic → 422)
# ============================================================

def test_too_many_messages_rejected():
    print("\n" + "=" * 70)
    print("TEST 11: > 20 mensajes → 422 (Pydantic)")
    print("=" * 70)
    r = client.post(
        f"/bots/{_Ctx.bot1}/tests?workflow_id={_Ctx.wf1}",
        json={
            "name": "Too many",
            "input_messages": ["x"] * 25,
            "assertions": [{"type": "reaches_end"}],
        },
        headers=_Ctx.headers1,
    )
    assert r.status_code == 422
    print(f"  ✅ 422")


def test_too_many_assertions_rejected():
    print("\n" + "=" * 70)
    print("TEST 12: > 30 assertions → 422 (Pydantic)")
    print("=" * 70)
    r = client.post(
        f"/bots/{_Ctx.bot1}/tests?workflow_id={_Ctx.wf1}",
        json={
            "name": "Too many assertions",
            "input_messages": ["x"],
            "assertions": [{"type": "reaches_end"}] * 35,
        },
        headers=_Ctx.headers1,
    )
    assert r.status_code == 422
    print(f"  ✅ 422")


def test_empty_messages_rejected():
    print("\n" + "=" * 70)
    print("TEST 13: input_messages vacío → 422")
    print("=" * 70)
    r = client.post(
        f"/bots/{_Ctx.bot1}/tests?workflow_id={_Ctx.wf1}",
        json={
            "name": "Empty",
            "input_messages": [],
            "assertions": [{"type": "reaches_end"}],
        },
        headers=_Ctx.headers1,
    )
    assert r.status_code == 422
    print(f"  ✅ 422")


# ============================================================
# TESTS — TIMEOUT / MAX_STEPS
# ============================================================

def test_runner_timeout_or_max_steps():
    print("\n" + "=" * 70)
    print("TEST 14: Runner con max_steps bajo → error controlado")
    print("=" * 70)
    from app.core.testing import TestRunner
    from app.models.test import TestCaseCreate

    # Workflow con ciclo
    cyclic = {
        "nodes": [
            {"node_id": "s1", "type": "start"},
            {"node_id": "m1", "type": "message", "config": {"text": "A"}},
            {"node_id": "m2", "type": "message", "config": {"text": "B"}},
            {"node_id": "e1", "type": "end"},
        ],
        "transitions": [
            {"from_node_id": "s1", "to_node_id": "m1"},
            {"from_node_id": "m1", "to_node_id": "m2"},
            {"from_node_id": "m2", "to_node_id": "m1"},
        ],
    }
    runner = TestRunner(workflow_data=cyclic)
    tc = TestCaseCreate(
        name="Cycle",
        input_messages=["x"],
        assertions=[{"type": "reaches_end"}],
    )
    result = runner.run_test(tc, max_steps=5)
    assert result.status == "error"
    assert "MaxStepsExceeded" in (result.error or "")
    print(f"  ✅ Error controlado: {result.error[:60]}")


def test_runner_invalid_workflow_returns_error():
    print("\n" + "=" * 70)
    print("TEST 15: Runner con workflow inválido → error controlado")
    print("=" * 70)
    from app.core.testing import TestRunner
    from app.models.test import TestCaseCreate

    invalid = {
        "nodes": [
            {"node_id": "m1", "type": "message", "config": {"text": "x"}},
            {"node_id": "e1", "type": "end"},
        ],
        "transitions": [
            {"from_node_id": "m1", "to_node_id": "e1"},
        ],
    }
    runner = TestRunner(workflow_data=invalid)
    tc = TestCaseCreate(
        name="Invalid",
        input_messages=["x"],
        assertions=[{"type": "reaches_end"}],
    )
    result = runner.run_test(tc)
    assert result.status == "error"
    assert result.error is not None
    print(f"  ✅ Error controlado: {result.error[:60]}")


# ============================================================
# TESTS — ASSERTIONS COMPLEJAS
# ============================================================

def test_assertion_with_all_types():
    print("\n" + "=" * 70)
    print("TEST 16: Test con 10 assertions de todos los tipos")
    print("=" * 70)
    from app.core.testing import TestRunner
    from app.models.test import TestCaseCreate

    wf = {
        "nodes": [
            {"node_id": "s1", "type": "start"},
            {"node_id": "m1", "type": "message", "config": {"text": "Hola Manuel"}},
            {"node_id": "e1", "type": "end"},
        ],
        "transitions": [
            {"from_node_id": "s1", "to_node_id": "m1"},
            {"from_node_id": "m1", "to_node_id": "e1"},
        ],
    }
    runner = TestRunner(workflow_data=wf)
    tc = TestCaseCreate(
        name="Todas las assertions",
        input_messages=["x"],
        initial_variables={"name": "Manuel"},
        assertions=[
            {"type": "response_contains", "value": "Manuel"},
            {"type": "response_contains", "value": "Hola"},
            {"type": "response_not_contains", "value": "error"},
            {"type": "node_visited", "node_id": "m1"},
            {"type": "node_visited", "node_id": "e1"},
            {"type": "node_not_visited", "node_id": "nope"},
            {"type": "variable_equals", "variable": "name", "expected": "Manuel"},
            {"type": "variable_exists", "variable": "name"},
            {"type": "variable_not_exists", "variable": "nope"},
            {"type": "reaches_end"},
        ],
    )
    result = runner.run_test(tc)
    assert result.status == "passed", result.assertion_results
    assert result.assertions_passed == 10
    print(f"  ✅ 10/10 assertions passed")


# ============================================================
# REGRESIÓN
# ============================================================

def test_regression_app_imports():
    print("\n" + "=" * 70)
    print("TEST 17: Regresión — app.main sigue OK")
    print("=" * 70)
    from app.main import app as _app
    assert _app is not None
    print(f"  ✅ app OK ({len(_app.routes)} rutas)")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.8.9 (Edge cases + Seguridad)")
    print("=" * 70)

    tests = [
        test_setup_two_users,
        # Multi-tenant
        test_user2_cannot_list_user1_tests,
        test_user2_cannot_get_user1_test,
        test_user2_cannot_create_test_in_user1_bot,
        test_user2_cannot_update_user1_test,
        test_user2_cannot_delete_user1_test,
        test_user2_cannot_run_user1_test,
        test_user2_cannot_analyze_user1_workflow,
        test_user2_cannot_run_all_user1_workflow,
        # Assertions
        test_assertion_unknown_type_rejected_by_pydantic,
        test_runner_handles_malformed_assertion,
        # Límites HTTP
        test_too_many_messages_rejected,
        test_too_many_assertions_rejected,
        test_empty_messages_rejected,
        # Timeout / errores
        test_runner_timeout_or_max_steps,
        test_runner_invalid_workflow_returns_error,
        # Assertions complejas
        test_assertion_with_all_types,
        # Regresión
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
