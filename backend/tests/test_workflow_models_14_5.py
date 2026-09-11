"""
Tests — Subfase 14.5.1
Verifica modelos Workflow, WorkflowNode, WorkflowTransition.
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database.config import SessionLocal, engine
from app.models.db_models import (
    Bot, User, Workflow, WorkflowNode, WorkflowTransition,
)


# ============================================================
# HELPERS
# ============================================================

def _unique(suffix: str) -> str:
    return f"{suffix}_{int(time.time() * 1000)}"


def setup_user_bot(suffix: str) -> tuple[int, int]:
    db = SessionLocal()
    try:
        from app.services.auth import get_password_hash

        email = f"test_wf_{suffix}@nuvora.com"
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                hashed_password=get_password_hash("123456"),
                full_name=f"Test WF {suffix}",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        bot_name = f"Bot WF {suffix}"
        bot = db.query(Bot).filter(Bot.name == bot_name).first()
        if not bot:
            bot = Bot(
                user_id=user.id,
                name=bot_name,
                business_name=f"Test {suffix}",
                nicho_id="otro",
                is_active=True,
                is_published=False,
                answer_mode="strict",
            )
            db.add(bot)
            db.commit()
            db.refresh(bot)

        return user.id, bot.id
    finally:
        db.close()


def cleanup_bot(bot_id: int):
    db = SessionLocal()
    try:
        db.query(WorkflowTransition).filter(
            WorkflowTransition.workflow_id.in_(
                db.query(Workflow.id).filter(Workflow.bot_id == bot_id)
            )
        ).delete(synchronize_session=False)
        db.query(WorkflowNode).filter(
            WorkflowNode.workflow_id.in_(
                db.query(Workflow.id).filter(Workflow.bot_id == bot_id)
            )
        ).delete(synchronize_session=False)
        db.query(Workflow).filter(Workflow.bot_id == bot_id).delete(synchronize_session=False)
        db.query(Bot).filter(Bot.id == bot_id).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def cleanup_user(email: str):
    db = SessionLocal()
    try:
        db.query(User).filter(User.email == email).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


# ============================================================
# TESTS
# ============================================================

def test_create_workflow():
    print("\n" + "=" * 70)
    print("TEST 1: Crear Workflow")
    print("=" * 70)
    unique = _unique("cw")
    email = f"test_wf_{unique}@nuvora.com"
    user_id, bot_id = setup_user_bot(unique)
    try:
        db = SessionLocal()
        wf = Workflow(
            bot_id=bot_id,
            name="Test Workflow",
            description="Descripción de prueba",
            status="draft",
            version=1,
            trigger="manual",
        )
        db.add(wf)
        db.commit()
        db.refresh(wf)

        assert wf.id is not None
        assert wf.name == "Test Workflow"
        assert wf.status == "draft"
        assert wf.version == 1
        assert wf.trigger == "manual"
        assert wf.created_at is not None
        print(f"✅ Workflow creado: id={wf.id}, name='{wf.name}'")
        db.close()
    finally:
        cleanup_bot(bot_id)
        cleanup_user(email)


def test_create_workflow_with_nodes():
    print("\n" + "=" * 70)
    print("TEST 2: Crear Workflow con Nodes")
    print("=" * 70)
    unique = _unique("cw_nodes")
    email = f"test_wf_{unique}@nuvora.com"
    user_id, bot_id = setup_user_bot(unique)
    try:
        db = SessionLocal()
        wf = Workflow(bot_id=bot_id, name="WF con nodos")
        db.add(wf)
        db.commit()
        db.refresh(wf)

        node1 = WorkflowNode(
            workflow_id=wf.id,
            node_id="start_1",
            type="start",
            name="Inicio",
            config=None,
        )
        node2 = WorkflowNode(
            workflow_id=wf.id,
            node_id="msg_1",
            type="message",
            name="Mensaje",
            config='{"text": "Hola"}',
        )
        db.add_all([node1, node2])
        db.commit()

        nodes = db.query(WorkflowNode).filter(WorkflowNode.workflow_id == wf.id).all()
        assert len(nodes) == 2
        print(f"✅ {len(nodes)} nodos creados")
        db.close()
    finally:
        cleanup_bot(bot_id)
        cleanup_user(email)


def test_create_workflow_with_transitions():
    print("\n" + "=" * 70)
    print("TEST 3: Crear Workflow con Transitions")
    print("=" * 70)
    unique = _unique("cw_trans")
    email = f"test_wf_{unique}@nuvora.com"
    user_id, bot_id = setup_user_bot(unique)
    try:
        db = SessionLocal()
        wf = Workflow(bot_id=bot_id, name="WF transiciones")
        db.add(wf)
        db.commit()
        db.refresh(wf)

        t1 = WorkflowTransition(
            workflow_id=wf.id,
            from_node_id="start_1",
            to_node_id="msg_1",
        )
        t2 = WorkflowTransition(
            workflow_id=wf.id,
            from_node_id="cond_1",
            to_node_id="msg_1",
            condition='name == "Manuel"',
            label="true",
            order=1,
        )
        db.add_all([t1, t2])
        db.commit()

        transitions = db.query(WorkflowTransition).filter(
            WorkflowTransition.workflow_id == wf.id
        ).all()
        assert len(transitions) == 2
        # Verificar orden por label
        labels = {t.label for t in transitions}
        assert "true" in labels
        assert None in labels
        print(f"✅ {len(transitions)} transiciones creadas")
        db.close()
    finally:
        cleanup_bot(bot_id)
        cleanup_user(email)


def test_cascade_delete_workflow():
    print("\n" + "=" * 70)
    print("TEST 4: CASCADE al eliminar workflow")
    print("=" * 70)
    unique = _unique("cascade")
    email = f"test_wf_{unique}@nuvora.com"
    user_id, bot_id = setup_user_bot(unique)
    try:
        db = SessionLocal()
        wf = Workflow(bot_id=bot_id, name="WF cascade")
        db.add(wf)
        db.commit()
        db.refresh(wf)
        wf_id = wf.id

        db.add_all([
            WorkflowNode(workflow_id=wf_id, node_id="n1", type="start"),
            WorkflowNode(workflow_id=wf_id, node_id="n2", type="end"),
            WorkflowTransition(workflow_id=wf_id, from_node_id="n1", to_node_id="n2"),
        ])
        db.commit()
        db.close()

        # Borrar workflow
        db = SessionLocal()
        wf = db.query(Workflow).filter(Workflow.id == wf_id).first()
        db.delete(wf)
        db.commit()

        # Verificar que nodos y transiciones desaparecieron
        nodes_after = db.query(WorkflowNode).filter(WorkflowNode.workflow_id == wf_id).count()
        trans_after = db.query(WorkflowTransition).filter(WorkflowTransition.workflow_id == wf_id).count()
        db.close()

        assert nodes_after == 0, f"CASCADE nodos falló: {nodes_after}"
        assert trans_after == 0, f"CASCADE transiciones falló: {trans_after}"
        print(f"✅ CASCADE funciona: 0 nodos, 0 transiciones")
    finally:
        cleanup_bot(bot_id)
        cleanup_user(email)


def test_unique_node_id_per_workflow():
    print("\n" + "=" * 70)
    print("TEST 5: node_id único dentro de workflow")
    print("=" * 70)
    unique = _unique("unique")
    email = f"test_wf_{unique}@nuvora.com"
    user_id, bot_id = setup_user_bot(unique)
    try:
        db = SessionLocal()
        wf = Workflow(bot_id=bot_id, name="WF unique")
        db.add(wf)
        db.commit()
        db.refresh(wf)

        # Primer nodo: OK
        db.add(WorkflowNode(workflow_id=wf.id, node_id="dup_1", type="start"))
        db.commit()

        # Segundo nodo con mismo node_id: debe fallar
        db.add(WorkflowNode(workflow_id=wf.id, node_id="dup_1", type="end"))
        try:
            db.commit()
            assert False, "Debería haber lanzado IntegrityError"
        except Exception as e:
            db.rollback()
            assert "unique" in str(e).lower() or "integrity" in str(e).lower()
            print(f"✅ Unique constraint funciona")

        db.close()
    finally:
        cleanup_bot(bot_id)
        cleanup_user(email)


def test_same_node_id_across_workflows():
    print("\n" + "=" * 70)
    print("TEST 6: mismo node_id en distintos workflows (permitido)")
    print("=" * 70)
    unique = _unique("across")
    email = f"test_wf_{unique}@nuvora.com"
    user_id, bot_id = setup_user_bot(unique)
    try:
        db = SessionLocal()
        wf1 = Workflow(bot_id=bot_id, name="WF 1")
        wf2 = Workflow(bot_id=bot_id, name="WF 2")
        db.add_all([wf1, wf2])
        db.commit()
        db.refresh(wf1)
        db.refresh(wf2)

        # Mismo node_id en dos workflows distintos: OK
        db.add(WorkflowNode(workflow_id=wf1.id, node_id="start_1", type="start"))
        db.add(WorkflowNode(workflow_id=wf2.id, node_id="start_1", type="start"))
        db.commit()

        nodes = db.query(WorkflowNode).filter(WorkflowNode.node_id == "start_1").all()
        assert len(nodes) == 2
        print(f"✅ Mismo node_id en 2 workflows: OK")
        db.close()
    finally:
        cleanup_bot(bot_id)
        cleanup_user(email)


def test_indexes_exist():
    print("\n" + "=" * 70)
    print("TEST 7: Verificar índices")
    print("=" * 70)
    db = SessionLocal()
    try:
        db_url = str(engine.url)
        if db_url.startswith("sqlite"):
            result = db.execute(text(
                "SELECT name FROM sqlite_master "
                "WHERE type='index' AND tbl_name IN ('workflows','workflow_nodes','workflow_transitions')"
            )).fetchall()
        else:
            result = db.execute(text(
                "SELECT indexname FROM pg_indexes "
                "WHERE tablename IN ('workflows','workflow_nodes','workflow_transitions')"
            )).fetchall()

        names = [r[0] for r in result if r[0]]
        print(f"   Índices encontrados: {len(names)}")
        for n in names:
            print(f"      - {n}")

        # Buscar al menos los índices clave
        expected = ["workflows_bot_id", "workflow_nodes_workflow_id", "workflow_transitions_workflow_id"]
        for exp in expected:
            found = any(exp in n for n in names)
            assert found, f"Falta índice con '{exp}'"
        print(f"✅ Índices verificados")
    finally:
        db.close()


def test_multi_tenant_isolation():
    print("\n" + "=" * 70)
    print("TEST 8: Aislamiento multi-tenant")
    print("=" * 70)
    u1, bot1 = setup_user_bot("mt1")
    u2, bot2 = setup_user_bot("mt2")
    try:
        db = SessionLocal()
        wf1 = Workflow(bot_id=bot1, name="WF Bot 1")
        wf2 = Workflow(bot_id=bot2, name="WF Bot 2")
        db.add_all([wf1, wf2])
        db.commit()

        # Consultar workflows por bot_id
        wfs_bot1 = db.query(Workflow).filter(Workflow.bot_id == bot1).all()
        wfs_bot2 = db.query(Workflow).filter(Workflow.bot_id == bot2).all()

        assert len(wfs_bot1) == 1
        assert len(wfs_bot2) == 1
        assert wfs_bot1[0].name == "WF Bot 1"
        assert wfs_bot2[0].name == "WF Bot 2"
        print(f"✅ Aislamiento OK: bot1={len(wfs_bot1)}, bot2={len(wfs_bot2)}")
        db.close()
    finally:
        cleanup_bot(bot1)
        cleanup_bot(bot2)
        cleanup_user(f"test_wf_mt1_{''.join(filter(str.isdigit, ''))}@nuvora.com")  # limpia por nombre
        cleanup_user("test_wf_mt1@nuvora.com")
        cleanup_user("test_wf_mt2@nuvora.com")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.5.1 (Workflow Models)")
    print("=" * 70)

    tests = [
        test_create_workflow,
        test_create_workflow_with_nodes,
        test_create_workflow_with_transitions,
        test_cascade_delete_workflow,
        test_unique_node_id_per_workflow,
        test_same_node_id_across_workflows,
        test_indexes_exist,
        test_multi_tenant_isolation,
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
