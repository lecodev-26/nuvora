from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.config import get_db
from app.models.bot import MemoryCreate
from app.models.db_models import Memory, Bot, User
from app.services.auth import get_current_user

router = APIRouter(prefix="/memories", tags=["memories"])

@router.post("/")
def add_memory(
    memory_data: MemoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bot = db.query(Bot).filter(Bot.id == memory_data.bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")

    if bot.owner_email != current_user.email:
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar este bot")

    new_memory = Memory(
        bot_id=memory_data.bot_id,
        fact=memory_data.fact,
        keyword=memory_data.keyword.lower()
    )

    db.add(new_memory)
    db.commit()
    db.refresh(new_memory)

    return {
        "message": "Memoria añadida correctamente",
        "memory_id": new_memory.id,
        "fact": new_memory.fact,
        "keyword": new_memory.keyword
    }

@router.get("/{bot_id}")
def get_memories(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")

    if bot.owner_email != current_user.email:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver este bot")

    memories = db.query(Memory).filter(Memory.bot_id == bot_id).all()
    return memories
