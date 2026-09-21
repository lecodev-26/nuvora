"""
Tests - Subfase 14.11.12 (Session helper multicanal)
======================================================
Tests formales de get_or_create_by_external() en public_session.py.

Cubre:
    - Creación de sesión nueva
    - Reutilización de sesión existente
    - Expiración y recreación
    - Aislamiento por channel, external_id, bot_id
    - Fallbacks cuando channel/external_id son None
    - Coexistencia con sesiones widget (default)

PATRÓN:
    BD SQLite local + helpers con _unique() + cleanup al final.
"""

import sys
import os
import time
import json
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.config import SessionLocal
from app.models.db_models import Bot, User, PublicSession
from app.services.auth import get_password_hash
from app.services.public_session import (
    get_or_create_by_external,
    create_session,
    STATUS_ACTIVE,
    STATUS_EXPIRED,
)


# ============================================================
# HELPERS
# ============================================================

def _unique(suffix):
    return f"{suffix}_{int(time.time() * 1000000)}"


def _make_bot():
    """Crea usuario + bot de test. Devuelve (user_id, bot_id)."""
    db = SessionLocal()
    try:
        uniq = _unique("sess")
        user = User(
            email=f"sess_{uniq}@nuvora.local",
            hashed_password=get_password_hash("test"),
            is_active=1,
        )
        db.add(user); db.commit(); db.refresh(user)

        bot = Bot(
            name=f"Sess Bot {uniq}",
            user_id=user.id,
            public_id=f"sess-{uniq}",
        )
        db.add(bot); db.commit(); db.refresh(bot)

        return user.id, bot.id
    finally:
        db.close()


def _get_bot(bot_id):
    """Recupera el bot en una sesión fresca."""
    db = SessionLocal()
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    db.close()
    return bot


def _count_sessions(bot_id, channel=None, external_id=None, status=None):
    """Cuenta sesiones con filtros opcionales."""
    db = SessionLocal()
    try:
        q = db.query(PublicSession).filter(PublicSession.bot_id == bot_id)
        if channel is not None:
            q = q.filter(PublicSession.channel == channel)
        if external_id is not None:
            q = q.filter(PublicSession.external_id == external_id)
        if status is not None:
            q = q.filter(PublicSession.status == status)
        return q.count()
    finally:
        db.close()


def _cleanup(user_id, bot_id):
    db = SessionLocal()
    try:
        db.query(PublicSession).filter(PublicSession.bot_id == bot_id).delete()
        db.query(Bot).filter(Bot.id == bot_id).delete()
        db.query(User).filter(User.id == user_id).delete()
        db.commit()
    finally:
        db.close()


# ============================================================
# TESTS
# ============================================================

def test_creates_new_session_when_not_exists():
    """Primera llamada → crea sesión nueva con channel + external_id."""
    user_id, bot_id = _make_bot()
    try:
        db = SessionLocal()
        try:
            bot = db.query(Bot).filter(Bot.id == bot_id).first()
            sess = get_or_create_by_external(
                bot=bot, channel="telegram", external_id="chat_123", db=db,
            )
            assert sess.id is not None
            assert sess.channel == "telegram"
            assert sess.external_id == "chat_123"
            assert sess.bot_id == bot.id
            assert sess.status == STATUS_ACTIVE
        finally:
            db.close()
    finally:
        _cleanup(user_id, bot_id)


def test_returns_same_session_when_exists_active():
    """Segunda llamada con mismos parámetros → misma sesión."""
    user_id, bot_id = _make_bot()
    try:
        db = SessionLocal()
        try:
            bot = db.query(Bot).filter(Bot.id == bot_id).first()
            sess1 = get_or_create_by_external(
                bot=bot, channel="telegram", external_id="chat_456", db=db,
            )
            sess2 = get_or_create_by_external(
                bot=bot, channel="telegram", external_id="chat_456", db=db,
            )
            assert sess1.id == sess2.id
            assert sess1.public_id == sess2.public_id
        finally:
            db.close()
    finally:
        _cleanup(user_id, bot_id)


def test_creates_new_session_when_expired():
    """Sesión expirada → se marca expired + se crea nueva."""
    user_id, bot_id = _make_bot()
    try:
        db = SessionLocal()
        try:
            bot = db.query(Bot).filter(Bot.id == bot_id).first()

            # Crear sesión manualmente expirada
            expired = PublicSession(
                public_id="expired_test_123",
                bot_id=bot.id,
                session_data="[]",
                status=STATUS_ACTIVE,
                expires_at=datetime.now(timezone.utc) - timedelta(hours=2),
                channel="telegram",
                external_id="chat_exp",
            )
            db.add(expired); db.commit(); db.refresh(expired)
            expired_id = expired.id

            # Llamar al helper
            sess_new = get_or_create_by_external(
                bot=bot, channel="telegram", external_id="chat_exp", db=db,
            )

            # Debe ser una sesión nueva
            assert sess_new.id != expired_id
            assert sess_new.status == STATUS_ACTIVE

            # La vieja debe estar marcada como expirada
            db.refresh(expired)
            assert expired.status == STATUS_EXPIRED
        finally:
            db.close()
    finally:
        _cleanup(user_id, bot_id)


def test_isolated_by_channel():
    """Mismo external_id, distinto channel → sesiones distintas."""
    user_id, bot_id = _make_bot()
    try:
        db = SessionLocal()
        try:
            bot = db.query(Bot).filter(Bot.id == bot_id).first()
            sess_tg = get_or_create_by_external(
                bot=bot, channel="telegram", external_id="shared_id", db=db,
            )
            sess_wa = get_or_create_by_external(
                bot=bot, channel="whatsapp", external_id="shared_id", db=db,
            )
            assert sess_tg.id != sess_wa.id
            assert sess_tg.channel == "telegram"
            assert sess_wa.channel == "whatsapp"
        finally:
            db.close()

        # Debe haber 2 sesiones activas
        assert _count_sessions(bot_id, status=STATUS_ACTIVE) == 2
    finally:
        _cleanup(user_id, bot_id)


def test_isolated_by_external_id():
    """Mismo channel, distinto external_id → sesiones distintas."""
    user_id, bot_id = _make_bot()
    try:
        db = SessionLocal()
        try:
            bot = db.query(Bot).filter(Bot.id == bot_id).first()
            sess1 = get_or_create_by_external(
                bot=bot, channel="telegram", external_id="chat_A", db=db,
            )
            sess2 = get_or_create_by_external(
                bot=bot, channel="telegram", external_id="chat_B", db=db,
            )
            assert sess1.id != sess2.id
            assert sess1.external_id == "chat_A"
            assert sess2.external_id == "chat_B"
        finally:
            db.close()
    finally:
        _cleanup(user_id, bot_id)


def test_isolated_by_bot_id():
    """Mismo channel + external_id, distinto bot → sesiones distintas."""
    user_id_a, bot_id_a = _make_bot()
    user_id_b, bot_id_b = _make_bot()
    try:
        db = SessionLocal()
        try:
            bot_a = db.query(Bot).filter(Bot.id == bot_id_a).first()
            bot_b = db.query(Bot).filter(Bot.id == bot_id_b).first()

            sess_a = get_or_create_by_external(
                bot=bot_a, channel="telegram", external_id="same_chat", db=db,
            )
            sess_b = get_or_create_by_external(
                bot=bot_b, channel="telegram", external_id="same_chat", db=db,
            )
            assert sess_a.id != sess_b.id
            assert sess_a.bot_id == bot_id_a
            assert sess_b.bot_id == bot_id_b
        finally:
            db.close()
    finally:
        _cleanup(user_id_a, bot_id_a)
        _cleanup(user_id_b, bot_id_b)


def test_fallback_when_channel_is_none():
    """channel=None → fallback a 'widget'."""
    user_id, bot_id = _make_bot()
    try:
        db = SessionLocal()
        try:
            bot = db.query(Bot).filter(Bot.id == bot_id).first()
            sess = get_or_create_by_external(
                bot=bot, channel=None, external_id="some_id", db=db,
            )
            assert sess.channel == "widget"
            assert sess.external_id == "some_id"
        finally:
            db.close()
    finally:
        _cleanup(user_id, bot_id)


def test_fallback_when_external_id_is_none():
    """external_id=None → crea sesión sin external_id (como create_session)."""
    user_id, bot_id = _make_bot()
    try:
        db = SessionLocal()
        try:
            bot = db.query(Bot).filter(Bot.id == bot_id).first()
            sess = get_or_create_by_external(
                bot=bot, channel="telegram", external_id=None, db=db,
            )
            assert sess.id is not None
            assert sess.external_id is None
            assert sess.channel == "telegram"
        finally:
            db.close()
    finally:
        _cleanup(user_id, bot_id)


def test_coexists_with_widget_sessions():
    """Sesiones widget (channel default) y Telegram coexisten sin colisión."""
    user_id, bot_id = _make_bot()
    try:
        db = SessionLocal()
        try:
            bot = db.query(Bot).filter(Bot.id == bot_id).first()

            # Sesión widget (default)
            sess_widget = create_session(bot, db)

            # Sesión Telegram
            sess_tg = get_or_create_by_external(
                bot=bot, channel="telegram", external_id="chat_xyz", db=db,
            )

            assert sess_widget.id != sess_tg.id
            assert sess_widget.channel == "widget"
            assert sess_tg.channel == "telegram"
        finally:
            db.close()

        # Dos sesiones activas
        assert _count_sessions(bot_id, status=STATUS_ACTIVE) == 2
    finally:
        _cleanup(user_id, bot_id)


def test_multiple_calls_only_one_active_session():
    """5 llamadas seguidas con mismos parámetros → solo 1 sesión activa."""
    user_id, bot_id = _make_bot()
    try:
        db = SessionLocal()
        try:
            bot = db.query(Bot).filter(Bot.id == bot_id).first()
            ids = set()
            for _ in range(5):
                sess = get_or_create_by_external(
                    bot=bot, channel="telegram", external_id="loop_chat", db=db,
                )
                ids.add(sess.id)

            assert len(ids) == 1
        finally:
            db.close()

        # Solo 1 sesión activa
        assert _count_sessions(
            bot_id, channel="telegram", external_id="loop_chat", status=STATUS_ACTIVE,
        ) == 1
    finally:
        _cleanup(user_id, bot_id)
