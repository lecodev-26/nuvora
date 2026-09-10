"""
Nuvora Core — Text Processor
==============================
Procesa texto plano (input directo del usuario).
"""

import re
from app.core.processors.base import BaseProcessor, ProcessorResult, ProcessorError


# Límite de tamaño (100 KB ≈ 20.000 palabras)
MAX_TEXT_SIZE = 100 * 1024


class TextProcessor(BaseProcessor):

    def process(self, content: str | bytes, **kwargs) -> ProcessorResult:
        # 1. Convertir bytes a str si es necesario
        if isinstance(content, bytes):
            try:
                content = content.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    content = content.decode("latin-1")
                except Exception as e:
                    raise ProcessorError(f"No se pudo decodificar el texto: {e}")

        # 2. Validar tipo
        if not isinstance(content, str):
            raise ProcessorError("El contenido debe ser texto (str o bytes)")

        # 3. Validar tamaño
        size_bytes = len(content.encode("utf-8"))
        if size_bytes > MAX_TEXT_SIZE:
            raise ProcessorError(
                f"El texto supera el límite de {MAX_TEXT_SIZE // 1024} KB "
                f"(recibido: {size_bytes // 1024} KB)"
            )

        # 4. Normalizar
        text = self._normalize(content)

        # 5. Validar que no esté vacío tras normalizar
        if not text.strip():
            raise ProcessorError("El texto está vacío o solo contiene espacios")

        # 6. Metadatos
        meta = {
            "chars": len(text),
            "lines": text.count("\n") + 1,
            "source_type": "text",
        }

        return ProcessorResult(text=text, meta=meta, size_bytes=size_bytes)

    def _normalize(self, text: str) -> str:
        """Normaliza el texto: limpieza de espacios, saltos de línea, etc."""
        # Normalizar saltos de línea
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Colapsar 3+ saltos de línea en 2 (mantener párrafos)
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Eliminar espacios al final de cada línea
        text = "\n".join(line.rstrip() for line in text.split("\n"))
        # Colapsar espacios múltiples dentro de líneas
        text = re.sub(r"[ \t]{2,}", " ", text)
        # Eliminar espacios al inicio y final
        text = text.strip()
        return text
