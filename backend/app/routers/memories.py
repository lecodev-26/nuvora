from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.config import get_db
from app.models.bot import MemoryCreate, MemoryResponse
from app.models.db_models import Memory, Bot, User
from app.services.auth import get_current_user

router = APIRouter(prefix="/memories", tags=["memories"])


# ============================================================
# HELPER — Validar ownership del bot
# ============================================================

def verify_bot_ownership(bot: Bot, current_user: User):
    """
    Valida que el usuario autenticado es dueño del bot.
    Compatible con user_id (nuevo) y owner_email (deprecado).
    """
    # Si el bot tiene user_id, validar por user_id
    if bot.user_id is not None:
        if bot.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="No tienes permiso para modificar este bot")
        return

    # Fallback: validar por owner_email (compatibilidad)
    if bot.owner_email != current_user.email:
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar este bot")


# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/", response_model=MemoryResponse)
def add_memory(
    memory_data: MemoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Añade una nueva memoria (hecho) a un bot.
    Solo el dueño del bot puede añadir memorias.
    """
    bot = db.query(Bot).filter(Bot.id == memory_data.bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")

    verify_bot_ownership(bot, current_user)

    # Crear nueva memoria
    new_memory = Memory(
        bot_id=memory_data.bot_id,
        category_id=memory_data.category_id,
        fact=memory_data.fact,
        keyword=memory_data.keyword.lower(),
        source=memory_data.source or "manual",
        is_confirmed=memory_data.is_confirmed if memory_data.is_confirmed is not None else True,
    )

    db.add(new_memory)
    db.commit()
    db.refresh(new_memory)

    return new_memory


@router.get("/{bot_id}", response_model=list[MemoryResponse])
def get_memories(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene todas las memorias de un bot específico.
    Solo el dueño del bot puede ver sus memorias.
    """
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")

    verify_bot_ownership(bot, current_user)

    memories = db.query(Memory).filter(Memory.bot_id == bot_id).all()
    return memories


@router.delete("/{memory_id}")
def delete_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Elimina una memoria específica.
    Solo el dueño del bot puede eliminar memorias.
    """
    memory = db.query(Memory).filter(Memory.id == memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memoria no encontrada")

    bot = db.query(Bot).filter(Bot.id == memory.bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")

    verify_bot_ownership(bot, current_user)

    db.delete(memory)
    db.commit()

    return {"message": "Memoria eliminada correctamente", "memory_id": memory_id}
