"""
Nuvora Core — Workflows: Conditions
======================================
Parser y evaluador SEGURO de condiciones para nodos CONDITION.

PROHIBIDO: eval() / exec() / compile(). Nunca.
Implementamos un parser controlado que solo soporta:

    - Comparaciones:  ==  !=  >  <  >=  <=
    - Operandos:
        - variable           (ej: age, name, status)
        - literal numérico   (ej: 18, 3.14, -5)
        - literal string     (ej: "Manuel", 'admin')
        - literal booleano   (true / false / True / False)
        - literal None       (null / None)
    - Espacios en blanco alrededor del operador.

NO soportamos (por ahora):
    - Operadores lógicos: and, or, not
    - Paréntesis
    - Aritmética: + - * /
    - Funciones

En 14.5.6b o posterior se puede extender sin romper el diseño.

USO:
    from app.core.workflows.conditions import evaluate_condition

    result = evaluate_condition("age > 18", {"age": 21})  # → True
    result = evaluate_condition('name == "Manuel"', {"name": "Manuel"})  # → True
"""

import re
from typing import Any

from app.core.workflows.errors import ConditionError


# ============================================================
# OPERADORES SOPORTADOS
# ============================================================
# Orden importa: los de 2 caracteres primero, para que el regex
# no capture '>' antes de '>='.
_OPERATORS = ["==", "!=", ">=", "<=", ">", "<"]

# Regex principal: OPERANDO   OPERADOR   OPERANDO
# Nota: el operador puede tener espacios alrededor.
_CONDITION_RE = re.compile(
    r"^\s*(?P<left>[^\s=!<>]+)\s*(?P<op>==|!=|>=|<=|>|<)\s*(?P<right>.+?)\s*$"
)


# ============================================================
# PARSER DE LITERALES
# ============================================================

def _parse_literal(raw: str) -> tuple[bool, Any]:
    """
    Intenta parsear `raw` como literal.

    Returns:
        (is_literal, value)
        - (True, value) si es un literal reconocido.
        - (False, None) si NO es un literal (será tratado como variable).
    """
    raw = raw.strip()
    if not raw:
        return False, None

    # Booleano
    if raw in ("true", "True"):
        return True, True
    if raw in ("false", "False"):
        return True, False

    # None / null
    if raw in ("null", "None", "none"):
        return True, None

    # Número (int o float, con signo opcional)
    # OJO: solo si es un número bien formado (no "18abc")
    if re.fullmatch(r"-?\d+", raw):
        return True, int(raw)
    if re.fullmatch(r"-?\d+\.\d+", raw):
        return True, float(raw)

    # String entre comillas dobles o simples
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ("'", '"'):
        return True, raw[1:-1]

    # No es literal → variable
    return False, None


# ============================================================
# RESOLUCIÓN DE OPERANDOS
# ============================================================

def _resolve_operand(raw: str, variables: dict[str, Any]) -> Any:
    """
    Resuelve un operando:
        - Si es literal → devuelve el valor literal.
        - Si es variable → busca en `variables`.
        - Si no existe → ConditionError.
    """
    is_lit, value = _parse_literal(raw)
    if is_lit:
        return value

    # Es una variable (por nombre)
    name = raw.strip()
    if name not in variables:
        raise ConditionError(
            expression=raw,
            message=f"Variable '{name}' no definida en el contexto",
        )
    return variables[name]


# ============================================================
# EVALUACIÓN DE COMPARACIONES
# ============================================================

def _compare(left: Any, op: str, right: Any, expression: str) -> bool:
    """
    Aplica el operador. Lanza ConditionError si los tipos no son comparables.
    """
    try:
        if op == "==":
            return left == right
        if op == "!=":
            return left != right
        if op == ">":
            return left > right
        if op == "<":
            return left < right
        if op == ">=":
            return left >= right
        if op == "<=":
            return left <= right
    except TypeError as e:
        raise ConditionError(
            expression=expression,
            message=f"Tipos no comparables: {type(left).__name__} {op} {type(right).__name__}",
        ) from e

    raise ConditionError(
        expression=expression,
        message=f"Operador no soportado: '{op}'",
    )


# ============================================================
# API PÚBLICA
# ============================================================

def evaluate_condition(expression: str, variables: dict[str, Any]) -> bool:
    """
    Evalúa una condición SEGURA contra un diccionario de variables.

    Args:
        expression: string con la condición. Ej: "age > 18", 'name == "Manuel"'.
        variables: dict con las variables de ejecución.

    Returns:
        bool: resultado de la comparación.

    Raises:
        ConditionError: si la expresión es inválida, tiene tipos incompatibles
                        o usa variables no definidas.
    """
    if expression is None or not isinstance(expression, str):
        raise ConditionError(
            expression=str(expression),
            message="La condición debe ser un string no vacío",
        )

    expression_stripped = expression.strip()
    if not expression_stripped:
        raise ConditionError(
            expression=expression,
            message="La condición está vacía",
        )

    match = _CONDITION_RE.match(expression_stripped)
    if not match:
        raise ConditionError(
            expression=expression,
            message="Formato inválido. Se esperaba: <operando> <operador> <operando>",
        )

    left_raw = match.group("left")
    op = match.group("op")
    right_raw = match.group("right")

    if op not in _OPERATORS:
        raise ConditionError(
            expression=expression,
            message=f"Operador no soportado: '{op}'",
        )

    left = _resolve_operand(left_raw, variables)
    right = _resolve_operand(right_raw, variables)

    return _compare(left, op, right, expression_stripped)


def validate_condition_expression(expression: str) -> None:
    """
    Valida la SINTAXIS de una expresión sin necesidad de variables.

    Útil en el validator (14.5.4) o en el router (14.5.7) para rechazar
    workflows con condiciones mal formadas antes de guardarlos.

    Raises:
        ConditionError: si la expresión es inválida sintácticamente.
    """
    if not isinstance(expression, str) or not expression.strip():
        raise ConditionError(
            expression=str(expression),
            message="La condición debe ser un string no vacío",
        )

    match = _CONDITION_RE.match(expression.strip())
    if not match:
        raise ConditionError(
            expression=expression,
            message="Formato inválido. Se esperaba: <operando> <operador> <operando>",
        )

    op = match.group("op")
    if op not in _OPERATORS:
        raise ConditionError(
            expression=expression,
            message=f"Operador no soportado: '{op}'",
        )


__all__ = [
    "evaluate_condition",
    "validate_condition_expression",
]
