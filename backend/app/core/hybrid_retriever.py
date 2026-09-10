"""
Nuvora Core — HybridRetriever
================================
Combina resultados de MemoryRetriever y SourceRetriever.

Reglas:
- Consultas secuenciales (memory → source)
- Ranking por score DESC
- Tie-break: memory antes que source, luego orden estable por source_id
- source_type: "memory" | "source" | "mixed"
- Sin filtro adicional de score (respeta lo que cada retriever devuelve)
- Cero lógica de nichos
"""

from sqlalchemy.orm import Session

from app.core.knowledge_retriever import (
    KnowledgeRetriever,
    KnowledgeResult,
    KnowledgeItem,
)
from app.core.memory_retriever import MemoryRetriever
from app.core.source_retriever import SourceRetriever


# ============================================================
# CONSTANTES
# ============================================================

# Orden de preferencia en empates (menor número = mayor prioridad)
TYPE_PRIORITY = {
    "memory": 0,
    "source": 1,
}


# ============================================================
# HYBRID RETRIEVER
# ============================================================

class HybridRetriever(KnowledgeRetriever):
    """
    Combina MemoryRetriever + SourceRetriever.
    """

    def __init__(self, db: Session):
        self.db = db
        self.memory_retriever = MemoryRetriever(db)
        self.source_retriever = SourceRetriever(db)

    def retrieve(
        self,
        bot_id: int,
        question: str,
        top_k: int = 5,
    ) -> KnowledgeResult:
        """
        Consulta ambos retrievers y devuelve un resultado combinado.
        """
        # 0. Validación de top_k
        if top_k <= 0:
            return KnowledgeResult(
                items=[],
                confidence=0.0,
                source_type="memory",
                metadata={
                    "memory_hits": 0,
                    "source_hits": 0,
                    "top_source_type": None,
                },
            )

        if not question or not question.strip():
            return KnowledgeResult(
                items=[],
                confidence=0.0,
                source_type="memory",
                metadata={
                    "memory_hits": 0,
                    "source_hits": 0,
                    "top_source_type": None,
                },
            )

        # 1. Consultar ambos retrievers (secuencial)
        #    Pedimos top_k a cada uno por si uno solo ya cubre el top_k final
        memory_result = self.memory_retriever.retrieve(bot_id, question, top_k=top_k)
        source_result = self.source_retriever.retrieve(bot_id, question, top_k=top_k)

        memory_items = memory_result.items if memory_result else []
        source_items = source_result.items if source_result else []

        memory_hits = len(memory_items)
        source_hits = len(source_items)

        # 2. Caso especial: ambos vacíos
        if memory_hits == 0 and source_hits == 0:
            return KnowledgeResult(
                items=[],
                confidence=0.0,
                source_type="memory",
                metadata={
                    "memory_hits": 0,
                    "source_hits": 0,
                    "top_source_type": None,
                },
            )

        # 3. Anotar cada item con su tipo (para tie-break)
        annotated: list[tuple[str, KnowledgeItem]] = []
        for item in memory_items:
            annotated.append(("memory", item))
        for item in source_items:
            annotated.append(("source", item))

        # 4. Ordenar por:
        #    - score DESC
        #    - tipo (memory primero)
        #    - source_id (estable)
        def sort_key(entry: tuple[str, KnowledgeItem]):
            item_type, item = entry
            # score descendente → usamos -score
            # tipo: memory=0, source=1
            # source_id como string para orden estable
            return (
                -float(item.score),
                TYPE_PRIORITY.get(item_type, 99),
                str(item.source_id or ""),
            )

        annotated.sort(key=sort_key)

        # 5. Tomar top_k
        top_entries = annotated[:top_k]

        # 6. Determinar source_type
        if memory_hits > 0 and source_hits > 0:
            source_type = "mixed"
        elif memory_hits > 0:
            source_type = "memory"
        else:
            source_type = "source"

        # 7. Metadata
        top_source_type = top_entries[0][0] if top_entries else None
        metadata = {
            "memory_hits": memory_hits,
            "source_hits": source_hits,
            "top_source_type": top_source_type,
        }

        # 8. Confidence basada en el mejor score
        top_score = float(top_entries[0][1].score) if top_entries else 0.0
        confidence = min(top_score * 10.0, 1.0)

        # 9. Devolver items sin la anotación de tipo
        items = [item for _, item in top_entries]

        return KnowledgeResult(
            items=items,
            confidence=confidence,
            source_type=source_type,
            metadata=metadata,
        )
