"""
Nuvora Core — AI: Templates
=============================
Plantillas estáticas de workflows (SIN IA).

Estas plantillas son workflows predefinidos que el usuario puede
instanciar directamente sin gastar tokens de IA.

Útiles para:
    - Onboarding rápido
    - Ejemplos de buenas prácticas
    - Fallback si el usuario no tiene configurado un provider
"""

from typing import Optional

from app.models.ai import GeneratedWorkflow, TemplateInfo


# ============================================================
# PLANTILLAS
# ============================================================

_TEMPLATE_CATALOG: dict[str, dict] = {
    "customer_support": {
        "info": {
            "id": "customer_support",
            "name": "Atención al cliente",
            "description": "Saludo, identificación del problema y cierre. Ideal para soporte básico.",
            "icon": "🎧",
        },
        "workflow": {
            "name": "Atención al cliente",
            "description": "Workflow básico de soporte: saluda, pregunta el motivo y agradece.",
            "nodes": [
                {"node_id": "start_1", "type": "start", "name": "Inicio"},
                {"node_id": "message_1", "type": "message", "name": "Saludo",
                 "config": {"text": "¡Hola! Soy el asistente virtual. ¿En qué puedo ayudarte?"}},
                {"node_id": "question_1", "type": "question", "name": "Motivo",
                 "config": {"text": "Cuéntame, ¿cuál es tu consulta?", "variable": "consulta"}},
                {"node_id": "message_2", "type": "message", "name": "Agradecimiento",
                 "config": {"text": "Gracias por tu mensaje: {{consulta}}. Lo revisamos y te respondemos lo antes posible."}},
                {"node_id": "end_1", "type": "end", "name": "Fin"},
            ],
            "transitions": [
                {"from_node_id": "start_1", "to_node_id": "message_1", "order": 0},
                {"from_node_id": "message_1", "to_node_id": "question_1", "order": 0},
                {"from_node_id": "question_1", "to_node_id": "message_2", "order": 0},
                {"from_node_id": "message_2", "to_node_id": "end_1", "order": 0},
            ],
        },
    },
    "lead_qualification": {
        "info": {
            "id": "lead_qualification",
            "name": "Cualificación de leads",
            "description": "Recoge nombre y email, y clasifica según el interés del cliente.",
            "icon": "🎯",
        },
        "workflow": {
            "name": "Cualificación de leads",
            "description": "Recoge datos básicos y clasifica al lead según interés.",
            "nodes": [
                {"node_id": "start_1", "type": "start", "name": "Inicio"},
                {"node_id": "message_1", "type": "message", "name": "Bienvenida",
                 "config": {"text": "¡Hola! Cuéntame un poco sobre ti para poder ayudarte mejor."}},
                {"node_id": "question_1", "type": "question", "name": "Nombre",
                 "config": {"text": "¿Cómo te llamas?", "variable": "nombre"}},
                {"node_id": "question_2", "type": "question", "name": "Email",
                 "config": {"text": "¿Cuál es tu email?", "variable": "email"}},
                {"node_id": "question_3", "type": "question", "name": "Interés",
                 "config": {"text": "¿En qué estás interesado? (alta/media/baja)", "variable": "interes"}},
                {"node_id": "condition_1", "type": "condition", "name": "¿Alto interés?",
                 "config": {"condition": "interes == \"alta\""}},
                {"node_id": "message_alta", "type": "message", "name": "Lead caliente",
                 "config": {"text": "¡Genial, {{nombre}}! Un comercial te contactará hoy mismo en {{email}}."}},
                {"node_id": "message_normal", "type": "message", "name": "Lead normal",
                 "config": {"text": "Gracias, {{nombre}}. Te añadimos a nuestra lista y te contactamos pronto."}},
                {"node_id": "end_1", "type": "end", "name": "Fin"},
            ],
            "transitions": [
                {"from_node_id": "start_1", "to_node_id": "message_1", "order": 0},
                {"from_node_id": "message_1", "to_node_id": "question_1", "order": 0},
                {"from_node_id": "question_1", "to_node_id": "question_2", "order": 0},
                {"from_node_id": "question_2", "to_node_id": "question_3", "order": 0},
                {"from_node_id": "question_3", "to_node_id": "condition_1", "order": 0},
                {"from_node_id": "condition_1", "to_node_id": "message_alta", "order": 1, "condition": "interes == \"alta\"", "label": "true"},
                {"from_node_id": "condition_1", "to_node_id": "message_normal", "order": 2, "condition": "interes != \"alta\"", "label": "false"},
                {"from_node_id": "message_alta", "to_node_id": "end_1", "order": 0},
                {"from_node_id": "message_normal", "to_node_id": "end_1", "order": 0},
            ],
        },
    },
    "booking": {
        "info": {
            "id": "booking",
            "name": "Reserva de citas",
            "description": "Recoge los datos necesarios para agendar una cita y confirma la reserva.",
            "icon": "📅",
        },
        "workflow": {
            "name": "Reserva de citas",
            "description": "Flujo de reserva: día, hora y confirmación.",
            "nodes": [
                {"node_id": "start_1", "type": "start", "name": "Inicio"},
                {"node_id": "message_1", "type": "message", "name": "Bienvenida",
                 "config": {"text": "¡Hola! Vamos a agendar tu cita."}},
                {"node_id": "question_1", "type": "question", "name": "Nombre",
                 "config": {"text": "¿Cómo te llamas?", "variable": "nombre"}},
                {"node_id": "question_2", "type": "question", "name": "Día",
                 "config": {"text": "¿Qué día te viene bien?", "variable": "dia"}},
                {"node_id": "question_3", "type": "question", "name": "Hora",
                 "config": {"text": "¿A qué hora?", "variable": "hora"}},
                {"node_id": "response_1", "type": "response", "name": "Confirmación",
                 "config": {"text": "Perfecto, {{nombre}}. Tu cita queda reservada para el {{dia}} a las {{hora}}. ¡Nos vemos!"}},
                {"node_id": "end_1", "type": "end", "name": "Fin"},
            ],
            "transitions": [
                {"from_node_id": "start_1", "to_node_id": "message_1", "order": 0},
                {"from_node_id": "message_1", "to_node_id": "question_1", "order": 0},
                {"from_node_id": "question_1", "to_node_id": "question_2", "order": 0},
                {"from_node_id": "question_2", "to_node_id": "question_3", "order": 0},
                {"from_node_id": "question_3", "to_node_id": "response_1", "order": 0},
                {"from_node_id": "response_1", "to_node_id": "end_1", "order": 0},
            ],
        },
    },
    "faq": {
        "info": {
            "id": "faq",
            "name": "FAQ rápido",
            "description": "Flujo mínimo para responder preguntas frecuentes sin ramificaciones.",
            "icon": "❓",
        },
        "workflow": {
            "name": "FAQ rápido",
            "description": "Pregunta al usuario y responde con un mensaje genérico.",
            "nodes": [
                {"node_id": "start_1", "type": "start", "name": "Inicio"},
                {"node_id": "message_1", "type": "message", "name": "Bienvenida",
                 "config": {"text": "¡Hola! Pregúntame lo que necesites."}},
                {"node_id": "question_1", "type": "question", "name": "Pregunta",
                 "config": {"text": "¿Cuál es tu pregunta?", "variable": "pregunta"}},
                {"node_id": "response_1", "type": "response", "name": "Respuesta",
                 "config": {"text": "Gracias por tu pregunta sobre '{{pregunta}}'. En breve te responderemos."}},
                {"node_id": "end_1", "type": "end", "name": "Fin"},
            ],
            "transitions": [
                {"from_node_id": "start_1", "to_node_id": "message_1", "order": 0},
                {"from_node_id": "message_1", "to_node_id": "question_1", "order": 0},
                {"from_node_id": "question_1", "to_node_id": "response_1", "order": 0},
                {"from_node_id": "response_1", "to_node_id": "end_1", "order": 0},
            ],
        },
    },
}


# ============================================================
# API PÚBLICA
# ============================================================

def list_templates() -> list[TemplateInfo]:
    """Lista las plantillas disponibles (sin IA)."""
    return [TemplateInfo(**t["info"]) for t in _TEMPLATE_CATALOG.values()]


def get_template_workflow(template_id: str) -> Optional[GeneratedWorkflow]:
    """
    Devuelve el workflow de una plantilla.

    Returns:
        GeneratedWorkflow si existe, None si no.
    """
    entry = _TEMPLATE_CATALOG.get(template_id)
    if not entry:
        return None
    return GeneratedWorkflow(**entry["workflow"])


def list_template_ids() -> list[str]:
    """Devuelve los IDs de plantillas disponibles."""
    return list(_TEMPLATE_CATALOG.keys())


__all__ = [
    "list_templates",
    "get_template_workflow",
    "list_template_ids",
]
