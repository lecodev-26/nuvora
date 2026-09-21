"""
Nuvora — API Key Service (Fase 14.10.3)
=========================================
Gestión de API Keys para Nuvora API.

RESPONSABILIDADES:
    - generate_api_key():   genera (full_key, prefix, hash)
    - hash_key():           SHA256 del secret
    - verify_key():         comparación timing-safe
    - create_api_key():     persiste una nueva key
    - list_api_keys():      keys de un bot
    - revoke_api_key():     revoca (is_active=False + revoked_at)
    - resolve_api_key():    Bearer → (api_key, bot) o error
    - touch_last_used():    actualiza last_used_at

SEGURIDAD:
    - secrets.token_urlsafe(32) → 256 bits de entropía (criptográficamente seguro)
    - SHA256 del secret como hash (suficiente para tokens de alta entropía)
    - secrets.compare_digest() para comparación timing-safe
    - La key completa NUNCA se guarda en BD

FORMATO DE KEY:
    nvr_live_<43 chars base64url>
    Ej: nvr_live_AbCdEf1234567890-_xYz...
"""

import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.db_models import ApiKey, Bot
from app.core.api_errors import ApiError, ErrorCode


# ============================================================
# CONSTANTES
# ============================================================

KEY_PREFIX = "nvr_live_"
PREFIX_DISPLAY_LENGTH = 8      # chars visibles del secret (nvr_live_ + 8)
KEY_BYTES = 32                 # 256 bits de entropía
TOUCH_INTERVAL_SECONDS = 60    # throttle para last_used_at


# ============================================================
# GENERACIÓN Y HASH
# ============================================================

def generate_api_key() -> tuple[str, str, str]:
    """
    Genera una nueva API Key.

    Returns:
        (full_key, key_prefix, key_hash)
        - full_key: "nvr_live_XXXXX..." (se muestra UNA VEZ al usuario)
        - key_prefix: primeros chars visibles (para identificar)
        - key_hash: SHA256 del secret (lo que se guarda en BD)

    Ejemplo:
        ('nvr_live_AbCd...', 'nvr_live_AbCdEf12', 'e3b0c442...')
    """
    secret = secrets.token_urlsafe(KEY_BYTES)
    full_key = f"{KEY_PREFIX}{secret}"
    key_prefix = full_key[:len(KEY_PREFIX) + PREFIX_DISPLAY_LENGTH]
    key_hash = hash_key(full_key)
    return full_key, key_prefix, key_hash


def hash_key(full_key: str) -> str:
    """
    SHA256 hexadecimal (64 chars) del full_key.

    No usamos bcrypt/argon2 porque:
        - Los secrets tienen 256 bits de entropía (no adivinables)
        - SHA256 es suficiente para tokens de alta entropía
        - Más rápido → mejor rendimiento en cada request
    """
    return hashlib.sha256(full_key.encode("utf-8")).hexdigest()


def verify_key(provided_key: str, stored_hash: str) -> bool:
    """
    Comparación timing-safe entre el hash de la key proporcionada
    y el hash almacenado.

    Returns:
        True si coinciden.
    """
    if not provided_key or not stored_hash:
        return False
    computed = hash_key(provided_key)
    return secrets.compare_digest(computed, stored_hash)


# ============================================================
# CREAR
# ============================================================

def create_api_key(
    db: Session,
    user_id: int,
    bot_id: int,
    name: str,
) -> tuple[ApiKey, str]:
    """
    Crea una nueva API Key en la BD.

    Args:
        user_id: propietario.
        bot_id: bot al que pertenece la key.
        name: nombre descriptivo ("Mi integración").

    Returns:
        (api_key_obj, full_key)
        - api_key_obj: registro persistido (con key_hash, NO full_key)
        - full_key: la key completa (mostrar UNA VEZ al usuario)

    Raises:
        HTTPException 404: si el bot no existe o no es del user.
    """
    # Verificar que el bot existe y es del usuario
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")

    # Ownership
    if bot.user_id is not None and bot.user_id != user_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para este bot")

    full_key, key_prefix, key_hash = generate_api_key()

    api_key = ApiKey(
        user_id=user_id,
        bot_id=bot_id,
        name=name.strip(),
        key_prefix=key_prefix,
        key_hash=key_hash,
        is_active=True,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return api_key, full_key


# ============================================================
# LISTAR
# ============================================================

def list_api_keys(db: Session, user_id: int, bot_id: int) -> list[ApiKey]:
    """
    Lista las API Keys activas e inactivas de un bot.

    Solo devuelve las keys del usuario propietario del bot.
    """
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")
    if bot.user_id is not None and bot.user_id != user_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para este bot")

    return (
        db.query(ApiKey)
        .filter(ApiKey.user_id == user_id, ApiKey.bot_id == bot_id)
        .order_by(ApiKey.created_at.desc())
        .all()
    )


# ============================================================
# REVOCAR
# ============================================================

def revoke_api_key(db: Session, key_id: int, user_id: int) -> ApiKey:
    """
    Revoca una API Key.

    - is_active = False
    - revoked_at = now()
    - No se puede reactivar

    Raises:
        HTTPException 404: si no existe.
        HTTPException 403: si no es del user.
    """
    key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API Key no encontrada")
    if key.user_id != user_id:
        raise HTTPException(status_code=403, detail="No tienes permiso")

    if not key.is_active:
        # Ya revocada — idempotente
        return key

    key.is_active = False
    key.revoked_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(key)
    return key


# ============================================================
# RESOLVER (autenticación)
# ============================================================

def _is_expired(key: ApiKey) -> bool:
    """True si la key ha expirado."""
    if key.expires_at is None:
        return False
    exp = key.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) > exp


def resolve_api_key(db: Session, provided_key: str) -> tuple[ApiKey, Bot]:
    """
    Dado un Bearer token, resuelve la API Key + Bot asociado.

    Args:
        provided_key: la key completa (nvr_live_...).

    Returns:
        (api_key, bot)

    Raises:
        HTTPException 401: key inválida, revocada, expirada o formato incorrecto.
        HTTPException 404: bot no existe (raro pero posible).
    """
    if not provided_key or not provided_key.startswith(KEY_PREFIX):
        raise ApiError(
            code=ErrorCode.INVALID_API_KEY,
            message="API Key inválida",
        )

    key_hash = hash_key(provided_key)

    # Buscar por hash (indexado)
    api_key = db.query(ApiKey).filter(ApiKey.key_hash == key_hash).first()
    if not api_key:
        raise ApiError(
            code=ErrorCode.INVALID_API_KEY,
            message="API Key inválida",
        )

    if not api_key.is_active:
        raise ApiError(
            code=ErrorCode.REVOKED_API_KEY,
            message="API Key revocada",
        )

    if _is_expired(api_key):
        raise ApiError(
            code=ErrorCode.EXPIRED_API_KEY,
            message="API Key expirada",
        )

    # Verificación timing-safe adicional
    if not verify_key(provided_key, api_key.key_hash):
        raise ApiError(
            code=ErrorCode.INVALID_API_KEY,
            message="API Key inválida",
        )

    # Resolver bot
    bot = db.query(Bot).filter(Bot.id == api_key.bot_id).first()
    if not bot:
        raise ApiError(
            code=ErrorCode.NOT_FOUND,
            message="Bot asociado no encontrado",
        )

    return api_key, bot


# ============================================================
# TOUCH last_used_at
# ============================================================

def touch_last_used(db: Session, api_key: ApiKey) -> None:
    """
    Actualiza last_used_at si ha pasado más de TOUCH_INTERVAL_SECONDS.

    Throttle para no escribir en BD en cada request.
    """
    now = datetime.now(timezone.utc)
    if api_key.last_used_at:
        last = api_key.last_used_at
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        if (now - last).total_seconds() < TOUCH_INTERVAL_SECONDS:
            return

    try:
        api_key.last_used_at = now
        db.commit()
    except Exception:
        db.rollback()


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "KEY_PREFIX",
    "PREFIX_DISPLAY_LENGTH",
    "KEY_BYTES",
    "TOUCH_INTERVAL_SECONDS",
    "generate_api_key",
    "hash_key",
    "verify_key",
    "create_api_key",
    "list_api_keys",
    "revoke_api_key",
    "resolve_api_key",
    "touch_last_used",
]
