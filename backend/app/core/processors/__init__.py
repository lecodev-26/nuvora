"""
Nuvora Core — Processors
Exporta los procesadores disponibles.
"""

from app.core.processors.base import BaseProcessor, ProcessorResult, ProcessorError
from app.core.processors.text_processor import TextProcessor
from app.core.processors.url_processor import URLProcessor
from app.core.processors.pdf_processor import PDFProcessor
from app.core.processors.csv_processor import CSVProcessor
from app.core.processors.chunker import Chunker, Chunk


__all__ = [
    "BaseProcessor",
    "ProcessorResult",
    "ProcessorError",
    "TextProcessor",
    "URLProcessor",
    "PDFProcessor",
    "CSVProcessor",
    "Chunker",
    "Chunk",
]
