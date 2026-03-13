"""Configuración unificada de herramientas para Hermes Agent.

Tanto `hermes tools` como `hermes setup tools` entran en este módulo.
Flujo: seleccionar una plataforma → activar/desactivar *toolsets* → para
las herramientas recién habilitadas que necesitan API keys, ejecutar una
configuración consciente del proveedor.

Guarda la configuración de herramientas por plataforma en ~/.hermes/config.yaml
bajo la clave ``platform_toolsets``.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

import os

from hermes_cli.config import (
    load_config, save_config, get_env_value, save_env_value,
    get_hermes_home,
)
from hermes_cli.colors import Colors, color

PROJECT_ROOT = Path(__file__).parent.parent.resolve()


# ─── Helpers de UI (compartidos con setup.py) ────────────────────────────────

def _print_info(text: str):
    print(color(f"  {text}", Colors.DIM))


def _print_success(text: str):
    print(color(f"✓ {text}", Colors.GREEN))


def _print_warning(text: str):
    print(color(f"⚠ {text}", Colors.YELLOW))


def _print_error(text: str):
    print(color(f"✗ {text}", Colors.RED))

def _prompt(question: str, default: str = None, password: bool = False) -> str:
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
        return default or ""

def _prompt_yes_no(question: str, default: bool = True) -> bool:
    default_str = "Y/n" if default else "y/N"
    while True:
        try:
            value = input(color(f"{question} [{default_str}]: ", Colors.YELLOW)).strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            return default
        if not value:
            return default
        if value in ('y', 'yes'):
            return True
        if value in ('n', 'no'):
            return False


# ─── Registro de toolsets ────────────────────────────────────────────────────

# Toolsets que se muestran en el configurador, agrupados para visualización.
# Cada entrada: (toolset_name, etiqueta, descripción)
# Estos valores se corresponden con claves en el dict TOOLSETS de toolsets.py.
CONFIGURABLE_TOOLSETS = [
    ("web",             "🔍 Búsqueda web y scraping",   "web_search, web_extract"),
    ("browser",         "🌐 Automatización de navegador", "navigate, click, type, scroll"),
    ("terminal",        "💻 Terminal y procesos",       "terminal, process"),
    ("file",            "📁 Operaciones con archivos",  "read, write, patch, search"),
    ("code_execution",  "⚡ Ejecución de código",       "execute_code"),
    ("vision",          "👁️  Visión / análisis de imagen", "vision_analyze"),
    ("image_gen",       "🎨 Generación de imágenes",    "image_generate"),
    ("moa",             "🧠 Mezcla de agentes (MoA)",   "mixture_of_agents"),
    ("tts",             "🔊 Texto a voz",               "text_to_speech"),
    ("skills",          "📚 Skills",                    "list, view, manage"),
    ("todo",            "📋 Planificación de tareas",   "todo"),
    ("memory",          "💾 Memoria",                   "persistent memory across sessions"),
    ("session_search",  "🔎 Búsqueda en sesiones",      "search past conversations"),
    ("clarify",         "❓ Preguntas de aclaración",   "clarify"),
    ("delegation",      "👥 Delegación de tareas",      "delegate_task"),
    ("cronjob",         "⏰ Tareas programadas (cron)", "schedule, list, remove"),
    ("rl",              "🧪 Entrenamiento RL",          "Tinker-Atropos training tools"),
    ("homeassistant",   "🏠 Home Assistant",           "smart home device control"),
]

# Toolsets que están APAGADOS por defecto en nuevas instalaciones.
# Siguen estando en _HERMES_CORE_TOOLS (disponibles en tiempo de ejecución
# si se habilitan), pero el checklist de setup no los preselecciona para
# usuarios que instalan por primera vez.
_DEFAULT_OFF_TOOLSETS = {"moa", "homeassistant", "rl"}

# Configuración de visualización de plataformas
PLATFORMS = {
    "cli":      {"label": "🖥️  CLI",       "default_toolset": "hermes-cli"},
    "telegram": {"label": "📱 Telegram",   "default_toolset": "hermes-telegram"},
    "discord":  {"label": "💬 Discord",    "default_toolset": "hermes-discord"},
    "slack":    {"label": "💼 Slack",      "default_toolset": "hermes-slack"},
    "whatsapp": {"label": "📱 WhatsApp",   "default_toolset": "hermes-whatsapp"},
    "signal":   {"label": "📡 Signal",     "default_toolset": "hermes-signal"},
    "email":    {"label": "📧 Email",      "default_toolset": "hermes-email"},
}


# ─── Categorías de herramientas (configuración por proveedor) ────────────────
# Asocia claves de toolset con sus opciones de proveedor. Cuando un toolset se
# habilita por primera vez, usamos esto para mostrar la selección de proveedor
# y pedir las API keys correctas. Los toolsets que no están en este mapa o bien
# no necesitan configuración o usan el flujo simple de *fallback*.

TOOL_CATEGORIES = {
    "tts": {
        "name": "Texto a voz",
        "icon": "🔊",
        "providers": [
            {
                "name": "Microsoft Edge TTS",
                "tag": "Gratis - no necesita API key",
                "env_vars": [],
                "tts_provider": "edge",
            },
            {
                "name": "OpenAI TTS",
                "tag": "Premium - voces de alta calidad",
                "env_vars": [
                    {"key": "VOICE_TOOLS_OPENAI_KEY", "prompt": "API key de OpenAI", "url": "https://platform.openai.com/api-keys"},
                ],
                "tts_provider": "openai",
            },
            {
                "name": "ElevenLabs",
                "tag": "Premium - voces muy naturales",
                "env_vars": [
                    {"key": "ELEVENLABS_API_KEY", "prompt": "API key de ElevenLabs", "url": "https://elevenlabs.io/app/settings/api-keys"},
                ],
                "tts_provider": "elevenlabs",
            },
        ],
    },
    "web": {
        "name": "Búsqueda web y extracción",
        "setup_title": "Selecciona proveedor de búsqueda",
        "setup_note": "También se incluye una skill gratuita de búsqueda DuckDuckGo — omite esto si no necesitas Firecrawl.",
        "icon": "🔍",
        "providers": [
            {
                "name": "Firecrawl Cloud",
                "tag": "Recomendado - servicio alojado",
                "env_vars": [
                    {"key": "FIRECRAWL_API_KEY", "prompt": "API key de Firecrawl", "url": "https://firecrawl.dev"},
                ],
            },
            {
                "name": "Firecrawl Self-Hosted",
                "tag": "Gratis - ejecuta tu propia instancia",
                "env_vars": [
                    {"key": "FIRECRAWL_API_URL", "prompt": "URL de tu instancia Firecrawl (ej.: http://localhost:3002)"},
                ],
            },
        ],
    },
    "image_gen": {
        "name": "Generación de imágenes",
        "icon": "🎨",
        "providers": [
            {
                "name": "FAL.ai",
                "tag": "FLUX 2 Pro con auto-escalado",
                "env_vars": [
                    {"key": "FAL_KEY", "prompt": "API key de FAL", "url": "https://fal.ai/dashboard/keys"},
                ],
            },
        ],
    },
    "browser": {
        "name": "Automatización de navegador",
        "icon": "🌐",
        "providers": [
            {
                "name": "Navegador local",
                "tag": "Chromium *headless* gratis (no necesita API key)",
                "env_vars": [],
                "post_setup": "browserbase",  # Same npm install for agent-browser
            },
            {
                "name": "Browserbase",
                "tag": "Navegador en la nube con *stealth* y proxies",
                "env_vars": [
                    {"key": "BROWSERBASE_API_KEY", "prompt": "API key de Browserbase", "url": "https://browserbase.com"},
                    {"key": "BROWSERBASE_PROJECT_ID", "prompt": "ID de proyecto de Browserbase"},
                ],
                "post_setup": "browserbase",
            },
        ],
    },
    "homeassistant": {
        "name": "Hogar inteligente",
        "icon": "🏠",
        "providers": [
            {
                "name": "Home Assistant",
                "tag": "Integración vía REST API",
                "env_vars": [
                    {"key": "HASS_TOKEN", "prompt": "Token de acceso de larga duración de Home Assistant"},
                    {"key": "HASS_URL", "prompt": "URL de Home Assistant", "default": "http://homeassistant.local:8123"},
                ],
            },
        ],
    },
    "rl": {
        "name": "Entrenamiento RL",
        "icon": "🧪",
        "requires_python": (3, 11),
        "providers": [
            {
                "name": "Tinker / Atropos",
                "tag": "Plataforma de entrenamiento RL",
                "env_vars": [
                    {"key": "TINKER_API_KEY", "prompt": "API key de Tinker", "url": "https://tinker-console.thinkingmachines.ai/keys"},
                    {"key": "WANDB_API_KEY", "prompt": "API key de WandB", "url": "https://wandb.ai/authorize"},
                ],
                "post_setup": "rl_training",
            },
        ],
    },
}

# Requisitos simples de variables de entorno para toolsets que NO están en
# TOOL_CATEGORIES. Se usan como *fallback* para herramientas como vision/moa
# que sólo necesitan una API key.
TOOLSET_ENV_REQUIREMENTS = {
    "vision":     [("OPENROUTER_API_KEY",   "https://openrouter.ai/keys")],
    "moa":        [("OPENROUTER_API_KEY",   "https://openrouter.ai/keys")],
}


# ─── Post-Setup Hooks ─────────────────────────────────────────────────────────

def _run_post_setup(post_setup_key: str):
    """Ejecuta pasos posteriores a la configuración para herramientas que
    requieren instalación adicional."""
    import shutil
    if post_setup_key == "browserbase":
        node_modules = PROJECT_ROOT / "node_modules" / "agent-browser"
        if not node_modules.exists() and shutil.which("npm"):
            _print_info("    Instalando dependencias de Node.js para herramientas de navegador...")
            import subprocess
            result = subprocess.run(
                ["npm", "install", "--silent"],
                capture_output=True, text=True, cwd=str(PROJECT_ROOT)
            )
            if result.returncode == 0:
                    _print_success("    Dependencias de Node.js instaladas")
            else:
                    _print_warning("    npm install falló - ejecútalo manualmente: cd ~/.hermes/hermes-agent && npm install")
        elif not node_modules.exists():
            _print_warning("    Node.js no se encontró - las herramientas de navegador requieren: npm install (en el directorio hermes-agent)")

    elif post_setup_key == "rl_training":
        try:
            __import__("tinker_atropos")
        except ImportError:
            tinker_dir = PROJECT_ROOT / "tinker-atropos"
            if tinker_dir.exists() and (tinker_dir / "pyproject.toml").exists():
                _print_info("    Instalando submódulo tinker-atropos...")
                import subprocess
                uv_bin = shutil.which("uv")
                if uv_bin:
                    result = subprocess.run(
                        [uv_bin, "pip", "install", "--python", sys.executable, "-e", str(tinker_dir)],
                        capture_output=True, text=True
                    )
                else:
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-e", str(tinker_dir)],
                        capture_output=True, text=True
                    )
                if result.returncode == 0:
                    _print_success("    tinker-atropos instalado")
                else:
                    _print_warning("    La instalación de tinker-atropos falló - ejecútalo manualmente:")
                    _print_info('      uv pip install -e "./tinker-atropos"')
            else:
                _print_warning("    Submódulo tinker-atropos no encontrado - ejecuta:")
                _print_info("      git submodule update --init --recursive")
                _print_info('      uv pip install -e "./tinker-atropos"')


# ─── Platform / Toolset Helpers ───────────────────────────────────────────────

def _get_enabled_platforms() -> List[str]:
    """Devuelve las claves de plataforma que están configuradas (tienen tokens o son CLI)."""
    enabled = ["cli"]
    if get_env_value("TELEGRAM_BOT_TOKEN"):
        enabled.append("telegram")
    if get_env_value("DISCORD_BOT_TOKEN"):
        enabled.append("discord")
    if get_env_value("SLACK_BOT_TOKEN"):
        enabled.append("slack")
    if get_env_value("WHATSAPP_ENABLED"):
        enabled.append("whatsapp")
    return enabled


def _platform_toolset_summary(config: dict, platforms: Optional[List[str]] = None) -> Dict[str, Set[str]]:
    """Devuelve un resumen de toolsets habilitados por plataforma.

    Cuando ``platforms`` es None, usa ``_get_enabled_platforms`` para
    auto-detectar plataformas. Los tests pueden pasar una lista explícita
    para no depender de variables de entorno.
    """
    if platforms is None:
        platforms = _get_enabled_platforms()

    summary: Dict[str, Set[str]] = {}
    for pkey in platforms:
        summary[pkey] = _get_platform_tools(config, pkey)
    return summary


def _get_platform_tools(config: dict, platform: str) -> Set[str]:
    """Resuelve qué nombres de toolset individuales están habilitados para una plataforma."""
    from toolsets import resolve_toolset, TOOLSETS

    platform_toolsets = config.get("platform_toolsets", {})
    toolset_names = platform_toolsets.get(platform)

    if toolset_names is None or not isinstance(toolset_names, list):
        default_ts = PLATFORMS[platform]["default_toolset"]
        toolset_names = [default_ts]

    # Resolver a nombres de herramientas individuales y luego mapear de vuelta
    # a qué toolsets configurables cubren esas herramientas
    all_tool_names = set()
    for ts_name in toolset_names:
        all_tool_names.update(resolve_toolset(ts_name))

    # Mapear los nombres individuales de herramientas a las claves de toolset configurables
    enabled_toolsets = set()
    for ts_key, _, _ in CONFIGURABLE_TOOLSETS:
        ts_tools = set(resolve_toolset(ts_key))
        if ts_tools and ts_tools.issubset(all_tool_names):
            enabled_toolsets.add(ts_key)

    return enabled_toolsets


def _save_platform_tools(config: dict, platform: str, enabled_toolset_keys: Set[str]):
    """Guarda en la configuración las claves de toolset seleccionadas para una plataforma."""
    config.setdefault("platform_toolsets", {})
    config["platform_toolsets"][platform] = sorted(enabled_toolset_keys)
    save_config(config)


def _toolset_has_keys(ts_key: str) -> bool:
    """Comprueba si las API keys requeridas por un toolset están configuradas."""
    # Check TOOL_CATEGORIES first (provider-aware)
    cat = TOOL_CATEGORIES.get(ts_key)
    if cat:
        for provider in cat["providers"]:
            env_vars = provider.get("env_vars", [])
            if not env_vars:
                return True  # Free provider (e.g., Edge TTS)
            if all(get_env_value(v["key"]) for v in env_vars):
                return True
        return False

    # Fallback to simple requirements
    requirements = TOOLSET_ENV_REQUIREMENTS.get(ts_key, [])
    if not requirements:
        return True
    return all(get_env_value(var) for var, _ in requirements)


# ─── Helpers de menús ────────────────────────────────────────────────────────

def _prompt_choice(question: str, choices: list, default: int = 0) -> int:
    """Menú de selección única (teclas de flecha).

    Usa curses para evitar errores de renderizado de simple_term_menu en tmux,
    iTerm y otros terminales no estándar.
    """

    # Selección única basada en curses — funciona en tmux, iTerm y terminales estándar
    try:
        import curses
        result_holder = [default]

        def _curses_menu(stdscr):
            curses.curs_set(0)
            if curses.has_colors():
                curses.start_color()
                curses.use_default_colors()
                curses.init_pair(1, curses.COLOR_GREEN, -1)
                curses.init_pair(2, curses.COLOR_YELLOW, -1)
            cursor = default

            while True:
                stdscr.clear()
                max_y, max_x = stdscr.getmaxyx()
                try:
                    stdscr.addnstr(0, 0, question, max_x - 1,
                                   curses.A_BOLD | (curses.color_pair(2) if curses.has_colors() else 0))
                except curses.error:
                    pass

                for i, c in enumerate(choices):
                    y = i + 2
                    if y >= max_y - 1:
                        break
                    arrow = "→" if i == cursor else " "
                    line = f" {arrow}  {c}"
                    attr = curses.A_NORMAL
                    if i == cursor:
                        attr = curses.A_BOLD
                        if curses.has_colors():
                            attr |= curses.color_pair(1)
                    try:
                        stdscr.addnstr(y, 0, line, max_x - 1, attr)
                    except curses.error:
                        pass

                stdscr.refresh()
                key = stdscr.getch()

                if key in (curses.KEY_UP, ord('k')):
                    cursor = (cursor - 1) % len(choices)
                elif key in (curses.KEY_DOWN, ord('j')):
                    cursor = (cursor + 1) % len(choices)
                elif key in (curses.KEY_ENTER, 10, 13):
                    result_holder[0] = cursor
                    return
                elif key in (27, ord('q')):
                    return

        curses.wrapper(_curses_menu)
        return result_holder[0]

    except Exception:
        pass

    # Fallback: entrada numerada (Windows sin curses, etc.)
    print(color(question, Colors.YELLOW))
    for i, c in enumerate(choices):
        marker = "●" if i == default else "○"
        style = Colors.GREEN if i == default else ""
        print(color(f"  {marker} {i+1}. {c}", style) if style else f"  {marker} {i+1}. {c}")
    while True:
        try:
            val = input(color(f"  Select [1-{len(choices)}] ({default + 1}): ", Colors.DIM))
            if not val:
                return default
            idx = int(val) - 1
            if 0 <= idx < len(choices):
                return idx
        except (ValueError, KeyboardInterrupt, EOFError):
            print()
            return default


def _prompt_toolset_checklist(platform_label: str, enabled: Set[str]) -> Set[str]:
    """Checklist multi-selección de toolsets. Devuelve el conjunto de claves seleccionadas."""
    from hermes_cli.curses_ui import curses_checklist

    labels = []
    for ts_key, ts_label, ts_desc in CONFIGURABLE_TOOLSETS:
        suffix = ""
        if not _toolset_has_keys(ts_key) and (TOOL_CATEGORIES.get(ts_key) or TOOLSET_ENV_REQUIREMENTS.get(ts_key)):
            suffix = "  [sin API key]"
        labels.append(f"{ts_label}  ({ts_desc}){suffix}")

    pre_selected = {
        i for i, (ts_key, _, _) in enumerate(CONFIGURABLE_TOOLSETS)
        if ts_key in enabled
    }

    chosen = curses_checklist(
        f"Herramientas para {platform_label}",
        labels,
        pre_selected,
        cancel_returns=pre_selected,
    )
    return {CONFIGURABLE_TOOLSETS[i][0] for i in chosen}


# ─── Provider-Aware Configuration ────────────────────────────────────────────

def _configure_toolset(ts_key: str, config: dict):
    """Configura un toolset: selección de proveedor + API keys.

    Usa TOOL_CATEGORIES para la configuración dependiente de proveedor y
    recurre a los prompts simples de variables de entorno para los toolsets
    que no están en TOOL_CATEGORIES.
    """
    cat = TOOL_CATEGORIES.get(ts_key)

    if cat:
        _configure_tool_category(ts_key, cat, config)
    else:
        # Simple fallback for vision, moa, etc.
        _configure_simple_requirements(ts_key)


def _configure_tool_category(ts_key: str, cat: dict, config: dict):
    """Configura una categoría de herramienta con selección de proveedor."""
    icon = cat.get("icon", "")
    name = cat["name"]
    providers = cat["providers"]

    # Comprobar requisito de versión de Python
    if cat.get("requires_python"):
        req = cat["requires_python"]
        if sys.version_info < req:
            print()
            _print_error(f"  {name} requiere Python {req[0]}.{req[1]}+ (actual: {sys.version_info.major}.{sys.version_info.minor})")
            _print_info("  Actualiza Python y reinstala para habilitar esta herramienta.")
            return

    if len(providers) == 1:
        # Proveedor único: configurar directamente
        provider = providers[0]
        print()
        print(color(f"  --- {icon} {name} ({provider['name']}) ---", Colors.CYAN))
        if provider.get("tag"):
            _print_info(f"  {provider['tag']}")
        # Para herramientas de proveedor único, mostrar nota si existe
        if cat.get("setup_note"):
            _print_info(f"  {cat['setup_note']}")
        _configure_provider(provider, config)
    else:
        # Varios proveedores: dejar que el usuario elija
        print()
        # Usar título personalizado si se proporciona (por ejemplo "Selecciona proveedor de búsqueda")
        title = cat.get("setup_title", "Elige un proveedor")
        print(color(f"  --- {icon} {name} - {title} ---", Colors.CYAN))
        if cat.get("setup_note"):
            _print_info(f"  {cat['setup_note']}")
        print()

        # Etiquetas sólo en texto plano (sin códigos ANSI en los elementos del menú)
        provider_choices = []
        for p in providers:
            tag = f" ({p['tag']})" if p.get("tag") else ""
            configured = ""
            env_vars = p.get("env_vars", [])
            if not env_vars or all(get_env_value(v["key"]) for v in env_vars):
                if p.get("tts_provider") and config.get("tts", {}).get("provider") == p["tts_provider"]:
                    configured = " [activo]"
                elif not env_vars:
                    configured = " [activo]" if config.get("tts", {}).get("provider", "edge") == p.get("tts_provider", "") else ""
                else:
                    configured = " [configurado]"
            provider_choices.append(f"{p['name']}{tag}{configured}")

        # Añadir opción de omitir
        provider_choices.append("Omitir — mantener valores por defecto / configurar después")

        # Detectar proveedor actual como valor por defecto
        default_idx = 0
        for i, p in enumerate(providers):
            if p.get("tts_provider") and config.get("tts", {}).get("provider") == p["tts_provider"]:
                default_idx = i
                break
            env_vars = p.get("env_vars", [])
            if env_vars and all(get_env_value(v["key"]) for v in env_vars):
                default_idx = i
                break

        provider_idx = _prompt_choice(f"  {title}:", provider_choices, default_idx)

        # Omitido
        if provider_idx >= len(providers):
            _print_info(f"  Se omitió {name}")
            return

        _configure_provider(providers[provider_idx], config)


def _configure_provider(provider: dict, config: dict):
    """Configura un único proveedor: pide API keys y ajusta la config."""
    env_vars = provider.get("env_vars", [])

    # Establecer proveedor TTS en la config si aplica
    if provider.get("tts_provider"):
        config.setdefault("tts", {})["provider"] = provider["tts_provider"]

    if not env_vars:
        _print_success(f"  {provider['name']} - no necesita configuración!")
        return

    # Pedir cada variable de entorno requerida
    all_configured = True
    for var in env_vars:
        existing = get_env_value(var["key"])
        if existing:
            _print_success(f"  {var['key']}: ya configurada")
            # No preguntar para actualizar: este es el flujo de habilitación nueva.
            # La reconfiguración se maneja por separado.
        else:
            url = var.get("url", "")
            if url:
                _print_info(f"  Consigue la tuya en: {url}")

            default_val = var.get("default", "")
            if default_val:
                value = _prompt(f"    {var.get('prompt', var['key'])}", default_val)
            else:
                value = _prompt(f"    {var.get('prompt', var['key'])}", password=True)

            if value:
                save_env_value(var["key"], value)
                _print_success("    Guardado")
            else:
                _print_warning("    Omitido")
                all_configured = False

    # Ejecutar hooks post-configuración si es necesario
    if provider.get("post_setup") and all_configured:
        _run_post_setup(provider["post_setup"])

    if all_configured:
        _print_success(f"  {provider['name']} configurado!")


def _configure_simple_requirements(ts_key: str):
    """*Fallback* simple para toolsets que sólo necesitan variables de entorno
    (sin selección de proveedor)."""
    requirements = TOOLSET_ENV_REQUIREMENTS.get(ts_key, [])
    if not requirements:
        return

    missing = [(var, url) for var, url in requirements if not get_env_value(var)]
    if not missing:
        return

    ts_label = next((l for k, l, _ in CONFIGURABLE_TOOLSETS if k == ts_key), ts_key)
    print()
    print(color(f"  {ts_label} requiere configuración:", Colors.YELLOW))

    for var, url in missing:
        if url:
            _print_info(f"  Consigue la key en: {url}")
        value = _prompt(f"    {var}", password=True)
        if value and value.strip():
            save_env_value(var, value.strip())
            _print_success("    Guardado")
        else:
            _print_warning("    Omitido")


def _reconfigure_tool(config: dict):
    """Permite al usuario reconfigurar el proveedor o API key de una herramienta existente."""
    # Build list of configurable tools that are currently set up
    configurable = []
    for ts_key, ts_label, _ in CONFIGURABLE_TOOLSETS:
        cat = TOOL_CATEGORIES.get(ts_key)
        reqs = TOOLSET_ENV_REQUIREMENTS.get(ts_key)
        if cat or reqs:
            if _toolset_has_keys(ts_key):
                configurable.append((ts_key, ts_label))

    if not configurable:
        _print_info("No hay herramientas configuradas para reconfigurar.")
        return

    choices = [label for _, label in configurable]
    choices.append("Cancelar")

    idx = _prompt_choice("  ¿Qué herramienta te gustaría reconfigurar?", choices, len(choices) - 1)

    if idx >= len(configurable):
        return  # Cancel

    ts_key, ts_label = configurable[idx]
    cat = TOOL_CATEGORIES.get(ts_key)

    if cat:
        _configure_tool_category_for_reconfig(ts_key, cat, config)
    else:
        _reconfigure_simple_requirements(ts_key)

    save_config(config)


def _configure_tool_category_for_reconfig(ts_key: str, cat: dict, config: dict):
    """Reconfigura una categoría de herramienta: selección de proveedor y
    actualización de API keys."""
    icon = cat.get("icon", "")
    name = cat["name"]
    providers = cat["providers"]

    if len(providers) == 1:
        provider = providers[0]
        print()
        print(color(f"  --- {icon} {name} ({provider['name']}) ---", Colors.CYAN))
        _reconfigure_provider(provider, config)
    else:
        print()
        print(color(f"  --- {icon} {name} - Elige un proveedor ---", Colors.CYAN))
        print()

        provider_choices = []
        for p in providers:
            tag = f" ({p['tag']})" if p.get("tag") else ""
            configured = ""
            env_vars = p.get("env_vars", [])
            if not env_vars or all(get_env_value(v["key"]) for v in env_vars):
                if p.get("tts_provider") and config.get("tts", {}).get("provider") == p["tts_provider"]:
                    configured = " [activo]"
                elif not env_vars:
                    configured = ""
                else:
                    configured = " [configurado]"
            provider_choices.append(f"{p['name']}{tag}{configured}")

        default_idx = 0
        for i, p in enumerate(providers):
            if p.get("tts_provider") and config.get("tts", {}).get("provider") == p["tts_provider"]:
                default_idx = i
                break
            env_vars = p.get("env_vars", [])
            if env_vars and all(get_env_value(v["key"]) for v in env_vars):
                default_idx = i
                break

        provider_idx = _prompt_choice("  Selecciona proveedor:", provider_choices, default_idx)
        _reconfigure_provider(providers[provider_idx], config)


def _reconfigure_provider(provider: dict, config: dict):
    """Reconfigura un proveedor: actualiza API keys."""
    env_vars = provider.get("env_vars", [])

    if provider.get("tts_provider"):
        config.setdefault("tts", {})["provider"] = provider["tts_provider"]
        _print_success(f"  Proveedor TTS establecido en: {provider['tts_provider']}")

    if not env_vars:
        _print_success(f"  {provider['name']} - no necesita configuración!")
        return

    for var in env_vars:
        existing = get_env_value(var["key"])
        if existing:
            _print_info(f"  {var['key']}: configurada ({existing[:8]}...)")
        url = var.get("url", "")
        if url:
            _print_info(f"  Consigue la tuya en: {url}")
        default_val = var.get("default", "")
        value = _prompt(f"    {var.get('prompt', var['key'])} (Enter para mantener la actual)", password=not default_val)
        if value and value.strip():
            save_env_value(var["key"], value.strip())
            _print_success("    Actualizado")
        else:
            _print_info("    Se mantiene el valor actual")


def _reconfigure_simple_requirements(ts_key: str):
    """Reconfigura requisitos simples de variables de entorno."""
    requirements = TOOLSET_ENV_REQUIREMENTS.get(ts_key, [])
    if not requirements:
        return

    ts_label = next((l for k, l, _ in CONFIGURABLE_TOOLSETS if k == ts_key), ts_key)
    print()
    print(color(f"  {ts_label}:", Colors.CYAN))

    for var, url in requirements:
        existing = get_env_value(var)
        if existing:
            _print_info(f"  {var}: configurada ({existing[:8]}...)")
        if url:
            _print_info(f"  Consigue la key en: {url}")
        value = _prompt(f"    {var} (Enter para mantener la actual)", password=True)
        if value and value.strip():
            save_env_value(var, value.strip())
            _print_success("    Actualizado")
        else:
            _print_info("    Se mantiene el valor actual")


# ─── Main Entry Point ─────────────────────────────────────────────────────────

def tools_command(args=None, first_install: bool = False, config: dict = None):
    """Punto de entrada para `hermes tools` y `hermes setup tools`.

    Args:
        first_install: cuando es True (lo establece el asistente de configuración
            en instalaciones nuevas), salta el menú de plataformas, va directo
            al checklist de CLI y pide API keys para todas las herramientas
            habilitadas que las necesiten.
        config: diccionario de configuración opcional. Cuando se llama desde el
            asistente, éste pasa su propio dict para que platform_toolsets se
            escriba ahí y sobreviva al save_config() final del asistente.
    """
    if config is None:
        config = load_config()
    enabled_platforms = _get_enabled_platforms()

    print()

    # Modo resumen no interactivo para uso desde la CLI
    if getattr(args, "summary", False):
        total = len(CONFIGURABLE_TOOLSETS)
        print(color("⚕ Resumen de herramientas", Colors.CYAN, Colors.BOLD))
        print()
        summary = _platform_toolset_summary(config, enabled_platforms)
        for pkey in enabled_platforms:
            pinfo = PLATFORMS[pkey]
            enabled = summary.get(pkey, set())
            count = len(enabled)
            print(color(f"  {pinfo['label']}", Colors.BOLD) + color(f"  ({count}/{total})", Colors.DIM))
            if enabled:
                for ts_key in sorted(enabled):
                    label = next((l for k, l, _ in CONFIGURABLE_TOOLSETS if k == ts_key), ts_key)
                    print(color(f"    ✓ {label}", Colors.GREEN))
            else:
                print(color("    (ninguna habilitada)", Colors.DIM))
        print()
        return
    print(color("⚕ Configuración de herramientas de Hermes", Colors.CYAN, Colors.BOLD))
    print(color("  Habilita o deshabilita herramientas por plataforma.", Colors.DIM))
    print(color("  Las herramientas que necesitan API keys se configurarán al habilitarlas.", Colors.DIM))
    print()

    # ── Primera instalación: flujo lineal, sin menú de plataforma ──
    if first_install:
        for pkey in enabled_platforms:
            pinfo = PLATFORMS[pkey]
            current_enabled = _get_platform_tools(config, pkey)

            # Desmarcar toolsets que deberían estar apagados por defecto
            checklist_preselected = current_enabled - _DEFAULT_OFF_TOOLSETS

            # Mostrar checklist
            new_enabled = _prompt_toolset_checklist(pinfo["label"], checklist_preselected)

            added = new_enabled - current_enabled
            removed = current_enabled - new_enabled
            if added:
                for ts in sorted(added):
                    label = next((l for k, l, _ in CONFIGURABLE_TOOLSETS if k == ts), ts)
                    print(color(f"  + {label}", Colors.GREEN))
            if removed:
                for ts in sorted(removed):
                    label = next((l for k, l, _ in CONFIGURABLE_TOOLSETS if k == ts), ts)
                    print(color(f"  - {label}", Colors.RED))

            # Recorrer TODAS las herramientas seleccionadas que tienen opciones
            # de proveedor o necesitan API keys. Esto asegura que navegador
            # (Local vs Browserbase), TTS (Edge vs OpenAI vs ElevenLabs), etc.,
            # se muestren incluso cuando existe un proveedor gratuito.
            to_configure = [
                ts_key for ts_key in sorted(new_enabled)
                if TOOL_CATEGORIES.get(ts_key) or TOOLSET_ENV_REQUIREMENTS.get(ts_key)
            ]

            if to_configure:
                print()
                print(color(f"  Configurando {len(to_configure)} herramienta(s):", Colors.YELLOW))
                for ts_key in to_configure:
                    label = next((l for k, l, _ in CONFIGURABLE_TOOLSETS if k == ts_key), ts_key)
                    print(color(f"    • {label}", Colors.DIM))
                print(color("  Puedes omitir cualquier herramienta que no necesites ahora.", Colors.DIM))
                print()
                for ts_key in to_configure:
                    _configure_toolset(ts_key, config)

            _save_platform_tools(config, pkey, new_enabled)
            save_config(config)
            print(color(f"  ✓ Configuración de herramientas de {pinfo['label']} guardada", Colors.GREEN))
            print()

        return

    # ── Usuario recurrente: bucle de menú de plataformas ──
    # Construir opciones de plataforma
    platform_choices = []
    platform_keys = []
    for pkey in enabled_platforms:
        pinfo = PLATFORMS[pkey]
        current = _get_platform_tools(config, pkey)
        count = len(current)
        total = len(CONFIGURABLE_TOOLSETS)
        platform_choices.append(f"Configurar {pinfo['label']}  ({count}/{total} habilitadas)")
        platform_keys.append(pkey)

    if len(platform_keys) > 1:
        platform_choices.append("Configurar todas las plataformas (global)")
    platform_choices.append("Reconfigurar proveedor o API key de una herramienta existente")
    platform_choices.append("Listo")

    # Index offsets for the extra options after per-platform entries
    _global_idx = len(platform_keys) if len(platform_keys) > 1 else -1
    _reconfig_idx = len(platform_keys) + (1 if len(platform_keys) > 1 else 0)
    _done_idx = _reconfig_idx + 1

    while True:
        idx = _prompt_choice("Selecciona una opción:", platform_choices, default=0)

        # "Listo" seleccionado
        if idx == _done_idx:
            break

        # "Reconfigurar" seleccionado
        if idx == _reconfig_idx:
            _reconfigure_tool(config)
            print()
            continue

        # "Configurar todas las plataformas (global)" seleccionado
        if idx == _global_idx:
            # Usar la unión de las herramientas actuales de todas las plataformas como estado inicial
            all_current = set()
            for pk in platform_keys:
                all_current |= _get_platform_tools(config, pk)
            new_enabled = _prompt_toolset_checklist("Todas las plataformas", all_current)
            if new_enabled != all_current:
                for pk in platform_keys:
                    prev = _get_platform_tools(config, pk)
                    added = new_enabled - prev
                    removed = prev - new_enabled
                    pinfo_inner = PLATFORMS[pk]
                    if added or removed:
                        print(color(f"  {pinfo_inner['label']}:", Colors.DIM))
                        for ts in sorted(added):
                            label = next((l for k, l, _ in CONFIGURABLE_TOOLSETS if k == ts), ts)
                            print(color(f"    + {label}", Colors.GREEN))
                        for ts in sorted(removed):
                            label = next((l for k, l, _ in CONFIGURABLE_TOOLSETS if k == ts), ts)
                            print(color(f"    - {label}", Colors.RED))
                    # Configure API keys for newly enabled tools
                    for ts_key in sorted(added):
                        if (TOOL_CATEGORIES.get(ts_key) or TOOLSET_ENV_REQUIREMENTS.get(ts_key)):
                            if not _toolset_has_keys(ts_key):
                                _configure_toolset(ts_key, config)
                    _save_platform_tools(config, pk, new_enabled)
                save_config(config)
                print(color("  ✓ Configuración guardada para todas las plataformas", Colors.GREEN))
                # Actualizar etiquetas de opciones
                for ci, pk in enumerate(platform_keys):
                    new_count = len(_get_platform_tools(config, pk))
                    total = len(CONFIGURABLE_TOOLSETS)
                    platform_choices[ci] = f"Configurar {PLATFORMS[pk]['label']}  ({new_count}/{total} habilitadas)"
            else:
                print(color("  Sin cambios", Colors.DIM))
            print()
            continue

        pkey = platform_keys[idx]
        pinfo = PLATFORMS[pkey]

        # Obtener toolsets habilitados actualmente para esta plataforma
        current_enabled = _get_platform_tools(config, pkey)

        # Mostrar checklist
        new_enabled = _prompt_toolset_checklist(pinfo["label"], current_enabled)

        if new_enabled != current_enabled:
            added = new_enabled - current_enabled
            removed = current_enabled - new_enabled

            if added:
                for ts in sorted(added):
                    label = next((l for k, l, _ in CONFIGURABLE_TOOLSETS if k == ts), ts)
                    print(color(f"  + {label}", Colors.GREEN))
            if removed:
                for ts in sorted(removed):
                    label = next((l for k, l, _ in CONFIGURABLE_TOOLSETS if k == ts), ts)
                    print(color(f"  - {label}", Colors.RED))

            # Configurar toolsets recién habilitados que necesitan API keys
            for ts_key in sorted(added):
                if (TOOL_CATEGORIES.get(ts_key) or TOOLSET_ENV_REQUIREMENTS.get(ts_key)):
                    if not _toolset_has_keys(ts_key):
                        _configure_toolset(ts_key, config)

            _save_platform_tools(config, pkey, new_enabled)
            save_config(config)
            print(color(f"  ✓ Configuración de {pinfo['label']} guardada", Colors.GREEN))
        else:
            print(color(f"  Sin cambios en {pinfo['label']}", Colors.DIM))

        print()

        # Actualizar la etiqueta de la opción con el nuevo conteo
        new_count = len(_get_platform_tools(config, pkey))
        total = len(CONFIGURABLE_TOOLSETS)
        platform_choices[idx] = f"Configurar {pinfo['label']}  ({new_count}/{total} habilitadas)"

    print()
    print(color("  Configuración de herramientas guardada en ~/.hermes/config.yaml", Colors.DIM))
    print(color("  Los cambios se aplican en el próximo 'hermes' o reinicio del gateway.", Colors.DIM))
    print()
