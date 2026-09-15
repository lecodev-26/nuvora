"""
Nuvora Core — AI: Workflow Designer
======================================
Orquestador del AI Workflow Designer (Fase 14.7).

RESPONSABILIDADES:
    - Construir el provider (con BYOK si aplica).
    - Construir los prompts (system + user).
    - Llamar al provider.
    - Parsear JSON con Pydantic.
    - Validar con WorkflowValidator (14.5.4) + validate_condition_expression.
    - Retry con feedback si el JSON no pasa el validador.
    - Devolver el resultado listo para el frontend.

FILOSOFÍA:
    - La IA produce datos JSON.
    - El validator (14.5.4) sigue siendo la autoridad estructural.
    - Nada se guarda en BD aquí. El usuario decide si guardar.
    - Nada se ejecuta. Solo se valida estructura.

NO duplica lógica de 14.5. Reutiliza:
    - WorkflowValidator
    - validate_condition_expression
    - Schemas Pydantic (14.7.3)
    - Prompts (14.7.4)
    - Providers (14.7.5)
"""

import json
import logging
from typing import Optional

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.ai import (
    BotContext,
    GeneratedWorkflow,
    GenerateWorkflowResponse,
    ModifyWorkflowResponse,
    ExplainWorkflowResponse,
    AnalyzeWorkflowResponse,
)
from app.core.ai.provider import AIRequest
from app.core.ai.providers import get_provider
from app.core.ai.prompts import (
    SYSTEM_PROMPT_BASE,
    build_generate_prompt,
    build_modify_prompt,
    build_explain_prompt,
    build_analyze_prompt,
)
from app.core.ai.schemas import (
    GENERATE_RESPONSE_SCHEMA,
    MODIFY_RESPONSE_SCHEMA,
    EXPLAIN_RESPONSE_SCHEMA,
    ANALYZE_RESPONSE_SCHEMA,
)
from app.core.ai.errors import (
    AIError,
    AIProviderError,
    AIInvalidOutputError,
    AIConfigError,
    AIUnavailableError,
)
from app.core.workflows.validator import WorkflowValidator
from app.core.workflows.conditions import validate_condition_expression
from app.core.workflows.errors import WorkflowValidationError, ConditionError


logger = logging.getLogger(__name__)


MAX_VALIDATION_RETRIES = 2


class AIWorkflowDesigner:
    """
    Orquestador de las tareas de IA de Nuvora.

    Uso:
        designer = AIWorkflowDesigner(db=db, user_id=user.id)
        result = designer.generate("Quiero un bot que salude...")
    """

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    # ============================================================
    # GUARDS
    # ============================================================

    def _check_enabled(self) -> None:
        """Comprueba que la capa de IA está activa."""
        if not settings.ai.enabled:
            raise AIUnavailableError(
                "La capa de IA está deshabilitada. Contacta con el administrador."
            )

    def _get_provider(self):
        """Devuelve el provider con BYOK si aplica."""
        return get_provider(db=self.db, user_id=self.user_id)

    # ============================================================
    # GENERATE
    # ============================================================

    def generate(
        self,
        prompt: str,
        bot_context: Optional[BotContext] = None,
    ) -> GenerateWorkflowResponse:
        """
        Genera un workflow nuevo desde una descripción.

        Retry: si el JSON no pasa el WorkflowValidator, reintenta hasta
        MAX_VALIDATION_RETRIES veces con feedback de los errores.

        Raises:
            AIUnavailableError, AIProviderError, AIInvalidOutputError, AIError
        """
        self._check_enabled()
        provider = self._get_provider()

        user_prompt = build_generate_prompt(prompt, bot_context)

        last_validation_error: str | None = None

        for attempt in range(MAX_VALIDATION_RETRIES + 1):
            request = AIRequest(
                system_prompt=SYSTEM_PROMPT_BASE,
                user_prompt=self._augment_with_feedback(user_prompt, last_validation_error),
                json_schema=GENERATE_RESPONSE_SCHEMA,
                max_tokens=settings.ai.max_tokens_output,
                timeout=settings.ai.timeout_seconds,
            )

            ai_response = provider.generate_json(request)

            try:
                workflow_data = ai_response.data.get("workflow")
                if not workflow_data:
                    raise AIInvalidOutputError(
                        "El JSON no contiene 'workflow'.",
                        raw_output=json.dumps(ai_response.data)[:500],
                    )

                # 1. Parsear con Pydantic
                workflow = GeneratedWorkflow(**workflow_data)

                # 2. Validar estructura (14.5.4)
                self._validate_workflow_structure(workflow)

                # 3. Extraer campos extra
                explanation = ai_response.data.get("explanation", "")
                warnings = ai_response.data.get("warnings") or []

                return GenerateWorkflowResponse(
                    workflow=workflow,
                    explanation=explanation,
                    warnings=warnings,
                    provider_used=ai_response.provider,
                    tokens_used=ai_response.tokens_used,
                )

            except (ValidationError, WorkflowValidationError, ConditionError, AIInvalidOutputError) as e:
                last_validation_error = self._format_error(e)
                logger.warning(
                    f"[designer.generate] Intento {attempt + 1} falló validación: "
                    f"{last_validation_error}"
                )
                if attempt >= MAX_VALIDATION_RETRIES:
                    # Último intento también falló → error al usuario
                    raise AIInvalidOutputError(
                        f"Tras {MAX_VALIDATION_RETRIES + 1} intentos, el workflow "
                        f"generado no pasó la validación: {last_validation_error}",
                        raw_output=json.dumps(ai_response.data)[:500],
                    )

        # No debería llegar aquí
        raise AIInvalidOutputError("Error inesperado en generate()")

    # ============================================================
    # MODIFY
    # ============================================================

    def modify(
        self,
        workflow: GeneratedWorkflow,
        instruction: str,
    ) -> ModifyWorkflowResponse:
        """Modifica un workflow existente según una instrucción."""
        self._check_enabled()
        provider = self._get_provider()

        user_prompt = build_modify_prompt(workflow, instruction)

        last_validation_error: str | None = None

        for attempt in range(MAX_VALIDATION_RETRIES + 1):
            request = AIRequest(
                system_prompt=SYSTEM_PROMPT_BASE,
                user_prompt=self._augment_with_feedback(user_prompt, last_validation_error),
                json_schema=MODIFY_RESPONSE_SCHEMA,
                max_tokens=settings.ai.max_tokens_output,
                timeout=settings.ai.timeout_seconds,
            )

            ai_response = provider.generate_json(request)

            try:
                workflow_data = ai_response.data.get("workflow")
                if not workflow_data:
                    raise AIInvalidOutputError(
                        "El JSON no contiene 'workflow'.",
                        raw_output=json.dumps(ai_response.data)[:500],
                    )

                modified = GeneratedWorkflow(**workflow_data)
                self._validate_workflow_structure(modified)

                explanation = ai_response.data.get("explanation", "")
                warnings = ai_response.data.get("warnings") or []

                return ModifyWorkflowResponse(
                    workflow=modified,
                    explanation=explanation,
                    warnings=warnings,
                    provider_used=ai_response.provider,
                    tokens_used=ai_response.tokens_used,
                )

            except (ValidationError, WorkflowValidationError, ConditionError, AIInvalidOutputError) as e:
                last_validation_error = self._format_error(e)
                logger.warning(
                    f"[designer.modify] Intento {attempt + 1} falló validación: "
                    f"{last_validation_error}"
                )
                if attempt >= MAX_VALIDATION_RETRIES:
                    raise AIInvalidOutputError(
                        f"Tras {MAX_VALIDATION_RETRIES + 1} intentos, el workflow "
                        f"modificado no pasó la validación: {last_validation_error}",
                        raw_output=json.dumps(ai_response.data)[:500],
                    )

        raise AIInvalidOutputError("Error inesperado en modify()")

    # ============================================================
    # EXPLAIN
    # ============================================================

    def explain(self, workflow: GeneratedWorkflow) -> ExplainWorkflowResponse:
        """Explica un workflow en lenguaje humano."""
        self._check_enabled()
        provider = self._get_provider()

        user_prompt = build_explain_prompt(workflow)
        request = AIRequest(
            system_prompt=SYSTEM_PROMPT_BASE,
            user_prompt=user_prompt,
            json_schema=EXPLAIN_RESPONSE_SCHEMA,
            max_tokens=settings.ai.max_tokens_output,
            timeout=settings.ai.timeout_seconds,
        )

        ai_response = provider.generate_json(request)

        explanation = ai_response.data.get("explanation")
        if not explanation or not isinstance(explanation, str):
            raise AIInvalidOutputError(
                "El JSON no contiene 'explanation' válida.",
                raw_output=json.dumps(ai_response.data)[:500],
            )

        return ExplainWorkflowResponse(
            explanation=explanation,
            provider_used=ai_response.provider,
        )

    # ============================================================
    # ANALYZE
    # ============================================================

    def analyze(self, workflow: GeneratedWorkflow) -> AnalyzeWorkflowResponse:
        """Analiza un workflow: warnings + suggestions."""
        self._check_enabled()
        provider = self._get_provider()

        user_prompt = build_analyze_prompt(workflow)
        request = AIRequest(
            system_prompt=SYSTEM_PROMPT_BASE,
            user_prompt=user_prompt,
            json_schema=ANALYZE_RESPONSE_SCHEMA,
            max_tokens=settings.ai.max_tokens_output,
            timeout=settings.ai.timeout_seconds,
        )

        ai_response = provider.generate_json(request)

        warnings = ai_response.data.get("warnings") or []
        suggestions = ai_response.data.get("suggestions") or []

        if not isinstance(warnings, list) or not isinstance(suggestions, list):
            raise AIInvalidOutputError(
                "El JSON no contiene 'warnings' o 'suggestions' como listas.",
                raw_output=json.dumps(ai_response.data)[:500],
            )

        return AnalyzeWorkflowResponse(
            warnings=warnings,
            suggestions=suggestions,
            provider_used=ai_response.provider,
        )

    # ============================================================
    # HELPERS
    # ============================================================

    def _validate_workflow_structure(self, workflow: GeneratedWorkflow) -> None:
        """
        Valida el workflow con 14.5.4 + 14.5.6.

        Raises:
            WorkflowValidationError
            ConditionError
        """
        payload = {
            "nodes": [n.model_dump() for n in workflow.nodes],
            "transitions": [t.model_dump() for t in workflow.transitions],
        }

        # 1. Estructura
        WorkflowValidator().validate(payload)

        # 2. Condiciones
        for t in workflow.transitions:
            if t.condition:
                validate_condition_expression(t.condition)

    def _augment_with_feedback(self, user_prompt: str, last_error: str | None) -> str:
        """Añade feedback del intento anterior al prompt."""
        if not last_error:
            return user_prompt

        feedback = (
            "\n\n"
            "═══════════════════════════════════════════════════════════\n"
            "ATENCIÓN: tu respuesta anterior fue RECHAZADA por el validador:\n"
            f"{last_error}\n"
            "Corrige el JSON y devuélvelo de nuevo cumpliendo TODAS las reglas.\n"
            "═══════════════════════════════════════════════════════════\n"
        )
        return user_prompt + feedback

    def _format_error(self, e: Exception) -> str:
        """Formatea el error de validación para feedback."""
        if isinstance(e, WorkflowValidationError):
            return "Errores de estructura:\n- " + "\n- ".join(e.errors)
        if isinstance(e, ConditionError):
            return f"Condición inválida: {e.message}"
        if isinstance(e, ValidationError):
            # Pydantic
            errors = []
            for err in e.errors():
                loc = ".".join(str(x) for x in err.get("loc", []))
                msg = err.get("msg", "")
                errors.append(f"{loc}: {msg}")
            return "Errores de schema:\n- " + "\n- ".join(errors)
        if isinstance(e, AIInvalidOutputError):
            return e.message
        return str(e)


__all__ = ["AIWorkflowDesigner"]
