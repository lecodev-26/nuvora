"""
Nuvora Core — Response Builder
===============================
Construye la respuesta final a partir del conocimiento recuperado.
NO conoce la lógica específica de ningún nicho.

NOTAS SOBRE LAS ESCALAS DE SCORE
---------------------------------
Los distintos retrievers usan escalas de score DIFERENTES:

- MemoryRetriever (tabla `memories`):
    Score acumulativo, sin normalizar. Rango típico: 0 a 20+.
    Un match perfecto de keyword puede llegar a valores altos.

- SourceRetriever (tabla `source_chunks`):
    Similitud coseno normalizada. Rango: 0.0 a 1.0.
    La mayoría de matches razonables quedan en 0.3-0.7.

Por eso NO se puede usar un único umbral global. El umbral se
selecciona según el TIPO del mejor KnowledgeItem (`best`), NO
según el source_type global del KnowledgeResult.

Esto también resuelve correctamente el caso "mixed": si el
mejor item es una memory con score bajo, se aplica el umbral
estricto de memory, aunque exista también una source.
"""

from app.core.bot_loader import LoadedBot
from app.core.knowledge_retriever import KnowledgeResult
from app.core.contracts import ChannelResponse


# ============================================================
# UMBRALES POR TIPO DE ITEM
# ============================================================

MIN_SCORE_MEMORY = 2.0   # Escala de MemoryRetriever
MIN_SCORE_SOURCE = 0.05  # Escala de SourceRetriever (coseno)


def _get_min_score_for_item_type(item_type: str) -> float:
    """
    Devuelve el umbral mínimo de score según el TIPO del item.

    - "memory" → MIN_SCORE_MEMORY
    - "source" → MIN_SCORE_SOURCE
    - otro / desconocido → MIN_SCORE_MEMORY (conservador)
    """
    if item_type == "source":
        return MIN_SCORE_SOURCE
    return MIN_SCORE_MEMORY


def _get_item_type(item) -> str:
    """
    Determina el tipo de un KnowledgeItem.

    Convención:
    - Si `source_id` empieza por "source:" → es "source"
    - Si empieza por "memory:" → es "memory"
    - Si no hay source_id → asumimos "memory" (conservador)
    """
    source_id = getattr(item, "source_id", None)
    if not source_id:
        return "memory"
    sid = str(source_id)
    if sid.startswith("source:"):
        return "source"
    if sid.startswith("memory:"):
        return "memory"
    # Fallback: mirar metadata
    metadata = getattr(item, "metadata", None) or {}
    if metadata.get("source_id") is not None and metadata.get("memory_id") is None:
        return "source"
    return "memory"


# ============================================================
# RESPONSE BUILDER
# ============================================================

class ResponseBuilder:

    def build(
        self,
        bot: LoadedBot,
        knowledge: KnowledgeResult,
        question: str,
    ) -> ChannelResponse:
        """
        Construye la respuesta final.

        Reglas:
        - Si no hay knowledge → fallback del bot.
        - Modo "strict":
            * Si el mejor item es de tipo "memory" → exigir score >= MIN_SCORE_MEMORY.
            * Si el mejor item es de tipo "source" → exigir score >= MIN_SCORE_SOURCE.
            * Si no supera el umbral → fallback.
        - Modo "flexible":
            * Aceptar cualquier item con score > 0.
        """
        best = knowledge.best()

        # Sin conocimiento → fallback
        if not best:
            return ChannelResponse(
                answer=bot.fallback_message,
                found=False,
                metadata={
                    "answer_mode": bot.answer_mode,
                    "confidence": 0.0,
                    "source_type": knowledge.source_type,
                },
            )

        item_type = _get_item_type(best)

        # Modo strict: exigir umbral según el tipo del MEJOR item
        if bot.answer_mode == "strict":
            min_score = _get_min_score_for_item_type(item_type)
            if best.score < min_score:
                return ChannelResponse(
                    answer=bot.fallback_message,
                    found=False,
                    metadata={
                        "answer_mode": "strict",
                        "best_item_type": item_type,
                        "best_score": float(best.score),
                        "min_score_applied": min_score,
                        "source_type": knowledge.source_type,
                    },
                )

        # Modo flexible: aceptar cualquier score > 0
        if bot.answer_mode == "flexible" and best.score <= 0:
            return ChannelResponse(
                answer=bot.fallback_message,
                found=False,
                metadata={
                    "answer_mode": "flexible",
                    "confidence": 0.0,
                    "source_type": knowledge.source_type,
                },
            )

        # Respuesta válida
        return ChannelResponse(
            answer=best.content,
            found=True,
            metadata={
                "answer_mode": bot.answer_mode,
                "best_item_type": item_type,
                "confidence": float(best.score),
                "source_type": knowledge.source_type,
                "source_id": best.source_id,
            },
        )
