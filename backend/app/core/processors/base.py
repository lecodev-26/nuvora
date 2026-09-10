"""
Nuvora Core — Processors Base
================================
Define el contrato común para todos los procesadores de fuentes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


# ============================================================
# EXCEPCIONES
# ============================================================

class ProcessorError(Exception):
    """
    Error durante el procesamiento de una fuente.
    El mensaje se guardará en Source.error_message.
    """
    pass


# ============================================================
# RESULTADO
# ============================================================

@dataclass
class ProcessorResult:
    """
    Resultado de procesar una fuente.

    Atributos:
        text: texto plano extraído (listo para chunking)
        meta: metadatos específicos del tipo de fuente
        size_bytes: tamaño del contenido procesado en bytes
    """
    text: str
    meta: dict[str, Any] = field(default_factory=dict)
    size_bytes: int = 0

    def __post_init__(self):
        if self.size_bytes == 0 and self.text:
            self.size_bytes = len(self.text.encode("utf-8"))


# ============================================================
# INTERFAZ
# ============================================================

class BaseProcessor(ABC):
    """
    Interfaz abstracta para todos los procesadores.
    Cada procesador recibe un contenido (str o bytes) y devuelve un ProcessorResult.
    """

    @abstractmethod
    def process(self, content: str | bytes, **kwargs) -> ProcessorResult:
        """
        Extrae texto plano del contenido.

        Args:
            content: contenido a procesar (str o bytes)
            **kwargs: parámetros específicos del procesador

        Returns:
            ProcessorResult con texto plano y metadatos

        Raises:
            ProcessorError: si el procesamiento falla
        """
        pass
