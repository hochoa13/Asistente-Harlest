"""
Subcomando gateway para la CLI de Hermes.

Maneja: hermes gateway [run|start|stop|restart|status|install|uninstall|setup]
"""

import asyncio
import os
import signal
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

from hermes_cli.config import get_env_value, save_env_value
from hermes_cli.setup import (
    print_header, print_info, print_success, print_warning, print_error,
    prompt, prompt_choice, prompt_yes_no,
)
from hermes_cli.colors import Colors, color


# =============================================================================
# Gestión de procesos (para ejecuciones manuales del gateway)
# =============================================================================

def find_gateway_pids() -> list:
    """Encontrar los PIDs de procesos del gateway en ejecución."""
    pids = []
    patterns = [
        "hermes_cli.main gateway",
        "hermes gateway",
        "gateway/run.py",
    ]

    try:
        if is_windows():
            # Windows: usar wmic para buscar en las líneas de comando
            result = subprocess.run(
                ["wmic", "process", "get", "ProcessId,CommandLine", "/FORMAT:LIST"],
                capture_output=True, text=True
            )
            # Analizar la salida LIST de WMIC: bloques de "CommandLine=...\nProcessId=...\n"
            current_cmd = ""
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line.startswith("CommandLine="):
                    current_cmd = line[len("CommandLine="):]
                elif line.startswith("ProcessId="):
                    pid_str = line[len("ProcessId="):]
                    if any(p in current_cmd for p in patterns):
                        try:
                            pid = int(pid_str)
                            if pid != os.getpid() and pid not in pids:
                                pids.append(pid)
                        except ValueError:
                            pass
                    current_cmd = ""
        else:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True
            )
            for line in result.stdout.split('\n'):
                # Omitir grep y el proceso actual
                if 'grep' in line or str(os.getpid()) in line:
                    continue
                for pattern in patterns:
                    if pattern in line:
                        parts = line.split()
                        if len(parts) > 1:
                            try:
                                pid = int(parts[1])
                                if pid not in pids:
                                    pids.append(pid)
                            except ValueError:
                                continue
                        break
    except Exception:
        pass

    return pids


def kill_gateway_processes(force: bool = False) -> int:
    """Mata cualquier proceso del gateway en ejecución. Devuelve la cantidad terminada."""
    pids = find_gateway_pids()
    killed = 0
    
    for pid in pids:
        try:
            if force and not is_windows():
                os.kill(pid, signal.SIGKILL)
            else:
                os.kill(pid, signal.SIGTERM)
            killed += 1
        except ProcessLookupError:
            # El proceso ya no existe
            pass
        except PermissionError:
            print(f"⚠ Permiso denegado para terminar el PID {pid}")
    
    return killed


def is_linux() -> bool:
    return sys.platform.startswith('linux')

def is_macos() -> bool:
    return sys.platform == 'darwin'

def is_windows() -> bool:
    return sys.platform == 'win32'


# =============================================================================
# Configuración del servicio
# =============================================================================

SERVICE_NAME = "hermes-gateway"
SERVICE_DESCRIPTION = "Gateway de Hermes Agent - Integración con plataformas de mensajería"

def get_systemd_unit_path() -> Path:
    return Path.home() / ".config" / "systemd" / "user" / f"{SERVICE_NAME}.service"

def get_launchd_plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / "ai.hermes.gateway.plist"

def get_python_path() -> str:
    if is_windows():
        venv_python = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"
    else:
        venv_python = PROJECT_ROOT / "venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable

def get_hermes_cli_path() -> str:
    """Obtener la ruta hacia la CLI de Hermes."""
    # Check if installed via pip
    import shutil
    hermes_bin = shutil.which("hermes")
    if hermes_bin:
        return hermes_bin
    
    # Fallback to direct module execution
    return f"{get_python_path()} -m hermes_cli.main"


# =============================================================================
# Systemd (Linux)
# =============================================================================

def generate_systemd_unit() -> str:
    import shutil
    python_path = get_python_path()
    working_dir = str(PROJECT_ROOT)
    venv_dir = str(PROJECT_ROOT / "venv")
    venv_bin = str(PROJECT_ROOT / "venv" / "bin")
    node_bin = str(PROJECT_ROOT / "node_modules" / ".bin")

    # Build a PATH that includes the venv, node_modules, and standard system dirs
    sane_path = f"{venv_bin}:{node_bin}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    
    hermes_cli = shutil.which("hermes") or f"{python_path} -m hermes_cli.main"
    return f"""[Unit]
Description={SERVICE_DESCRIPTION}
After=network.target

[Service]
Type=simple
ExecStart={python_path} -m hermes_cli.main gateway run --replace
ExecStop={hermes_cli} gateway stop
WorkingDirectory={working_dir}
Environment="PATH={sane_path}"
Environment="VIRTUAL_ENV={venv_dir}"
Restart=on-failure
RestartSec=10
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=15
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
"""

def systemd_install(force: bool = False):
    unit_path = get_systemd_unit_path()
    
    if unit_path.exists() and not force:
        print(f"El servicio ya está instalado en: {unit_path}")
        print("Usa --force para reinstalar")
        return
    
    unit_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Instalando servicio de systemd en: {unit_path}")
    unit_path.write_text(generate_systemd_unit())
    
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "--user", "enable", SERVICE_NAME], check=True)
    
    print()
    print("✓ ¡Servicio instalado y habilitado!")
    print()
    print("Siguientes pasos:")
    print(f"  hermes gateway start              # Iniciar el servicio")
    print(f"  hermes gateway status             # Verificar estado")
    print(f"  journalctl --user -u {SERVICE_NAME} -f  # Ver registros")
    print()
    print("Para habilitar lingering (que siga ejecutándose después de cerrar sesión):")
    print("  sudo loginctl enable-linger $USER")

def systemd_uninstall():
    subprocess.run(["systemctl", "--user", "stop", SERVICE_NAME], check=False)
    subprocess.run(["systemctl", "--user", "disable", SERVICE_NAME], check=False)
    
    unit_path = get_systemd_unit_path()
    if unit_path.exists():
        unit_path.unlink()
        print(f"✓ Eliminado {unit_path}")
    
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    print("✓ Servicio desinstalado")

def systemd_start():
    subprocess.run(["systemctl", "--user", "start", SERVICE_NAME], check=True)
    print("✓ Servicio iniciado")

def systemd_stop():
    subprocess.run(["systemctl", "--user", "stop", SERVICE_NAME], check=True)
    print("✓ Servicio detenido")

def systemd_restart():
    subprocess.run(["systemctl", "--user", "restart", SERVICE_NAME], check=True)
    print("✓ Servicio reiniciado")

def systemd_status(deep: bool = False):
    # Check if service unit file exists
    unit_path = get_systemd_unit_path()
    if not unit_path.exists():
        print("✗ El servicio del gateway no está instalado")
        print("  Ejecuta: hermes gateway install")
        return
    
    # Show detailed status first
    subprocess.run(
        ["systemctl", "--user", "status", SERVICE_NAME, "--no-pager"],
        capture_output=False
    )
    
    # Check if service is active
    result = subprocess.run(
        ["systemctl", "--user", "is-active", SERVICE_NAME],
        capture_output=True,
        text=True
    )
    
    status = result.stdout.strip()
    
    if status == "active":
        print("✓ El servicio del gateway está en ejecución")
    else:
        print("✗ El servicio del gateway está detenido")
        print("  Ejecuta: hermes gateway start")
    
    if deep:
        print()
        print("Registros recientes:")
        subprocess.run([
            "journalctl", "--user", "-u", SERVICE_NAME,
            "-n", "20", "--no-pager"
        ])


# =============================================================================
# Launchd (macOS)
# =============================================================================

def generate_launchd_plist() -> str:
    python_path = get_python_path()
    working_dir = str(PROJECT_ROOT)
    log_dir = Path.home() / ".hermes" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.hermes.gateway</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>-m</string>
        <string>hermes_cli.main</string>
        <string>gateway</string>
        <string>run</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>{working_dir}</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    
    <key>StandardOutPath</key>
    <string>{log_dir}/gateway.log</string>
    
    <key>StandardErrorPath</key>
    <string>{log_dir}/gateway.error.log</string>
</dict>
</plist>
"""

def launchd_install(force: bool = False):
    plist_path = get_launchd_plist_path()
    
    if plist_path.exists() and not force:
        print(f"El servicio ya está instalado en: {plist_path}")
        print("Usa --force para reinstalar")
        return
    
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Instalando servicio launchd en: {plist_path}")
    plist_path.write_text(generate_launchd_plist())
    
    subprocess.run(["launchctl", "load", str(plist_path)], check=True)
    
    print()
    print("✓ ¡Servicio instalado y cargado!")
    print()
    print("Siguientes pasos:")
    print("  hermes gateway status             # Verificar estado")
    print("  tail -f ~/.hermes/logs/gateway.log  # Ver registros")

def launchd_uninstall():
    plist_path = get_launchd_plist_path()
    subprocess.run(["launchctl", "unload", str(plist_path)], check=False)
    
    if plist_path.exists():
        plist_path.unlink()
        print(f"✓ Eliminado {plist_path}")
    
    print("✓ Servicio desinstalado")

def launchd_start():
    subprocess.run(["launchctl", "start", "ai.hermes.gateway"], check=True)
    print("✓ Servicio iniciado")

def launchd_stop():
    subprocess.run(["launchctl", "stop", "ai.hermes.gateway"], check=True)
    print("✓ Servicio detenido")

def launchd_restart():
    launchd_stop()
    launchd_start()

def launchd_status(deep: bool = False):
    result = subprocess.run(
        ["launchctl", "list", "ai.hermes.gateway"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✓ El servicio del gateway está cargado")
        print(result.stdout)
    else:
        print("✗ El servicio del gateway no está cargado")
    
    if deep:
        log_file = Path.home() / ".hermes" / "logs" / "gateway.log"
        if log_file.exists():
            print()
            print("Registros recientes:")
            subprocess.run(["tail", "-20", str(log_file)])


# =============================================================================
# Gateway Runner
# =============================================================================

def run_gateway(verbose: bool = False, replace: bool = False):
    """Ejecuta el gateway en primer plano.
    
    Args:
        verbose: Habilita la salida detallada de registros.
        replace: Si es True, mata cualquier instancia existente del gateway
                 antes de iniciar. Esto evita bucles de reinicio de systemd
                 cuando el proceso antiguo aún no ha terminado.
    """
    sys.path.insert(0, str(PROJECT_ROOT))
    
    from gateway.run import start_gateway
    
    print("┌─────────────────────────────────────────────────────────┐")
    print("│           ⚕ Iniciando Hermes Gateway...                │")
    print("├─────────────────────────────────────────────────────────┤")
    print("│  Plataformas de mensajería + programador (cron)        │")
    print("│  Pulsa Ctrl+C para detener                             │")
    print("└─────────────────────────────────────────────────────────┘")
    print()
    
    # Exit with code 1 if gateway fails to connect any platform,
    # so systemd Restart=on-failure will retry on transient errors
    success = asyncio.run(start_gateway(replace=replace))
    if not success:
        sys.exit(1)


# =============================================================================
# Gateway Setup (Interactive Messaging Platform Configuration)
# =============================================================================

# Configuración por plataforma: cada entrada define las variables de entorno, instrucciones de setup,
# y prompts necesarios para configurar una plataforma de mensajería.
_PLATFORMS = [
    {
        "key": "telegram",
        "label": "Telegram",
        "emoji": "📱",
        "token_var": "TELEGRAM_BOT_TOKEN",
        "setup_instructions": [
            "1. Abre Telegram y envía un mensaje a @BotFather",
            "2. Envía /newbot y sigue las instrucciones para crear tu bot",
            "3. Copia el token del bot que te da BotFather",
            "4. Para encontrar tu ID de usuario: envía un mensaje a @userinfobot — te responde con tu ID numérico",
        ],
        "vars": [
            {"name": "TELEGRAM_BOT_TOKEN", "prompt": "Token del bot", "password": True,
             "help": "Pega el token de @BotFather (paso 3 arriba)."},
            {"name": "TELEGRAM_ALLOWED_USERS", "prompt": "IDs de usuarios permitidos (separados por comas)", "password": False,
             "is_allowlist": True,
             "help": "Pega tu ID de usuario del paso 4 arriba."},
            {"name": "TELEGRAM_HOME_CHANNEL", "prompt": "ID del canal principal (para entrega de cron/notificaciones, o vacío para configurar después con /set-home)", "password": False,
             "help": "Para DMs, este es tu ID de usuario. Puedes configurarlo después escribiendo /set-home en el chat."},
        ],
    },
    {
        "key": "discord",
        "label": "Discord",
        "emoji": "💬",
        "token_var": "DISCORD_BOT_TOKEN",
        "setup_instructions": [
            "1. Ve a https://discord.com/developers/applications → Nueva Aplicación",
            "2. Ve a Bot → Reestablecer Token → copia el token del bot",
            "3. Habilita: Bot → Intentos de Pasarela Privilegiados → Intención de Contenido de Mensajes",
            "4. Invita el bot a tu servidor:",
            "   OAuth2 → Generador de URL → marca AMBOS alcances:",
            "     - bot",
            "     - applications.commands  (¡requerido para comandos de barra!)",
            "   Permisos del Bot: Enviar Mensajes, Leer Historial de Mensajes, Adjuntar Archivos",
            "   Copia la URL y ábrela en tu navegador para invitar.",
            "5. Obtén tu ID de usuario: habilita Modo de Desarrollador en la configuración de Discord,",
            "   luego haz clic derecho en tu nombre → Copiar ID",
        ],
        "vars": [
            {"name": "DISCORD_BOT_TOKEN", "prompt": "Token del bot", "password": True,
             "help": "Pega el token del paso 2 arriba."},
            {"name": "DISCORD_ALLOWED_USERS", "prompt": "IDs de usuario permitidos o nombres de usuario (separados por comas)", "password": False,
             "is_allowlist": True,
             "help": "Pega tu ID de usuario del paso 5 arriba."},
            {"name": "DISCORD_HOME_CHANNEL", "prompt": "ID del canal principal (para entrega de cron/notificaciones, o vacío para configurar después con /set-home)", "password": False,
             "help": "Haz clic derecho en un canal → Copiar ID del Canal (requiere Modo de Desarrollador)."},
        ],
    },
    {
        "key": "slack",
        "label": "Slack",
        "emoji": "💼",
        "token_var": "SLACK_BOT_TOKEN",
        "setup_instructions": [
            "1. Ve a https://api.slack.com/apps → Crear Nueva Aplicación → Desde Cero",
            "2. Habilita Modo Socket: Configuración → Modo Socket → Habilitar",
            "   Crea un Token a Nivel de Aplicación con alcance: connections:write → copia el token xapp-...",
            "3. Agrega Alcances de Token del Bot: Características → OAuth Y Permisos → Alcances",
            "   Requeridos: chat:write, app_mentions:read, channels:history, channels:read,",
            "   groups:history, im:history, im:read, im:write, users:read, files:write",
            "4. Suscríbete a Eventos: Características → Suscripciones de Eventos → Habilitar",
            "   Eventos requeridos: message.im, message.channels, app_mention",
            "   Opcional: message.groups (para canales privados)",
            "   ⚠ ¡Sin message.channels el bot SOLO funcionará en DMs!",
            "5. Instala en el Area de Trabajo: Configuración → Instalar Aplicación → copia el token xoxb-...",
            "6. Reinstala la aplicación después de cambios en alcances o eventos",
            "7. Encuentra tu ID de usuario: haz clic en tu perfil → tres puntos → Copiar ID de Miembro",
            "8. Invita el bot a canales: /invite @TuBot",
        ],
        "vars": [
            {"name": "SLACK_BOT_TOKEN", "prompt": "Token del Bot (xoxb-...)", "password": True,
             "help": "Pega el token del bot del paso 3 arriba."},
            {"name": "SLACK_APP_TOKEN", "prompt": "Token de la Aplicación (xapp-...)", "password": True,
             "help": "Pega el token a nivel de aplicación del paso 4 arriba."},
            {"name": "SLACK_ALLOWED_USERS", "prompt": "IDs de usuario permitidos (separados por comas)", "password": False,
             "is_allowlist": True,
             "help": "Pega tu ID de miembro del paso 7 arriba."},
        ],
    },
    {
        "key": "whatsapp",
        "label": "WhatsApp",
        "emoji": "📲",
        "token_var": "WHATSAPP_ENABLED",
    },
    {
        "key": "signal",
        "label": "Signal",
        "emoji": "📡",
        "token_var": "SIGNAL_HTTP_URL",
    },
    {
        "key": "email",
        "label": "Correo Electrónico",
        "emoji": "📧",
        "token_var": "EMAIL_ADDRESS",
        "setup_instructions": [
            "1. Usa una cuenta de correo dedicada para tu agente Hermes",
            "2. Para Gmail: habilita 2FA, luego crea una Contraseña de Aplicación en",
            "   https://myaccount.google.com/apppasswords",
            "3. Para otros proveedores: usa tu contraseña de correo o contraseña específica de la app",
            "4. IMAP debe estar habilitado en tu cuenta de correo",
        ],
        "vars": [
            {"name": "EMAIL_ADDRESS", "prompt": "Dirección de correo electrónico", "password": False,
             "help": "La dirección de correo que usará Hermes (p. ej., hermes@gmail.com)."},
            {"name": "EMAIL_PASSWORD", "prompt": "Contraseña del correo (o contraseña de app)", "password": True,
             "help": "Para Gmail, usa una Contraseña de Aplicación (no tu contraseña normal)."},
            {"name": "EMAIL_IMAP_HOST", "prompt": "Host IMAP", "password": False,
             "help": "p. ej., imap.gmail.com para Gmail, outlook.office365.com para Outlook."},
            {"name": "EMAIL_SMTP_HOST", "prompt": "Host SMTP", "password": False,
             "help": "p. ej., smtp.gmail.com para Gmail, smtp.office365.com para Outlook."},
            {"name": "EMAIL_ALLOWED_USERS", "prompt": "Correos electrónicos de remitentes permitidos (separados por comas)", "password": False,
             "is_allowlist": True,
             "help": "Solo se procesarán correos de estas direcciones."},
        ],
    },
]


def _platform_status(platform: dict) -> str:
    """Devuelve una cadena de estado de texto plano para una plataforma.

    Devuelve texto sin color para que pueda ser integrado de forma segura en
    elementos de simple_term_menu (los códigos ANSI rompen el cálculo de ancho).
    """
    token_var = platform["token_var"]
    val = get_env_value(token_var)
    if token_var == "WHATSAPP_ENABLED":
        if val and val.lower() == "true":
            session_file = Path.home() / ".hermes" / "whatsapp" / "session" / "creds.json"
            if session_file.exists():
                return "configurado + emparejado"
            return "habilitado, no emparejado"
        return "no configurado"
    if platform.get("key") == "signal":
        account = get_env_value("SIGNAL_ACCOUNT")
        if val and account:
            return "configurado"
        if val or account:
            return "parcialmente configurado"
        return "no configurado"
    if platform.get("key") == "email":
        pwd = get_env_value("EMAIL_PASSWORD")
        imap = get_env_value("EMAIL_IMAP_HOST")
        smtp = get_env_value("EMAIL_SMTP_HOST")
        if all([val, pwd, imap, smtp]):
            return "configurado"
        if any([val, pwd, imap, smtp]):
            return "parcialmente configurado"
        return "no configurado"
    if val:
        return "configurado"
    return "no configurado"


def _setup_standard_platform(platform: dict):
    """Configuración interactiva para Telegram, Discord o Slack."""
    emoji = platform["emoji"]
    label = platform["label"]
    token_var = platform["token_var"]

    print()
    print(color(f"  ─── {emoji} {label} Setup ───", Colors.CYAN))

    # Mostrar instrucciones de configuración paso a paso si la plataforma las tiene
    instructions = platform.get("setup_instructions")
    if instructions:
        print()
        for line in instructions:
            print_info(f"  {line}")

    existing_token = get_env_value(token_var)
    if existing_token:
        print()
        print_success(f"{label} ya está configurado.")
        if not prompt_yes_no(f"  ¿Reconfigurar {label}?", False):
            return

    allowed_val_set = None  # Rastrear si el usuario configuró una lista blanca (para oferta de home channel)

    for var in platform["vars"]:
        print()
        print_info(f"  {var['help']}")
        existing = get_env_value(var["name"])
        if existing and var["name"] != token_var:
            print_info(f"  Actual: {existing}")

        # Los campos de lista blanca reciben manejo especial para el modelo de seguridad de denegación por defecto
        if var.get("is_allowlist"):
            print_info(f"  El gateway NIEGA a todos los usuarios por defecto por seguridad.")
            print_info(f"  Introduce IDs de usuario para crear una lista blanca, o déjalo vacío")
            print_info(f"  y se te preguntará sobre acceso abierto a continuación.")
            value = prompt(f"  {var['prompt']}", password=False)
            if value:
                cleaned = value.replace(" ", "")
                save_env_value(var["name"], cleaned)
                print_success(f"  Guardado — solo estos usuarios pueden interactuar con el bot.")
                allowed_val_set = cleaned
            else:
                # Sin lista blanca — preguntar sobre acceso abierto vs emparejamiento por DM
                print()
                access_choices = [
                    "Habilitar acceso abierto (cualquiera puede enviar mensajes al bot)",
                    "Usar emparejamiento por DM (usuarios desconocidos solicitan acceso, tú apruebas con 'hermes pairing approve')",
                    "Omitir por ahora (el bot negará a todos los usuarios hasta que se configure)",
                ]
                access_idx = prompt_choice("  ¿Cómo deben tratarse los usuarios no autorizados?", access_choices, 1)
                if access_idx == 0:
                    save_env_value("GATEWAY_ALLOW_ALL_USERS", "true")
                    print_warning("  Acceso abierto habilitado — ¡cualquiera puede usar tu bot!")
                elif access_idx == 1:
                    print_success("  Modo emparejamiento por DM — los usuarios recibirán un código para solicitar acceso.")
                    print_info("  Aprueba con: hermes pairing approve {platform} {code}")
                else:
                    print_info("  Omitido — configura más tarde con 'hermes gateway setup'")
            continue

        value = prompt(f"  {var['prompt']}", password=var.get("password", False))
        if value:
            save_env_value(var["name"], value)
            print_success(f"  Guardado {var['name']}")
        elif var["name"] == token_var:
            print_warning(f"  Omitido — {label} no funcionará sin esto.")
            return
        else:
            print_info(f"  Omitido (puede configurarse más tarde)")

    # Si se configuró una lista blanca y el canal principal no, ofrecer
    # reutilizar el primer ID de usuario (común para DMs de Telegram).
    home_var = f"{label.upper()}_HOME_CHANNEL"
    home_val = get_env_value(home_var)
    if allowed_val_set and not home_val and label == "Telegram":
        first_id = allowed_val_set.split(",")[0].strip()
        if first_id and prompt_yes_no(f"  ¿Usar tu ID de usuario ({first_id}) como canal principal?", True):
            save_env_value(home_var, first_id)
            print_success(f"  Canal principal configurado a {first_id}")

    print()
    print_success(f"¡{emoji} {label} configurado!")


def _setup_whatsapp():
    """Delegate to the existing WhatsApp setup flow."""
    from hermes_cli.main import cmd_whatsapp
    import argparse
    cmd_whatsapp(argparse.Namespace())


def _is_service_installed() -> bool:
    """Check if the gateway is installed as a system service."""
    if is_linux():
        return get_systemd_unit_path().exists()
    elif is_macos():
        return get_launchd_plist_path().exists()
    return False


def _is_service_running() -> bool:
    """Check if the gateway service is currently running."""
    if is_linux() and get_systemd_unit_path().exists():
        result = subprocess.run(
            ["systemctl", "--user", "is-active", SERVICE_NAME],
            capture_output=True, text=True
        )
        return result.stdout.strip() == "active"
    elif is_macos() and get_launchd_plist_path().exists():
        result = subprocess.run(
            ["launchctl", "list", "ai.hermes.gateway"],
            capture_output=True, text=True
        )
        return result.returncode == 0
    # Check for manual processes
    return len(find_gateway_pids()) > 0


def _setup_signal():
    """Configuración interactiva para el mensajero Signal."""
    import shutil

    print()
    print(color("  ─── Configuración de 📡 Signal ───", Colors.CYAN))

    existing_url = get_env_value("SIGNAL_HTTP_URL")
    existing_account = get_env_value("SIGNAL_ACCOUNT")
    if existing_url and existing_account:
        print()
        print_success("Signal ya está configurado.")
        if not prompt_yes_no("  ¿Reconfigurar Signal?", False):
            return

    # Check if signal-cli is available
    print()
    if shutil.which("signal-cli"):
        print_success("signal-cli encontrado en el PATH.")
    else:
        print_warning("signal-cli no se encontró en el PATH.")
        print_info("  Signal requiere signal-cli ejecutándose como demonio HTTP.")
        print_info("  Opciones de instalación:")
        print_info("    Linux:  sudo apt install signal-cli")
        print_info("            o descárgalo desde https://github.com/AsamK/signal-cli")
        print_info("    macOS:  brew install signal-cli")
        print_info("    Docker: bbernhard/signal-cli-rest-api")
        print()
        print_info("  Después de instalar, vincula tu cuenta y arranca el demonio:")
        print_info("    signal-cli link -n \"HermesAgent\"")
        print_info("    signal-cli --account +YOURNUMBER daemon --http 127.0.0.1:8080")
        print()

    # HTTP URL
    print()
    print_info("  Introduce la URL donde está ejecutándose el demonio HTTP de signal-cli.")
    default_url = existing_url or "http://127.0.0.1:8080"
    try:
        url = input(f"  URL HTTP [{default_url}]: ").strip() or default_url
    except (EOFError, KeyboardInterrupt):
        print("\n  Configuración cancelada.")
        return

    # Test connectivity
    print_info("  Probando la conexión...")
    try:
        import httpx
        resp = httpx.get(f"{url.rstrip('/')}/api/v1/check", timeout=10.0)
        if resp.status_code == 200:
            print_success("  ¡El demonio de signal-cli es accesible!")
        else:
            print_warning(f"  signal-cli respondió con el estado {resp.status_code}.")
            if not prompt_yes_no("  ¿Continuar de todos modos?", False):
                return
    except Exception as e:
        print_warning(f"  No se pudo contactar a signal-cli en {url}: {e}")
        if not prompt_yes_no("  ¿Guardar esta URL de todos modos? (puedes iniciar signal-cli más tarde)", True):
            return

    save_env_value("SIGNAL_HTTP_URL", url)

    # Account phone number
    print()
    print_info("  Introduce el número de teléfono de tu cuenta Signal en formato E.164.")
    print_info("  Ejemplo: +15551234567")
    default_account = existing_account or ""
    try:
        account = input(f"  Account number{f' [{default_account}]' if default_account else ''}: ").strip()
        if not account:
            account = default_account
    except (EOFError, KeyboardInterrupt):
        print("\n  Configuración cancelada.")
        return

    if not account:
        print_error("  Account number is required.")
        return

    save_env_value("SIGNAL_ACCOUNT", account)

    # Allowed users
    print()
    print_info("  El gateway NIEGA a todos los usuarios por defecto por seguridad.")
    print_info("  Introduce números de teléfono o UUIDs de usuarios permitidos (separados por comas).")
    existing_allowed = get_env_value("SIGNAL_ALLOWED_USERS") or ""
    default_allowed = existing_allowed or account
    try:
        allowed = input(f"  Allowed users [{default_allowed}]: ").strip() or default_allowed
    except (EOFError, KeyboardInterrupt):
        print("\n  Setup cancelled.")
        return

    save_env_value("SIGNAL_ALLOWED_USERS", allowed)

    # Group messaging
    print()
    if prompt_yes_no("  ¿Habilitar mensajería de grupo? (deshabilitado por defecto por seguridad)", False):
        print()
        print_info("  Introduce IDs de grupo a permitir, o * para todos los grupos.")
        existing_groups = get_env_value("SIGNAL_GROUP_ALLOWED_USERS") or ""
        try:
            groups = input(f"  Group IDs [{existing_groups or '*'}]: ").strip() or existing_groups or "*"
        except (EOFError, KeyboardInterrupt):
            print("\n  Setup cancelled.")
            return
        save_env_value("SIGNAL_GROUP_ALLOWED_USERS", groups)

    print()
    print_success("¡Signal configurado!")
    print_info(f"  URL: {url}")
    print_info(f"  Cuenta: {account}")
    print_info(f"  Autenticación por DM: vía SIGNAL_ALLOWED_USERS + emparejamiento por DM")
    print_info(f"  Grupos: {'habilitados' if get_env_value('SIGNAL_GROUP_ALLOWED_USERS') else 'deshabilitados'}")


def gateway_setup():
    """Configuración interactiva de plataformas de mensajería + servicio de gateway."""

    print()
    print(color("┌─────────────────────────────────────────────────────────┐", Colors.MAGENTA))
    print(color("│             ⚕ Configuración del Gateway               │", Colors.MAGENTA))
    print(color("├─────────────────────────────────────────────────────────┤", Colors.MAGENTA))
    print(color("│  Configura las plataformas de mensajería y el servicio │", Colors.MAGENTA))
    print(color("│  del gateway. Pulsa Ctrl+C en cualquier momento para   │", Colors.MAGENTA))
    print(color("│  salir.                                                 │", Colors.MAGENTA))
    print(color("└─────────────────────────────────────────────────────────┘", Colors.MAGENTA))

    # ── Gateway service status ──
    print()
    service_installed = _is_service_installed()
    service_running = _is_service_running()

    if service_installed and service_running:
        print_success("El servicio del gateway está instalado y en ejecución.")
    elif service_installed:
        print_warning("El servicio del gateway está instalado pero no se está ejecutando.")
        if prompt_yes_no("  ¿Iniciarlo ahora?", True):
            try:
                if is_linux():
                    systemd_start()
                elif is_macos():
                    launchd_start()
            except subprocess.CalledProcessError as e:
                print_error(f"  Error al iniciar: {e}")
    else:
        print_info("El servicio del gateway todavía no está instalado.")
        print_info("Se te ofrecerá instalarlo después de configurar las plataformas.")

    # ── Platform configuration loop ──
    while True:
        print()
        print_header("Plataformas de mensajería")

        menu_items = []
        for plat in _PLATFORMS:
            status = _platform_status(plat)
            menu_items.append(f"{plat['label']}  ({status})")
        menu_items.append("Listo")

        choice = prompt_choice("Selecciona una plataforma para configurar:", menu_items, len(menu_items) - 1)

        if choice == len(_PLATFORMS):
            break

        platform = _PLATFORMS[choice]

        if platform["key"] == "whatsapp":
            _setup_whatsapp()
        elif platform["key"] == "signal":
            _setup_signal()
        else:
            _setup_standard_platform(platform)

    # ── Post-setup: offer to install/restart gateway ──
    any_configured = any(
        bool(get_env_value(p["token_var"]))
        for p in _PLATFORMS
        if p["key"] != "whatsapp"
    ) or (get_env_value("WHATSAPP_ENABLED") or "").lower() == "true"

    if any_configured:
        print()
        print(color("─" * 58, Colors.DIM))
        service_installed = _is_service_installed()
        service_running = _is_service_running()

        if service_running:
            if prompt_yes_no("  ¿Reiniciar el gateway para aplicar cambios?", True):
                try:
                    if is_linux():
                        systemd_restart()
                    elif is_macos():
                        launchd_restart()
                    else:
                        kill_gateway_processes()
                        print_info("Inicia manualmente: hermes gateway")
                except subprocess.CalledProcessError as e:
                    print_error(f"  Error al reiniciar: {e}")
        elif service_installed:
            if prompt_yes_no("  ¿Iniciar el servicio del gateway?", True):
                try:
                    if is_linux():
                        systemd_start()
                    elif is_macos():
                        launchd_start()
                except subprocess.CalledProcessError as e:
                    print_error(f"  Error al iniciar: {e}")
        else:
            print()
            if is_linux() or is_macos():
                platform_name = "systemd" if is_linux() else "launchd"
                if prompt_yes_no(f"  ¿Instalar el gateway como servicio {platform_name}? (se ejecuta en segundo plano, inicia al arrancar)", True):
                    try:
                        force = False
                        if is_linux():
                            systemd_install(force)
                        else:
                            launchd_install(force)
                        print()
                        if prompt_yes_no("  ¿Iniciar el servicio ahora?", True):
                            try:
                                if is_linux():
                                    systemd_start()
                                else:
                                    launchd_start()
                            except subprocess.CalledProcessError as e:
                                print_error(f"  Error al iniciar: {e}")
                    except subprocess.CalledProcessError as e:
                        print_error(f"  Error al instalar: {e}")
                        print_info("  Puedes intentar manualmente: hermes gateway install")
                else:
                    print_info("  Puedes instalar después: hermes gateway install")
                    print_info("  O ejecutar en primer plano:  hermes gateway")
            else:
                print_info("  La instalación del servicio no es compatible con esta plataforma.")
                print_info("  Ejecuta en primer plano: hermes gateway")
    else:
        print()
        print_info("Ninguna plataforma configurada. Ejecuta 'hermes gateway setup' cuando esté listo.")

    print()


# =============================================================================
# Main Command Handler
# =============================================================================

def gateway_command(args):
    """Maneja subcomandos del gateway."""
    subcmd = getattr(args, 'gateway_command', None)
    
    # Default to run if no subcommand
    if subcmd is None or subcmd == "run":
        verbose = getattr(args, 'verbose', False)
        replace = getattr(args, 'replace', False)
        run_gateway(verbose, replace=replace)
        return

    if subcmd == "setup":
        gateway_setup()
        return

    # Comandos de gestión del servicio
    if subcmd == "install":
        force = getattr(args, 'force', False)
        if is_linux():
            systemd_install(force)
        elif is_macos():
            launchd_install(force)
        else:
            print("La instalación del servicio no es compatible con esta plataforma.")
            print("Ejecuta manualmente: hermes gateway run")
            sys.exit(1)
    
    elif subcmd == "uninstall":
        if is_linux():
            systemd_uninstall()
        elif is_macos():
            launchd_uninstall()
        else:
            print("No es compatible con esta plataforma.")
            sys.exit(1)
    
    elif subcmd == "start":
        if is_linux():
            systemd_start()
        elif is_macos():
            launchd_start()
        else:
            print("No es compatible con esta plataforma.")
            sys.exit(1)
    
    elif subcmd == "stop":
        # Try service first, fall back to killing processes directly
        service_available = False
        
        if is_linux() and get_systemd_unit_path().exists():
            try:
                systemd_stop()
                service_available = True
            except subprocess.CalledProcessError:
                pass  # Fall through to process kill
        elif is_macos() and get_launchd_plist_path().exists():
            try:
                launchd_stop()
                service_available = True
            except subprocess.CalledProcessError:
                pass
        
        if not service_available:
            # Termina los procesos del gateway directamente
            killed = kill_gateway_processes()
            if killed:
                print(f"✓ Detenido {killed} proceso(s) del gateway")
            else:
                print("✗ No se encontraron procesos del gateway")
    
    elif subcmd == "restart":
        # Try service first, fall back to killing and restarting
        service_available = False
        
        if is_linux() and get_systemd_unit_path().exists():
            try:
                systemd_restart()
                service_available = True
            except subprocess.CalledProcessError:
                pass
        elif is_macos() and get_launchd_plist_path().exists():
            try:
                launchd_restart()
                service_available = True
            except subprocess.CalledProcessError:
                pass
        
        if not service_available:
            # Reinicio manual: termina procesos existentes
            killed = kill_gateway_processes()
            if killed:
                print(f"✓ Detenido {killed} proceso(s) del gateway")
            
            import time
            time.sleep(2)
            
            # Inicia fresco
            print("Iniciando gateway...")
            run_gateway(verbose=False)
    
    elif subcmd == "status":
        deep = getattr(args, 'deep', False)
        
        # Check for service first
        if is_linux() and get_systemd_unit_path().exists():
            systemd_status(deep)
        elif is_macos() and get_launchd_plist_path().exists():
            launchd_status(deep)
        else:
            # Comprueba si hay procesos ejecutándose manualmente
            pids = find_gateway_pids()
            if pids:
                print(f"✓ El gateway está en ejecución (PID: {', '.join(map(str, pids))})")
                print("  (Ejecutándose manualmente, no como servicio del sistema)")
                print()
                print("Para instalar como servicio:")
                print("  hermes gateway install")
            else:
                print("✗ El gateway no está en ejecución")
                print()
                print("Para iniciar:")
                print("  hermes gateway          # Ejecutar en primer plano")
                print("  hermes gateway install  # Instalar como servicio")
