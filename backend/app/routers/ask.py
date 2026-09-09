from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database.config import get_db
from app.models.db_models import Bot, Memory, User
from app.services.auth import get_current_user

router = APIRouter(prefix="/ask", tags=["ask"])

class AskRequest(BaseModel):
    bot_id: int
    question: str

class AskResponse(BaseModel):
    answer: str
    found: bool

@router.post("/", response_model=AskResponse)
def ask_question(
    request: AskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Un visitante hace una pregunta al bot.
    El bot busca en su memoria y responde.
    """
    # Verificar que el bot existe y el usuario es dueño
    bot = db.query(Bot).filter(Bot.id == request.bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")

    if bot.owner_email != current_user.email:
        raise HTTPException(status_code=403, detail="No tienes permiso para usar este bot")

    # Obtener todas las memorias del bot
    memories = db.query(Memory).filter(Memory.bot_id == request.bot_id).all()

    if not memories:
        return AskResponse(
            answer="Aún no tengo información sobre este restaurante. Por favor, contacta directamente con ellos.",
            found=False
        )

    # Buscar coincidencia mejorada
    question_lower = request.question.lower()
    stopwords = {"qué", "cuál", "cómo", "dónde", "cuándo", "quién", "para", "por", "con", "sin", "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al", "a", "e", "y", "o", "u", "mi", "tu", "su", "nuestro", "vuestro", "me", "te", "se", "nos", "os", "lo", "la", "le", "les", "los", "las", "más", "menos", "muy", "tan", "tanto", "demasiado", "algo", "nada", "todo", "siempre", "nunca", "quizás", "tal", "vez"}

    best_match = None
    best_score = 0

    for memory in memories:
        keywords = [k.strip().lower() for k in memory.keyword.split(",")]
        score = 0
        for keyword in keywords:
            if keyword in question_lower:
                score += len(keyword)
            words = question_lower.split()
            for word in words:
                if word in stopwords:
                    continue
                if keyword in word or word in keyword:
                    score += min(len(keyword), len(word)) * 0.5

        if score > best_score:
            best_score = score
            best_match = memory

    MIN_SCORE = 2

    if best_match and best_score >= MIN_SCORE:
        return AskResponse(
            answer=best_match.fact,
            found=True
        )
    else:
        return AskResponse(
            answer="No tengo esa información en mi memoria. Te recomiendo contactar directamente con el restaurante.",
            found=False
        )
