"""Callbacks de prompts interactivos para la integración con terminal_tool.

Estos callbacks conectan los prompts interactivos de terminal_tool (clarify,
sudo, approval) con el bucle de eventos de prompt_toolkit. Cada función recibe
la instancia de HermesCLI como primer argumento y usa su estado (colas,
referencia a la app) para coordinarse con la TUI.
"""

import queue
import time as _time

from hermes_cli.banner import cprint, _DIM, _RST


def clarify_callback(cli, question, choices):
    """Lanza una pregunta de aclaración a través de la TUI.

    Configura la UI de selección interactiva y bloquea hasta que el usuario
    responda. Devuelve la elección del usuario o un mensaje de timeout.
    """
    from cli import CLI_CONFIG

    timeout = CLI_CONFIG.get("clarify", {}).get("timeout", 120)
    response_queue = queue.Queue()
    is_open_ended = not choices or len(choices) == 0

    cli._clarify_state = {
        "question": question,
        "choices": choices if not is_open_ended else [],
        "selected": 0,
        "response_queue": response_queue,
    }
    cli._clarify_deadline = _time.monotonic() + timeout
    cli._clarify_freetext = is_open_ended

    if hasattr(cli, '_app') and cli._app:
        cli._app.invalidate()

    while True:
        try:
            result = response_queue.get(timeout=1)
            cli._clarify_deadline = 0
            return result
        except queue.Empty:
            remaining = cli._clarify_deadline - _time.monotonic()
            if remaining <= 0:
                break
            if hasattr(cli, '_app') and cli._app:
                cli._app.invalidate()

    cli._clarify_state = None
    cli._clarify_freetext = False
    cli._clarify_deadline = 0
    if hasattr(cli, '_app') and cli._app:
        cli._app.invalidate()
    cprint(f"\n{_DIM}(la aclaración expiró tras {timeout}s — el agente decidirá){_RST}")
    return (
        "El usuario no proporcionó una respuesta dentro del límite de tiempo. "
        "Usa tu mejor criterio para tomar la decisión y continuar."
    )


def sudo_password_callback(cli) -> str:
    """Pide la contraseña de sudo a través de la TUI.

    Configura un área de entrada de contraseña y bloquea hasta que el usuario
    responda.
    """
    timeout = 45
    response_queue = queue.Queue()

    cli._sudo_state = {"response_queue": response_queue}
    cli._sudo_deadline = _time.monotonic() + timeout

    if hasattr(cli, '_app') and cli._app:
        cli._app.invalidate()

    while True:
        try:
            result = response_queue.get(timeout=1)
            cli._sudo_state = None
            cli._sudo_deadline = 0
            if hasattr(cli, '_app') and cli._app:
                cli._app.invalidate()
            if result:
                cprint(f"\n{_DIM}  ✓ Contraseña recibida (cacheada para la sesión){_RST}")
            else:
                cprint(f"\n{_DIM}  ⏭ Omitido{_RST}")
            return result
        except queue.Empty:
            remaining = cli._sudo_deadline - _time.monotonic()
            if remaining <= 0:
                break
            if hasattr(cli, '_app') and cli._app:
                cli._app.invalidate()

    cli._sudo_state = None
    cli._sudo_deadline = 0
    if hasattr(cli, '_app') and cli._app:
        cli._app.invalidate()
    cprint(f"\n{_DIM}  ⏱ Timeout — continuando sin sudo{_RST}")
    return ""


def approval_callback(cli, command: str, description: str) -> str:
    """Pide aprobación para un comando peligroso a través de la TUI.

    Muestra una UI de selección con opciones: once / session / always / deny.
    Cuando el comando es más largo de 70 caracteres, se incluye una opción
    "view" para que el usuario pueda ver el texto completo antes de decidir.
    """
    timeout = 60
    response_queue = queue.Queue()
    choices = ["once", "session", "always", "deny"]
    if len(command) > 70:
        choices.append("view")

    cli._approval_state = {
        "command": command,
        "description": description,
        "choices": choices,
        "selected": 0,
        "response_queue": response_queue,
    }
    cli._approval_deadline = _time.monotonic() + timeout

    if hasattr(cli, '_app') and cli._app:
        cli._app.invalidate()

    while True:
        try:
            result = response_queue.get(timeout=1)
            cli._approval_state = None
            cli._approval_deadline = 0
            if hasattr(cli, '_app') and cli._app:
                cli._app.invalidate()
            return result
        except queue.Empty:
            remaining = cli._approval_deadline - _time.monotonic()
            if remaining <= 0:
                break
            if hasattr(cli, '_app') and cli._app:
                cli._app.invalidate()

    cli._approval_state = None
    cli._approval_deadline = 0
    if hasattr(cli, '_app') and cli._app:
        cli._app.invalidate()
    cprint(f"\n{_DIM}  ⏱ Timeout — denegando el comando{_RST}")
    return "deny"
