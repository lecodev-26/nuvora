"""
Nuvora Core — AI: Schemas internos
=====================================
Define el JSON schema que se le pasa a la IA como contrato.

IMPORTANTE:
    - Este schema es DATO, no validación runtime.
    - La validación real la hace Pydantic (models/ai.py)
      + WorkflowValidator (14.5.4).
    - Los providers lo usan para generar outputs estructurados
      (Gemini responseSchema, Groq JSON mode, etc.).

Mantener SINCRONIZADO con:
    - app/models/workflow.py (NodeType, WorkflowStatus, WorkflowTrigger)
    - app/core/workflows/validator.py (reglas estructurales)
"""

from typing import Any


# ============================================================
# TIPOS VÁLIDOS (debe coincidir con 14.5.2)
# ============================================================

VALID_NODE_TYPES = [
    "start",
    "message",
    "question",
    "condition",
    "variable",
    "response",
    "end",
]


# ============================================================
# JSON SCHEMA DEL WORKFLOW (para providers con structured output)
# ============================================================

WORKFLOW_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "Nombre corto y descriptivo del workflow (máx 200 chars)",
        },
        "description": {
            "type": "string",
            "description": "Descripción opcional de qué hace el workflow",
        },
        "nodes": {
            "type": "array",
            "description": "Nodos del workflow. Debe haber exactamente 1 START y al menos 1 END.",
            "items": {
                "type": "object",
                "properties": {
                    "node_id": {
                        "type": "string",
                        "description": "ID lógico único. Formato: '{type}_{n}' (ej: 'start_1', 'message_2')",
                    },
                    "type": {
                        "type": "string",
                        "enum": VALID_NODE_TYPES,
                    },
                    "name": {
                        "type": "string",
                        "description": "Nombre descriptivo opcional",
                    },
                    "config": {
                        "type": "object",
                        "description": (
                            "Configuración específica por tipo. "
                            "message/response: {text}. "
                            "question: {text, variable}. "
                            "variable: {name, value}. "
                            "condition: {condition}. "
                            "start/end: {} o null."
                        ),
                        "additionalProperties": True,
                    },
                },
                "required": ["node_id", "type"],
            },
        },
        "transitions": {
            "type": "array",
            "description": "Conexiones entre nodos. CONDITION necesita ≥2 salidas.",
            "items": {
                "type": "object",
                "properties": {
                    "from_node_id": {"type": "string"},
                    "to_node_id": {"type": "string"},
                    "condition": {
                        "type": "string",
                        "description": "Expresión opcional (ej: 'age > 18'). Vacío = else implícito.",
                    },
                    "label": {
                        "type": "string",
                        "description": "Etiqueta opcional: 'true', 'false' o custom",
                    },
                    "order": {
                        "type": "integer",
                        "description": "Orden de evaluación (default 0)",
                    },
                },
                "required": ["from_node_id", "to_node_id"],
            },
        },
    },
    "required": ["name", "nodes", "transitions"],
}


# ============================================================
# JSON SCHEMA DE RESPUESTA COMPLETA (con explicación)
# ============================================================

GENERATE_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "workflow": WORKFLOW_JSON_SCHEMA,
        "explanation": {
            "type": "string",
            "description": "Explicación breve (2-4 frases) de qué hace el workflow",
        },
        "warnings": {
            "type": "array",
            "description": "Avisos opcionales sobre limitaciones o suposiciones hechas",
            "items": {"type": "string"},
        },
    },
    "required": ["workflow", "explanation"],
}


MODIFY_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "workflow": WORKFLOW_JSON_SCHEMA,
        "explanation": {
            "type": "string",
            "description": "Explicación del cambio realizado",
        },
        "warnings": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["workflow", "explanation"],
}


EXPLAIN_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "explanation": {
            "type": "string",
            "description": "Explicación clara del workflow en lenguaje humano (2-6 párrafos)",
        },
    },
    "required": ["explanation"],
}


ANALYZE_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "warnings": {
            "type": "array",
            "description": "Problemas detectados (ej: nodo huérfano, variable sin usar)",
            "items": {"type": "string"},
        },
        "suggestions": {
            "type": "array",
            "description": "Sugerencias de mejora (ej: añadir confirmación)",
            "items": {"type": "string"},
        },
    },
    "required": ["warnings", "suggestions"],
}


__all__ = [
    "VALID_NODE_TYPES",
    "WORKFLOW_JSON_SCHEMA",
    "GENERATE_RESPONSE_SCHEMA",
    "MODIFY_RESPONSE_SCHEMA",
    "EXPLAIN_RESPONSE_SCHEMA",
    "ANALYZE_RESPONSE_SCHEMA",
]
