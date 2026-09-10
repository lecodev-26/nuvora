"""
Nuvora Core — Training Assistant: Recommendations
==================================================
STUB 14.4.2 — Sin lógica real.

En 14.4.5 se implementará:
    - Recomendaciones por temas faltantes (missing_topic)
    - Recomendaciones por temas parciales (partial_topic)
    - Recomendaciones por preguntas frecuentes sin responder (frequent_question)

REGLA:
    - Las recomendaciones son SUGERENCIAS
    - NUNCA se auto-añade conocimiento
    - El usuario decide
"""

from app.models.db_models import Bot
from app.models.training import (
    TopicCoverage,
    UnansweredQuestionGroup,
    Recommendation,
)


def generate_recommendations(
    bot: Bot,
    coverages: list[TopicCoverage],
    question_groups: list[UnansweredQuestionGroup],
) -> list[Recommendation]:
    """
    STUB 14.4.2:
    Devuelve lista vacía.

    La lógica real se implementa en 14.4.5.
    """
    return []
