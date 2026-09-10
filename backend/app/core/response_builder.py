"""
Nuvora Core — Response Builder
Construye la respuesta final a partir del conocimiento recuperado.
NO conoce la lógica específica de ningún nicho.
"""

from app.core.bot_loader import LoadedBot
from app.core.knowledge_retriever import KnowledgeResult
from app.core.contracts import ChannelResponse


# Umbral mínimo de score para considerar que hay respuesta
# (mismo umbral que usaba el sistema anterior, para compatibilidad)
MIN_SCORE = 2.0


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
        - Si hay conocimiento con score >= MIN_SCORE → responder con él
        - Si no → responder con el fallback del bot (o el genérico)
        - El modo `strict` mantiene la regla de no inventar
        - El modo `flexible` permite responder con el mejor match aunque sea flojo
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

        # Modo strict: exigir score mínimo
        if bot.answer_mode == "strict" and best.score < MIN_SCORE:
            return ChannelResponse(
                answer=bot.fallback_message,
                found=False,
                metadata={
                    "answer_mode": "strict",
                    "confidence": best.score,
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
                "confidence": best.score,
                "source_type": knowledge.source_type,
                "source_id": best.source_id,
            },
        )
