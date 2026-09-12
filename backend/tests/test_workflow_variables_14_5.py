"""
Tests — Subfase 14.5.6
Verifica el interpolador SEGURO de variables.

Casos cubiertos:
    1.  {{name}} simple
    2.  Sin variables → texto intacto
    3.  Variable inexistente → placeholder intacto
    4.  Múltiples variables
    5.  Variable numérica → se convierte a str
    6.  Variable None → "None"
    7.  Espacios internos {{ name }}
    8.  Texto con muchas ocurrencias
    9.  extract_variable_names
    10. Sin eval()/exec()/compile() en el código
"""

import sys
import os
import inspect
import re as re_module

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.workflows.variables import interpolate, extract_variable_names


def test_simple_interpolation():
    print("\n" + "=" * 70)
    print("TEST 1: {{name}} simple")
    print("=" * 70)
    result = interpolate("Hola {{name}}", {"name": "Manuel"})
    assert result == "Hola Manuel"
    print(f"✅ '{result}'")


def test_no_variables():
    print("\n" + "=" * 70)
    print("TEST 2: Sin variables → texto intacto")
    print("=" * 70)
    result = interpolate("Texto plano sin placeholders", {"x": 1})
    assert result == "Texto plano sin placeholders"
    print(f"✅ '{result}'")


def test_missing_variable():
    print("\n" + "=" * 70)
    print("TEST 3: Variable inexistente → placeholder intacto")
    print("=" * 70)
    result = interpolate("Hola {{name}}", {})
    assert result == "Hola {{name}}"
    print(f"✅ '{result}'")


def test_multiple_variables():
    print("\n" + "=" * 70)
    print("TEST 4: Múltiples variables")
    print("=" * 70)
    result = interpolate(
        "{{a}} y {{b}}",
        {"a": "uno", "b": "dos"}
    )
    assert result == "uno y dos"
    print(f"✅ '{result}'")


def test_numeric_variable():
    print("\n" + "=" * 70)
    print("TEST 5: Variable numérica → str")
    print("=" * 70)
    result = interpolate("Tienes {{age}} años", {"age": 21})
    assert result == "Tienes 21 años"
    print(f"✅ '{result}'")


def test_none_variable():
    print("\n" + "=" * 70)
    print("TEST 6: Variable None → 'None'")
    print("=" * 70)
    result = interpolate("Valor: {{x}}", {"x": None})
    assert result == "Valor: None"
    print(f"✅ '{result}'")


def test_spaces_inside():
    print("\n" + "=" * 70)
    print("TEST 7: Espacios internos {{ name }}")
    print("=" * 70)
    result = interpolate("Hola {{ name }}", {"name": "Manuel"})
    assert result == "Hola Manuel"
    print(f"✅ '{result}'")


def test_repeated_occurrences():
    print("\n" + "=" * 70)
    print("TEST 8: Variable repetida")
    print("=" * 70)
    result = interpolate("{{x}} + {{x}} = 2{{x}}", {"x": "1"})
    assert result == "1 + 1 = 21"
    print(f"✅ '{result}'")


def test_extract_names():
    print("\n" + "=" * 70)
    print("TEST 9: extract_variable_names")
    print("=" * 70)
    names = extract_variable_names("Hola {{name}}, edad {{age}} y {{city}}")
    assert names == ["name", "age", "city"], f"names={names}"
    print(f"✅ {names}")

    names_empty = extract_variable_names("Sin variables")
    assert names_empty == []
    print(f"✅ Sin variables → []")


def test_no_eval_in_source():
    print("\n" + "=" * 70)
    print("TEST 10: Sin eval()/exec()/compile() en variables.py")
    print("=" * 70)

    import app.core.workflows.variables as var_module
    source = inspect.getsource(var_module)
    lines = source.split("\n")

    suspicious = []
    in_docstring = False
    docstring_delim = None

    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()

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

        if in_docstring:
            continue
        if stripped.startswith("#"):
            continue

        line_clean = re_module.sub(r"\bre\.compile\s*\(", "", stripped)

        if re_module.search(r"\beval\s*\(", line_clean):
            suspicious.append((line_no, "eval", stripped))
        if re_module.search(r"\bexec\s*\(", line_clean):
            suspicious.append((line_no, "exec", stripped))
        if re_module.search(r"\bcompile\s*\(", line_clean):
            suspicious.append((line_no, "compile", stripped))

    assert not suspicious, f"❌ Encontrado código peligroso: {suspicious}"
    print("✅ No hay eval(), exec() ni compile()")


def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.5.6 (Variables interpolation)")
    print("=" * 70)

    tests = [
        test_simple_interpolation,
        test_no_variables,
        test_missing_variable,
        test_multiple_variables,
        test_numeric_variable,
        test_none_variable,
        test_spaces_inside,
        test_repeated_occurrences,
        test_extract_names,
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
