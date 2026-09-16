"""
Tests — Subfase 14.9.6 (Public Workflow Resolver)
===================================================
Cubre:
    - resolve_public_bot: 404 si no existe / no publicado / input inválido
    - resolve_public_bot_by_identifier: prioridad public_id, fallback slug
    - get_active_workflow: 1 activo OK, 0 activos 500, 2 activos 500
    - build_public_workflow_dict: estructura + parseo config
    - parse_public_config: JSON válido, vacío, corrupto
    - is_publicly_accessible: combinaciones de flags
"""

import sys
import os
import time
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import HTTPException

from app.database.config import SessionLocal
from app.models.db_models import (
    Bot, User, Workflow, WorkflowNode, WorkflowTransition,
)
from app.services.public_resolver import (
    resolve_public_bot,
    resolve_public_bot_by_identifier,
    get_active_workflow,
    build_public_workflow_dict,
    parse_public_config,
    is_publicly_accessible,
)


# ============================================================
# HELPERS
# ============================================================

def _unique(suffix):
    return f"{suffix}_{int(time.time() * 1000000)}_{os.getpid()}"


def _cleanup_user(db, email):
    u = db.query(User).filter(User.email == email).first()
    if u:
        bots = db.query(Bot).filter(Bot.user_id == u.id).all()
        for b in bots:
            db.delete(b)
        db.delete(u)
        db.commit()


def _create_user(db):
    email = f"{_unique('pub_res_user')}@nuvora.com"
    u = User(email=email, hashed_password="x", full_name="Resolver Test")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u, email


def _create_bot(db, user_id, name, is_published=False,
                public_id=None, public_slug=None, public_config=None):
    b = Bot(
        user_id=user_id,
        name=name,
        business_name="Test",
        nicho_id="otro",
        is_published=is_published,
        public_id=public_id,
        public_slug=public_slug,
        public_config=public_config,
        published_at=datetime.now(timezone.utc) if is_published else None,
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


def _create_workflow(db, bot_id, status="active", with_nodes=True):
    wf = Workflow(bot_id=bot_id, name=f"WF {_unique('wf')}", status=status)
    db.add(wf)
    db.flush()

    if with_nodes:
        db.add(WorkflowNode(
            workflow_id=wf.id, node_id="s1", type="start",
        ))
        db.add(WorkflowNode(
            workflow_id=wf.id, node_id="m1", type="message",
            config=json.dumps({"text": "Hola"}),
        ))
        db.add(WorkflowNode(
            workflow_id=wf.id, node_id="e1", type="end",
        ))
        db.add(WorkflowTransition(
            workflow_id=wf.id, from_node_id="s1", to_node_id="m1", order=0,
        ))
        db.add(WorkflowTransition(
            workflow_id=wf.id, from_node_id="m1", to_node_id="e1", order=0,
        ))

    db.commit()
    db.refresh(wf)
    return wf


# ============================================================
# TESTS — resolve_public_bot
# ============================================================

def test_resolve_public_bot_ok():
    print("\n" + "=" * 70)
    print("TEST 1: resolve_public_bot — bot publicado OK")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(
            db, u.id, "Bot OK", is_published=True,
            public_id=_unique("pid"),
        )
        found = resolve_public_bot(b.public_id, db)
        assert found.id == b.id
        print(f"  ✅ Encontrado: bot #{found.id}")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_resolve_public_bot_not_published():
    print("\n" + "=" * 70)
    print("TEST 2: resolve_public_bot — bot NO publicado → 404")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(
            db, u.id, "Bot Not Pub", is_published=False,
            public_id=_unique("pid"),
        )
        try:
            resolve_public_bot(b.public_id, db)
            raise AssertionError("Debería haber lanzado 404")
        except HTTPException as e:
            assert e.status_code == 404
            print(f"  ✅ 404")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_resolve_public_bot_not_found():
    print("\n" + "=" * 70)
    print("TEST 3: resolve_public_bot — public_id inexistente → 404")
    print("=" * 70)
    db = SessionLocal()
    try:
        try:
            resolve_public_bot("non-existent-uuid-xxxx", db)
            raise AssertionError("Debería haber lanzado 404")
        except HTTPException as e:
            assert e.status_code == 404
            print("  ✅ 404")
    finally:
        db.close()


def test_resolve_public_bot_invalid_input():
    print("\n" + "=" * 70)
    print("TEST 4: resolve_public_bot — input inválido → 404")
    print("=" * 70)
    db = SessionLocal()
    try:
        for bad in [None, "", 123, [], {}]:
            try:
                resolve_public_bot(bad, db)
                raise AssertionError(f"Debería haber lanzado 404 con {bad!r}")
            except HTTPException as e:
                assert e.status_code == 404
        print("  ✅ 5 inputs inválidos → 404")
    finally:
        db.close()


# ============================================================
# TESTS — resolve_public_bot_by_identifier
# ============================================================

def test_resolve_by_identifier_id():
    print("\n" + "=" * 70)
    print("TEST 5: resolve_public_bot_by_identifier — encuentra por public_id")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(
            db, u.id, "Bot Id", is_published=True,
            public_id=_unique("pid"),
            public_slug=_unique("slug"),
        )
        found = resolve_public_bot_by_identifier(b.public_id, db)
        assert found.id == b.id
        print(f"  ✅ Encontrado por public_id")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_resolve_by_identifier_slug():
    print("\n" + "=" * 70)
    print("TEST 6: resolve_public_bot_by_identifier — fallback a public_slug")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        slug = _unique("slug-only")
        b = _create_bot(
            db, u.id, "Bot Slug", is_published=True,
            public_id=_unique("pid"),
            public_slug=slug,
        )
        found = resolve_public_bot_by_identifier(slug, db)
        assert found.id == b.id
        print(f"  ✅ Encontrado por slug")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_resolve_by_identifier_prioritizes_id():
    print("\n" + "=" * 70)
    print("TEST 7: resolve_by_identifier — public_id tiene prioridad")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        # Bot A: public_id = "shared-x"
        bot_a = _create_bot(
            db, u.id, "Bot A", is_published=True,
            public_id="shared-priority-id",
            public_slug="slug-of-bot-a",
        )
        found = resolve_public_bot_by_identifier("shared-priority-id", db)
        assert found.id == bot_a.id
        print(f"  ✅ Prioriza public_id sobre slug")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_resolve_by_identifier_not_published():
    print("\n" + "=" * 70)
    print("TEST 8: resolve_by_identifier — no publicado → 404")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(
            db, u.id, "Bot NP", is_published=False,
            public_id="nopub-id",
            public_slug="nopub-slug",
        )
        for identifier in ["nopub-id", "nopub-slug"]:
            try:
                resolve_public_bot_by_identifier(identifier, db)
                raise AssertionError(f"Debería haber lanzado 404 con {identifier!r}")
            except HTTPException as e:
                assert e.status_code == 404
        print("  ✅ 404 (tanto por id como por slug)")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


# ============================================================
# TESTS — get_active_workflow
# ============================================================

def test_get_active_workflow_ok():
    print("\n" + "=" * 70)
    print("TEST 9: get_active_workflow — 1 activo OK")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id, "Bot WF", is_published=False)
        wf = _create_workflow(db, b.id, status="active")
        found = get_active_workflow(b.id, db)
        assert found.id == wf.id
        print(f"  ✅ Encontrado wf #{found.id}")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_get_active_workflow_zero():
    print("\n" + "=" * 70)
    print("TEST 10: get_active_workflow — 0 activos → 500")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id, "Bot No WF", is_published=False)
        try:
            get_active_workflow(b.id, db)
            raise AssertionError("Debería haber lanzado 500")
        except HTTPException as e:
            assert e.status_code == 500
            print(f"  ✅ 500: {e.detail}")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_get_active_workflow_two():
    print("\n" + "=" * 70)
    print("TEST 11: get_active_workflow — 2 activos → 500")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id, "Bot 2WF", is_published=False)
        _create_workflow(db, b.id, status="active")
        _create_workflow(db, b.id, status="active")
        try:
            get_active_workflow(b.id, db)
            raise AssertionError("Debería haber lanzado 500")
        except HTTPException as e:
            assert e.status_code == 500
            print(f"  ✅ 500 (2 activos)")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


# ============================================================
# TESTS — build_public_workflow_dict
# ============================================================

def test_build_public_workflow_dict():
    print("\n" + "=" * 70)
    print("TEST 12: build_public_workflow_dict — estructura correcta")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id, "Bot D", is_published=False)
        wf = _create_workflow(db, b.id, status="active", with_nodes=True)
        d = build_public_workflow_dict(wf)
        assert "nodes" in d
        assert "transitions" in d
        assert len(d["nodes"]) == 3
        assert len(d["transitions"]) == 2
        assert d["nodes"][0]["node_id"] == "s1"
        assert d["nodes"][1]["config"] == {"text": "Hola"}
        assert d["transitions"][0]["order"] == 0
        print(f"  ✅ {len(d['nodes'])} nodos, {len(d['transitions'])} transiciones")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_build_public_workflow_dict_invalid_config():
    print("\n" + "=" * 70)
    print("TEST 13: build_public_workflow_dict — config corrupto → None")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id, "Bot Corrupt", is_published=False)

        wf = Workflow(bot_id=b.id, name="Corrupt", status="active")
        db.add(wf)
        db.flush()
        db.add(WorkflowNode(
            workflow_id=wf.id, node_id="m1", type="message",
            config="this-is-not-json",
        ))
        db.commit()
        db.refresh(wf)

        d = build_public_workflow_dict(wf)
        assert d["nodes"][0]["config"] is None
        print("  ✅ config corrupto → None")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


# ============================================================
# TESTS — parse_public_config
# ============================================================

def test_parse_public_config_valid():
    print("\n" + "=" * 70)
    print("TEST 14: parse_public_config — JSON válido")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(
            db, u.id, "Bot CFG", is_published=False,
            public_config=json.dumps({"welcome_message": "Hola"}),
        )
        cfg = parse_public_config(b)
        assert cfg["welcome_message"] == "Hola"
        print("  ✅ JSON válido → dict")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_parse_public_config_none():
    print("\n" + "=" * 70)
    print("TEST 15: parse_public_config — sin config → {}")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(db, u.id, "Bot NoCFG", is_published=False)
        cfg = parse_public_config(b)
        assert cfg == {}
        print("  ✅ Sin config → {}")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_parse_public_config_corrupt():
    print("\n" + "=" * 70)
    print("TEST 16: parse_public_config — JSON corrupto → {}")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(
            db, u.id, "Bot CorruptCFG", is_published=False,
            public_config="not-json",
        )
        cfg = parse_public_config(b)
        assert cfg == {}
        print("  ✅ JSON corrupto → {}")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


# ============================================================
# TESTS — is_publicly_accessible
# ============================================================

def test_is_publicly_accessible_true():
    print("\n" + "=" * 70)
    print("TEST 17: is_publicly_accessible — True")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)
        b = _create_bot(
            db, u.id, "Bot Acc", is_published=True,
            public_id="acc-id",
        )
        assert is_publicly_accessible(b) is True
        print("  ✅ True")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


def test_is_publicly_accessible_false():
    print("\n" + "=" * 70)
    print("TEST 18: is_publicly_accessible — False (varias combinaciones)")
    print("=" * 70)
    db = SessionLocal()
    u = None
    try:
        u, email = _create_user(db)

        b1 = _create_bot(db, u.id, "B1", is_published=False, public_id="x1")
        assert is_publicly_accessible(b1) is False

        b2 = _create_bot(db, u.id, "B2", is_published=True, public_id=None)
        assert is_publicly_accessible(b2) is False

        b3 = _create_bot(db, u.id, "B3", is_published=False, public_id=None)
        assert is_publicly_accessible(b3) is False

        print("  ✅ 3 combinaciones → False")
    finally:
        if u:
            _cleanup_user(db, u.email)
        db.close()


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.9.6 (Public Resolver)")
    print("=" * 70)

    tests = [
        test_resolve_public_bot_ok,
        test_resolve_public_bot_not_published,
        test_resolve_public_bot_not_found,
        test_resolve_public_bot_invalid_input,
        test_resolve_by_identifier_id,
        test_resolve_by_identifier_slug,
        test_resolve_by_identifier_prioritizes_id,
        test_resolve_by_identifier_not_published,
        test_get_active_workflow_ok,
        test_get_active_workflow_zero,
        test_get_active_workflow_two,
        test_build_public_workflow_dict,
        test_build_public_workflow_dict_invalid_config,
        test_parse_public_config_valid,
        test_parse_public_config_none,
        test_parse_public_config_corrupt,
        test_is_publicly_accessible_true,
        test_is_publicly_accessible_false,
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
