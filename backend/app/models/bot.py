from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal


# ============================================================
# BOT — CREAR
# ============================================================

class BotCreate(BaseModel):
    """Modelo para crear un nuevo bot (universal, no específico de nicho)."""
    name: str
    description: Optional[str] = None

    # Negocio (opcional)
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    nicho_id: Optional[str] = "otro"

    # Propósito
    goal: Optional[str] = None
    instructions: Optional[str] = None

    # Personalidad
    personality: Optional[str] = None
    tone: Optional[str] = None

    # Comportamiento
    greeting: Optional[str] = None
    fallback_message: Optional[str] = None
    answer_mode: Literal["strict", "flexible"] = "strict"

    # Compatibilidad (deprecados)
    owner_email: Optional[str] = None   # DEPRECATED


# ============================================================
# BOT — ACTUALIZAR
# ============================================================

class BotUpdate(BaseModel):
    """Modelo para actualizar un bot (todos los campos opcionales)."""
    name: Optional[str] = None
    description: Optional[str] = None

    business_name: Optional[str] = None
    business_type: Optional[str] = None
    nicho_id: Optional[str] = None

    goal: Optional[str] = None
    instructions: Optional[str] = None

    personality: Optional[str] = None
    tone: Optional[str] = None

    greeting: Optional[str] = None
    fallback_message: Optional[str] = None
    answer_mode: Optional[Literal["strict", "flexible"]] = None

    is_published: Optional[bool] = None
    is_active: Optional[bool] = None


# ============================================================
# BOT — RESPUESTA
# ============================================================

class BotResponse(BaseModel):
    """Modelo para responder con datos del bot."""
    id: int
    user_id: Optional[int] = None
    name: str
    description: Optional[str] = None

    business_name: Optional[str] = None
    business_type: Optional[str] = None
    nicho_id: Optional[str] = "otro"

    goal: Optional[str] = None
    instructions: Optional[str] = None

    personality: Optional[str] = None
    tone: Optional[str] = None

    greeting: Optional[str] = None
    fallback_message: Optional[str] = None
    answer_mode: str = "strict"

    is_published: bool = False
    is_active: bool = True
    plan: str = "free"

    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# BOT — RESPUESTA PÚBLICA (widget)
# ============================================================

class BotPublicResponse(BaseModel):
    """Datos públicos del bot (sin información sensible)."""
    id: int
    name: str
    description: Optional[str] = None
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    nicho_id: Optional[str] = "otro"
    greeting: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True


# ============================================================
# MEMORY
# ============================================================

class MemoryCreate(BaseModel):
    """Modelo para añadir una memoria al bot."""
    bot_id: int
    fact: str
    keyword: str
    category_id: Optional[int] = None
    source: Literal["manual", "suggested", "imported"] = "manual"
    is_confirmed: bool = True


class MemoryResponse(BaseModel):
    """Modelo para responder con una memoria."""
    id: int
    bot_id: int
    category_id: Optional[int] = None
    fact: str
    keyword: str
    source: str = "manual"
    is_confirmed: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# MEMORY CATEGORY
# ============================================================

class CategoryCreate(BaseModel):
    """Modelo para crear una categoría."""
    bot_id: int
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    order: int = 0


class CategoryUpdate(BaseModel):
    """Modelo para actualizar una categoría."""
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    order: Optional[int] = None


class CategoryResponse(BaseModel):
    """Modelo para responder con una categoría."""
    id: int
    bot_id: int
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    order: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# ASK — PREGUNTAS AL BOT
# ============================================================

class AskRequest(BaseModel):
    """Modelo para hacer una pregunta al bot."""
    bot_id: int
    question: str
    session_id: Optional[str] = None


class AskResponse(BaseModel):
    """Modelo para la respuesta del bot."""
    answer: str
    found: bool
