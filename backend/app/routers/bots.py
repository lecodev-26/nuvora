from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.config import get_db
from app.models.bot import BotCreate, BotUpdate, BotResponse, BotPublicResponse
from app.models.db_models import Bot, User
from app.services.auth import get_current_user

router = APIRouter(prefix="/bots", tags=["bots"])


# ============================================================
# ENDPOINTS AUTENTICADOS (DASHBOARD)
# ============================================================

@router.post("/", response_model=BotResponse)
def create_bot(
    bot_data: BotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crea un nuevo bot universal.
    Compatible con el modelo antiguo (owner_email) y nuevo (user_id).
    """
    # Verificar si ya existe un bot con ese email (compatibilidad)
    existing_bot = db.query(Bot).filter(Bot.owner_email == current_user.email).first()
    if existing_bot:
        raise HTTPException(status_code=400, detail="Ya existe un bot con este email")

    # Crear nuevo bot con los nuevos campos universales
    new_bot = Bot(
        user_id=current_user.id,
        name=bot_data.name,
        description=bot_data.description,
        # Negocio (opcional)
        business_name=bot_data.business_name,
        business_type=bot_data.business_type,
        nicho_id=bot_data.nicho_id or "otro",
        # Compatibilidad (deprecados)
        restaurant_name=bot_data.business_name,  # Copia por compatibilidad
        owner_email=current_user.email,           # Copia por compatibilidad
        # Propósito
        goal=bot_data.goal,
        instructions=bot_data.instructions,
        # Personalidad
        personality=bot_data.personality,
        tone=bot_data.tone,
        # Comportamiento
        greeting=bot_data.greeting,
        fallback_message=bot_data.fallback_message,
        answer_mode=bot_data.answer_mode or "strict",
        # Control
        is_published=False,
        is_active=True,
        plan="free",
    )

    db.add(new_bot)
    db.commit()
    db.refresh(new_bot)

    return new_bot


@router.get("/", response_model=list[BotResponse])
def list_bots(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lista todos los bots del usuario autenticado.
    Compatible con user_id (nuevo) y owner_email (antiguo).
    """
    bots = db.query(Bot).filter(
        (Bot.user_id == current_user.id) | (Bot.owner_email == current_user.email)
    ).all()
    return bots


@router.get("/{bot_id}", response_model=BotResponse)
def get_bot(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")

    # Validar ownership (compatible con ambos campos)
    if bot.user_id and bot.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver este bot")
    if not bot.user_id and bot.owner_email != current_user.email:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver este bot")

    return bot


@router.patch("/{bot_id}", response_model=BotResponse)
def update_bot(
    bot_id: int,
    bot_data: BotUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualiza un bot existente.
    NO modifica las memorias existentes.
    """
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")

    # Validar ownership
    if bot.user_id and bot.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar este bot")
    if not bot.user_id and bot.owner_email != current_user.email:
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar este bot")

    # Actualizar solo los campos proporcionados
    update_data = bot_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(bot, field):
            setattr(bot, field, value)

    # Sincronizar business_name → restaurant_name por compatibilidad
    if bot_data.business_name is not None:
        bot.restaurant_name = bot_data.business_name

    db.commit()
    db.refresh(bot)

    return bot


# ============================================================
# ENDPOINT PÚBLICO (WIDGET) — SIN AUTENTICACIÓN
# ============================================================

@router.get("/{bot_id}/public", response_model=BotPublicResponse)
def get_bot_public(
    bot_id: int,
    db: Session = Depends(get_db)
):
    """
    Devuelve solo los datos públicos del bot (nombre, negocio, nicho).
    Sin información sensible. Usado por el widget.
    """
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")

    return BotPublicResponse(
        id=bot.id,
        name=bot.name,
        description=bot.description,
        business_name=bot.business_name or bot.restaurant_name,  # Fallback por compatibilidad
        business_type=bot.business_type,
        nicho_id=bot.nicho_id or "otro",
        greeting=bot.greeting,
        is_active=bot.is_active if bot.is_active is not None else True,
    )
