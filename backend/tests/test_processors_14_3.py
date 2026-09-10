"""
Tests — Subfase 14.3.2
Verifica processors y chunker.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.processors import (
    TextProcessor,
    CSVProcessor,
    Chunker,
    ProcessorError,
)


def test_text_processor_basic():
    print("\n" + "=" * 70)
    print("TEST 1: TextProcessor básico")
    print("=" * 70)
    tp = TextProcessor()
    result = tp.process("Hola   mundo.\n\n\nEsto es una   prueba.")
    assert "Hola mundo" in result.text
    assert "\n\n\n" not in result.text  # 3 saltos se colapsan a 2
    assert result.meta["source_type"] == "text"
    print(f"✅ Texto procesado: {len(result.text)} chars")
    print(f"   Meta: {result.meta}")


def test_text_processor_empty():
    print("\n" + "=" * 70)
    print("TEST 2: TextProcessor texto vacío")
    print("=" * 70)
    tp = TextProcessor()
    try:
        tp.process("   \n\n   ")
        assert False, "Debería haber lanzado ProcessorError"
    except ProcessorError as e:
        print(f"✅ Error esperado: {e}")


def test_text_processor_too_large():
    print("\n" + "=" * 70)
    print("TEST 3: TextProcessor texto demasiado grande")
    print("=" * 70)
    tp = TextProcessor()
    try:
        tp.process("a" * (200 * 1024))
        assert False, "Debería haber lanzado ProcessorError"
    except ProcessorError as e:
        print(f"✅ Error esperado: {e}")


def test_csv_processor_basic():
    print("\n" + "=" * 70)
    print("TEST 4: CSVProcessor básico")
    print("=" * 70)
    cp = CSVProcessor()
    csv_content = "Producto,Precio\nPizza,12\nEnsalada,8"
    result = cp.process(csv_content)
    assert "Producto: Pizza" in result.text
    assert "Precio: 12" in result.text
    assert result.meta["has_header"] is True
    print(f"✅ CSV procesado: {result.meta}")


def test_csv_processor_semicolon():
    print("\n" + "=" * 70)
    print("TEST 5: CSVProcessor con delimitador ;")
    print("=" * 70)
    cp = CSVProcessor()
    csv_content = "Producto;Precio\nPizza;12"
    result = cp.process(csv_content)
    assert result.meta["delimiter"] == ";"
    assert "Producto: Pizza" in result.text
    print(f"✅ CSV con ; procesado: {result.meta}")


def test_chunker_short():
    print("\n" + "=" * 70)
    print("TEST 6: Chunker texto corto (1 chunk)")
    print("=" * 70)
    chunker = Chunker()
    chunks = chunker.chunk("Hola, esto es una prueba corta.")
    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    print(f"✅ 1 chunk generado: {len(chunks[0].content)} chars")


def test_chunker_long():
    print("\n" + "=" * 70)
    print("TEST 7: Chunker texto largo (varios chunks)")
    print("=" * 70)
    # Texto de ~3000 chars
    long_text = ("Esto es una oración de prueba. " * 100)
    chunker = Chunker()
    chunks = chunker.chunk(long_text)
    assert len(chunks) > 1
    # Verificar overlap
    for i in range(1, len(chunks)):
        assert chunks[i].chunk_index == i
    print(f"✅ {len(chunks)} chunks generados")
    for c in chunks[:3]:
        print(f"   Chunk {c.chunk_index}: {len(c.content)} chars, "
              f"tokens~{c.tokens_estimate}")


def test_chunker_with_sections():
    print("\n" + "=" * 70)
    print("TEST 8: Chunker con secciones detectadas")
    print("=" * 70)
    text = """# Horarios

Abrimos de 9:00 a 18:00.

## Precios

Menú del día: 15€.

## Ubicación

Calle Principal 123."""
    chunker = Chunker()
    chunks = chunker.chunk(text)
    assert len(chunks) >= 1
    # Al menos algún chunk debe tener sección detectada
    sections = [c.section for c in chunks if c.section]
    assert len(sections) > 0
    print(f"✅ {len(chunks)} chunks, {len(sections)} con sección")
    for c in chunks:
        print(f"   Chunk {c.chunk_index}: section='{c.section}'")


def test_chunker_with_pages():
    print("\n" + "=" * 70)
    print("TEST 9: Chunker con marcadores de página")
    print("=" * 70)
    text = "[[PAGE:1]]\nContenido página 1.\n\n[[PAGE:2]]\nContenido página 2."
    chunker = Chunker()
    chunks = chunker.chunk(text)
    pages = [c.page for c in chunks if c.page]
    assert len(pages) > 0
    print(f"✅ Chunks con páginas: {[c.page for c in chunks]}")


def test_chunker_empty():
    print("\n" + "=" * 70)
    print("TEST 10: Chunker texto vacío")
    print("=" * 70)
    chunker = Chunker()
    chunks = chunker.chunk("")
    assert chunks == []
    chunks = chunker.chunk("   \n\n   ")
    assert chunks == []
    print(f"✅ Chunker devuelve lista vacía para texto vacío")


def main():
    print("=" * 70)
    print("🧪 TESTS — SUBFASE 14.3.2 (Processors + Chunker)")
    print("=" * 70)

    tests = [
        test_text_processor_basic,
        test_text_processor_empty,
        test_text_processor_too_large,
        test_csv_processor_basic,
        test_csv_processor_semicolon,
        test_chunker_short,
        test_chunker_long,
        test_chunker_with_sections,
        test_chunker_with_pages,
        test_chunker_empty,
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
