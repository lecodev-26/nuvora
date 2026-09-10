"""
Nuvora Core — Training Assistant: Topic Catalog
=================================================
Catálogo data-driven de temas esperados por nicho.

IMPORTANTE — REGLA ARQUITECTÓNICA:
    Este archivo es DATOS, no LÓGICA.
    NO contiene `if nicho == "..."`.
    Solo define catálogos y expone funciones puras de consulta.

Añadir un nuevo nicho = añadir un `NichoCatalog` al registro NICHOS.
Añadir un tema a un nicho = añadir un `Topic` a su catálogo.
"""

from dataclasses import dataclass
from typing import Optional


# ============================================================
# DATACLASSES
# ============================================================

@dataclass(frozen=True)
class Topic:
    """
    Un tema esperado en el conocimiento de un bot.

    Atributos:
        id: identificador único (snake_case)
        label: nombre legible para UI
        description: explicación breve (para UI y para recomendaciones)
        keywords: señales para detectar cobertura (Fase 14.4.3)
        icon: emoji opcional para UI
    """
    id: str
    label: str
    description: str
    keywords: tuple[str, ...]
    icon: str = ""


@dataclass(frozen=True)
class NichoCatalog:
    """Catálogo de temas para un nicho."""
    nicho_id: str
    display_name: str
    topics: tuple[Topic, ...]


# ============================================================
# CATÁLOGO GENÉRICO (base)
# ============================================================

_GENERIC_TOPICS: tuple[Topic, ...] = (
    Topic(
        id="descripcion",
        label="Descripción",
        description="Información general sobre el negocio o proyecto",
        keywords=(
            "quiénes somos", "sobre", "negocio", "empresa",
            "proyecto", "comunidad", "dedicamos", "somos",
        ),
        icon="📋",
    ),
    Topic(
        id="servicios",
        label="Servicios / Productos",
        description="Qué ofrece el negocio o proyecto",
        keywords=(
            "servicio", "servicios", "producto", "productos",
            "ofrecemos", "vendemos", "proporcionamos", "brindamos",
        ),
        icon="🎯",
    ),
    Topic(
        id="horarios",
        label="Horarios",
        description="Horarios de apertura, cierre y disponibilidad",
        keywords=(
            "horario", "horarios", "abrimos", "cerramos",
            "apertura", "cierre", "lunes", "martes", "miércoles",
            "jueves", "viernes", "sábado", "domingo",
            "mañana", "tarde", "noche",
        ),
        icon="🕐",
    ),
    Topic(
        id="contacto",
        label="Contacto",
        description="Formas de contacto con el negocio o proyecto",
        keywords=(
            "teléfono", "email", "correo", "contacto",
            "llamar", "escribir", "whatsapp", "redes",
        ),
        icon="📞",
    ),
    Topic(
        id="ubicacion",
        label="Ubicación",
        description="Dónde se encuentra el negocio",
        keywords=(
            "dirección", "dónde", "ubicación", "llegar",
            "calle", "avenida", "plaza", "ciudad", "barrio",
            "mapa", "cómo llegar",
        ),
        icon="📍",
    ),
    Topic(
        id="precios",
        label="Precios",
        description="Precios, tarifas y costes",
        keywords=(
            "precio", "precios", "coste", "costes", "tarifa",
            "tarifas", "cuánto", "cuánto cuesta", "gratis",
        ),
        icon="💶",
    ),
    Topic(
        id="politicas",
        label="Políticas",
        description="Normas, políticas y condiciones",
        keywords=(
            "política", "políticas", "normas", "condiciones",
            "reglas", "requisitos",
        ),
        icon="📜",
    ),
    Topic(
        id="faq",
        label="Preguntas frecuentes",
        description="Preguntas recurrentes de los usuarios",
        keywords=(
            "pregunta", "preguntas", "duda", "dudas",
            "frecuente", "frecuentes",
        ),
        icon="❓",
    ),
)


# ============================================================
# HELPERS
# ============================================================

def _merge_with_generic(
    specific: tuple[Topic, ...],
    exclude_ids: Optional[tuple[str, ...]] = None,
) -> tuple[Topic, ...]:
    """
    Fusiona topics específicos con los genéricos.
    Si un topic específico comparte id con uno genérico, el específico
    gana (por eso excluimos el genérico).

    Args:
        specific: topics específicos del nicho
        exclude_ids: ids genéricos a excluir (porque hay versión específica)

    Returns:
        Tuple de topics: específicos primero, luego genéricos no excluidos.
    """
    exclude = set(exclude_ids or ())
    generic_filtered = tuple(t for t in _GENERIC_TOPICS if t.id not in exclude)
    return specific + generic_filtered


# ============================================================
# CATÁLOGOS POR NICHO
# ============================================================

# --- Restaurantes ---
_RESTAURANTES_TOPICS: tuple[Topic, ...] = (
    Topic(
        id="menu",
        label="Menú",
        description="Platos, bebidas y especialidades disponibles",
        keywords=(
            "menú", "menu", "carta", "plato", "platos",
            "especialidad", "especialidades", "bebida", "bebidas",
        ),
        icon="🍽️",
    ),
    Topic(
        id="reservas",
        label="Reservas",
        description="Política de reservas y cómo reservar",
        keywords=(
            "reserva", "reservas", "reservar", "mesa", "mesas",
            "aforo", "grupos",
        ),
        icon="📅",
    ),
    Topic(
        id="delivery",
        label="Delivery / Reparto",
        description="Servicio de reparto a domicilio",
        keywords=(
            "delivery", "reparto", "domicilio", "envío", "envíos",
        ),
        icon="🛵",
    ),
    Topic(
        id="alergenos",
        label="Alérgenos y dietas",
        description="Información sobre alérgenos y opciones dietéticas",
        keywords=(
            "alérgeno", "alérgenos", "alergia", "alergias",
            "vegetariano", "vegetariana", "vegano", "vegana",
            "sin gluten", "intolerancia",
        ),
        icon="⚠️",
    ),
)


# --- Peluquerías ---
_PELUQUERIAS_TOPICS: tuple[Topic, ...] = (
    Topic(
        id="reservas",
        label="Reservas / Citas",
        description="Cómo reservar cita",
        keywords=(
            "reserva", "reservas", "reservar", "cita", "citas",
            "peluquero", "peluquera", "estilista",
        ),
        icon="📅",
    ),
    Topic(
        id="productos",
        label="Productos",
        description="Productos utilizados o vendidos",
        keywords=(
            "producto", "productos", "marca", "marcas",
            "champú", "tratamiento", "tinte",
        ),
        icon="🧴",
    ),
)


# --- Hoteles ---
_HOTELES_TOPICS: tuple[Topic, ...] = (
    Topic(
        id="habitaciones",
        label="Habitaciones",
        description="Tipos de habitaciones y servicios",
        keywords=(
            "habitación", "habitaciones", "suite", "suites",
            "doble", "individual", "familiar", "cama",
        ),
        icon="🛏️",
    ),
    Topic(
        id="checkin",
        label="Check-in / Check-out",
        description="Horarios y proceso de entrada y salida",
        keywords=(
            "check-in", "checkin", "check-out", "checkout",
            "entrada", "salida", "llegada", "marcharse",
        ),
        icon="🔑",
    ),
    Topic(
        id="servicios_extra",
        label="Servicios extra",
        description="Servicios adicionales (wifi, parking, desayuno, spa)",
        keywords=(
            "wifi", "parking", "desayuno", "spa", "piscina",
            "gimnasio", "servicio", "servicios extra",
        ),
        icon="✨",
    ),
)


# --- Gimnasios ---
_GIMNASIOS_TOPICS: tuple[Topic, ...] = (
    Topic(
        id="clases",
        label="Clases",
        description="Clases y actividades disponibles",
        keywords=(
            "clase", "clases", "yoga", "pilates", "spinning",
            "zumba", "crossfit", "actividad", "actividades",
        ),
        icon="🧘",
    ),
    Topic(
        id="instalaciones",
        label="Instalaciones",
        description="Instalaciones y equipamiento",
        keywords=(
            "instalación", "instalaciones", "sala", "salas",
            "musculación", "cardio", "piscina", "vestuario",
        ),
        icon="🏋️",
    ),
    Topic(
        id="cuotas",
        label="Cuotas",
        description="Cuotas, bonos y precios",
        keywords=(
            "cuota", "cuotas", "bono", "bonos", "mensualidad",
            "matrícula", "tarifa",
        ),
        icon="💶",
    ),
)


# --- Clínicas ---
_CLINICAS_TOPICS: tuple[Topic, ...] = (
    Topic(
        id="citas",
        label="Citas",
        description="Cómo pedir cita y política de cancelación",
        keywords=(
            "cita", "citas", "pedir cita", "reservar cita",
            "consulta", "consultas",
        ),
        icon="📅",
    ),
    Topic(
        id="especialidades",
        label="Especialidades",
        description="Especialidades y servicios médicos",
        keywords=(
            "especialidad", "especialidades", "odontología",
            "dermatología", "fisioterapia", "consulta médica",
        ),
        icon="🩺",
    ),
    Topic(
        id="seguros",
        label="Seguros",
        description="Seguros aceptados y formas de pago",
        keywords=(
            "seguro", "seguros", "mutua", "mutuas",
            "cobertura", "reembolso",
        ),
        icon="🏥",
    ),
)


# --- Tiendas ---
_TIENDAS_TOPICS: tuple[Topic, ...] = (
    Topic(
        id="envios",
        label="Envíos",
        description="Política de envíos y tiempos de entrega",
        keywords=(
            "envío", "envíos", "enviar", "reparto",
            "entrega", "mensajería", "paquetería",
        ),
        icon="📦",
    ),
    Topic(
        id="devoluciones",
        label="Devoluciones",
        description="Política de devoluciones y cambios",
        keywords=(
            "devolución", "devoluciones", "devolver",
            "cambio", "cambios", "reembolso",
        ),
        icon="↩️",
    ),
    Topic(
        id="pagos",
        label="Pagos",
        description="Métodos de pago aceptados",
        keywords=(
            "pago", "pagos", "tarjeta", "efectivo", "bizum",
            "paypal", "transferencia",
        ),
        icon="💳",
    ),
)


# ============================================================
# REGISTRO DE NICHOS
# ============================================================

NICHOS: dict[str, NichoCatalog] = {
    "restaurantes": NichoCatalog(
        nicho_id="restaurantes",
        display_name="Restaurantes",
        topics=_merge_with_generic(
            _RESTAURANTES_TOPICS,
            exclude_ids=("servicios",),  # El menú cubre "servicios"
        ),
    ),
    "peluquerias": NichoCatalog(
        nicho_id="peluquerias",
        display_name="Peluquerías",
        topics=_merge_with_generic(
            _PELUQUERIAS_TOPICS,
            exclude_ids=("servicios",),  # Los servicios específicos ganan
        ),
    ),
    "hoteles": NichoCatalog(
        nicho_id="hoteles",
        display_name="Hoteles",
        topics=_merge_with_generic(
            _HOTELES_TOPICS,
            exclude_ids=("servicios",),  # servicios_extra gana
        ),
    ),
    "gimnasios": NichoCatalog(
        nicho_id="gimnasios",
        display_name="Gimnasios",
        topics=_merge_with_generic(
            _GIMNASIOS_TOPICS,
            exclude_ids=("servicios",),  # clases e instalaciones ganan
        ),
    ),
    "clinicas": NichoCatalog(
        nicho_id="clinicas",
        display_name="Clínicas",
        topics=_merge_with_generic(
            _CLINICAS_TOPICS,
            exclude_ids=("servicios",),  # especialidades gana
        ),
    ),
    "tiendas": NichoCatalog(
        nicho_id="tiendas",
        display_name="Tiendas",
        topics=_merge_with_generic(
            _TIENDAS_TOPICS,
            exclude_ids=("servicios",),  # productos genéricos ya cubren
        ),
    ),
    "otro": NichoCatalog(
        nicho_id="otro",
        display_name="Otro negocio",
        topics=_GENERIC_TOPICS,
    ),
}


# Nicho por defecto cuando no hay match
_DEFAULT_NICHO = "otro"


# ============================================================
# API PÚBLICA
# ============================================================

def get_nicho_catalog(nicho_id: Optional[str]) -> NichoCatalog:
    """
    Devuelve el catálogo de un nicho.

    Si `nicho_id` es None o no existe, devuelve el catálogo "otro".
    """
    if not nicho_id:
        return NICHOS[_DEFAULT_NICHO]
    return NICHOS.get(nicho_id, NICHOS[_DEFAULT_NICHO])


def get_topics_for_nicho(nicho_id: Optional[str]) -> list[Topic]:
    """Devuelve la lista de temas esperados para un nicho."""
    return list(get_nicho_catalog(nicho_id).topics)


def get_topic_by_id(nicho_id: Optional[str], topic_id: str) -> Optional[Topic]:
    """Busca un tema específico dentro de un nicho."""
    for t in get_nicho_catalog(nicho_id).topics:
        if t.id == topic_id:
            return t
    return None


def list_nichos() -> list[str]:
    """Devuelve la lista de nichos disponibles."""
    return list(NICHOS.keys())
