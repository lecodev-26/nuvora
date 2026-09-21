"""
Nuvora — Servicio Public Session (Fase 14.9)
==============================================
Gestión de sesiones anónimas de bots publicados.

RESPONSABILIDADES:
    - create_session(bot, db): crea sesión nueva con TTL
    - get_session(session_id, bot, db): recupera + verifica pertenencia + TTL
    - append_message(session, role, content, db): añade mensaje al array
    - get_session_messages(session): lista de mensajes
    - close_session(session, db): cierra sesión
    - expire_old_sessions(db): marca como expiradas las caducadas

FILOSOFÍA:
    - Sesión ANÓNIMA. Sin login, sin email.
    - Solo guarda CONTEXTO mínimo (lista de mensajes user/bot).
    - NO reemplaza a `conversations` (esa es analytics).
    - Expira en 1h por defecto.
    - Máximo 50 mensajes por sesión (protección anti-abuso).

AISLAMIENTO:
    get_session() verifica que session.bot_id == bot.id. Si no,
    devuelve 404 (no revela que la sesión existe para otro bot).
"""

import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.db_models import Bot, PublicSession


# ============================================================
# CONSTANTES
# ============================================================

SESSION_TTL_SECONDS = 3600           # 1 hora
MAX_SESSION_MESSAGES = 50            # límite de mensajes por sesión

STATUS_ACTIVE = "active"
STATUS_EXPIRED = "expired"
STATUS_CLOSED = "closed"


# ============================================================
# HELPERS INTERNOS
# ============================================================

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Convierte a UTC si el datetime es naive."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _load_messages(session: PublicSession) -> list:
    """Lee session_data (JSON TEXT) → list. Fallback []."""
    if not session.session_data:
        return []
    try:
        data = json.loads(session.session_data)
        return data if isinstance(data, list) else []
    except (ValueError, TypeError):
        return []


def _save_messages(session: PublicSession, messages: list, db: Session) -> None:
    """Serializa lista de mensajes → session_data."""
    session.session_data = json.dumps(messages)
    db.commit()


# ============================================================
# CREAR SESIÓN
# ============================================================

def create_session(
    bot: Bot,
    db: Session,
    channel: str = "widget",
    external_id: Optional[str] = None,
) -> PublicSession:
    """
    Crea una nueva sesión anónima para el bot.

    Args:
        bot: el bot al que pertenece la sesión.
        db: sesión SQLAlchemy.
        channel: canal de la sesión ("widget" | "api" | "telegram").
                 Default "widget" para compatibilidad con código existente.
        external_id: identificador externo del usuario en el canal
                     (ej: chat_id de Telegram). None para widget/api.

    - public_id: UUID v4 (identidad técnica de la sesión).
    - bot_id: FK al bot.
    - session_data: "[]" (lista vacía).
    - status: "active".
    - expires_at: now + SESSION_TTL_SECONDS.
    """
    session_public_id = str(uuid.uuid4())
    expires = _now_utc() + timedelta(seconds=SESSION_TTL_SECONDS)

    sess = PublicSession(
        public_id=session_public_id,
        bot_id=bot.id,
        session_data="[]",
        status=STATUS_ACTIVE,
        expires_at=expires,
        channel=channel,
        external_id=external_id,
    )
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return sess


# ============================================================
# OBTENER SESIÓN
# ============================================================

def get_session(
    session_public_id: str,
    bot: Bot,
    db: Session,
) -> PublicSession:
    """
    Recupera una sesión por su public_id, verificando:
        1. Existe.
        2. Pertenece al bot indicado.
        3. No ha expirado (si expiró → la marca y lanza 404).
        4. No está cerrada.

    Lanza HTTPException 404 en cualquier caso inválido
    (para no filtrar información).
    """
    if not session_public_id or not isinstance(session_public_id, str):
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    sess = db.query(PublicSession).filter(
        PublicSession.public_id == session_public_id,
    ).first()

    if not sess:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    # Verificación de pertenencia al bot (aislamiento multi-tenant)
    if sess.bot_id != bot.id:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    # Verificación de estado
    if sess.status == STATUS_CLOSED:
        raise HTTPException(status_code=404, detail="Sesión cerrada")

    # Verificación de TTL
    expires = _ensure_utc(sess.expires_at)
    if expires and _now_utc() > expires:
        sess.status = STATUS_EXPIRED
        db.commit()
        raise HTTPException(status_code=404, detail="Sesión expirada")

    return sess


# ============================================================
# MENSAJES
# ============================================================

def get_session_messages(session: PublicSession) -> list:
    """Devuelve la lista de mensajes (dicts con role/content/ts)."""
    return _load_messages(session)


def append_message(
    session: PublicSession,
    role: str,
    content: str,
    db: Session,
) -> None:
    """
    Añade un mensaje a la sesión.

    Args:
        role: "user" o "bot".
        content: texto del mensaje.

    Raises:
        HTTPException 400: si la sesión superó MAX_SESSION_MESSAGES.
    """
    messages = _load_messages(session)

    if len(messages) >= MAX_SESSION_MESSAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Sesión ha alcanzado el límite de {MAX_SESSION_MESSAGES} mensajes",
        )

    messages.append({
        "role": role,
        "content": content,
        "ts": _now_utc().isoformat(),
    })

    _save_messages(session, messages, db)


def append_user_message(session: PublicSession, content: str, db: Session) -> None:
    """Shortcut para mensaje del usuario."""
    append_message(session, "user", content, db)


def append_bot_message(session: PublicSession, content: str, db: Session) -> None:
    """Shortcut para mensaje del bot."""
    append_message(session, "bot", content, db)


# ============================================================
# CERRAR SESIÓN
# ============================================================

def close_session(session: PublicSession, db: Session) -> None:
    """Marca la sesión como cerrada."""
    session.status = STATUS_CLOSED
    db.commit()


# ============================================================
# LIMPIEZA (opcional, para cron / startup)
# ============================================================

def expire_old_sessions(db: Session, limit: int = 500) -> int:
    """
    Marca como expiradas las sesiones caducadas.

    Devuelve el número de sesiones actualizadas.
    """
    now = _now_utc()
    sessions = db.query(PublicSession).filter(
        PublicSession.status == STATUS_ACTIVE,
        PublicSession.expires_at < now,
    ).limit(limit).all()

    for s in sessions:
        s.status = STATUS_EXPIRED

    if sessions:
        db.commit()

    return len(sessions)


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "create_session",
    "get_session",
    "get_session_messages",
    "append_message",
    "append_user_message",
    "append_bot_message",
    "close_session",
    "expire_old_sessions",
    "SESSION_TTL_SECONDS",
    "MAX_SESSION_MESSAGES",
    "STATUS_ACTIVE",
    "STATUS_EXPIRED",
    "STATUS_CLOSED",
]
