from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.config import get_db
from app.models.bot import BotCreate, BotResponse, BotUpdate
from app.models.db_models import Bot, User
from app.services.auth import get_current_user

router = APIRouter(prefix="/bots", tags=["bots"])

@router.post("/", response_model=BotResponse)
def create_bot(
    bot_data: BotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verificar si ya existe un bot con ese email
    existing_bot = db.query(Bot).filter(Bot.owner_email == current_user.email).first()
    if existing_bot:
        raise HTTPException(status_code=400, detail="Ya existe un bot con este email")

    # Crear nuevo bot con el email del usuario autenticado
    new_bot = Bot(
        name=bot_data.name,
        restaurant_name=bot_data.restaurant_name,
        owner_email=current_user.email,
        nicho_id=bot_data.nicho_id or "otro"
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
    bots = db.query(Bot).filter(Bot.owner_email == current_user.email).all()
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
    if bot.owner_email != current_user.email:
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
    Actualiza un bot existente (nombre, negocio o nicho).
    NO modifica las memorias existentes.
    """
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")
    if bot.owner_email != current_user.email:
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar este bot")

    # Actualizar solo los campos proporcionados
    if bot_data.name is not None:
        bot.name = bot_data.name
    if bot_data.restaurant_name is not None:
        bot.restaurant_name = bot_data.restaurant_name
    if bot_data.nicho_id is not None:
        bot.nicho_id = bot_data.nicho_id

    db.commit()
    db.refresh(bot)

    return bot
