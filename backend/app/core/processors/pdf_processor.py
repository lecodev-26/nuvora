"""
Nuvora Core — PDF Processor
==============================
Extrae texto de un PDF usando pypdf.
"""

import io
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.core.processors.base import BaseProcessor, ProcessorResult, ProcessorError


# ============================================================
# LÍMITES
# ============================================================

MAX_PDF_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_PDF_PAGES = 100
# Umbral para considerar un PDF "escaneado" (sin texto extraíble)
# Por debajo de este valor en TODO el PDF, asumimos que es un escaneo.
SCANNED_THRESHOLD = 10


class PDFProcessor(BaseProcessor):

    def process(self, content: str | bytes, **kwargs) -> ProcessorResult:
        # 1. Aceptar bytes o str
        if isinstance(content, str):
            # Un PDF no debería llegar como str, pero por si acaso
            raise ProcessorError("El PDF debe proporcionarse como bytes")

        if not isinstance(content, bytes):
            raise ProcessorError("Contenido no válido para PDF (se esperaban bytes)")

        # 2. Validar tamaño
        size_bytes = len(content)
        if size_bytes > MAX_PDF_SIZE:
            raise ProcessorError(
                f"El PDF supera el límite de {MAX_PDF_SIZE // (1024*1024)} MB "
                f"(recibido: {size_bytes / (1024*1024):.1f} MB)"
            )

        # 3. Leer PDF
        try:
            reader = PdfReader(io.BytesIO(content))
        except PdfReadError as e:
            raise ProcessorError(f"No se pudo leer el PDF: {e}")
        except Exception as e:
            raise ProcessorError(f"Error al procesar el PDF: {e}")

        # 4. Validar número de páginas
        num_pages = len(reader.pages)
        if num_pages == 0:
            raise ProcessorError("El PDF no contiene páginas")

        if num_pages > MAX_PDF_PAGES:
            raise ProcessorError(
                f"El PDF tiene {num_pages} páginas (máx {MAX_PDF_PAGES})"
            )

        # 5. Extraer texto página por página
        page_texts = []
        total_chars = 0

        for page_num, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text() or ""
            except Exception:
                page_text = ""

            page_text = page_text.strip()
            total_chars += len(page_text)

            # Marcador de página para el chunker
            page_texts.append(f"[[PAGE:{page_num}]]\n{page_text}")

        # 6. Distinguir escaneado vs vacío vs válido
        # - total_chars < SCANNED_THRESHOLD → probablemente escaneado
        if total_chars < SCANNED_THRESHOLD:
            raise ProcessorError(
                "El PDF parece estar escaneado (sin texto extraíble). "
                "Prueba con un PDF con texto seleccionable."
            )

        # 7. Unir todo
        text = "\n\n".join(page_texts)

        # 8. Metadatos
        meta = {
            "pages": num_pages,
            "chars": len(text),
            "is_scanned": False,
            "source_type": "pdf",
        }

        return ProcessorResult(text=text, meta=meta, size_bytes=size_bytes)
