"""
Nuvora Core — Training Assistant: Coverage
============================================
Implementación real (14.4.3) del cálculo de cobertura por tema.

Reutiliza HybridRetriever (NO duplica el motor de búsqueda).

REGLAS:
    - La relevancia/calidad del score es el criterio principal.
    - Una única evidencia fuerte puede marcar un topic como COVERED.
    - evidence_count es informativo, NO requisito para COVERED.
    - NO se suman scores entre Memory y Source (escalas diferentes).
    - Tipos desconocidos de source_id NO se asumen como memory.

UMBRALES NATIVOS (escalas distintas):
    Memory (score acumulativo):
        strong  >= 2.0
        partial >= 0.5
    Source (score coseno [0, 1]):
        strong  >= 0.10
        partial >= 0.03

NOTA:
    SourceRetriever ya filtra por MIN_SCORE=0.05 antes de devolver items.
    Por tanto, cualquier source que llegue aquí tiene score >= 0.05.
    Esto significa que un source con score en [0.05, 0.10) será PARTIAL,
    y uno con score >= 0.10 será COVERED.

REGLA ARQUITECTÓNICA:
    - Sin lógica de nichos en el Core.
    - La función _item_type está duplicada deliberadamente desde
      response_builder.py (14.3.6) para no tocar ese módulo.
      Si los umbrales cambian, actualizar ambos sitios.
"""

from sqlalchemy.orm import Session

from app.core.training.topics import Topic
from app.core.hybrid_retriever import HybridRetriever
from app.core.knowledge_retriever import KnowledgeItem
from app.models.training import TopicCoverage, TopicCoverageStatus


# ============================================================
# CONSTANTES
# ============================================================

# Top_K items a pedir por topic al HybridRetriever
TOP_K_PER_TOPIC = 5

# Umbrales Memory (escala acumulativa)
MEMORY_STRONG_THRESHOLD = 2.0
MEMORY_PARTIAL_THRESHOLD = 0.5

# Umbrales Source (escala coseno [0, 1])
SOURCE_STRONG_THRESHOLD = 0.10
SOURCE_PARTIAL_THRESHOLD = 0.03


# ============================================================
# HELPERS
# ============================================================

def _item_type(item: KnowledgeItem) -> str:
    """
    Determina el tipo de un KnowledgeItem.

    NOTA: Duplicado deliberadamente de response_builder._get_item_type()
    para no tocar ese módulo (alcance 14.4.3).

    Reglas:
        - source_id "memory:" → "memory"
        - source_id "source:" → "source"
        - cualquier otro formato → "unknown" (NO asumir memory)
    """
    sid = str(item.source_id or "")
    if sid.startswith("source:"):
        return "source"
    if sid.startswith("memory:"):
        return "memory"
    return "unknown"


def _build_query_for_topic(topic: Topic) -> str:
    """Construye un query sintético uniendo las keywords del topic."""
    return " ".join(topic.keywords)


def _classify(
    items: list[KnowledgeItem],
) -> tuple[TopicCoverageStatus, int, float]:
    """
    Clasifica la lista de items en COVERED/PARTIAL/MISSING.

    Returns:
        (status, evidence_count, best_score)
        - evidence_count: nº de items con tipo válido (memory o source)
        - best_score: mejor score entre los items válidos (de cualquier tipo)
    """
    # Separar scores por tipo (ignorar "unknown")
    memory_scores: list[float] = []
    source_scores: list[float] = []

    for item in items:
        itype = _item_type(item)
        if itype == "memory":
            memory_scores.append(float(item.score))
        elif itype == "source":
            source_scores.append(float(item.score))
        # "unknown" → ignorado

    best_memory = max(memory_scores) if memory_scores else None
    best_source = max(source_scores) if source_scores else None

    # Evaluar fuerza
    memory_strong = best_memory is not None and best_memory >= MEMORY_STRONG_THRESHOLD
    memory_partial = best_memory is not None and best_memory >= MEMORY_PARTIAL_THRESHOLD
    source_strong = best_source is not None and best_source >= SOURCE_STRONG_THRESHOLD
    source_partial = best_source is not None and best_source >= SOURCE_PARTIAL_THRESHOLD

    # Decisión (sin sumar scores entre escalas)
    if memory_strong or source_strong:
        status = TopicCoverageStatus.COVERED
    elif memory_partial or source_partial:
        status = TopicCoverageStatus.PARTIAL
    else:
        status = TopicCoverageStatus.MISSING

    # Evidencia informativa
    evidence_count = len(memory_scores) + len(source_scores)
    best_score = max(
        [s for s in (best_memory, best_source) if s is not None],
        default=0.0,
    )

    return status, evidence_count, best_score


# ============================================================
# API PÚBLICA
# ============================================================

def compute_coverage(
    topics: list[Topic],
    bot_id: int,
    db: Session,
) -> list[TopicCoverage]:
    """
    Calcula la cobertura de cada topic consultando HybridRetriever.

    Args:
        topics: catálogo de topics del nicho del bot
        bot_id: ID del bot
        db: sesión de BD (para HybridRetriever)

    Returns:
        list[TopicCoverage], uno por cada topic (mismo orden)
    """
    retriever = HybridRetriever(db)
    results: list[TopicCoverage] = []

    for topic in topics:
        query = _build_query_for_topic(topic)

        # Consulta al retriever (Memory + Source combinados)
        knowledge = retriever.retrieve(
            bot_id=bot_id,
            question=query,
            top_k=TOP_K_PER_TOPIC,
        )

        status, evidence_count, best_score = _classify(knowledge.items)

        results.append(TopicCoverage(
            topic_id=topic.id,
            label=topic.label,
            description=topic.description,
            icon=topic.icon,
            status=status,
            evidence_count=evidence_count,
            best_score=best_score,
        ))

    return results
