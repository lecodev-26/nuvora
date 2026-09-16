"""
Nuvora Core — Testing: Basic Test Generator (Fase 14.8.13)
==============================================================
Genera DEFINICIONES de tests básicos SIN IA.

FILOSOFÍA:
    - 100% determinista. Sin IA. Sin coste. Sin tokens.
    - Basado en la estructura del workflow.
    - NO ejecuta workflows.
    - NO guarda en BD.
    - El usuario decide si guardar.

QUÉ GENERA:
    1. Test "happy path": llega a END (reaches_end)
    2. Test por nodo (hasta 5): verifica node_visited
    3. Test "no excede MAX_STEPS" (max_steps=50)
    4. Test "sin error en output" (response_not_contains="error")
"""

from app.models.test import (
    TestCaseCreate,
    GenerateBasicTestsResponse,
)
from app.core.testing.analyzer import WorkflowAnalyzer


MAX_NODE_TESTS = 5


class BasicTestGenerator:
    """
    Genera tests básicos automáticamente (deterministas, sin IA).

    Uso:
        gen = BasicTestGenerator()
        result = gen.generate(workflow_data=wf_dict)
    """

    def generate(self, workflow_data: dict) -> GenerateBasicTestsResponse:
        """Genera tests básicos para el workflow."""
        nodes = workflow_data.get("nodes") or []
        transitions = workflow_data.get("transitions") or []

        if not nodes:
            return GenerateBasicTestsResponse(
                generated=[],
                count=0,
                notes=["El workflow está vacío. No se pueden generar tests."],
            )

        notes: list[str] = []
        generated: list[TestCaseCreate] = []

        # 1. Test happy path (START → END)
        happy = self._build_happy_path_test(nodes, transitions)
        if happy:
            generated.append(happy)

        # 2. Test por nodo (hasta MAX_NODE_TESTS)
        node_tests = self._build_node_tests(nodes)
        generated.extend(node_tests[:MAX_NODE_TESTS])

        # 3. Test no excede MAX_STEPS
        max_steps_test = self._build_max_steps_test()
        generated.append(max_steps_test)

        # 4. Test sin error en output (solo si hay MESSAGE/RESPONSE)
        has_message = any(n.get("type") in ("message", "response") for n in nodes)
        if has_message:
            no_error_test = self._build_no_error_test()
            generated.append(no_error_test)

        # Notas
        node_count = len(nodes)
        if node_count > MAX_NODE_TESTS:
            notes.append(
                f"Se generaron solo {MAX_NODE_TESTS} tests por nodo "
                f"(el workflow tiene {node_count} nodos)."
            )

        # Analizar workflow para detectar problemas
        try:
            analysis = WorkflowAnalyzer(workflow_data).analyze()
            if analysis.summary.get("error", 0) > 0:
                notes.append(
                    f"⚠️ El workflow tiene {analysis.summary['error']} errores "
                    f"estructurales. Los tests podrían fallar."
                )
            if analysis.summary.get("warning", 0) > 0:
                notes.append(
                    f"El workflow tiene {analysis.summary['warning']} warnings."
                )
        except Exception:
            pass  # el análisis es best-effort

        return GenerateBasicTestsResponse(
            generated=generated,
            count=len(generated),
            notes=notes,
        )

    # ============================================================
    # BUILDERS
    # ============================================================

    def _build_happy_path_test(
        self,
        nodes: list[dict],
        transitions: list[dict],
    ) -> TestCaseCreate | None:
        """
        Genera un test que verifica que el workflow llega a END.

        Incluye variables iniciales inferidas:
        - Si hay nodos QUESTION, se inventan respuestas genéricas.
        - Si hay nodos CONDITION, se intenta cubrir la rama "true".
        """
        ends = [n for n in nodes if n.get("type") == "end"]
        if not ends:
            return None  # sin END, no hay happy path

        # Inferir variables iniciales a partir de los nodos
        initial_vars = self._infer_initial_variables(nodes)

        assertions = [
            {"type": "reaches_end"},
            {"type": "max_steps", "max_steps": 50},
        ]

        return TestCaseCreate(
            name="Happy path (llega a END)",
            description="Verifica que el workflow puede completarse correctamente.",
            input_messages=["Hola"],
            initial_variables=initial_vars,
            assertions=assertions,
            enabled=True,
        )

    def _build_node_tests(self, nodes: list[dict]) -> list[TestCaseCreate]:
        """Genera un test por nodo: verifica que el nodo se visita."""
        tests: list[TestCaseCreate] = []
        initial_vars = self._infer_initial_variables(nodes)

        for n in nodes:
            node_id = n.get("node_id")
            node_type = n.get("type")
            if not node_id:
                continue

            tests.append(TestCaseCreate(
                name=f"Visita nodo: {node_id}",
                description=f"Verifica que el nodo '{node_id}' ({node_type}) es visitado.",
                input_messages=["Hola"],
                initial_variables=initial_vars,
                assertions=[
                    {"type": "node_visited", "node_id": node_id},
                ],
                enabled=True,
            ))

        return tests

    def _build_max_steps_test(self) -> TestCaseCreate:
        """Genera un test que verifica que no se excede MAX_STEPS."""
        return TestCaseCreate(
            name="No excede MAX_STEPS",
            description="Verifica que el workflow termina en menos de 50 pasos.",
            input_messages=["Hola"],
            initial_variables={},
            assertions=[
                {"type": "max_steps", "max_steps": 50},
            ],
            enabled=True,
        )

    def _build_no_error_test(self) -> TestCaseCreate:
        """Genera un test que verifica que no aparece 'error' en los outputs."""
        return TestCaseCreate(
            name="Sin 'error' en output",
            description="Verifica que ningún mensaje contiene la palabra 'error'.",
            input_messages=["Hola"],
            initial_variables={},
            assertions=[
                {"type": "response_not_contains", "value": "error"},
            ],
            enabled=True,
        )

    # ============================================================
    # INFERENCIA
    # ============================================================

    def _infer_initial_variables(self, nodes: list[dict]) -> dict:
        """
        Infiere variables iniciales a partir de los nodos:
        - Por cada QUESTION, propone un valor genérico para su `variable`.
        - Por cada CONDITION, propone variables que probablemente satisfagan
          la condición más simple (ej: age=25 si es "age > 18").
        """
        variables: dict = {}

        for n in nodes:
            ntype = n.get("type")
            config = n.get("config") or {}

            if ntype == "question":
                var = config.get("variable")
                if var and var not in variables:
                    variables[var] = self._default_value_for_var(var)

            elif ntype == "condition":
                cond = config.get("condition") or ""
                inferred = self._infer_condition_vars(cond)
                for k, v in inferred.items():
                    if k not in variables:
                        variables[k] = v

        return variables

    def _default_value_for_var(self, var: str) -> str:
        """Devuelve un valor genérico para una variable."""
        name = var.lower()
        if "email" in name or "correo" in name:
            return "test@example.com"
        if "phone" in name or "tel" in name or "movil" in name:
            return "600123456"
        if "name" in name or "nombre" in name:
            return "Manuel"
        if "day" in name or "dia" in name:
            return "mañana"
        if "hora" in name or "time" in name:
            return "10:00"
        if "city" in name or "ciudad" in name:
            return "Madrid"
        if "date" in name or "fecha" in name:
            return "2026-01-15"
        return "test"

    def _infer_condition_vars(self, condition: str) -> dict:
        """
        Intenta inferir valores para variables de una condición simple.
        Heurística:
            - "x > 18" o "x >= 18" → x = 25
            - "x < 18" o "x <= 18" → x = 5
            - "x == 'valor'" → x = 'valor'
            - "x != 'valor'" → x = 'otro'
        """
        result: dict = {}
        import re

        # Regex simple: var op value
        m = re.match(
            r"\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*(==|!=|>=|<=|>|<)\s*(.+)\s*$",
            condition.strip(),
        )
        if not m:
            return result

        var = m.group(1)
        op = m.group(2)
        raw_val = m.group(3).strip()

        # Quitar comillas si es string
        if raw_val.startswith(('"', "'")) and raw_val.endswith(('"', "'")):
            raw_val = raw_val[1:-1]

        # Parsear número si aplica
        try:
            num = float(raw_val) if "." in raw_val else int(raw_val)
        except (ValueError, TypeError):
            num = None

        if op in (">", ">="):
            result[var] = (num + 10) if num is not None else "test"
        elif op in ("<", "<="):
            result[var] = (num - 10) if num is not None else "test"
        elif op == "==":
            result[var] = num if num is not None else raw_val
        elif op == "!=":
            result[var] = (num + 1) if num is not None else "__otro__"

        return result


__all__ = ["BasicTestGenerator"]
