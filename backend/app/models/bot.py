from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BotCreate(BaseModel):
    """Modelo para crear un nuevo bot"""
    name: str
    restaurant_name: str
    owner_email: Optional[str] = None  # ← Ahora es opcional

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
    fact: str
    keyword: str
