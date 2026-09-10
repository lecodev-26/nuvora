"""
Nuvora Core — Chunker
========================
Fragmenta texto en chunks indexables.

Genérico: NO conoce nichos, ni tipos de negocio.
Solo sabe dividir texto en trozos lógicos.
"""

import re
from dataclasses import dataclass, field
from typing import Optional


# ============================================================
# PARÁMETROS
# ============================================================

TARGET_CHUNK_SIZE = 500
MAX_CHUNK_SIZE = 1000
MIN_CHUNK_SIZE = 100
OVERLAP = 50

# Marcador de página dejado por el PDFProcessor
PAGE_MARKER_RE = re.compile(r"\[\[PAGE:(\d+)\]\]")


# ============================================================
# DATACLASS CHUNK
# ============================================================

@dataclass
class Chunk:
    """
    Fragmento de texto con metadatos.

    Nota:
        char_start y char_end corresponden al texto NORMALIZADO/PROCESADO,
        no al contenido original de la fuente.
    """
    content: str
    chunk_index: int
    section: Optional[str] = None
    page: Optional[int] = None
    char_start: int = 0
    char_end: int = 0
    tokens_estimate: int = 0
    meta: dict = field(default_factory=dict)


# ============================================================
# CHUNKER
# ============================================================

class Chunker:
    """
    Fragmentador híbrido de texto.

    Estrategia:
    1. Detectar secciones (líneas que parecen títulos)
    2. Dividir por párrafos (doble salto de línea)
    3. Fusionar párrafos pequeños
    4. Dividir párrafos grandes por frases o por tamaño fijo
    5. Añadir overlap entre chunks consecutivos
    """

    def __init__(
        self,
        target_size: int = TARGET_CHUNK_SIZE,
        max_size: int = MAX_CHUNK_SIZE,
        min_size: int = MIN_CHUNK_SIZE,
        overlap: int = OVERLAP,
    ):
        self.target_size = target_size
        self.max_size = max_size
        self.min_size = min_size
        self.overlap = overlap

    def chunk(self, text: str, meta: Optional[dict] = None) -> list[Chunk]:
        """
        Divide el texto en chunks.
        Devuelve lista de Chunk ordenados.
        """
        if not text or not text.strip():
            return []

        # 1. Normalizar
        text = self._normalize(text)

        # 2. Extraer páginas y limpiar marcadores
        text, page_map = self._extract_pages(text)

        # 3. Detectar secciones
        text, section_map = self._extract_sections(text)

        # 4. Dividir en bloques lógicos
        blocks = self._split_into_blocks(text)

        # 5. Fusionar bloques pequeños consecutivos
        blocks = self._merge_small_blocks(blocks)

        # 6. Dividir bloques grandes
        blocks = self._split_large_blocks(blocks)

        # 7. Construir chunks con metadatos
        chunks: list[Chunk] = []
        cursor = 0  # offset acumulado en el texto normalizado

        for i, block in enumerate(blocks):
            content = block["text"].strip()
            if not content:
                continue

            # Añadir overlap con el chunk anterior
            if i > 0 and chunks:
                prev = chunks[-1].content
                overlap_text = prev[-self.overlap:] if len(prev) > self.overlap else prev
                # Evitar duplicar si el overlap ya está al inicio
                if not content.startswith(overlap_text):
                    content = overlap_text + " " + content

            # Calcular offsets (en el texto normalizado)
            char_start = cursor
            char_end = cursor + len(block["text"])
            cursor = char_end

            # Sección y página para este chunk
            section = self._lookup_section(char_start, section_map)
            page = self._lookup_page(char_start, page_map)

            # Estimar tokens (~4 caracteres por token en español)
            tokens_estimate = max(1, len(content) // 4)

            chunks.append(Chunk(
                content=content,
                chunk_index=len(chunks),
                section=section,
                page=page,
                char_start=char_start,
                char_end=char_end,
                tokens_estimate=tokens_estimate,
                meta=meta or {},
            ))

        return chunks

    # ============================================================
    # NORMALIZACIÓN
    # ============================================================

    def _normalize(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = "\n".join(line.rstrip() for line in text.split("\n"))
        return text.strip()

    # ============================================================
    # PÁGINAS (marcadores [[PAGE:N]])
    # ============================================================

    def _extract_pages(self, text: str) -> tuple[str, list[tuple[int, int]]]:
        """
        Extrae los marcadores de página.
        Devuelve (texto_limpio, page_map) donde page_map es [(offset, page_num), ...].
        """
        page_map: list[tuple[int, int]] = []
        cleaned_parts = []
        cursor = 0

        for match in PAGE_MARKER_RE.finditer(text):
            # Texto antes del marcador
            before = text[cursor:match.start()]
            cleaned_parts.append(before)
            offset = sum(len(p) for p in cleaned_parts)
            page_map.append((offset, int(match.group(1))))
            cursor = match.end()

        # Texto restante
        cleaned_parts.append(text[cursor:])
        cleaned = "".join(cleaned_parts)

        # Si el primer marcador estaba al inicio, la primera página se asigna desde offset 0
        if not page_map and PAGE_MARKER_RE.search(text):
            pass

        return cleaned, page_map

    def _lookup_page(self, offset: int, page_map: list[tuple[int, int]]) -> Optional[int]:
        """Devuelve el número de página correspondiente a un offset."""
        if not page_map:
            return None
        current_page = None
        for page_offset, page_num in page_map:
            if offset >= page_offset:
                current_page = page_num
            else:
                break
        return current_page

    # ============================================================
    # SECCIONES
    # ============================================================

    def _extract_sections(self, text: str) -> tuple[str, list[tuple[int, str]]]:
        """
        Detecta títulos y los devuelve en un mapa de offset → título.
        NO elimina los títulos del texto (los deja como parte del chunk).
        """
        sections: list[tuple[int, str]] = []
        cursor = 0

        lines = text.split("\n")
        for line in lines:
            line_len = len(line) + 1  # +1 por el \n
            stripped = line.strip()
            if self._is_section_header(stripped):
                sections.append((cursor, stripped))
            cursor += line_len

        return text, sections

    def _is_section_header(self, line: str) -> bool:
        """Heurísticas para detectar un título."""
        if not line or len(line) > 80:
            return False

        # Markdown
        if re.match(r"^#{1,6}\s+\S", line):
            return True

        # MAYÚSCULAS cortas
        if len(line) < 60 and line.isupper() and any(c.isalpha() for c in line):
            return True

        # Termina en : y es corta
        if line.endswith(":") and len(line) < 60:
            return True

        return False

    def _lookup_section(self, offset: int, section_map: list[tuple[int, str]]) -> Optional[str]:
        """Devuelve la sección activa para un offset."""
        if not section_map:
            return None
        current = None
        for sec_offset, title in section_map:
            if offset >= sec_offset:
                current = title
            else:
                break
        return current

    # ============================================================
    # DIVISIÓN EN BLOQUES
    # ============================================================

    def _split_into_blocks(self, text: str) -> list[dict]:
        """
        Divide el texto en bloques por párrafos (doble salto).
        Cada bloque es {"text": str}.
        """
        paragraphs = re.split(r"\n\s*\n", text)
        blocks = []
        for p in paragraphs:
            p = p.strip()
            if p:
                blocks.append({"text": p + "\n\n"})
        return blocks

    def _merge_small_blocks(self, blocks: list[dict]) -> list[dict]:
        """Fusiona bloques consecutivos si son muy pequeños."""
        if not blocks:
            return []

        merged = []
        buffer = ""

        for block in blocks:
            candidate = buffer + block["text"] if buffer else block["text"]
            if len(candidate.strip()) < self.min_size and buffer is not None:
                buffer = candidate
            else:
                if buffer.strip():
                    merged.append({"text": buffer})
                buffer = block["text"]

        if buffer.strip():
            merged.append({"text": buffer})

        return merged

    def _split_large_blocks(self, blocks: list[dict]) -> list[dict]:
        """Divide bloques que superen MAX_CHUNK_SIZE."""
        result = []
        for block in blocks:
            text = block["text"]
            if len(text) <= self.max_size:
                result.append(block)
                continue

            # Dividir por frases
            sentences = re.split(r"(?<=[.!?])\s+", text)
            buffer = ""
            for sentence in sentences:
                candidate = buffer + " " + sentence if buffer else sentence
                if len(candidate) <= self.target_size:
                    buffer = candidate
                else:
                    if buffer.strip():
                        result.append({"text": buffer.strip() + "\n\n"})
                    # Si una sola frase es mayor que target, dividir por tamaño fijo
                    if len(sentence) > self.max_size:
                        for i in range(0, len(sentence), self.target_size):
                            piece = sentence[i:i + self.target_size]
                            result.append({"text": piece.strip() + "\n\n"})
                        buffer = ""
                    else:
                        buffer = sentence
            if buffer.strip():
                result.append({"text": buffer.strip() + "\n\n"})

        return result
