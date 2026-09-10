"""
Schemas Pydantic para el Knowledge Engine 2.0.
Solo define los contratos de entrada/salida para /sources/.
La lógica de procesamiento está en otro sitio (14.3.2+).
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal, Any


# ============================================================
# TIPOS Y ESTADOS
# ============================================================

SourceType = Literal["text", "url", "pdf", "csv"]
SourceStatus = Literal["pending", "processing", "ready", "failed"]


# ============================================================
# SOURCE — CREAR
# ============================================================

class SourceCreateText(BaseModel):
    """Crear fuente de texto plano."""
    bot_id: int
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)


class SourceCreateURL(BaseModel):
    """Crear fuente desde URL."""
    bot_id: int
    title: Optional[str] = Field(None, max_length=200)
    url: str = Field(..., min_length=1)


# ============================================================
# SOURCE — RESPUESTA
# ============================================================

class SourceResponse(BaseModel):
    """Respuesta con datos de una fuente."""
    id: int
    bot_id: int
    user_id: int
    type: SourceType
    title: str
    origin: Optional[str] = None
    status: SourceStatus
    error_message: Optional[str] = None
    chunks_count: int = 0
    size_bytes: Optional[int] = None
    meta: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SourceDetailResponse(SourceResponse):
    """Respuesta con detalle completo (incluye content_raw)."""
    content_raw: Optional[str] = None


class SourceListResponse(BaseModel):
    """Respuesta con lista de fuentes."""
    sources: list[SourceResponse]
    total: int


# ============================================================
# SOURCE CHUNK — RESPUESTA
# ============================================================

class SourceChunkResponse(BaseModel):
    """Respuesta con datos de un chunk."""
    id: int
    source_id: int
    bot_id: int
    chunk_index: int
    content: str
    section: Optional[str] = None
    page: Optional[int] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    tokens_estimate: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SourceChunksListResponse(BaseModel):
    """Respuesta con lista de chunks de una fuente."""
    source_id: int
    chunks: list[SourceChunkResponse]
    total: int


# ============================================================
# RESPUESTAS GENÉRICAS
# ============================================================

class SourceActionResponse(BaseModel):
    """Respuesta genérica para acciones sobre fuentes."""
    success: bool
    message: str
    source_id: Optional[int] = None
    metadata: Optional[dict[str, Any]] = None
