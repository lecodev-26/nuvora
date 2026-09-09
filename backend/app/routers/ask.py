from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database.config import get_db
from app.models.bot import AskRequest, AskResponse
from app.models.db_models import Bot, Memory, User, Conversation
from app.services.auth import get_current_user

router = APIRouter(prefix="/ask", tags=["ask"])

# ============================================================
# BÚSQUEDA POR KEYWORD (FALLBACK)
# ============================================================

def search_memories(memories, question: str):
    question_lower = question.lower()
    
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
        return best_match.fact, True
    else:
        return None, False

def save_conversation(db: Session, bot_id: int, question: str, answer: Optional[str], was_answered: bool, session_id: Optional[str] = None):
    conversation = Conversation(
        bot_id=bot_id,
        question=question,
        answer=answer,
        was_answered=was_answered,
        session_id=session_id
    )
    db.add(conversation)
    db.commit()

# ============================================================
# ENDPOINT PÚBLICO (WIDGET) — SIN AUTENTICACIÓN
# ============================================================

@router.post("/public", response_model=AskResponse)
def ask_question_public(
    request: AskRequest,
    db: Session = Depends(get_db)
):
    bot = db.query(Bot).filter(Bot.id == request.bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")

    memories = db.query(Memory).filter(Memory.bot_id == request.bot_id).all()

    if not memories:
        answer_text = "Aún no tengo información sobre este restaurante. Por favor, contacta directamente con ellos."
        was_answered = False
    else:
        answer_text, was_answered = search_memories(memories, request.question)
        if not was_answered:
            answer_text = "No tengo esa información en mi memoria. Te recomiendo contactar directamente con el restaurante."

    save_conversation(
        db=db,
        bot_id=request.bot_id,
        question=request.question,
        answer=answer_text,
        was_answered=was_answered,
        session_id=request.session_id
    )

    return AskResponse(answer=answer_text, found=was_answered)

# ============================================================
# ENDPOINT PRIVADO (DASHBOARD) — CON AUTENTICACIÓN
# ============================================================

@router.post("/", response_model=AskResponse)
def ask_question_private(
    request: AskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bot = db.query(Bot).filter(Bot.id == request.bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot no encontrado")

    if bot.owner_email != current_user.email:
        raise HTTPException(status_code=403, detail="No tienes permiso para usar este bot")

    memories = db.query(Memory).filter(Memory.bot_id == request.bot_id).all()

    if not memories:
        answer_text = "Aún no tengo información sobre este restaurante. Por favor, contacta directamente con ellos."
        was_answered = False
    else:
        answer_text, was_answered = search_memories(memories, request.question)
        if not was_answered:
            answer_text = "No tengo esa información en mi memoria. Te recomiendo contactar directamente con el restaurante."

    save_conversation(
        db=db,
        bot_id=request.bot_id,
        question=request.question,
        answer=answer_text,
        was_answered=was_answered,
        session_id=request.session_id
    )

    return AskResponse(answer=answer_text, found=was_answered)
