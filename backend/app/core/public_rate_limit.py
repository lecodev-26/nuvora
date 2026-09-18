"""
Nuvora — Rate Limiting para endpoints públicos (Fase 14.9.9)
==============================================================
Protege /public/* contra abuso desde visitantes anónimos.

MECANISMO:
    - In-memory: dict de { (bucket, key): [timestamps] }
    - Al hacer check, se limpian los timestamps fuera de la ventana.
    - Si len(timestamps) >= max → lanza PublicRateLimitExceeded.

BUCKETS:
    - public_session_create: por IP
    - public_message:        por IP
    - public_message_session: por session_id

IMPORTANTE:
    - In-memory → se resetea al reiniciar el server.
    - Redis → futuro (14.13).
    - Uso: check_public_rate_limit(key="1.2.3.4", bucket="public_message").
"""

import time
from typing import Optional

from app.config import settings


# ============================================================
# EXCEPCIÓN
# ============================================================

class PublicRateLimitExceeded(Exception):
    """Se superó el rate limit público."""

    def __init__(self, bucket: str, limit: int, window_seconds: int, retry_after: int):
        self.bucket = bucket
        self.limit = limit
        self.window_seconds = window_seconds
        self.retry_after = max(1, retry_after)
        super().__init__(
            f"Rate limit excedido ({bucket}): {limit}/{window_seconds}s"
        )


# ============================================================
# ALMACENAMIENTO IN-MEMORY
# ============================================================

# { (bucket, key): [timestamp, ...] }
_store: dict[tuple[str, str], list[float]] = {}


def _now() -> float:
    return time.time()


def _prune(entries: list[float], window: float) -> list[float]:
    """Devuelve solo los timestamps dentro de la ventana."""
    cutoff = _now() - window
    return [t for t in entries if t > cutoff]


# ============================================================
# CONFIG POR BUCKET
# ============================================================

def _get_limit_for(bucket: str) -> int:
    """
    Devuelve el límite por hora (o ventana configurada) según bucket.
    """
    cfg = settings.public_rate_limit
    if bucket == "public_session_create":
        return cfg.session_create_limit
    if bucket == "public_message":
        return cfg.message_limit
    if bucket == "public_message_session":
        return cfg.message_per_session_limit
    # Default conservador
    return 30


# ============================================================
# API PRINCIPAL
# ============================================================

def check_public_rate_limit(
    key: str,
    bucket: str,
    max_per_window: Optional[int] = None,
    window_seconds: Optional[int] = None,
) -> None:
    """
    Comprueba y actualiza el rate limit.

    Args:
        key: identificador (IP, session_id, ...).
        bucket: nombre del bucket.
        max_per_window: override del límite (default: según bucket).
        window_seconds: override de la ventana (default: settings).

    Raises:
        PublicRateLimitExceeded: si se superó el límite.
    """
    cfg = settings.public_rate_limit

    # Si está desactivado, no hacemos nada
    if not cfg.enabled:
        return

    limit = max_per_window if max_per_window is not None else _get_limit_for(bucket)
    window = window_seconds if window_seconds is not None else cfg.window_seconds

    if limit <= 0:
        return  # límite 0 o negativo → ilimitado

    store_key = (bucket, key)
    entries = _store.get(store_key, [])
    entries = _prune(entries, window)

    if len(entries) >= limit:
        # Calcular Retry-After: cuándo expira el más antiguo
        oldest = min(entries) if entries else _now()
        retry_after = int(window - (_now() - oldest)) + 1
        raise PublicRateLimitExceeded(
            bucket=bucket,
            limit=limit,
            window_seconds=window,
            retry_after=retry_after,
        )

    entries.append(_now())
    _store[store_key] = entries


def get_public_remaining(key: str, bucket: str) -> dict:
    """
    Devuelve info de uso del rate limit (para debug/tests).
    """
    cfg = settings.public_rate_limit
    limit = _get_limit_for(bucket)
    window = cfg.window_seconds

    entries = _store.get((bucket, key), [])
    entries = _prune(entries, window)

    return {
        "bucket": bucket,
        "key": key,
        "limit": limit,
        "window_seconds": window,
        "used": len(entries),
        "remaining": max(0, limit - len(entries)),
    }


def reset_public_all() -> None:
    """Limpia todos los contadores (para tests)."""
    _store.clear()


def reset_public_key(key: str) -> None:
    """Limpia los contadores de una key concreta (para tests)."""
    for k in list(_store.keys()):
        if k[1] == key:
            del _store[k]


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "PublicRateLimitExceeded",
    "check_public_rate_limit",
    "get_public_remaining",
    "reset_public_all",
    "reset_public_key",
]
