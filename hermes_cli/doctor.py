"""Comando "doctor" para el CLI de Hermes.

Diagnostica problemas en la configuración de Hermes Agent.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

from hermes_cli.config import get_project_root, get_hermes_home, get_env_path

PROJECT_ROOT = get_project_root()
HERMES_HOME = get_hermes_home()

# Load environment variables from ~/.hermes/.env so API key checks work
from dotenv import load_dotenv
_env_path = get_env_path()
if _env_path.exists():
    try:
        load_dotenv(_env_path, encoding="utf-8")
    except UnicodeDecodeError:
        load_dotenv(_env_path, encoding="latin-1")
# Also try project .env as dev fallback
load_dotenv(PROJECT_ROOT / ".env", override=False, encoding="utf-8")

# Point mini-swe-agent at ~/.hermes/ so it shares our config
os.environ.setdefault("MSWEA_GLOBAL_CONFIG_DIR", str(HERMES_HOME))
os.environ.setdefault("MSWEA_SILENT_STARTUP", "1")

from hermes_cli.colors import Colors, color
from hermes_constants import OPENROUTER_MODELS_URL


_PROVIDER_ENV_HINTS = (
    "OPENROUTER_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENAI_BASE_URL",
    "GLM_API_KEY",
    "ZAI_API_KEY",
    "Z_AI_API_KEY",
    "KIMI_API_KEY",
    "MINIMAX_API_KEY",
    "MINIMAX_CN_API_KEY",
)


def _has_provider_env_config(content: str) -> bool:
    """Devuelve True cuando ~/.hermes/.env contiene ajustes de auth/base URL de proveedores."""
    return any(key in content for key in _PROVIDER_ENV_HINTS)


def check_ok(text: str, detail: str = ""):
    print(f"  {color('✓', Colors.GREEN)} {text}" + (f" {color(detail, Colors.DIM)}" if detail else ""))

def check_warn(text: str, detail: str = ""):
    print(f"  {color('⚠', Colors.YELLOW)} {text}" + (f" {color(detail, Colors.DIM)}" if detail else ""))

def check_fail(text: str, detail: str = ""):
    print(f"  {color('✗', Colors.RED)} {text}" + (f" {color(detail, Colors.DIM)}" if detail else ""))

def check_info(text: str):
    print(f"    {color('→', Colors.CYAN)} {text}")


def run_doctor(args):
    """Ejecuta las comprobaciones de diagnóstico."""
    should_fix = getattr(args, 'fix', False)
    
    issues = []
    manual_issues = []  # issues that can't be auto-fixed
    fixed_count = 0
    
    print()
    print(color("┌─────────────────────────────────────────────────────────┐", Colors.CYAN))
    print(color("│                 🩺 Hermes Doctor                        │", Colors.CYAN))
    print(color("└─────────────────────────────────────────────────────────┘", Colors.CYAN))
    
    # =========================================================================
    # Comprobación: versión de Python
    # =========================================================================
    print()
    print(color("◆ Entorno Python", Colors.CYAN, Colors.BOLD))
    
    py_version = sys.version_info
    if py_version >= (3, 11):
        check_ok(f"Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    elif py_version >= (3, 10):
        check_ok(f"Python {py_version.major}.{py_version.minor}.{py_version.micro}")
        check_warn("Se recomienda Python 3.11+ para herramientas de entrenamiento RL (tinker requiere >= 3.11)")
    elif py_version >= (3, 8):
        check_warn(f"Python {py_version.major}.{py_version.minor}.{py_version.micro}", "(se recomienda 3.10+)")
    else:
        check_fail(f"Python {py_version.major}.{py_version.minor}.{py_version.micro}", "(se requiere 3.10+)")
        issues.append("Actualizar Python a 3.10+")
    
    # Check if in virtual environment
    in_venv = sys.prefix != sys.base_prefix
    if in_venv:
        check_ok("Entorno virtual activo")
    else:
        check_warn("No estás en un entorno virtual", "(recomendado)")
    
    # =========================================================================
    # Comprobación: paquetes requeridos
    # =========================================================================
    print()
    print(color("◆ Paquetes requeridos", Colors.CYAN, Colors.BOLD))
    
    required_packages = [
        ("openai", "OpenAI SDK"),
        ("rich", "Rich (terminal UI)"),
        ("dotenv", "python-dotenv"),
        ("yaml", "PyYAML"),
        ("httpx", "HTTPX"),
    ]
    
    optional_packages = [
        ("croniter", "Croniter (cron expressions)"),
        ("telegram", "python-telegram-bot"),
        ("discord", "discord.py"),
    ]
    
    for module, name in required_packages:
        try:
            __import__(module)
            check_ok(name)
        except ImportError:
            check_fail(name, "(faltante)")
            issues.append(f"Instala {name}: uv pip install {module}")
    
    for module, name in optional_packages:
        try:
            __import__(module)
            check_ok(name, "(optional)")
        except ImportError:
            check_warn(name, "(opcional, no instalado)")
    
    # =========================================================================
    # Comprobación: archivos de configuración
    # =========================================================================
    print()
    print(color("◆ Archivos de configuración", Colors.CYAN, Colors.BOLD))
    
    # Comprobar ~/.hermes/.env (ubicación principal de la config de usuario)
    env_path = HERMES_HOME / '.env'
    if env_path.exists():
        check_ok("~/.hermes/.env existe")
        
        # Comprobar problemas comunes
        content = env_path.read_text()
        if _has_provider_env_config(content):
            check_ok("API key o endpoint personalizado configurado")
        else:
            check_warn("No se encontró API key en ~/.hermes/.env")
            issues.append("Ejecuta 'hermes setup' para configurar las API keys")
    else:
        # También comprobar el root del proyecto como fallback
        fallback_env = PROJECT_ROOT / '.env'
        if fallback_env.exists():
            check_ok(".env existe (en el directorio del proyecto)")
        else:
            check_fail("Falta ~/.hermes/.env")
            if should_fix:
                env_path.parent.mkdir(parents=True, exist_ok=True)
                env_path.touch()
                check_ok("Se creó un ~/.hermes/.env vacío")
                check_info("Ejecuta 'hermes setup' para configurar las API keys")
                fixed_count += 1
            else:
                check_info("Ejecuta 'hermes setup' para crear uno")
                issues.append("Ejecuta 'hermes setup' para crear .env")
    
    # Comprobar ~/.hermes/config.yaml (principal) o cli-config.yaml del proyecto (fallback)
    config_path = HERMES_HOME / 'config.yaml'
    if config_path.exists():
        check_ok("~/.hermes/config.yaml existe")
    else:
        fallback_config = PROJECT_ROOT / 'cli-config.yaml'
        if fallback_config.exists():
            check_ok("cli-config.yaml existe (en el directorio del proyecto)")
        else:
            example_config = PROJECT_ROOT / 'cli-config.yaml.example'
            if should_fix and example_config.exists():
                config_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(example_config), str(config_path))
                check_ok("Se creó ~/.hermes/config.yaml desde cli-config.yaml.example")
                fixed_count += 1
            elif should_fix:
                check_warn("config.yaml no encontrado y no hay ejemplo para copiar")
                manual_issues.append("Crea ~/.hermes/config.yaml manualmente")
            else:
                check_warn("config.yaml no encontrado", "(usando valores por defecto)")
    
    # =========================================================================
    # Comprobación: proveedores de auth
    # =========================================================================
    print()
    print(color("◆ Proveedores de auth", Colors.CYAN, Colors.BOLD))

    try:
        from hermes_cli.auth import get_nous_auth_status, get_codex_auth_status

        nous_status = get_nous_auth_status()
        if nous_status.get("logged_in"):
            check_ok("Auth Nous Portal", "(sesión iniciada)")
        else:
            check_warn("Auth Nous Portal", "(sin sesión)")

        codex_status = get_codex_auth_status()
        if codex_status.get("logged_in"):
            check_ok("Auth OpenAI Codex", "(sesión iniciada)")
        else:
            check_warn("Auth OpenAI Codex", "(sin sesión)")
            if codex_status.get("error"):
                check_info(codex_status["error"])
    except Exception as e:
        check_warn("Estado de proveedores de auth", f"(no se pudo comprobar: {e})")

    if shutil.which("codex"):
        check_ok("codex CLI")
    else:
        check_warn("codex CLI no encontrado", "(requerido para login openai-codex)")

    # =========================================================================
    # Comprobación: estructura de directorios
    # =========================================================================
    print()
    print(color("◆ Estructura de directorios", Colors.CYAN, Colors.BOLD))
    
    hermes_home = HERMES_HOME
    if hermes_home.exists():
        check_ok("El directorio ~/.hermes existe")
    else:
        if should_fix:
            hermes_home.mkdir(parents=True, exist_ok=True)
            check_ok("Se creó el directorio ~/.hermes")
            fixed_count += 1
        else:
            check_warn("~/.hermes no encontrado", "(se creará en el primer uso)")
    
    # Comprobar subdirectorios esperados
    expected_subdirs = ["cron", "sessions", "logs", "skills", "memories"]
    for subdir_name in expected_subdirs:
        subdir_path = hermes_home / subdir_name
        if subdir_path.exists():
            check_ok(f"~/.hermes/{subdir_name}/ existe")
        else:
            if should_fix:
                subdir_path.mkdir(parents=True, exist_ok=True)
                check_ok(f"Se creó ~/.hermes/{subdir_name}/")
                fixed_count += 1
            else:
                check_warn(f"~/.hermes/{subdir_name}/ no encontrado", "(se creará en el primer uso)")
    
    # Comprobar archivo de persona SOUL.md
    soul_path = hermes_home / "SOUL.md"
    if soul_path.exists():
        content = soul_path.read_text(encoding="utf-8").strip()
        # Check if it's just the template comments (no real content)
        lines = [l for l in content.splitlines() if l.strip() and not l.strip().startswith(("<!--", "-->", "#"))]
        if lines:
            check_ok("~/.hermes/SOUL.md existe (persona configurada)")
        else:
            check_info("~/.hermes/SOUL.md existe pero está vacío — edítalo para personalizar la personalidad")
    else:
        check_warn("~/.hermes/SOUL.md no encontrado", "(créalo para darle a Hermes una personalidad personalizada)")
        if should_fix:
            soul_path.parent.mkdir(parents=True, exist_ok=True)
            soul_path.write_text(
                "# Hermes Agent Persona\n\n"
                "<!-- Edita este archivo para personalizar cómo se comunica Hermes. -->\n\n"
                "Eres Hermes, un asistente de IA servicial.\n",
                encoding="utf-8",
            )
            check_ok("Se creó ~/.hermes/SOUL.md con plantilla básica")
            fixed_count += 1
    
    # Comprobar directorio de memoria
    memories_dir = hermes_home / "memories"
    if memories_dir.exists():
        check_ok("El directorio ~/.hermes/memories/ existe")
        memory_file = memories_dir / "MEMORY.md"
        user_file = memories_dir / "USER.md"
        if memory_file.exists():
            size = len(memory_file.read_text(encoding="utf-8").strip())
            check_ok(f"MEMORY.md existe ({size} caracteres)")
        else:
            check_info("MEMORY.md aún no se ha creado (se creará cuando el agente escriba la primera memoria)")
        if user_file.exists():
            size = len(user_file.read_text(encoding="utf-8").strip())
            check_ok(f"USER.md existe ({size} caracteres)")
        else:
            check_info("USER.md aún no se ha creado (se creará cuando el agente escriba la primera memoria)")
    else:
        check_warn("~/.hermes/memories/ no encontrado", "(se creará en el primer uso)")
        if should_fix:
            memories_dir.mkdir(parents=True, exist_ok=True)
            check_ok("Se creó ~/.hermes/memories/")
            fixed_count += 1
    
    # Comprobar almacén de sesiones SQLite
    state_db_path = hermes_home / "state.db"
    if state_db_path.exists():
        try:
            import sqlite3
            conn = sqlite3.connect(str(state_db_path))
            cursor = conn.execute("SELECT COUNT(*) FROM sessions")
            count = cursor.fetchone()[0]
            conn.close()
            check_ok(f"~/.hermes/state.db existe ({count} sesión(es))")
        except Exception as e:
            check_warn(f"~/.hermes/state.db existe pero tiene problemas: {e}")
    else:
        check_info("~/.hermes/state.db aún no se ha creado (se creará en la primera sesión)")
    
    # =========================================================================
    # Comprobación: herramientas externas
    # =========================================================================
    print()
    print(color("◆ Herramientas externas", Colors.CYAN, Colors.BOLD))
    
    # Git
    if shutil.which("git"):
        check_ok("git")
    else:
        check_warn("git no encontrado", "(opcional)")
    
    # ripgrep (opcional, para búsqueda de archivos más rápida)
    if shutil.which("rg"):
        check_ok("ripgrep (rg)", "(búsqueda de archivos más rápida)")
    else:
        check_warn("ripgrep (rg) no encontrado", "(la búsqueda de archivos usará grep)")
        check_info("Instálalo para búsqueda más rápida: sudo apt install ripgrep")
    
    # Docker (opcional)
    terminal_env = os.getenv("TERMINAL_ENV", "local")
    if terminal_env == "docker":
        if shutil.which("docker"):
            # Check if docker daemon is running
            result = subprocess.run(["docker", "info"], capture_output=True)
            if result.returncode == 0:
                check_ok("docker", "(daemon en ejecución)")
            else:
                check_fail("docker daemon no está en ejecución")
                issues.append("Inicia el daemon de Docker")
        else:
            check_fail("docker no encontrado", "(requerido para TERMINAL_ENV=docker)")
            issues.append("Instala Docker o cambia TERMINAL_ENV")
    else:
        if shutil.which("docker"):
            check_ok("docker", "(opcional)")
        else:
            check_warn("docker no encontrado", "(opcional)")
    
    # SSH (si se usa backend ssh)
    if terminal_env == "ssh":
        ssh_host = os.getenv("TERMINAL_SSH_HOST")
        if ssh_host:
            # Try to connect
            result = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes", ssh_host, "echo ok"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                check_ok(f"Conexión SSH a {ssh_host}")
            else:
                check_fail(f"Conexión SSH a {ssh_host}")
                issues.append(f"Revisa la configuración SSH para {ssh_host}")
        else:
            check_fail("TERMINAL_SSH_HOST no definido", "(requerido para TERMINAL_ENV=ssh)")
            issues.append("Define TERMINAL_SSH_HOST en .env")
    
    # Daytona (si se usa backend daytona)
    if terminal_env == "daytona":
        daytona_key = os.getenv("DAYTONA_API_KEY")
        if daytona_key:
            check_ok("Daytona API key", "(configurada)")
        else:
            check_fail("DAYTONA_API_KEY no definida", "(requerida para TERMINAL_ENV=daytona)")
            issues.append("Define la variable de entorno DAYTONA_API_KEY")
        try:
            from daytona import Daytona
            check_ok("daytona SDK", "(instalado)")
        except ImportError:
            check_fail("daytona SDK no instalado", "(pip install daytona)")
            issues.append("Instala daytona SDK: pip install daytona")

    # Node.js + agent-browser (para herramientas de automatización del navegador)
    if shutil.which("node"):
        check_ok("Node.js")
        # Comprobar si agent-browser está instalado
        agent_browser_path = PROJECT_ROOT / "node_modules" / "agent-browser"
        if agent_browser_path.exists():
            check_ok("agent-browser (Node.js)", "(browser automation)")
        else:
            check_warn("agent-browser no instalado", "(ejecuta: npm install)")
    else:
        check_warn("Node.js no encontrado", "(opcional, necesario para herramientas de navegador)")
    
    # npm audit para todos los paquetes Node.js
    if shutil.which("npm"):
        npm_dirs = [
            (PROJECT_ROOT, "Browser tools (agent-browser)"),
            (PROJECT_ROOT / "scripts" / "whatsapp-bridge", "WhatsApp bridge"),
        ]
        for npm_dir, label in npm_dirs:
            if not (npm_dir / "node_modules").exists():
                continue
            try:
                audit_result = subprocess.run(
                    ["npm", "audit", "--json"],
                    cwd=str(npm_dir),
                    capture_output=True, text=True, timeout=30,
                )
                import json as _json
                audit_data = _json.loads(audit_result.stdout) if audit_result.stdout.strip() else {}
                vuln_count = audit_data.get("metadata", {}).get("vulnerabilities", {})
                critical = vuln_count.get("critical", 0)
                high = vuln_count.get("high", 0)
                moderate = vuln_count.get("moderate", 0)
                total = critical + high + moderate
                if total == 0:
                    check_ok(f"{label} deps", "(sin vulnerabilidades conocidas)")
                elif critical > 0 or high > 0:
                    check_warn(
                        f"{label} deps",
                        f"({critical} críticas, {high} altas, {moderate} moderadas — ejecuta: cd {npm_dir} && npm audit fix)"
                    )
                    issues.append(f"{label} tiene {total} vulnerabilidad(es) npm")
                else:
                    check_ok(f"{label} deps", f"({moderate} vulnerabilidad(es) moderada(s))")
            except Exception:
                pass

    # =========================================================================
    # Comprobación: conectividad API
    # =========================================================================
    print()
    print(color("◆ Conectividad API", Colors.CYAN, Colors.BOLD))
    
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        print("  Comprobando OpenRouter API...", end="", flush=True)
        try:
            import httpx
            response = httpx.get(
                OPENROUTER_MODELS_URL,
                headers={"Authorization": f"Bearer {openrouter_key}"},
                timeout=10
            )
            if response.status_code == 200:
                print(f"\r  {color('✓', Colors.GREEN)} OpenRouter API                          ")
            elif response.status_code == 401:
                print(f"\r  {color('✗', Colors.RED)} OpenRouter API {color('(API key inválida)', Colors.DIM)}                ")
                issues.append("Revisa OPENROUTER_API_KEY en .env")
            else:
                print(f"\r  {color('✗', Colors.RED)} OpenRouter API {color(f'(HTTP {response.status_code})', Colors.DIM)}                ")
        except Exception as e:
            print(f"\r  {color('✗', Colors.RED)} OpenRouter API {color(f'({e})', Colors.DIM)}                ")
            issues.append("Revisa la conectividad de red")
    else:
        check_warn("OpenRouter API", "(no configurada)")
    
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        print("  Comprobando Anthropic API...", end="", flush=True)
        try:
            import httpx
            response = httpx.get(
                "https://api.anthropic.com/v1/models",
                headers={
                    "x-api-key": anthropic_key,
                    "anthropic-version": "2023-06-01"
                },
                timeout=10
            )
            if response.status_code == 200:
                print(f"\r  {color('✓', Colors.GREEN)} Anthropic API                           ")
            elif response.status_code == 401:
                print(f"\r  {color('✗', Colors.RED)} Anthropic API {color('(API key inválida)', Colors.DIM)}                 ")
            else:
                msg = "(no se pudo verificar)"
                print(f"\r  {color('⚠', Colors.YELLOW)} Anthropic API {color(msg, Colors.DIM)}                 ")
        except Exception as e:
            print(f"\r  {color('⚠', Colors.YELLOW)} Anthropic API {color(f'({e})', Colors.DIM)}                 ")

    # -- API-key providers (Z.AI/GLM, Kimi, MiniMax, MiniMax-CN) --
    # Tuple: (name, env_vars, default_url, base_env, supports_models_endpoint)
    # If supports_models_endpoint is False, we skip the health check and just show "configured"
    _apikey_providers = [
        ("Z.AI / GLM",      ("GLM_API_KEY", "ZAI_API_KEY", "Z_AI_API_KEY"), "https://api.z.ai/api/paas/v4/models", "GLM_BASE_URL", True),
        ("Kimi / Moonshot",  ("KIMI_API_KEY",),                              "https://api.moonshot.ai/v1/models",   "KIMI_BASE_URL", True),
        # MiniMax APIs don't support /models endpoint — https://github.com/NousResearch/hermes-agent/issues/811
        ("MiniMax",          ("MINIMAX_API_KEY",),                            None,                                  "MINIMAX_BASE_URL", False),
        ("MiniMax (China)",  ("MINIMAX_CN_API_KEY",),                         None,                                  "MINIMAX_CN_BASE_URL", False),
    ]
    for _pname, _env_vars, _default_url, _base_env, _supports_health_check in _apikey_providers:
        _key = ""
        for _ev in _env_vars:
            _key = os.getenv(_ev, "")
            if _key:
                break
        if _key:
            _label = _pname.ljust(20)
            # Some providers (like MiniMax) don't support /models endpoint
            if not _supports_health_check:
                print(f"  {color('✓', Colors.GREEN)} {_label} {color('(key configurada)', Colors.DIM)}")
                continue
            print(f"  Comprobando {_pname} API...", end="", flush=True)
            try:
                import httpx
                _base = os.getenv(_base_env, "")
                # Auto-detect Kimi Code keys (sk-kimi-) → api.kimi.com
                if not _base and _key.startswith("sk-kimi-"):
                    _base = "https://api.kimi.com/coding/v1"
                _url = (_base.rstrip("/") + "/models") if _base else _default_url
                _headers = {"Authorization": f"Bearer {_key}"}
                if "api.kimi.com" in _url.lower():
                    _headers["User-Agent"] = "KimiCLI/1.0"
                _resp = httpx.get(
                    _url,
                    headers=_headers,
                    timeout=10,
                )
                if _resp.status_code == 200:
                    print(f"\r  {color('✓', Colors.GREEN)} {_label}                          ")
                elif _resp.status_code == 401:
                    print(f"\r  {color('✗', Colors.RED)} {_label} {color('(API key inválida)', Colors.DIM)}           ")
                    issues.append(f"Revisa {_env_vars[0]} en .env")
                else:
                    print(f"\r  {color('⚠', Colors.YELLOW)} {_label} {color(f'(HTTP {_resp.status_code})', Colors.DIM)}           ")
            except Exception as _e:
                print(f"\r  {color('⚠', Colors.YELLOW)} {_label} {color(f'({_e})', Colors.DIM)}           ")

    # =========================================================================
    # Comprobación: submódulos
    # =========================================================================
    print()
    print(color("◆ Submódulos", Colors.CYAN, Colors.BOLD))
    
    # mini-swe-agent (terminal tool backend)
    mini_swe_dir = PROJECT_ROOT / "mini-swe-agent"
    if mini_swe_dir.exists() and (mini_swe_dir / "pyproject.toml").exists():
        try:
            __import__("minisweagent")
            check_ok("mini-swe-agent", "(backend de terminal)")
        except ImportError:
            check_warn("mini-swe-agent encontrado pero no instalado", "(ejecuta: uv pip install -e ./mini-swe-agent)")
            issues.append("Instala mini-swe-agent: uv pip install -e ./mini-swe-agent")
    else:
        check_warn("mini-swe-agent no encontrado", "(ejecuta: git submodule update --init --recursive)")
    
    # tinker-atropos (backend de entrenamiento RL)
    tinker_dir = PROJECT_ROOT / "tinker-atropos"
    if tinker_dir.exists() and (tinker_dir / "pyproject.toml").exists():
        if py_version >= (3, 11):
            try:
                __import__("tinker_atropos")
                check_ok("tinker-atropos", "(backend de entrenamiento RL)")
            except ImportError:
                check_warn("tinker-atropos encontrado pero no instalado", "(ejecuta: uv pip install -e ./tinker-atropos)")
                issues.append("Instala tinker-atropos: uv pip install -e ./tinker-atropos")
        else:
            check_warn("tinker-atropos requiere Python 3.11+", f"(actual: {py_version.major}.{py_version.minor})")
    else:
        check_warn("tinker-atropos no encontrado", "(ejecuta: git submodule update --init --recursive)")
    
    # =========================================================================
    # Comprobación: disponibilidad de herramientas
    # =========================================================================
    print()
    print(color("◆ Disponibilidad de herramientas", Colors.CYAN, Colors.BOLD))
    
    try:
        # Add project root to path for imports
        sys.path.insert(0, str(PROJECT_ROOT))
        from model_tools import check_tool_availability, TOOLSET_REQUIREMENTS
        
        available, unavailable = check_tool_availability()
        
        for tid in available:
            info = TOOLSET_REQUIREMENTS.get(tid, {})
            check_ok(info.get("name", tid))
        
        for item in unavailable:
            env_vars = item.get("missing_vars") or item.get("env_vars") or []
            if env_vars:
                vars_str = ", ".join(env_vars)
                check_warn(item["name"], f"(faltan {vars_str})")
            else:
                check_warn(item["name"], "(dependencia de sistema no satisfecha)")

        # Count disabled tools with API key requirements
        api_disabled = [u for u in unavailable if (u.get("missing_vars") or u.get("env_vars"))]
        if api_disabled:
            issues.append("Ejecuta 'hermes setup' para configurar las API keys faltantes y tener acceso completo a las herramientas")
    except Exception as e:
        check_warn("No se pudo comprobar la disponibilidad de herramientas", f"({e})")
    
    # =========================================================================
    # Comprobación: Skills Hub
    # =========================================================================
    print()
    print(color("◆ Skills Hub", Colors.CYAN, Colors.BOLD))

    hub_dir = HERMES_HOME / "skills" / ".hub"
    if hub_dir.exists():
        check_ok("El directorio de Skills Hub existe")
        lock_file = hub_dir / "lock.json"
        if lock_file.exists():
            try:
                import json
                lock_data = json.loads(lock_file.read_text())
                count = len(lock_data.get("installed", {}))
                check_ok(f"Lock file OK ({count} skill(s) instaladas desde el hub)")
            except Exception:
                check_warn("Lock file", "(corrupto o ilegible)")
        quarantine = hub_dir / "quarantine"
        q_count = sum(1 for d in quarantine.iterdir() if d.is_dir()) if quarantine.exists() else 0
        if q_count > 0:
            check_warn(f"{q_count} skill(s) en cuarentena", "(pendientes de revisión)")
    else:
        check_warn("Directorio de Skills Hub no inicializado", "(ejecuta: hermes skills list)")

    from hermes_cli.config import get_env_value
    github_token = get_env_value("GITHUB_TOKEN") or get_env_value("GH_TOKEN")
    if github_token:
        check_ok("GitHub token configurado (acceso API autenticado)")
    else:
        check_warn("No hay GITHUB_TOKEN", "(límite 60 req/h — defínelo en ~/.hermes/.env para mejores tasas)")

    # =========================================================================
    # Summary
    # =========================================================================
    print()
    remaining_issues = issues + manual_issues
    if should_fix and fixed_count > 0:
        print(color("─" * 60, Colors.GREEN))
        print(color(f"  Se corrigieron {fixed_count} problema(s).", Colors.GREEN, Colors.BOLD), end="")
        if remaining_issues:
            print(color(f" {len(remaining_issues)} problema(s) requieren intervención manual.", Colors.YELLOW, Colors.BOLD))
        else:
            print()
        print()
        if remaining_issues:
            for i, issue in enumerate(remaining_issues, 1):
                print(f"  {i}. {issue}")
            print()
    elif remaining_issues:
        print(color("─" * 60, Colors.YELLOW))
        print(color(f"  Se encontraron {len(remaining_issues)} problema(s) a resolver:", Colors.YELLOW, Colors.BOLD))
        print()
        for i, issue in enumerate(remaining_issues, 1):
            print(f"  {i}. {issue}")
        print()
        if not should_fix:
            print(color("  Tip: ejecuta 'hermes doctor --fix' para auto-corregir lo posible.", Colors.DIM))
    else:
        print(color("─" * 60, Colors.GREEN))
        print(color("  ¡Todas las comprobaciones pasaron! 🎉", Colors.GREEN, Colors.BOLD))
    
    print()
