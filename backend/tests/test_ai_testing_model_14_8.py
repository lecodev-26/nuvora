"""
Tests — Subfase 14.8.6
Verifica el modelo WorkflowTest (tabla workflow_tests).
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from app.database.config import engine, SessionLocal
from app.models.db_models import (
    WorkflowTest, Workflow, Bot, User,
)


# ============================================================
# HELPERS
# ============================================================

def _create_test_entities(db):
    """Crea usuario + bot + workflow para tests."""
    unique = int(time.time() * 1000)
    u = User(
        email=f"test_wf_test_{unique}@nuvora.com",
        hashed_password="x",
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)

    b = Bot(
        user_id=u.id,
        name=f"Bot Test {unique}",
        description="Test",
        nicho_id="otro",
        owner_email=u.email,
        is_active=True,
        plan="free",
    )
    db.add(b)
    db.commit()
    db.refresh(b)

    wf = Workflow(
        bot_id=b.id,
        name=f"WF Test {unique}",
        status="draft",
        version=1,
        trigger="manual",
    )
    db.add(wf)
    db.commit()
    db.refresh(wf)

    return u, b, wf


def _cleanup(db, u, b, wf):
    """Limpia las entidades de prueba."""
    db.query(WorkflowTest).filter(WorkflowTest.workflow_id == wf.id).delete()
    db.query(Workflow).filter(Workflow.id == wf.id).delete()
    db.query(Bot).filter(Bot.id == b.id).delete()
    db.query(User).filter(User.id == u.id).delete()
    db.commit()


# ============================================================
# TESTS
# ============================================================

def test_table_exists():
    print("\n" + "=" * 70)
    print("TEST 1: Tabla workflow_tests existe")
    print("=" * 70)
    inspector = inspect(engine)
    assert "workflow_tests" in inspector.get_table_names()
    print(f"  ✅ Tabla existe")


def test_columns():
    print("\n" + "=" * 70)
    print("TEST 2: Columnas esperadas")
    print("=" * 70)
    inspector = inspect(engine)
    columns = {c["name"] for c in inspector.get_columns("workflow_tests")}
    expected = {
        "id", "workflow_id", "bot_id",
        "name", "description",
        "input_messages", "initial_vars", "assertions",
        "enabled", "created_at", "updated_at",
    }
    assert expected.issubset(columns), f"Faltan columnas: {expected - columns}"
    print(f"  ✅ {len(columns)} columnas OK")


def test_indexes():
    print("\n" + "=" * 70)
    print("TEST 3: Índices presentes")
    print("=" * 70)
    inspector = inspect(engine)
    indexes = inspector.get_indexes("workflow_tests")
    indexed_columns = {tuple(idx["column_names"]) for idx in indexes}
    # Al menos: workflow_id, bot_id, enabled
    has_workflow = any("workflow_id" in cols for cols in indexed_columns)
    has_bot = any("bot_id" in cols for cols in indexed_columns)
    has_enabled = any("enabled" in cols for cols in indexed_columns)
    assert has_workflow
    assert has_bot
    assert has_enabled
    print(f"  ✅ Índices OK ({len(indexes)} índices)")


def test_create_workflow_test():
    print("\n" + "=" * 70)
    print("TEST 4: Crear WorkflowTest")
    print("=" * 70)
    db = SessionLocal()
    try:
        u, b, wf = _create_test_entities(db)

        wt = WorkflowTest(
            workflow_id=wf.id,
            bot_id=b.id,
            name="Test 1",
            description="Test de reserva",
            input_messages=json.dumps(["Hola", "Quiero reservar"]),
            initial_vars=json.dumps({}),
            assertions=json.dumps([
                {"type": "response_contains", "value": "reserva"},
            ]),
            enabled=True,
        )
        db.add(wt)
        db.commit()
        db.refresh(wt)

        assert wt.id is not None
        assert wt.name == "Test 1"
        assert wt.enabled is True
        # Verificar JSON
        msgs = json.loads(wt.input_messages)
        assert len(msgs) == 2
        assertions = json.loads(wt.assertions)
        assert len(assertions) == 1
        print(f"  ✅ WorkflowTest id={wt.id} creado")

        _cleanup(db, u, b, wf)
    finally:
        db.close()


def test_cascade_delete_workflow():
    print("\n" + "=" * 70)
    print("TEST 5: CASCADE al borrar Workflow")
    print("=" * 70)
    db = SessionLocal()
    try:
        u, b, wf = _create_test_entities(db)

        wt = WorkflowTest(
            workflow_id=wf.id,
            bot_id=b.id,
            name="Test cascade",
            input_messages=json.dumps(["x"]),
            assertions=json.dumps([{"type": "reaches_end"}]),
        )
        db.add(wt)
        db.commit()
        wt_id = wt.id

        # Borrar workflow → CASCADE debe borrar el test
        db.query(Workflow).filter(Workflow.id == wf.id).delete()
        db.commit()

        gone = db.query(WorkflowTest).filter(WorkflowTest.id == wt_id).first()
        assert gone is None, "El test debería haberse borrado en CASCADE"
        print(f"  ✅ CASCADE OK")

        # Limpieza
        db.query(Bot).filter(Bot.id == b.id).delete()
        db.query(User).filter(User.id == u.id).delete()
        db.commit()
    finally:
        db.close()


def test_cascade_delete_bot():
    print("\n" + "=" * 70)
    print("TEST 6: CASCADE al borrar Bot")
    print("=" * 70)
    db = SessionLocal()
    try:
        u, b, wf = _create_test_entities(db)

        wt = WorkflowTest(
            workflow_id=wf.id,
            bot_id=b.id,
            name="Test cascade bot",
            input_messages=json.dumps(["x"]),
            assertions=json.dumps([{"type": "reaches_end"}]),
        )
        db.add(wt)
        db.commit()
        wt_id = wt.id

        # Borrar bot → CASCADE debe borrar workflow y test
        db.query(Bot).filter(Bot.id == b.id).delete()
        db.commit()

        gone = db.query(WorkflowTest).filter(WorkflowTest.id == wt_id).first()
        assert gone is None, "El test debería haberse borrado en CASCADE por bot"
        print(f"  ✅ CASCADE por bot OK")

        # Limpieza
        db.query(User).filter(User.id == u.id).delete()
        db.commit()
    finally:
        db.close()


def test_disabled_test():
    print("\n" + "=" * 70)
    print("TEST 7: Test con enabled=False")
    print("=" * 70)
    db = SessionLocal()
    try:
        u, b, wf = _create_test_entities(db)

        wt = WorkflowTest(
            workflow_id=wf.id,
            bot_id=b.id,
            name="Test disabled",
            input_messages=json.dumps(["x"]),
            assertions=json.dumps([{"type": "reaches_end"}]),
            enabled=False,
        )
        db.add(wt)
        db.commit()
        db.refresh(wt)

        assert wt.enabled is False
        print(f"  ✅ enabled=False guardado")

        _cleanup(db, u, b, wf)
    finally:
        db.close()


def test_find_by_workflow():
    print("\n" + "=" * 70)
    print("TEST 8: Buscar tests por workflow_id")
    print("=" * 70)
    db = SessionLocal()
    try:
        u, b, wf = _create_test_entities(db)

        for i in range(3):
            db.add(WorkflowTest(
                workflow_id=wf.id,
                bot_id=b.id,
                name=f"Test {i}",
                input_messages=json.dumps(["x"]),
                assertions=json.dumps([{"type": "reaches_end"}]),
            ))
        db.commit()

        found = db.query(WorkflowTest).filter(WorkflowTest.workflow_id == wf.id).all()
        assert len(found) == 3
        print(f"  ✅ {len(found)} tests encontrados")

        _cleanup(db, u, b, wf)
    finally:
        db.close()


def test_find_by_bot_and_enabled():
    print("\n" + "=" * 70)
    print("TEST 9: Buscar tests por bot_id + enabled")
    print("=" * 70)
    db = SessionLocal()
    try:
        u, b, wf = _create_test_entities(db)

        db.add(WorkflowTest(
            workflow_id=wf.id, bot_id=b.id, name="A",
            input_messages=json.dumps(["x"]),
            assertions=json.dumps([{"type": "reaches_end"}]),
            enabled=True,
        ))
        db.add(WorkflowTest(
            workflow_id=wf.id, bot_id=b.id, name="B",
            input_messages=json.dumps(["x"]),
            assertions=json.dumps([{"type": "reaches_end"}]),
            enabled=False,
        ))
        db.commit()

        enabled_only = (
            db.query(WorkflowTest)
            .filter(WorkflowTest.bot_id == b.id, WorkflowTest.enabled == True)
            .all()
        )
        assert len(enabled_only) == 1
        assert enabled_only[0].name == "A"
        print(f"  ✅ Filtro bot_id + enabled OK")

        _cleanup(db, u, b, wf)
    finally:
        db.close()


def test_multi_tenant_isolation():
    print("\n" + "=" * 70)
    print("TEST 10: Aislamiento multi-tenant")
    print("=" * 70)
    db = SessionLocal()
    try:
        u1, b1, wf1 = _create_test_entities(db)
        u2, b2, wf2 = _create_test_entities(db)

        db.add(WorkflowTest(
            workflow_id=wf1.id, bot_id=b1.id, name="Test user1",
            input_messages=json.dumps(["x"]),
            assertions=json.dumps([{"type": "reaches_end"}]),
        ))
        db.add(WorkflowTest(
            workflow_id=wf2.id, bot_id=b2.id, name="Test user2",
            input_messages=json.dumps(["x"]),
            assertions=json.dumps([{"type": "reaches_end"}]),
        ))
        db.commit()

        tests_b1 = db.query(WorkflowTest).filter(WorkflowTest.bot_id == b1.id).all()
        assert len(tests_b1) == 1
        assert tests_b1[0].name == "Test user1"

        tests_b2 = db.query(WorkflowTest).filter(WorkflowTest.bot_id == b2.id).all()
        assert len(tests_b2) == 1
        assert tests_b2[0].name == "Test user2"
        print(f"  ✅ Aislamiento multi-tenant OK")

        _cleanup(db, u1, b1, wf1)
        _cleanup(db, u2, b2, wf2)
    finally:
        db.close()


def test_regression_app_imports():
    print("\n" + "=" * 70)
    print("TEST 11: Regresión — app.main sigue OK")
    print("=" * 70)
    from app.main import app as _app
    assert _app is not None
    print(f"  ✅ app OK ({len(_app.routes)} rutas)")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.8.6 (WorkflowTest model)")
    print("=" * 70)

    tests = [
        test_table_exists,
        test_columns,
        test_indexes,
        test_create_workflow_test,
        test_cascade_delete_workflow,
        test_cascade_delete_bot,
        test_disabled_test,
        test_find_by_workflow,
        test_find_by_bot_and_enabled,
        test_multi_tenant_isolation,
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
