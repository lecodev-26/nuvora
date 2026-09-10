"""
Nuvora Core — Router de categorías de conocimiento.
Permite organizar las memorias en categorías (ej: "Horarios", "Cursos", "Precios").
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.bot import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
)
from app.models.db_models import MemoryCategory, Bot, User, Memory
from app.services.auth import get_current_user


router = APIRouter(prefix="/categories", tags=["categories"])


# ============================================================
# HELPER — Validar ownership del bot
# ============================================================

def verify_bot_ownership(bot: Bot, current_user: User):
    """Valida que el usuario es dueño del bot."""
    if bot.user_id is not None:
        if bot.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="No tienes permiso para modificar este bot")
        return
    if bot.owner_email != current_user.email:
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar este bot")


# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/", response_model=CategoryResponse)
def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crea una nueva categoría para un bot."""
    bot = db.query(Bot).filter(Bot.id == category_data.bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")

    verify_bot_ownership(bot, current_user)

    new_category = MemoryCategory(
        bot_id=category_data.bot_id,
        name=category_data.name,
        description=category_data.description,
        icon=category_data.icon,
        order=category_data.order or 0,
    )

    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    return new_category


@router.get("/{bot_id}", response_model=list[CategoryResponse])
def list_categories(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista todas las categorías de un bot, ordenadas por `order`."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")

    verify_bot_ownership(bot, current_user)

    categories = db.query(MemoryCategory).filter(
        MemoryCategory.bot_id == bot_id
    ).order_by(MemoryCategory.order, MemoryCategory.id).all()

    return categories


@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Actualiza una categoría existente."""
    category = db.query(MemoryCategory).filter(MemoryCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    bot = db.query(Bot).filter(Bot.id == category.bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")

    verify_bot_ownership(bot, current_user)

    # Actualizar solo los campos proporcionados
    update_data = category_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(category, field):
            setattr(category, field, value)

    db.commit()
    db.refresh(category)

    return category


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Elimina una categoría.
    IMPORTANTE: NO elimina las memorias asociadas — solo las desvincula
    (su `category_id` pasa a NULL).
    """
    category = db.query(MemoryCategory).filter(MemoryCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    bot = db.query(Bot).filter(Bot.id == category.bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")

    verify_bot_ownership(bot, current_user)

    # Desvincular memorias (NO borrar)
    db.query(Memory).filter(Memory.category_id == category_id).update(
        {Memory.category_id: None}
    )

    db.delete(category)
    db.commit()

    return {"message": "Categoría eliminada correctamente", "category_id": category_id}
