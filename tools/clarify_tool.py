#!/usr/bin/env python3
"""
Clarify Tool Module - Interactive Clarifying Questions

Allows the agent to present structured multiple-choice questions or open-ended
prompts to the user. In CLI mode, choices are navigable with arrow keys. On
messaging platforms, choices are rendered as a numbered list.

The actual user-interaction logic lives in the platform layer (cli.py for CLI,
gateway/run.py for messaging). This module defines the schema, validation, and
a thin dispatcher that delegates to a platform-provided callback.
"""

import json
from typing import Dict, Any, List, Optional, Callable


# Maximum number of predefined choices the agent can offer.
# A 5th "Other (type your answer)" option is always appended by the UI.
MAX_CHOICES = 4


def clarify_tool(
    question: str,
    choices: Optional[List[str]] = None,
    callback: Optional[Callable] = None,
) -> str:
    """
    Ask the user a question, optionally with multiple-choice options.

    Args:
        question: The question text to present.
        choices:  Up to 4 predefined answer choices. When omitted the
                  question is purely open-ended.
        callback: Platform-provided function that handles the actual UI
                  interaction. Signature: callback(question, choices) -> str.
                  Injected by the agent runner (cli.py / gateway).

    Returns:
        JSON string with the user's response.
    """
    if not question or not question.strip():
        return json.dumps({"error": "Question text is required."}, ensure_ascii=False)

    question = question.strip()

    # Validate and trim choices
    if choices is not None:
        if not isinstance(choices, list):
            return json.dumps({"error": "choices must be a list of strings."}, ensure_ascii=False)
        choices = [str(c).strip() for c in choices if str(c).strip()]
        if len(choices) > MAX_CHOICES:
            choices = choices[:MAX_CHOICES]
        if not choices:
            choices = None  # empty list → open-ended

    if callback is None:
        return json.dumps(
            {"error": "Clarify tool is not available in this execution context."},
            ensure_ascii=False,
        )

    try:
        user_response = callback(question, choices)
    except Exception as exc:
        return json.dumps(
            {"error": f"Failed to get user input: {exc}"},
            ensure_ascii=False,
        )

    return json.dumps({
        "question": question,
        "choices_offered": choices,
        "user_response": str(user_response).strip(),
    }, ensure_ascii=False)


def check_clarify_requirements() -> bool:
    """Clarify tool has no external requirements -- always available."""
    return True


# =============================================================================
# OpenAI Function-Calling Schema
# =============================================================================

CLARIFY_SCHEMA = {
    "name": "clarify",
    "description": (
        "Haz una pregunta al usuario cuando necesites aclaración, comentarios o una "
        "decisión antes de proceder. Soporta dos modos:\n\n"
        "1. **Múltiple opción** — proporciona hasta 4 opciones. El usuario elige una "
        "o escribe su propia respuesta a través de una opción 'Otro' de 5ta.\n"
        "2. **Extremo abierto** — omite las opciones completamente. El usuario escribe una "
        "respuesta de forma libre.\n\n"
        "Usa esta herramienta cuando:\n"
        "- La tarea es ambigua y necesitas que el usuario elija un enfoque\n"
        "- Quieres comentarios posteriores a la tarea ('\u00bfCuál fue el resultado?')\n"
        "- Quieres ofrecer guardar una habilidad o actualizar memoria\n"
        "- Una decisión tiene compensaciones significativas que el usuario debe considerar\n\n"
        "NO uses esta herramienta para confirmación simple de sí/no de comandos "
        "peligrosos (la herramienta de terminal maneja eso). Prefiere hacer una elección "
        "razonable por defecto cuando la decisión es de bajo riesgo."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "La pregunta a presentar al usuario.",
            },
            "choices": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": MAX_CHOICES,
                "description": (
                    "Hasta 4 opciones de respuesta. Omite este parámetro completamente para "
                    "hacer una pregunta de extremo abierto. Cuando se provided, la UI "
                    "automáticamente añade una opción 'Otro (escribe tu respuesta)'."
                ),
            },
        },
        "required": ["question"],
    },
}


# --- Registry ---
from tools.registry import registry

registry.register(
    name="clarify",
    toolset="clarify",
    schema=CLARIFY_SCHEMA,
    handler=lambda args, **kw: clarify_tool(
        question=args.get("question", ""),
        choices=args.get("choices"),
        callback=kw.get("callback")),
    check_fn=check_clarify_requirements,
)
