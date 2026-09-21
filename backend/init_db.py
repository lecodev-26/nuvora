from app.database.config import engine, Base
from app.models.db_models import (
    Bot,
    Memory,
    User,
    Conversation,
    MemoryCategory,
    Source,
    SourceChunk,
    # Fase 14.11 - Telegram Channel
    TelegramIntegration,
    TelegramUpdate,
)

print("Creando tablas...")
Base.metadata.create_all(bind=engine)
print("Tablas creadas correctamente!")
