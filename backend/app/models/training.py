"""
Nuvora — Training Assistant: Schemas Pydantic
==============================================
Contratos de entrada/salida del Training Assistant (Fase 14.4).

Estos schemas son SOLO de lectura (el Training Assistant no escribe
en BD en 14.4). No se persisten.

IMPORTANTE:
    - `nicho_id` es opcional. Un bot "Desde cero" tendrá nicho_id=None.
    - Los status de cobertura no incluyen "not_applicable" en 14.4.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional


# ============================================================
# ENUMS
# ============================================================

class TopicCoverageStatus(str, Enum):
    """Estado de cobertura de un tema."""
    COVERED = "covered"
    PARTIAL = "partial"
    MISSING = "missing"


class RecommendationType(str, Enum):
    """Tipo de recomendación."""
    MISSING_TOPIC = "missing_topic"
    PARTIAL_TOPIC = "partial_topic"
    FREQUENT_QUESTION = "frequent_question"


# ============================================================
# TOPIC COVERAGE
# ============================================================

class TopicCoverage(BaseModel):
    """Estado de un tema concreto en el conocimiento del bot."""
    topic_id: str
    label: str
    description: str
    icon: str = ""
    status: TopicCoverageStatus
    evidence_count: int = 0     # Nº de resultados del KnowledgeRetriever
    best_score: float = 0.0     # Mejor score encontrado (escala del retriever)


# ============================================================
# UNANSWERED QUESTIONS
# ============================================================

class UnansweredQuestionGroup(BaseModel):
    """Grupo de preguntas similares sin responder."""
    representative: str                          # Pregunta representativa
    variants: list[str] = Field(default_factory=list)
    count: int = 0                               # Frecuencia total del grupo
    conversation_ids: list[int] = Field(default_factory=list)


# ============================================================
# RECOMMENDATION
# ============================================================

class Recommendation(BaseModel):
    """Recomendación generada por el Training Assistant."""
    id: str                                      # Identificador único
    type: RecommendationType
    title: str
    reason: str
    action_type: str                             # "add_memory" | "add_source" | "answer_question"
    action_payload: dict = Field(default_factory=dict)


# ============================================================
# TRAINING REPORT
# ============================================================

class TrainingReport(BaseModel):
    """
    Resultado completo del análisis del Training Assistant.

    NOTA:
        - `nicho_id` es Optional. Un bot "Desde cero" tiene nicho_id=None.
        - El catálogo usa fallback (ej: "otro") para mostrar topics genéricos,
          pero eso es decisión del catálogo, no modifica el bot real.
    """
    bot_id: int
    bot_name: str
    nicho_id: Optional[str] = None

    # Progreso global (0.0 a 1.0)
    progress: float = 0.0
    total_topics: int = 0
    covered_count: int = 0
    partial_count: int = 0
    missing_count: int = 0

    # Detalle por tema
    topics: list[TopicCoverage] = Field(default_factory=list)
    missing_topics: list[TopicCoverage] = Field(default_factory=list)
    partial_topics: list[TopicCoverage] = Field(default_factory=list)

    # Preguntas sin responder
    unanswered_questions: list[UnansweredQuestionGroup] = Field(default_factory=list)

    # Recomendaciones
    recommendations: list[Recommendation] = Field(default_factory=list)

    # Metadata
    analyzed_at: datetime
    has_memories: bool = False
    has_sources: bool = False
    memories_count: int = 0
    ready_sources_count: int = 0
    conversations_analyzed: int = 0
