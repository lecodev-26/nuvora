"""
Nuvora Core — Testing: AI Test Generator (Fase 14.8.12)
==========================================================
Genera definiciones de tests usando la infraestructura de 14.7.

FILOSOFÍA (aprobada en 14.8.1):
    - La IA NO ejecuta workflows.
    - La IA recibe el workflow como contexto.
    - Genera DEFINICIONES de tests (JSON).
    - Pydantic valida.
    - El usuario decide si guardarlos.
    - NUNCA se ejecuta nada automáticamente.

FLUJO:
    workflow_data (dict)
        ↓
    build_generate_tests_prompt()
        ↓
    AIProvider.generate_json()
        ↓
    Parse + validación Pydantic (TestCaseCreate)
        ↓
    GenerateAITestsResponse

REUTILIZA:
    - Provider Layer (14.7)
    - System prompt (14.7)
    - Rate limiting (14.7)
    - Pydantic schemas (14.8.2)
"""

import logging
from typing import Optional

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.test import (
    TestCaseCreate,
    GenerateAITestsResponse,
)
from app.core.ai.provider import AIRequest
from app.core.ai.providers import get_provider
from app.core.ai.prompts import (
    SYSTEM_PROMPT_BASE,
    build_generate_tests_prompt,
)
from app.core.ai.schemas import GENERATE_TESTS_RESPONSE_SCHEMA
from app.core.ai.errors import (
    AIInvalidOutputError,
    AIUnavailableError,
    AIError,
)
from app.core.testing.errors import TestDefinitionError


logger = logging.getLogger(__name__)


class AITestGenerator:
    """
    Genera tests a partir de un workflow usando IA.

    Uso:
        gen = AITestGenerator(db=db, user_id=user.id)
        result = gen.generate(workflow_data=wf_dict)
    """

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def generate(self, workflow_data: dict) -> GenerateAITestsResponse:
        """
        Genera definiciones de tests para el workflow.

        Args:
            workflow_data: dict con 'nodes' y 'transitions' (formato engine).

        Returns:
            GenerateAITestsResponse con definiciones (NO guardadas).

        Raises:
            AIUnavailableError, AIError, TestDefinitionError
        """
        # 1. Comprobar feature flag
        if not settings.ai.enabled:
            raise AIUnavailableError(
                "La capa de IA está deshabilitada. Contacta con el administrador."
            )

        # 2. Obtener provider (con BYOK si aplica)
        provider = get_provider(db=self.db, user_id=self.user_id)

        # 3. Construir prompts
        user_prompt = build_generate_tests_prompt(workflow_data)

        # 4. Llamar al provider
        request = AIRequest(
            system_prompt=SYSTEM_PROMPT_BASE,
            user_prompt=user_prompt,
            json_schema=GENERATE_TESTS_RESPONSE_SCHEMA,
            max_tokens=settings.ai.max_tokens_output,
            timeout=settings.ai.timeout_seconds,
        )

        ai_response = provider.generate_json(request)

        # 5. Parsear + validar
        return self._parse_response(ai_response.data)

    # ============================================================
    # INTERNOS
    # ============================================================

    def _parse_response(self, data: dict) -> GenerateAITestsResponse:
        """
        Parsea la respuesta de la IA y la valida con Pydantic.
        """
        generated_raw = data.get("generated")
        if not isinstance(generated_raw, list) or not generated_raw:
            raise AIInvalidOutputError(
                "El JSON no contiene 'generated' como lista no vacía.",
                raw_output=str(data)[:500],
            )

        # Validar cada test con Pydantic
        generated: list[TestCaseCreate] = []
        for i, item in enumerate(generated_raw):
            try:
                tc = TestCaseCreate(**item)
                generated.append(tc)
            except ValidationError as e:
                # Reportar el índice y los errores
                errors = []
                for err in e.errors():
                    loc = ".".join(str(x) for x in err.get("loc", []))
                    msg = err.get("msg", "")
                    errors.append(f"{loc}: {msg}")
                raise TestDefinitionError(
                    f"Test #{i + 1} inválido: {'; '.join(errors)}"
                )

        # Notas opcionales
        notes = data.get("notes") or []
        if not isinstance(notes, list):
            notes = []

        # Count declarado vs real
        declared_count = data.get("count")
        if declared_count is not None and declared_count != len(generated):
            notes.append(
                f"Aviso: la IA declaró {declared_count} tests, "
                f"pero se generaron {len(generated)}."
            )

        return GenerateAITestsResponse(
            generated=generated,
            count=len(generated),
            notes=notes,
            explanation="",  # placeholder por compatibilidad
            warnings=[],
            provider_used="",  # se rellena en el router
        )


__all__ = ["AITestGenerator"]
