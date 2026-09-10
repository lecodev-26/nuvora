"""
Nuvora Core — Training Assistant: Scoring
==========================================
Implementación real (14.4.3) del cálculo de progreso.

Algoritmo determinista:
    - cubierto = 1.0
    - parcial   = 0.5
    - faltante  = 0

    progress = (covered + partial * 0.5) / total

NOTA:
    - En 14.4 no existe `not_applicable`, así que no se excluye nada
      del denominador.
    - Si en el futuro se añade `not_applicable`, actualizar la fórmula
      y excluir esos topics del denominador.
    - Redondeo a 2 decimales.
"""

from app.models.training import TopicCoverage, TopicCoverageStatus


def calculate_progress(coverages: list[TopicCoverage]) -> dict:
    """
    Calcula el progreso global del bot.

    Returns:
        dict con:
            - progress: float (0.0 a 1.0, redondeado a 2 decimales)
            - covered_count: int
            - partial_count: int
            - missing_count: int
    """
    total = len(coverages)
    if total == 0:
        return {
            "progress": 0.0,
            "covered_count": 0,
            "partial_count": 0,
            "missing_count": 0,
        }

    covered = sum(1 for c in coverages if c.status == TopicCoverageStatus.COVERED)
    partial = sum(1 for c in coverages if c.status == TopicCoverageStatus.PARTIAL)
    missing = sum(1 for c in coverages if c.status == TopicCoverageStatus.MISSING)

    raw = (covered * 1.0 + partial * 0.5) / total
    progress = round(raw, 2)

    return {
        "progress": progress,
        "covered_count": covered,
        "partial_count": partial,
        "missing_count": missing,
    }
