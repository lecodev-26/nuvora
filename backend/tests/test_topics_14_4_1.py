"""
Tests — Subfase 14.4.1
Verifica el Topic Catalog (training/topics.py).
"""

import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.training import (
    Topic,
    NichoCatalog,
    get_nicho_catalog,
    get_topics_for_nicho,
    get_topic_by_id,
    list_nichos,
)


# ============================================================
# TESTS
# ============================================================

def test_list_nichos_includes_all():
    print("\n" + "=" * 70)
    print("TEST 1: list_nichos() incluye todos los nichos esperados")
    print("=" * 70)
    nichos = list_nichos()
    expected = ["restaurantes", "peluquerias", "hoteles",
                "gimnasios", "clinicas", "tiendas", "otro"]
    for n in expected:
        assert n in nichos, f"Falta nicho: {n}"
    print(f"✅ Nichos: {nichos}")


def test_get_catalog_returns_nicho_catalog():
    print("\n" + "=" * 70)
    print("TEST 2: get_nicho_catalog() devuelve NichoCatalog")
    print("=" * 70)
    cat = get_nicho_catalog("restaurantes")
    assert isinstance(cat, NichoCatalog)
    assert cat.nicho_id == "restaurantes"
    assert cat.display_name == "Restaurantes"
    assert len(cat.topics) > 0
    print(f"✅ Catálogo: {cat.display_name} ({len(cat.topics)} temas)")


def test_get_catalog_fallback_unknown():
    print("\n" + "=" * 70)
    print("TEST 3: get_nicho_catalog() fallback a 'otro'")
    print("=" * 70)
    cat = get_nicho_catalog("inexistente")
    assert cat.nicho_id == "otro"
    print(f"✅ Fallback correcto: {cat.nicho_id}")


def test_get_catalog_fallback_none():
    print("\n" + "=" * 70)
    print("TEST 4: get_nicho_catalog() fallback con None")
    print("=" * 70)
    cat = get_nicho_catalog(None)
    assert cat.nicho_id == "otro"
    print(f"✅ Fallback con None: {cat.nicho_id}")


def test_topics_have_required_fields():
    print("\n" + "=" * 70)
    print("TEST 5: Todos los temas tienen campos obligatorios")
    print("=" * 70)
    for nicho_id in list_nichos():
        cat = get_nicho_catalog(nicho_id)
        for t in cat.topics:
            assert isinstance(t, Topic)
            assert t.id, f"Topic sin id en {nicho_id}"
            assert t.label, f"Topic {t.id} sin label en {nicho_id}"
            assert t.description, f"Topic {t.id} sin description en {nicho_id}"
            assert isinstance(t.keywords, tuple), f"Topic {t.id} keywords no es tuple"
            assert len(t.keywords) > 0, f"Topic {t.id} sin keywords en {nicho_id}"
    print(f"✅ Todos los temas tienen id, label, description y keywords")


def test_topics_ids_unique_per_nicho():
    print("\n" + "=" * 70)
    print("TEST 6: IDs de temas únicos por nicho")
    print("=" * 70)
    for nicho_id in list_nichos():
        cat = get_nicho_catalog(nicho_id)
        ids = [t.id for t in cat.topics]
        assert len(ids) == len(set(ids)), f"IDs duplicados en {nicho_id}: {ids}"
    print(f"✅ IDs únicos en todos los nichos")


def test_generic_topics_present_in_all_nichos():
    print("\n" + "=" * 70)
    print("TEST 7: Temas genéricos presentes en todos los nichos")
    print("=" * 70)
    mandatory = ["descripcion", "horarios", "contacto", "ubicacion", "precios"]
    for nicho_id in list_nichos():
        cat = get_nicho_catalog(nicho_id)
        topic_ids = {t.id for t in cat.topics}
        for m in mandatory:
            assert m in topic_ids, f"Falta {m} en {nicho_id}"
    print(f"✅ Temas obligatorios presentes en todos los nichos")


def test_get_topics_for_nicho():
    print("\n" + "=" * 70)
    print("TEST 8: get_topics_for_nicho()")
    print("=" * 70)
    topics = get_topics_for_nicho("restaurantes")
    assert isinstance(topics, list)
    assert len(topics) > 0
    assert all(isinstance(t, Topic) for t in topics)
    print(f"✅ {len(topics)} temas para restaurantes")


def test_get_topic_by_id():
    print("\n" + "=" * 70)
    print("TEST 9: get_topic_by_id()")
    print("=" * 70)
    topic = get_topic_by_id("restaurantes", "menu")
    assert topic is not None
    assert topic.id == "menu"
    assert topic.label == "Menú"

    topic_unknown = get_topic_by_id("xyz", "menu")
    assert topic_unknown is None

    none_topic = get_topic_by_id("restaurantes", "no_existe")
    assert none_topic is None
    print(f"✅ Búsquedas correctas")


def test_topics_immutability():
    print("\n" + "=" * 70)
    print("TEST 10: Topics son inmutables (frozen)")
    print("=" * 70)
    topic = get_topic_by_id("restaurantes", "horarios")
    try:
        topic.label = "Otro"  # type: ignore
        assert False, "Debería haber lanzado FrozenInstanceError"
    except Exception as e:
        assert "frozen" in str(e).lower() or "cannot assign" in str(e).lower()
    print(f"✅ Topic es inmutable")


def _strip_docstrings_and_comments(source: str) -> str:
    """
    Limpia el código fuente para el test de arquitectura:
    - Elimina contenido entre backticks (`...`)
    - Elimina comentarios (# ...)
    - Elimina triple-quoted strings (docstrings)
    """
    # 1. Eliminar backticks
    source = re.sub(r"`[^`]*`", "", source)

    # 2. Eliminar comentarios de línea
    source = re.sub(r"#[^\n]*", "", source)

    # 3. Eliminar triple-quoted strings (docstrings y strings multilínea)
    # """...""" y '''...'''
    source = re.sub(r'""".*?"""', "", source, flags=re.DOTALL)
    source = re.sub(r"'''.*?'''", "", source, flags=re.DOTALL)

    # 4. Eliminar strings de una línea (comillas simples y dobles)
    # Nota: hacemos esto DESPUÉS de eliminar comentarios para no romper URLs
    source = re.sub(r'"[^"\n]*"', '""', source)
    source = re.sub(r"'[^'\n]*'", "''", source)

    return source


def test_no_nicho_logic_in_module():
    """
    Regla arquitectónica: topics.py debe ser datos, no lógica.

    Verifica que no existe código real del tipo:
        if nicho_id == "restaurantes":
        if nicho == "peluquerias":
    """

    print("\n" + "=" * 70)
    print("TEST 11: Sin lógica de nichos en el módulo")
    print("=" * 70)

    import inspect
    from app.core.training import topics as topics_module

    raw_source = inspect.getsource(topics_module)
    clean_source = _strip_docstrings_and_comments(raw_source)

    # Patrones prohibidos en código real (ya sin docstrings/comentarios)
    forbidden_patterns = [
        r'if\s+nicho_id\s*==\s*["\']',
        r'if\s+nicho\s*==\s*["\']',
        r'elif\s+nicho_id\s*==\s*["\']',
        r'elif\s+nicho\s*==\s*["\']',
    ]

    for pattern in forbidden_patterns:
        matches = re.findall(pattern, clean_source)
        assert not matches, (
            f"Encontrada lógica de nicho en código real: {pattern}. "
            f"Coincidencias: {matches}"
        )

    print(f"✅ Sin lógica de nichos en el Core (regla arquitectónica cumplida)")


def test_catalog_count():
    print("\n" + "=" * 70)
    print("TEST 12: Número de temas por nicho")
    print("=" * 70)
    for nicho_id in list_nichos():
        cat = get_nicho_catalog(nicho_id)
        print(f"   {nicho_id}: {len(cat.topics)} temas")
    otro = get_nicho_catalog("otro")
    assert len(otro.topics) >= 8
    print(f"✅ 'otro' tiene {len(otro.topics)} temas (>= 8)")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.4.1 (Topic Catalog)")
    print("=" * 70)

    tests = [
        test_list_nichos_includes_all,
        test_get_catalog_returns_nicho_catalog,
        test_get_catalog_fallback_unknown,
        test_get_catalog_fallback_none,
        test_topics_have_required_fields,
        test_topics_ids_unique_per_nicho,
        test_generic_topics_present_in_all_nichos,
        test_get_topics_for_nicho,
        test_get_topic_by_id,
        test_topics_immutability,
        test_no_nicho_logic_in_module,
        test_catalog_count,
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
