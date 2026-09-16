"""
Nuvora Core — AI: Rate Limiting
==================================
Rate limiting in-memory para endpoints /ai/*.

FILOSOFÍA:
    - MVP: in-memory dict. Migrable a Redis cuando escale.
    - Sliding window por usuario y por endpoint.
    - Limpieza automática de timestamps antiguos.

USO:
    from app.core.ai.rate_limit import check_rate_limit
    check_rate_limit(user_id=42, bucket="generate", max_per_hour=10)
    # Lanza RateLimitExceeded si supera el límite.

    from app.core.ai.rate_limit import get_remaining
    remaining = get_remaining(user_id=42, bucket="generate", max_per_hour=10)

NO conoce la lógica de Nuvora. Solo cuenta timestamps.
"""

import time
import logging
import threading

from app.config import settings


logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTES
# ============================================================

WINDOW_SECONDS = 3600  # ventana de 1 hora

# Buckets válidos (para validación interna)
VALID_BUCKETS = {
    # IA (14.7)
    "generate",
    "modify",
    "explain",
    "analyze",
    "templates_list",
    "templates_instantiate",
    # Bot Tester (14.8)
    "test_run",
    "test_run_all",
    "test_analyze",
}


# ============================================================
# ERROR
# ============================================================

class RateLimitExceeded(Exception):
    """
    Excepción lanzada cuando un usuario supera el rate limit.

    Atributos:
        user_id: ID del usuario
        bucket: nombre del bucket (ej: "generate")
        retry_after: segundos hasta el siguiente intento permitido
        limit: límite configurado (para mensaje)
    """

    def __init__(self, user_id: int, bucket: str, retry_after: int, limit: int):
        self.user_id = user_id
        self.bucket = bucket
        self.retry_after = retry_after
        self.limit = limit
        super().__init__(
            f"Rate limit excedido en '{bucket}': {limit} por hora. "
            f"Reintenta en {retry_after}s."
        )


# ============================================================
# ALMACENAMIENTO IN-MEMORY
# ============================================================

# Estructura: _buckets[(user_id, bucket)] = [timestamp1, timestamp2, ...]
_buckets: dict[tuple[int, str], list[float]] = {}

# Lock para concurrencia (aunque FastAPI con sync endpoints no lo requiere
# estrictamente, es buena práctica y permite futuro async)
_lock = threading.Lock()


# ============================================================
# API PÚBLICA
# ============================================================

def check_rate_limit(user_id: int, bucket: str, max_per_hour: int) -> None:
    """
    Comprueba y registra un intento.

    Si el usuario ha superado el límite → RateLimitExceeded.

    Si no lo ha superado → registra el timestamp y devuelve None.

    Args:
        user_id: ID del usuario autenticado.
        bucket: nombre del bucket ('generate', 'modify', ...).
        max_per_hour: límite máximo en la ventana de 1 hora.

    Raises:
        RateLimitExceeded: si supera el límite.
        ValueError: si el bucket no es válido.
    """
    if bucket not in VALID_BUCKETS:
        raise ValueError(f"Bucket inválido: '{bucket}'. Válidos: {VALID_BUCKETS}")

    # Si el rate limit está deshabilitado globalmente → no hacer nada
    if not settings.ai.rate_limit_enabled:
        return

    if user_id is None or user_id <= 0:
        raise ValueError(f"user_id inválido: {user_id}")

    now = time.time()
    cutoff = now - WINDOW_SECONDS
    key = (user_id, bucket)

    with _lock:
        timestamps = _buckets.get(key, [])

        # 1. Limpiar timestamps fuera de la ventana
        timestamps = [ts for ts in timestamps if ts > cutoff]

        # 2. Comprobar límite
        if len(timestamps) >= max_per_hour:
            # Retry: cuándo expira el más antiguo + 1s de margen
            oldest = min(timestamps)
            retry_after = max(1, int(oldest + WINDOW_SECONDS - now) + 1)
            _buckets[key] = timestamps
            logger.warning(
                f"[rate_limit] user={user_id} bucket={bucket} EXCEDIDO "
                f"({len(timestamps)}/{max_per_hour}). Retry en {retry_after}s."
            )
            raise RateLimitExceeded(
                user_id=user_id,
                bucket=bucket,
                retry_after=retry_after,
                limit=max_per_hour,
            )

        # 3. Registrar el nuevo intento
        timestamps.append(now)
        _buckets[key] = timestamps

        logger.debug(
            f"[rate_limit] user={user_id} bucket={bucket} "
            f"{len(timestamps)}/{max_per_hour}"
        )


def get_remaining(user_id: int, bucket: str, max_per_hour: int) -> int:
    """
    Devuelve cuántos intentos le quedan al usuario en la ventana actual.
    """
    if not settings.ai.rate_limit_enabled:
        return max_per_hour

    if bucket not in VALID_BUCKETS:
        raise ValueError(f"Bucket inválido: '{bucket}'")

    now = time.time()
    cutoff = now - WINDOW_SECONDS
    key = (user_id, bucket)

    with _lock:
        timestamps = _buckets.get(key, [])
        timestamps = [ts for ts in timestamps if ts > cutoff]
        _buckets[key] = timestamps
        return max(0, max_per_hour - len(timestamps))


def reset_bucket(user_id: int, bucket: str | None = None) -> None:
    """
    Resetea los timestamps de un usuario.
    Si bucket=None, resetea TODOS los buckets del usuario.

    Útil para tests.
    """
    with _lock:
        if bucket is None:
            keys_to_delete = [k for k in _buckets if k[0] == user_id]
            for k in keys_to_delete:
                del _buckets[k]
        else:
            _buckets.pop((user_id, bucket), None)


def reset_all() -> None:
    """Resetea TODOS los buckets. Solo para tests."""
    with _lock:
        _buckets.clear()


def get_stats() -> dict:
    """Devuelve estadísticas del rate limiter (útil para debug)."""
    with _lock:
        now = time.time()
        cutoff = now - WINDOW_SECONDS
        stats = {
            "enabled": settings.ai.rate_limit_enabled,
            "window_seconds": WINDOW_SECONDS,
            "active_buckets": 0,
            "total_timestamps": 0,
        }
        for key, timestamps in _buckets.items():
            valid = [ts for ts in timestamps if ts > cutoff]
            if valid:
                stats["active_buckets"] += 1
                stats["total_timestamps"] += len(valid)
        return stats


__all__ = [
    "check_rate_limit",
    "get_remaining",
    "reset_bucket",
    "reset_all",
    "get_stats",
    "RateLimitExceeded",
    "VALID_BUCKETS",
    "WINDOW_SECONDS",
]
