"""
Nuvora Core — Training Assistant: Scoring
==========================================
STUB 14.4.2 — Sin lógica real.

En 14.4.3 se implementará el cálculo real de progreso.

REGLA:
    - cubierto = 1.0
    - parcial = 0.5
    - faltante = 0
    - no_aplicable = excluido del denominador (no en 14.4)
"""

from app.models.training import TopicCoverage


def calculate_progress(coverages: list[TopicCoverage]) -> dict:
    """
    STUB 14.4.2:
    Devuelve progreso 0.0 y contadores 0.

    La lógica real se implementa en 14.4.3.
    """
    return {
        "progress": 0.0,
        "covered_count": 0,
        "partial_count": 0,
        "missing_count": 0,
    }
