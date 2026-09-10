"""
Nuvora Core — Personality Filter
Aplica personalidad, tono e instrucciones a la respuesta final.
No conoce la lógica específica de ningún nicho.
"""

from app.core.bot_loader import LoadedBot
from app.core.contracts import ChannelResponse


class PersonalityFilter:
    """
    Filtro de personalidad.

    En la Fase 14.1 este filtro es DELIBERADAMENTE SIMPLE.
    NO aplica IA ni servicios externos.
    Solo:
    - Conserva la respuesta tal cual (strict)
    - En el futuro podrá adaptar tono/personalidad sin IA obligatoria
    """

    def apply(self, bot: LoadedBot, response: ChannelResponse) -> ChannelResponse:
        """
        Aplica la personalidad del bot a la respuesta.

        Reglas actuales (Fase 14.1):
        - No modifica el contenido factual de la respuesta
        - Solo añade metadata de personalidad para uso futuro
        """
        if not response.answer:
            return response

        # Añadir metadata de personalidad (sin modificar el texto)
        if response.metadata is None:
            response.metadata = {}

        response.metadata["personality"] = bot.personality
        response.metadata["tone"] = bot.tone

        # En fases futuras, aquí se aplicará el tono real
        # (sin LLM obligatorio — puede ser reglas + plantillas)

        return response
