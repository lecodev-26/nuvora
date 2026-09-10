"""
Nuvora Core — Router /sources/
================================
CRUD e ingesta de fuentes de conocimiento.
Todo el procesamiento es síncrono en 14.3.5.
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    Query,
)
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime

from app.database.config import get_db
from app.models.db_models import Bot, User, Source, SourceChunk
from app.models.source import (
    SourceCreateText,
    SourceCreateURL,
    SourceResponse,
    SourceDetailResponse,
    SourceListResponse,
    SourceChunkResponse,
    SourceChunksListResponse,
    SourceActionResponse,
)
from app.services.auth import get_current_user
from app.core.processors import (
    TextProcessor,
    URLProcessor,
    PDFProcessor,
    CSVProcessor,
    Chunker,
    ProcessorError,
)
from app.core.indexing import invalidate_index


router = APIRouter(prefix="/sources", tags=["sources"])


# ============================================================
# CONSTANTES
# ============================================================

MAX_SOURCES_PER_BOT = 20
MAX_PDF_UPLOAD_BYTES = 5 * 1024 * 1024    # 5 MB
MAX_CSV_UPLOAD_BYTES = 2 * 1024 * 1024    # 2 MB


# ============================================================
# HELPERS — Ownership
# ============================================================

def _verify_bot_ownership(bot: Bot, current_user: User):
    """Valida que el usuario es dueño del bot."""
    if bot.user_id is not None:
        if bot.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="No tienes permiso para modificar este bot")
        return
    if bot.owner_email != current_user.email:
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar este bot")


def _get_bot_or_404(db: Session, bot_id: int) -> Bot:
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")
    return bot


def _get_source_or_404(db: Session, source_id: int) -> Source:
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Fuente no encontrada")
    return source


def _check_source_limit(db: Session, bot_id: int):
    count = db.query(Source).filter(Source.bot_id == bot_id).count()
    if count >= MAX_SOURCES_PER_BOT:
        raise HTTPException(
            status_code=400,
            detail=f"Límite de {MAX_SOURCES_PER_BOT} fuentes por bot alcanzado",
        )


# ============================================================
# HELPERS — Procesamiento y guardado
# ============================================================

def _process_content(source_type: str, content, kwargs: dict = None) -> dict:
    """
    Procesa el contenido con el processor adecuado.
    Devuelve {"text": str, "meta": dict, "size_bytes": int}
    """
    kwargs = kwargs or {}
    if source_type == "text":
        proc = TextProcessor()
    elif source_type == "url":
        proc = URLProcessor()
    elif source_type == "pdf":
        proc = PDFProcessor()
    elif source_type == "csv":
        proc = CSVProcessor()
    else:
        raise HTTPException(status_code=400, detail=f"Tipo no soportado: {source_type}")

    result = proc.process(content, **kwargs)
    return {"text": result.text, "meta": result.meta, "size_bytes": result.size_bytes}


def _chunk_and_save(
    db: Session,
    source: Source,
    processed_text: str,
    *,
    replace_existing: bool = False,
):
    """
    Genera chunks a partir del texto procesado y los guarda en BD.

    Atómico:
        - Si replace_existing=True, los chunks antiguos SOLO se eliminan
          después de que los nuevos se hayan generado correctamente.
        - Si algo falla antes del commit, los antiguos permanecen intactos.
    """
    chunker = Chunker()
    new_chunks = chunker.chunk(processed_text)

    if not new_chunks:
        raise ValueError("No se generaron chunks del contenido")

    # 1. Construir objetos nuevos (aún NO tocan la BD)
    new_chunk_objects = []
    for c in new_chunks:
        new_chunk_objects.append(SourceChunk(
            source_id=source.id,
            bot_id=source.bot_id,
            chunk_index=c.chunk_index,
            content=c.content,
            section=c.section,
            page=c.page,
            char_start=c.char_start,
            char_end=c.char_end,
            tokens_estimate=c.tokens_estimate,
        ))

    # 2. Eliminar antiguos (si aplica) y crear nuevos en la misma transacción
    if replace_existing:
        db.query(SourceChunk).filter(SourceChunk.source_id == source.id).delete(
            synchronize_session=False
        )
    for obj in new_chunk_objects:
        db.add(obj)

    db.flush()  # Persistir chunks antes de actualizar contadores

    source.chunks_count = len(new_chunk_objects)
    source.status = "ready"
    source.error_message = None
    source.processed_at = datetime.utcnow()
    source.content_processed = processed_text

    db.commit()


def _mark_source_failed(db: Session, source: Source, error_msg: str):
    """
    Marca una Source como fallida sin destruir chunks existentes.
    """
    source.status = "failed"
    source.error_message = error_msg
    db.commit()


# ============================================================
# HELPERS — Reindexado
# ============================================================

def _reprocess_source(db: Session, source: Source):
    """
    Reindexa una Source atómicamente.
    Según el tipo:
      - text → content_raw
      - csv  → content_processed (ya es el texto estructurado)
      - pdf  → content_processed (ya es el texto extraído)
      - url  → origin (volver a hacer fetch)
    Lanza ValueError si los datos de entrada no son válidos.
    """
    if source.type == "text":
        content = source.content_raw
        if not content or not content.strip():
            raise ValueError("content_raw vacío para reindexar")
        processed = _process_content("text", content)
        _chunk_and_save(db, source, processed["text"], replace_existing=True)

    elif source.type in ("csv", "pdf"):
        if not source.content_processed or not source.content_processed.strip():
            raise ValueError(f"content_processed vacío para reindexar tipo {source.type}")
        _chunk_and_save(db, source, source.content_processed, replace_existing=True)

    elif source.type == "url":
        if not source.origin:
            raise ValueError("origin vacío para reindexar URL")
        processed = _process_content("url", source.origin)
        _chunk_and_save(db, source, processed["text"], replace_existing=True)

    else:
        raise ValueError(f"Tipo no soportado para reindexar: {source.type}")


# ============================================================
# ENDPOINTS — CREAR
# ============================================================

@router.post("/text", response_model=SourceResponse)
def create_text_source(
    payload: SourceCreateText,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bot = _get_bot_or_404(db, payload.bot_id)
    _verify_bot_ownership(bot, current_user)
    _check_source_limit(db, payload.bot_id)

    source = Source(
        bot_id=bot.id,
        user_id=current_user.id,
        type="text",
        title=payload.title,
        content_raw=payload.content,
        status="pending",
        chunks_count=0,
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    try:
        processed = _process_content("text", payload.content)
        source.size_bytes = processed["size_bytes"]
        _chunk_and_save(db, source, processed["text"])
        invalidate_index(bot.id)
    except (ProcessorError, ValueError) as e:
        _mark_source_failed(db, source, str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        _mark_source_failed(db, source, f"Error inesperado: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")

    db.refresh(source)
    return source


@router.post("/url", response_model=SourceResponse)
def create_url_source(
    payload: SourceCreateURL,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bot = _get_bot_or_404(db, payload.bot_id)
    _verify_bot_ownership(bot, current_user)
    _check_source_limit(db, payload.bot_id)

    title = payload.title or payload.url

    source = Source(
        bot_id=bot.id,
        user_id=current_user.id,
        type="url",
        title=title,
        origin=payload.url,
        status="pending",
        chunks_count=0,
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    try:
        processed = _process_content("url", payload.url)
        source.size_bytes = processed["size_bytes"]
        _chunk_and_save(db, source, processed["text"])
        invalidate_index(bot.id)
    except (ProcessorError, ValueError) as e:
        _mark_source_failed(db, source, str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        _mark_source_failed(db, source, f"Error inesperado: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")

    db.refresh(source)
    return source


@router.post("/pdf", response_model=SourceResponse)
async def create_pdf_source(
    bot_id: int = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)
    _check_source_limit(db, bot_id)

    raw = await _read_upload_file_with_limit(file, MAX_PDF_UPLOAD_BYTES)

    source = Source(
        bot_id=bot.id,
        user_id=current_user.id,
        type="pdf",
        title=title,
        origin=file.filename,
        status="pending",
        size_bytes=len(raw),
        chunks_count=0,
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    try:
        processed = _process_content("pdf", raw)
        _chunk_and_save(db, source, processed["text"])
        invalidate_index(bot.id)
    except (ProcessorError, ValueError) as e:
        _mark_source_failed(db, source, str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        _mark_source_failed(db, source, f"Error inesperado: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")

    db.refresh(source)
    return source


@router.post("/csv", response_model=SourceResponse)
async def create_csv_source(
    bot_id: int = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)
    _check_source_limit(db, bot_id)

    raw = await _read_upload_file_with_limit(file, MAX_CSV_UPLOAD_BYTES)

    source = Source(
        bot_id=bot.id,
        user_id=current_user.id,
        type="csv",
        title=title,
        origin=file.filename,
        status="pending",
        size_bytes=len(raw),
        chunks_count=0,
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    try:
        processed = _process_content("csv", raw)
        _chunk_and_save(db, source, processed["text"])
        invalidate_index(bot.id)
    except (ProcessorError, ValueError) as e:
        _mark_source_failed(db, source, str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        _mark_source_failed(db, source, f"Error inesperado: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")

    db.refresh(source)
    return source


# ============================================================
# HELPERS — Upload
# ============================================================

async def _read_upload_file_with_limit(file: UploadFile, max_bytes: int) -> bytes:
    """
    Lee un UploadFile en bloques, abortando si supera el límite.
    NO confía solo en Content-Length.
    """
    chunks = []
    total = 0
    while True:
        chunk = await file.read(1024 * 1024)  # 1 MB por iteración
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"Archivo demasiado grande (máx {max_bytes // (1024*1024)} MB)",
            )
        chunks.append(chunk)
    return b"".join(chunks)


# ============================================================
# ENDPOINTS — LISTAR
# ============================================================

@router.get("/list/{bot_id}", response_model=SourceListResponse)
def list_sources(
    bot_id: int,
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)

    q = db.query(Source).filter(Source.bot_id == bot_id)
    if status:
        q = q.filter(Source.status == status)

    total = q.count()
    sources = (
        q.order_by(desc(Source.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )

    return SourceListResponse(sources=sources, total=total)


@router.get("/{source_id}/detail", response_model=SourceDetailResponse)
def get_source_detail(
    source_id: int,
    include_chunks: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    source = _get_source_or_404(db, source_id)
    bot = _get_bot_or_404(db, source.bot_id)
    _verify_bot_ownership(bot, current_user)
    return source


@router.get("/{source_id}/chunks", response_model=SourceChunksListResponse)
def get_source_chunks(
    source_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    source = _get_source_or_404(db, source_id)
    bot = _get_bot_or_404(db, source.bot_id)
    _verify_bot_ownership(bot, current_user)

    chunks = (
        db.query(SourceChunk)
        .filter(SourceChunk.source_id == source_id)
        .order_by(SourceChunk.chunk_index)
        .all()
    )

    return SourceChunksListResponse(
        source_id=source_id,
        chunks=chunks,
        total=len(chunks),
    )


# ============================================================
# ENDPOINTS — ELIMINAR
# ============================================================

@router.delete("/{source_id}", response_model=SourceActionResponse)
def delete_source(
    source_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    source = _get_source_or_404(db, source_id)
    bot = _get_bot_or_404(db, source.bot_id)
    _verify_bot_ownership(bot, current_user)

    bot_id = source.bot_id
    db.delete(source)
    db.commit()
    invalidate_index(bot_id)

    return SourceActionResponse(
        success=True,
        message="Fuente eliminada",
        source_id=source_id,
    )


# ============================================================
# ENDPOINTS — REINDEXAR
# ============================================================

@router.post("/{source_id}/reindex", response_model=SourceResponse)
def reindex_source(
    source_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    source = _get_source_or_404(db, source_id)
    bot = _get_bot_or_404(db, source.bot_id)
    _verify_bot_ownership(bot, current_user)

    try:
        _reprocess_source(db, source)
        invalidate_index(bot.id)
    except (ProcessorError, ValueError) as e:
        _mark_source_failed(db, source, str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        _mark_source_failed(db, source, f"Error inesperado: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")

    db.refresh(source)
    return source


@router.post("/reindex-all/{bot_id}", response_model=SourceActionResponse)
def reindex_all_sources(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bot = _get_bot_or_404(db, bot_id)
    _verify_bot_ownership(bot, current_user)

    sources = db.query(Source).filter(Source.bot_id == bot_id).all()
    reindexed = 0
    failed = 0

    for source in sources:
        try:
            _reprocess_source(db, source)
            reindexed += 1
        except Exception as e:
            _mark_source_failed(db, source, f"Error reindexando: {e}")
            failed += 1

    if reindexed > 0:
        invalidate_index(bot_id)

    return SourceActionResponse(
        success=True,
        message=f"Reindexadas {reindexed}, fallidas {failed}",
        metadata={"reindexed": reindexed, "failed": failed},
    )
