from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.config import get_db
from app.models.bot import BotCreate, BotResponse
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
        owner_email=current_user.email  # ← Usamos el email del usuario
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
    """
    bots = db.query(Bot).filter(Bot.owner_email == current_user.email).all()
    return bots
