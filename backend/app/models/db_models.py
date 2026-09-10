from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.database.config import Base


# ============================================================
# USERS
# ============================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    full_name = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Integer, default=1)

    # Nuvora Service Fields
    trial_start = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    service_status = Column(String(20), default="trial")
    payment_date = Column(DateTime(timezone=True), nullable=True)
    expiration_date = Column(DateTime(timezone=True), nullable=True)
    stripe_customer_id = Column(String(100), nullable=True)

    def __repr__(self):
        return f"<User {self.id}: {self.email}>"


# ============================================================
# BOTS (Nuvora Core Universal)
# ============================================================

class Bot(Base):
    __tablename__ = "bots"

    # --- Identidad ---
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # NUEVO: FK real
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # --- Negocio (OPCIONAL) ---
    business_name = Column(String(200), nullable=True)   # NUEVO: reemplaza restaurant_name (nullable)
    business_type = Column(String(50), nullable=True)    # NUEVO: tipo de negocio libre
    nicho_id = Column(String(50), nullable=True, default="otro")  # Plantilla opcional

    # --- Compatibilidad (deprecados, se mantienen 1 fase) ---
    restaurant_name = Column(String(200), nullable=True)  # DEPRECATED: usar business_name
    owner_email = Column(String(100), nullable=True, index=True)  # DEPRECATED: usar user_id

    # --- Propósito ---
    goal = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)

    # --- Personalidad (FLEXIBLE, sin enums) ---
    personality = Column(String(100), nullable=True)
    tone = Column(String(100), nullable=True)

    # --- Comportamiento ---
    greeting = Column(Text, nullable=True)
    fallback_message = Column(Text, nullable=True)
    answer_mode = Column(String(20), default="strict")  # strict | flexible

    # --- Control ---
    is_published = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    plan = Column(String(20), default="free")

    # --- Metadata ---
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Bot {self.id}: {self.name}>"


# ============================================================
# MEMORY CATEGORIES
# ============================================================

class MemoryCategory(Base):
    __tablename__ = "memory_categories"

    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(10), nullable=True)
    order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<MemoryCategory {self.id}: {self.name} (bot={self.bot_id})>"


# ============================================================
# MEMORIES
# ============================================================

class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("memory_categories.id"), nullable=True, index=True)  # NUEVO
    fact = Column(Text, nullable=False)
    keyword = Column(String(100), nullable=False)
    source = Column(String(20), default="manual")  # NUEVO: manual | suggested | imported
    is_confirmed = Column(Boolean, default=True)   # NUEVO: True = conocimiento confirmado
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Memory {self.id}: {self.keyword} -> {self.fact[:50]}...>"


# ============================================================
# CONVERSATIONS
# ============================================================

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False, index=True)
    channel = Column(String(30), default="widget")  # NUEVO: widget | link | telegram | ...
    session_id = Column(String(100), nullable=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    was_answered = Column(Boolean, default=False)
    workflow_id = Column(Integer, nullable=True)  # NUEVO: preparado para Fase 14.5
    meta = Column(Text, nullable=True)  # NUEVO: JSON opcional (reservado para futuro)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Conversation {self.id}: bot={self.bot_id} answered={self.was_answered}>"
