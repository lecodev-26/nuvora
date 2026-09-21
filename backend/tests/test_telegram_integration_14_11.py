"""
Tests - Subfase 14.11.19 (Integración E2E Telegram)
=====================================================
Suite de INTEGRACIÓN del flujo completo Telegram:

    Telegram Update
        |
    Webhook (secret + idempotencia)
        |
    Mapper -> ChannelRequest
        |
    Session helper (crear o recuperar)
        |
    WorkflowEngine (ejecutar workflow activo)
        |
    Adapter (send_message)
        |
    Conversation (analytics con channel=telegram)

DIFERENCIA CON 14.11.10:
    - 14.11.10 cubre el webhook en aislamiento (unit-ish).
    - 14.11.19 verifica el flujo COMPLETO cruzando varios componentes
      (webhook + sesiones + workflow + analytics) en un mismo test.

PATRÓN:
    BD SQLite local + helpers con _unique() + cleanup al final.
"""

import sys
import os
import time
import json
import secrets

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.database.config import SessionLocal
from app.models.db_models import (
    Bot, User, Workflow, WorkflowNode, WorkflowTransition,
    TelegramIntegration, TelegramUpdate, PublicSession, Conversation,
)
from app.services.auth import get_password_hash
from app.services.ai_config_service import encrypt_api_key
from app.core.public_rate_limit import reset_public_all


client = TestClient(app)


# ============================================================
# HELPERS
# ============================================================

def _unique(suffix):
    return f"{suffix}_{int(time.time() * 1000000)}"


def _mock_telegram_send_ok(text="Respuesta del workflow"):
    """Mock requests.post para sendMessage."""
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {
        "ok": True,
        "result": {"message_id": 1000, "chat": {"id": 555}, "text": text},
    }
    return mock


def _make_env(with_workflow=True, bot_published=True):
    """
    Setup de integración: user + bot + workflow + integración Telegram.

    Devuelve dict con user_id, bot_id, integration_id, secret, chat_id.
    """
    db = SessionLocal()
    try:
        uniq = _unique("int")

        # User
        user = User(
            email=f"tgint_{uniq}@nuvora.local",
            hashed_password=get_password_hash("test123"),
            is_active=1,
        )
        db.add(user); db.commit(); db.refresh(user)

        # Bot
        bot = Bot(
            name=f"Tg Int Bot {uniq}",
            user_id=user.id,
            is_published=bot_published,
            public_id=f"tgint-{uniq}",
        )
        db.add(bot); db.commit(); db.refresh(bot)

        # Workflow activo
        if with_workflow:
            wf = Workflow(
                bot_id=bot.id,
                name=f"WF Int {uniq}",
                status="active",
                entry_node_id="s1",
            )
            db.add(wf); db.commit(); db.refresh(wf)

            n1 = WorkflowNode(workflow_id=wf.id, node_id="s1", type="start", config="{}")
            n2 = WorkflowNode(workflow_id=wf.id, node_id="m1", type="message",
                              config=json.dumps({"text": "Respuesta integración"}))
            n3 = WorkflowNode(workflow_id=wf.id, node_id="e1", type="end", config="{}")
            db.add_all([n1, n2, n3])

            t1 = WorkflowTransition(workflow_id=wf.id, from_node_id="s1", to_node_id="m1")
            t2 = WorkflowTransition(workflow_id=wf.id, from_node_id="m1", to_node_id="e1")
            db.add_all([t1, t2])
            db.commit()

        # Integración Telegram
        secret = secrets.token_urlsafe(32)
        integration = TelegramIntegration(
            bot_id=bot.id,
            telegram_bot_id="999888777",
            telegram_username=f"int_bot_{uniq}",
            encrypted_token=encrypt_api_key("123:FAKE_INTEGRATION_TOKEN"),
            webhook_secret=secret,
            webhook_url=f"http://localhost:8000/webhooks/telegram/{secret}",
            status="connected",
            is_active=True,
        )
        db.add(integration); db.commit(); db.refresh(integration)

        return {
            "user_id": user.id,
            "bot_id": bot.id,
            "integration_id": integration.id,
            "secret": secret,
            "chat_id": 50000 + (integration.id % 1000),
        }
    finally:
        db.close()


def _cleanup(env):
    """Borra todo lo del test."""
    db = SessionLocal()
    try:
        db.query(TelegramUpdate).filter(
            TelegramUpdate.integration_id == env["integration_id"]
        ).delete()
        db.query(Conversation).filter(Conversation.bot_id == env["bot_id"]).delete()
        db.query(PublicSession).filter(PublicSession.bot_id == env["bot_id"]).delete()
        db.query(TelegramIntegration).filter(TelegramIntegration.id == env["integration_id"]).delete()

        wf_ids = [w.id for w in db.query(Workflow).filter(Workflow.bot_id == env["bot_id"]).all()]
        if wf_ids:
            db.query(WorkflowNode).filter(WorkflowNode.workflow_id.in_(wf_ids)).delete(synchronize_session=False)
            db.query(WorkflowTransition).filter(WorkflowTransition.workflow_id.in_(wf_ids)).delete(synchronize_session=False)
        db.query(Workflow).filter(Workflow.bot_id == env["bot_id"]).delete()

        db.query(Bot).filter(Bot.id == env["bot_id"]).delete()
        db.query(User).filter(User.id == env["user_id"]).delete()
        db.commit()
    finally:
        db.close()


def _post_update(env, update_id, chat_id, text="Hola"):
    """Envía un Update al webhook."""
    return client.post(
        f"/webhooks/telegram/{env['secret']}",
        headers={"X-Telegram-Bot-Api-Secret-Token": env["secret"]},
        json={
            "update_id": update_id,
            "message": {
                "message_id": update_id + 1000,
                "date": 1726934400,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": chat_id, "is_bot": False, "first_name": "Tester"},
                "text": text,
            },
        },
    )


# ============================================================
# TESTS DE INTEGRACIÓN
# ============================================================

def test_e2e_flujo_completo_ok():
    """Flujo completo: mensaje → sesión + workflow + respuesta + analytics."""
    env = _make_env()
    try:
        with patch("app.channels.telegram.client.requests.post",
                   return_value=_mock_telegram_send_ok()) as mock_post:
            r = _post_update(env, 100, env["chat_id"], text="Hola mundo")

        # 1. Respuesta 200 processed
        assert r.status_code == 200
        assert r.json()["status"] == "processed"

        # 2. Sesión creada con channel=telegram + external_id=chat_id
        db = SessionLocal()
        try:
            sess = db.query(PublicSession).filter(
                PublicSession.bot_id == env["bot_id"],
                PublicSession.channel == "telegram",
                PublicSession.external_id == str(env["chat_id"]),
            ).first()
            assert sess is not None
            assert sess.status == "active"

            # 3. Conversation analytics con channel=telegram
            conv = db.query(Conversation).filter(
                Conversation.bot_id == env["bot_id"],
                Conversation.channel == "telegram",
            ).first()
            assert conv is not None
            assert conv.question == "Hola mundo"
            assert conv.answer is not None
            assert conv.session_id == sess.public_id

            # 4. Update registrado (idempotencia)
            upd = db.query(TelegramUpdate).filter(
                TelegramUpdate.integration_id == env["integration_id"],
                TelegramUpdate.update_id == 100,
            ).first()
            assert upd is not None
        finally:
            db.close()

        # 5. Respuesta enviada a Telegram (mock_post llamado)
        assert mock_post.called
        payload = mock_post.call_args.kwargs.get("json", {})
        assert payload["chat_id"] == env["chat_id"]
    finally:
        _cleanup(env)


def test_e2e_multi_turno_mismo_chat():
    """2 mensajes en el mismo chat → misma sesión, 2 Conversations."""
    env = _make_env()
    try:
        with patch("app.channels.telegram.client.requests.post",
                   return_value=_mock_telegram_send_ok()):
            r1 = _post_update(env, 200, env["chat_id"], text="Primer mensaje")
            r2 = _post_update(env, 201, env["chat_id"], text="Segundo mensaje")

        assert r1.json()["status"] == "processed"
        assert r2.json()["status"] == "processed"

        db = SessionLocal()
        try:
            sessions = db.query(PublicSession).filter(
                PublicSession.bot_id == env["bot_id"],
                PublicSession.channel == "telegram",
            ).all()
            assert len(sessions) == 1

            convs = db.query(Conversation).filter(
                Conversation.bot_id == env["bot_id"],
                Conversation.channel == "telegram",
            ).all()
            assert len(convs) == 2
            questions = {c.question for c in convs}
            assert questions == {"Primer mensaje", "Segundo mensaje"}
        finally:
            db.close()
    finally:
        _cleanup(env)


def test_e2e_multi_turno_chats_distintos():
    """Mismo bot, chats distintos → 2 sesiones, 2 Conversations."""
    env = _make_env()
    try:
        with patch("app.channels.telegram.client.requests.post",
                   return_value=_mock_telegram_send_ok()):
            _post_update(env, 300, env["chat_id"], text="Chat A")
            _post_update(env, 301, env["chat_id"] + 1, text="Chat B")

        db = SessionLocal()
        try:
            sessions = db.query(PublicSession).filter(
                PublicSession.bot_id == env["bot_id"],
                PublicSession.channel == "telegram",
            ).all()
            assert len(sessions) == 2

            external_ids = {s.external_id for s in sessions}
            assert str(env["chat_id"]) in external_ids
            assert str(env["chat_id"] + 1) in external_ids
        finally:
            db.close()
    finally:
        _cleanup(env)


def test_e2e_idempotencia_no_duplica_sesion():
    """Reenviar mismo update_id → no duplica sesión ni Conversation."""
    env = _make_env()
    try:
        with patch("app.channels.telegram.client.requests.post",
                   return_value=_mock_telegram_send_ok()):
            r1 = _post_update(env, 400, env["chat_id"], text="Hola")
            r2 = _post_update(env, 400, env["chat_id"], text="Hola repetido")

        assert r1.json()["status"] == "processed"
        assert r2.json()["ignored"] == "duplicate"

        db = SessionLocal()
        try:
            sessions = db.query(PublicSession).filter(
                PublicSession.bot_id == env["bot_id"],
                PublicSession.channel == "telegram",
            ).count()
            assert sessions == 1

            convs = db.query(Conversation).filter(
                Conversation.bot_id == env["bot_id"],
                Conversation.channel == "telegram",
            ).count()
            assert convs == 1
        finally:
            db.close()
    finally:
        _cleanup(env)


def test_e2e_bot_no_publicado_fallback():
    """Bot no publicado → fallback al usuario + NO Conversation."""
    env = _make_env(bot_published=False)
    try:
        with patch("app.channels.telegram.client.requests.post",
                   return_value=_mock_telegram_send_ok()) as mock_post:
            r = _post_update(env, 500, env["chat_id"])

        assert r.status_code == 200
        assert r.json()["status"] == "bot_not_published"

        # Se envió fallback
        assert mock_post.called

        # NO hay Conversation
        db = SessionLocal()
        try:
            convs = db.query(Conversation).filter(
                Conversation.bot_id == env["bot_id"],
            ).count()
            assert convs == 0
        finally:
            db.close()
    finally:
        _cleanup(env)


def test_e2e_sin_workflow_fallback():
    """Bot sin workflow activo → fallback + NO Conversation."""
    env = _make_env(with_workflow=False)
    try:
        with patch("app.channels.telegram.client.requests.post",
                   return_value=_mock_telegram_send_ok()) as mock_post:
            r = _post_update(env, 600, env["chat_id"])

        assert r.status_code == 200
        assert r.json()["status"] == "no_workflow"
        assert mock_post.called

        db = SessionLocal()
        try:
            convs = db.query(Conversation).filter(
                Conversation.bot_id == env["bot_id"],
            ).count()
            assert convs == 0
        finally:
            db.close()
    finally:
        _cleanup(env)


def test_e2e_multitenancy_mismo_chat_dos_bots():
    """Mismo chat_id en 2 bots → 2 sesiones independientes."""
    env_a = _make_env()
    env_b = _make_env()
    try:
        chat = 99999
        with patch("app.channels.telegram.client.requests.post",
                   return_value=_mock_telegram_send_ok()):
            _post_update(env_a, 700, chat, text="Bot A")
            _post_update(env_b, 700, chat, text="Bot B")

        db = SessionLocal()
        try:
            sess_a = db.query(PublicSession).filter(
                PublicSession.bot_id == env_a["bot_id"],
                PublicSession.channel == "telegram",
            ).count()
            sess_b = db.query(PublicSession).filter(
                PublicSession.bot_id == env_b["bot_id"],
                PublicSession.channel == "telegram",
            ).count()
            assert sess_a == 1
            assert sess_b == 1

            conv_a = db.query(Conversation).filter(
                Conversation.bot_id == env_a["bot_id"],
            ).first()
            conv_b = db.query(Conversation).filter(
                Conversation.bot_id == env_b["bot_id"],
            ).first()
            assert conv_a.question == "Bot A"
            assert conv_b.question == "Bot B"
        finally:
            db.close()
    finally:
        _cleanup(env_a)
        _cleanup(env_b)


def test_e2e_sesion_expirada_recrea():
    """Sesión Telegram expirada → se crea una nueva."""
    from datetime import datetime, timezone, timedelta

    env = _make_env()
    try:
        # 1. Primer mensaje → crea sesión
        with patch("app.channels.telegram.client.requests.post",
                   return_value=_mock_telegram_send_ok()):
            _post_update(env, 800, env["chat_id"], text="Antes de expirar")

        # 2. Forzar sesión como expirada
        db = SessionLocal()
        try:
            sess = db.query(PublicSession).filter(
                PublicSession.bot_id == env["bot_id"],
                PublicSession.channel == "telegram",
                PublicSession.external_id == str(env["chat_id"]),
            ).first()
            old_id = sess.id
            sess.expires_at = datetime.now(timezone.utc) - timedelta(hours=2)
            db.commit()
        finally:
            db.close()

        # 3. Segundo mensaje → nueva sesión
        with patch("app.channels.telegram.client.requests.post",
                   return_value=_mock_telegram_send_ok()):
            r = _post_update(env, 801, env["chat_id"], text="Después de expirar")

        assert r.json()["status"] == "processed"

        db = SessionLocal()
        try:
            # La vieja debe estar expirada
            old = db.query(PublicSession).filter(PublicSession.id == old_id).first()
            assert old.status == "expired"

            # Debe haber una nueva activa
            new = db.query(PublicSession).filter(
                PublicSession.bot_id == env["bot_id"],
                PublicSession.channel == "telegram",
                PublicSession.external_id == str(env["chat_id"]),
                PublicSession.status == "active",
            ).first()
            assert new is not None
            assert new.id != old_id
        finally:
            db.close()
    finally:
        _cleanup(env)


def test_e2e_update_no_texto_no_crea_nada():
    """Update sin texto → sin sesión, sin Conversation, sin envío."""
    env = _make_env()
    try:
        # Update sin texto
        with patch("app.channels.telegram.client.requests.post",
                   return_value=_mock_telegram_send_ok()) as mock_post:
            r = client.post(
                f"/webhooks/telegram/{env['secret']}",
                headers={"X-Telegram-Bot-Api-Secret-Token": env["secret"]},
                json={
                    "update_id": 900,
                    "message": {
                        "message_id": 1900,
                        "date": 1726934400,
                        "chat": {"id": env["chat_id"], "type": "private"},
                        "from": {"id": env["chat_id"], "is_bot": False},
                        # sin text
                    },
                },
            )

        assert r.status_code == 200
        assert r.json()["ignored"] == "not_processable"

        # No se envió nada a Telegram
        assert not mock_post.called

        # No hay sesión ni Conversation
        db = SessionLocal()
        try:
            assert db.query(PublicSession).filter(
                PublicSession.bot_id == env["bot_id"],
            ).count() == 0
            assert db.query(Conversation).filter(
                Conversation.bot_id == env["bot_id"],
            ).count() == 0
        finally:
            db.close()
    finally:
        _cleanup(env)


def test_e2e_workflow_falla_no_rompe_webhook():
    """Si el WorkflowEngine falla → fallback enviado + 200 OK."""
    env = _make_env()
    try:
        # Forzar que el workflow falle eliminando el nodo END en tiempo de ejecución
        # Alternativa: mock del engine para que lance excepción
        with patch("app.routers.telegram_webhook.WorkflowEngine") as mock_engine:
            from app.core.workflows.errors import WorkflowExecutionError
            mock_engine.return_value.run.side_effect = WorkflowExecutionError("fallo simulado")

            with patch("app.channels.telegram.client.requests.post",
                       return_value=_mock_telegram_send_ok()) as mock_post:
                r = _post_update(env, 1000, env["chat_id"], text="Hola")

        # 200 OK siempre
        assert r.status_code == 200
        assert r.json()["status"] == "processed"

        # Se envió el fallback
        assert mock_post.called
    finally:
        _cleanup(env)
