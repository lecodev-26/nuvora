"""
Nuvora Core — Interfaz abstracta del KnowledgeRetriever.
El Core NUNCA habla directamente con la tabla Memory.
Siempre a través de un KnowledgeRetriever.

Implementaciones:
- MemoryRetriever (actual, basado en tabla memories)
- SourceRetriever (Fase 14.3, basado en fuentes: PDFs, URLs, etc.)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class KnowledgeItem:
    """Un fragmento de conocimiento recuperado."""
    content: str
    keyword: Optional[str] = None
    source_id: Optional[str] = None       # Ej: "memory:42", "pdf:3:chunk_5"
    category: Optional[str] = None
    score: float = 0.0
    metadata: dict = field(default_factory=dict)


@dataclass
class KnowledgeResult:
    """Resultado de una búsqueda de conocimiento."""
    items: list[KnowledgeItem] = field(default_factory=list)
    confidence: float = 0.0
    source_type: str = "memory"  # memory | source | mixed
    metadata: dict = field(default_factory=dict)

    def is_empty(self) -> bool:
        return len(self.items) == 0

    def best(self) -> Optional[KnowledgeItem]:
        if not self.items:
            return None
        return max(self.items, key=lambda i: i.score)


class KnowledgeRetriever(ABC):
    """
    Interfaz abstracta del KnowledgeRetriever.
    Cualquier implementación debe devolver un KnowledgeResult.
    """

    @abstractmethod
    def retrieve(self, bot_id: int, question: str, top_k: int = 5) -> KnowledgeResult:
        """
        Recupera conocimiento relevante para una pregunta dada.

        Args:
            bot_id: ID del bot
            question: Pregunta del usuario
            top_k: Número máximo de resultados

        Returns:
            KnowledgeResult con los items encontrados
        """
        pass
