"""Definición de comandos slash y autocompletado para el CLI de Hermes.

Contiene el diccionario compartido de comandos integrados ``COMMANDS`` y el
``SlashCommandCompleter``.
El autocompletado puede incluir opcionalmente comandos slash de skills
dinámicos proporcionados por el CLI interactivo.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from prompt_toolkit.completion import Completer, Completion


# Comandos organizados por categoría para una mejor visualización en la ayuda
COMMANDS_BY_CATEGORY = {
    "Session": {
        "/new": "Iniciar una nueva conversación (reinicia el historial)",
        "/reset": "Reiniciar solo la conversación (mantener pantalla)",
        "/clear": "Limpiar pantalla y reiniciar conversación (inicio en limpio)",
        "/history": "Mostrar historial de conversación",
        "/save": "Guardar la conversación actual",
        "/retry": "Reintentar el último mensaje (reenviarlo al agente)",
        "/undo": "Eliminar el último intercambio usuario/agente",
        "/title": "Establecer un título para la sesión actual (uso: /title Mi Título)",
        "/compress": "Comprimir manualmente el contexto (vaciar memorias + resumir)",
        "/rollback": "Listar o restaurar checkpoints del sistema de archivos (uso: /rollback [número])",
        "/background": "Ejecutar un prompt en segundo plano (uso: /background <prompt>)",
    },
    "Configuration": {
        "/config": "Mostrar la configuración actual",
        "/model": "Mostrar o cambiar el modelo actual",
        "/provider": "Mostrar proveedores disponibles y el proveedor actual",
        "/prompt": "Ver/establecer un system prompt personalizado",
        "/personality": "Establecer una personalidad predefinida",
        "/verbose": "Ciclar el progreso de herramientas: off → new → all → verbose",
        "/reasoning": "Gestionar esfuerzo y visualización del razonamiento (uso: /reasoning [nivel|show|hide])",
        "/skin": "Mostrar o cambiar el skin/tema de la interfaz",
    },
    "Tools & Skills": {
        "/tools": "Listar herramientas disponibles",
        "/toolsets": "Listar toolsets disponibles",
        "/skills": "Buscar, instalar, inspeccionar o gestionar skills desde registros en línea",
        "/cron": "Gestionar tareas programadas (listar, añadir, eliminar)",
        "/reload-mcp": "Recargar servidores MCP desde config.yaml",
    },
    "Info": {
        "/help": "Mostrar este mensaje de ayuda",
        "/usage": "Mostrar uso de tokens en la sesión actual",
        "/insights": "Mostrar insights y métricas de uso (últimos 30 días)",
        "/platforms": "Mostrar estado de gateway/plataformas de mensajería",
        "/paste": "Revisar el portapapeles por una imagen y adjuntarla",
    },
    "Exit": {
        "/quit": "Salir del CLI (también: /exit, /q)",
    },
}

# Flat dict for backwards compatibility and autocomplete
COMMANDS = {}
for category_commands in COMMANDS_BY_CATEGORY.values():
    COMMANDS.update(category_commands)


class SlashCommandCompleter(Completer):
    """Autocompletado para comandos slash integrados y comandos de skills."""

    def __init__(
        self,
        skill_commands_provider: Callable[[], Mapping[str, dict[str, Any]]] | None = None,
    ) -> None:
        self._skill_commands_provider = skill_commands_provider

    def _iter_skill_commands(self) -> Mapping[str, dict[str, Any]]:
        if self._skill_commands_provider is None:
            return {}
        try:
            return self._skill_commands_provider() or {}
        except Exception:
            return {}

    @staticmethod
    def _completion_text(cmd_name: str, word: str) -> str:
        """Devuelve el texto de reemplazo para un completion.

        Cuando el usuario ya ha escrito el comando completo exactamente
        (``/help``), devolver ``help`` sería un no-op y prompt_toolkit suprime
        el menú. Añadir un espacio final mantiene el desplegable visible y hace
        que al borrar se vuelva a disparar de forma natural.
        """
        return f"{cmd_name} " if cmd_name == word else cmd_name

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if not text.startswith("/"):
            return

        word = text[1:]

        for cmd, desc in COMMANDS.items():
            cmd_name = cmd[1:]
            if cmd_name.startswith(word):
                yield Completion(
                    self._completion_text(cmd_name, word),
                    start_position=-len(word),
                    display=cmd,
                    display_meta=desc,
                )

        for cmd, info in self._iter_skill_commands().items():
            cmd_name = cmd[1:]
            if cmd_name.startswith(word):
                description = str(info.get("description", "Comando de skill"))
                short_desc = description[:50] + ("..." if len(description) > 50 else "")
                yield Completion(
                    self._completion_text(cmd_name, word),
                    start_position=-len(word),
                    display=cmd,
                    display_meta=f"⚡ {short_desc}",
                )
