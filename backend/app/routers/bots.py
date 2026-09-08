from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.config import get_db
from app.models.bot import BotCreate, BotResponse
from app.models.db_models import Bot

router = APIRouter(prefix="/bots", tags=["bots"])

@router.post("/", response_model=BotResponse)
def create_bot(bot_data: BotCreate, db: Session = Depends(get_db)):
    existing_bot = db.query(Bot).filter(Bot.owner_email == bot_data.owner_email).first()
    if existing_bot:
        raise HTTPException(status_code=400, detail="Ya existe un bot con este email")

    new_bot = Bot(
        name=bot_data.name,
        restaurant_name=bot_data.restaurant_name,
        owner_email=bot_data.owner_email
    )

    db.add(new_bot)
    db.commit()
    db.refresh(new_bot)

    return new_bot

@router.get("/", response_model=list[BotResponse])
def list_bots(db: Session = Depends(get_db)):
    """
    Lista todos los bots (solo para administración).
    """
    bots = db.query(Bot).all()
    return bots
