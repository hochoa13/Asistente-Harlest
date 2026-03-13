"""Gestión de configuración para Hermes Agent.

Los archivos de configuración se guardan en ~/.hermes/ para un acceso fácil:
- ~/.hermes/config.yaml  - Todos los ajustes (modelo, toolsets, terminal, etc.)
- ~/.hermes/.env         - API keys y secretos

Este módulo proporciona:
- hermes config          - Mostrar la configuración actual
- hermes config edit     - Abrir la configuración en un editor
- hermes config set      - Establecer un valor específico
- hermes config wizard   - Volver a ejecutar el asistente de configuración
"""

import os
import platform
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

_IS_WINDOWS = platform.system() == "Windows"

import yaml

from hermes_cli.colors import Colors, color


# =============================================================================
# Config paths
# =============================================================================

def get_hermes_home() -> Path:
    """Obtiene el directorio principal de Hermes (~/.hermes)."""
    return Path(os.getenv("HERMES_HOME", Path.home() / ".hermes"))

def get_config_path() -> Path:
    """Obtiene la ruta del archivo principal de configuración."""
    return get_hermes_home() / "config.yaml"

def get_env_path() -> Path:
    """Obtiene la ruta del archivo .env (para API keys)."""
    return get_hermes_home() / ".env"

def get_project_root() -> Path:
    """Obtiene el directorio de instalación del proyecto."""
    return Path(__file__).parent.parent.resolve()

def _secure_dir(path):
    """Establece acceso solo para el dueño (0700). Sin efecto en Windows."""
    try:
        os.chmod(path, 0o700)
    except (OSError, NotImplementedError):
        pass


def _secure_file(path):
    """Establece lectura/escritura solo para el dueño (0600). Sin efecto en Windows."""
    try:
        if os.path.exists(str(path)):
            os.chmod(path, 0o600)
    except (OSError, NotImplementedError):
        pass


def ensure_hermes_home():
    """Garantiza que ~/.hermes exista con permisos seguros."""
    home = get_hermes_home()
    home.mkdir(parents=True, exist_ok=True)
    _secure_dir(home)
    for subdir in ("cron", "sessions", "logs", "memories"):
        d = home / subdir
        d.mkdir(parents=True, exist_ok=True)
        _secure_dir(d)


# =============================================================================
# Config loading/saving
# =============================================================================

DEFAULT_CONFIG = {
    "model": "anthropic/claude-opus-4.6",
    "toolsets": ["hermes-cli"],
    "agent": {
        "max_turns": 90,
    },
    
    "terminal": {
        "backend": "local",
        "cwd": ".",  # Usar el directorio actual
        "timeout": 180,
        "docker_image": "nikolaik/python-nodejs:python3.11-nodejs20",
        "singularity_image": "docker://nikolaik/python-nodejs:python3.11-nodejs20",
        "modal_image": "nikolaik/python-nodejs:python3.11-nodejs20",
        "daytona_image": "nikolaik/python-nodejs:python3.11-nodejs20",
        # Container resource limits (docker, singularity, modal, daytona — ignored for local/ssh)
        "container_cpu": 1,
        "container_memory": 5120,       # MB (por defecto 5GB)
        "container_disk": 51200,        # MB (por defecto 50GB)
        "container_persistent": True,   # Persistir el sistema de archivos entre sesiones
        # Montajes de volúmenes Docker — comparten directorios del host con el contenedor.
        # Cada entrada es "host_path:container_path" (sintaxis estándar Docker -v).
        # Ejemplo: ["/home/user/projects:/workspace/projects", "/data:/data"]
        "docker_volumes": [],
    },
    
    "browser": {
        "inactivity_timeout": 120,
        "record_sessions": False,  # Grabar automáticamente sesiones del navegador como videos WebM
    },
    
    # Checkpoints del sistema de archivos — snapshots automáticos antes de operaciones destructivas.
    # Cuando está activado, el agente toma un snapshot del directorio de trabajo una vez
    # por turno de conversación (en la primera llamada a write_file/patch). Usa /rollback para restaurar.
    "checkpoints": {
        "enabled": False,
        "max_snapshots": 50,  # Máximo de checkpoints a mantener por directorio
    },
    
    "compression": {
        "enabled": True,
        "threshold": 0.85,
        "summary_model": "google/gemini-3-flash-preview",
        "summary_provider": "auto",
    },
    
    # Configuración de modelos auxiliares — provider:model para cada tarea secundaria.
    # Formato: provider es el nombre del proveedor, model es el slug del modelo.
    # "auto" para provider = autodetectar el mejor proveedor disponible.
    # Modelo vacío = usar el modelo auxiliar por defecto del proveedor.
    # Todas las tareas caen a openrouter:google/gemini-3-flash-preview si
    # el proveedor configurado no está disponible.
    "auxiliary": {
        "vision": {
            "provider": "auto",    # auto | openrouter | nous | codex | custom
            "model": "",           # e.g. "google/gemini-2.5-flash", "gpt-4o"
        },
        "web_extract": {
            "provider": "auto",
            "model": "",
        },
        "compression": {
            "provider": "auto",
            "model": "",
        },
        "session_search": {
            "provider": "auto",
            "model": "",
        },
        "skills_hub": {
            "provider": "auto",
            "model": "",
        },
        "mcp": {
            "provider": "auto",
            "model": "",
        },
        "flush_memories": {
            "provider": "auto",
            "model": "",
        },
    },
    
    "display": {
        "compact": False,
        "personality": "kawaii",
        "resume_display": "full",
        "bell_on_complete": False,
        "show_reasoning": False,
        "skin": "default",
    },
    
    # Configuración de text-to-speech
    "tts": {
        "provider": "edge",  # "edge" (gratis) | "elevenlabs" (premium) | "openai"
        "edge": {
            "voice": "en-US-AriaNeural",
            # Populares: AriaNeural, JennyNeural, AndrewNeural, BrianNeural, SoniaNeural
        },
        "elevenlabs": {
            "voice_id": "pNInz6obpgDQGcFmaJgB",  # Adam
            "model_id": "eleven_multilingual_v2",
        },
        "openai": {
            "model": "gpt-4o-mini-tts",
            "voice": "alloy",
            # Voces: alloy, echo, fable, onyx, nova, shimmer
        },
    },
    
    "stt": {
        "enabled": True,
        "model": "whisper-1",
    },
    
    "human_delay": {
        "mode": "off",
        "min_ms": 800,
        "max_ms": 2500,
    },
    
    # Persistent memory -- bounded curated memory injected into system prompt
    "memory": {
        "memory_enabled": True,
        "user_profile_enabled": True,
        "memory_char_limit": 2200,   # ~800 tokens a 2.75 chars/token
        "user_char_limit": 1375,     # ~500 tokens a 2.75 chars/token
    },

    # Delegación a subagentes — sobrescribe el provider:model usado por delegate_task
    # para que los agentes hijos puedan ejecutarse en otro proveedor/modelo (más barato/rápido).
    # Usa la misma resolución de proveedor en tiempo de ejecución que el CLI/gateway,
    # así que se soportan todos los proveedores configurados (OpenRouter, Nous, Z.ai, Kimi, etc.).
    "delegation": {
        "model": "",       # e.g. "google/gemini-3-flash-preview" (empty = inherit parent model)
        "provider": "",    # e.g. "openrouter" (empty = inherit parent provider + credentials)
    },

    # Archivo de mensajes de prefill efímeros — lista JSON de dicts {role, content}
    # inyectados al inicio de cada llamada de API para few-shot priming.
    # Nunca se guarda en sesiones, logs ni trayectorias.
    "prefill_messages_file": "",
    
    # Memoria nativa Honcho -- lee ~/.honcho/config.json como única fuente de verdad.
    # Esta sección solo es necesaria para overrides específicos de Hermes; todo lo demás
    # (apiKey, workspace, peerName, sessions, enabled) viene de la configuración global.
    "honcho": {},

    # Zona horaria IANA (p. ej. "Asia/Kolkata", "America/New_York").
    # Cadena vacía significa usar la hora local del servidor.
    "timezone": "",

    # Ajustes de la plataforma Discord (modo gateway)
    "discord": {
        "require_mention": True,       # Requerir @mención para responder en canales de servidor
        "free_response_channels": "",  # IDs de canal separados por comas donde el bot responde sin mención
    },

    # Patrones de comandos peligrosos permitidos permanentemente (añadidos mediante aprobación "always")
    "command_allowlist": [],
    # Comandos rápidos definidos por el usuario que se saltan el loop del agente (tipo: exec solamente)
    "quick_commands": {},
    # Personalidades personalizadas — añade tus propias entradas aquí
    # Soporta formato string: {"name": "system prompt"}
    # O formato dict: {"name": {"description": "...", "system_prompt": "...", "tone": "...", "style": "..."}}
    "personalities": {},

    # Versión del esquema de config - súbela cuando añadas nuevos campos obligatorios
    "_config_version": 7,
}

# =============================================================================
# Config Migration System
# =============================================================================

# Track which env vars were introduced in each config version.
# Migration only mentions vars new since the user's previous version.
ENV_VARS_BY_VERSION: Dict[int, List[str]] = {
    3: ["FIRECRAWL_API_KEY", "BROWSERBASE_API_KEY", "BROWSERBASE_PROJECT_ID", "FAL_KEY"],
    4: ["VOICE_TOOLS_OPENAI_KEY", "ELEVENLABS_API_KEY"],
    5: ["WHATSAPP_ENABLED", "WHATSAPP_MODE", "WHATSAPP_ALLOWED_USERS",
        "SLACK_BOT_TOKEN", "SLACK_APP_TOKEN", "SLACK_ALLOWED_USERS"],
}

# Variables de entorno requeridas con metadatos para mensajes de migración.
# El proveedor de LLM es obligatorio pero se gestiona en el asistente de
# configuración (Nous Portal / OpenRouter / endpoint personalizado), por lo
# que este dict se deja vacío a propósito: ninguna variable es universalmente requerida.
REQUIRED_ENV_VARS = {}

# Variables de entorno opcionales que mejoran la funcionalidad
OPTIONAL_ENV_VARS = {
    # ── Proveedor (gestionado en la selección de proveedor, no se muestra en checklists) ──
    "NOUS_BASE_URL": {
        "description": "Override de la base URL de Nous Portal",
        "prompt": "Base URL de Nous Portal (deja vacío para usar por defecto)",
        "url": None,
        "password": False,
        "category": "provider",
        "advanced": True,
    },
    "OPENROUTER_API_KEY": {
        "description": "OpenRouter API key (para visión, helpers de scraping web y MoA)",
        "prompt": "OpenRouter API key",
        "url": "https://openrouter.ai/keys",
        "password": True,
        "tools": ["vision_analyze", "mixture_of_agents"],
        "category": "provider",
        "advanced": True,
    },
    "GLM_API_KEY": {
        "description": "Z.AI / GLM API key (también se reconoce como ZAI_API_KEY / Z_AI_API_KEY)",
        "prompt": "Z.AI / GLM API key",
        "url": "https://z.ai/",
        "password": True,
        "category": "provider",
        "advanced": True,
    },
    "ZAI_API_KEY": {
        "description": "Z.AI API key (alias de GLM_API_KEY)",
        "prompt": "Z.AI API key",
        "url": "https://z.ai/",
        "password": True,
        "category": "provider",
        "advanced": True,
    },
    "Z_AI_API_KEY": {
        "description": "Z.AI API key (alias de GLM_API_KEY)",
        "prompt": "Z.AI API key",
        "url": "https://z.ai/",
        "password": True,
        "category": "provider",
        "advanced": True,
    },
    "GLM_BASE_URL": {
        "description": "Override de la base URL de Z.AI / GLM",
        "prompt": "Base URL de Z.AI / GLM (deja vacío para usar por defecto)",
        "url": None,
        "password": False,
        "category": "provider",
        "advanced": True,
    },
    "KIMI_API_KEY": {
        "description": "Kimi / Moonshot API key",
        "prompt": "Kimi API key",
        "url": "https://platform.moonshot.cn/",
        "password": True,
        "category": "provider",
        "advanced": True,
    },
    "KIMI_BASE_URL": {
        "description": "Override de la base URL de Kimi / Moonshot",
        "prompt": "Base URL de Kimi (deja vacío para usar por defecto)",
        "url": None,
        "password": False,
        "category": "provider",
        "advanced": True,
    },
    "MINIMAX_API_KEY": {
        "description": "MiniMax API key (internacional)",
        "prompt": "MiniMax API key",
        "url": "https://www.minimax.io/",
        "password": True,
        "category": "provider",
        "advanced": True,
    },
    "MINIMAX_BASE_URL": {
        "description": "Override de la base URL de MiniMax",
        "prompt": "Base URL de MiniMax (deja vacío para usar por defecto)",
        "url": None,
        "password": False,
        "category": "provider",
        "advanced": True,
    },
    "MINIMAX_CN_API_KEY": {
        "description": "MiniMax API key (endpoint China)",
        "prompt": "MiniMax (China) API key",
        "url": "https://www.minimaxi.com/",
        "password": True,
        "category": "provider",
        "advanced": True,
    },
    "MINIMAX_CN_BASE_URL": {
        "description": "Override de la base URL de MiniMax (China)",
        "prompt": "Base URL de MiniMax (China) (deja vacío para usar por defecto)",
        "url": None,
        "password": False,
        "category": "provider",
        "advanced": True,
    },

    # ── Tool API keys ──
    "FIRECRAWL_API_KEY": {
        "description": "Firecrawl API key para búsqueda web y scraping",
        "prompt": "Firecrawl API key",
        "url": "https://firecrawl.dev/",
        "tools": ["web_search", "web_extract"],
        "password": True,
        "category": "tool",
    },
    "FIRECRAWL_API_URL": {
        "description": "Firecrawl API URL para instancias self-hosted (opcional)",
        "prompt": "Firecrawl API URL (deja vacío para usar cloud)",
        "url": None,
        "password": False,
        "category": "tool",
        "advanced": True,
    },
    "BROWSERBASE_API_KEY": {
        "description": "Browserbase API key para navegador en la nube (opcional — el navegador local funciona sin esto)",
        "prompt": "Browserbase API key",
        "url": "https://browserbase.com/",
        "tools": ["browser_navigate", "browser_click"],
        "password": True,
        "category": "tool",
    },
    "BROWSERBASE_PROJECT_ID": {
        "description": "Browserbase project ID (opcional — solo necesario para navegador en la nube)",
        "prompt": "Browserbase project ID",
        "url": "https://browserbase.com/",
        "tools": ["browser_navigate", "browser_click"],
        "password": False,
        "category": "tool",
    },
    "FAL_KEY": {
        "description": "FAL API key para generación de imágenes",
        "prompt": "FAL API key",
        "url": "https://fal.ai/",
        "tools": ["image_generate"],
        "password": True,
        "category": "tool",
    },
    "TINKER_API_KEY": {
        "description": "Tinker API key para entrenamiento RL",
        "prompt": "Tinker API key",
        "url": "https://tinker-console.thinkingmachines.ai/keys",
        "tools": ["rl_start_training", "rl_check_status", "rl_stop_training"],
        "password": True,
        "category": "tool",
    },
    "WANDB_API_KEY": {
        "description": "Weights & Biases API key para seguimiento de experimentos",
        "prompt": "WandB API key",
        "url": "https://wandb.ai/authorize",
        "tools": ["rl_get_results", "rl_check_status"],
        "password": True,
        "category": "tool",
    },
    "VOICE_TOOLS_OPENAI_KEY": {
        "description": "OpenAI API key para transcripción de voz (Whisper) y OpenAI TTS",
        "prompt": "OpenAI API Key (para Whisper STT + TTS)",
        "url": "https://platform.openai.com/api-keys",
        "tools": ["voice_transcription", "openai_tts"],
        "password": True,
        "category": "tool",
    },
    "ELEVENLABS_API_KEY": {
        "description": "ElevenLabs API key para voces premium de text-to-speech",
        "prompt": "ElevenLabs API key",
        "url": "https://elevenlabs.io/",
        "password": True,
        "category": "tool",
    },
    "GITHUB_TOKEN": {
        "description": "GitHub token para Skills Hub (más límite de rate de API, publicación de skills)",
        "prompt": "GitHub Token",
        "url": "https://github.com/settings/tokens",
        "password": True,
        "category": "tool",
    },

    # ── Honcho ──
    "HONCHO_API_KEY": {
        "description": "Honcho API key para memoria persistente nativa de IA",
        "prompt": "Honcho API key",
        "url": "https://app.honcho.dev",
        "tools": ["query_user_context"],
        "password": True,
        "category": "tool",
    },

    # ── Messaging platforms ──
    "TELEGRAM_BOT_TOKEN": {
        "description": "Telegram bot token obtenido de @BotFather",
        "prompt": "Telegram bot token",
        "url": "https://t.me/BotFather",
        "password": True,
        "category": "messaging",
    },
    "TELEGRAM_ALLOWED_USERS": {
        "description": "IDs de usuario de Telegram (separados por comas) autorizados a usar el bot (obtén el ID de @userinfobot)",
        "prompt": "IDs de usuario de Telegram permitidos (separados por comas)",
        "url": "https://t.me/userinfobot",
        "password": False,
        "category": "messaging",
    },
    "DISCORD_BOT_TOKEN": {
        "description": "Discord bot token obtenido desde Developer Portal",
        "prompt": "Discord bot token",
        "url": "https://discord.com/developers/applications",
        "password": True,
        "category": "messaging",
    },
    "DISCORD_ALLOWED_USERS": {
        "description": "IDs de usuario de Discord autorizados a usar el bot (separados por comas)",
        "prompt": "IDs de usuario de Discord permitidos (separados por comas)",
        "url": None,
        "password": False,
        "category": "messaging",
    },
    "SLACK_BOT_TOKEN": {
        "description": "Slack bot token (xoxb-). Consíguelo en OAuth & Permissions tras instalar tu app. "
                       "Scopes requeridos: chat:write, app_mentions:read, channels:history, groups:history, "
                       "im:history, im:read, im:write, users:read, files:write",
        "prompt": "Slack Bot Token (xoxb-...)",
        "url": "https://api.slack.com/apps",
        "password": True,
        "category": "messaging",
    },
    "SLACK_APP_TOKEN": {
        "description": "Slack app-level token (xapp-) para Socket Mode. Consíguelo en Basic Information → "
                       "App-Level Tokens. Asegúrate también de que Event Subscriptions incluya: message.im, "
                       "message.channels, message.groups, app_mention",
        "prompt": "Slack App Token (xapp-...)",
        "url": "https://api.slack.com/apps",
        "password": True,
        "category": "messaging",
    },
    "GATEWAY_ALLOW_ALL_USERS": {
        "description": "Permitir que todos los usuarios interactúen con los bots de mensajería (true/false). Por defecto: false.",
        "prompt": "Permitir a todos los usuarios (true/false)",
        "url": None,
        "password": False,
        "category": "messaging",
        "advanced": True,
    },

    # ── Agent settings ──
    "MESSAGING_CWD": {
        "description": "Directorio de trabajo para comandos de terminal vía mensajería",
        "prompt": "Directorio de trabajo de mensajería (por defecto: home)",
        "url": None,
        "password": False,
        "category": "setting",
    },
    "SUDO_PASSWORD": {
        "description": "Contraseña sudo para comandos de terminal que requieren acceso root",
        "prompt": "Contraseña sudo",
        "url": None,
        "password": True,
        "category": "setting",
    },
    "HERMES_MAX_ITERATIONS": {
        "description": "Número máximo de iteraciones de llamadas a herramientas por conversación (por defecto: 90)",
        "prompt": "Iteraciones máximas",
        "url": None,
        "password": False,
        "category": "setting",
    },
    # HERMES_TOOL_PROGRESS and HERMES_TOOL_PROGRESS_MODE are deprecated —
    # now configured via display.tool_progress in config.yaml (off|new|all|verbose).
    # Gateway falls back to these env vars for backward compatibility.
    "HERMES_TOOL_PROGRESS": {
        "description": "(deprecated) Usa display.tool_progress en config.yaml en su lugar",
        "prompt": "Tool progress (deprecated — usa config.yaml)",
        "url": None,
        "password": False,
        "category": "setting",
    },
    "HERMES_TOOL_PROGRESS_MODE": {
        "description": "(deprecated) Usa display.tool_progress en config.yaml en su lugar",
        "prompt": "Progress mode (deprecated — usa config.yaml)",
        "url": None,
        "password": False,
        "category": "setting",
    },
    "HERMES_PREFILL_MESSAGES_FILE": {
        "description": "Ruta a un archivo JSON con mensajes efímeros de prefill para few-shot priming",
        "prompt": "Ruta del archivo de mensajes de prefill",
        "url": None,
        "password": False,
        "category": "setting",
    },
    "HERMES_EPHEMERAL_SYSTEM_PROMPT": {
        "description": "System prompt efímero inyectado en tiempo de llamada de API (nunca se persiste en sesiones)",
        "prompt": "System prompt efímero",
        "url": None,
        "password": False,
        "category": "setting",
    },
}


def get_missing_env_vars(required_only: bool = False) -> List[Dict[str, Any]]:
    """Comprueba qué variables de entorno faltan.

    Devuelve una lista de dicts con información de cada variable ausente.
    """
    missing = []
    
    # Check required vars
    for var_name, info in REQUIRED_ENV_VARS.items():
        if not get_env_value(var_name):
            missing.append({"name": var_name, **info, "is_required": True})
    
    # Check optional vars (if not required_only)
    if not required_only:
        for var_name, info in OPTIONAL_ENV_VARS.items():
            if not get_env_value(var_name):
                missing.append({"name": var_name, **info, "is_required": False})
    
    return missing


def _set_nested(config: dict, dotted_key: str, value):
    """Set a value at an arbitrarily nested dotted key path.

    Creates intermediate dicts as needed, e.g. ``_set_nested(c, "a.b.c", 1)``
    ensures ``c["a"]["b"]["c"] == 1``.
    """
    parts = dotted_key.split(".")
    current = config
    for part in parts[:-1]:
        if part not in current or not isinstance(current.get(part), dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


def get_missing_config_fields() -> List[Dict[str, Any]]:
    """Comprueba qué campos de configuración faltan o están desactualizados (recursivo).

    Recorre DEFAULT_CONFIG a cualquier profundidad y reporta las claves
    presentes en los defaults pero ausentes en la config cargada del usuario.
    """
    config = load_config()
    missing = []

    def _check(defaults: dict, current: dict, prefix: str = ""):
        for key, default_value in defaults.items():
            if key.startswith('_'):
                continue
            full_key = key if not prefix else f"{prefix}.{key}"
            if key not in current:
                missing.append({
                    "key": full_key,
                    "default": default_value,
                    "description": f"Nueva opción de configuración: {full_key}",
                })
            elif isinstance(default_value, dict) and isinstance(current.get(key), dict):
                _check(default_value, current[key], full_key)

    _check(DEFAULT_CONFIG, config)
    return missing


def check_config_version() -> Tuple[int, int]:
    """Comprueba la versión de configuración.

    Devuelve (versión_actual, versión_última).
    """
    config = load_config()
    current = config.get("_config_version", 0)
    latest = DEFAULT_CONFIG.get("_config_version", 1)
    return current, latest


def migrate_config(interactive: bool = True, quiet: bool = False) -> Dict[str, Any]:
    """Migra la configuración a la última versión, pidiendo nuevos campos requeridos.

    Args:
        interactive: Si es True, pregunta al usuario por los valores que faltan
        quiet: Si es True, suprime la salida
		
    Returns:
        Dict con los resultados de la migración: {"env_added": [...], "config_added": [...], "warnings": [...]}
    """
    results = {"env_added": [], "config_added": [], "warnings": []}
    
    # Check config version
    current_ver, latest_ver = check_config_version()
    
    # ── Versión 3 → 4: migrar tool progress de .env a config.yaml ──
    if current_ver < 4:
        config = load_config()
        display = config.get("display", {})
        if not isinstance(display, dict):
            display = {}
        if "tool_progress" not in display:
            old_enabled = get_env_value("HERMES_TOOL_PROGRESS")
            old_mode = get_env_value("HERMES_TOOL_PROGRESS_MODE")
            if old_enabled and old_enabled.lower() in ("false", "0", "no"):
                display["tool_progress"] = "off"
                results["config_added"].append("display.tool_progress=off (from HERMES_TOOL_PROGRESS=false)")
            elif old_mode and old_mode.lower() in ("new", "all"):
                display["tool_progress"] = old_mode.lower()
                results["config_added"].append(f"display.tool_progress={old_mode.lower()} (from HERMES_TOOL_PROGRESS_MODE)")
            else:
                display["tool_progress"] = "all"
                results["config_added"].append("display.tool_progress=all (default)")
            config["display"] = display
            save_config(config)
            if not quiet:
                print(f"  ✓ Se migró tool_progress a config.yaml: {display['tool_progress']}")
    
    # ── Versión 4 → 5: añadir campo timezone ──
    if current_ver < 5:
        config = load_config()
        if "timezone" not in config:
            old_tz = os.getenv("HERMES_TIMEZONE", "")
            if old_tz and old_tz.strip():
                config["timezone"] = old_tz.strip()
                results["config_added"].append(f"timezone={old_tz.strip()} (from HERMES_TIMEZONE)")
            else:
                config["timezone"] = ""
                results["config_added"].append("timezone= (vacío, usa hora local del servidor)")
            save_config(config)
            if not quiet:
                tz_display = config["timezone"] or "(hora local del servidor)"
                print(f"  ✓ Se añadió timezone a config.yaml: {tz_display}")

    if current_ver < latest_ver and not quiet:
        print(f"Versión de config: {current_ver} → {latest_ver}")
    
    # Comprobar variables de entorno requeridas que falten
    missing_env = get_missing_env_vars(required_only=True)
    
    if missing_env and not quiet:
        print("\n⚠️  Faltan variables de entorno requeridas:")
        for var in missing_env:
            print(f"   • {var['name']}: {var['description']}")
    
    if interactive and missing_env:
        print("\nVamos a configurarlas ahora:\n")
        for var in missing_env:
            if var.get("url"):
                print(f"  Obtén tu key en: {var['url']}")
            
            if var.get("password"):
                import getpass
                value = getpass.getpass(f"  {var['prompt']}: ")
            else:
                value = input(f"  {var['prompt']}: ").strip()
            
            if value:
                save_env_value(var["name"], value)
                results["env_added"].append(var["name"])
                print(f"  ✓ Se guardó {var['name']}")
            else:
                results["warnings"].append(f"Se omitió {var['name']} - algunas funciones pueden no funcionar")
            print()
    
    # Comprobar variables de entorno opcionales que falten y ofrecer configurarlas de forma interactiva
    # Saltar las vars "advanced" (como OPENAI_BASE_URL): son para usuarios avanzados
    missing_optional = get_missing_env_vars(required_only=False)
    required_names = {v["name"] for v in missing_env} if missing_env else set()
    missing_optional = [
        v for v in missing_optional
        if v["name"] not in required_names and not v.get("advanced")
    ]
    
    # Solo ofrecer configurar variables que sean NUEVAS desde la versión anterior del usuario
    new_var_names = set()
    for ver in range(current_ver + 1, latest_ver + 1):
        new_var_names.update(ENV_VARS_BY_VERSION.get(ver, []))

    if new_var_names and interactive and not quiet:
        new_and_unset = [
            (name, OPTIONAL_ENV_VARS[name])
            for name in sorted(new_var_names)
            if not get_env_value(name) and name in OPTIONAL_ENV_VARS
        ]
        if new_and_unset:
            print(f"\n  {len(new_and_unset)} nuevas API keys opcionales en esta actualización:")
            for name, info in new_and_unset:
                print(f"    • {name} — {info.get('description', '')}")
            print()
            try:
                answer = input("  ¿Configurar nuevas keys ahora? [y/N]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                answer = "n"

            if answer in ("y", "yes"):
                print()
                for name, info in new_and_unset:
                    if info.get("url"):
                        print(f"  {info.get('description', name)}")
                        print(f"  Obtén tu key en: {info['url']}")
                    else:
                        print(f"  {info.get('description', name)}")
                    if info.get("password"):
                        import getpass
                        value = getpass.getpass(f"  {info.get('prompt', name)} (Enter para omitir): ")
                    else:
                        value = input(f"  {info.get('prompt', name)} (Enter para omitir): ").strip()
                    if value:
                        save_env_value(name, value)
                        results["env_added"].append(name)
                        print(f"  ✓ Se guardó {name}")
                    print()
            else:
                print("  Puedes configurarlas luego con: hermes config set KEY VALUE")
    
    # Comprobar campos de config que falten
    missing_config = get_missing_config_fields()
    
    if missing_config:
        config = load_config()
        
        for field in missing_config:
            key = field["key"]
            default = field["default"]
            
            _set_nested(config, key, default)
            results["config_added"].append(key)
            if not quiet:
                print(f"  ✓ Se añadió {key} = {default}")
        
        # Update version and save
        config["_config_version"] = latest_ver
        save_config(config)
    elif current_ver < latest_ver:
        # Just update version
        config = load_config()
        config["_config_version"] = latest_ver
        save_config(config)
    
    return results


def _deep_merge(base: dict, override: dict) -> dict:
    """Fusiona recursivamente *override* en *base*, preservando defaults anidados.

    Las claves en *override* tienen prioridad. Si ambos valores son dicts, la
    fusión es recursiva, así que un usuario que sobrescriba solo
    ``tts.elevenlabs.voice_id`` conservará el ``tts.elevenlabs.model_id`` por defecto.
    """
    result = base.copy()
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _normalize_max_turns_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Normaliza el max_turns de nivel raíz antiguo en agent.max_turns."""
    config = dict(config)
    agent_config = dict(config.get("agent") or {})

    if "max_turns" in config and "max_turns" not in agent_config:
        agent_config["max_turns"] = config["max_turns"]

    if "max_turns" not in agent_config:
        agent_config["max_turns"] = DEFAULT_CONFIG["agent"]["max_turns"]

    config["agent"] = agent_config
    config.pop("max_turns", None)
    return config



def load_config() -> Dict[str, Any]:
    """Carga la configuración desde ~/.hermes/config.yaml."""
    import copy
    config_path = get_config_path()
    
    config = copy.deepcopy(DEFAULT_CONFIG)
    
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                user_config = yaml.safe_load(f) or {}

            if "max_turns" in user_config:
                agent_user_config = dict(user_config.get("agent") or {})
                if agent_user_config.get("max_turns") is None:
                    agent_user_config["max_turns"] = user_config["max_turns"]
                user_config["agent"] = agent_user_config
                user_config.pop("max_turns", None)

            config = _deep_merge(config, user_config)
        except Exception as e:
            print(f"Advertencia: no se pudo cargar la configuración: {e}")
    
    return _normalize_max_turns_config(config)


# _COMMENTED_SECTIONS contiene secciones comentadas opcionales que se añaden
# al guardar config.yaml para documentar opciones avanzadas.
_COMMENTED_SECTIONS = """
# ── Security ──────────────────────────────────────────────────────────
# API keys, tokens y contraseñas se ocultan en la salida de herramientas por defecto.
# Ponlo en false para ver los valores completos (útil para depurar problemas de auth).
#
# security:
#   redact_secrets: false

# ── Fallback Model ────────────────────────────────────────────────────
# Failover automático de proveedor cuando el primario no está disponible.
# Descomenta y configura para activarlo. Se dispara en rate limits (429),
# sobrecarga (529), errores de servicio (503) o fallos de conexión.
#
# Proveedores soportados:
#   openrouter   (OPENROUTER_API_KEY)  — enruta a cualquier modelo
#   openai-codex (OAuth — hermes login) — OpenAI Codex
#   nous         (OAuth — hermes login) — Nous Portal
#   zai          (ZAI_API_KEY)         — Z.AI / GLM
#   kimi-coding  (KIMI_API_KEY)        — Kimi / Moonshot
#   minimax      (MINIMAX_API_KEY)     — MiniMax
#   minimax-cn   (MINIMAX_CN_API_KEY)  — MiniMax (China)
#
# Para endpoints personalizados compatibles con OpenAI, añade base_url y api_key_env.
#
# fallback_model:
#   provider: openrouter
#   model: anthropic/claude-sonnet-4
"""


def save_config(config: Dict[str, Any]):
    """Guarda la configuración en ~/.hermes/config.yaml."""
    from utils import atomic_yaml_write

    ensure_hermes_home()
    config_path = get_config_path()
    normalized = _normalize_max_turns_config(config)

    # Build optional commented-out sections for features that are off by
    # default or only relevant when explicitly configured.
    sections = []
    sec = normalized.get("security", {})
    if not sec or sec.get("redact_secrets") is None:
        sections.append("security")
    fb = normalized.get("fallback_model", {})
    if not fb or not (fb.get("provider") and fb.get("model")):
        sections.append("fallback")

    atomic_yaml_write(
        config_path,
        normalized,
        extra_content=_COMMENTED_SECTIONS if sections else None,
    )
    _secure_file(config_path)


def load_env() -> Dict[str, str]:
    """Carga variables de entorno desde ~/.hermes/.env."""
    env_path = get_env_path()
    env_vars = {}
    
    if env_path.exists():
        # On Windows, open() defaults to the system locale (cp1252) which can
        # fail on UTF-8 .env files. Use explicit UTF-8 only on Windows.
        open_kw = {"encoding": "utf-8", "errors": "replace"} if _IS_WINDOWS else {}
        with open(env_path, **open_kw) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    env_vars[key.strip()] = value.strip().strip('"\'')
    
    return env_vars


def save_env_value(key: str, value: str):
    """Guarda o actualiza un valor en ~/.hermes/.env."""
    ensure_hermes_home()
    env_path = get_env_path()
    
    # On Windows, open() defaults to the system locale (cp1252) which can
    # cause OSError errno 22 on UTF-8 .env files.
    read_kw = {"encoding": "utf-8", "errors": "replace"} if _IS_WINDOWS else {}
    write_kw = {"encoding": "utf-8"} if _IS_WINDOWS else {}

    lines = []
    if env_path.exists():
        with open(env_path, **read_kw) as f:
            lines = f.readlines()
    
    # Find and update or append
    found = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{key}="):
            lines[i] = f"{key}={value}\n"
            found = True
            break
    
    if not found:
        # Ensure there's a newline at the end of the file before appending
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        lines.append(f"{key}={value}\n")
    
    fd, tmp_path = tempfile.mkstemp(dir=str(env_path.parent), suffix='.tmp', prefix='.env_')
    try:
        with os.fdopen(fd, 'w', **write_kw) as f:
            f.writelines(lines)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, env_path)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    _secure_file(env_path)

    # Restrict .env permissions to owner-only (contains API keys)
    if not _IS_WINDOWS:
        try:
            os.chmod(env_path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass


def get_env_value(key: str) -> Optional[str]:
    """Obtiene un valor desde ~/.hermes/.env o desde el entorno."""
    # Check environment first
    if key in os.environ:
        return os.environ[key]
    
    # Then check .env file
    env_vars = load_env()
    return env_vars.get(key)


# =============================================================================
# Config display
# =============================================================================

def redact_key(key: str) -> str:
    """Oculta parcialmente una API key para mostrarla en pantalla."""
    if not key:
        return color("(no configurada)", Colors.DIM)
    if len(key) < 12:
        return "***"
    return key[:4] + "..." + key[-4:]


def show_config():
    """Muestra la configuración actual."""
    config = load_config()
    env_vars = load_env()
    
    print()
    print(color("┌─────────────────────────────────────────────────────────┐", Colors.CYAN))
    print(color("│           ⚕ Configuración de Hermes                    │", Colors.CYAN))
    print(color("└─────────────────────────────────────────────────────────┘", Colors.CYAN))
    
    # Rutas
    print()
    print(color("◆ Rutas", Colors.CYAN, Colors.BOLD))
    print(f"  Config:       {get_config_path()}")
    print(f"  Secrets:      {get_env_path()}")
    print(f"  Install:      {get_project_root()}")
    
    # API Keys
    print()
    print(color("◆ API Keys", Colors.CYAN, Colors.BOLD))
    
    keys = [
        ("OPENROUTER_API_KEY", "OpenRouter"),
        ("ANTHROPIC_API_KEY", "Anthropic"),
        ("VOICE_TOOLS_OPENAI_KEY", "OpenAI (STT/TTS)"),
        ("FIRECRAWL_API_KEY", "Firecrawl"),
        ("BROWSERBASE_API_KEY", "Browserbase"),
        ("FAL_KEY", "FAL"),
    ]
    
    for env_key, name in keys:
        value = get_env_value(env_key)
        print(f"  {name:<14} {redact_key(value)}")
    
    # Ajustes de modelo
    print()
    print(color("◆ Modelo", Colors.CYAN, Colors.BOLD))
    print(f"  Modelo:       {config.get('model', 'no configurado')}")
    print(f"  Máx. turnos:  {config.get('agent', {}).get('max_turns', DEFAULT_CONFIG['agent']['max_turns'])}")
    print(f"  Toolsets:     {', '.join(config.get('toolsets', ['all']))}")
    
    # Display
    print()
    print(color("◆ Display", Colors.CYAN, Colors.BOLD))
    display = config.get('display', {})
    print(f"  Personalidad: {display.get('personality', 'kawaii')}")
    print(f"  Razonamiento: {'activado' if display.get('show_reasoning', False) else 'desactivado'}")
    print(f"  Campana:      {'activada' if display.get('bell_on_complete', False) else 'desactivada'}")

    # Terminal
    print()
    print(color("◆ Terminal", Colors.CYAN, Colors.BOLD))
    terminal = config.get('terminal', {})
    print(f"  Backend:      {terminal.get('backend', 'local')}")
    print(f"  Directorio:   {terminal.get('cwd', '.')}")
    print(f"  Timeout:      {terminal.get('timeout', 60)}s")
    
    if terminal.get('backend') == 'docker':
        print(f"  Docker image: {terminal.get('docker_image', 'python:3.11-slim')}")
    elif terminal.get('backend') == 'singularity':
        print(f"  Image:        {terminal.get('singularity_image', 'docker://python:3.11')}")
    elif terminal.get('backend') == 'modal':
        print(f"  Modal image:  {terminal.get('modal_image', 'python:3.11')}")
        modal_token = get_env_value('MODAL_TOKEN_ID')
        print(f"  Modal token:  {'configurado' if modal_token else '(no configurado)'}")
    elif terminal.get('backend') == 'daytona':
        print(f"  Daytona image: {terminal.get('daytona_image', 'nikolaik/python-nodejs:python3.11-nodejs20')}")
        daytona_key = get_env_value('DAYTONA_API_KEY')
        print(f"  API key:      {'configurada' if daytona_key else '(no configurada)'}")
    elif terminal.get('backend') == 'ssh':
        ssh_host = get_env_value('TERMINAL_SSH_HOST')
        ssh_user = get_env_value('TERMINAL_SSH_USER')
        print(f"  SSH host:     {ssh_host or '(no configurado)'}")
        print(f"  SSH user:     {ssh_user or '(no configurado)'}")
    
    # Zona horaria
    print()
    print(color("◆ Zona horaria", Colors.CYAN, Colors.BOLD))
    tz = config.get('timezone', '')
    if tz:
        print(f"  Zona horaria: {tz}")
    else:
        print(f"  Zona horaria: {color('(hora local del servidor)', Colors.DIM)}")

    # Compresión de contexto
    print()
    print(color("◆ Compresión de contexto", Colors.CYAN, Colors.BOLD))
    compression = config.get('compression', {})
    enabled = compression.get('enabled', True)
    print(f"  Activada:     {'sí' if enabled else 'no'}")
    if enabled:
        print(f"  Threshold:    {compression.get('threshold', 0.85) * 100:.0f}%")
        print(f"  Modelo:       {compression.get('summary_model', 'google/gemini-3-flash-preview')}")
        comp_provider = compression.get('summary_provider', 'auto')
        if comp_provider != 'auto':
            print(f"  Proveedor:    {comp_provider}")
    
    # Modelos auxiliares
    auxiliary = config.get('auxiliary', {})
    aux_tasks = {
        "Vision":      auxiliary.get('vision', {}),
        "Web extract": auxiliary.get('web_extract', {}),
    }
    has_overrides = any(
        t.get('provider', 'auto') != 'auto' or t.get('model', '')
        for t in aux_tasks.values()
    )
    if has_overrides:
        print()
        print(color("◆ Modelos auxiliares (overrides)", Colors.CYAN, Colors.BOLD))
        for label, task_cfg in aux_tasks.items():
            prov = task_cfg.get('provider', 'auto')
            mdl = task_cfg.get('model', '')
            if prov != 'auto' or mdl:
                parts = [f"proveedor={prov}"]
                if mdl:
                    parts.append(f"modelo={mdl}")
                print(f"  {label:12s}  {', '.join(parts)}")
    
    # Mensajería
    print()
    print(color("◆ Plataformas de mensajería", Colors.CYAN, Colors.BOLD))
    
    telegram_token = get_env_value('TELEGRAM_BOT_TOKEN')
    discord_token = get_env_value('DISCORD_BOT_TOKEN')
    
    print(f"  Telegram:     {'configurado' if telegram_token else color('no configurado', Colors.DIM)}")
    print(f"  Discord:      {'configurado' if discord_token else color('no configurado', Colors.DIM)}")
    
    print()
    print(color("─" * 60, Colors.DIM))
    print(color("  hermes config edit     # Editar archivo de configuración", Colors.DIM))
    print(color("  hermes config set KEY VALUE", Colors.DIM))
    print(color("  hermes setup           # Ejecutar asistente de configuración", Colors.DIM))
    print()


def edit_config():
    """Abre el archivo de configuración en el editor del usuario."""
    config_path = get_config_path()
    
    # Asegurarse de que exista config
    if not config_path.exists():
        save_config(DEFAULT_CONFIG)
        print(f"Se creó {config_path}")
    
    # Buscar editor
    editor = os.getenv('EDITOR') or os.getenv('VISUAL')
    
    if not editor:
        # Probar editores comunes
        for cmd in ['nano', 'vim', 'vi', 'code', 'notepad']:
            import shutil
            if shutil.which(cmd):
                editor = cmd
                break
    
    if not editor:
        print(f"No editor found. Config file is at:")
        print(f"  {config_path}")
        return
    
    print(f"Abriendo {config_path} en {editor}...")
    subprocess.run([editor, str(config_path)])


def set_config_value(key: str, value: str):
    """Establece un valor de configuración."""
    # Comprobar si es una API key (va a .env)
    api_keys = [
        'OPENROUTER_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'VOICE_TOOLS_OPENAI_KEY',
        'FIRECRAWL_API_KEY', 'FIRECRAWL_API_URL', 'BROWSERBASE_API_KEY', 'BROWSERBASE_PROJECT_ID',
        'FAL_KEY', 'TELEGRAM_BOT_TOKEN', 'DISCORD_BOT_TOKEN',
        'TERMINAL_SSH_HOST', 'TERMINAL_SSH_USER', 'TERMINAL_SSH_KEY',
        'SUDO_PASSWORD', 'SLACK_BOT_TOKEN', 'SLACK_APP_TOKEN',
        'GITHUB_TOKEN', 'HONCHO_API_KEY', 'WANDB_API_KEY',
        'TINKER_API_KEY',
    ]
    
    if key.upper() in api_keys or key.upper().endswith('_API_KEY') or key.upper().endswith('_TOKEN') or key.upper().startswith('TERMINAL_SSH'):
        save_env_value(key.upper(), value)
        print(f"✓ Se estableció {key} en {get_env_path()}")
        return
    
    # En caso contrario, va a config.yaml
    # Leer la config de usuario en bruto (sin fusionar con defaults) para evitar
    # volcar todos los valores por defecto al archivo
    config_path = get_config_path()
    user_config = {}
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                user_config = yaml.safe_load(f) or {}
        except Exception:
            user_config = {}
    
    # Manejar claves anidadas (p. ej. "tts.provider")
    parts = key.split('.')
    current = user_config
    
    for part in parts[:-1]:
        if part not in current or not isinstance(current.get(part), dict):
            current[part] = {}
        current = current[part]
    
    # Convertir value al tipo apropiado
    if value.lower() in ('true', 'yes', 'on'):
        value = True
    elif value.lower() in ('false', 'no', 'off'):
        value = False
    elif value.isdigit():
        value = int(value)
    elif value.replace('.', '', 1).isdigit():
        value = float(value)
    
    current[parts[-1]] = value
    
    # Escribir solo la config de usuario (no todos los defaults fusionados)
    ensure_hermes_home()
    with open(config_path, 'w', encoding="utf-8") as f:
        yaml.dump(user_config, f, default_flow_style=False, sort_keys=False)
    
    # Mantener .env en sync para claves que terminal_tool lee directamente de vars de entorno.
    # config.yaml es la fuente principal, pero terminal_tool solo lee TERMINAL_ENV, etc.
    _config_to_env_sync = {
        "terminal.backend": "TERMINAL_ENV",
        "terminal.docker_image": "TERMINAL_DOCKER_IMAGE",
        "terminal.singularity_image": "TERMINAL_SINGULARITY_IMAGE",
        "terminal.modal_image": "TERMINAL_MODAL_IMAGE",
        "terminal.daytona_image": "TERMINAL_DAYTONA_IMAGE",
        "terminal.cwd": "TERMINAL_CWD",
        "terminal.timeout": "TERMINAL_TIMEOUT",
        "terminal.sandbox_dir": "TERMINAL_SANDBOX_DIR",
    }
    if key in _config_to_env_sync:
        save_env_value(_config_to_env_sync[key], str(value))

    print(f"✓ Se estableció {key} = {value} en {config_path}")


# =============================================================================
# Command handler
# =============================================================================

def config_command(args):
    """Gestiona los subcomandos de config."""
    subcmd = getattr(args, 'config_command', None)
    
    if subcmd is None or subcmd == "show":
        show_config()
    
    elif subcmd == "edit":
        edit_config()
    
    elif subcmd == "set":
        key = getattr(args, 'key', None)
        value = getattr(args, 'value', None)
        if not key or not value:
            print("Uso: hermes config set KEY VALUE")
            print()
            print("Ejemplos:")
            print("  hermes config set model anthropic/claude-sonnet-4")
            print("  hermes config set terminal.backend docker")
            print("  hermes config set OPENROUTER_API_KEY sk-or-...")
            sys.exit(1)
        set_config_value(key, value)
    
    elif subcmd == "path":
        print(get_config_path())
    
    elif subcmd == "env-path":
        print(get_env_path())
    
    elif subcmd == "migrate":
        print()
        print(color("🔄 Comprobando configuración para actualizaciones...", Colors.CYAN, Colors.BOLD))
        print()
        
        # Comprobar qué falta
        missing_env = get_missing_env_vars(required_only=False)
        missing_config = get_missing_config_fields()
        current_ver, latest_ver = check_config_version()
        
        if not missing_env and not missing_config and current_ver >= latest_ver:
            print(color("✓ ¡La configuración está actualizada!", Colors.GREEN))
            print()
            return
        
        # Mostrar qué necesita actualizarse
        if current_ver < latest_ver:
            print(f"  Versión de config: {current_ver} → {latest_ver}")
        
        if missing_config:
            print(f"\n  {len(missing_config)} nuevas opciones de config se añadirán con valores por defecto")
        
        required_missing = [v for v in missing_env if v.get("is_required")]
        optional_missing = [
            v for v in missing_env
            if not v.get("is_required") and not v.get("advanced")
        ]
        
        if required_missing:
            print(f"\n  ⚠️  Faltan {len(required_missing)} API key(s) requeridas:")
            for var in required_missing:
                print(f"     • {var['name']}")
        
        if optional_missing:
            print(f"\n  ℹ️  {len(optional_missing)} API key(s) opcionales sin configurar:")
            for var in optional_missing:
                tools = var.get("tools", [])
                tools_str = f" (enables: {', '.join(tools[:2])})" if tools else ""
                print(f"     • {var['name']}{tools_str}")
        
        print()
        
        # Run migration
        results = migrate_config(interactive=True, quiet=False)
        
        print()
        if results["env_added"] or results["config_added"]:
            print(color("✓ ¡Configuración actualizada!", Colors.GREEN))
        
        if results["warnings"]:
            print()
            for warning in results["warnings"]:
                print(color(f"  ⚠️  {warning}", Colors.YELLOW))
        
        print()
    
    elif subcmd == "check":
        # Non-interactive check for what's missing
        print()
        print(color("📋 Estado de la configuración", Colors.CYAN, Colors.BOLD))
        print()
        
        current_ver, latest_ver = check_config_version()
        if current_ver >= latest_ver:
            print(f"  Versión de config: {current_ver} ✓")
        else:
            print(color(f"  Versión de config: {current_ver} → {latest_ver} (actualización disponible)", Colors.YELLOW))
        
        print()
        print(color("  Requeridas:", Colors.BOLD))
        for var_name in REQUIRED_ENV_VARS:
            if get_env_value(var_name):
                print(f"    ✓ {var_name}")
            else:
                print(color(f"    ✗ {var_name} (falta)", Colors.RED))
        
        print()
        print(color("  Opcionales:", Colors.BOLD))
        for var_name, info in OPTIONAL_ENV_VARS.items():
            if get_env_value(var_name):
                print(f"    ✓ {var_name}")
            else:
                tools = info.get("tools", [])
                tools_str = f" → {', '.join(tools[:2])}" if tools else ""
                print(color(f"    ○ {var_name}{tools_str}", Colors.DIM))
        
        missing_config = get_missing_config_fields()
        if missing_config:
            print()
            print(color(f"  {len(missing_config)} nuevas opciones de config disponibles", Colors.YELLOW))
            print(f"    Ejecuta 'hermes config migrate' para añadirlas")
        
        print()
    
    else:
        print(f"Comando de config desconocido: {subcmd}")
        print()
        print("Comandos disponibles:")
        print("  hermes config           Mostrar configuración actual")
        print("  hermes config edit      Abrir configuración en el editor")
        print("  hermes config set K V   Establecer un valor de config")
        print("  hermes config check     Comprobar config faltante/desactualizada")
        print("  hermes config migrate   Actualizar config con nuevas opciones")
        print("  hermes config path      Mostrar ruta del archivo de config")
        print("  hermes config env-path  Mostrar ruta del archivo .env")
        sys.exit(1)
