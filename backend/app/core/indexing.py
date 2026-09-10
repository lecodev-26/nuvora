"""
Nuvora Core — Indexing (TF-IDF MVP)
======================================
Implementación propia de TF-IDF sin dependencias externas.

ARQUITECTURA
------------
Este módulo define una capa SUSTITUIBLE de indexación.
Se separa en dos responsabilidades:

1. Construcción del índice (IndexBuilder)
   - Analiza un corpus de documentos y calcula IDF
   - El resultado se puede cachear por bot_id

2. Scoring de consultas (score_query_against_documents)
   - Dado un índice ya construido y una query, puntúa cada documento
   - NO reconstruye el corpus

En Fase 15 se podrá sustituir esta capa por:
- KeywordIndexer (BM25, etc.)
- EmbeddingIndexer (embeddings reales)
- VectorIndexer (pgvector, Pinecone, etc.)

LIMITACIONES (MVP 14.3.3)
-------------------------
- NO hace stemming ni lematización
- NO maneja sinónimos
- NO maneja typos (fuzzy matching)

Estas limitaciones se documentan y se resolverán en Fase 15.
"""

import math
import re
import unicodedata
from datetime import datetime, timedelta


# ============================================================
# CONSTANTES
# ============================================================

MIN_TOKEN_LENGTH = 2
IDF_CACHE_TTL_SECONDS = 60

# Stopwords en español (básicas)
STOPWORDS_ES = {
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se",
    "las", "por", "un", "para", "con", "no", "una", "su", "al",
    "lo", "como", "más", "pero", "sus", "le", "ya", "o", "este",
    "sí", "porque", "esta", "entre", "cuando", "muy", "sin",
    "sobre", "también", "me", "hasta", "hay", "donde", "quien",
    "desde", "todo", "nos", "durante", "todos", "uno", "les",
    "ni", "contra", "otros", "ese", "eso", "ante", "ellos",
    "e", "esto", "mí", "antes", "algunos", "qué", "unos", "yo",
    "otro", "otras", "otra", "él", "tanto", "esa", "estos",
    "mucho", "quienes", "nada", "muchos", "cual", "poco", "ella",
    "estar", "estas", "algunas", "algo", "nosotros", "mi", "mis",
    "tú", "te", "ti", "tu", "tus", "ellas", "nosotras", "vosotros",
    "vosotras", "os", "mío", "mía", "míos", "mías", "tuyo", "tuya",
    "tuyos", "tuyas", "suyo", "suya", "suyos", "suyas", "nuestro",
    "nuestra", "nuestros", "nuestras", "vuestro", "vuestra",
    "vuestros", "vuestras", "esos", "esas", "estoy", "estás",
    "está", "estamos", "estáis", "están", "sea", "ser", "es",
    "son", "era", "fue", "he", "has", "ha", "hemos", "habéis",
    "han", "sido", "fui", "fuiste", "fue", "fuimos", "fuisteis",
    "fueron", "tener", "tengo", "tienes", "tiene", "tenemos",
    "tenéis", "tienen", "hacer", "hago", "haces", "hace",
    "hacemos", "hacéis", "hacen", "puedo", "puedes", "puede",
    "podemos", "podéis", "pueden",
}


# ============================================================
# TOKENIZACIÓN
# ============================================================

def _strip_accents(text: str) -> str:
    """Elimina acentos usando normalización Unicode NFD."""
    nfd = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")


def tokenize(text: str) -> list[str]:
    """
    Tokeniza un texto:
    - Pasa a minúsculas
    - Elimina acentos
    - Separa por caracteres no alfanuméricos
    - Filtra stopwords
    - Filtra tokens muy cortos
    """
    if not text:
        return []

    # Minúsculas + sin acentos
    text = _strip_accents(text.lower())

    # Separar por no-alfanuméricos
    raw_tokens = re.findall(r"[a-z0-9]+", text)

    tokens = []
    for tok in raw_tokens:
        if len(tok) < MIN_TOKEN_LENGTH:
            continue
        if tok in STOPWORDS_ES:
            continue
        tokens.append(tok)

    return tokens


# ============================================================
# INDEX BUILDER — Construcción del índice
# ============================================================

class IndexBuilder:
    """
    Construye el índice TF-IDF a partir de un corpus de documentos.

    Uso:
        builder = IndexBuilder(documents)
        index = builder.build()
        # index = {"idf": {...}, "doc_tfs": [...], "doc_norms": [...]}
    """

    def __init__(self, documents: list[str]):
        """
        Args:
            documents: lista de textos (chunks)
        """
        self.documents = documents
        self._tokenized_docs: list[list[str]] = []

    def build(self) -> dict:
        """
        Construye el índice completo.

        Returns:
            dict con:
                - idf: dict[token, float]
                - doc_tfs: list[dict[token, float]]
                - doc_norms: list[float]
                - num_docs: int
        """
        # 1. Tokenizar todos los documentos
        self._tokenized_docs = [tokenize(doc) for doc in self.documents]
        num_docs = len(self._tokenized_docs)

        # 2. Calcular DF (document frequency) de cada token
        df: dict[str, int] = {}
        for tokens in self._tokenized_docs:
            unique_tokens = set(tokens)
            for tok in unique_tokens:
                df[tok] = df.get(tok, 0) + 1

        # 3. Calcular IDF con suavizado
        #    idf(t) = log((N + 1) / (df(t) + 1)) + 1
        idf: dict[str, float] = {}
        for tok, freq in df.items():
            idf[tok] = math.log((num_docs + 1) / (freq + 1)) + 1.0

        # 4. Calcular TF (term frequency) normalizado para cada documento
        doc_tfs: list[dict[str, float]] = []
        doc_norms: list[float] = []

        for tokens in self._tokenized_docs:
            if not tokens:
                doc_tfs.append({})
                doc_norms.append(0.0)
                continue

            # Contar
            counts: dict[str, int] = {}
            for tok in tokens:
                counts[tok] = counts.get(tok, 0) + 1

            # TF = count / total
            total = len(tokens)
            tf = {tok: cnt / total for tok, cnt in counts.items()}
            doc_tfs.append(tf)

            # Norma del vector TF-IDF (para similitud coseno)
            norm_sq = sum((tf.get(tok, 0.0) * idf.get(tok, 0.0)) ** 2 for tok in tf)
            doc_norms.append(math.sqrt(norm_sq))

        return {
            "idf": idf,
            "doc_tfs": doc_tfs,
            "doc_norms": doc_norms,
            "num_docs": num_docs,
        }


# ============================================================
# SCORING DE CONSULTAS
# ============================================================

def score_query_against_documents(
    query: str,
    index: dict,
) -> list[float]:
    """
    Dado un índice construido, puntúa la query contra cada documento.
    NO reconstruye el corpus.

    Returns:
        lista de scores (uno por documento, en el mismo orden)
    """
    query_tokens = tokenize(query)
    if not query_tokens:
        return [0.0] * index["num_docs"]

    idf = index["idf"]

    # Calcular TF de la query
    counts: dict[str, int] = {}
    for tok in query_tokens:
        counts[tok] = counts.get(tok, 0) + 1
    total = len(query_tokens)
    query_tf = {tok: cnt / total for tok, cnt in counts.items()}

    # Norma del vector query
    query_norm_sq = sum(
        (query_tf.get(tok, 0.0) * idf.get(tok, 0.0)) ** 2
        for tok in query_tf
    )
    query_norm = math.sqrt(query_norm_sq)

    if query_norm == 0.0:
        return [0.0] * index["num_docs"]

    # Calcular similitud coseno con cada documento
    scores = []
    for i, doc_tf in enumerate(index["doc_tfs"]):
        doc_norm = index["doc_norms"][i]
        if doc_norm == 0.0 or not doc_tf:
            scores.append(0.0)
            continue

        # Producto punto
        dot = 0.0
        for tok, q_tf in query_tf.items():
            if tok in doc_tf:
                idf_val = idf.get(tok, 0.0)
                dot += (q_tf * idf_val) * (doc_tf[tok] * idf_val)

        score = dot / (query_norm * doc_norm)
        scores.append(score)

    return scores


# ============================================================
# CACHÉ DE ÍNDICES (con TTL + invalidación explícita)
# ============================================================

_idf_cache: dict[int, dict] = {}
_idf_cache_timestamps: dict[int, datetime] = {}


def get_cached_index(bot_id: int) -> dict | None:
    """Recupera el índice cacheado para un bot si no ha expirado."""
    if bot_id not in _idf_cache:
        return None

    ts = _idf_cache_timestamps.get(bot_id)
    if ts is None:
        return None

    # TTL como fallback
    if datetime.utcnow() - ts > timedelta(seconds=IDF_CACHE_TTL_SECONDS):
        invalidate_index(bot_id)
        return None

    return _idf_cache[bot_id]


def set_cached_index(bot_id: int, index: dict):
    """Guarda el índice en caché con timestamp."""
    _idf_cache[bot_id] = index
    _idf_cache_timestamps[bot_id] = datetime.utcnow()


def invalidate_index(bot_id: int):
    """
    Invalida el índice cacheado de un bot.
    Se debe llamar cuando:
    - Se añade/elimina una Source
    - Se reindexa una Source
    """
    _idf_cache.pop(bot_id, None)
    _idf_cache_timestamps.pop(bot_id, None)


def invalidate_all_indexes():
    """Invalida el caché completo. Útil en tests."""
    _idf_cache.clear()
    _idf_cache_timestamps.clear()
