"""
Tests — Subfase 14.9.9 (Rate limiting público — UNIT)
=======================================================
Tests del rate limiter en aislamiento (sin HTTP).

Cubre:
    - check_public_rate_limit: dentro, exacto, superado
    - get_public_remaining: refleja uso correcto
    - reset_public_all / reset_public_key
    - Buckets independientes
    - Límite 0 → ilimitado
    - enabled=False → no aplica
    - Bucket desconocido → fallback 30
    - Retry-After correcto
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.core.public_rate_limit import (
    check_public_rate_limit,
    get_public_remaining,
    reset_public_all,
    reset_public_key,
    PublicRateLimitExceeded,
)


# ============================================================
# TESTS
# ============================================================

def test_below_limit_ok():
    print("\n" + "=" * 70)
    print("TEST 1: por debajo del límite → OK")
    print("=" * 70)
    reset_public_all()
    # 5 llamadas al bucket session_create (limit 10)
    for _ in range(5):
        check_public_rate_limit(key="1.1.1.1", bucket="public_session_create")
    info = get_public_remaining(key="1.1.1.1", bucket="public_session_create")
    assert info["used"] == 5
    assert info["remaining"] == 5
    print(f"  ✅ used=5, remaining=5")


def test_exactly_at_limit_ok():
    print("\n" + "=" * 70)
    print("TEST 2: exactamente en el límite → OK (la última entra)")
    print("=" * 70)
    reset_public_all()
    # 10 llamadas (limit 10) → la 10ª debe entrar
    for _ in range(10):
        check_public_rate_limit(key="1.1.1.1", bucket="public_session_create")
    info = get_public_remaining(key="1.1.1.1", bucket="public_session_create")
    assert info["used"] == 10
    assert info["remaining"] == 0
    print(f"  ✅ used=10, remaining=0")


def test_exceeded_limit_raises():
    print("\n" + "=" * 70)
    print("TEST 3: superar el límite → excepción")
    print("=" * 70)
    reset_public_all()
    for _ in range(10):
        check_public_rate_limit(key="1.1.1.1", bucket="public_session_create")
    try:
        check_public_rate_limit(key="1.1.1.1", bucket="public_session_create")
        raise AssertionError("Debería haber lanzado excepción")
    except PublicRateLimitExceeded as e:
        assert e.bucket == "public_session_create"
        assert e.limit == 10
        assert e.retry_after > 0
        print(f"  ✅ Excepción: retry_after={e.retry_after}s")


def test_get_remaining_reflects_usage():
    print("\n" + "=" * 70)
    print("TEST 4: get_public_remaining refleja uso")
    print("=" * 70)
    reset_public_all()
    check_public_rate_limit(key="x", bucket="public_message")
    check_public_rate_limit(key="x", bucket="public_message")
    check_public_rate_limit(key="x", bucket="public_message")
    info = get_public_remaining(key="x", bucket="public_message")
    assert info["used"] == 3
    assert info["remaining"] == 57
    assert info["limit"] == 60
    print(f"  ✅ used=3, remaining=57, limit=60")


def test_reset_all():
    print("\n" + "=" * 70)
    print("TEST 5: reset_public_all limpia todo")
    print("=" * 70)
    reset_public_all()
    for _ in range(5):
        check_public_rate_limit(key="a", bucket="public_message")
        check_public_rate_limit(key="b", bucket="public_message")
    info_a = get_public_remaining(key="a", bucket="public_message")
    assert info_a["used"] == 5

    reset_public_all()
    info_a = get_public_remaining(key="a", bucket="public_message")
    info_b = get_public_remaining(key="b", bucket="public_message")
    assert info_a["used"] == 0
    assert info_b["used"] == 0
    print("  ✅ Todo limpio")


def test_reset_specific_key():
    print("\n" + "=" * 70)
    print("TEST 6: reset_public_key limpia solo esa key")
    print("=" * 70)
    reset_public_all()
    for _ in range(3):
        check_public_rate_limit(key="a", bucket="public_message")
        check_public_rate_limit(key="b", bucket="public_message")

    reset_public_key("a")

    info_a = get_public_remaining(key="a", bucket="public_message")
    info_b = get_public_remaining(key="b", bucket="public_message")
    assert info_a["used"] == 0, f"a debería estar limpio, tiene {info_a['used']}"
    assert info_b["used"] == 3, f"b debería tener 3, tiene {info_b['used']}"
    print("  ✅ Key 'a' limpia, 'b' intacta")


def test_buckets_independent():
    print("\n" + "=" * 70)
    print("TEST 7: buckets independientes (IP ≠ session)")
    print("=" * 70)
    reset_public_all()
    # 10 llamadas al bucket por IP con key "1.1.1.1"
    for _ in range(10):
        check_public_rate_limit(key="1.1.1.1", bucket="public_message")

    # El bucket por session con la misma key NO debe estar afectado
    check_public_rate_limit(key="1.1.1.1", bucket="public_message_session")
    info = get_public_remaining(key="1.1.1.1", bucket="public_message_session")
    assert info["used"] == 1
    print("  ✅ Buckets no se mezclan")


def test_limit_zero_means_unlimited():
    print("\n" + "=" * 70)
    print("TEST 8: max_per_window=0 → ilimitado")
    print("=" * 70)
    reset_public_all()
    for _ in range(100):
        check_public_rate_limit(key="x", bucket="custom", max_per_window=0)
    print("  ✅ 100 llamadas OK (ilimitado)")


def test_bucket_unknown_fallback():
    print("\n" + "=" * 70)
    print("TEST 9: bucket desconocido → fallback 30")
    print("=" * 70)
    reset_public_all()
    info = get_public_remaining(key="x", bucket="unknown_bucket_xyz")
    assert info["limit"] == 30, f"Esperado 30, obtenido {info['limit']}"
    print(f"  ✅ Fallback limit=30")


def test_retry_after_positive():
    print("\n" + "=" * 70)
    print("TEST 10: Retry-After positivo y razonable")
    print("=" * 70)
    reset_public_all()
    for _ in range(10):
        check_public_rate_limit(key="x", bucket="public_session_create")
    try:
        check_public_rate_limit(key="x", bucket="public_session_create")
        raise AssertionError("Debería haber lanzado excepción")
    except PublicRateLimitExceeded as e:
        assert e.retry_after > 0
        assert e.retry_after <= settings.public_rate_limit.window_seconds + 1
        print(f"  ✅ retry_after={e.retry_after}s (dentro de ventana)")
        # En la práctica, como acabamos de hacer las llamadas, retry_after ~3600


def test_custom_limit_override():
    print("\n" + "=" * 70)
    print("TEST 11: override max_per_window")
    print("=" * 70)
    reset_public_all()
    for _ in range(3):
        check_public_rate_limit(
            key="x", bucket="public_message", max_per_window=3,
        )
    try:
        check_public_rate_limit(
            key="x", bucket="public_message", max_per_window=3,
        )
        raise AssertionError("Debería haber lanzado excepción")
    except PublicRateLimitExceeded as e:
        assert e.limit == 3
        print(f"  ✅ Override limit=3 → excepción con limit=3")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS UNIT — SUBFASE 14.9.9 (Rate limiter aislado)")
    print("=" * 70)

    tests = [
        test_below_limit_ok,
        test_exactly_at_limit_ok,
        test_exceeded_limit_raises,
        test_get_remaining_reflects_usage,
        test_reset_all,
        test_reset_specific_key,
        test_buckets_independent,
        test_limit_zero_means_unlimited,
        test_bucket_unknown_fallback,
        test_retry_after_positive,
        test_custom_limit_override,
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
