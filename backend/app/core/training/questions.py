"""
Nuvora Core — Training Assistant: Unanswered Questions
========================================================
Implementación real (14.4.4).

Consulta Conversation.was_answered=False y agrupa preguntas similares
usando Jaccard similarity sobre tokens normalizados.

REGLAS:
    - Sin IA. Solo Jaccard determinista.
    - Reutiliza tokenize() de indexing.py (mismo motor de normalización).
    - Jaccard encapsulado para poder sustituirlo por similitud semántica
      en el futuro (Fase 15).
    - Aislamiento multi-tenant estricto por bot_id.
    - Ignorar preguntas con < 2 tokens (regla exclusiva, sin heurísticas
      adicionales para "hola", "ok", etc.).

DECISIONES (14.4.4):
    - Threshold Jaccard: 0.5
    - Agrupación contra el representante del grupo (no contra todos).
    - Representante: pregunta más frecuente textualmente; en empate, la más corta.
    - Consulta: ORDER BY created_at DESC LIMIT limit.
    - Variants: preguntas únicas textualmente dentro del grupo.
    - conversation_ids: todas las conversaciones del grupo (con duplicados).
"""

from collections import Counter
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.db_models import Conversation
from app.models.training import UnansweredQuestionGroup
from app.core.indexing import tokenize


# ============================================================
# CONSTANTES
# ============================================================

# Umbral de similitud Jaccard para agrupar dos preguntas.
JACCARD_THRESHOLD = 0.5

# Mínimo de tokens para considerar una pregunta válida.
# Preguntas con < MIN_TOKENS_VALIDOS tokens se ignoran.
MIN_TOKENS_VALIDOS = 2


# ============================================================
# JACCARD
# ============================================================

def jaccard_similarity(tokens_a: set[str], tokens_b: set[str]) -> float:
    """
    Calcula la similitud Jaccard entre dos conjuntos de tokens.

    J(A, B) = |A ∩ B| / |A ∪ B|

    Función ENCAPSULADA:
        - Es la única pieza que hace comparación de similitud.
        - Sustituible en el futuro por embeddings / similitud semántica
          (Fase 15) sin tocar el resto del módulo.

    Returns:
        float entre 0.0 y 1.0. Devuelve 0.0 si algún conjunto es vacío.
    """
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


# ============================================================
# HELPERS INTERNOS
# ============================================================

def _pick_representative(questions: list[str]) -> str:
    """
    Elige la pregunta representativa de un grupo:
        - La más frecuente textualmente.
        - En empate, la más corta.
    """
    counter = Counter(questions)
    max_count = max(counter.values())

    # Candidatos con el conteo máximo
    candidates = [q for q, count in counter.items() if count == max_count]

    # En empate, la más corta
    return min(candidates, key=lambda q: len(q))


def _dedupe_preserving_order(items: list[str]) -> list[str]:
    """Deduplica una lista preservando el orden de aparición."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


# ============================================================
# API PÚBLICA
# ============================================================

def get_unanswered_question_groups(
    bot_id: int,
    db: Session,
    limit: int = 100,
) -> list[UnansweredQuestionGroup]:
    """
    Obtiene las preguntas sin responder de un bot y las agrupa por similitud.

    Args:
        bot_id: ID del bot
        db: sesión de BD
        limit: máximo de conversaciones a analizar (las más recientes)

    Returns:
        Lista de UnansweredQuestionGroup ordenada por count DESC.
        Si limit <= 0, devuelve [].
    """
    # Protección: limit <= 0 → []
    if limit <= 0:
        return []

    # 1. Consultar conversaciones sin responder (más recientes primero)
    conversations = (
        db.query(Conversation)
        .filter(
            Conversation.bot_id == bot_id,
            Conversation.was_answered == False,
        )
        .order_by(Conversation.created_at.desc())
        .limit(limit)
        .all()
    )

    if not conversations:
        return []

    # 2. Normalizar tokens y filtrar las triviales
    #    Estructura: list[(conversation, tokens_set, question_str)]
    valid: list[tuple[Conversation, set[str], str]] = []
    for conv in conversations:
        q = (conv.question or "").strip()
        if not q:
            continue
        tokens = set(tokenize(q))
        if len(tokens) < MIN_TOKENS_VALIDOS:
            continue
        valid.append((conv, tokens, q))

    if not valid:
        return []

    # 3. Agrupación greedy contra el representante del grupo
    groups: list[dict] = []
    # Cada grupo: {
    #   "representative_tokens": set[str],
    #   "conversations": list[Conversation],
    #   "questions": list[str],
    # }

    for conv, tokens, q in valid:
        matched = None
        for group in groups:
            sim = jaccard_similarity(tokens, group["representative_tokens"])
            if sim >= JACCARD_THRESHOLD:
                matched = group
                break

        if matched is not None:
            matched["conversations"].append(conv)
            matched["questions"].append(q)
            # El representante NO cambia (es estable y evita reordenamientos)
        else:
            groups.append({
                "representative_tokens": tokens,
                "conversations": [conv],
                "questions": [q],
            })

    # 4. Construir UnansweredQuestionGroup y ordenar por count DESC
    result: list[UnansweredQuestionGroup] = []
    for group in groups:
        questions = group["questions"]
        representative = _pick_representative(questions)
        variants = _dedupe_preserving_order(questions)
        conv_ids = [c.id for c in group["conversations"]]

        result.append(UnansweredQuestionGroup(
            representative=representative,
            variants=variants,
            count=len(group["conversations"]),
            conversation_ids=conv_ids,
        ))

    result.sort(key=lambda g: g.count, reverse=True)
    return result
