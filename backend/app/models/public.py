"""
Nuvora — Schemas Pydantic de Publicación Universal (Fase 14.9)
================================================================
Contratos de entrada/salida para los endpoints de publicación.

DISEÑO:
    - Privados (JWT): publish, unpublish, get/put publication
    - Públicos (sin JWT): get bot info, session, message

REGLA DE ORO:
    - public_config es SOLO visual/textos.
    - NUNCA contiene workflow_id, provider, system_prompt, etc.
    - El visitante NUNCA recibe datos internos (nodes, variables, keys, owner).
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Literal
import re


# ============================================================
# PUBLIC CONFIG (solo visual/textos)
# ============================================================

HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


class PublicationConfig(BaseModel):
    """
    Configuración visual/textos del bot publicado.

    REGLA: SOLO apariencia y textos públicos.
    NO workflow_id, NO provider, NO system_prompt.
    """
    welcome_message: Optional[str] = Field(
        None, max_length=500,
        description="Mensaje de bienvenida (máx 500 chars)"
    )
    placeholder: Optional[str] = Field(
        None, max_length=100,
        description="Placeholder del input (máx 100 chars)"
    )
    avatar_url: Optional[str] = Field(
        None, max_length=500,
        description="URL del avatar (máx 500 chars)"
    )
    primary_color: Optional[str] = Field(
        None,
        description="Color principal en formato #RRGGBB"
    )
    show_branding: bool = Field(
        True,
        description="Mostrar 'Powered by Nuvora' al pie"
    )

    @field_validator("primary_color")
    @classmethod
    def _validate_color(cls, v):
        if v is None:
            return v
        if not HEX_COLOR_RE.match(v):
            raise ValueError("primary_color debe ser #RRGGBB (ej: #7B5CFF)")
        return v


# ============================================================
# PUBLICACIÓN — RESPUESTAS PRIVADAS (JWT)
# ============================================================

class PublicationResponse(BaseModel):
    """Estado de publicación de un bot (respuesta privada)."""
    bot_id: int
    is_published: bool = False
    public_id: Optional[str] = None
    public_slug: Optional[str] = None
    published_at: Optional[datetime] = None
    public_url: Optional[str] = Field(
        None,
        description="URL pública completa (calculada por el backend)"
    )
    config: Optional[PublicationConfig] = None

    class Config:
        from_attributes = True


class PublicationUpdate(BaseModel):
    """Payload para actualizar la configuración de publicación (PUT)."""
    config: PublicationConfig


class PublishResponse(BaseModel):
    """Respuesta de POST /bots/{id}/publish."""
    bot_id: int
    is_published: bool
    public_id: str
    public_slug: Optional[str] = None
    published_at: datetime
    public_url: str

    class Config:
        from_attributes = True


# ============================================================
# PUBLIC — RESPUESTAS SIN JWT
# ============================================================

class PublicBotInfo(BaseModel):
    """
    Información pública de un bot publicado.
    Endpoint: GET /public/bots/{public_id}
    """
    public_id: str
    name: str
    description: Optional[str] = None
    nicho_id: Optional[str] = "otro"
    business_name: Optional[str] = None
    config: PublicationConfig

    class Config:
        from_attributes = True


class PublicSessionCreateRequest(BaseModel):
    """Payload para crear una sesión anónima (POST /session)."""
    # Sin campos por ahora — el servidor genera el public_id de la sesión.
    # Se deja el schema por consistencia y por si en el futuro se añade algo.
    pass


class PublicSessionResponse(BaseModel):
    """Respuesta de creación de sesión."""
    session_id: str
    bot_public_id: str
    expires_at: datetime

    class Config:
        from_attributes = True


class PublicMessageRequest(BaseModel):
    """Payload para enviar un mensaje al bot publicado (POST /message)."""
    session_id: str = Field(..., min_length=1, max_length=64)
    message: str = Field(..., min_length=1, max_length=2000)


class PublicMessageResponse(BaseModel):
    """Respuesta pública del bot."""
    reply: str
    session_id: str
    status: Literal["completed", "waiting_input", "error"] = "completed"
    variables_public: Optional[dict] = Field(
        None,
        description="Variables que el workflow quiera exponer (opcional)"
    )


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "PublicationConfig",
    "PublicationResponse",
    "PublicationUpdate",
    "PublishResponse",
    "PublicBotInfo",
    "PublicSessionCreateRequest",
    "PublicSessionResponse",
    "PublicMessageRequest",
    "PublicMessageResponse",
]
