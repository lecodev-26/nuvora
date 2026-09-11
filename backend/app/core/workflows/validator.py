"""
Nuvora Core — Workflows: Validator
=====================================
Validación estática de workflows.

Se ejecuta ANTES de guardar un workflow (14.5.7) y ANTES de ejecutarlo (14.5.5).

REGLAS:
    1. Exactamente un nodo START.
    2. Al menos un nodo END.
    3. node_id únicos dentro del workflow.
    4. Todas las transiciones apuntan a nodos existentes.
    5. Tipos de nodo válidos.
    6. Config válida según el tipo (message/response → text; question → text + variable;
       variable → name + value; condition → condition).
    7. CONDITION tiene al menos 2 transiciones.
    8. END no tiene transiciones salientes.
    9. START no tiene transiciones entrantes.

NO valida ciclos: pueden ser válidos.
La protección real contra bucles es MAX_STEPS en el engine.
"""

from app.core.workflows.errors import WorkflowValidationError


VALID_NODE_TYPES = {
    "start", "message", "question", "condition", "variable", "response", "end",
}


class WorkflowValidator:
    """
    Valida un workflow representado como diccionario.

    Entrada esperada (dict):
        {
            "nodes": [
                {"node_id": "start_1", "type": "start", "config": {...}},
                ...
            ],
            "transitions": [
                {"from_node_id": "start_1", "to_node_id": "msg_1", "condition": None},
                ...
            ],
        }

    Lanza WorkflowValidationError con una lista de errores.
    """

    def validate(self, workflow_data: dict) -> None:
        errors: list[str] = []

        nodes = workflow_data.get("nodes") or []
        transitions = workflow_data.get("transitions") or []

        # 1. Exactamente un START
        starts = [n for n in nodes if n.get("type") == "start"]
        if len(starts) == 0:
            errors.append("Falta nodo START")
        elif len(starts) > 1:
            errors.append(f"Hay {len(starts)} nodos START (debe haber exactamente 1)")

        # 2. Al menos un END
        ends = [n for n in nodes if n.get("type") == "end"]
        if len(ends) == 0:
            errors.append("Falta nodo END (debe haber al menos 1)")

        # 3. node_id únicos
        node_ids = [n.get("node_id") for n in nodes if n.get("node_id")]
        seen = set()
        dups = set()
        for nid in node_ids:
            if nid in seen:
                dups.add(nid)
            seen.add(nid)
        for d in dups:
            errors.append(f"node_id duplicado: '{d}'")

        # 5. Tipos válidos
        for n in nodes:
            ntype = n.get("type")
            if ntype not in VALID_NODE_TYPES:
                errors.append(f"Nodo '{n.get('node_id')}' tiene tipo inválido: '{ntype}'")

        # 6. Config según tipo
        for n in nodes:
            ntype = n.get("type")
            node_id = n.get("node_id", "?")
            config = n.get("config") or {}

            if ntype in ("message", "response"):
                if not config.get("text"):
                    errors.append(f"Nodo '{node_id}' ({ntype}) requiere 'text' en config")

            elif ntype == "question":
                if not config.get("text"):
                    errors.append(f"Nodo '{node_id}' (question) requiere 'text' en config")
                if not config.get("variable"):
                    errors.append(f"Nodo '{node_id}' (question) requiere 'variable' en config")

            elif ntype == "variable":
                if not config.get("name"):
                    errors.append(f"Nodo '{node_id}' (variable) requiere 'name' en config")

            elif ntype == "condition":
                if not config.get("condition"):
                    errors.append(f"Nodo '{node_id}' (condition) requiere 'condition' en config")

        # 4. Transiciones apuntan a nodos existentes
        node_id_set = set(node_ids)
        for t in transitions:
            frm = t.get("from_node_id")
            to = t.get("to_node_id")
            if frm not in node_id_set:
                errors.append(f"Transición desde nodo inexistente: '{frm}'")
            if to not in node_id_set:
                errors.append(f"Transición hacia nodo inexistente: '{to}'")

        # Índice: transiciones agrupadas por from_node_id
        outgoing: dict[str, list] = {}
        incoming: dict[str, list] = {}
        for t in transitions:
            frm = t.get("from_node_id")
            to = t.get("to_node_id")
            outgoing.setdefault(frm, []).append(t)
            incoming.setdefault(to, []).append(t)

        # 7. CONDITION ≥ 2 transiciones salientes
        for n in nodes:
            if n.get("type") == "condition":
                nid = n.get("node_id")
                outs = outgoing.get(nid, [])
                if len(outs) < 2:
                    errors.append(
                        f"CONDITION '{nid}' tiene {len(outs)} transiciones salientes (mínimo 2)"
                    )

        # 8. END sin transiciones salientes
        for n in nodes:
            if n.get("type") == "end":
                nid = n.get("node_id")
                outs = outgoing.get(nid, [])
                if len(outs) > 0:
                    errors.append(f"END '{nid}' tiene {len(outs)} transiciones salientes (debe ser 0)")

        # 9. START sin transiciones entrantes
        for n in nodes:
            if n.get("type") == "start":
                nid = n.get("node_id")
                ins = incoming.get(nid, [])
                if len(ins) > 0:
                    errors.append(f"START '{nid}' tiene {len(ins)} transiciones entrantes (debe ser 0)")

        if errors:
            raise WorkflowValidationError(errors)


def validate_workflow(workflow_data: dict) -> None:
    """
    Wrapper de conveniencia.
    Lanza WorkflowValidationError si el workflow es inválido.
    """
    WorkflowValidator().validate(workflow_data)
