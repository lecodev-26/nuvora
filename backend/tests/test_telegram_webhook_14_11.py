"""
Tests - Subfase 14.11.10 (Webhook Telegram)
=============================================
Suite formal de tests del webhook público de Telegram.

BLOQUES:
    A. Seguridad del webhook (headers + secret)
    B. Idempotencia (update_id)
    C. Filtrado de updates no procesables
    D. Multitenancy
    E. Estados del bot (no publicado, sin workflow)
    F. Analytics (channel=telegram)

PATRÓN:
    Mismo que test_e2e_api_14_10.py: TestClient + BD local
    + helpers con _unique() + cleanup al final de cada test.
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


def _mock_send_message():
    """Mock de requests.post para que sendMessage devuelva ok."""
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {
        "ok": True,
        "result": {"message_id": 1000, "chat": {"id": 555}, "text": "respuesta"},
    }
    return mock


def _make_telegram_env(bot_published=True, with_workflow=True, integration_status="connected"):
    """
    Crea usuario + bot + (opcional) workflow + integración Telegram.

    Devuelve dict con:
        user_id, bot_id, integration_id, secret
    """
    db = SessionLocal()
    try:
        uniq = _unique("tg")

        # Usuario
        user = User(
            email=f"wh_{uniq}@nuvora.local",
            hashed_password=get_password_hash("test123"),
            is_active=1,
        )
        db.add(user); db.commit(); db.refresh(user)

        # Bot
        bot = Bot(
            name=f"WH Bot {uniq}",
            user_id=user.id,
            is_published=bot_published,
            public_id=f"wh-{uniq}",
        )
        db.add(bot); db.commit(); db.refresh(bot)

        # Workflow
        if with_workflow:
            wf = Workflow(
                bot_id=bot.id,
                name=f"WF {uniq}",
                status="active",
                entry_node_id="s1",
            )
            db.add(wf); db.commit(); db.refresh(wf)

            n1 = WorkflowNode(workflow_id=wf.id, node_id="s1", type="start", config="{}")
            n2 = WorkflowNode(workflow_id=wf.id, node_id="m1", type="message",
                              config=json.dumps({"text": "Respuesta Telegram"}))
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
            telegram_username=f"bot_{uniq}",
            encrypted_token=encrypt_api_key("123:FAKE_TOKEN"),
            webhook_secret=secret,
            webhook_url=f"http://localhost:8000/webhooks/telegram/{secret}",
            status=integration_status,
            is_active=(integration_status == "connected"),
        )
        db.add(integration); db.commit(); db.refresh(integration)

        return {
            "user_id": user.id,
            "bot_id": bot.id,
            "integration_id": integration.id,
            "secret": secret,
        }
    finally:
        db.close()


def _cleanup_env(bot_id, integration_id):
    """Borra todo lo creado para un test."""
    db = SessionLocal()
    try:
        db.query(TelegramUpdate).filter(TelegramUpdate.integration_id == integration_id).delete()
        db.query(Conversation).filter(Conversation.bot_id == bot_id).delete()
        db.query(PublicSession).filter(PublicSession.bot_id == bot_id).delete()
        db.query(TelegramIntegration).filter(TelegramIntegration.id == integration_id).delete()
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
        db.query(Bot).filter(Bot.id == bot_id).delete()
        db.commit()
    finally:
        db.close()


def _msg_update(update_id, chat_id=555, text="Hola", chat_type="private", is_bot=False):
    """Construye un update de mensaje estándar."""
    return {
        "update_id": update_id,
        "message": {
            "message_id": update_id + 1000,
            "date": 1726934400,
            "chat": {"id": chat_id, "type": chat_type},
            "from": {"id": chat_id, "is_bot": is_bot, "first_name": "Tester"},
            "text": text,
        },
    }


# ============================================================
# BLOQUE A: SEGURIDAD
# ============================================================

def test_webhook_no_header_returns_403():
    """Sin header X-Telegram-Bot-Api-Secret-Token → 403."""
    env = _make_telegram_env()
    try:
        r = client.post(f"/webhooks/telegram/{env['secret']}", json=_msg_update(1))
        assert r.status_code == 403
    finally:
        _cleanup_env(env["bot_id"], env["integration_id"])


def test_webhook_wrong_header_returns_403():
    """Header distinto del secret de URL → 403."""
    env = _make_telegram_env()
    try:
        r = client.post(
            f"/webhooks/telegram/{env['secret']}",
            headers={"X-Telegram-Bot-Api-Secret-Token": "OTRO_SECRET"},
            json=_msg_update(2),
        )
        assert r.status_code == 403
    finally:
        _cleanup_env(env["bot_id"], env["integration_id"])


def test_webhook_unknown_secret_returns_404():
    """Secret con formato válido pero no existe en BD → 404."""
    env = _make_telegram_env()
    try:
        fake = secrets.token_urlsafe(32)
        r = client.post(
            f"/webhooks/telegram/{fake}",
            headers={"X-Telegram-Bot-Api-Secret-Token": fake},
            json=_msg_update(3),
        )
        assert r.status_code == 404
    finally:
        _cleanup_env(env["bot_id"], env["integration_id"])


def test_webhook_inactive_integration_returns_404():
    """Integración inactiva → 404."""
    env = _make_telegram_env(integration_status="disconnected")
    try:
        r = client.post(
            f"/webhooks/telegram/{env['secret']}",
            headers={"X-Telegram-Bot-Api-Secret-Token": env["secret"]},
            json=_msg_update(4),
        )
        assert r.status_code == 404
    finally:
        _cleanup_env(env["bot_id"], env["integration_id"])


def test_webhook_error_status_integration_returns_404():
    """Integración en status=error → 404."""
    env = _make_telegram_env(integration_status="error")
    try:
        r = client.post(
            f"/webhooks/telegram/{env['secret']}",
            headers={"X-Telegram-Bot-Api-Secret-Token": env["secret"]},
            json=_msg_update(5),
        )
        assert r.status_code == 404
    finally:
        _cleanup_env(env["bot_id"], env["integration_id"])


# ============================================================
# BLOQUE B: IDEMPOTENCIA
# ============================================================

def test_webhook_duplicate_update_id_processed_once():
    """Mismo update_id dos veces → solo se procesa la primera."""
    env = _make_telegram_env()
    try:
        with patch("app.channels.telegram.client.requests.post", return_value=_mock_send_message()):
            r1 = client.post(
                f"/webhooks/telegram/{env['secret']}",
                headers={"X-Telegram-Bot-Api-Secret-Token": env["secret"]},
                json=_msg_update(100),
            )
            r2 = client.post(
                f"/webhooks/telegram/{env['secret']}",
                headers={"X-Telegram-Bot-Api-Secret-Token": env["secret"]},
                json=_msg_update(100),
            )

        assert r1.status_code == 200
        assert r1.json()["status"] == "processed"
        assert r2.status_code == 200
        assert r2.json()["ignored"] == "duplicate"

        # Solo debe haber 1 telegram_update
        db = SessionLocal()
        try:
            cnt = db.query(TelegramUpdate).filter(
                TelegramUpdate.integration_id == env["integration_id"]
            ).count()
            assert cnt == 1
        finally:
            db.close()
    finally:
        _cleanup_env(env["bot_id"], env["integration_id"])


def test_webhook_different_update_ids_both_processed():
    """Distintos update_id → ambos se procesan."""
    env = _make_telegram_env()
    try:
        with patch("app.channels.telegram.client.requests.post", return_value=_mock_send_message()):
            r1 = client.post(
                f"/webhooks/telegram/{env['secret']}",
                headers={"X-Telegram-Bot-Api-Secret-Token": env["secret"]},
                json=_msg_update(200),
            )
            r2 = client.post(
                f"/webhooks/telegram/{env['secret']}",
                headers={"X-Telegram-Bot-Api-Secret-Token": env["secret"]},
                json=_msg_update(201),
            )
        assert r1.json()["status"] == "processed"
        assert r2.json()["status"] == "processed"

        db = SessionLocal()
        try:
            cnt = db.query(TelegramUpdate).filter(
                TelegramUpdate.integration_id == env["integration_id"]
            ).count()
            assert cnt == 2
        finally:
            db.close()
    finally:
        _cleanup_env(env["bot_id"], env["integration_id"])


def test_webhook_same_update_id_different_integrations_both_processed():
    """Mismo update_id en 2 integraciones distintas → ambas procesan."""
    env1 = _make_telegram_env()
    env2 = _make_telegram_env()
    try:
        with patch("app.channels.telegram.client.requests.post", return_value=_mock_send_message()):
            r1 = client.post(
                f"/webhooks/telegram/{env1['secret']}",
                headers={"X-Telegram-Bot-Api-Secret-Token": env1["secret"]},
                json=_msg_update(300),
            )
            r2 = client.post(
                f"/webhooks/telegram/{env2['secret']}",
                headers={"X-Telegram-Bot-Api-Secret-Token": env2["secret"]},
                json=_msg_update(300),
            )
        assert r1.json()["status"] == "processed"
        assert r2.json()["status"] == "processed"
    finally:
        _cleanup_env(env1["bot_id"], env1["integration_id"])
        _cleanup_env(env2["bot_id"], env2["integration_id"])


# ============================================================
# BLOQUE C: FILTRADO DE UPDATES
# ============================================================

def test_webhook_no_message_ignored():
    """Update sin message → ignored."""
    env = _make_telegram_env()
    try:
        r = client.post(
            f"/webhooks/telegram/{env['secret']}",
            headers={"X-Telegram-Bot-Api-Secret-Token": env["secret"]},
            json={"update_id": 400},
        )
        assert r.status_code == 200
        assert r.json()["ignored"] == "not_processable"
    finally:
        _cleanup_env(env["bot_id"], env["integration_id"])


def test_webhook_group_message_ignored():
    """Mensaje de grupo → ignored."""
    env = _make_telegram_env()
    try:
        r = client.post(
            f"/webhooks/telegram/{env['secret']}",
            headers={"X-Telegram-Bot-Api-Secret-Token": env["secret"]},
            json=_msg_update(401, chat_id=-100, chat_type="group"),
        )
        assert r.status_code == 200
        assert r.json()["ignored"] == "not_processable"
    finally:
        _cleanup_env(env["bot_id"], env["integration_id"])


def test_webhook_no_text_ignored():
    """Mensaje sin texto → ignored."""
    env = _make_telegram_env()
    try:
        raw = {
            "update_id": 402,
            "message": {
                "message_id": 1402,
                "date": 1726934400,
                "chat": {"id": 555, "type": "private"},
                "from": {"id": 555, "is_bot": False},
                # sin text
            },
        }
        r = client.post(
            f"/webhooks/telegram/{env['secret']}",
            headers={"X-Telegram-Bot-Api-Secret-Token": env["secret"]},
            json=raw,
        )
        assert r.status_code == 200
        assert r.json()["ignored"] == "not_processable"
    finally:
        _cleanup_env(env["bot_id"], env["integration_id"])


def test_webhook_bot_message_ignored():
    """Mensaje de otro bot → ignored."""
    env = _make_telegram_env()
    try:
        r = client.post(
            f"/webhooks/telegram/{env['secret']}",
            headers={"X-Telegram-Bot-Api-Secret-Token": env["secret"]},
            json=_msg_update(403, is_bot=True),
        )
        assert r.status_code == 200
        assert r.json()["ignored"] == "not_processable"
    finally:
        _cleanup_env(env["bot_id"], env["integration_id"])


def test_webhook_invalid_json_ignored():
    """Body no-JSON → ignored sin error."""
    env = _make_telegram_env()
    try:
        r = client.post(
            f"/webhooks/telegram/{env['secret']}",
            headers={
                "X-Telegram-Bot-Api-Secret-Token": env["secret"],
                "Content-Type": "application/json",
            },
            content=b"no soy json",
        )
        assert r.status_code == 200
        # La respuesta debe indicar que se ignoró
        body = r.json()
        assert body.get("ignored") in ("invalid_json", "invalid_schema")
    finally:
        _cleanup_env(env["bot_id"], env["integration_id"])


# ============================================================
# BLOQUE D: MULTITENANCY
# ============================================================

def test_webhook_bot_a_does_not_process_bot_b():
    """Secret de bot A → solo procesa en el bot A."""
    env_a = _make_telegram_env()
    env_b = _make_telegram_env()
    try:
        with patch("app.channels.telegram.client.requests.post", return_value=_mock_send_message()):
            r = client.post(
                f"/webhooks/telegram/{env_a['secret']}",
                headers={"X-Telegram-Bot-Api-Secret-Token": env_a["secret"]},
                json=_msg_update(500, chat_id=600),
            )
        assert r.status_code == 200
        assert r.json()["status"] == "processed"

        # Verificar: sesión en bot A, NO en bot B
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
            assert sess_b == 0
        finally:
            db.close()
    finally:
        _cleanup_env(env_a["bot_id"], env_a["integration_id"])
        _cleanup_env(env_b["bot_id"], env_b["integration_id"])


def test_webhook_sessions_isolated_by_chat_id():
    """Distintos chat_id → distintas sesiones."""
    env = _make_telegram_env()
    try:
        with patch("app.channels.telegram.client.requests.post", return_value=_mock_send_message()):
            client.post(
                f"/webhooks/telegram/{env['secret']}",
                headers={"X-Telegram-Bot-Api-Secret-Token": env["secret"]},
                json=_msg_update(600, chat_id=700),
            )
            client.post(
                f"/webhooks/telegram/{env['secret']}",
                headers={"X-Telegram-Bot-Api-Secret-Token": env["secret"]},
                json=_msg_update(601, chat_id=800),
            )

        db = SessionLocal()
        try:
            sessions = db.query(PublicSession).filter(
                PublicSession.bot_id == env["bot_id"],
                PublicSession.channel == "telegram",
            ).all()
            chat_ids = {s.external_id for s in sessions}
            assert chat_ids == {"700", "800"}
        finally:
            db.close()
    finally:
        _cleanup_env(env["bot_id"], env["integration_id"])


# ============================================================
# BLOQUE E: ESTADOS DEL BOT
# ============================================================

def test_webhook_bot_not_published_returns_fallback():
    """Bot no publicado → fallback al usuario, sin ejecutar workflow."""
    env = _make_telegram_env(bot_published=False)
    try:
        with patch("app.channels.telegram.client.requests.post", return_value=_mock_send_message()) as mock_post:
            r = client.post(
                f"/webhooks/telegram/{env['secret']}",
                headers={"X-Telegram-Bot-Api-Secret-Token": env["secret"]},
                json=_msg_update(700),
            )
        assert r.status_code == 200
        assert r.json()["status"] == "bot_not_published"

        # Verificar que se envió el fallback
        payload = mock_post.call_args.kwargs.get("json", {})
        assert "no esta disponible" in payload.get("text", "").lower() or \
               "no está disponible" in payload.get("text", "").lower()
    finally:
        _cleanup_env(env["bot_id"], env["integration_id"])


def test_webhook_no_workflow_returns_fallback():
    """Bot sin workflow activo → fallback al usuario."""
    env = _make_telegram_env(with_workflow=False)
    try:
        with patch("app.channels.telegram.client.requests.post", return_value=_mock_send_message()) as mock_post:
            r = client.post(
                f"/webhooks/telegram/{env['secret']}",
                headers={"X-Telegram-Bot-Api-Secret-Token": env["secret"]},
                json=_msg_update(701),
            )
        assert r.status_code == 200
        assert r.json()["status"] == "no_workflow"

        payload = mock_post.call_args.kwargs.get("json", {})
        assert "no esta configurado" in payload.get("text", "").lower() or \
               "no está configurado" in payload.get("text", "").lower()
    finally:
        _cleanup_env(env["bot_id"], env["integration_id"])


# ============================================================
# BLOQUE F: ANALYTICS
# ============================================================

def test_webhook_creates_conversation_with_channel_telegram():
    """Cada mensaje procesado → Conversation con channel=telegram."""
    env = _make_telegram_env()
    try:
        with patch("app.channels.telegram.client.requests.post", return_value=_mock_send_message()):
            r = client.post(
                f"/webhooks/telegram/{env['secret']}",
                headers={"X-Telegram-Bot-Api-Secret-Token": env["secret"]},
                json=_msg_update(800, chat_id=900, text="Pregunta Telegram"),
            )
        assert r.json()["status"] == "processed"

        db = SessionLocal()
        try:
            conv = db.query(Conversation).filter(
                Conversation.bot_id == env["bot_id"],
                Conversation.channel == "telegram",
            ).first()
            assert conv is not None
            assert conv.question == "Pregunta Telegram"
            assert conv.session_id is not None
        finally:
            db.close()
    finally:
        _cleanup_env(env["bot_id"], env["integration_id"])


def test_webhook_session_has_channel_telegram():
    """La sesión creada tiene channel='telegram' y external_id correcto."""
    env = _make_telegram_env()
    try:
        with patch("app.channels.telegram.client.requests.post", return_value=_mock_send_message()):
            r = client.post(
                f"/webhooks/telegram/{env['secret']}",
                headers={"X-Telegram-Bot-Api-Secret-Token": env["secret"]},
                json=_msg_update(801, chat_id=999),
            )
        assert r.json()["status"] == "processed"

        db = SessionLocal()
        try:
            sess = db.query(PublicSession).filter(
                PublicSession.bot_id == env["bot_id"],
                PublicSession.channel == "telegram",
            ).first()
            assert sess is not None
            assert sess.external_id == "999"
            assert sess.channel == "telegram"
        finally:
            db.close()
    finally:
        _cleanup_env(env["bot_id"], env["integration_id"])


# ============================================================
# BLOQUE G: RATE LIMITING
# ============================================================

def test_webhook_rate_limit_triggers_429():
    """Muchas peticiones → rate limit."""
    env = _make_telegram_env()
    try:
        reset_public_all()
        # El límite es 120 por integración. Enviamos 130 rápidas.
        # Muchas serán idempotentes, pero cuentan igual para rate limit.
        got_429 = False
        with patch("app.channels.telegram.client.requests.post", return_value=_mock_send_message()):
            for i in range(130):
                r = client.post(
                    f"/webhooks/telegram/{env['secret']}",
                    headers={"X-Telegram-Bot-Api-Secret-Token": env["secret"]},
                    json=_msg_update(9000 + i),
                )
                if r.status_code == 429:
                    got_429 = True
                    break
        assert got_429, "Esperaba recibir 429 tras muchas peticiones"
    finally:
        reset_public_all()
        _cleanup_env(env["bot_id"], env["integration_id"])
