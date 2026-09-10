"""
Nuvora Core — Bot Loader
Carga el bot y su configuración desde la base de datos.
No conoce la lógica de negocio específica de ningún nicho.
"""

from sqlalchemy.orm import Session
from app.models.db_models import Bot


class BotNotFoundError(Exception):
    """Excepción lanzada cuando el bot no existe."""
    pass


class BotInactiveError(Exception):
    """Excepción lanzada cuando el bot está inactivo."""
    pass


class LoadedBot:
    """
    Representación del bot cargado por el Core.
    Incluye la configuración necesaria para procesar mensajes.
    """

    def __init__(self, bot: Bot):
        self.id = bot.id
        self.name = bot.name
        self.description = bot.description

        # Negocio (opcional)
        self.business_name = bot.business_name or bot.restaurant_name
        self.business_type = bot.business_type
        self.nicho_id = bot.nicho_id or "otro"

        # Propósito
        self.goal = bot.goal
        self.instructions = bot.instructions

        # Personalidad
        self.personality = bot.personality
        self.tone = bot.tone

        # Comportamiento
        self.greeting = bot.greeting
        self.fallback_message = bot.fallback_message or (
            "No tengo esa información en mi memoria. "
            "Te recomiendo contactar directamente con el negocio."
        )
        self.answer_mode = bot.answer_mode or "strict"

        # Control
        self.is_active = bot.is_active if bot.is_active is not None else True
        self.is_published = bot.is_published if bot.is_published is not None else False

    def __repr__(self):
        return f"<LoadedBot {self.id}: {self.name}>"


def load_bot(db: Session, bot_id: int) -> LoadedBot:
    """
    Carga un bot por ID y lo envuelve en LoadedBot.
    Lanza BotNotFoundError o BotInactiveError si procede.
    """
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise BotNotFoundError(f"Bot {bot_id} no encontrado")

    loaded = LoadedBot(bot)

    if not loaded.is_active:
        raise BotInactiveError(f"Bot {bot_id} está inactivo")

    return loaded
