"""
Nuvora Core — Training Assistant: Recommendations
====================================================
Implementación real (14.4.5).

Genera recomendaciones basadas en:
    - Cobertura de temas (missing / partial)
    - Preguntas frecuentes sin responder

REGLAS:
    - Determinista y explicable.
    - Sin IA. Sin lógica de nichos.
    - Las recomendaciones son SUGERENCIAS. Nunca se auto-añade conocimiento.
    - El usuario decide.

ORDEN DE PRIORIDAD:
    1. missing_topic (🔴)
    2. frequent_question con count >= 3
    3. partial_topic (🟡)
    4. frequent_question con count == 2

LÍMITE:
    - Máximo 10 recomendaciones (para no abrumar al usuario).

IDs:
    - missing_topic / partial_topic: "rec_{type}_{topic_id}"
    - frequent_question: "rec_frequent_question_{md5(representative)[:8]}"
"""

import hashlib

from app.models.db_models import Bot
from app.models.training import (
    TopicCoverage,
    TopicCoverageStatus,
    UnansweredQuestionGroup,
    Recommendation,
    RecommendationType,
)


# ============================================================
# CONSTANTES
# ============================================================

# Mínimo de veces que una pregunta debe aparecer para generar recomendación
MIN_QUESTION_COUNT = 2

# Límite total de recomendaciones devueltas
MAX_RECOMMENDATIONS = 10

# Frecuencia a partir de la cual una pregunta se considera "crítica"
CRITICAL_QUESTION_COUNT = 3


# ============================================================
# HELPERS INTERNOS
# ============================================================

def _hash_representative(representative: str) -> str:
    """
    Devuelve un hash determinista corto para una pregunta representativa.
    Se usa para construir IDs estables de recomendaciones de tipo frequent_question.
    """
    return hashlib.md5(representative.encode("utf-8")).hexdigest()[:8]


def _build_missing_topic_rec(coverage: TopicCoverage) -> Recommendation:
    """Construye una recomendación para un tema MISSING."""
    return Recommendation(
        id=f"rec_missing_topic_{coverage.topic_id}",
        type=RecommendationType.MISSING_TOPIC,
        title=f"Añade información sobre {coverage.label.lower()}",
        reason=(
            f"No hemos encontrado información suficiente "
            f"sobre {coverage.description.lower()}."
        ),
        action_type="add_memory",
        action_payload={
            "topic_id": coverage.topic_id,
            "topic_label": coverage.label,
            "suggested_keyword": coverage.topic_id,
        },
    )


def _build_partial_topic_rec(coverage: TopicCoverage) -> Recommendation:
    """Construye una recomendación para un tema PARTIAL."""
    return Recommendation(
        id=f"rec_partial_topic_{coverage.topic_id}",
        type=RecommendationType.PARTIAL_TOPIC,
        title=f"Mejora la información sobre {coverage.label.lower()}",
        reason=(
            f"Tenemos algo de información sobre {coverage.description.lower()}, "
            f"pero parece insuficiente."
        ),
        action_type="add_memory",
        action_payload={
            "topic_id": coverage.topic_id,
            "topic_label": coverage.label,
            "suggested_keyword": coverage.topic_id,
        },
    )


def _build_frequent_question_rec(group: UnansweredQuestionGroup) -> Recommendation:
    """Construye una recomendación para un grupo de preguntas frecuentes."""
    rep_hash = _hash_representative(group.representative)
    return Recommendation(
        id=f"rec_frequent_question_{rep_hash}",
        type=RecommendationType.FREQUENT_QUESTION,
        title=f'Responde a: "{group.representative}"',
        reason=(
            f"Esta pregunta ha quedado sin respuesta {group.count} veces."
        ),
        action_type="answer_question",
        action_payload={
            "question": group.representative,
            "variants": list(group.variants),
            "count": group.count,
            "conversation_ids": list(group.conversation_ids),
        },
    )


# ============================================================
# API PÚBLICA
# ============================================================

def generate_recommendations(
    bot: Bot,
    coverages: list[TopicCoverage],
    question_groups: list[UnansweredQuestionGroup],
) -> list[Recommendation]:
    """
    Genera recomendaciones priorizadas para el usuario.

    Args:
        bot: el bot analizado (no se modifica)
        coverages: cobertura de cada topic
        question_groups: grupos de preguntas sin responder

    Returns:
        Lista de Recommendation, ordenada por prioridad, máximo MAX_RECOMMENDATIONS.
    """
    # 1. Clasificar topics
    missing = [c for c in coverages if c.status == TopicCoverageStatus.MISSING]
    partial = [c for c in coverages if c.status == TopicCoverageStatus.PARTIAL]

    # 2. Clasificar preguntas por frecuencia
    critical_questions = [
        g for g in question_groups if g.count >= CRITICAL_QUESTION_COUNT
    ]
    normal_questions = [
        g for g in question_groups
        if MIN_QUESTION_COUNT <= g.count < CRITICAL_QUESTION_COUNT
    ]

    # 3. Ordenar dentro de cada grupo (estable)
    #    - Topics: por topic_id (orden estable)
    #    - Questions: por count DESC, luego por representative (estable)
    missing.sort(key=lambda c: c.topic_id)
    partial.sort(key=lambda c: c.topic_id)
    critical_questions.sort(key=lambda g: (-g.count, g.representative))
    normal_questions.sort(key=lambda g: (-g.count, g.representative))

    # 4. Construir recomendaciones en orden de prioridad
    recommendations: list[Recommendation] = []

    # 4.1 missing_topic
    for cov in missing:
        recommendations.append(_build_missing_topic_rec(cov))

    # 4.2 frequent_question (count >= 3)
    for g in critical_questions:
        recommendations.append(_build_frequent_question_rec(g))

    # 4.3 partial_topic
    for cov in partial:
        recommendations.append(_build_partial_topic_rec(cov))

    # 4.4 frequent_question (count == 2)
    for g in normal_questions:
        recommendations.append(_build_frequent_question_rec(g))

    # 5. Truncar al límite
    return recommendations[:MAX_RECOMMENDATIONS]
