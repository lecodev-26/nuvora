"""
Schemas Pydantic para el Knowledge Engine 2.0.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal, Any


SourceType = Literal["text", "url", "pdf", "csv"]
SourceStatus = Literal["pending", "processing", "ready", "failed"]


class SourceCreateText(BaseModel):
    bot_id: int
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)


class SourceCreateURL(BaseModel):
    bot_id: int
    title: Optional[str] = Field(None, max_length=200)
    url: str = Field(..., min_length=1)


class SourceResponse(BaseModel):
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
    content_raw: Optional[str] = None
    content_processed: Optional[str] = None


class SourceListResponse(BaseModel):
    sources: list[SourceResponse]
    total: int


class SourceChunkResponse(BaseModel):
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
    source_id: int
    chunks: list[SourceChunkResponse]
    total: int


class SourceActionResponse(BaseModel):
    success: bool
    message: str
    source_id: Optional[int] = None
    metadata: Optional[dict[str, Any]] = None
