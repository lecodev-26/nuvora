"""
Nuvora — Servicio BYOK (Fase 14.7.4b)
=======================================
Gestiona las API keys propias de cada usuario.

RESPONSABILIDADES:
    - Cifrar/descifrar API keys (sin dependencias externas).
    - CRUD de UserAIConfig.
    - get_effective_api_key(user_id, provider) → BYOK o fallback al sistema.

SEGURIDAD:
    - Las keys se cifran ANTES de guardar.
    - Las keys descifradas NUNCA se loguean.
    - La clave maestra (AI_ENCRYPTION_KEY) viene de .env.

CRIPTOGRAFÍA:
    Implementación propia con stdlib (hashlib + hmac + os.urandom):
        ciphertext = base64( IV (16 bytes) || XOR(plain, keystream) || HMAC-SHA256 )
    - Compatible con cualquier Python ≥ 3.6.
    - No usa `cryptography` (evita problemas en Termux/ARM64).
    - No es AES-GCM, pero es reversible, autenticado y suficiente para BYOK.
    - Migrable a Fernet en producción sin tocar la API pública.
"""

import os
import base64
import hashlib
import hmac
import logging

from sqlalchemy.orm import Session

from app.config import settings
from app.models.db_models import UserAIConfig


logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTES
# ============================================================

_IV_SIZE = 16          # bytes de IV aleatorio
_KEY_SIZE = 32         # 32 bytes de clave derivada (SHA256)
_HMAC_SIZE = 32        # SHA256 → 32 bytes
_PBKDF2_ITERATIONS = 100_000


# ============================================================
# CLAVE MAESTRA
# ============================================================

def _get_master_key() -> bytes:
    """
    Deriva la clave maestra de 32 bytes desde AI_ENCRYPTION_KEY
    (o SECRET_KEY como fallback en desarrollo).
    """
    raw = os.getenv("AI_ENCRYPTION_KEY") or os.getenv("SECRET_KEY") or "nuvora-dev-secret"

    if not os.getenv("AI_ENCRYPTION_KEY"):
        logger.warning(
            "AI_ENCRYPTION_KEY no definida. Usando SECRET_KEY como fallback. "
            "En producción, define AI_ENCRYPTION_KEY."
        )

    # PBKDF2-HMAC-SHA256 → clave de 32 bytes determinista
    salt = b"nuvora-ai-byok-v1"  # salt fijo por diseño (no es contraseña de usuario)
    return hashlib.pbkdf2_hmac(
        "sha256",
        raw.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
        dklen=_KEY_SIZE,
    )


# ============================================================
# KEYSTREAM (XOR)
# ============================================================

def _generate_keystream(key: bytes, iv: bytes, length: int) -> bytes:
    """
    Genera un keystream pseudoaleatorio de `length` bytes a partir
    de (key, iv) usando SHA256 en modo contador.

    IMPORTANTE: no es criptográficamente fuerte como AES, pero es
    determinista, no reutiliza keystream (IV aleatorio) y es suficiente
    para ofuscar API keys en una BD de confianza.
    """
    stream = b""
    counter = 0
    while len(stream) < length:
        block_input = iv + counter.to_bytes(8, "big")
        block = hmac.new(key, block_input, hashlib.sha256).digest()
        stream += block
        counter += 1
    return stream[:length]


def _xor_bytes(a: bytes, b: bytes) -> bytes:
    """XOR byte a byte. `a` y `b` deben tener la misma longitud."""
    return bytes(x ^ y for x, y in zip(a, b))


# ============================================================
# CIFRADO / DESCIFRADO
# ============================================================

def encrypt_api_key(plain: str) -> str:
    """
    Cifra una API key en texto plano.

    Returns:
        String base64 con: IV(16) || ciphertext || HMAC(32)
    """
    if not plain:
        raise ValueError("api_key vacía")

    key = _get_master_key()
    iv = os.urandom(_IV_SIZE)
    plain_bytes = plain.encode("utf-8")

    # Cifrar
    keystream = _generate_keystream(key, iv, len(plain_bytes))
    ciphertext = _xor_bytes(plain_bytes, keystream)

    # HMAC sobre (iv || ciphertext)
    mac = hmac.new(key, iv + ciphertext, hashlib.sha256).digest()

    # Empaquetar
    packed = iv + ciphertext + mac
    return base64.urlsafe_b64encode(packed).decode("ascii")


def decrypt_api_key(ciphertext_b64: str) -> str:
    """
    Descifra una API key.

    Lanza ValueError si:
        - El base64 es inválido
        - La longitud es incorrecta
        - El HMAC no coincide (manipulación)
    """
    if not ciphertext_b64:
        raise ValueError("ciphertext vacío")

    try:
        packed = base64.urlsafe_b64decode(ciphertext_b64.encode("ascii"))
    except Exception as e:
        raise ValueError("ciphertext no es base64 válido") from e

    # Mínimo: IV + algo + HMAC
    min_len = _IV_SIZE + 1 + _HMAC_SIZE
    if len(packed) < min_len:
        raise ValueError("ciphertext demasiado corto")

    iv = packed[:_IV_SIZE]
    mac = packed[-_HMAC_SIZE:]
    ciphertext = packed[_IV_SIZE:-_HMAC_SIZE]

    key = _get_master_key()

    # Verificar HMAC (constant-time)
    expected_mac = hmac.new(key, iv + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(mac, expected_mac):
        raise ValueError("HMAC inválido — el ciphertext ha sido manipulado")

    # Descifrar
    keystream = _generate_keystream(key, iv, len(ciphertext))
    plain_bytes = _xor_bytes(ciphertext, keystream)

    try:
        return plain_bytes.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ValueError("No se pudo decodificar el plaintext") from e


# ============================================================
# CRUD
# ============================================================

def get_user_config(
    db: Session,
    user_id: int,
    provider: str,
) -> UserAIConfig | None:
    """Devuelve el UserAIConfig del usuario para un provider (o None)."""
    return (
        db.query(UserAIConfig)
        .filter(
            UserAIConfig.user_id == user_id,
            UserAIConfig.provider == provider.lower(),
        )
        .first()
    )


def list_user_configs(db: Session, user_id: int) -> list[UserAIConfig]:
    """Lista todas las configs del usuario."""
    return (
        db.query(UserAIConfig)
        .filter(UserAIConfig.user_id == user_id)
        .order_by(UserAIConfig.provider)
        .all()
    )


def set_user_config(
    db: Session,
    user_id: int,
    provider: str,
    api_key: str,
) -> UserAIConfig:
    """
    Crea o actualiza la API key de un usuario para un provider.
    """
    provider = provider.lower()
    ciphertext = encrypt_api_key(api_key)

    existing = get_user_config(db, user_id, provider)
    if existing:
        existing.api_key_encrypted = ciphertext
        db.commit()
        db.refresh(existing)
        return existing

    config = UserAIConfig(
        user_id=user_id,
        provider=provider,
        api_key_encrypted=ciphertext,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def delete_user_config(
    db: Session,
    user_id: int,
    provider: str,
) -> bool:
    """Borra la config del usuario para un provider. Devuelve True si existía."""
    provider = provider.lower()
    existing = get_user_config(db, user_id, provider)
    if not existing:
        return False
    db.delete(existing)
    db.commit()
    return True


# ============================================================
# SELECCIÓN EFECTIVA (BYOK vs sistema)
# ============================================================

def get_effective_api_key(
    db: Session,
    user_id: int | None,
    provider: str,
) -> str | None:
    """
    Devuelve la API key a usar para un provider.

    Prioridad:
        1. Si user_id tiene key propia para ese provider → se usa la suya (BYOK).
        2. Si no → se usa la key del sistema (settings.ai).

    NUNCA loguea la key.
    """
    provider = provider.lower()

    # 1. BYOK
    if user_id is not None:
        config = get_user_config(db, user_id, provider)
        if config:
            try:
                return decrypt_api_key(config.api_key_encrypted)
            except ValueError:
                logger.warning(
                    f"No se pudo descifrar key BYOK del user {user_id} "
                    f"para provider {provider}. Usando sistema."
                )

    # 2. Fallback al sistema
    return settings.ai.get_api_key_for(provider)


def has_user_key(db: Session, user_id: int, provider: str) -> bool:
    """Comprueba si el usuario tiene key propia para un provider."""
    return get_user_config(db, user_id, provider.lower()) is not None


__all__ = [
    "encrypt_api_key",
    "decrypt_api_key",
    "get_user_config",
    "list_user_configs",
    "set_user_config",
    "delete_user_config",
    "get_effective_api_key",
    "has_user_key",
]
