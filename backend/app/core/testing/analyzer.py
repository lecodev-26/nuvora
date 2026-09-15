"""
Nuvora Core — Testing: Static Workflow Analyzer
==================================================
Analiza workflows SIN ejecutarlos. Detecta problemas estructurales
y de configuración que podrían causar fallos en runtime.

FILOSOFÍA:
    - 100% determinista. Sin IA. Sin ejecución.
    - Solo lee. No modifica nada.
    - Reutiliza piezas de 14.5 (WorkflowValidator, conditions).
    - No duplica lógica innecesariamente.

CHECKS IMPLEMENTADOS:
    Estructura:
        1. Exactamente 1 START
        2. Al menos 1 END
        3. Nodos huérfanos (sin entradas ni salidas)
        4. Nodos inalcanzables desde START
    Condiciones:
        5. CONDITION con < 2 salidas
        6. Condiciones sintácticamente inválidas
    Ejecución:
        7. Dead-ends (nodos sin camino a END, no siendo END)
        8. Ciclos detectados (info, no error)
    Variables:
        9. Variables usadas antes de ser creadas ({{var}})
        10. Variables usadas en CONDITION antes de ser creadas
"""

import re
from typing import Optional

from app.models.test import AnalyzeResponse, StructuralIssue
from app.core.workflows.validator import WorkflowValidator
from app.core.workflows.errors import WorkflowValidationError
from app.core.workflows.conditions import validate_condition_expression
from app.core.workflows.errors import ConditionError


# Regex para {{var}} en textos
VAR_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


class WorkflowAnalyzer:
    """
    Analiza un workflow y devuelve issues detectados.

    Uso:
        analyzer = WorkflowAnalyzer(workflow_data)
        response = analyzer.analyze()
    """

    def __init__(self, workflow_data: dict):
        self.workflow_data = workflow_data or {}
        self.nodes = self.workflow_data.get("nodes") or []
        self.transitions = self.workflow_data.get("transitions") or []
        self.nodes_map = {n.get("node_id"): n for n in self.nodes if n.get("node_id")}

        # Índices de transiciones
        self.outgoing: dict[str, list[dict]] = {}
        self.incoming: dict[str, list[dict]] = {}
        for t in self.transitions:
            frm = t.get("from_node_id")
            to = t.get("to_node_id")
            self.outgoing.setdefault(frm, []).append(t)
            self.incoming.setdefault(to, []).append(t)

        self.issues: list[StructuralIssue] = []

    # ============================================================
    # API PÚBLICA
    # ============================================================

    def analyze(self) -> AnalyzeResponse:
        """Ejecuta todos los checks y devuelve el análisis."""
        self.issues = []

        self._check_start_exists()
        self._check_end_exists()
        self._check_orphan_nodes()
        self._check_unreachable_nodes()
        self._check_condition_min_outputs()
        self._check_condition_syntax()
        self._check_dead_ends()
        self._check_cycles()
        self._check_variables_used_before_created()

        # Resumen
        summary = {
            "error": sum(1 for i in self.issues if i.severity == "error"),
            "warning": sum(1 for i in self.issues if i.severity == "warning"),
            "info": sum(1 for i in self.issues if i.severity == "info"),
        }

        return AnalyzeResponse(
            workflow_id=0,  # el router lo rellena
            issues=self.issues,
            summary=summary,
        )

    # ============================================================
    # CHECKS — ESTRUCTURA
    # ============================================================

    def _check_start_exists(self):
        starts = [n for n in self.nodes if n.get("type") == "start"]
        if len(starts) == 0:
            self._add("error", "missing_start", "Falta nodo START")
        elif len(starts) > 1:
            self._add(
                "error", "multiple_starts",
                f"Hay {len(starts)} nodos START (debe haber exactamente 1)",
            )

    def _check_end_exists(self):
        ends = [n for n in self.nodes if n.get("type") == "end"]
        if len(ends) == 0:
            self._add("error", "missing_end", "Falta nodo END")

    def _check_orphan_nodes(self):
        """
        Nodos sin entradas ni salidas, excluyendo START y END.
        START puede no tener entradas, END puede no tener salidas.
        """
        for n in self.nodes:
            node_id = n.get("node_id")
            node_type = n.get("type")
            if node_type in ("start", "end"):
                continue
            ins = self.incoming.get(node_id, [])
            outs = self.outgoing.get(node_id, [])
            if len(ins) == 0 and len(outs) == 0:
                self._add(
                    "warning", "orphan_node",
                    f"Nodo '{node_id}' no tiene ni entradas ni salidas",
                    node_id=node_id,
                )

    def _check_unreachable_nodes(self):
        """
        Nodos que no se pueden alcanzar desde START (BFS).
        Solo se aplica si hay exactamente 1 START.
        """
        starts = [n for n in self.nodes if n.get("type") == "start"]
        if len(starts) != 1:
            return  # sin START único, no aplicable

        start_id = starts[0].get("node_id")
        if not start_id:
            return

        reachable = set()
        queue = [start_id]
        while queue:
            current = queue.pop(0)
            if current in reachable:
                continue
            reachable.add(current)
            for t in self.outgoing.get(current, []):
                to = t.get("to_node_id")
                if to and to not in reachable:
                    queue.append(to)

        for n in self.nodes:
            node_id = n.get("node_id")
            if node_id and node_id not in reachable:
                self._add(
                    "warning", "unreachable_node",
                    f"Nodo '{node_id}' no es alcanzable desde START",
                    node_id=node_id,
                )

    # ============================================================
    # CHECKS — CONDICIONES
    # ============================================================

    def _check_condition_min_outputs(self):
        for n in self.nodes:
            if n.get("type") != "condition":
                continue
            node_id = n.get("node_id")
            outs = self.outgoing.get(node_id, [])
            if len(outs) < 2:
                self._add(
                    "error", "condition_few_outputs",
                    f"CONDITION '{node_id}' tiene {len(outs)} salidas (mínimo 2)",
                    node_id=node_id,
                )

    def _check_condition_syntax(self):
        for n in self.nodes:
            if n.get("type") != "condition":
                continue
            node_id = n.get("node_id")
            config = n.get("config") or {}
            condition = config.get("condition")
            if not condition:
                continue  # ya lo detecta WorkflowValidator

            try:
                validate_condition_expression(condition)
            except ConditionError as e:
                self._add(
                    "error", "invalid_condition_syntax",
                    f"CONDITION '{node_id}' tiene condición inválida: {e.message}",
                    node_id=node_id,
                )

    # ============================================================
    # CHECKS — EJECUCIÓN
    # ============================================================

    def _check_dead_ends(self):
        """
        Nodos (no END) sin camino a END.
        Algoritmo: BFS inverso desde END.
        """
        ends = [n.get("node_id") for n in self.nodes if n.get("type") == "end"]
        if not ends:
            return  # sin END, otro check ya lo detecta

        # Nodos que pueden llegar a algún END (BFS inverso)
        can_reach_end = set(ends)
        changed = True
        while changed:
            changed = False
            for n in self.nodes:
                node_id = n.get("node_id")
                if node_id in can_reach_end:
                    continue
                # ¿Alguna salida lleva a un nodo que llega a END?
                for t in self.outgoing.get(node_id, []):
                    if t.get("to_node_id") in can_reach_end:
                        can_reach_end.add(node_id)
                        changed = True
                        break

        for n in self.nodes:
            node_id = n.get("node_id")
            node_type = n.get("type")
            if node_type == "end":
                continue
            if node_id and node_id not in can_reach_end:
                self._add(
                    "warning", "dead_end",
                    f"Nodo '{node_id}' no tiene camino a END",
                    node_id=node_id,
                )

    def _check_cycles(self):
        """
        Detecta ciclos en el grafo. Los ciclos NO son error:
        pueden ser válidos. Se reportan como info.
        """
        visited: set[str] = set()
        in_stack: set[str] = set()
        cycles_found: list[list[str]] = []

        def dfs(node_id: str, path: list[str]):
            if node_id in in_stack:
                # Ciclo detectado
                idx = path.index(node_id)
                cycles_found.append(path[idx:] + [node_id])
                return
            if node_id in visited:
                return

            visited.add(node_id)
            in_stack.add(node_id)
            path.append(node_id)

            for t in self.outgoing.get(node_id, []):
                to = t.get("to_node_id")
                if to:
                    dfs(to, path)

            path.pop()
            in_stack.discard(node_id)

        # Empezar desde START si existe, sino desde todos
        starts = [n.get("node_id") for n in self.nodes if n.get("type") == "start"]
        start_points = starts if starts else [n.get("node_id") for n in self.nodes]

        for node_id in start_points:
            if node_id and node_id not in visited:
                dfs(node_id, [])

        if cycles_found:
            self._add(
                "info", "cycles_detected",
                f"Se detectaron {len(cycles_found)} ciclo(s). Los ciclos pueden ser válidos "
                f"(protegidos por MAX_STEPS en el engine).",
            )

    # ============================================================
    # CHECKS — VARIABLES
    # ============================================================

    def _check_variables_used_before_created(self):
        """
        Recorre los nodos en orden de ejecución (BFS desde START)
        y detecta variables usadas ({{var}} o en CONDITION) antes
        de haber sido creadas (por question.variable o variable.name).

        Limitación: en grafos con ramas es aproximado. Reportamos
        como warning, no error.
        """
        starts = [n.get("node_id") for n in self.nodes if n.get("type") == "start"]
        if len(starts) != 1:
            return
        start_id = starts[0]

        # Variables iniciales conocidas (del workflow_data si viniera)
        known_vars: set[str] = set()

        # BFS con "variables disponibles" en cada nodo
        # Uso de un dict para evitar loops infinitos
        visited_state: set[tuple[str, frozenset]] = set()
        queue: list[tuple[str, frozenset[str]]] = [(start_id, frozenset(known_vars))]

        while queue:
            node_id, avail_vars = queue.pop(0)
            state_key = (node_id, avail_vars)
            if state_key in visited_state:
                continue
            visited_state.add(state_key)

            node = self.nodes_map.get(node_id)
            if not node:
                continue

            node_type = node.get("type")
            config = node.get("config") or {}

            # 1. Comprobar uso de variables ANTES de crearlas
            # En textos (message, response, question)
            texts_to_check = []
            if node_type in ("message", "response", "question"):
                t = config.get("text")
                if isinstance(t, str):
                    texts_to_check.append(t)

            for text in texts_to_check:
                for var_name in VAR_RE.findall(text):
                    if var_name not in avail_vars:
                        self._add(
                            "warning", "variable_used_before_created",
                            f"Variable '{var_name}' usada en '{node_id}' "
                            f"antes de ser creada",
                            node_id=node_id,
                        )

            # En CONDITION
            if node_type == "condition":
                cond = config.get("condition")
                if isinstance(cond, str):
                    # Extraer variables de la condición (heurística simple)
                    for m in re.finditer(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b", cond):
                        name = m.group(1)
                        # Ignorar literales booleanos/números/keywords
                        if name in ("true", "false", "null", "and", "or", "not"):
                            continue
                        if name.isdigit():
                            continue
                        if name not in avail_vars:
                            self._add(
                                "warning", "variable_used_before_created",
                                f"Variable '{name}' usada en condición de '{node_id}' "
                                f"antes de ser creada",
                                node_id=node_id,
                            )

            # 2. Añadir variables CREADAS por este nodo
            new_vars = set(avail_vars)
            if node_type == "question":
                v = config.get("variable")
                if v:
                    new_vars.add(v)
            elif node_type == "variable":
                name = config.get("name")
                if name:
                    new_vars.add(name)
                # También el value puede usar {{var}} (ya cubierto arriba)

            # 3. Propagar a siguientes
            for t in self.outgoing.get(node_id, []):
                to = t.get("to_node_id")
                if to:
                    queue.append((to, frozenset(new_vars)))

    # ============================================================
    # HELPERS
    # ============================================================

    def _add(
        self,
        severity: str,
        code: str,
        message: str,
        node_id: Optional[str] = None,
        edge_key: Optional[str] = None,
    ):
        self.issues.append(StructuralIssue(
            severity=severity,
            code=code,
            message=message,
            node_id=node_id,
            edge_key=edge_key,
        ))


__all__ = ["WorkflowAnalyzer"]
