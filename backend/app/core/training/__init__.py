"""
Nuvora Core — Training Assistant
==================================
Módulo del Training Assistant (Fase 14.4).

Este paquete es RESPONSABLE de analizar el estado de preparación
del bot y sugerir mejoras al propietario.

NO modifica el Core de respuestas (/ask).
NO modifica Orchestrator, ResponseBuilder, ni retrievers.
Solo LEE datos existentes.
"""

from app.core.training.topics import (
    Topic,
    NichoCatalog,
    get_nicho_catalog,
    get_topics_for_nicho,
    get_topic_by_id,
    list_nichos,
)
from app.core.training.analyzer import TrainingAnalyzer


__all__ = [
    # Topic Catalog (14.4.1)
    "Topic",
    "NichoCatalog",
    "get_nicho_catalog",
    "get_topics_for_nicho",
    "get_topic_by_id",
    "list_nichos",
    # Analyzer (14.4.2)
    "TrainingAnalyzer",
]
