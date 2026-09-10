"""
Nuvora Core — Training Assistant: Unanswered Questions
========================================================
STUB 14.4.2 — Sin lógica real.

En 14.4.4 se implementará:
    - Consulta de Conversation.was_answered=False
    - Agrupación por Jaccard similarity
    - Limit configurable

REGLA:
    - Sin IA
    - Jaccard sobre tokens (reutilizar tokenize() de 14.3.3)
    - Encapsulado para poder sustituirlo después
"""

from sqlalchemy.orm import Session

from app.models.training import UnansweredQuestionGroup


def get_unanswered_question_groups(
    bot_id: int,
    db: Session,
    limit: int = 100,
) -> list[UnansweredQuestionGroup]:
    """
    STUB 14.4.2:
    Devuelve lista vacía.

    La lógica real se implementa en 14.4.4.
    """
    return []
