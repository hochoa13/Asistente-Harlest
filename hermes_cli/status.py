"""Comando de estado para el CLI de Hermes.

Muestra el estado de todos los componentes de Hermes Agent.
"""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

from hermes_cli.colors import Colors, color
from hermes_cli.config import get_env_path, get_env_value
from hermes_constants import OPENROUTER_MODELS_URL

def check_mark(ok: bool) -> str:
    if ok:
        return color("✓", Colors.GREEN)
    return color("✗", Colors.RED)

def redact_key(key: str) -> str:
    """Oculta parcialmente una API key para mostrarla en pantalla."""
    if not key:
        return "(no configurada)"
    if len(key) < 12:
        return "***"
    return key[:4] + "..." + key[-4:]


def _format_iso_timestamp(value) -> str:
    """Formatea timestamps ISO para el estado, convirtiendo a zona horaria local."""
    if not value or not isinstance(value, str):
        return "(unknown)"
    from datetime import datetime, timezone
    text = value.strip()
    if not text:
        return "(unknown)"
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return value
    return parsed.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def show_status(args):
    """Muestra el estado de todos los componentes de Hermes Agent."""
    show_all = getattr(args, 'all', False)
    deep = getattr(args, 'deep', False)
    
    print()
    print(color("┌─────────────────────────────────────────────────────────┐", Colors.CYAN))
    print(color("│                 ⚕ Estado de Hermes Agent               │", Colors.CYAN))
    print(color("└─────────────────────────────────────────────────────────┘", Colors.CYAN))
    
    # =========================================================================
    # Entorno
    # =========================================================================
    print()
    print(color("◆ Entorno", Colors.CYAN, Colors.BOLD))
    print(f"  Proyecto:     {PROJECT_ROOT}")
    print(f"  Python:       {sys.version.split()[0]}")
    
    env_path = get_env_path()
    print(f"  .env file:    {check_mark(env_path.exists())} {'existe' if env_path.exists() else 'no encontrado'}")
    
    # =========================================================================
    # API Keys
    # =========================================================================
    print()
    print(color("◆ API Keys", Colors.CYAN, Colors.BOLD))
    
    keys = {
        "OpenRouter": "OPENROUTER_API_KEY",
        "Anthropic": "ANTHROPIC_API_KEY", 
        "OpenAI": "OPENAI_API_KEY",
        "Z.AI/GLM": "GLM_API_KEY",
        "Kimi": "KIMI_API_KEY",
        "MiniMax": "MINIMAX_API_KEY",
        "MiniMax-CN": "MINIMAX_CN_API_KEY",
        "Firecrawl": "FIRECRAWL_API_KEY",
        "Browserbase": "BROWSERBASE_API_KEY",  # Optional — local browser works without this
        "FAL": "FAL_KEY",
        "Tinker": "TINKER_API_KEY",
        "WandB": "WANDB_API_KEY",
        "ElevenLabs": "ELEVENLABS_API_KEY",
        "GitHub": "GITHUB_TOKEN",
    }
    
    for name, env_var in keys.items():
        value = get_env_value(env_var) or ""
        has_key = bool(value)
        display = redact_key(value) if not show_all else value
        print(f"  {name:<12}  {check_mark(has_key)} {display}")

    # =========================================================================
    # Proveedores de autenticación (OAuth)
    # =========================================================================
    print()
    print(color("◆ Auth Providers", Colors.CYAN, Colors.BOLD))

    try:
        from hermes_cli.auth import get_nous_auth_status, get_codex_auth_status
        nous_status = get_nous_auth_status()
        codex_status = get_codex_auth_status()
    except Exception:
        nous_status = {}
        codex_status = {}

    nous_logged_in = bool(nous_status.get("logged_in"))
    print(
        f"  {'Nous Portal':<12}  {check_mark(nous_logged_in)} "
        f"{'sesión iniciada' if nous_logged_in else 'sin sesión (ejecuta: hermes model)'}"
    )
    if nous_logged_in:
        portal_url = nous_status.get("portal_base_url") or "(unknown)"
        access_exp = _format_iso_timestamp(nous_status.get("access_expires_at"))
        key_exp = _format_iso_timestamp(nous_status.get("agent_key_expires_at"))
        refresh_label = "yes" if nous_status.get("has_refresh_token") else "no"
        print(f"    Portal URL: {portal_url}")
        print(f"    Access exp: {access_exp}")
        print(f"    Key exp:    {key_exp}")
        print(f"    Refresh:    {refresh_label}")

    codex_logged_in = bool(codex_status.get("logged_in"))
    print(
        f"  {'OpenAI Codex':<12}  {check_mark(codex_logged_in)} "
        f"{'sesión iniciada' if codex_logged_in else 'sin sesión (ejecuta: hermes model)'}"
    )
    codex_auth_file = codex_status.get("auth_store")
    if codex_auth_file:
        print(f"    Auth file:  {codex_auth_file}")
    codex_last_refresh = _format_iso_timestamp(codex_status.get("last_refresh"))
    if codex_status.get("last_refresh"):
        print(f"    Refreshed:  {codex_last_refresh}")
    if codex_status.get("error") and not codex_logged_in:
        print(f"    Error:      {codex_status.get('error')}")

    # =========================================================================
    # Proveedores por API key
    # =========================================================================
    print()
    print(color("◆ API-Key Providers", Colors.CYAN, Colors.BOLD))

    apikey_providers = {
        "Z.AI / GLM":       ("GLM_API_KEY", "ZAI_API_KEY", "Z_AI_API_KEY"),
        "Kimi / Moonshot":  ("KIMI_API_KEY",),
        "MiniMax":          ("MINIMAX_API_KEY",),
        "MiniMax (China)":  ("MINIMAX_CN_API_KEY",),
    }
    for pname, env_vars in apikey_providers.items():
        key_val = ""
        for ev in env_vars:
            key_val = get_env_value(ev) or ""
            if key_val:
                break
        configured = bool(key_val)
        label = "configurado" if configured else "no configurado (ejecuta: hermes model)"
        print(f"  {pname:<16} {check_mark(configured)} {label}")

    # =========================================================================
    # Configuración del terminal
    # =========================================================================
    print()
    print(color("◆ Backend de terminal", Colors.CYAN, Colors.BOLD))
    
    terminal_env = os.getenv("TERMINAL_ENV", "")
    if not terminal_env:
        # Usar el valor del archivo de config cuando la variable de entorno no está definida
        # (hermes status no pasa por la carga de config de cli.py)
        try:
            from hermes_cli.config import load_config
            _cfg = load_config()
            terminal_env = _cfg.get("terminal", {}).get("backend", "local")
        except Exception:
            terminal_env = "local"
    print(f"  Backend:      {terminal_env}")
    
    if terminal_env == "ssh":
        ssh_host = os.getenv("TERMINAL_SSH_HOST", "")
        ssh_user = os.getenv("TERMINAL_SSH_USER", "")
        print(f"  SSH Host:     {ssh_host or '(no configurado)'}")
        print(f"  SSH User:     {ssh_user or '(no configurado)'}")
    elif terminal_env == "docker":
        docker_image = os.getenv("TERMINAL_DOCKER_IMAGE", "python:3.11-slim")
        print(f"  Docker Image: {docker_image}")
    elif terminal_env == "daytona":
        daytona_image = os.getenv("TERMINAL_DAYTONA_IMAGE", "nikolaik/python-nodejs:python3.11-nodejs20")
        print(f"  Daytona Image: {daytona_image}")
    
    sudo_password = os.getenv("SUDO_PASSWORD", "")
    print(f"  Sudo:         {check_mark(bool(sudo_password))} {'habilitado' if sudo_password else 'deshabilitado'}")
    
    # =========================================================================
    # Plataformas de mensajería
    # =========================================================================
    print()
    print(color("◆ Messaging Platforms", Colors.CYAN, Colors.BOLD))
    
    platforms = {
        "Telegram": ("TELEGRAM_BOT_TOKEN", "TELEGRAM_HOME_CHANNEL"),
        "Discord": ("DISCORD_BOT_TOKEN", "DISCORD_HOME_CHANNEL"),
        "WhatsApp": ("WHATSAPP_ENABLED", None),
        "Signal": ("SIGNAL_HTTP_URL", "SIGNAL_HOME_CHANNEL"),
        "Slack": ("SLACK_BOT_TOKEN", None),
        "Email": ("EMAIL_ADDRESS", "EMAIL_HOME_ADDRESS"),
    }
    
    for name, (token_var, home_var) in platforms.items():
        token = os.getenv(token_var, "")
        has_token = bool(token)
        
        home_channel = ""
        if home_var:
            home_channel = os.getenv(home_var, "")
        
        status = "configurado" if has_token else "no configurado"
        if home_channel:
            status += f" (home: {home_channel})"
        
        print(f"  {name:<12}  {check_mark(has_token)} {status}")
    
    # =========================================================================
    # Estado del Gateway
    # =========================================================================
    print()
    print(color("◆ Gateway Service", Colors.CYAN, Colors.BOLD))
    
    if sys.platform.startswith('linux'):
        result = subprocess.run(
            ["systemctl", "--user", "is-active", "hermes-gateway"],
            capture_output=True,
            text=True
        )
        is_active = result.stdout.strip() == "active"
        print(f"  Status:       {check_mark(is_active)} {'ejecutándose' if is_active else 'detenido'}")
        print(f"  Manager:      systemd (usuario)")
        
    elif sys.platform == 'darwin':
        result = subprocess.run(
            ["launchctl", "list", "ai.hermes.gateway"],
            capture_output=True,
            text=True
        )
        is_loaded = result.returncode == 0
        print(f"  Status:       {check_mark(is_loaded)} {'cargado' if is_loaded else 'no cargado'}")
        print(f"  Manager:      launchd")
    else:
        print(f"  Status:       {color('N/A', Colors.DIM)}")
        print(f"  Manager:      (no soportado en esta plataforma)")
    
    # =========================================================================
    # Trabajos programados
    # =========================================================================
    print()
    print(color("◆ Scheduled Jobs", Colors.CYAN, Colors.BOLD))
    
    jobs_file = Path.home() / ".hermes" / "cron" / "jobs.json"
    if jobs_file.exists():
        import json
        try:
            with open(jobs_file, encoding="utf-8") as f:
                data = json.load(f)
                jobs = data.get("jobs", [])
                enabled_jobs = [j for j in jobs if j.get("enabled", True)]
                print(f"  Jobs:         {len(enabled_jobs)} activos, {len(jobs)} en total")
        except Exception:
            print(f"  Jobs:         (error al leer el archivo de jobs)")
    else:
        print(f"  Jobs:         0")
    
    # =========================================================================
    # Sesiones
    # =========================================================================
    print()
    print(color("◆ Sessions", Colors.CYAN, Colors.BOLD))
    
    sessions_file = Path.home() / ".hermes" / "sessions" / "sessions.json"
    if sessions_file.exists():
        import json
        try:
            with open(sessions_file, encoding="utf-8") as f:
                data = json.load(f)
                print(f"  Activas:      {len(data)} sesión(es)")
        except Exception:
            print(f"  Activas:      (error al leer el archivo de sesiones)")
    else:
        print(f"  Active:       0")
    
    # =========================================================================
    # Comprobaciones profundas
    # =========================================================================
    if deep:
        print()
        print(color("◆ Deep Checks", Colors.CYAN, Colors.BOLD))
        
        # Comprobar conectividad con OpenRouter
        openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
        if openrouter_key:
            try:
                import httpx
                response = httpx.get(
                    OPENROUTER_MODELS_URL,
                    headers={"Authorization": f"Bearer {openrouter_key}"},
                    timeout=10
                )
                ok = response.status_code == 200
                print(f"  OpenRouter:   {check_mark(ok)} {'accesible' if ok else f'error ({response.status_code})'}")
            except Exception as e:
                print(f"  OpenRouter:   {check_mark(False)} error: {e}")
        
        # Comprobar el puerto del gateway
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', 18789))
            sock.close()
            # Puerto en uso = gateway probablemente en ejecución
            port_in_use = result == 0
            # Es solo informativo, no necesariamente un problema
            print(f"  Puerto 18789: {'en uso' if port_in_use else 'disponible'}")
        except OSError:
            pass
    
    print()
    print(color("─" * 60, Colors.DIM))
    print(color("  Run 'hermes doctor' for detailed diagnostics", Colors.DIM))
    print(color("  Run 'hermes setup' to configure", Colors.DIM))
    print()
