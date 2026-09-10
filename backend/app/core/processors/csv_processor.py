"""
Nuvora Core — CSV Processor
==============================
Convierte un CSV en texto indexable.
Cada fila se convierte en un bloque tipo "col: val | col: val".
"""

import csv
import io

from app.core.processors.base import BaseProcessor, ProcessorResult, ProcessorError


# ============================================================
# LÍMITES
# ============================================================

MAX_CSV_SIZE = 2 * 1024 * 1024  # 2 MB
MAX_CSV_ROWS = 5000
MAX_CSV_COLS = 30


class CSVProcessor(BaseProcessor):

    def process(self, content: str | bytes, **kwargs) -> ProcessorResult:
        # 1. Decodificar si es bytes
        if isinstance(content, bytes):
            raw_size = len(content)
            try:
                content = content.decode("utf-8-sig")  # utf-8-sig elimina BOM
            except UnicodeDecodeError:
                try:
                    content = content.decode("latin-1")
                except Exception as e:
                    raise ProcessorError(f"No se pudo decodificar el CSV: {e}")
        else:
            raw_size = len(content.encode("utf-8"))

        if not content.strip():
            raise ProcessorError("El CSV está vacío")

        # 2. Validar tamaño
        if raw_size > MAX_CSV_SIZE:
            raise ProcessorError(
                f"El CSV supera el límite de {MAX_CSV_SIZE // (1024*1024)} MB"
            )

        # 3. Detectar delimitador
        delimiter = self._detect_delimiter(content)

        # 4. Parsear
        try:
            reader = csv.reader(io.StringIO(content), delimiter=delimiter)
            rows = list(reader)
        except csv.Error as e:
            raise ProcessorError(f"Error parseando CSV: {e}")

        if not rows:
            raise ProcessorError("El CSV no contiene filas")

        # 5. Validar número de filas
        if len(rows) > MAX_CSV_ROWS:
            raise ProcessorError(
                f"El CSV tiene {len(rows)} filas (máx {MAX_CSV_ROWS})"
            )

        # 6. Detectar cabecera
        first_row = rows[0]
        has_header = self._looks_like_header(first_row, rows[1] if len(rows) > 1 else None)

        # 7. Validar número de columnas
        if len(first_row) > MAX_CSV_COLS:
            raise ProcessorError(
                f"El CSV tiene {len(first_row)} columnas (máx {MAX_CSV_COLS})"
            )

        # 8. Convertir filas a texto
        lines = []

        if has_header:
            header = [h.strip() for h in first_row]
            data_rows = rows[1:]
        else:
            header = [f"col_{i+1}" for i in range(len(first_row))]
            data_rows = rows

        for row in data_rows:
            if not row or all(not cell.strip() for cell in row):
                continue  # saltar filas vacías

            parts = []
            for i, cell in enumerate(row):
                cell = cell.strip()
                if not cell:
                    continue
                col_name = header[i] if i < len(header) else f"col_{i+1}"
                parts.append(f"{col_name}: {cell}")

            if parts:
                lines.append(" | ".join(parts))

        if not lines:
            raise ProcessorError("El CSV no contiene datos")

        text = "\n\n".join(lines)

        # 9. Metadatos
        meta = {
            "rows": len(data_rows),
            "columns": len(header),
            "delimiter": delimiter,
            "has_header": has_header,
            "source_type": "csv",
        }

        return ProcessorResult(text=text, meta=meta, size_bytes=raw_size)

    def _detect_delimiter(self, content: str) -> str:
        """Detecta el delimitador del CSV."""
        # Probar con csv.Sniffer
        try:
            sample = content[:4096]
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            return dialect.delimiter
        except csv.Error:
            # Fallback: contar ocurrencias
            first_line = content.split("\n", 1)[0]
            counts = {
                ",": first_line.count(","),
                ";": first_line.count(";"),
                "\t": first_line.count("\t"),
                "|": first_line.count("|"),
            }
            # Devolver el más frecuente (o coma por defecto)
            best = max(counts, key=counts.get)
            return best if counts[best] > 0 else ","

    def _looks_like_header(self, first_row: list, second_row: list | None) -> bool:
        """
        Heurística: ¿la primera fila es cabecera?
        - Si la primera fila no tiene números pero la segunda sí → probablemente cabecera
        - Si todas las celdas de la primera fila son texto sin números → probable cabecera
        """
        if not first_row:
            return False

        first_has_numbers = any(self._has_number(cell) for cell in first_row)
        if second_row:
            second_has_numbers = any(self._has_number(cell) for cell in second_row)
            if not first_has_numbers and second_has_numbers:
                return True

        # Si todas las celdas son no-vacías y sin números → probable cabecera
        non_empty = [c.strip() for c in first_row if c.strip()]
        if non_empty and all(not self._has_number(c) for c in non_empty):
            return True

        return False

    def _has_number(self, text: str) -> bool:
        """Comprueba si un texto contiene algún dígito."""
        return any(ch.isdigit() for ch in text)
