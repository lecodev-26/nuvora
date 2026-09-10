"""
Nuvora Core — SourceRetriever
================================
Implementación de KnowledgeRetriever que busca en `source_chunks`.

- Cero dependencias externas.
- Cero lógica de nichos.
- Aislamiento multi-tenant estricto por bot_id.
"""

from sqlalchemy.orm import Session

from app.models.db_models import SourceChunk
from app.core.knowledge_retriever import (
    KnowledgeRetriever,
    KnowledgeResult,
    KnowledgeItem,
)
from app.core.indexing import (
    IndexBuilder,
    score_query_against_documents,
    get_cached_index,
    set_cached_index,
)


# ============================================================
# CONSTANTES
# ============================================================

# Umbral mínimo de score para considerar un chunk relevante.
# Bajo a propósito: preferimos incluir de más y dejar que el
# ResponseBuilder decida después.
MIN_SCORE = 0.05

# Categoría por defecto si el chunk no tiene sección.
DEFAULT_CATEGORY = "general"


# ============================================================
# SOURCE RETRIEVER
# ============================================================

class SourceRetriever(KnowledgeRetriever):
    """
    Busca en la tabla `source_chunks` usando TF-IDF propio.
    """

    def __init__(self, db: Session):
        self.db = db

    def retrieve(
        self,
        bot_id: int,
        question: str,
        top_k: int = 5,
    ) -> KnowledgeResult:
        """
        Busca chunks relevantes para una pregunta.

        Returns:
            KnowledgeResult con source_type="source"
        """
        if not question or not question.strip():
            return KnowledgeResult(items=[], confidence=0.0, source_type="source")

        # 1. Cargar todos los chunks del bot
        chunks = (
            self.db.query(SourceChunk)
            .filter(SourceChunk.bot_id == bot_id)
            .order_by(SourceChunk.source_id, SourceChunk.chunk_index)
            .all()
        )

        if not chunks:
            return KnowledgeResult(items=[], confidence=0.0, source_type="source")

        # 2. Obtener índice (cacheado o construirlo)
        index = get_cached_index(bot_id)

        # Si el índice no está cacheado o el número de chunks no coincide,
        # reconstruirlo. Comparamos num_docs para detectar invalidación implícita.
        if index is None or index.get("num_docs") != len(chunks):
            documents = [c.content for c in chunks]
            builder = IndexBuilder(documents)
            index = builder.build()
            set_cached_index(bot_id, index)

        # 3. Calcular scores de la query contra los chunks
        scores = score_query_against_documents(question, index)

        # 4. Filtrar y ordenar
        scored_chunks = [
            (chunk, score)
            for chunk, score in zip(chunks, scores)
            if score >= MIN_SCORE
        ]

        if not scored_chunks:
            return KnowledgeResult(items=[], confidence=0.0, source_type="source")

        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        top_chunks = scored_chunks[:top_k]

        # 5. Construir KnowledgeItems
        items = []
        for chunk, score in top_chunks:
            items.append(KnowledgeItem(
                content=chunk.content,
                keyword=None,
                source_id=f"source:{chunk.source_id}:chunk:{chunk.chunk_index}",
                category=chunk.section or DEFAULT_CATEGORY,
                score=float(score),
                metadata={
                    "source_id": chunk.source_id,
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "section": chunk.section,
                    "page": chunk.page,
                },
            ))

        # 6. Confianza global
        top_score = top_chunks[0][1]
        confidence = min(float(top_score) * 10.0, 1.0)

        return KnowledgeResult(
            items=items,
            confidence=confidence,
            source_type="source",
            metadata={
                "total_chunks": len(chunks),
                "hits": len(items),
            },
        )
