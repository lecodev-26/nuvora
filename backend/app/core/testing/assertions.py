"""
Nuvora Core — Testing: Assertion Engine
==========================================
Evalúa assertions contra un ExecutionResult del WorkflowEngine (14.5).

FILOSOFÍA:
    - Determinista. Sin IA.
    - Solo lee. No modifica nada.
    - Cada assertion devuelve PASSED o FAILED, nunca ERROR (los errores
      técnicos se capturan en el Runner).
    - No duplica lógica del Engine. Solo evalúa el resultado.

10 TIPOS DE ASSERTION:
    1.  response_contains       → algún output contiene `value`
    2.  response_equals         → algún output == `value` (exacto)
    3.  response_not_contains   → NINGÚN output contiene `value`
    4.  node_visited            → el history contiene `node_id`
    5.  node_not_visited        → el history NO contiene `node_id`
    6.  variable_equals         → variables[`variable`] == `expected`
    7.  variable_exists         → `variable` está en variables
    8.  variable_not_exists     → `variable` NO está en variables
    9.  reaches_end             → status == COMPLETED
    10. max_steps               → steps_used <= `max_steps`
"""

from typing import Any

from app.models.test import TestAssertion, AssertionResult
from app.core.workflows.execution import ExecutionResult, ExecutionStatus


# ============================================================
# API PÚBLICA
# ============================================================

def evaluate_assertion(
    assertion: TestAssertion,
    result: ExecutionResult,
) -> AssertionResult:
    """
    Evalúa una sola assertion contra el resultado de una ejecución.

    Args:
        assertion: la assertion a evaluar.
        result: ExecutionResult del WorkflowEngine.

    Returns:
        AssertionResult con passed=True/False, expected, actual y message.

    Raises:
        TestAssertionError: si el tipo de assertion es desconocido
                            (no debería pasar tras la validación Pydantic).
    """
    t = assertion.type

    if t == "response_contains":
        return _check_response_contains(assertion, result)
    if t == "response_equals":
        return _check_response_equals(assertion, result)
    if t == "response_not_contains":
        return _check_response_not_contains(assertion, result)
    if t == "node_visited":
        return _check_node_visited(assertion, result)
    if t == "node_not_visited":
        return _check_node_not_visited(assertion, result)
    if t == "variable_equals":
        return _check_variable_equals(assertion, result)
    if t == "variable_exists":
        return _check_variable_exists(assertion, result)
    if t == "variable_not_exists":
        return _check_variable_not_exists(assertion, result)
    if t == "reaches_end":
        return _check_reaches_end(assertion, result)
    if t == "max_steps":
        return _check_max_steps(assertion, result)

    # No debería llegar aquí (Pydantic valida el Literal)
    from app.core.testing.errors import TestAssertionError
    raise TestAssertionError(
        assertion_type=t,
        message="Tipo de assertion desconocido",
    )


def evaluate_all_assertions(
    assertions: list[TestAssertion],
    result: ExecutionResult,
) -> list[AssertionResult]:
    """
    Evalúa TODAS las assertions contra el resultado.
    NUNCA lanza excepción: cada assertion devuelve PASSED o FAILED.
    Si una assertion falla técnicamente, se marca como failed con mensaje.
    """
    results: list[AssertionResult] = []
    for a in assertions:
        try:
            results.append(evaluate_assertion(a, result))
        except Exception as e:
            # Fallback: assertion mal formada o error interno
            results.append(AssertionResult(
                type=a.type,
                passed=False,
                expected=None,
                actual=None,
                message=f"Error evaluando assertion: {type(e).__name__}: {e}",
            ))
    return results


def summarize_assertions(results: list[AssertionResult]) -> tuple[int, int]:
    """
    Devuelve (passed_count, failed_count) de una lista de AssertionResult.
    """
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    return passed, failed


# ============================================================
# HELPERS INTERNOS
# ============================================================

def _get_all_output_texts(result: ExecutionResult) -> list[str]:
    """
    Extrae todos los textos de los outputs.
    Cada output tiene forma {"step": N, "node_id": ..., "type": ..., "text": "..."}
    """
    texts: list[str] = []
    for o in result.outputs or []:
        if isinstance(o, dict):
            t = o.get("text")
            if isinstance(t, str) and t:
                texts.append(t)
    return texts


def _get_all_node_ids(result: ExecutionResult) -> list[str]:
    """Extrae todos los node_id del history."""
    ids: list[str] = []
    for h in result.history or []:
        if isinstance(h, dict):
            nid = h.get("node_id")
            if isinstance(nid, str) and nid:
                ids.append(nid)
    return ids


# ============================================================
# CHECKS INDIVIDUALES
# ============================================================

def _check_response_contains(assertion: TestAssertion, result: ExecutionResult) -> AssertionResult:
    needle = assertion.value or ""
    texts = _get_all_output_texts(result)
    found = any(needle in t for t in texts)
    return AssertionResult(
        type=assertion.type,
        passed=found,
        expected=f"algún output contiene '{needle}'",
        actual=texts,
        message=None if found else f"Ningún output contiene '{needle}'",
    )


def _check_response_equals(assertion: TestAssertion, result: ExecutionResult) -> AssertionResult:
    needle = assertion.value or ""
    texts = _get_all_output_texts(result)
    found = any(t == needle for t in texts)
    return AssertionResult(
        type=assertion.type,
        passed=found,
        expected=f"algún output == '{needle}'",
        actual=texts,
        message=None if found else f"Ningún output es exactamente '{needle}'",
    )


def _check_response_not_contains(assertion: TestAssertion, result: ExecutionResult) -> AssertionResult:
    needle = assertion.value or ""
    texts = _get_all_output_texts(result)
    found = any(needle in t for t in texts)
    passed = not found
    return AssertionResult(
        type=assertion.type,
        passed=passed,
        expected=f"ningún output contiene '{needle}'",
        actual=texts,
        message=None if passed else f"Algún output contiene '{needle}' (no esperado)",
    )


def _check_node_visited(assertion: TestAssertion, result: ExecutionResult) -> AssertionResult:
    node_id = assertion.node_id or ""
    ids = _get_all_node_ids(result)
    passed = node_id in ids
    return AssertionResult(
        type=assertion.type,
        passed=passed,
        expected=f"nodo '{node_id}' visitado",
        actual=ids,
        message=None if passed else f"El nodo '{node_id}' NO fue visitado",
    )


def _check_node_not_visited(assertion: TestAssertion, result: ExecutionResult) -> AssertionResult:
    node_id = assertion.node_id or ""
    ids = _get_all_node_ids(result)
    passed = node_id not in ids
    return AssertionResult(
        type=assertion.type,
        passed=passed,
        expected=f"nodo '{node_id}' NO visitado",
        actual=ids,
        message=None if passed else f"El nodo '{node_id}' fue visitado (no esperado)",
    )


def _check_variable_equals(assertion: TestAssertion, result: ExecutionResult) -> AssertionResult:
    var = assertion.variable or ""
    expected = assertion.expected
    variables = result.variables or {}
    actual = variables.get(var)
    passed = var in variables and actual == expected
    return AssertionResult(
        type=assertion.type,
        passed=passed,
        expected=f"{var} == {expected!r}",
        actual={var: actual},
        message=None if passed else f"{var} = {actual!r} (esperado {expected!r})",
    )


def _check_variable_exists(assertion: TestAssertion, result: ExecutionResult) -> AssertionResult:
    var = assertion.variable or ""
    variables = result.variables or {}
    passed = var in variables
    return AssertionResult(
        type=assertion.type,
        passed=passed,
        expected=f"variable '{var}' existe",
        actual=list(variables.keys()),
        message=None if passed else f"La variable '{var}' NO existe",
    )


def _check_variable_not_exists(assertion: TestAssertion, result: ExecutionResult) -> AssertionResult:
    var = assertion.variable or ""
    variables = result.variables or {}
    passed = var not in variables
    return AssertionResult(
        type=assertion.type,
        passed=passed,
        expected=f"variable '{var}' NO existe",
        actual=list(variables.keys()),
        message=None if passed else f"La variable '{var}' existe (no esperado)",
    )


def _check_reaches_end(assertion: TestAssertion, result: ExecutionResult) -> AssertionResult:
    passed = result.status == ExecutionStatus.COMPLETED
    return AssertionResult(
        type=assertion.type,
        passed=passed,
        expected="status == COMPLETED",
        actual=result.status.value,
        message=None if passed else f"El workflow terminó con status '{result.status.value}'",
    )


def _check_max_steps(assertion: TestAssertion, result: ExecutionResult) -> AssertionResult:
    max_steps = assertion.max_steps or 0
    passed = result.steps_used <= max_steps
    return AssertionResult(
        type=assertion.type,
        passed=passed,
        expected=f"steps_used <= {max_steps}",
        actual=result.steps_used,
        message=None if passed else f"steps_used={result.steps_used} > {max_steps}",
    )


__all__ = [
    "evaluate_assertion",
    "evaluate_all_assertions",
    "summarize_assertions",
]
