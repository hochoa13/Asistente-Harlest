"""
Asistente de configuración interactivo para Hermes Agent.

Asistente modular con secciones que se pueden ejecutar de forma independiente:
    1. Modelo y proveedor — elige tu proveedor de IA y modelo
    2. Backend de terminal — dónde ejecuta comandos tu agente
    3. Plataformas de mensajería — conecta Telegram, Discord, etc.
    4. Herramientas — configura TTS, búsqueda web, generación de imágenes, etc.
    5. Ajustes del agente — iteraciones, compresión, reinicio de sesión

Los archivos de configuración se guardan en ~/.hermes/ para un acceso sencillo.
"""

import importlib.util
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.resolve()


def _model_config_dict(config: Dict[str, Any]) -> Dict[str, Any]:
    current_model = config.get("model")
    if isinstance(current_model, dict):
        return dict(current_model)
    if isinstance(current_model, str) and current_model.strip():
        return {"default": current_model.strip()}
    return {}


def _set_model_provider(
    config: Dict[str, Any], provider_id: str, base_url: str = ""
) -> None:
    model_cfg = _model_config_dict(config)
    model_cfg["provider"] = provider_id
    if base_url:
        model_cfg["base_url"] = base_url.rstrip("/")
    else:
        model_cfg.pop("base_url", None)
    config["model"] = model_cfg


def _set_default_model(config: Dict[str, Any], model_name: str) -> None:
    if not model_name:
        return
    model_cfg = _model_config_dict(config)
    model_cfg["default"] = model_name
    config["model"] = model_cfg


def _sync_model_from_disk(config: Dict[str, Any]) -> None:
    disk_model = load_config().get("model")
    if isinstance(disk_model, dict):
        model_cfg = _model_config_dict(config)
        model_cfg.update(disk_model)
        config["model"] = model_cfg
    elif isinstance(disk_model, str) and disk_model.strip():
        _set_default_model(config, disk_model.strip())


# Import config helpers
from hermes_cli.config import (
    get_hermes_home,
    get_config_path,
    get_env_path,
    load_config,
    save_config,
    save_env_value,
    get_env_value,
    ensure_hermes_home,
    DEFAULT_CONFIG,
)

from hermes_cli.colors import Colors, color


def print_header(title: str):
    """Imprime un encabezado de sección."""
    print()
    print(color(f"◆ {title}", Colors.CYAN, Colors.BOLD))


def print_info(text: str):
    """Imprime texto informativo."""
    print(color(f"  {text}", Colors.DIM))


def print_success(text: str):
    """Imprime un mensaje de éxito."""
    print(color(f"✓ {text}", Colors.GREEN))


def print_warning(text: str):
    """Imprime un mensaje de advertencia."""
    print(color(f"⚠ {text}", Colors.YELLOW))


def print_error(text: str):
    """Imprime un mensaje de error."""
    print(color(f"✗ {text}", Colors.RED))


def prompt(question: str, default: str = None, password: bool = False) -> str:
    """Pide una entrada por consola con valor por defecto opcional."""
    if default:
        display = f"{question} [{default}]: "
    else:
        display = f"{question}: "

    try:
        if password:
            import getpass

            value = getpass.getpass(color(display, Colors.YELLOW))
        else:
            value = input(color(display, Colors.YELLOW))

        return value.strip() or default or ""
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(1)


def prompt_choice(question: str, choices: list, default: int = 0) -> int:
    """Pide elegir una opción de una lista con navegación por flechas.

    Escape mantiene el valor por defecto actual (omite la pregunta).
    Ctrl+C sale del asistente.
    """
    print(color(question, Colors.YELLOW))

    # Intentar usar un menú interactivo si está disponible
    try:
        from simple_term_menu import TerminalMenu
        import re

        # Eliminar caracteres emoji — simple_term_menu calcula mal el ancho
        # visual de los emojis, causando líneas duplicadas/corruptas al redibujar.
        _emoji_re = re.compile(
            "[\U0001f300-\U0001f9ff\U00002600-\U000027bf\U0000fe00-\U0000fe0f"
            "\U0001fa00-\U0001fa6f\U0001fa70-\U0001faff\u200d]+",
            flags=re.UNICODE,
        )
        menu_choices = [f"  {_emoji_re.sub('', choice).strip()}" for choice in choices]

        print_info("  ↑/↓ Navegar  Enter Seleccionar  Esc Omitir  Ctrl+C Salir")

        terminal_menu = TerminalMenu(
            menu_choices,
            cursor_index=default,
            menu_cursor="→ ",
            menu_cursor_style=("fg_green", "bold"),
            menu_highlight_style=("fg_green",),
            cycle_cursor=True,
            clear_screen=False,
        )

        idx = terminal_menu.show()
        if idx is None:  # Usuario pulsó Escape — mantener valor actual
            print_info("  Omitido (manteniendo el valor actual)")
            print()
            return default
        print()  # Add newline after selection
        return idx

    except (ImportError, NotImplementedError):
        pass
    except Exception as e:
        print(f"  (Interactive menu unavailable: {e})")

    # Alternativa: selección basada en números (simple_term_menu no soporta bien Windows)
    for i, choice in enumerate(choices):
        marker = "●" if i == default else "○"
        if i == default:
            print(color(f"  {marker} {choice}", Colors.GREEN))
        else:
            print(f"  {marker} {choice}")

    print_info(f"  Enter para valor por defecto ({default + 1})  Ctrl+C para salir")

    while True:
        try:
            value = input(
                color(f"  Select [1-{len(choices)}] ({default + 1}): ", Colors.DIM)
            )
            if not value:
                return default
            idx = int(value) - 1
            if 0 <= idx < len(choices):
                return idx
            print_error(f"Introduce un número entre 1 y {len(choices)}")
        except ValueError:
            print_error("Introduce un número")
        except (KeyboardInterrupt, EOFError):
            print()
            sys.exit(1)


def prompt_yes_no(question: str, default: bool = True) -> bool:
    """Pide una respuesta sí/no. Ctrl+C sale, entrada vacía devuelve el valor por defecto."""
    default_str = "Y/n" if default else "y/N"

    while True:
        try:
            value = (
                input(color(f"{question} [{default_str}]: ", Colors.YELLOW))
                .strip()
                .lower()
            )
        except (KeyboardInterrupt, EOFError):
            print()
            sys.exit(1)

        if not value:
            return default
        if value in ("y", "yes"):
            return True
        if value in ("n", "no"):
            return False
        print_error("Introduce 'y' o 'n'")


def prompt_checklist(title: str, items: list, pre_selected: list = None) -> list:
    """
    Muestra una checklist multi-selección y devuelve los índices seleccionados.

    Cada elemento en `items` es una cadena para mostrar. `pre_selected` es una
    lista de índices que deberían marcarse por defecto. Se añade al final una
    opción de "Continuar →" — el usuario alterna elementos con Espacio y
    confirma con Enter sobre "Continuar →".

    Si simple_term_menu no está disponible, se usa una interfaz numerada.

    Devuelve:
        Lista de índices seleccionados (sin incluir la opción Continuar).
    """
    if pre_selected is None:
        pre_selected = []

    print(color(title, Colors.YELLOW))
    print_info("  ESPACIO Alternar  ENTER Confirmar  ESC Omitir  Ctrl+C Salir")
    print()

    try:
        from simple_term_menu import TerminalMenu
        import re

        # Eliminar emojis de las etiquetas — simple_term_menu calcula mal
        # el ancho visual de los emojis en macOS, causando líneas corruptas.
        _emoji_re = re.compile(
            "[\U0001f300-\U0001f9ff\U00002600-\U000027bf\U0000fe00-\U0000fe0f"
            "\U0001fa00-\U0001fa6f\U0001fa70-\U0001faff\u200d]+",
            flags=re.UNICODE,
        )
        menu_items = [f"  {_emoji_re.sub('', item).strip()}" for item in items]

        # Mapear índices preseleccionados a las cadenas reales del menú
        preselected = [menu_items[i] for i in pre_selected if i < len(menu_items)]

        terminal_menu = TerminalMenu(
            menu_items,
            multi_select=True,
            show_multi_select_hint=False,
            multi_select_cursor="[✓] ",
            multi_select_select_on_accept=False,
            multi_select_empty_ok=True,
            preselected_entries=preselected if preselected else None,
            menu_cursor="→ ",
            menu_cursor_style=("fg_green", "bold"),
            menu_highlight_style=("fg_green",),
            cycle_cursor=True,
            clear_screen=False,
        )

        terminal_menu.show()

        if terminal_menu.chosen_menu_entries is None:
            print_info("  Skipped (keeping current)")
            return list(pre_selected)

        selected = list(terminal_menu.chosen_menu_indices or [])
        return selected

    except (ImportError, NotImplementedError):
        # Alternativa: interfaz numerada (simple_term_menu no soporta bien Windows)
        selected = set(pre_selected)

        while True:
            for i, item in enumerate(items):
                marker = color("[✓]", Colors.GREEN) if i in selected else "[ ]"
                print(f"  {marker} {i + 1}. {item}")
            print()

            try:
                value = input(
                    color("  Toggle # (or Enter to confirm): ", Colors.DIM)
                ).strip()
                if not value:
                    break
                idx = int(value) - 1
                if 0 <= idx < len(items):
                    if idx in selected:
                        selected.discard(idx)
                    else:
                        selected.add(idx)
                else:
                    print_error(f"Introduce un número entre 1 y {len(items)}")
            except ValueError:
                print_error("Introduce un número")
            except (KeyboardInterrupt, EOFError):
                print()
                return []

            # Clear and redraw (simple approach)
            print()

        return sorted(selected)


def _prompt_api_key(var: dict):
    """Muestra una pantalla formateada para introducir una API key de una variable de entorno."""
    tools = var.get("tools", [])
    tools_str = ", ".join(tools[:3])
    if len(tools) > 3:
        tools_str += f", +{len(tools) - 3} más"

    print()
    print(color(f"  ─── {var.get('description', var['name'])} ───", Colors.CYAN))
    print()
    if tools_str:
        print_info(f"  Habilita: {tools_str}")
    if var.get("url"):
        print_info(f"  Obtén tu key en: {var['url']}")
    print()

    if var.get("password"):
        value = prompt(f"  {var.get('prompt', var['name'])}", password=True)
    else:
        value = prompt(f"  {var.get('prompt', var['name'])}")

    if value:
        save_env_value(var["name"], value)
        print_success("  ✓ Guardado")
    else:
        print_warning("  Omitido (configura más tarde con 'hermes setup')")


def _print_setup_summary(config: dict, hermes_home):
    """Imprime el resumen final de la configuración."""
    # Resumen de disponibilidad de herramientas
    print()
    print_header("Resumen de disponibilidad de herramientas")

    tool_status = []

    # OpenRouter (requerido para visión y MoA)
    if get_env_value("OPENROUTER_API_KEY"):
        tool_status.append(("Visión (análisis de imágenes)", True, None))
        tool_status.append(("Mezcla de agentes (Mixture of Agents)", True, None))
    else:
        tool_status.append(("Vision (image analysis)", False, "OPENROUTER_API_KEY"))
        tool_status.append(("Mixture of Agents", False, "OPENROUTER_API_KEY"))

    # Firecrawl (herramientas web)
    if get_env_value("FIRECRAWL_API_KEY") or get_env_value("FIRECRAWL_API_URL"):
        tool_status.append(("Búsqueda y extracción web", True, None))
    else:
        tool_status.append(("Búsqueda y extracción web", False, "FIRECRAWL_API_KEY"))

    # Herramientas de navegador (Chromium local o Browserbase en la nube)
    import shutil

    _ab_found = (
        shutil.which("agent-browser")
        or (
            Path(__file__).parent.parent / "node_modules" / ".bin" / "agent-browser"
        ).exists()
    )
    if get_env_value("BROWSERBASE_API_KEY"):
        tool_status.append(("Automatización de navegador (Browserbase)", True, None))
    elif _ab_found:
        tool_status.append(("Automatización de navegador (local)", True, None))
    else:
        tool_status.append(
            ("Automatización de navegador", False, "npm install -g agent-browser")
        )

    # FAL (generación de imágenes)
    if get_env_value("FAL_KEY"):
        tool_status.append(("Generación de imágenes", True, None))
    else:
        tool_status.append(("Generación de imágenes", False, "FAL_KEY"))

    # TTS — mostrar proveedor configurado
    tts_provider = config.get("tts", {}).get("provider", "edge")
    if tts_provider == "elevenlabs" and get_env_value("ELEVENLABS_API_KEY"):
        tool_status.append(("Texto a voz (ElevenLabs)", True, None))
    elif tts_provider == "openai" and get_env_value("VOICE_TOOLS_OPENAI_KEY"):
        tool_status.append(("Texto a voz (OpenAI)", True, None))
    else:
        tool_status.append(("Texto a voz (Edge TTS)", True, None))

    # Tinker + WandB (entrenamiento RL)
    if get_env_value("TINKER_API_KEY") and get_env_value("WANDB_API_KEY"):
        tool_status.append(("Entrenamiento RL (Tinker)", True, None))
    elif get_env_value("TINKER_API_KEY"):
        tool_status.append(("Entrenamiento RL (Tinker)", False, "WANDB_API_KEY"))
    else:
        tool_status.append(("Entrenamiento RL (Tinker)", False, "TINKER_API_KEY"))

    # Home Assistant
    if get_env_value("HASS_TOKEN"):
        tool_status.append(("Hogar inteligente (Home Assistant)", True, None))

    # Skills Hub
    if get_env_value("GITHUB_TOKEN"):
        tool_status.append(("Skills Hub (GitHub)", True, None))
    else:
        tool_status.append(("Skills Hub (GitHub)", False, "GITHUB_TOKEN"))

    # Terminal (siempre disponible si las dependencias del sistema están satisfechas)
    tool_status.append(("Terminal/Comandos", True, None))

    # Planificación de tareas (siempre disponible, en memoria)
    tool_status.append(("Planificación de tareas (todo)", True, None))

    # Skills (siempre disponibles: incluidas + creadas por el usuario)
    tool_status.append(("Skills (ver, crear, editar)", True, None))

    # Print status
    available_count = sum(1 for _, avail, _ in tool_status if avail)
    total_count = len(tool_status)

    print_info(f"{available_count}/{total_count} categorías de herramientas disponibles:")
    print()

    for name, available, missing_var in tool_status:
        if available:
            print(f"   {color('✓', Colors.GREEN)} {name}")
        else:
            print(
                f"   {color('✗', Colors.RED)} {name} {color(f'(falta {missing_var})', Colors.DIM)}"
            )

    print()

    disabled_tools = [(name, var) for name, avail, var in tool_status if not avail]
    if disabled_tools:
        print_warning(
            "Algunas herramientas están deshabilitadas. Ejecuta 'hermes setup tools' para configurarlas,"
        )
        print_warning(
            "o edita ~/.hermes/.env directamente para añadir las API keys que faltan."
        )
        print()

    # Banner de finalización
    print()
    print(
        color(
            "┌─────────────────────────────────────────────────────────┐", Colors.GREEN
        )
    )
    print(
        color(
            "│              ✓ ¡Configuración completa!                 │", Colors.GREEN
        )
    )
    print(
        color(
            "└─────────────────────────────────────────────────────────┘", Colors.GREEN
        )
    )
    print()

    # Mostrar ubicaciones de archivos de forma destacada
    print(color("📁 Todos tus archivos están en ~/.hermes/:", Colors.CYAN, Colors.BOLD))
    print()
    print(f"   {color('Ajustes:', Colors.YELLOW)}  {get_config_path()}")
    print(f"   {color('API Keys:', Colors.YELLOW)}  {get_env_path()}")
    print(
        f"   {color('Datos:', Colors.YELLOW)}      {hermes_home}/cron/, sessions/, logs/"
    )
    print()

    print(color("─" * 60, Colors.DIM))
    print()
    print(color("📝 Para editar tu configuración:", Colors.CYAN, Colors.BOLD))
    print()
    print(f"   {color('hermes setup', Colors.GREEN)}          Ejecuta de nuevo el asistente completo")
    print(f"   {color('hermes setup model', Colors.GREEN)}    Cambia modelo/proveedor")
    print(f"   {color('hermes setup terminal', Colors.GREEN)} Cambia el backend de terminal")
    print(f"   {color('hermes setup gateway', Colors.GREEN)}  Configura mensajería")
    print(f"   {color('hermes setup tools', Colors.GREEN)}    Configura proveedores de herramientas")
    print()
    print(f"   {color('hermes config', Colors.GREEN)}         Ver ajustes actuales")
    print(
        f"   {color('hermes config edit', Colors.GREEN)}    Abrir la config en tu editor"
    )
    print(f"   {color('hermes config set KEY VALUE', Colors.GREEN)}")
    print(f"                          Establecer un valor específico")
    print()
    print("   O edita los archivos directamente:")
    print(f"   {color(f'nano {get_config_path()}', Colors.DIM)}")
    print(f"   {color(f'nano {get_env_path()}', Colors.DIM)}")
    print()

    print(color("─" * 60, Colors.DIM))
    print()
    print(color("🚀 ¡Todo listo!", Colors.CYAN, Colors.BOLD))
    print()
    print(f"   {color('hermes', Colors.GREEN)}              Empezar a chatear")
    print(f"   {color('hermes gateway', Colors.GREEN)}      Iniciar gateway de mensajería")
    print(f"   {color('hermes doctor', Colors.GREEN)}       Comprobar problemas")
    print()


def _prompt_container_resources(config: dict):
    """Pide los ajustes de recursos del contenedor (Docker, Singularity, Modal, Daytona)."""
    terminal = config.setdefault("terminal", {})

    print()
    print_info("Ajustes de recursos del contenedor:")

    # Persistencia
    current_persist = terminal.get("container_persistent", True)
    persist_label = "yes" if current_persist else "no"
    print_info("  Un sistema de archivos persistente mantiene los archivos entre sesiones.")
    print_info("  Usa 'no' para sandboxes efímeros que se reinician cada vez.")
    persist_str = prompt(
        "  ¿Persistir el sistema de archivos entre sesiones? (yes/no)", persist_label
    )
    terminal["container_persistent"] = persist_str.lower() in ("yes", "true", "y", "1")

    # CPU
    current_cpu = terminal.get("container_cpu", 1)
    cpu_str = prompt("  Núcleos de CPU", str(current_cpu))
    try:
        terminal["container_cpu"] = float(cpu_str)
    except ValueError:
        pass

    # Memoria
    current_mem = terminal.get("container_memory", 5120)
    mem_str = prompt("  Memoria en MB (5120 = 5GB)", str(current_mem))
    try:
        terminal["container_memory"] = int(mem_str)
    except ValueError:
        pass

    # Disco
    current_disk = terminal.get("container_disk", 51200)
    disk_str = prompt("  Disco en MB (51200 = 50GB)", str(current_disk))
    try:
        terminal["container_disk"] = int(disk_str)
    except ValueError:
        pass


# Tool categories and provider config are now in tools_config.py (shared
# between `hermes tools` and `hermes setup tools`).


# =============================================================================
# Section 1: Model & Provider Configuration
# =============================================================================


def setup_model_provider(config: dict):
    """Configura el proveedor de inferencia y el modelo por defecto."""
    from hermes_cli.auth import (
        get_active_provider,
        get_provider_auth_state,
        PROVIDER_REGISTRY,
        format_auth_error,
        AuthError,
        fetch_nous_models,
        resolve_nous_runtime_credentials,
        _update_config_for_provider,
        _login_openai_codex,
        get_codex_auth_status,
        DEFAULT_CODEX_BASE_URL,
        detect_external_credentials,
    )

    print_header("Proveedor de inferencia")
    print_info("Elige cómo conectarte a tu modelo principal de chat.")
    print()

    existing_or = get_env_value("OPENROUTER_API_KEY")
    active_oauth = get_active_provider()
    existing_custom = get_env_value("OPENAI_BASE_URL")

    # Detect credentials from other CLI tools
    detected_creds = detect_external_credentials()
    if detected_creds:
        print_info("Se detectaron credenciales existentes:")
        for cred in detected_creds:
            if cred["provider"] == "openai-codex":
                print_success(f'  * {cred["label"]} -- selecciona "OpenAI Codex" para usarlo')
            else:
                print_info(f"  * {cred['label']}")
        print()

    # Detectar si ya hay algún proveedor configurado
    has_any_provider = bool(active_oauth or existing_custom or existing_or)

    # Construir la etiqueta de "mantener actual"
    if active_oauth and active_oauth in PROVIDER_REGISTRY:
        keep_label = f"Mantener actual ({PROVIDER_REGISTRY[active_oauth].name})"
    elif existing_custom:
        keep_label = f"Mantener actual (Personalizado: {existing_custom})"
    elif existing_or:
        keep_label = "Mantener actual (OpenRouter)"
    else:
        keep_label = None  # No provider configured — don't show "Keep current"

    provider_choices = [
        "Iniciar sesión con Nous Portal (suscripción Nous Research — OAuth)",
        "Iniciar sesión con OpenAI Codex",
        "API key de OpenRouter (100+ modelos, pago por uso)",
        "Endpoint compatible con OpenAI (self-hosted / VLLM / etc.)",
        "Z.AI / GLM (modelos de Zhipu AI)",
        "Kimi / Moonshot (modelos de Kimi para código)",
        "MiniMax (endpoint global)",
        "MiniMax China (endpoint para China continental)",
    ]
    if keep_label:
        provider_choices.append(keep_label)

    # Por defecto: "Mantener actual" si ya hay proveedor, si no OpenRouter (más común)
    default_provider = len(provider_choices) - 1 if has_any_provider else 2

    if not has_any_provider:
        print_warning("Se requiere un proveedor de inferencia para que Hermes funcione.")
        print()

    provider_idx = prompt_choice(
        "Select your inference provider:", provider_choices, default_provider
    )

    # Track which provider was selected for model step
    selected_provider = (
        None  # "nous", "openai-codex", "openrouter", "custom", or None (keep)
    )
    nous_models = []  # populated if Nous login succeeds

    if provider_idx == 0:  # Nous Portal (OAuth)
        selected_provider = "nous"
        print()
        print_header("Inicio de sesión en Nous Portal")
        print_info("Se abrirá tu navegador para autenticarte con Nous Portal.")
        print_info("Necesitas una cuenta de Nous Research con una suscripción activa.")
        print()

        try:
            from hermes_cli.auth import _login_nous, ProviderConfig
            import argparse

            mock_args = argparse.Namespace(
                portal_url=None,
                inference_url=None,
                client_id=None,
                scope=None,
                no_browser=False,
                timeout=15.0,
                ca_bundle=None,
                insecure=False,
            )
            pconfig = PROVIDER_REGISTRY["nous"]
            _login_nous(mock_args, pconfig)
            _sync_model_from_disk(config)

            # Obtener modelos para el paso de selección
            try:
                creds = resolve_nous_runtime_credentials(
                    min_key_ttl_seconds=5 * 60,
                    timeout_seconds=15.0,
                )
                nous_models = fetch_nous_models(
                    inference_base_url=creds.get("base_url", ""),
                    api_key=creds.get("api_key", ""),
                )
            except Exception as e:
                logger.debug("No se pudieron obtener los modelos de Nous tras el login: %s", e)

        except SystemExit:
            print_warning("El inicio de sesión en Nous Portal fue cancelado o falló.")
            print_info("Puedes intentarlo de nuevo más tarde con: hermes model")
            selected_provider = None
        except Exception as e:
            print_error(f"Inicio de sesión fallido: {e}")
            print_info("Puedes intentarlo de nuevo más tarde con: hermes model")
            selected_provider = None

    elif provider_idx == 1:  # OpenAI Codex
        selected_provider = "openai-codex"
        print()
        print_header("Inicio de sesión en OpenAI Codex")
        print()

        try:
            import argparse

            mock_args = argparse.Namespace()
            _login_openai_codex(mock_args, PROVIDER_REGISTRY["openai-codex"])
            # Clear custom endpoint vars that would override provider routing.
            if existing_custom:
                save_env_value("OPENAI_BASE_URL", "")
                save_env_value("OPENAI_API_KEY", "")
            _update_config_for_provider("openai-codex", DEFAULT_CODEX_BASE_URL)
            _set_model_provider(config, "openai-codex", DEFAULT_CODEX_BASE_URL)
        except SystemExit:
            print_warning("El inicio de sesión en OpenAI Codex fue cancelado o falló.")
            print_info("Puedes intentarlo de nuevo más tarde con: hermes model")
            selected_provider = None
        except Exception as e:
            print_error(f"Inicio de sesión fallido: {e}")
            print_info("Puedes intentarlo de nuevo más tarde con: hermes model")
            selected_provider = None

    elif provider_idx == 2:  # OpenRouter
        selected_provider = "openrouter"
        print()
        print_header("API key de OpenRouter")
        print_info("OpenRouter da acceso a más de 100 modelos de múltiples proveedores.")
        print_info("Obtén tu API key en: https://openrouter.ai/keys")

        if existing_or:
            print_info(f"Actual: {existing_or[:8]}... (configurada)")
            if prompt_yes_no("¿Actualizar API key de OpenRouter?", False):
                api_key = prompt("  API key de OpenRouter", password=True)
                if api_key:
                    save_env_value("OPENROUTER_API_KEY", api_key)
                    print_success("API key de OpenRouter actualizada")
        else:
            api_key = prompt("  API key de OpenRouter", password=True)
            if api_key:
                save_env_value("OPENROUTER_API_KEY", api_key)
                print_success("API key de OpenRouter guardada")
            else:
                print_warning("Omitido: el agente no funcionará sin una API key")

        # Clear any custom endpoint if switching to OpenRouter
        if existing_custom:
            save_env_value("OPENAI_BASE_URL", "")
            save_env_value("OPENAI_API_KEY", "")

        # Actualizar config.yaml y desactivar cualquier proveedor OAuth para
        # que el resolvedor no siga devolviendo el proveedor antiguo (p. ej. Codex).
        try:
            from hermes_cli.auth import deactivate_provider

            deactivate_provider()
        except Exception:
            pass
        import yaml

        config_path = (
            Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")) / "config.yaml"
        )
        try:
            disk_cfg = {}
            if config_path.exists():
                disk_cfg = yaml.safe_load(config_path.read_text()) or {}
            model_section = disk_cfg.get("model", {})
            if isinstance(model_section, str):
                model_section = {"default": model_section}
            model_section["provider"] = "openrouter"
            model_section.pop("base_url", None)  # OpenRouter uses default URL
            disk_cfg["model"] = model_section
            config_path.write_text(yaml.safe_dump(disk_cfg, sort_keys=False))
            _set_model_provider(config, "openrouter")
        except Exception as e:
            logger.debug("No se pudo guardar el proveedor en config.yaml: %s", e)

    elif provider_idx == 3:  # Custom endpoint
        selected_provider = "custom"
        print()
        print_header("Endpoint personalizado compatible con OpenAI")
        print_info("Funciona con cualquier API que siga la especificación de chat completions de OpenAI")

        current_url = get_env_value("OPENAI_BASE_URL") or ""
        current_key = get_env_value("OPENAI_API_KEY")
        _raw_model = config.get("model", "")
        current_model = (
            _raw_model.get("default", "")
            if isinstance(_raw_model, dict)
            else (_raw_model or "")
        )

        if current_url:
            print_info(f"  URL actual: {current_url}")
        if current_key:
            print_info(f"  Key actual: {current_key[:8]}... (configurada)")

        base_url = prompt(
            "  URL base de la API (ej.: https://api.example.com/v1)", current_url
        )
        api_key = prompt("  API key", password=True)
        model_name = prompt("  Nombre de modelo (ej.: gpt-4, claude-3-opus)", current_model)

        if base_url:
            save_env_value("OPENAI_BASE_URL", base_url)
        if api_key:
            save_env_value("OPENAI_API_KEY", api_key)
        if model_name:
            _set_default_model(config, model_name)

        try:
            from hermes_cli.auth import deactivate_provider

            deactivate_provider()
        except Exception:
            pass

        # Guardar provider y base_url en config.yaml para que el gateway y el CLI
        # resuelvan el proveedor correcto sin depender sólo de heurísticas con variables de entorno.
        if base_url:
            import yaml

            config_path = (
                Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
                / "config.yaml"
            )
            try:
                disk_cfg = {}
                if config_path.exists():
                    disk_cfg = yaml.safe_load(config_path.read_text()) or {}
                model_section = disk_cfg.get("model", {})
                if isinstance(model_section, str):
                    model_section = {"default": model_section}
                model_section["provider"] = "custom"
                model_section["base_url"] = base_url.rstrip("/")
                if model_name:
                    model_section["default"] = model_name
                disk_cfg["model"] = model_section
                config_path.write_text(yaml.safe_dump(disk_cfg, sort_keys=False))
            except Exception as e:
                logger.debug("No se pudo guardar el proveedor en config.yaml: %s", e)

            _set_model_provider(config, "custom", base_url)

        print_success("Endpoint personalizado configurado")

    elif provider_idx == 4:  # Z.AI / GLM
        selected_provider = "zai"
        print()
        print_header("API key de Z.AI / GLM")
        pconfig = PROVIDER_REGISTRY["zai"]
        print_info(f"Proveedor: {pconfig.name}")
        print_info("Obtén tu API key en: https://open.bigmodel.cn/")
        print()

        existing_key = get_env_value("GLM_API_KEY") or get_env_value("ZAI_API_KEY")
        api_key = existing_key  # will be overwritten if user enters a new one
        if existing_key:
            print_info(f"Actual: {existing_key[:8]}... (configurada)")
            if prompt_yes_no("¿Actualizar API key?", False):
                new_key = prompt("  API key de GLM", password=True)
                if new_key:
                    api_key = new_key
                    save_env_value("GLM_API_KEY", api_key)
                    print_success("API key de GLM actualizada")
        else:
            api_key = prompt("  API key de GLM", password=True)
            if api_key:
                save_env_value("GLM_API_KEY", api_key)
                print_success("API key de GLM guardada")
            else:
                print_warning("Omitido: el agente no funcionará sin una API key")

        # Detectar el endpoint correcto de z.ai para esta key.
        # Z.AI tiene facturación separada para planes generales vs. de código y
        # endpoints globales vs. China — se hace un sondeo para encontrar el adecuado.
        zai_base_url = pconfig.inference_base_url
        if api_key:
            print()
            print_info("Detectando tu endpoint de z.ai...")
            from hermes_cli.auth import detect_zai_endpoint

            detected = detect_zai_endpoint(api_key)
            if detected:
                zai_base_url = detected["base_url"]
                print_success(f"Detectado: endpoint {detected['label']}")
                print_info(f"  URL: {detected['base_url']}")
                if detected["id"].startswith("coding"):
                    print_info(
                        f"  Nota: se detectó un Coding Plan — GLM-5 no está disponible, usando {detected['model']}"
                    )
                save_env_value("GLM_BASE_URL", zai_base_url)
            else:
                print_warning("No se pudo verificar ningún endpoint de z.ai con esta key.")
                print_info(f"  Usando el por defecto: {zai_base_url}")
                print_info(
                    "  Si ves errores de facturación, revisa tu plan en https://open.bigmodel.cn/"
                )

        # Clear custom endpoint vars if switching
        if existing_custom:
            save_env_value("OPENAI_BASE_URL", "")
            save_env_value("OPENAI_API_KEY", "")
        _update_config_for_provider("zai", zai_base_url)
        _set_model_provider(config, "zai", zai_base_url)

    elif provider_idx == 5:  # Kimi / Moonshot
        selected_provider = "kimi-coding"
        print()
        print_header("API key de Kimi / Moonshot")
        pconfig = PROVIDER_REGISTRY["kimi-coding"]
        print_info(f"Proveedor: {pconfig.name}")
        print_info(f"Base URL: {pconfig.inference_base_url}")
        print_info("Obtén tu API key en: https://platform.moonshot.cn/")
        print()

        existing_key = get_env_value("KIMI_API_KEY")
        if existing_key:
            print_info(f"Actual: {existing_key[:8]}... (configurada)")
            if prompt_yes_no("¿Actualizar API key?", False):
                api_key = prompt("  API key de Kimi", password=True)
                if api_key:
                    save_env_value("KIMI_API_KEY", api_key)
                    print_success("API key de Kimi actualizada")
        else:
            api_key = prompt("  API key de Kimi", password=True)
            if api_key:
                save_env_value("KIMI_API_KEY", api_key)
                print_success("API key de Kimi guardada")
            else:
                print_warning("Omitido: el agente no funcionará sin una API key")

        # Clear custom endpoint vars if switching
        if existing_custom:
            save_env_value("OPENAI_BASE_URL", "")
            save_env_value("OPENAI_API_KEY", "")
        _update_config_for_provider("kimi-coding", pconfig.inference_base_url)
        _set_model_provider(config, "kimi-coding", pconfig.inference_base_url)

    elif provider_idx == 6:  # MiniMax
        selected_provider = "minimax"
        print()
        print_header("API key de MiniMax")
        pconfig = PROVIDER_REGISTRY["minimax"]
        print_info(f"Proveedor: {pconfig.name}")
        print_info(f"Base URL: {pconfig.inference_base_url}")
        print_info("Obtén tu API key en: https://platform.minimaxi.com/")
        print()

        existing_key = get_env_value("MINIMAX_API_KEY")
        if existing_key:
            print_info(f"Actual: {existing_key[:8]}... (configurada)")
            if prompt_yes_no("¿Actualizar API key?", False):
                api_key = prompt("  API key de MiniMax", password=True)
                if api_key:
                    save_env_value("MINIMAX_API_KEY", api_key)
                    print_success("API key de MiniMax actualizada")
        else:
            api_key = prompt("  API key de MiniMax", password=True)
            if api_key:
                save_env_value("MINIMAX_API_KEY", api_key)
                print_success("API key de MiniMax guardada")
            else:
                print_warning("Omitido: el agente no funcionará sin una API key")

        # Clear custom endpoint vars if switching
        if existing_custom:
            save_env_value("OPENAI_BASE_URL", "")
            save_env_value("OPENAI_API_KEY", "")
        _update_config_for_provider("minimax", pconfig.inference_base_url)
        _set_model_provider(config, "minimax", pconfig.inference_base_url)

    elif provider_idx == 7:  # MiniMax China
        selected_provider = "minimax-cn"
        print()
        print_header("API key de MiniMax China")
        pconfig = PROVIDER_REGISTRY["minimax-cn"]
        print_info(f"Proveedor: {pconfig.name}")
        print_info(f"Base URL: {pconfig.inference_base_url}")
        print_info("Obtén tu API key en: https://platform.minimaxi.com/")
        print()

        existing_key = get_env_value("MINIMAX_CN_API_KEY")
        if existing_key:
            print_info(f"Actual: {existing_key[:8]}... (configurada)")
            if prompt_yes_no("¿Actualizar API key?", False):
                api_key = prompt("  API key de MiniMax CN", password=True)
                if api_key:
                    save_env_value("MINIMAX_CN_API_KEY", api_key)
                    print_success("API key de MiniMax CN actualizada")
        else:
            api_key = prompt("  API key de MiniMax CN", password=True)
            if api_key:
                save_env_value("MINIMAX_CN_API_KEY", api_key)
                print_success("API key de MiniMax CN guardada")
            else:
                print_warning("Omitido: el agente no funcionará sin una API key")

        # Clear custom endpoint vars if switching
        if existing_custom:
            save_env_value("OPENAI_BASE_URL", "")
            save_env_value("OPENAI_API_KEY", "")
        _update_config_for_provider("minimax-cn", pconfig.inference_base_url)
        _set_model_provider(config, "minimax-cn", pconfig.inference_base_url)

    # else: provider_idx == 8 (Keep current) — only shown when a provider already exists

    # ── API key de OpenRouter para herramientas (si aún no está definida) ──
    # Las herramientas (visión, web, MoA) usan OpenRouter de forma independiente
    # del proveedor principal. Se pide la API key de OpenRouter si no está
    # configurada y se eligió un proveedor distinto de OpenRouter.
    if selected_provider in (
        "nous",
        "openai-codex",
        "custom",
        "zai",
        "kimi-coding",
        "minimax",
        "minimax-cn",
    ) and not get_env_value("OPENROUTER_API_KEY"):
        print()
        print_header("API key de OpenRouter (para herramientas)")
        print_info("Herramientas como análisis de visión, búsqueda web y MoA usan OpenRouter")
        print_info("de forma independiente de tu proveedor de inferencia principal.")
        print_info("Obtén tu API key en: https://openrouter.ai/keys")

        api_key = prompt(
            "  API key de OpenRouter (opcional, Enter para omitir)", password=True
        )
        if api_key:
            save_env_value("OPENROUTER_API_KEY", api_key)
            print_success("API key de OpenRouter guardada (para herramientas)")
        else:
            print_info(
                "Omitido: algunas herramientas (visión, scraping web) no funcionarán sin esto"
            )

    # ── Model Selection (adapts based on provider) ──
    if selected_provider != "custom":  # Custom already prompted for model name
        print_header("Modelo por defecto")

        _raw_model = config.get("model", "anthropic/claude-opus-4.6")
        current_model = (
            _raw_model.get("default", "anthropic/claude-opus-4.6")
            if isinstance(_raw_model, dict)
            else (_raw_model or "anthropic/claude-opus-4.6")
        )
        print_info(f"Actual: {current_model}")

        if selected_provider == "nous" and nous_models:
            # Lista dinámica de modelos desde Nous Portal
            model_choices = [f"{m}" for m in nous_models]
            model_choices.append("Custom model")
            model_choices.append(f"Keep current ({current_model})")

            # Validación post login: avisar si el modelo actual puede no estar disponible
            if current_model and current_model not in nous_models:
                print_warning(
                    f"Tu modelo actual ({current_model}) puede no estar disponible vía Nous Portal."
                )
                print_info(
                    "Selecciona un modelo de la lista, o mantén el actual para usarlo igualmente."
                )
                print()

            model_idx = prompt_choice(
                "Selecciona el modelo por defecto:", model_choices, len(model_choices) - 1
            )

            if model_idx < len(nous_models):
                _set_default_model(config, nous_models[model_idx])
            elif model_idx == len(model_choices) - 2:  # Custom
                model_name = prompt("  Model name")
                if model_name:
                    _set_default_model(config, model_name)
            # else: keep current

        elif selected_provider == "nous":
            # Login a Nous fue correcto pero la obtención de modelos falló —
            # pedir manualmente en lugar de usar la lista estática de OpenRouter.
            print_warning("No se pudieron obtener los modelos disponibles desde Nous Portal.")
            print_info("Introduce manualmente un modelo de Nous (por ejemplo, claude-opus-4-6).")
            custom = prompt(f"  Nombre de modelo (Enter para mantener '{current_model}')")
            if custom:
                _set_default_model(config, custom)
        elif selected_provider == "openai-codex":
            from hermes_cli.codex_models import get_codex_model_ids

            codex_models = get_codex_model_ids()
            model_choices = codex_models + [f"Keep current ({current_model})"]
            default_codex = 0
            if current_model in codex_models:
                default_codex = codex_models.index(current_model)
            elif current_model:
                default_codex = len(model_choices) - 1

            model_idx = prompt_choice(
                "Selecciona el modelo por defecto:", model_choices, default_codex
            )
            if model_idx < len(codex_models):
                _set_default_model(config, codex_models[model_idx])
            elif model_idx == len(codex_models):
                custom = prompt("Introduce el nombre del modelo")
                if custom:
                    _set_default_model(config, custom)
            _update_config_for_provider("openai-codex", DEFAULT_CODEX_BASE_URL)
            _set_model_provider(config, "openai-codex", DEFAULT_CODEX_BASE_URL)
        elif selected_provider == "zai":
            # Coding Plan endpoints don't have GLM-5
            is_coding_plan = get_env_value("GLM_BASE_URL") and "coding" in (
                get_env_value("GLM_BASE_URL") or ""
            )
            if is_coding_plan:
                zai_models = ["glm-4.7", "glm-4.5", "glm-4.5-flash"]
            else:
                zai_models = ["glm-5", "glm-4.7", "glm-4.5", "glm-4.5-flash"]
            model_choices = list(zai_models)
            model_choices.append("Modelo personalizado")
            model_choices.append(f"Mantener actual ({current_model})")

            keep_idx = len(model_choices) - 1
            model_idx = prompt_choice("Selecciona el modelo por defecto:", model_choices, keep_idx)

            if model_idx < len(zai_models):
                _set_default_model(config, zai_models[model_idx])
            elif model_idx == len(zai_models):
                custom = prompt("Introduce el nombre del modelo")
                if custom:
                    _set_default_model(config, custom)
            # else: keep current
        elif selected_provider == "kimi-coding":
            kimi_models = ["kimi-k2.5", "kimi-k2-thinking", "kimi-k2-turbo-preview"]
            model_choices = list(kimi_models)
            model_choices.append("Modelo personalizado")
            model_choices.append(f"Mantener actual ({current_model})")

            keep_idx = len(model_choices) - 1
            model_idx = prompt_choice("Selecciona el modelo por defecto:", model_choices, keep_idx)

            if model_idx < len(kimi_models):
                _set_default_model(config, kimi_models[model_idx])
            elif model_idx == len(kimi_models):
                custom = prompt("Introduce el nombre del modelo")
                if custom:
                    _set_default_model(config, custom)
            # else: keep current
        elif selected_provider in ("minimax", "minimax-cn"):
            minimax_models = ["MiniMax-M2.5", "MiniMax-M2.5-highspeed", "MiniMax-M2.1"]
            model_choices = list(minimax_models)
            model_choices.append("Modelo personalizado")
            model_choices.append(f"Mantener actual ({current_model})")

            keep_idx = len(model_choices) - 1
            model_idx = prompt_choice("Selecciona el modelo por defecto:", model_choices, keep_idx)

            if model_idx < len(minimax_models):
                _set_default_model(config, minimax_models[model_idx])
            elif model_idx == len(minimax_models):
                custom = prompt("Introduce el nombre del modelo")
                if custom:
                    _set_default_model(config, custom)
            # else: keep current
        else:
            # Static list for OpenRouter / fallback (from canonical list)
            from hermes_cli.models import model_ids, menu_labels

            ids = model_ids()
            model_choices = menu_labels() + [
                "Modelo personalizado",
                f"Mantener actual ({current_model})",
            ]

            keep_idx = len(model_choices) - 1
            model_idx = prompt_choice("Selecciona el modelo por defecto:", model_choices, keep_idx)

            if model_idx < len(ids):
                _set_default_model(config, ids[model_idx])
            elif model_idx == len(ids):  # Custom
                custom = prompt("Introduce el nombre del modelo (por ejemplo, anthropic/claude-opus-4.6)")
                if custom:
                    _set_default_model(config, custom)
            # else: Keep current

        _final_model = config.get("model", "")
        if _final_model:
            _display = (
                _final_model.get("default", _final_model)
                if isinstance(_final_model, dict)
                else _final_model
            )
            print_success(f"Modelo establecido en: {_display}")

    save_config(config)


# =============================================================================
# Section 2: Terminal Backend Configuration
# =============================================================================


def setup_terminal_backend(config: dict):
    """Configura el backend de ejecución de terminal."""
    import platform as _platform
    import shutil

    print_header("Backend de terminal")
    print_info("Elige dónde Hermes ejecuta comandos de shell y código.")
    print_info("Esto afecta a la ejecución de herramientas, acceso a archivos y aislamiento.")
    print()

    current_backend = config.get("terminal", {}).get("backend", "local")
    is_linux = _platform.system() == "Linux"

    # Construir las opciones de backend con descripciones
    terminal_choices = [
        "Local - ejecutar directamente en esta máquina (por defecto)",
        "Docker - contenedor aislado con recursos configurables",
        "Modal - sandbox en la nube sin servidor",
        "SSH - ejecutar en una máquina remota",
        "Daytona - entorno de desarrollo en la nube persistente",
    ]
    idx_to_backend = {0: "local", 1: "docker", 2: "modal", 3: "ssh", 4: "daytona"}
    backend_to_idx = {"local": 0, "docker": 1, "modal": 2, "ssh": 3, "daytona": 4}

    next_idx = 5
    if is_linux:
        terminal_choices.append("Singularity/Apptainer - contenedor apto para HPC")
        idx_to_backend[next_idx] = "singularity"
        backend_to_idx["singularity"] = next_idx
        next_idx += 1

    # Añadir opción de mantener el backend actual
    keep_current_idx = next_idx
    terminal_choices.append(f"Keep current ({current_backend})")
    idx_to_backend[keep_current_idx] = current_backend

    default_terminal = backend_to_idx.get(current_backend, 0)

    terminal_idx = prompt_choice(
        "Selecciona el backend de terminal:", terminal_choices, keep_current_idx
    )

    selected_backend = idx_to_backend.get(terminal_idx)

    if terminal_idx == keep_current_idx:
        print_info(f"Manteniendo el backend actual: {current_backend}")
        return

    config.setdefault("terminal", {})["backend"] = selected_backend

    if selected_backend == "local":
        print_success("Backend de terminal: Local")
        print_info("Los comandos se ejecutan directamente en esta máquina.")

        # CWD for messaging
        print()
        print_info("Directorio de trabajo para sesiones de mensajería:")
        print_info("  Cuando uses Hermes vía Telegram/Discord, aquí es donde")
        print_info(
            "  comienza el agente. El modo CLI siempre empieza en el directorio actual."
        )
        current_cwd = config.get("terminal", {}).get("cwd", "")
        cwd = prompt("  Directorio de trabajo de mensajería", current_cwd or str(Path.home()))
        if cwd:
            config["terminal"]["cwd"] = cwd

        # Soporte de sudo
        print()
        existing_sudo = get_env_value("SUDO_PASSWORD")
        if existing_sudo:
            print_info("Contraseña de sudo: configurada")
        else:
            if prompt_yes_no(
                "¿Habilitar soporte sudo? (almacena la contraseña para apt install, etc.)", False
            ):
                sudo_pass = prompt("  Contraseña de sudo", password=True)
                if sudo_pass:
                    save_env_value("SUDO_PASSWORD", sudo_pass)
                    print_success("Contraseña de sudo guardada")

    elif selected_backend == "docker":
        print_success("Backend de terminal: Docker")

        # Comprobar si Docker está disponible
        docker_bin = shutil.which("docker")
        if not docker_bin:
            print_warning("¡Docker no se encontró en el PATH!")
            print_info("Instala Docker: https://docs.docker.com/get-docker/")
        else:
            print_info(f"Docker encontrado: {docker_bin}")

        # Docker image
        current_image = config.get("terminal", {}).get(
            "docker_image", "python:3.11-slim"
        )
        image = prompt("  Imagen de Docker", current_image)
        config["terminal"]["docker_image"] = image
        save_env_value("TERMINAL_DOCKER_IMAGE", image)

        _prompt_container_resources(config)

    elif selected_backend == "singularity":
        print_success("Backend de terminal: Singularity/Apptainer")

        # Comprobar si singularity/apptainer está disponible
        sing_bin = shutil.which("apptainer") or shutil.which("singularity")
        if not sing_bin:
            print_warning("¡Singularity/Apptainer no se encontró en el PATH!")
            print_info(
                "Instala: https://apptainer.org/docs/admin/main/installation.html"
            )
        else:
            print_info(f"Encontrado: {sing_bin}")

        current_image = config.get("terminal", {}).get(
            "singularity_image", "docker://python:3.11-slim"
        )
        image = prompt("  Imagen del contenedor", current_image)
        config["terminal"]["singularity_image"] = image
        save_env_value("TERMINAL_SINGULARITY_IMAGE", image)

        _prompt_container_resources(config)

    elif selected_backend == "modal":
        print_success("Backend de terminal: Modal")
        print_info("Sandboxes en la nube sin servidor. Cada sesión tiene su propio contenedor.")
        print_info("Requiere una cuenta de Modal: https://modal.com")

        # Comprobar si swe-rex[modal] está instalado
        try:
            __import__("swe_rex")
        except ImportError:
            print_info("Instalando swe-rex[modal]...")
            import subprocess

            uv_bin = shutil.which("uv")
            if uv_bin:
                result = subprocess.run(
                    [
                        uv_bin,
                        "pip",
                        "install",
                        "--python",
                        sys.executable,
                        "swe-rex[modal]",
                    ],
                    capture_output=True,
                    text=True,
                )
            else:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "swe-rex[modal]"],
                    capture_output=True,
                    text=True,
                )
            if result.returncode == 0:
                print_success("swe-rex[modal] instalado")
            else:
                print_warning(
                    "La instalación falló — ejecútalo manualmente: pip install 'swe-rex[modal]'"
                )

        # Modal token
        print()
        print_info("Autenticación de Modal:")
        print_info("  Obtén tu token en: https://modal.com/settings")
        existing_token = get_env_value("MODAL_TOKEN_ID")
        if existing_token:
            print_info("  Token de Modal: ya configurado")
            if prompt_yes_no("  ¿Actualizar credenciales de Modal?", False):
                token_id = prompt("    Token ID de Modal", password=True)
                token_secret = prompt("    Token secreto de Modal", password=True)
                if token_id:
                    save_env_value("MODAL_TOKEN_ID", token_id)
                if token_secret:
                    save_env_value("MODAL_TOKEN_SECRET", token_secret)
        else:
            token_id = prompt("    Modal Token ID", password=True)
            token_secret = prompt("    Modal Token Secret", password=True)
            if token_id:
                save_env_value("MODAL_TOKEN_ID", token_id)
            if token_secret:
                save_env_value("MODAL_TOKEN_SECRET", token_secret)

        _prompt_container_resources(config)

    elif selected_backend == "daytona":
        print_success("Backend de terminal: Daytona")
        print_info("Entornos de desarrollo en la nube persistentes.")
        print_info("Cada sesión obtiene un sandbox dedicado con sistema de archivos persistente.")
        print_info("Regístrate en: https://daytona.io")

        # Comprobar si el SDK de daytona está instalado
        try:
            __import__("daytona")
        except ImportError:
            print_info("Instalando SDK de daytona...")
            import subprocess

            uv_bin = shutil.which("uv")
            if uv_bin:
                result = subprocess.run(
                    [uv_bin, "pip", "install", "--python", sys.executable, "daytona"],
                    capture_output=True,
                    text=True,
                )
            else:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "daytona"],
                    capture_output=True,
                    text=True,
                )
            if result.returncode == 0:
                print_success("SDK de daytona instalado")
            else:
                print_warning("La instalación falló — ejecútalo manualmente: pip install daytona")
                if result.stderr:
                    print_info(f"  Error: {result.stderr.strip().splitlines()[-1]}")

        # Daytona API key
        print()
        existing_key = get_env_value("DAYTONA_API_KEY")
        if existing_key:
            print_info("  API key de Daytona: ya configurada")
            if prompt_yes_no("  ¿Actualizar API key?", False):
                api_key = prompt("    API key de Daytona", password=True)
                if api_key:
                    save_env_value("DAYTONA_API_KEY", api_key)
                    print_success("    Updated")
        else:
            api_key = prompt("    API key de Daytona", password=True)
            if api_key:
                save_env_value("DAYTONA_API_KEY", api_key)
                print_success("    Configurada")

        # Daytona image
        current_image = config.get("terminal", {}).get(
            "daytona_image", "nikolaik/python-nodejs:python3.11-nodejs20"
        )
        image = prompt("  Imagen del sandbox", current_image)
        config["terminal"]["daytona_image"] = image
        save_env_value("TERMINAL_DAYTONA_IMAGE", image)

        _prompt_container_resources(config)

    elif selected_backend == "ssh":
        print_success("Backend de terminal: SSH")
        print_info("Ejecuta comandos en una máquina remota vía SSH.")

        # Host SSH
        current_host = get_env_value("TERMINAL_SSH_HOST") or ""
        host = prompt("  Host SSH (hostname o IP)", current_host)
        if host:
            save_env_value("TERMINAL_SSH_HOST", host)

        # Usuario SSH
        current_user = get_env_value("TERMINAL_SSH_USER") or ""
        user = prompt("  Usuario SSH", current_user or os.getenv("USER", ""))
        if user:
            save_env_value("TERMINAL_SSH_USER", user)

        # Puerto SSH
        current_port = get_env_value("TERMINAL_SSH_PORT") or "22"
        port = prompt("  Puerto SSH", current_port)
        if port and port != "22":
            save_env_value("TERMINAL_SSH_PORT", port)

        # Clave SSH
        current_key = get_env_value("TERMINAL_SSH_KEY") or ""
        default_key = str(Path.home() / ".ssh" / "id_rsa")
        ssh_key = prompt("  Ruta de la clave privada SSH", current_key or default_key)
        if ssh_key:
            save_env_value("TERMINAL_SSH_KEY", ssh_key)

        # Probar conexión
        if host and prompt_yes_no("  ¿Probar conexión SSH?", True):
            print_info("  Probando conexión...")
            import subprocess

            ssh_cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5"]
            if ssh_key:
                ssh_cmd.extend(["-i", ssh_key])
            if port and port != "22":
                ssh_cmd.extend(["-p", port])
            ssh_cmd.append(f"{user}@{host}" if user else host)
            ssh_cmd.append("echo ok")
            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print_success("  ¡Conexión SSH exitosa!")
            else:
                print_warning(f"  La conexión SSH falló: {result.stderr.strip()}")
                print_info("  Revisa tu clave SSH y la configuración del host.")

    # Sincronizar el backend de terminal a .env para que terminal_tool lo lea directamente.
    # config.yaml es la fuente de verdad, pero terminal_tool lee TERMINAL_ENV.
    save_env_value("TERMINAL_ENV", selected_backend)
    save_config(config)
    print()
    print_success(f"Backend de terminal establecido en: {selected_backend}")


# =============================================================================
# Section 3: Agent Settings
# =============================================================================


def setup_agent_settings(config: dict):
    """Configura el comportamiento del agente: iteraciones, progreso, compresión y reinicio de sesión."""

    # ── Iteraciones máximas ──
    print_header("Ajustes del agente")

    current_max = get_env_value("HERMES_MAX_ITERATIONS") or str(
        config.get("agent", {}).get("max_turns", 90)
    )
    print_info("Número máximo de iteraciones con herramientas por conversación.")
    print_info("Más alto = tareas más complejas, pero mayor coste en tokens.")
    print_info("Recomendado: 30-60 para la mayoría de tareas, 100+ para exploración abierta.")

    max_iter_str = prompt("Iteraciones máximas", current_max)
    try:
        max_iter = int(max_iter_str)
        if max_iter > 0:
            save_env_value("HERMES_MAX_ITERATIONS", str(max_iter))
            config.setdefault("agent", {})["max_turns"] = max_iter
            config.pop("max_turns", None)
            print_success(f"Iteraciones máximas establecidas en {max_iter}")
    except ValueError:
        print_warning("Número no válido, se mantiene el valor actual")

    # ── Visualización del progreso de herramientas ──
    print_info("")
    print_info("Visualización del progreso de herramientas")
    print_info("Controla cuánta actividad de herramientas se muestra (CLI y mensajería).")
    print_info("  off     — Silencioso, sólo la respuesta final")
    print_info("  new     — Muestra el nombre de la herramienta sólo cuando cambia (menos ruido)")
    print_info("  all     — Muestra cada llamada de herramienta con un breve resumen")
    print_info("  verbose — Args completos, resultados y logs de depuración")

    current_mode = config.get("display", {}).get("tool_progress", "all")
    mode = prompt("Modo de progreso de herramientas", current_mode)
    if mode.lower() in ("off", "new", "all", "verbose"):
        if "display" not in config:
            config["display"] = {}
        config["display"]["tool_progress"] = mode.lower()
        save_config(config)
        print_success(f"Progreso de herramientas establecido en: {mode.lower()}")
    else:
        print_warning(f"Modo desconocido '{mode}', se mantiene '{current_mode}'")

    # ── Compresión de contexto ──
    print_header("Compresión de contexto")
    print_info("Resume automáticamente mensajes antiguos cuando el contexto es muy largo.")
    print_info(
        "Umbral más alto = comprimir más tarde (usar más contexto). Más bajo = comprimir antes."
    )

    config.setdefault("compression", {})["enabled"] = True

    current_threshold = config.get("compression", {}).get("threshold", 0.85)
    threshold_str = prompt("Umbral de compresión (0.5-0.95)", str(current_threshold))
    try:
        threshold = float(threshold_str)
        if 0.5 <= threshold <= 0.95:
            config["compression"]["threshold"] = threshold
    except ValueError:
        pass

    print_success(
        f"Umbral de compresión de contexto establecido en {config['compression'].get('threshold', 0.85)}"
    )

    # ── Política de reinicio de sesión ──
    print_header("Política de reinicio de sesión")
    print_info(
        "Las sesiones de mensajería (Telegram, Discord, etc.) acumulan contexto con el tiempo."
    )
    print_info(
        "Cada mensaje se añade al historial de conversación, lo que implica mayor coste de API."
    )
    print_info("")
    print_info(
        "Para gestionarlo, las sesiones pueden reiniciarse automáticamente tras un periodo de inactividad"
    )
    print_info(
        "o a una hora fija cada día. Cuando hay un reinicio, el agente guarda primero lo importante"
    )
    print_info(
        "en su memoria persistente, pero se limpia el contexto de la conversación."
    )
    print_info("")
    print_info("También puedes reiniciar manualmente en cualquier momento escribiendo /reset en el chat.")
    print_info("")

    reset_choices = [
        "Inactividad + reinicio diario (recomendado - se reinicia lo que ocurra primero)",
        "Sólo inactividad (reinicio tras N minutos sin mensajes)",
        "Sólo diario (reinicio a una hora fija cada día)",
        "Nunca auto-reiniciar (el contexto vive hasta /reset o compresión)",
        "Mantener ajustes actuales",
    ]

    current_policy = config.get("session_reset", {})
    current_mode = current_policy.get("mode", "both")
    current_idle = current_policy.get("idle_minutes", 1440)
    current_hour = current_policy.get("at_hour", 4)

    default_reset = {"both": 0, "idle": 1, "daily": 2, "none": 3}.get(current_mode, 0)

    reset_idx = prompt_choice("Modo de reinicio de sesión:", reset_choices, default_reset)

    config.setdefault("session_reset", {})

    if reset_idx == 0:  # Both
        config["session_reset"]["mode"] = "both"
        idle_str = prompt("  Tiempo de inactividad (minutos)", str(current_idle))
        try:
            idle_val = int(idle_str)
            if idle_val > 0:
                config["session_reset"]["idle_minutes"] = idle_val
        except ValueError:
            pass
        hour_str = prompt("  Hora de reinicio diario (0-23, hora local)", str(current_hour))
        try:
            hour_val = int(hour_str)
            if 0 <= hour_val <= 23:
                config["session_reset"]["at_hour"] = hour_val
        except ValueError:
            pass
        print_success(
            f"Las sesiones se reinician tras {config['session_reset'].get('idle_minutes', 1440)} min de inactividad o diariamente a las {config['session_reset'].get('at_hour', 4)}:00"
        )
    elif reset_idx == 1:  # Idle only
        config["session_reset"]["mode"] = "idle"
        idle_str = prompt("  Tiempo de inactividad (minutos)", str(current_idle))
        try:
            idle_val = int(idle_str)
            if idle_val > 0:
                config["session_reset"]["idle_minutes"] = idle_val
        except ValueError:
            pass
        print_success(
            f"Las sesiones se reinician tras {config['session_reset'].get('idle_minutes', 1440)} min de inactividad"
        )
    elif reset_idx == 2:  # Daily only
        config["session_reset"]["mode"] = "daily"
        hour_str = prompt("  Hora de reinicio diario (0-23, hora local)", str(current_hour))
        try:
            hour_val = int(hour_str)
            if 0 <= hour_val <= 23:
                config["session_reset"]["at_hour"] = hour_val
        except ValueError:
            pass
        print_success(
            f"Las sesiones se reinician diariamente a las {config['session_reset'].get('at_hour', 4)}:00"
        )
    elif reset_idx == 3:  # None
        config["session_reset"]["mode"] = "none"
        print_info(
            "Las sesiones nunca se auto-reiniciarán. El contexto se gestiona sólo por compresión."
        )
        print_warning(
            "Las conversaciones largas aumentarán de coste. Usa /reset manualmente cuando lo necesites."
        )
    # else: keep current (idx == 4)

    save_config(config)


# =============================================================================
# Section 4: Messaging Platforms (Gateway)
# =============================================================================


def setup_gateway(config: dict):
    """Configura las integraciones con plataformas de mensajería."""
    print_header("Plataformas de mensajería")
    print_info("Conecta plataformas de mensajería para chatear con Hermes desde cualquier lugar.")
    print()

    # ── Telegram ──
    existing_telegram = get_env_value("TELEGRAM_BOT_TOKEN")
    if existing_telegram:
        print_info("Telegram: ya configurado")
        if prompt_yes_no("¿Reconfigurar Telegram?", False):
            existing_telegram = None

    if not existing_telegram and prompt_yes_no("¿Configurar bot de Telegram?", False):
        print_info("Crea un bot vía @BotFather en Telegram")
        token = prompt("Token del bot de Telegram", password=True)
        if token:
            save_env_value("TELEGRAM_BOT_TOKEN", token)
            print_success("Token de Telegram guardado")

            # Usuarios permitidos (seguridad)
            print()
            print_info("🔒 Seguridad: restringe quién puede usar tu bot")
            print_info("   Para encontrar tu ID de usuario de Telegram:")
            print_info("   1. Escribe a @userinfobot en Telegram")
            print_info("   2. Te responderá con tu ID numérico (ej.: 123456789)")
            print()
            allowed_users = prompt(
                "IDs de usuario permitidos (separados por coma, dejar vacío para acceso abierto)"
            )
            if allowed_users:
                save_env_value("TELEGRAM_ALLOWED_USERS", allowed_users.replace(" ", ""))
                print_success(
                    "Lista de permitidos de Telegram configurada: sólo los usuarios listados podrán usar el bot"
                )
            else:
                print_info(
                    "⚠️  Sin lista de permitidos: cualquiera que encuentre tu bot podrá usarlo."
                )

            # Canal principal (home channel) con guía mejorada
            print()
            print_info("📬 Home Channel: donde Hermes envía resultados de cron,")
            print_info("   mensajes entre plataformas y notificaciones.")
            print_info("   Para DMs en Telegram, es tu ID de usuario (el mismo de arriba).")

            first_user_id = allowed_users.split(",")[0].strip() if allowed_users else ""
            if first_user_id:
                if prompt_yes_no(
                    f"¿Usar tu ID de usuario ({first_user_id}) como home channel?", True
                ):
                    save_env_value("TELEGRAM_HOME_CHANNEL", first_user_id)
                    print_success(f"Home channel de Telegram establecido en {first_user_id}")
                else:
                    home_channel = prompt(
                        "ID de home channel (o dejar vacío para establecerlo luego con /set-home en Telegram)"
                    )
                    if home_channel:
                        save_env_value("TELEGRAM_HOME_CHANNEL", home_channel)
            else:
                print_info(
                    "   También puedes establecerlo más tarde escribiendo /set-home en tu chat de Telegram."
                )
                home_channel = prompt("ID de home channel (dejar vacío para hacerlo después)")
                if home_channel:
                    save_env_value("TELEGRAM_HOME_CHANNEL", home_channel)

    # Check/update existing Telegram allowlist
    elif existing_telegram:
        existing_allowlist = get_env_value("TELEGRAM_ALLOWED_USERS")
        if not existing_allowlist:
            print_info("⚠️  Telegram no tiene lista de permitidos: ¡cualquiera puede usar tu bot!")
            if prompt_yes_no("¿Añadir usuarios permitidos ahora?", True):
                print_info("   Para encontrar tu ID de usuario de Telegram: escribe a @userinfobot")
                allowed_users = prompt("IDs de usuario permitidos (separados por coma)")
                if allowed_users:
                    save_env_value(
                        "TELEGRAM_ALLOWED_USERS", allowed_users.replace(" ", "")
                    )
                    print_success("Lista de permitidos de Telegram configurada")

    # ── Discord ──
    existing_discord = get_env_value("DISCORD_BOT_TOKEN")
    if existing_discord:
        print_info("Discord: ya configurado")
        if prompt_yes_no("¿Reconfigurar Discord?", False):
            existing_discord = None

    if not existing_discord and prompt_yes_no("¿Configurar bot de Discord?", False):
        print_info("Crea un bot en https://discord.com/developers/applications")
        token = prompt("Token del bot de Discord", password=True)
        if token:
            save_env_value("DISCORD_BOT_TOKEN", token)
            print_success("Token de Discord guardado")

            # Usuarios permitidos (seguridad)
            print()
            print_info("🔒 Seguridad: restringe quién puede usar tu bot")
            print_info("   Para encontrar tu ID de usuario de Discord:")
            print_info("   1. Habilita el Modo desarrollador en ajustes de Discord")
            print_info("   2. Clic derecho sobre tu nombre → Copy ID")
            print()
            print_info(
                "   También puedes usar nombres de usuario de Discord (se resuelven al iniciar el gateway)."
            )
            print()
            allowed_users = prompt(
                "IDs de usuario o nombres de usuario permitidos (separados por coma, vacío para acceso abierto)"
            )
            if allowed_users:
                save_env_value("DISCORD_ALLOWED_USERS", allowed_users.replace(" ", ""))
                print_success("Lista de permitidos de Discord configurada")
            else:
                print_info(
                    "⚠️  Sin lista de permitidos: cualquiera en los servidores con tu bot puede usarlo."
                )

            # Home channel con mejor guía
            print()
            print_info("📬 Home Channel: donde Hermes envía resultados de cron,")
            print_info("   mensajes entre plataformas y notificaciones.")
            print_info(
                "   Para obtener un ID de canal: clic derecho sobre el canal → Copy Channel ID"
            )
            print_info("   (requires Developer Mode in Discord settings)")
            print_info(
                "   También puedes establecerlo después escribiendo /set-home en un canal de Discord."
            )
            home_channel = prompt(
                "ID de home channel (vacío para establecerlo después con /set-home)"
            )
            if home_channel:
                save_env_value("DISCORD_HOME_CHANNEL", home_channel)

    # Check/update existing Discord allowlist
    elif existing_discord:
        existing_allowlist = get_env_value("DISCORD_ALLOWED_USERS")
        if not existing_allowlist:
            print_info("⚠️  Discord no tiene lista de permitidos: ¡cualquiera puede usar tu bot!")
            if prompt_yes_no("¿Añadir usuarios permitidos ahora?", True):
                print_info(
                    "   Para encontrar tu ID de Discord: habilita Modo desarrollador, clic derecho en tu nombre → Copy ID"
                )
                allowed_users = prompt("IDs de usuario permitidos (separados por coma)")
                if allowed_users:
                    save_env_value(
                        "DISCORD_ALLOWED_USERS", allowed_users.replace(" ", "")
                    )
                    print_success("Lista de permitidos de Discord configurada")

    # ── Slack ──
    existing_slack = get_env_value("SLACK_BOT_TOKEN")
    if existing_slack:
        print_info("Slack: ya configurado")
        if prompt_yes_no("¿Reconfigurar Slack?", False):
            existing_slack = None

    if not existing_slack and prompt_yes_no("¿Configurar bot de Slack?", False):
        print_info("Pasos para crear una app de Slack:")
        print_info(
            "   1. Ve a https://api.slack.com/apps → Create New App (from scratch)"
        )
        print_info("   2. Habilita Socket Mode: Settings → Socket Mode → Enable")
        print_info("      • Crea un App-Level Token con el scope 'connections:write'")
        print_info("   3. Añade Bot Token Scopes: Features → OAuth & Permissions")
        print_info("      Scopes requeridos: chat:write, app_mentions:read,")
        print_info("      channels:history, channels:read, groups:history,")
        print_info("      im:history, im:read, im:write, users:read, files:write")
        print_info("   4. Suscríbete a eventos: Features → Event Subscriptions → Enable")
        print_info("      Eventos requeridos: message.im, message.channels,")
        print_info("      message.groups, app_mention")
        print_warning("   ⚠ Sin los eventos message.channels/message.groups,")
        print_warning("     el bot SOLO funcionará en DMs, no en canales.")
        print_info("   5. Instala en el Workspace: Settings → Install App")
        print_info(
            "   6. Después de instalar, invita el bot a canales: /invite @YourBot"
        )
        print()
        print_info(
            "   Guía completa: https://hermes-agent.ai/docs/user-guide/messaging/slack"
        )
        print()
        bot_token = prompt("Slack Bot Token (xoxb-...)", password=True)
        if bot_token:
            save_env_value("SLACK_BOT_TOKEN", bot_token)
            app_token = prompt("Slack App Token (xapp-...)", password=True)
            if app_token:
                save_env_value("SLACK_APP_TOKEN", app_token)
            print_success("Tokens de Slack guardados")

            print()
            print_info("🔒 Seguridad: restringe quién puede usar tu bot")
            print_info(
                "   Para encontrar un Member ID: clic en el nombre de usuario → View full profile → ⋮ → Copy member ID"
            )
            print()
            allowed_users = prompt(
                "IDs de usuario permitidos (separados por coma, vacío para acceso abierto)"
            )
            if allowed_users:
                save_env_value("SLACK_ALLOWED_USERS", allowed_users.replace(" ", ""))
                print_success("Lista de permitidos de Slack configurada")
            else:
                print_info(
                    "⚠️  Sin lista de permitidos: cualquiera en tu workspace puede usar el bot."
                )

    # ── WhatsApp ──
    existing_whatsapp = get_env_value("WHATSAPP_ENABLED")
    if not existing_whatsapp and prompt_yes_no("¿Configurar WhatsApp?", False):
        print_info("WhatsApp se conecta mediante un bridge integrado (Baileys).")
        print_info("Requiere Node.js. Ejecuta 'hermes whatsapp' para una configuración guiada.")
        print()
        if prompt_yes_no("¿Habilitar WhatsApp ahora?", True):
            save_env_value("WHATSAPP_ENABLED", "true")
            print_success("WhatsApp habilitado")
            print_info("Ejecuta 'hermes whatsapp' para elegir tu modo (número de bot separado")
            print_info("o chat personal contigo mismo) y enlazar mediante código QR.")

    # ── Gateway Service Setup ──
    any_messaging = (
        get_env_value("TELEGRAM_BOT_TOKEN")
        or get_env_value("DISCORD_BOT_TOKEN")
        or get_env_value("SLACK_BOT_TOKEN")
        or get_env_value("WHATSAPP_ENABLED")
    )
    if any_messaging:
        print()
        print_info("━" * 50)
        print_success("¡Plataformas de mensajería configuradas!")

        # Comprobar si falta algún home channel
        missing_home = []
        if get_env_value("TELEGRAM_BOT_TOKEN") and not get_env_value(
            "TELEGRAM_HOME_CHANNEL"
        ):
            missing_home.append("Telegram")
        if get_env_value("DISCORD_BOT_TOKEN") and not get_env_value(
            "DISCORD_HOME_CHANNEL"
        ):
            missing_home.append("Discord")
        if get_env_value("SLACK_BOT_TOKEN") and not get_env_value("SLACK_HOME_CHANNEL"):
            missing_home.append("Slack")

        if missing_home:
            print()
            print_warning(f"No hay home channel definido para: {', '.join(missing_home)}")
            print_info("   Sin un home channel, los cron jobs y mensajes entre plataformas")
            print_info("   no se podrán entregar a esas plataformas.")
            print_info("   Establece uno después con /set-home en tu chat, o con:")
            for plat in missing_home:
                print_info(
                    f"     hermes config set {plat.upper()}_HOME_CHANNEL <channel_id>"
                )

        # Ofrecer instalar el gateway como servicio del sistema
        import platform as _platform

        _is_linux = _platform.system() == "Linux"
        _is_macos = _platform.system() == "Darwin"

        from hermes_cli.gateway import (
            _is_service_installed,
            _is_service_running,
            systemd_install,
            systemd_start,
            systemd_restart,
            launchd_install,
            launchd_start,
            launchd_restart,
        )

        service_installed = _is_service_installed()
        service_running = _is_service_running()

        print()
        if service_running:
            if prompt_yes_no("  ¿Reiniciar el gateway para aplicar los cambios?", True):
                try:
                    if _is_linux:
                        systemd_restart()
                    elif _is_macos:
                        launchd_restart()
                except Exception as e:
                    print_error(f"  El reinicio falló: {e}")
        elif service_installed:
            if prompt_yes_no("  ¿Iniciar el servicio del gateway?", True):
                try:
                    if _is_linux:
                        systemd_start()
                    elif _is_macos:
                        launchd_start()
                except Exception as e:
                    print_error(f"  El inicio falló: {e}")
        elif _is_linux or _is_macos:
            svc_name = "systemd" if _is_linux else "launchd"
            if prompt_yes_no(
                f"  ¿Instalar el gateway como servicio {svc_name}? (se ejecuta en segundo plano y arranca al inicio)",
                True,
            ):
                try:
                    if _is_linux:
                        systemd_install(force=False)
                    else:
                        launchd_install(force=False)
                    print()
                    if prompt_yes_no("  ¿Iniciar el servicio ahora?", True):
                        try:
                            if _is_linux:
                                systemd_start()
                            elif _is_macos:
                                launchd_start()
                        except Exception as e:
                            print_error(f"  El inicio falló: {e}")
                except Exception as e:
                    print_error(f"  La instalación falló: {e}")
                    print_info("  Puedes intentarlo manualmente: hermes gateway install")
            else:
                print_info("  Puedes instalarlo más tarde: hermes gateway install")
                print_info("  O ejecutarlo en primer plano:  hermes gateway")
        else:
            print_info("Inicia el gateway para poner tus bots en línea:")
            print_info("   hermes gateway              # Ejecutar en primer plano")

        print_info("━" * 50)


# =============================================================================
# Section 5: Tool Configuration (delegates to unified tools_config.py)
# =============================================================================


def setup_tools(config: dict, first_install: bool = False):
    """Configura herramientas — delega en tools_command() unificado en tools_config.py.

    Tanto `hermes setup tools` como `hermes tools` usan el mismo flujo:
    selección de plataforma → activación/desactivación de toolsets → configuración de proveedor/API key.

    Args:
        first_install: cuando es True, usa un flujo simplificado de primera instalación
            (sin menú de plataforma, pide todas las API keys no configuradas).
    """
    from hermes_cli.tools_config import tools_command

    tools_command(first_install=first_install, config=config)


# =============================================================================
# OpenClaw Migration
# =============================================================================


_OPENCLAW_SCRIPT = (
    PROJECT_ROOT
    / "optional-skills"
    / "migration"
    / "openclaw-migration"
    / "scripts"
    / "openclaw_to_hermes.py"
)


def _offer_openclaw_migration(hermes_home: Path) -> bool:
    """Detecta ~/.openclaw y ofrece migrar durante la configuración inicial.

    Devuelve True si la migración se ejecutó correctamente, False en caso contrario.
    """
    openclaw_dir = Path.home() / ".openclaw"
    if not openclaw_dir.is_dir():
        return False

    if not _OPENCLAW_SCRIPT.exists():
        return False

    print()
    print_header("Instalación de OpenClaw detectada")
    print_info(f"Se encontraron datos de OpenClaw en {openclaw_dir}")
    print_info("Hermes puede importar tus ajustes, memorias, skills y API keys.")
    print()

    if not prompt_yes_no("¿Quieres importar desde OpenClaw?", default=True):
        print_info(
            "Omitiendo migración. Puedes ejecutarla más tarde mediante la skill openclaw-migration."
        )
        return False

    # Asegurarse de que config.yaml exista antes de que la migración intente leerlo
    config_path = get_config_path()
    if not config_path.exists():
        save_config(load_config())

    # Cargar dinámicamente el script de migración
    try:
        spec = importlib.util.spec_from_file_location(
            "openclaw_to_hermes", _OPENCLAW_SCRIPT
        )
        if spec is None or spec.loader is None:
            print_warning("Could not load migration script.")
            return False

        mod = importlib.util.module_from_spec(spec)
        # Registrar en sys.modules para que @dataclass pueda resolver el módulo
        # (Python 3.11+ lo requiere para módulos cargados dinámicamente)
        import sys as _sys
        _sys.modules[spec.name] = mod
        try:
            spec.loader.exec_module(mod)
        except Exception:
            _sys.modules.pop(spec.name, None)
            raise

        # Run migration with the "full" preset, execute mode, no overwrite
        selected = mod.resolve_selected_options(None, None, preset="full")
        migrator = mod.Migrator(
            source_root=openclaw_dir.resolve(),
            target_root=hermes_home.resolve(),
            execute=True,
            workspace_target=None,
            overwrite=False,
            migrate_secrets=True,
            output_dir=None,
            selected_options=selected,
            preset_name="full",
        )
        report = migrator.migrate()
    except Exception as e:
        print_warning(f"La migración falló: {e}")
        logger.debug("Error en la migración de OpenClaw", exc_info=True)
        return False

    # Imprimir resumen
    summary = report.get("summary", {})
    migrated = summary.get("migrated", 0)
    skipped = summary.get("skipped", 0)
    conflicts = summary.get("conflict", 0)
    errors = summary.get("error", 0)

    print()
    if migrated:
        print_success(f"Se importaron {migrated} elemento(s) desde OpenClaw.")
    if conflicts:
        print_info(f"Se omitieron {conflicts} elemento(s) que ya existen en Hermes.")
    if skipped:
        print_info(f"Se omitieron {skipped} elemento(s) (no encontrados o sin cambios).")
    if errors:
        print_warning(f"{errors} elemento(s) tuvieron errores — revisa el informe de migración.")

    output_dir = report.get("output_dir")
    if output_dir:
        print_info(f"Informe completo guardado en: {output_dir}")

    print_success("¡Migración completa! Continuando con la configuración...")
    return True


# =============================================================================
# Main Wizard Orchestrator
# =============================================================================

SETUP_SECTIONS = [
    ("model", "Modelo y proveedor", setup_model_provider),
    ("terminal", "Backend de terminal", setup_terminal_backend),
    ("gateway", "Plataformas de mensajería (Gateway)", setup_gateway),
    ("tools", "Herramientas", setup_tools),
    ("agent", "Ajustes del agente", setup_agent_settings),
]


def run_setup_wizard(args):
    """Ejecuta el asistente de configuración interactivo.

    Soporta configuración completa, rápida o por secciones:
        hermes setup           — completa o rápida (auto-detectada)
        hermes setup model     — sólo modelo/proveedor
        hermes setup terminal  — sólo backend de terminal
        hermes setup gateway   — sólo plataformas de mensajería
        hermes setup tools     — sólo configuración de herramientas
        hermes setup agent     — sólo ajustes del agente
    """
    ensure_hermes_home()

    config = load_config()
    hermes_home = get_hermes_home()

    # Comprobar si se pidió una sección específica
    section = getattr(args, "section", None)
    if section:
        for key, label, func in SETUP_SECTIONS:
            if key == section:
                print()
                print(
                    color(
                        "┌─────────────────────────────────────────────────────────┐",
                        Colors.MAGENTA,
                    )
                )
                print(color(f"│     ⚕ Hermes Setup — {label:<34s} │", Colors.MAGENTA))
                print(
                    color(
                        "└─────────────────────────────────────────────────────────┘",
                        Colors.MAGENTA,
                    )
                )
                func(config)
                save_config(config)
                print()
                print_success(f"Configuración de {label} completada.")
                return

        print_error(f"Sección de configuración desconocida: {section}")
        print_info(f"Secciones disponibles: {', '.join(k for k, _, _ in SETUP_SECTIONS)}")
        return

    # Comprobar si es una instalación existente con proveedor configurado
    from hermes_cli.auth import get_active_provider

    active_provider = get_active_provider()
    is_existing = (
        bool(get_env_value("OPENROUTER_API_KEY"))
        or bool(get_env_value("OPENAI_BASE_URL"))
        or active_provider is not None
    )

    print()
    print(
        color(
            "┌─────────────────────────────────────────────────────────┐",
            Colors.MAGENTA,
        )
    )
    print(
        color(
            "│     ⚕ Asistente de configuración de Hermes Agent      │", Colors.MAGENTA
        )
    )
    print(
        color(
            "├─────────────────────────────────────────────────────────┤",
            Colors.MAGENTA,
        )
    )
    print(
        color(
            "│  Vamos a configurar tu instalación de Hermes Agent.   │", Colors.MAGENTA
        )
    )
    print(
        color(
            "│  Pulsa Ctrl+C en cualquier momento para salir.        │", Colors.MAGENTA
        )
    )
    print(
        color(
            "└─────────────────────────────────────────────────────────┘",
            Colors.MAGENTA,
        )
    )

    if is_existing:
        # ── Menú para usuario recurrente ──
        print()
        print_header("¡Bienvenido de nuevo!")
        print_success("Ya tienes Hermes configurado.")
        print()

        menu_choices = [
            "Configuración rápida - sólo elementos faltantes",
            "Configuración completa - reconfigurar todo",
            "---",
            "Modelo y proveedor",
            "Backend de terminal",
            "Plataformas de mensajería (Gateway)",
            "Herramientas",
            "Ajustes del agente",
            "---",
            "Salir",
        ]

        # Índices separadores (no seleccionables, prompt_choice no los filtra,
        # así que los manejamos abajo)
        choice = prompt_choice("¿Qué te gustaría hacer?", menu_choices, 0)

        if choice == 0:
            # Configuración rápida
            _run_quick_setup(config, hermes_home)
            return
        elif choice == 1:
            # Configuración completa — continúa para ejecutar todas las secciones
            pass
        elif choice in (2, 8):
            # Separador — tratar como salida
            print_info("Saliendo. Ejecuta 'hermes setup' de nuevo cuando quieras.")
            return
        elif choice == 9:
            print_info("Saliendo. Ejecuta 'hermes setup' de nuevo cuando quieras.")
            return
        elif 3 <= choice <= 7:
            # Sección individual
            section_idx = choice - 3
            _, label, func = SETUP_SECTIONS[section_idx]
            func(config)
            save_config(config)
            _print_setup_summary(config, hermes_home)
            return
    else:
        # ── Configuración por primera vez ──
        print()
        print_info("Te guiaremos por:")
        print_info("  1. Modelo y proveedor — elige tu proveedor de IA y modelo")
        print_info("  2. Backend de terminal — dónde ejecuta comandos tu agente")
        print_info("  3. Plataformas de mensajería — conecta Telegram, Discord, etc.")
        print_info("  4. Herramientas — configura TTS, búsqueda web, generación de imágenes, etc.")
        print_info("  5. Ajustes del agente — iteraciones, compresión, reinicio de sesión")
        print()
        print_info("Pulsa Enter para empezar, o Ctrl+C para salir.")
        try:
            input(color("  Pulsa Enter para comenzar... ", Colors.YELLOW))
        except (KeyboardInterrupt, EOFError):
            print()
            return

        # Ofrecer migración desde OpenClaw antes de comenzar la configuración
        if _offer_openclaw_migration(hermes_home):
            # Recargar config en caso de que la migración la haya modificado
            config = load_config()

    # ── Configuración completa — ejecutar todas las secciones ──
    print_header("Ubicación de la configuración")
    print_info(f"Archivo de config:  {get_config_path()}")
    print_info(f"Archivo de secretos: {get_env_path()}")
    print_info(f"Carpeta de datos:  {hermes_home}")
    print_info(f"Directorio de instalación:  {PROJECT_ROOT}")
    print()
    print_info("Puedes editar estos archivos directamente o usar 'hermes config edit'")

    # Sección 1: Modelo y proveedor
    setup_model_provider(config)

    # Sección 2: Backend de terminal
    setup_terminal_backend(config)

    # Sección 3: Ajustes del agente
    setup_agent_settings(config)

    # Sección 4: Plataformas de mensajería
    setup_gateway(config)

    # Sección 5: Herramientas
    setup_tools(config, first_install=not is_existing)

    # Guardar y mostrar resumen
    save_config(config)
    _print_setup_summary(config, hermes_home)


def _run_quick_setup(config: dict, hermes_home):
    """Configuración rápida — sólo configura elementos que faltan."""
    from hermes_cli.config import (
        get_missing_env_vars,
        get_missing_config_fields,
        check_config_version,
        migrate_config,
    )

    print()
    print_header("Configuración rápida — sólo elementos faltantes")

    # Comprobar qué falta
    missing_required = [
        v for v in get_missing_env_vars(required_only=False) if v.get("is_required")
    ]
    missing_optional = [
        v for v in get_missing_env_vars(required_only=False) if not v.get("is_required")
    ]
    missing_config = get_missing_config_fields()
    current_ver, latest_ver = check_config_version()

    has_anything_missing = (
        missing_required
        or missing_optional
        or missing_config
        or current_ver < latest_ver
    )

    if not has_anything_missing:
        print_success("¡Todo está configurado! Nada que hacer.")
        print()
        print_info("Ejecuta 'hermes setup' y elige 'Configuración completa' para reconfigurar,")
        print_info("o selecciona una sección específica desde el menú.")
        return

    # Gestionar variables de entorno requeridas que faltan
    if missing_required:
        print()
        print_info(f"Faltan {len(missing_required)} ajuste(s) requerido(s):")
        for var in missing_required:
            print(f"     • {var['name']}")
        print()

        for var in missing_required:
            print()
            print(color(f"  {var['name']}", Colors.CYAN))
            print_info(f"  {var.get('description', '')}")
            if var.get("url"):
                print_info(f"  Obtén la key en: {var['url']}")

            if var.get("password"):
                value = prompt(f"  {var.get('prompt', var['name'])}", password=True)
            else:
                value = prompt(f"  {var.get('prompt', var['name'])}")

            if value:
                save_env_value(var["name"], value)
                print_success(f"  Guardado {var['name']}")
            else:
                print_warning(f"  Omitido {var['name']}")

    # Dividir las vars opcionales que faltan por categoría
    missing_tools = [v for v in missing_optional if v.get("category") == "tool"]
    missing_messaging = [
        v
        for v in missing_optional
        if v.get("category") == "messaging" and not v.get("advanced")
    ]

    # ── API keys de herramientas (checklist) ──
    if missing_tools:
        print()
        print_header("API keys de herramientas")

        checklist_labels = []
        for var in missing_tools:
            tools = var.get("tools", [])
            tools_str = f" → {', '.join(tools[:2])}" if tools else ""
            checklist_labels.append(f"{var.get('description', var['name'])}{tools_str}")

        selected_indices = prompt_checklist(
            "¿Qué herramientas te gustaría configurar?",
            checklist_labels,
        )

        for idx in selected_indices:
            var = missing_tools[idx]
            _prompt_api_key(var)

    # ── Plataformas de mensajería (checklist y luego prompts para las seleccionadas) ──
    if missing_messaging:
        print()
        print_header("Plataformas de mensajería")
        print_info("Conecta Hermes a apps de mensajería para chatear desde cualquier lugar.")
        print_info("Puedes configurarlas más tarde con 'hermes setup gateway'.")

        # Agrupar por plataforma (preservando el orden)
        platform_order = []
        platforms = {}
        for var in missing_messaging:
            name = var["name"]
            if "TELEGRAM" in name:
                plat = "Telegram"
            elif "DISCORD" in name:
                plat = "Discord"
            elif "SLACK" in name:
                plat = "Slack"
            else:
                continue
            if plat not in platforms:
                platform_order.append(plat)
            platforms.setdefault(plat, []).append(var)

        platform_labels = [
            {
                "Telegram": "📱 Telegram",
                "Discord": "💬 Discord",
                "Slack": "💼 Slack",
            }.get(p, p)
            for p in platform_order
        ]

        selected_indices = prompt_checklist(
            "¿Qué plataformas te gustaría configurar?",
            platform_labels,
        )

        for idx in selected_indices:
            plat = platform_order[idx]
            vars_list = platforms[plat]
            emoji = {"Telegram": "📱", "Discord": "💬", "Slack": "💼"}.get(plat, "")
            print()
            print(color(f"  ─── {emoji} {plat} ───", Colors.CYAN))
            print()
            for var in vars_list:
                print_info(f"  {var.get('description', '')}")
                if var.get("url"):
                    print_info(f"  {var['url']}")
                if var.get("password"):
                    value = prompt(f"  {var.get('prompt', var['name'])}", password=True)
                else:
                    value = prompt(f"  {var.get('prompt', var['name'])}")
                if value:
                    save_env_value(var["name"], value)
                    print_success("  ✓ Guardado")
                else:
                    print_warning("  Omitido")
                print()

    # Gestionar campos de configuración que faltan
    if missing_config:
        print()
        print_info(
            f"Añadiendo {len(missing_config)} nueva(s) opción(es) de config con valores por defecto..."
        )
        for field in missing_config:
            print_success(f"  Añadido {field['key']} = {field['default']}")

        # Update config version
        config["_config_version"] = latest_ver
        save_config(config)

    # Ir al resumen
    _print_setup_summary(config, hermes_home)
