"""
Nuvora Core — MemoryRetriever
Implementación del KnowledgeRetriever basada en la tabla `memories`.
Esta es la única pieza del Core que conoce la existencia de la tabla `memories`.
"""

from sqlalchemy.orm import Session
from app.models.db_models import Memory
from app.core.knowledge_retriever import (
    KnowledgeRetriever, KnowledgeResult, KnowledgeItem
)


# Palabras vacías en español (no aportan información)
STOPWORDS = {
    "qué", "cuál", "cómo", "dónde", "cuándo", "quién",
    "para", "por", "con", "sin", "el", "la", "los", "las",
    "un", "una", "unos", "unas", "de", "del", "al", "a",
    "e", "y", "o", "u", "mi", "tu", "su", "nuestro", "vuestro",
    "me", "te", "se", "nos", "os", "lo", "le", "les",
    "más", "menos", "muy", "tan", "tanto", "demasiado",
    "algo", "nada", "todo", "siempre", "nunca", "quizás",
    "tal", "vez", "hay", "tiene", "tienen", "tenéis", "tenemos",
}


class MemoryRetriever(KnowledgeRetriever):
    """Implementación del KnowledgeRetriever usando la tabla `memories`."""

    def __init__(self, db: Session):
        self.db = db

    def retrieve(self, bot_id: int, question: str, top_k: int = 5) -> KnowledgeResult:
        """Busca memorias relevantes por keyword + matching difuso."""

        # Obtener todas las memorias confirmadas del bot
        memories = self.db.query(Memory).filter(
            Memory.bot_id == bot_id,
            Memory.is_confirmed == True
        ).all()

        if not memories:
            return KnowledgeResult(items=[], confidence=0.0, source_type="memory")

        question_lower = question.lower()
        question_words = set(question_lower.split())

        items: list[KnowledgeItem] = []

        for memory in memories:
            score = self._score_memory(memory, question_lower, question_words)
            if score > 0:
                items.append(KnowledgeItem(
                    content=memory.fact,
                    keyword=memory.keyword,
                    source_id=f"memory:{memory.id}",
                    category=str(memory.category_id) if memory.category_id else None,
                    score=score,
                    metadata={"memory_id": memory.id},
                ))

        # Ordenar por score descendente
        items.sort(key=lambda i: i.score, reverse=True)
        items = items[:top_k]

        if not items:
            return KnowledgeResult(items=[], confidence=0.0, source_type="memory")

        # Confianza normalizada (score máximo / 10, cap a 1.0)
        confidence = min(items[0].score / 10.0, 1.0)

        return KnowledgeResult(
            items=items,
            confidence=confidence,
            source_type="memory",
        )

    def _score_memory(self, memory: Memory, question_lower: str, question_words: set) -> float:
        """Calcula el score de una memoria frente a una pregunta."""
        score = 0.0
        keywords = [k.strip().lower() for k in memory.keyword.split(",")]

        for keyword in keywords:
            # Coincidencia directa de keyword en la pregunta
            if keyword in question_lower:
                score += len(keyword)

            # Matching difuso palabra por palabra
            for word in question_words:
                if word in STOPWORDS:
                    continue
                if keyword in word or word in keyword:
                    score += min(len(keyword), len(word)) * 0.5

        return score
