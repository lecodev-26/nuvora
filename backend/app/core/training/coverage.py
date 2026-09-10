"""
Nuvora Core — Training Assistant: Coverage
============================================
STUB 14.4.2 — Sin lógica real.

En 14.4.3 se implementará el cálculo real de cobertura usando
HybridRetriever + keywords de cada topic.

REGLA ARQUITECTÓNICA:
    - Sin lógica de nichos en el Core
    - Reutiliza HybridRetriever cuando llegue 14.4.3
"""

from sqlalchemy.orm import Session

from app.core.training.topics import Topic
from app.models.training import TopicCoverage, TopicCoverageStatus


def compute_coverage(
    topics: list[Topic],
    bot_id: int,
    db: Session,
) -> list[TopicCoverage]:
    """
    STUB 14.4.2:
    Devuelve todos los temas con status=MISSING.

    La lógica real (búsqueda en Memory + Sources, thresholds, partial)
    se implementa en 14.4.3.
    """
    return [
        TopicCoverage(
            topic_id=t.id,
            label=t.label,
            description=t.description,
            icon=t.icon,
            status=TopicCoverageStatus.MISSING,
            evidence_count=0,
            best_score=0.0,
        )
        for t in topics
    ]
