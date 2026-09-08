from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BotCreate(BaseModel):
    """Modelo para crear un nuevo bot"""
    name: str
    restaurant_name: str
    owner_email: str

class BotResponse(BaseModel):
    """Modelo para responder con datos del bot"""
    id: int
    name: str
    restaurant_name: str
    owner_email: str
    created_at: datetime
    plan: str = "free"

class MemoryCreate(BaseModel):
    """Modelo para añadir memoria al bot"""
    bot_id: int
    fact: str  # El hecho que aprende el bot
    keyword: str  # Palabra clave para buscar
