"""
Nuvora Core — Training Assistant: Analyzer
============================================
Orquesta el análisis del estado de preparación de un bot.

FASE 14.4.2 — SOLO ESQUELETO:
    - Carga bot, topics del nicho, counts de memories/sources.
    - Delega a stubs (coverage, scoring, questions, recommendations).
    - NO hace análisis real todavía.
    - NO hace consultas de conversations (eso es 14.4.4).

REGLA ARQUITECTÓNICA:
    - Sin lógica de nichos en el Core.
    - Separado del Core de respuestas.
    - Sin persistencia en BD.
"""

import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.db_models import Bot, Memory, Source, Conversation
from app.core.bot_loader import BotNotFoundError
from app.core.training.topics import get_nicho_catalog
from app.core.training.coverage import compute_coverage
from app.core.training.scoring import calculate_progress
from app.core.training.questions import get_unanswered_question_groups
from app.core.training.recommendations import generate_recommendations
from app.models.training import TrainingReport, TopicCoverageStatus


# Límite por defecto de conversaciones a analizar (14.4.4).
# En 14.4.2 no se usa, pero queda preparado.
DEFAULT_CONVERSATION_LIMIT = 100


class TrainingAnalyzer:
    """Analiza el estado de preparación de un bot."""

    def __init__(self, db: Session):
        self.db = db

    # ============================================================
    # API PÚBLICA
    # ============================================================

    def analyze(
        self,
        bot_id: int,
        conversation_limit: int = DEFAULT_CONVERSATION_LIMIT,
    ) -> TrainingReport:
        """
        Analiza el bot y devuelve un TrainingReport.

        Raises:
            BotNotFoundError: si el bot no existe.
        """
        start = time.monotonic()

        # 1. Cargar bot (404 si no existe)
        bot = self._load_bot(bot_id)

        # 2. Catálogo de topics del nicho
        #    Fallback a "otro" si nicho_id es None o desconocido.
        #    NO modificamos bot.nicho_id.
        catalog = get_nicho_catalog(bot.nicho_id)
        topics = list(catalog.topics)

        # 3. Contadores de conocimiento
        memories_count = self._count_memories(bot_id)
        ready_sources_count = self._count_ready_sources(bot_id)

        # 4. Cobertura (STUB en 14.4.2 → todos MISSING)
        coverages = compute_coverage(topics, bot_id, self.db)

        # 5. Progreso (STUB en 14.4.2 → 0.0)
        progress_data = calculate_progress(coverages)

        # 6. Preguntas sin responder (STUB en 14.4.2 → [])
        #    conversation_limit se pasa para cuando 14.4.4 lo implemente.
        question_groups = get_unanswered_question_groups(
            bot_id=bot_id,
            db=self.db,
            limit=conversation_limit,
        )

        # 7. Recomendaciones (STUB en 14.4.2 → [])
        recommendations = generate_recommendations(
            bot=bot,
            coverages=coverages,
            question_groups=question_groups,
        )

        # 8. Listas derivadas
        missing_topics = [
            c for c in coverages
            if c.status == TopicCoverageStatus.MISSING
        ]
        partial_topics = [
            c for c in coverages
            if c.status == TopicCoverageStatus.PARTIAL
        ]

        # 9. Construir reporte
        report = TrainingReport(
            bot_id=bot.id,
            bot_name=bot.name,
            nicho_id=bot.nicho_id,  # Puede ser None
            progress=progress_data["progress"],
            total_topics=len(coverages),
            covered_count=progress_data["covered_count"],
            partial_count=progress_data["partial_count"],
            missing_count=progress_data["missing_count"],
            topics=coverages,
            missing_topics=missing_topics,
            partial_topics=partial_topics,
            unanswered_questions=question_groups,
            recommendations=recommendations,
            analyzed_at=datetime.now(timezone.utc),
            has_memories=memories_count > 0,
            has_sources=ready_sources_count > 0,
            memories_count=memories_count,
            ready_sources_count=ready_sources_count,
            conversations_analyzed=0,  # STUB: 0 en 14.4.2
        )

        # 10. Log técnico mínimo (sin contenido sensible)
        duration_ms = int((time.monotonic() - start) * 1000)
        print(
            f"[TrainingAnalyzer] bot_id={bot_id} "
            f"topics={len(coverages)} "
            f"duration_ms={duration_ms}"
        )

        return report

    # ============================================================
    # CARGA DE DATOS
    # ============================================================

    def _load_bot(self, bot_id: int) -> Bot:
        """Carga un bot o lanza BotNotFoundError."""
        bot = self.db.query(Bot).filter(Bot.id == bot_id).first()
        if not bot:
            raise BotNotFoundError(f"Bot {bot_id} no encontrado")
        return bot

    def _count_memories(self, bot_id: int) -> int:
        """Cuenta las memorias del bot."""
        return self.db.query(Memory).filter(Memory.bot_id == bot_id).count()

    def _count_ready_sources(self, bot_id: int) -> int:
        """Cuenta las fuentes listas (status=ready) del bot."""
        return (
            self.db.query(Source)
            .filter(Source.bot_id == bot_id, Source.status == "ready")
            .count()
        )
