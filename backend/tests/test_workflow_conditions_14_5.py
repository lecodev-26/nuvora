"""
Tests — Subfase 14.5.6
Verifica el parser y evaluador SEGURO de condiciones.

Casos cubiertos:
    1-19. (ver más abajo)
    20. Sin eval() / exec() en el código (ignorando comentarios y re.compile)
"""

import sys
import os
import inspect
import re as re_module

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.workflows.conditions import (
    evaluate_condition,
    validate_condition_expression,
)
from app.core.workflows.errors import ConditionError


# ============================================================
# TESTS
# ============================================================

def test_int_greater_true():
    print("\n" + "=" * 70)
    print("TEST 1: age > 18 con age=21 → True")
    print("=" * 70)
    assert evaluate_condition("age > 18", {"age": 21}) is True
    print("✅ True")


def test_int_greater_false():
    print("\n" + "=" * 70)
    print("TEST 2: age > 18 con age=15 → False")
    print("=" * 70)
    assert evaluate_condition("age > 18", {"age": 15}) is False
    print("✅ False")


def test_int_greater_equal_border():
    print("\n" + "=" * 70)
    print("TEST 3: age >= 18 con age=18 → True (borde)")
    print("=" * 70)
    assert evaluate_condition("age >= 18", {"age": 18}) is True
    print("✅ True (borde)")


def test_int_less_false():
    print("\n" + "=" * 70)
    print("TEST 4: age < 18 con age=21 → False")
    print("=" * 70)
    assert evaluate_condition("age < 18", {"age": 21}) is False
    print("✅ False")


def test_int_less_equal_border():
    print("\n" + "=" * 70)
    print("TEST 5: age <= 18 con age=18 → True (borde)")
    print("=" * 70)
    assert evaluate_condition("age <= 18", {"age": 18}) is True
    print("✅ True (borde)")


def test_string_equal_true():
    print("\n" + "=" * 70)
    print("TEST 6: name == \"Manuel\" con name=Manuel → True")
    print("=" * 70)
    assert evaluate_condition('name == "Manuel"', {"name": "Manuel"}) is True
    print("✅ True")


def test_string_equal_false():
    print("\n" + "=" * 70)
    print("TEST 7: name == \"Ana\" con name=Manuel → False")
    print("=" * 70)
    assert evaluate_condition('name == "Ana"', {"name": "Manuel"}) is False
    print("✅ False")


def test_string_not_equal():
    print("\n" + "=" * 70)
    print("TEST 8: name != \"Ana\" con name=Manuel → True")
    print("=" * 70)
    assert evaluate_condition('name != "Ana"', {"name": "Manuel"}) is True
    print("✅ True")


def test_string_single_quotes():
    print("\n" + "=" * 70)
    print("TEST 9: status == 'active' (comillas simples)")
    print("=" * 70)
    assert evaluate_condition("status == 'active'", {"status": "active"}) is True
    print("✅ True")


def test_boolean_literal():
    print("\n" + "=" * 70)
    print("TEST 10: active == true")
    print("=" * 70)
    assert evaluate_condition("active == true", {"active": True}) is True
    assert evaluate_condition("active == false", {"active": False}) is True
    print("✅ True")


def test_none_literal():
    print("\n" + "=" * 70)
    print("TEST 11: x == null")
    print("=" * 70)
    assert evaluate_condition("x == null", {"x": None}) is True
    assert evaluate_condition("x != null", {"x": "algo"}) is True
    print("✅ True")


def test_float_comparison():
    print("\n" + "=" * 70)
    print("TEST 12: price > 9.5")
    print("=" * 70)
    assert evaluate_condition("price > 9.5", {"price": 10.0}) is True
    assert evaluate_condition("price > 9.5", {"price": 9.4}) is False
    print("✅ True / False")


def test_variable_not_defined():
    print("\n" + "=" * 70)
    print("TEST 13: Variable inexistente → ConditionError")
    print("=" * 70)
    try:
        evaluate_condition("no_existe > 18", {"age": 21})
        assert False, "Debería haber lanzado ConditionError"
    except ConditionError as e:
        assert "no_existe" in str(e)
        print(f"✅ ConditionError detectado: {e}")


def test_unsupported_operator():
    print("\n" + "=" * 70)
    print("TEST 14: Operador no soportado → ConditionError")
    print("=" * 70)
    try:
        evaluate_condition("age && 18", {})
        assert False, "Debería haber lanzado ConditionError"
    except ConditionError as e:
        print(f"✅ ConditionError detectado: {e}")


def test_empty_expression():
    print("\n" + "=" * 70)
    print("TEST 15: Expresión vacía → ConditionError")
    print("=" * 70)
    try:
        evaluate_condition("", {})
        assert False, "Debería haber lanzado ConditionError"
    except ConditionError as e:
        print(f"✅ ConditionError detectado: {e}")


def test_malformed_expression():
    print("\n" + "=" * 70)
    print("TEST 16: Expresión mal formada → ConditionError")
    print("=" * 70)
    try:
        evaluate_condition("age 18", {})
        assert False, "Debería haber lanzado ConditionError"
    except ConditionError as e:
        print(f"✅ ConditionError detectado: {e}")


def test_type_mismatch():
    print("\n" + "=" * 70)
    print("TEST 17: Tipos incompatibles → ConditionError")
    print("=" * 70)
    try:
        evaluate_condition('age > "hola"', {"age": 21})
        assert False, "Debería haber lanzado ConditionError"
    except ConditionError as e:
        assert "no comparables" in str(e).lower() or "tipos" in str(e).lower()
        print(f"✅ ConditionError detectado: {e}")


def test_validate_expression_ok():
    print("\n" + "=" * 70)
    print("TEST 18: validate_condition_expression OK")
    print("=" * 70)
    validate_condition_expression("age > 18")
    validate_condition_expression('name == "Manuel"')
    validate_condition_expression("x != null")
    validate_condition_expression("active == true")
    print("✅ Todas las expresiones válidas")


def test_validate_expression_ko():
    print("\n" + "=" * 70)
    print("TEST 19: validate_condition_expression KO")
    print("=" * 70)
    invalids = ["", "   ", "age 18", "no op", "== 18"]
    for expr in invalids:
        try:
            validate_condition_expression(expr)
            assert False, f"Debería haber fallado: {expr!r}"
        except ConditionError:
            pass
    print(f"✅ {len(invalids)} expresiones inválidas detectadas")


def test_no_eval_in_source():
    """
    Verifica que el módulo conditions.py NO usa eval()/exec()/compile().

    Ignora:
        - Comentarios (líneas que empiezan por #)
        - Docstrings (líneas dentro de \"\"\" ... \"\"\")
        - re.compile() (compilación de regex, segura)
    """
    print("\n" + "=" * 70)
    print("TEST 20: Sin eval() / exec() / compile() en conditions.py")
    print("=" * 70)

    import app.core.workflows.conditions as cond_module
    source = inspect.getsource(cond_module)
    lines = source.split("\n")

    suspicious = []
    in_docstring = False
    docstring_delim = None

    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Detectar entrada/salida de docstring triple
        triple_dq = stripped.count('"""')
        triple_sq = stripped.count("'''")
        if triple_dq == 1:
            if in_docstring and docstring_delim == '"""':
                in_docstring = False
                docstring_delim = None
                continue
            elif not in_docstring:
                in_docstring = True
                docstring_delim = '"""'
                continue
        if triple_sq == 1:
            if in_docstring and docstring_delim == "'''":
                in_docstring = False
                docstring_delim = None
                continue
            elif not in_docstring:
                in_docstring = True
                docstring_delim = "'''"
                continue

        # Ignorar si estamos dentro de docstring
        if in_docstring:
            continue

        # Ignorar comentarios
        if stripped.startswith("#"):
            continue

        # Ignorar 're.compile' (compilación de regex, no de código)
        line_clean = re_module.sub(r"\bre\.compile\s*\(", "", stripped)

        # Buscar eval/exec/compile como llamadas
        if re_module.search(r"\beval\s*\(", line_clean):
            suspicious.append((line_no, "eval", stripped))
        if re_module.search(r"\bexec\s*\(", line_clean):
            suspicious.append((line_no, "exec", stripped))
        if re_module.search(r"\bcompile\s*\(", line_clean):
            suspicious.append((line_no, "compile", stripped))

    assert not suspicious, f"❌ Encontrado código peligroso: {suspicious}"
    print("✅ No hay eval(), exec() ni compile() en el código (ignorando docstrings y re.compile)")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.5.6 (Conditions)")
    print("=" * 70)

    tests = [
        test_int_greater_true,
        test_int_greater_false,
        test_int_greater_equal_border,
        test_int_less_false,
        test_int_less_equal_border,
        test_string_equal_true,
        test_string_equal_false,
        test_string_not_equal,
        test_string_single_quotes,
        test_boolean_literal,
        test_none_literal,
        test_float_comparison,
        test_variable_not_defined,
        test_unsupported_operator,
        test_empty_expression,
        test_malformed_expression,
        test_type_mismatch,
        test_validate_expression_ok,
        test_validate_expression_ko,
        test_no_eval_in_source,
    ]

    try:
        for t in tests:
            t()
        print("\n" + "=" * 70)
        print("🎉 TODOS LOS TESTS PASARON")
        print("=" * 70)
    except AssertionError as e:
        print(f"\n🛑 TEST FALLIDO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n🛑 ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
