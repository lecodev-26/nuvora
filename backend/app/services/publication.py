"""
Nuvora — Servicio de Publicación (Fase 14.9)
==============================================
Utilidades para publicar bots:
    - generate_public_id():    UUID v4 (identidad técnica)
    - slugify(name):           convierte texto a slug
    - generate_public_slug():  slug único (con sufijo si colisiona)
    - build_public_url():      URL pública completa

REGLAS:
    - public_id: inmutable, único global, no enumerable.
    - public_slug: humano, opcional, único global.
    - Si el slug ya existe → sufijo numérico (-2, -3, ...).
    - Sin dependencias externas (solo stdlib + SQLAlchemy).
"""

import re
import uuid
import unicodedata
from typing import Optional

from sqlalchemy.orm import Session

from app.models.db_models import Bot


# ============================================================
# CONSTANTES
# ============================================================

PUBLIC_BASE_URL = "https://nuvora-chi.vercel.app/b"
SLUG_MIN_LENGTH = 3
SLUG_MAX_LENGTH = 80
SLUG_SUFFIX_MAX = 100  # máximo intentos de sufijo


# ============================================================
# PUBLIC ID
# ============================================================

def generate_public_id() -> str:
    """
    Genera un public_id único (UUID v4).

    Garantía: no enumerable, 122 bits de entropía.
    Ejemplo: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    """
    return str(uuid.uuid4())


# ============================================================
# SLUGIFY
# ============================================================

def slugify(text: str) -> str:
    """
    Convierte texto a slug:
        "Clínica Salud Madrid" → "clinica-salud-madrid"
        "Café Ñandú" → "cafe-nandu"
        "  ---Hello---  " → "hello"

    Reglas:
        - minúsculas
        - quita acentos (NFKD → ASCII)
        - solo [a-z0-9-]
        - colapsa guiones repetidos
        - quita guiones al inicio/final
    """
    if not text:
        return ""

    # NFKD: descompone caracteres compuestos (é → e + ´)
    # Y luego filtra solo ASCII alfanuméricos
    normalized = unicodedata.normalize("NFKD", text)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")

    # minúsculas
    lower = ascii_only.lower()

    # sustituir todo lo que no sea [a-z0-9] por guion
    dashed = re.sub(r"[^a-z0-9]+", "-", lower)

    # colapsar guiones y limpiar extremos
    clean = re.sub(r"-+", "-", dashed).strip("-")

    return clean


def _resize_slug(slug: str, max_len: int = SLUG_MAX_LENGTH) -> str:
    """Recorta un slug a max_len, sin cortar a mitad de palabra."""
    if len(slug) <= max_len:
        return slug
    cut = slug[:max_len]
    if "-" in cut:
        cut = cut.rsplit("-", 1)[0]
    return cut.strip("-")


# ============================================================
# PUBLIC SLUG (único)
# ============================================================

def _slug_exists(db: Session, slug: str) -> bool:
    """¿Existe ya un bot con ese public_slug?"""
    return db.query(Bot).filter(Bot.public_slug == slug).first() is not None


def generate_public_slug(
    name: str,
    db: Session,
    max_length: int = SLUG_MAX_LENGTH,
) -> str:
    """
    Genera un public_slug único a partir del nombre del bot.

    Si "clinica-salud" ya existe:
        → "clinica-salud-2"
        → "clinica-salud-3"
        → ...

    Si el nombre no produce slug válido (vacío, solo símbolos, demasiado corto):
        → usa "bot-XXXXXX" (fallback con UUID corto).

    Args:
        name: nombre del bot (ej: "Clínica Salud")
        db: sesión SQLAlchemy para comprobar colisiones
        max_length: longitud máxima del slug (default 80)

    Returns:
        str: slug único y human-readable.
    """
    # 1. Slug base
    base = slugify(name or "")
    base = _resize_slug(base, max_length - 10)  # reservar espacio para sufijo

    # 2. Si no llega al mínimo → fallback
    if len(base) < SLUG_MIN_LENGTH:
        short_uuid = uuid.uuid4().hex[:6]
        base = f"bot-{short_uuid}"

    # 3. Si no existe → directo
    if not _slug_exists(db, base):
        return base

    # 4. Buscar sufijo libre
    for i in range(2, SLUG_SUFFIX_MAX + 1):
        candidate = f"{base}-{i}"
        if len(candidate) > max_length:
            candidate = _resize_slug(base, max_length - len(str(i)) - 1)
            candidate = f"{candidate}-{i}"
        if not _slug_exists(db, candidate):
            return candidate

    # 5. Fallback extremo (improbable)
    return f"{base}-{uuid.uuid4().hex[:8]}"


# ============================================================
# URL PÚBLICA
# ============================================================

def build_public_url(
    public_id: str,
    public_slug: Optional[str] = None,
) -> str:
    """
    Construye la URL pública del bot.

    Prioridad:
        1. Si hay public_slug → /b/{slug}
        2. Si no → /b/{public_id}

    Ejemplo:
        build_public_url("abc-123", "clinica-salud")
        → "https://nuvora-chi.vercel.app/b/clinica-salud"

        build_public_url("abc-123", None)
        → "https://nuvora-chi.vercel.app/b/abc-123"
    """
    identifier = public_slug or public_id
    return f"{PUBLIC_BASE_URL}/{identifier}"


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "generate_public_id",
    "slugify",
    "generate_public_slug",
    "build_public_url",
    "PUBLIC_BASE_URL",
    "SLUG_MIN_LENGTH",
    "SLUG_MAX_LENGTH",
]
