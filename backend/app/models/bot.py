from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BotCreate(BaseModel):
    """Modelo para crear un nuevo bot"""
    name: str
    restaurant_name: str
    owner_email: Optional[str] = None
    nicho_id: Optional[str] = "otro"

class BotUpdate(BaseModel):
    """Modelo para actualizar un bot"""
    name: Optional[str] = None
    restaurant_name: Optional[str] = None
    nicho_id: Optional[str] = None

class BotResponse(BaseModel):
    """Modelo para responder con datos del bot"""
    id: int
    name: str
    restaurant_name: str
    owner_email: str
    nicho_id: str = "otro"
    created_at: datetime
    plan: str = "free"

class MemoryCreate(BaseModel):
    """Modelo para añadir memoria al bot"""
    bot_id: int
    fact: str
    keyword: str

class AskRequest(BaseModel):
    """Modelo para hacer una pregunta al bot"""
    bot_id: int
    question: str
    session_id: Optional[str] = None

class AskResponse(BaseModel):
    """Modelo para la respuesta del bot"""
    answer: str
    found: bool
