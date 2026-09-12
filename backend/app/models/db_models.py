from sqlalchemy import (
    Column, Integer, String, DateTime, Text, Boolean, ForeignKey, UniqueConstraint,
)
from sqlalchemy.orm import relationship
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

    trial_start = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    service_status = Column(String(20), default="trial")
    payment_date = Column(DateTime(timezone=True), nullable=True)
    expiration_date = Column(DateTime(timezone=True), nullable=True)
    stripe_customer_id = Column(String(100), nullable=True)

    def __repr__(self):
        return f"<User {self.id}: {self.email}>"


# ============================================================
# BOTS
# ============================================================

class Bot(Base):
    __tablename__ = "bots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    business_name = Column(String(200), nullable=True)
    business_type = Column(String(50), nullable=True)
    nicho_id = Column(String(50), nullable=True, default="otro")

    restaurant_name = Column(String(200), nullable=True)
    owner_email = Column(String(100), nullable=True, index=True)

    goal = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)

    personality = Column(String(100), nullable=True)
    tone = Column(String(100), nullable=True)

    greeting = Column(Text, nullable=True)
    fallback_message = Column(Text, nullable=True)
    answer_mode = Column(String(20), default="strict")

    is_published = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    plan = Column(String(20), default="free")

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
    category_id = Column(Integer, ForeignKey("memory_categories.id"), nullable=True, index=True)
    fact = Column(Text, nullable=False)
    keyword = Column(String(100), nullable=False)
    source = Column(String(20), default="manual")
    is_confirmed = Column(Boolean, default=True)
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
    channel = Column(String(30), default="widget")
    session_id = Column(String(100), nullable=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    was_answered = Column(Boolean, default=False)
    workflow_id = Column(Integer, nullable=True)
    meta = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Conversation {self.id}: bot={self.bot_id} answered={self.was_answered}>"


# ============================================================
# SOURCES
# ============================================================

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    type = Column(String(20), nullable=False)
    title = Column(String(200), nullable=False)
    origin = Column(Text, nullable=True)
    content_raw = Column(Text, nullable=True)
    content_processed = Column(Text, nullable=True)

    status = Column(String(20), nullable=False, default="pending")
    error_message = Column(Text, nullable=True)
    chunks_count = Column(Integer, nullable=False, default=0)

    size_bytes = Column(Integer, nullable=True)
    meta = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Source {self.id}: {self.type} '{self.title}' (bot={self.bot_id}, status={self.status})>"


# ============================================================
# SOURCE CHUNKS
# ============================================================

class SourceChunk(Base):
    __tablename__ = "source_chunks"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id", ondelete="CASCADE"), nullable=False, index=True)

    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    section = Column(String(200), nullable=True)
    page = Column(Integer, nullable=True)
    char_start = Column(Integer, nullable=True)
    char_end = Column(Integer, nullable=True)
    tokens_estimate = Column(Integer, nullable=True)

    meta = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<SourceChunk {self.id}: source={self.source_id} idx={self.chunk_index}>"


# ============================================================
# WORKFLOWS (Fase 14.5)
# ============================================================

class Workflow(Base):
    """
    Definición estática de un workflow asociado a un bot.

    Estados:
        - draft: borrador, no ejecutable en producción
        - active: workflow listo para ejecutarse
        - archived: workflow retirado
    """
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(
        Integer,
        ForeignKey("bots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="draft")  # draft | active | archived
    version = Column(Integer, default=1)
    trigger = Column(String(50), default="manual")  # manual | message | keyword
    entry_node_id = Column(String(50), nullable=True)  # ID del nodo START
    meta = Column(Text, nullable=True)  # JSON serializado para metadata

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relaciones ORM
    nodes = relationship(
        "WorkflowNode",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="WorkflowNode.id",
    )
    transitions = relationship(
        "WorkflowTransition",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="WorkflowTransition.order",
    )

    def __repr__(self):
        return f"<Workflow {self.id}: '{self.name}' (bot={self.bot_id}, status={self.status})>"


class WorkflowNode(Base):
    """
    Nodo individual dentro de un workflow.

    El campo `config` es JSON serializado en TEXT (por compatibilidad
    SQLite ↔ PostgreSQL, igual que el campo `meta` de otras tablas).

    El campo `node_id` es un identificador lógico único DENTRO del
    workflow (ej: "start_1", "ask_name", "check_age"). NO es el PK.
    """
    __tablename__ = "workflow_nodes"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(
        Integer,
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    node_id = Column(String(50), nullable=False, index=True)
    type = Column(String(30), nullable=False)  # start|message|question|condition|variable|response|end
    name = Column(String(200), nullable=True)
    config = Column(Text, nullable=True)  # JSON serializado

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relación inversa
    workflow = relationship("Workflow", back_populates="nodes")

    __table_args__ = (
        UniqueConstraint("workflow_id", "node_id", name="uq_workflow_node"),
    )

    def __repr__(self):
        return f"<WorkflowNode {self.id}: {self.node_id} ({self.type})>"


class WorkflowTransition(Base):
    """
    Transición entre dos nodos de un workflow.

    - `condition`: expresión opcional. Si es None, la transición es
      "default" y aplica para nodos lineales.
    - `label`: etiqueta opcional ("true" / "false" / custom) útil para UI.
    - `order`: orden de evaluación cuando hay varias transiciones desde
      el mismo nodo.
    """
    __tablename__ = "workflow_transitions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(
        Integer,
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_node_id = Column(String(50), nullable=False, index=True)
    to_node_id = Column(String(50), nullable=False)
    condition = Column(Text, nullable=True)
    label = Column(String(50), nullable=True)
    order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relación inversa
    workflow = relationship("Workflow", back_populates="transitions")

    def __repr__(self):
        return f"<WorkflowTransition {self.from_node_id} -> {self.to_node_id}>"


# ============================================================
# USER AI CONFIG (Fase 14.7.4b — BYOK)
# ============================================================

class UserAIConfig(Base):
    """
    Configuración de API key propia del usuario para un provider de IA.

    BYOK (Bring Your Own Key): el usuario puede traer su propia API key
    de Gemini, Groq o DeepSeek. Si la tiene, Nuvora la usa en lugar de
    la suya. Si no, se usa la del sistema.

    SEGURIDAD:
        - La API key se guarda CIFRADA (Fernet).
        - El campo `api_key_encrypted` contiene el ciphertext.
        - Nunca se devuelve la key al frontend (solo si existe o no).
    """
    __tablename__ = "user_ai_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider = Column(String(50), nullable=False)  # gemini | groq | deepseek
    api_key_encrypted = Column(Text, nullable=False)  # ciphertext Fernet

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_user_ai_config_provider"),
    )

    def __repr__(self):
        return f"<UserAIConfig user={self.user_id} provider={self.provider}>"

