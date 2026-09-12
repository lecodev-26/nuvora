"""
Nuvora Core — Workflows: Variables
=====================================
Interpolación SEGURA de variables en textos.

Sintaxis soportada:
    {{nombre}}
    {{age}}
    {{user.name}}   ← no soportado todavía (solo flat)

Reglas:
    - Si la variable existe en el contexto → se sustituye por su valor (str).
    - Si la variable NO existe → se deja literal "{{nombre}}" (no rompe).
    - Si el texto no tiene "{{...}}" → se devuelve tal cual.
    - Espacios internos permitidos: {{ nombre }} == {{nombre}}.

PROHIBIDO: eval() / exec() / compile(). Nunca.
"""

import re
from typing import Any


# Regex que captura "{{variable}}" (permitiendo espacios internos)
_VAR_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


def interpolate(text: str, variables: dict[str, Any]) -> str:
    """
    Sustituye las ocurrencias de {{var}} en `text` por su valor en `variables`.

    Args:
        text: texto con posibles placeholders.
        variables: dict con las variables de ejecución.

    Returns:
        Texto con las variables sustituidas.
        Si una variable no existe, se deja el placeholder original.

    Ejemplos:
        >>> interpolate("Hola {{name}}", {"name": "Manuel"})
        'Hola Manuel'

        >>> interpolate("Hola {{name}}", {})
        'Hola {{name}}'

        >>> interpolate("Sin variables", {"x": 1})
        'Sin variables'

        >>> interpolate("{{a}} y {{b}}", {"a": 1, "b": 2})
        '1 y 2'
    """
    if text is None:
        return ""

    if not isinstance(text, str):
        text = str(text)

    def _replace(match: re.Match) -> str:
        var_name = match.group(1)
        if var_name in variables:
            return str(variables[var_name])
        # No existe → dejar el placeholder intacto
        return match.group(0)

    return _VAR_RE.sub(_replace, text)


def extract_variable_names(text: str) -> list[str]:
    """
    Devuelve la lista de nombres de variables referenciadas en `text`.

    Útil para validación (saber qué variables necesita un workflow).

    Ejemplo:
        >>> extract_variable_names("Hola {{name}}, edad {{age}}")
        ['name', 'age']
    """
    if not isinstance(text, str):
        return []
    return _VAR_RE.findall(text)


__all__ = [
    "interpolate",
    "extract_variable_names",
]
