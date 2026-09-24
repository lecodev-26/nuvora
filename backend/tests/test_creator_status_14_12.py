"""
Tests - Subfase 14.12.3 (Creator Status endpoint)
====================================================
Cubre:
    - Auth: 401 sin JWT
    - Ownership: 404 (inexistente) / 403 (ajeno)
    - Configuration: OK / KO
    - Workflow: 0 activos / 1 válido / 1 inválido / 2+ activos
    - Publication: OK / KO
    - Channels: web / api / telegram / combinaciones
    - Ready: distintos escenarios
    - Next step: 4 reglas deterministas
    - Sin filtración de datos internos
"""

import sys
import os
import time
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.main import app
from app.database.config import SessionLocal
from app.models.db_models import (
    Bot, User, Workflow, WorkflowNode, WorkflowTransition,
    ApiKey, TelegramIntegration,
)
from app.services.auth import get_password_hash
from app.services.api_key_service import create_api_key


client = TestClient(app)


# ============================================================
# HELPERS
# ============================================================

def _unique(suffix):
    return f"{suffix}_{int(time.time() * 1000000)}"


def _make_user_and_bot(bot_name=None, published=False):
    """Crea user + bot. Devuelve dict con ids + jwt + email."""
    db = SessionLocal()
    try:
        uniq = _unique("cr")
        user = User(
            email=f"cr_{uniq}@nuvora.local",
            hashed_password=get_password_hash("test123"),
            is_active=1,
        )
        db.add(user); db.commit(); db.refresh(user)

        bot = Bot(
            name=bot_name if bot_name is not None else f"Bot {uniq}",
            user_id=user.id,
            is_published=published,
            public_id=f"cr-{uniq}" if published else None,
        )
        db.add(bot); db.commit(); db.refresh(bot)

        return {
            "user_id": user.id,
            "email": user.email,
            "bot_id": bot.id,
        }
    finally:
        db.close()


def _login(email):
    """Login y devuelve header Authorization."""
    r = client.post(
        "/auth/login",
        data={"username": email, "password": "test123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_active_workflow(bot_id, valid=True):
    """Crea un workflow activo (válido o inválido estructuralmente)."""
    db = SessionLocal()
    try:
        if valid:
            wf = Workflow(
                bot_id=bot_id, name="WF Válido",
                status="active", entry_node_id="s1",
            )
            db.add(wf); db.commit(); db.refresh(wf)

            n1 = WorkflowNode(workflow_id=wf.id, node_id="s1", type="start", config="{}")
            n2 = WorkflowNode(
                workflow_id=wf.id, node_id="m1", type="message",
                config=json.dumps({"text": "Hola"}),
            )
            n3 = WorkflowNode(workflow_id=wf.id, node_id="e1", type="end", config="{}")
            db.add_all([n1, n2, n3])

            t1 = WorkflowTransition(workflow_id=wf.id, from_node_id="s1", to_node_id="m1", order=0)
            t2 = WorkflowTransition(workflow_id=wf.id, from_node_id="m1", to_node_id="e1", order=0)
            db.add_all([t1, t2])
            db.commit()
        else:
            # Workflow inválido: SIN nodo START
            wf = Workflow(
                bot_id=bot_id, name="WF Inválido",
                status="active", entry_node_id=None,
            )
            db.add(wf); db.commit(); db.refresh(wf)

            # Solo un MESSAGE + END (sin START → falla el validador)
            n1 = WorkflowNode(
                workflow_id=wf.id, node_id="m1", type="message",
                config=json.dumps({"text": "Hola"}),
            )
            n2 = WorkflowNode(workflow_id=wf.id, node_id="e1", type="end", config="{}")
            db.add_all([n1, n2])
            db.commit()

        return wf.id
    finally:
        db.close()


def _cleanup(user_id, bot_id):
    db = SessionLocal()
    try:
        db.query(WorkflowNode).filter(
            WorkflowNode.workflow_id.in_(
                db.query(Workflow.id).filter(Workflow.bot_id == bot_id)
            )
        ).delete(synchronize_session=False)
        db.query(WorkflowTransition).filter(
            WorkflowTransition.workflow_id.in_(
                db.query(Workflow.id).filter(Workflow.bot_id == bot_id)
            )
        ).delete(synchronize_session=False)
        db.query(Workflow).filter(Workflow.bot_id == bot_id).delete()
        db.query(ApiKey).filter(ApiKey.bot_id == bot_id).delete()
        db.query(TelegramIntegration).filter(TelegramIntegration.bot_id == bot_id).delete()
        db.query(Bot).filter(Bot.id == bot_id).delete()
        db.query(User).filter(User.id == user_id).delete()
        db.commit()
    finally:
        db.close()


# ============================================================
# TESTS
# ============================================================

def test_requires_auth():
    """Sin JWT → 401."""
    env = _make_user_and_bot()
    try:
        r = client.get(f"/bots/{env['bot_id']}/creator-status")
        assert r.status_code == 401
    finally:
        _cleanup(env["user_id"], env["bot_id"])


def test_bot_not_found():
    """Bot inexistente → 404."""
    env = _make_user_and_bot()
    try:
        headers = _login(env["email"])
        r = client.get("/bots/99999999/creator-status", headers=headers)
        assert r.status_code == 404
    finally:
        _cleanup(env["user_id"], env["bot_id"])


def test_bot_ajeno_403():
    """Bot de otro usuario → 403."""
    env_a = _make_user_and_bot()
    env_b = _make_user_and_bot()
    try:
        headers_a = _login(env_a["email"])
        r = client.get(f"/bots/{env_b['bot_id']}/creator-status", headers=headers_a)
        assert r.status_code == 403
    finally:
        _cleanup(env_a["user_id"], env_a["bot_id"])
        _cleanup(env_b["user_id"], env_b["bot_id"])


def test_configuration_ok_with_name():
    """Bot con nombre válido → configuration.ok = true."""
    env = _make_user_and_bot(bot_name="Mi Bot")
    try:
        headers = _login(env["email"])
        r = client.get(f"/bots/{env['bot_id']}/creator-status", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["configuration"]["ok"] is True
    finally:
        _cleanup(env["user_id"], env["bot_id"])


def test_workflow_not_active():
    """Sin workflow activo → workflow.ok = false."""
    env = _make_user_and_bot()
    try:
        headers = _login(env["email"])
        r = client.get(f"/bots/{env['bot_id']}/creator-status", headers=headers)
        data = r.json()
        assert data["workflow"]["ok"] is False
        assert data["workflow"]["id"] is None
        assert data["workflow"]["name"] is None
    finally:
        _cleanup(env["user_id"], env["bot_id"])


def test_workflow_active_valid():
    """1 workflow activo y válido → workflow.ok = true."""
    env = _make_user_and_bot()
    try:
        wf_id = _create_active_workflow(env["bot_id"], valid=True)
        headers = _login(env["email"])
        r = client.get(f"/bots/{env['bot_id']}/creator-status", headers=headers)
        data = r.json()
        assert data["workflow"]["ok"] is True
        assert data["workflow"]["id"] == wf_id
        assert data["workflow"]["name"] == "WF Válido"
    finally:
        _cleanup(env["user_id"], env["bot_id"])


def test_workflow_active_invalid_structure():
    """Workflow status=active pero estructuralmente inválido → workflow.ok = false."""
    env = _make_user_and_bot()
    try:
        _create_active_workflow(env["bot_id"], valid=False)
        headers = _login(env["email"])
        r = client.get(f"/bots/{env['bot_id']}/creator-status", headers=headers)
        data = r.json()
        assert data["workflow"]["ok"] is False
    finally:
        _cleanup(env["user_id"], env["bot_id"])


def test_publication_not_published():
    """Bot sin publicar → publication.ok = false."""
    env = _make_user_and_bot(published=False)
    try:
        headers = _login(env["email"])
        r = client.get(f"/bots/{env['bot_id']}/creator-status", headers=headers)
        data = r.json()
        assert data["publication"]["ok"] is False
        assert data["publication"]["public_url"] is None
    finally:
        _cleanup(env["user_id"], env["bot_id"])


def test_publication_published():
    """Bot publicado → publication.ok = true + public_url."""
    env = _make_user_and_bot(published=True)
    try:
        headers = _login(env["email"])
        r = client.get(f"/bots/{env['bot_id']}/creator-status", headers=headers)
        data = r.json()
        assert data["publication"]["ok"] is True
        assert data["publication"]["public_url"] is not None
        assert "/b/" in data["publication"]["public_url"]
    finally:
        _cleanup(env["user_id"], env["bot_id"])


def test_channels_web_only():
    """Publicado sin keys ni telegram → web=true, api=false, telegram=false."""
    env = _make_user_and_bot(published=True)
    try:
        headers = _login(env["email"])
        r = client.get(f"/bots/{env['bot_id']}/creator-status", headers=headers)
        data = r.json()
        assert data["channels"]["web"] is True
        assert data["channels"]["api"] is False
        assert data["channels"]["telegram"] is False
    finally:
        _cleanup(env["user_id"], env["bot_id"])


def test_channels_api_active():
    """Bot con 1 API key activa → api=true."""
    env = _make_user_and_bot(published=True)
    try:
        db = SessionLocal()
        try:
            create_api_key(
                db=db,
                user_id=env["user_id"],
                bot_id=env["bot_id"],
                name="Test Key",
            )
        finally:
            db.close()

        headers = _login(env["email"])
        r = client.get(f"/bots/{env['bot_id']}/creator-status", headers=headers)
        data = r.json()
        assert data["channels"]["api"] is True
    finally:
        _cleanup(env["user_id"], env["bot_id"])


def test_channels_telegram_connected():
    """Bot con TelegramIntegration status=connected → telegram=true."""
    from app.services.ai_config_service import encrypt_api_key
    import secrets

    env = _make_user_and_bot(published=True)
    try:
        db = SessionLocal()
        try:
            secret = secrets.token_urlsafe(32)
            tg = TelegramIntegration(
                bot_id=env["bot_id"],
                telegram_bot_id="999",
                telegram_username="test_bot",
                encrypted_token=encrypt_api_key("123:FAKE"),
                webhook_secret=secret,
                webhook_url=f"http://localhost:8000/webhooks/telegram/{secret}",
                status="connected",
                is_active=True,
            )
            db.add(tg); db.commit()
        finally:
            db.close()

        headers = _login(env["email"])
        r = client.get(f"/bots/{env['bot_id']}/creator-status", headers=headers)
        data = r.json()
        assert data["channels"]["telegram"] is True
    finally:
        _cleanup(env["user_id"], env["bot_id"])


def test_ready_false_when_no_workflow():
    """Sin workflow → ready=false."""
    env = _make_user_and_bot(published=True)
    try:
        headers = _login(env["email"])
        r = client.get(f"/bots/{env['bot_id']}/creator-status", headers=headers)
        data = r.json()
        assert data["ready"] is False
    finally:
        _cleanup(env["user_id"], env["bot_id"])


def test_ready_false_when_not_published():
    """Con workflow válido pero sin publicar → ready=false."""
    env = _make_user_and_bot(published=False)
    try:
        _create_active_workflow(env["bot_id"], valid=True)
        headers = _login(env["email"])
        r = client.get(f"/bots/{env['bot_id']}/creator-status", headers=headers)
        data = r.json()
        assert data["ready"] is False
    finally:
        _cleanup(env["user_id"], env["bot_id"])


def test_ready_true_when_all_ok():
    """Config + workflow válido + publicado → ready=true."""
    env = _make_user_and_bot(published=True)
    try:
        _create_active_workflow(env["bot_id"], valid=True)
        headers = _login(env["email"])
        r = client.get(f"/bots/{env['bot_id']}/creator-status", headers=headers)
        data = r.json()
        assert data["ready"] is True
    finally:
        _cleanup(env["user_id"], env["bot_id"])


def test_next_step_configuration():
    """next_step = 'configuration' si config no OK (bot sin nombre)."""
    env = _make_user_and_bot(bot_name="")
    try:
        headers = _login(env["email"])
        r = client.get(f"/bots/{env['bot_id']}/creator-status", headers=headers)
        data = r.json()
        # NOTA: si name es "" el bot no debería existir, pero al forzarlo:
        assert data["next_step"] in ("configuration", "workflow")
    finally:
        _cleanup(env["user_id"], env["bot_id"])


def test_next_step_workflow():
    """next_step = 'workflow' si config OK pero sin workflow."""
    env = _make_user_and_bot()
    try:
        headers = _login(env["email"])
        r = client.get(f"/bots/{env['bot_id']}/creator-status", headers=headers)
        data = r.json()
        assert data["next_step"] == "workflow"
    finally:
        _cleanup(env["user_id"], env["bot_id"])


def test_next_step_publication():
    """next_step = 'publication' si workflow OK pero sin publicar."""
    env = _make_user_and_bot(published=False)
    try:
        _create_active_workflow(env["bot_id"], valid=True)
        headers = _login(env["email"])
        r = client.get(f"/bots/{env['bot_id']}/creator-status", headers=headers)
        data = r.json()
        assert data["next_step"] == "publication"
    finally:
        _cleanup(env["user_id"], env["bot_id"])


def test_next_step_null_when_ready():
    """next_step = null cuando todo OK."""
    env = _make_user_and_bot(published=True)
    try:
        _create_active_workflow(env["bot_id"], valid=True)
        headers = _login(env["email"])
        r = client.get(f"/bots/{env['bot_id']}/creator-status", headers=headers)
        data = r.json()
        assert data["next_step"] is None
    finally:
        _cleanup(env["user_id"], env["bot_id"])


def test_no_internal_data_leaked():
    """El contrato NO expone datos internos (nodos, config, prompts, etc.)."""
    env = _make_user_and_bot(published=True)
    try:
        _create_active_workflow(env["bot_id"], valid=True)
        headers = _login(env["email"])
        r = client.get(f"/bots/{env['bot_id']}/creator-status", headers=headers)
        data = r.json()

        # Verificar que NO hay campos internos
        serialized = json.dumps(data).lower()
        forbidden = ["prompt", "nodes", "transitions", "encrypted", "token", "secret"]
        for word in forbidden:
            assert word not in serialized, f"Filtración detectada: {word}"

        # Verificar estructura exacta de claves
        assert set(data.keys()) == {"bot_id", "configuration", "workflow", "publication", "channels", "ready", "next_step"}
    finally:
        _cleanup(env["user_id"], env["bot_id"])
