"""
Nuvora Core — Orchestrator
Coordina el flujo completo de procesamiento de un mensaje entrante.

Flujo:
1. Cargar bot
2. [Futuro] Detectar workflow activo (Fase 14.5)
3. Recuperar conocimiento
4. Construir respuesta
5. Aplicar personalidad
6. Persistir conversación
7. Devolver ChannelResponse

IMPORTANTE:
- No conoce ningún canal específico (widget, Telegram, etc.)
- No conoce la lógica de ningún nicho específico
- Solo trabaja con contratos universales
"""

from sqlalchemy.orm import Session
from app.core.contracts import ChannelRequest, ChannelResponse
from app.core.bot_loader import load_bot, BotNotFoundError, BotInactiveError
from app.core.knowledge_retriever import KnowledgeRetriever
from app.core.memory_retriever import MemoryRetriever
from app.core.response_builder import ResponseBuilder
from app.core.personality_filter import PersonalityFilter
from app.models.db_models import Conversation


class Orchestrator:

    def __init__(self, db: Session):
        self.db = db

    def _get_retriever(self) -> KnowledgeRetriever:
        """
        Devuelve el KnowledgeRetriever adecuado.
        En Fase 14.1 solo existe MemoryRetriever.
        En Fase 14.3 se añadirá SourceRetriever (y posiblemente un híbrido).
        """
        return MemoryRetriever(self.db)

    def process(self, request: ChannelRequest) -> ChannelResponse:
        """
        Procesa un mensaje entrante y devuelve la respuesta.
        """
        # 1. Cargar bot
        try:
            bot = load_bot(self.db, request.bot_id)
        except BotNotFoundError:
            return ChannelResponse(
                answer="Bot no encontrado.",
                found=False,
                metadata={"error": "bot_not_found"},
            )
        except BotInactiveError:
            return ChannelResponse(
                answer="Este asistente está temporalmente inactivo.",
                found=False,
                metadata={"error": "bot_inactive"},
            )

        # 2. [Futuro] Detectar workflow activo (Fase 14.5)
        # workflow_response = workflow_dispatcher.dispatch(bot, request)
        # if workflow_response:
        #     return workflow_response

        # 3. Recuperar conocimiento
        retriever = self._get_retriever()
        knowledge = retriever.retrieve(bot.id, request.message)

        # 4. Construir respuesta
        builder = ResponseBuilder()
        response = builder.build(bot, knowledge, request.message)

        # 5. Aplicar personalidad
        filter_ = PersonalityFilter()
        response = filter_.apply(bot, response)

        # 6. Persistir conversación
        self._save_conversation(bot, request, response)

        return response

    def _save_conversation(
        self,
        bot,
        request: ChannelRequest,
        response: ChannelResponse,
    ):
        """Guarda la conversación en la base de datos (para analytics)."""
        try:
            conv = Conversation(
                bot_id=bot.id,
                channel=request.channel or "widget",
                session_id=request.session_id,
                question=request.message,
                answer=response.answer,
                was_answered=response.found,
                workflow_id=None,
                meta=None,
            )
            self.db.add(conv)
            self.db.commit()
        except Exception as e:
            # No rompemos la respuesta por un fallo de analytics
            print(f"⚠️ Error guardando conversación: {e}")
            self.db.rollback()
