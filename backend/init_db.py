from app.database.config import engine, Base
from app.models.db_models import (
    Bot,
    Memory,
    User,
    Conversation,
    MemoryCategory,
    Source,
    SourceChunk,
)

print("Creando tablas...")
Base.metadata.create_all(bind=engine)
print("Tablas creadas correctamente!")
