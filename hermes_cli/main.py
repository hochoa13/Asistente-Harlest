#!/usr/bin/env python3
"""
Hermes CLI - Punto de entrada principal.

Uso:
    hermes                     # Chat interactivo (predeterminado)
    hermes chat                # Chat interactivo
    hermes gateway             # Ejecutar gateway en primer plano
    hermes gateway start       # Iniciar gateway como servicio
    hermes gateway stop        # Detener servicio del gateway
    hermes gateway status      # Mostrar estado del gateway
    hermes gateway install     # Instalar gateway como servicio
    hermes gateway uninstall   # Desinstalar servicio del gateway
    hermes setup               # Asistente de configuracion interactivo
    hermes logout              # Limpiar autenticacion almacenada
    hermes status              # Mostrar estado de todos los componentes
    hermes cron                # Gestionar trabajos cron
    hermes cron list           # Listar trabajos cron
    hermes cron status         # Comprobar si el planificador cron esta en ejecucion
    hermes doctor              # Verificar configuracion y dependencias
    hermes version             # Mostrar version
    hermes update              # Actualizar a la ultima version
    hermes uninstall           # Desinstalar Hermes Agent
    hermes sessions browse     # Navegador de sesiones interactivo con busqueda
    hermes claw migrate        # Migrar desde OpenClaw a Hermes
    hermes claw migrate --dry-run  # Vista previa de migracion sin cambios
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

# Agregar raíz del proyecto a la ruta
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# Cargar .env desde ~/.hermes/.env primero, luego raíz del proyecto como fallback de desarrollo
from dotenv import load_dotenv
from hermes_cli.config import get_env_path, get_hermes_home
_user_env = get_env_path()
if _user_env.exists():
    try:
        load_dotenv(dotenv_path=_user_env, encoding="utf-8")
    except UnicodeDecodeError:
        load_dotenv(dotenv_path=_user_env, encoding="latin-1")
load_dotenv(dotenv_path=PROJECT_ROOT / '.env', override=False)

# Apuntar mini-swe-agent a ~/.hermes/ para que comparta nuestra configuración
os.environ.setdefault("MSWEA_GLOBAL_CONFIG_DIR", str(get_hermes_home()))
os.environ.setdefault("MSWEA_SILENT_STARTUP", "1")

import logging

from hermes_cli import __version__, __release_date__
from hermes_constants import OPENROUTER_BASE_URL

logger = logging.getLogger(__name__)


def _has_any_provider_configured() -> bool:
    """Comprueba si al menos un proveedor de inferencia esta configurado."""
    from hermes_cli.config import get_env_path, get_hermes_home
    from hermes_cli.auth import get_auth_status

    # Comprobar variables de entorno (pueden estar configuradas por .env o shell).
    # OPENAI_BASE_URL solo cuenta — modelos locales (vLLM, llama.cpp, etc.)
    # a menudo no requieren una clave de API.
    from hermes_cli.auth import PROVIDER_REGISTRY

    # Recopilar todas las variables de entorno del proveedor
    provider_env_vars = {"OPENROUTER_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_BASE_URL"}
    for pconfig in PROVIDER_REGISTRY.values():
        if pconfig.auth_type == "api_key":
            provider_env_vars.update(pconfig.api_key_env_vars)
    if any(os.getenv(v) for v in provider_env_vars):
        return True

    # Comprobar archivo .env para claves
    env_file = get_env_path()
    if env_file.exists():
        try:
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                val = val.strip().strip("'\"")
                if key.strip() in provider_env_vars and val:
                    return True
        except Exception:
            pass

    # Comprobar credenciales OAuth de Nous Portal
    auth_file = get_hermes_home() / "auth.json"
    if auth_file.exists():
        try:
            import json
            auth = json.loads(auth_file.read_text())
            active = auth.get("active_provider")
            if active:
                status = get_auth_status(active)
                if status.get("logged_in"):
                    return True
        except Exception:
            pass

    return False


def _session_browse_picker(sessions: list) -> Optional[str]:
    """Navegador interactivo de sesiones basado en curses con filtrado de búsqueda en vivo.

    Devuelve el ID de la sesión seleccionada, o None si se cancela.
    Usa curses (no simple_term_menu) para evitar el error de renderizado de duplicación fantasma
    en tmux/iTerm cuando se usan las teclas de flecha.
    """
    if not sessions:
        print("No se encontraron sesiones.")
        return None

    # Intentar primero el selector basado en curses
    try:
        import curses
        import time as _time
        from datetime import datetime

        result_holder = [None]

        def _relative_time(ts):
            if not ts:
                return "?"
            delta = _time.time() - ts
            if delta < 60:
                return "justo ahora"
            elif delta < 3600:
                return f"{int(delta / 60)}m atrás"
            elif delta < 86400:
                return f"{int(delta / 3600)}h atrás"
            elif delta < 172800:
                return "ayer"
            elif delta < 604800:
                return f"{int(delta / 86400)}d atrás"
            else:
                return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")

        def _format_row(s, max_x):
            """Formatea una fila de sesión para mostrar."""
            title = (s.get("title") or "").strip()
            preview = (s.get("preview") or "").strip()
            source = s.get("source", "")[:6]
            last_active = _relative_time(s.get("last_active"))
            sid = s["id"][:18]

            # Anchos de columna adaptativos basados en el ancho del terminal
            # Diseño: [flecha 3] [título/vista previa flexible] [activo 12] [src 6] [id 18]
            fixed_cols = 3 + 12 + 6 + 18 + 6  # flecha + activo + src + id + relleno
            name_width = max(20, max_x - fixed_cols)

            if title:
                name = title[:name_width]
            elif preview:
                name = preview[:name_width]
            else:
                name = sid

            return f"{name:<{name_width}}  {last_active:<10}  {source:<5} {sid}"

        def _match(s, query):
            """Comprueba si una sesión coincide con la consulta de búsqueda (sin distinción de mayúsculas)."""
            q = query.lower()
            return (
                q in (s.get("title") or "").lower()
                or q in (s.get("preview") or "").lower()
                or q in s.get("id", "").lower()
                or q in (s.get("source") or "").lower()
            )

        def _curses_browse(stdscr):
            curses.curs_set(0)
            if curses.has_colors():
                curses.start_color()
                curses.use_default_colors()
                curses.init_pair(1, curses.COLOR_GREEN, -1)   # seleccionado
                curses.init_pair(2, curses.COLOR_YELLOW, -1)  # encabezado
                curses.init_pair(3, curses.COLOR_CYAN, -1)    # búsqueda
                curses.init_pair(4, 8, -1)                    # atenuado

            cursor = 0
            scroll_offset = 0
            search_text = ""
            filtered = list(sessions)

            while True:
                stdscr.clear()
                max_y, max_x = stdscr.getmaxyx()
                if max_y < 5 or max_x < 40:
                    # Terminal demasiado pequeño
                    try:
                        stdscr.addstr(0, 0, "Terminal demasiado pequeña")
                    except curses.error:
                        pass
                    stdscr.refresh()
                    stdscr.getch()
                    return

                # Header line
                if search_text:
                    header = f"  Navegar sesiones — filtro: {search_text}█"
                    header_attr = curses.A_BOLD
                    if curses.has_colors():
                        header_attr |= curses.color_pair(3)
                else:
                    header = "  Navegar sesiones — ↑↓ navega  Intro selecciona  Escribe para filtrar  Esc salir"
                    header_attr = curses.A_BOLD
                    if curses.has_colors():
                        header_attr |= curses.color_pair(2)
                try:
                    stdscr.addnstr(0, 0, header, max_x - 1, header_attr)
                except curses.error:
                    pass

                # Column header line
                fixed_cols = 3 + 12 + 6 + 18 + 6
                name_width = max(20, max_x - fixed_cols)
                col_header = f"   {'Título / Vista Previa':<{name_width}}  {'Activo':<10}  {'Src':<5} {'ID'}"
                try:
                    dim_attr = curses.color_pair(4) if curses.has_colors() else curses.A_DIM
                    stdscr.addnstr(1, 0, col_header, max_x - 1, dim_attr)
                except curses.error:
                    pass

                # Compute visible area
                visible_rows = max_y - 4  # header + col header + blank + footer
                if visible_rows < 1:
                    visible_rows = 1

                # Clamp cursor and scroll
                if not filtered:
                    try:
                        msg = "  No hay sesiones que coincidan con el filtro."
                        stdscr.addnstr(3, 0, msg, max_x - 1, curses.A_DIM)
                    except curses.error:
                        pass
                else:
                    if cursor >= len(filtered):
                        cursor = len(filtered) - 1
                    if cursor < 0:
                        cursor = 0
                    if cursor < scroll_offset:
                        scroll_offset = cursor
                    elif cursor >= scroll_offset + visible_rows:
                        scroll_offset = cursor - visible_rows + 1

                    for draw_i, i in enumerate(range(
                        scroll_offset,
                        min(len(filtered), scroll_offset + visible_rows)
                    )):
                        y = draw_i + 3
                        if y >= max_y - 1:
                            break
                        s = filtered[i]
                        arrow = " → " if i == cursor else "   "
                        row = arrow + _format_row(s, max_x - 3)
                        attr = curses.A_NORMAL
                        if i == cursor:
                            attr = curses.A_BOLD
                            if curses.has_colors():
                                attr |= curses.color_pair(1)
                        try:
                            stdscr.addnstr(y, 0, row, max_x - 1, attr)
                        except curses.error:
                            pass

                # Footer
                footer_y = max_y - 1
                if filtered:
                    footer = f"  {cursor + 1}/{len(filtered)} sesiones"
                    if len(filtered) < len(sessions):
                        footer += f" (filtradas de {len(sessions)})"
                else:
                    footer = f"  0/{len(sessions)} sesiones"
                try:
                    stdscr.addnstr(footer_y, 0, footer, max_x - 1,
                                   curses.color_pair(4) if curses.has_colors() else curses.A_DIM)
                except curses.error:
                    pass

                stdscr.refresh()
                key = stdscr.getch()

                if key in (curses.KEY_UP, ):
                    if filtered:
                        cursor = (cursor - 1) % len(filtered)
                elif key in (curses.KEY_DOWN, ):
                    if filtered:
                        cursor = (cursor + 1) % len(filtered)
                elif key in (curses.KEY_ENTER, 10, 13):
                    if filtered:
                        result_holder[0] = filtered[cursor]["id"]
                    return
                elif key == 27:  # Esc
                    if search_text:
                        # El primer Esc elimina la búsqueda
                        search_text = ""
                        filtered = list(sessions)
                        cursor = 0
                        scroll_offset = 0
                    else:
                        # El segundo Esc sale
                        return
                elif key in (curses.KEY_BACKSPACE, 127, 8):
                    if search_text:
                        search_text = search_text[:-1]
                        if search_text:
                            filtered = [s for s in sessions if _match(s, search_text)]
                        else:
                            filtered = list(sessions)
                        cursor = 0
                        scroll_offset = 0
                elif key == ord('q') and not search_text:
                    return
                elif 32 <= key <= 126:
                    # Carácter imprimible → agregar al filtro de búsqueda
                    search_text += chr(key)
                    filtered = [s for s in sessions if _match(s, search_text)]
                    cursor = 0
                    scroll_offset = 0

        curses.wrapper(_curses_browse)
        return result_holder[0]

    except Exception:
        pass

    # Alternativa: lista numerada (Windows sin curses, etc.)
    import time as _time
    from datetime import datetime

    def _relative_time_fb(ts):
        if not ts:
            return "?"
        delta = _time.time() - ts
        if delta < 60:
            return "justo ahora"
        elif delta < 3600:
            return f"{int(delta / 60)}m atrás"
        elif delta < 86400:
            return f"{int(delta / 3600)}h atrás"
        elif delta < 172800:
            return "ayer"
        elif delta < 604800:
            return f"{int(delta / 86400)}d atrás"
        else:
            return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")

    print("\n  Navegar sesiones  (ingresa número para reanudar, q para cancelar)\n")
    for i, s in enumerate(sessions):
        title = (s.get("title") or "").strip()
        preview = (s.get("preview") or "").strip()
        label = title or preview or s["id"]
        if len(label) > 50:
            label = label[:47] + "..."
        last_active = _relative_time_fb(s.get("last_active"))
        src = s.get("source", "")[:6]
        print(f"  {i + 1:>3}. {label:<50}  {last_active:<10}  {src}")

    while True:
        try:
            val = input(f"\n  Selecciona [1-{len(sessions)}]: ").strip()
            if not val or val.lower() in ("q", "quit", "exit", "salir"):
                return None
            idx = int(val) - 1
            if 0 <= idx < len(sessions):
                return sessions[idx]["id"]
            print(f"  Selección inválida. Ingresa 1-{len(sessions)} o q para cancelar.")
        except ValueError:
            print(f"  Entrada inválida. Ingresa un número o q para cancelar.")
        except (KeyboardInterrupt, EOFError):
            print()
            return None


def _resolve_last_cli_session() -> Optional[str]:
    """Buscar el ID de sesión CLI más reciente en SQLite. Devuelve None si no está disponible."""
    try:
        from hermes_state import SessionDB
        db = SessionDB()
        sessions = db.search_sessions(source="cli", limit=1)
        db.close()
        if sessions:
            return sessions[0]["id"]
    except Exception:
        pass
    return None


def _resolve_session_by_name_or_id(name_or_id: str) -> Optional[str]:
    """Resolver un nombre de sesión (título) o ID a un ID de sesión.

    - Si parece un ID de sesión (contiene guión bajo + hex), intentar primero búsqueda directa.
    - De lo contrario, tratarlo como un título y usar resolve_session_by_title (auto-último).
    - Recurrir al otro método si el primero no coincide.
    """
    try:
        from hermes_state import SessionDB
        db = SessionDB()

        # Intentar primero como ID de sesión exacto
        session = db.get_session(name_or_id)
        if session:
            db.close()
            return session["id"]

        # Intentar como título (con auto-último para linaje)
        session_id = db.resolve_session_by_title(name_or_id)
        db.close()
        return session_id
    except Exception:
        pass
    return None


def cmd_chat(args):
    """Ejecuta CLI de chat interactivo."""
    # Resolver --continue en --resume con la sesión CLI más reciente o por nombre
    continue_val = getattr(args, "continue_last", None)
    if continue_val and not getattr(args, "resume", None):
        if isinstance(continue_val, str):
            # -c "nombre de sesión" — resolver por título o ID
            resolved = _resolve_session_by_name_or_id(continue_val)
            if resolved:
                args.resume = resolved
            else:
                print(f"No se encontro sesion que coincida con '{continue_val}'.") 
                print("Usa 'hermes sessions list' para ver sesiones disponibles.")
                sys.exit(1)
        else:
            # -c sin argumento — continuar la sesión más reciente
            last_id = _resolve_last_cli_session()
            if last_id:
                args.resume = last_id
            else:
                print("No se encontro sesion CLI anterior para continuar.")
                sys.exit(1)

    # Resolver --resume por título si no es un ID de sesión directo
    resume_val = getattr(args, "resume", None)
    if resume_val:
        resolved = _resolve_session_by_name_or_id(resume_val)
        if resolved:
            args.resume = resolved
        # Si la resolución falla, mantener el valor original — _init_agent will
        # report "Session not found" with the original input

    # Guardia de primera ejecucion: comprueba si hay algun proveedor configurado antes de lanzar
    if not _has_any_provider_configured():
        print()
        print("Parece que Hermes aun no esta configurado -- no se encontraron claves de API ni proveedores.")
        print()
        print("  Ejecuta:  hermes setup")
        print()
        try:
            reply = input("Ejecutar configuracion ahora? [S/n] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            reply = "n"
        if reply in ("", "s", "si", "y", "yes"):
            cmd_setup(args)
            return
        print()
        print("Puedes ejecutar 'hermes setup' en cualquier momento para configurar.")
        sys.exit(1)

    # Sincronizar habilidades incluidas en cada inicio de CLI (rápido -- omite habilidades sin cambios)
    try:
        from tools.skills_sync import sync_skills
        sync_skills(quiet=True)
    except Exception:
        pass

    # --yolo: obviar todas las aprobaciones de comandos peligrosos
    if getattr(args, "yolo", False):
        os.environ["HERMES_YOLO_MODE"] = "1"

    # Importar y ejecutar la CLI
    from cli import main as cli_main
    
    # Construir kwargs a partir de args
    kwargs = {
        "model": args.model,
        "provider": getattr(args, "provider", None),
        "toolsets": args.toolsets,
        "verbose": args.verbose,
        "quiet": getattr(args, "quiet", False),
        "query": args.query,
        "resume": getattr(args, "resume", None),
        "worktree": getattr(args, "worktree", False),
        "checkpoints": getattr(args, "checkpoints", False),
        "pass_session_id": getattr(args, "pass_session_id", False),
    }
    # Filtrar valores None
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    
    cli_main(**kwargs)


def cmd_gateway(args):
    """Comandos de gestion del gateway."""
    from hermes_cli.gateway import gateway_command
    gateway_command(args)


def cmd_whatsapp(args):
    """Configura WhatsApp: elige modo, configura, instala puente, empareja por codigo QR."""
    import os
    import subprocess
    from pathlib import Path
    from hermes_cli.config import get_env_value, save_env_value

    print()
    print("⚕ Configuracion de WhatsApp")
    print("=" * 50)

    # ── Paso 1: Elige el modo ──────────────────────────────────────────────
    current_mode = get_env_value("WHATSAPP_MODE") or ""
    if not current_mode:
        print()
        print("Como usaras WhatsApp con Hermes?")
        print()
        print("  1. Numero de bot separado (recomendado)")
        print("     Las personas envian mensajes al numero del bot -- experiencia mas limpia.")
        print("     Requiere un segundo numero de telefono con WhatsApp instalado en un dispositivo.")
        print()
        print("  2. Numero personal (auto-chat)")
        print("     Te envias mensajes a ti mismo para hablar con el agente.")
        print("     Rapido de configurar, pero la UX es menos intuitiva.")
        print()
        try:
            choice = input("  Elige [1/2]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nConfiguracion cancelada.")
            return

        if choice == "1":
            save_env_value("WHATSAPP_MODE", "bot")
            wa_mode = "bot"
            print("  ✓ Mode: separate bot number")
            print()
            print("  ┌─────────────────────────────────────────────────┐")
            print("  │  Getting a second number for the bot:           │")
            print("  │                                                 │")
            print("  │  Easiest: Install WhatsApp Business (free app)  │")
            print("  │  on your phone with a second number:            │")
            print("  │    • Dual-SIM: use your 2nd SIM slot            │")
            print("  │    • Google Voice: free US number (voice.google) │")
            print("  │    • Prepaid SIM: $3-10, verify once            │")
            print("  │                                                 │")
            print("  │  WhatsApp Business runs alongside your personal │")
            print("  │  WhatsApp — no second phone needed.             │")
            print("  └─────────────────────────────────────────────────┘")
        else:
            save_env_value("WHATSAPP_MODE", "self-chat")
            wa_mode = "self-chat"
            print("  ✓ Mode: personal number (self-chat)")
    else:
        wa_mode = current_mode
        mode_label = "separate bot number" if wa_mode == "bot" else "personal number (self-chat)"
        print(f"\n✓ Mode: {mode_label}")

    # ── Step 2: Enable WhatsApp ──────────────────────────────────────────
    print()
    current = get_env_value("WHATSAPP_ENABLED")
    if current and current.lower() == "true":
        print("✓ WhatsApp is already enabled")
    else:
        save_env_value("WHATSAPP_ENABLED", "true")
        print("✓ WhatsApp enabled")

    # ── Step 3: Allowed users ────────────────────────────────────────────
    current_users = get_env_value("WHATSAPP_ALLOWED_USERS") or ""
    if current_users:
        print(f"✓ Allowed users: {current_users}")
        try:
            response = input("\n  Update allowed users? [y/N] ").strip()
        except (EOFError, KeyboardInterrupt):
            response = "n"
        if response.lower() in ("y", "yes"):
            if wa_mode == "bot":
                phone = input("  Phone numbers that can message the bot (comma-separated): ").strip()
            else:
                phone = input("  Your phone number (e.g. 15551234567): ").strip()
            if phone:
                save_env_value("WHATSAPP_ALLOWED_USERS", phone.replace(" ", ""))
                print(f"  ✓ Updated to: {phone}")
    else:
        print()
        if wa_mode == "bot":
            print("  Who should be allowed to message the bot?")
            phone = input("  Phone numbers (comma-separated, or * for anyone): ").strip()
        else:
            phone = input("  Your phone number (e.g. 15551234567): ").strip()
        if phone:
            save_env_value("WHATSAPP_ALLOWED_USERS", phone.replace(" ", ""))
            print(f"  ✓ Allowed users set: {phone}")
        else:
            print("  ⚠ No allowlist — the agent will respond to ALL incoming messages")

    # ── Step 4: Install bridge dependencies ──────────────────────────────
    project_root = Path(__file__).resolve().parents[1]
    bridge_dir = project_root / "scripts" / "whatsapp-bridge"
    bridge_script = bridge_dir / "bridge.js"

    if not bridge_script.exists():
        print(f"\n✗ Bridge script not found at {bridge_script}")
        return

    if not (bridge_dir / "node_modules").exists():
        print("\n→ Installing WhatsApp bridge dependencies...")
        result = subprocess.run(
            ["npm", "install"],
            cwd=str(bridge_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            print(f"  ✗ npm install failed: {result.stderr}")
            return
        print("  ✓ Dependencies installed")
    else:
        print("✓ Bridge dependencies already installed")

    # ── Step 5: Check for existing session ───────────────────────────────
    session_dir = Path.home() / ".hermes" / "whatsapp" / "session"
    session_dir.mkdir(parents=True, exist_ok=True)

    if (session_dir / "creds.json").exists():
        print("✓ Existing WhatsApp session found")
        try:
            response = input("\n  Re-pair? This will clear the existing session. [y/N] ").strip()
        except (EOFError, KeyboardInterrupt):
            response = "n"
        if response.lower() in ("y", "yes"):
            import shutil
            shutil.rmtree(session_dir, ignore_errors=True)
            session_dir.mkdir(parents=True, exist_ok=True)
            print("  ✓ Session cleared")
        else:
            print("\n✓ WhatsApp is configured and paired!")
            print("  Start the gateway with: hermes gateway")
            return

    # ── Step 6: QR code pairing ──────────────────────────────────────────
    print()
    print("─" * 50)
    if wa_mode == "bot":
        print("📱 Open WhatsApp (or WhatsApp Business) on the")
        print("   phone with the BOT's number, then scan:")
    else:
        print("📱 Open WhatsApp on your phone, then scan:")
    print()
    print("   Settings → Linked Devices → Link a Device")
    print("─" * 50)
    print()

    try:
        subprocess.run(
            ["node", str(bridge_script), "--pair-only", "--session", str(session_dir)],
            cwd=str(bridge_dir),
        )
    except KeyboardInterrupt:
        pass

    # ── Step 7: Post-pairing ─────────────────────────────────────────────
    print()
    if (session_dir / "creds.json").exists():
        print("✓ WhatsApp paired successfully!")
        print()
        if wa_mode == "bot":
            print("  Next steps:")
            print("    1. Start the gateway:  hermes gateway")
            print("    2. Send a message to the bot's WhatsApp number")
            print("    3. The agent will reply automatically")
            print()
            print("  Tip: Agent responses are prefixed with '⚕ Hermes Agent'")
        else:
            print("  Next steps:")
            print("    1. Start the gateway:  hermes gateway")
            print("    2. Open WhatsApp → Message Yourself")
            print("    3. Type a message — the agent will reply")
            print()
            print("  Tip: Agent responses are prefixed with '⚕ Hermes Agent'")
            print("  so you can tell them apart from your own messages.")
        print()
        print("  Or install as a service: hermes gateway install")
    else:
        print("⚠ Pairing may not have completed. Run 'hermes whatsapp' to try again.")


def cmd_setup(args):
    """Asistente de configuracion interactiva."""
    from hermes_cli.setup import run_setup_wizard
    run_setup_wizard(args)


def cmd_model(args):
    """Selecciona modelo predeterminado -- comienza con seleccion de proveedor, luego selector de modelo."""
    from hermes_cli.auth import (
        resolve_provider, get_provider_auth_state, PROVIDER_REGISTRY,
        _prompt_model_selection, _save_model_choice, _update_config_for_provider,
        resolve_nous_runtime_credentials, fetch_nous_models, AuthError, format_auth_error,
        _login_nous,
    )
    from hermes_cli.config import load_config, save_config, get_env_value, save_env_value

    config = load_config()
    current_model = config.get("model")
    if isinstance(current_model, dict):
        current_model = current_model.get("default", "")
    current_model = current_model or "(not set)"

    # Read effective provider the same way the CLI does at startup:
    # config.yaml model.provider > env var > auto-detect
    import os
    config_provider = None
    model_cfg = config.get("model")
    if isinstance(model_cfg, dict):
        config_provider = model_cfg.get("provider")

    effective_provider = (
        os.getenv("HERMES_INFERENCE_PROVIDER")
        or config_provider
        or "auto"
    )
    try:
        active = resolve_provider(effective_provider)
    except AuthError as exc:
        warning = format_auth_error(exc)
        print(f"Warning: {warning} Falling back to auto provider detection.")
        active = resolve_provider("auto")

    # Detectar punto final personalizado
    if active == "openrouter" and get_env_value("OPENAI_BASE_URL"):
        active = "custom"

    provider_labels = {
        "openrouter": "OpenRouter",
        "nous": "Nous Portal",
        "openai-codex": "OpenAI Codex",
        "zai": "Z.AI / GLM",
        "kimi-coding": "Kimi / Moonshot",
        "minimax": "MiniMax",
        "minimax-cn": "MiniMax (China)",
        "custom": "Endpoint personalizado",
    }
    active_label = provider_labels.get(active, active)

    print()
    print(f"  Modelo actual:    {current_model}")
    print(f"  Proveedor activo: {active_label}")
    print()

    # Paso 1: Selección de proveedor — poner proveedor activo primero con marcador
    providers = [
        ("openrouter", "OpenRouter (100+ modelos, paga por uso)"),
        ("nous", "Nous Portal (suscripción Nous Research)"),
        ("openai-codex", "OpenAI Codex"),
        ("zai", "Z.AI / GLM (API directa Zhipu AI)"),
        ("kimi-coding", "Kimi / Moonshot (API directa Moonshot AI)"),
        ("minimax", "MiniMax (API directa global)"),
        ("minimax-cn", "MiniMax China (API directa doméstica)"),
    ]

    # Agregar proveedores personalizados definidos por el usuario desde config.yaml
    custom_providers_cfg = config.get("custom_providers") or []
    _custom_provider_map = {}  # clave → {nombre, base_url, api_key}
    if isinstance(custom_providers_cfg, list):
        for entry in custom_providers_cfg:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name", "").strip()
            base_url = entry.get("base_url", "").strip()
            if not name or not base_url:
                continue
            # Generar una clave estable a partir del nombre
            key = "custom:" + name.lower().replace(" ", "-")
            short_url = base_url.replace("https://", "").replace("http://", "").rstrip("/")
            saved_model = entry.get("model", "")
            model_hint = f" — {saved_model}" if saved_model else ""
            providers.append((key, f"{name} ({short_url}){model_hint}"))
            _custom_provider_map[key] = {
                "name": name,
                "base_url": base_url,
                "api_key": entry.get("api_key", ""),
                "model": saved_model,
            }

    # Siempre agregar la opción de punto final personalizado manual al final
    providers.append(("custom", "Endpoint personalizado (ingresa URL manualmente)"))

    # Agregar opción de eliminación si hay proveedores personalizados guardados
    if _custom_provider_map:
        providers.append(("remove-custom", "Remove a saved custom provider"))

    # Reordenar para que el proveedor activo esté en la parte superior
    known_keys = {k for k, _ in providers}
    active_key = active if active in known_keys else "custom"
    ordered = []
    for key, label in providers:
        if key == active_key:
            ordered.insert(0, (key, f"{label}  ← currently active"))
        else:
            ordered.append((key, label))
    ordered.append(("cancel", "Cancel"))

    provider_idx = _prompt_provider_choice([label for _, label in ordered])
    if provider_idx is None or ordered[provider_idx][0] == "cancel":
        print("No change.")
        return

    selected_provider = ordered[provider_idx][0]

    # Paso 2: Configuración específ ica del proveedor + selección de modelo
    if selected_provider == "openrouter":
        _model_flow_openrouter(config, current_model)
    elif selected_provider == "nous":
        _model_flow_nous(config, current_model)
    elif selected_provider == "openai-codex":
        _model_flow_openai_codex(config, current_model)
    elif selected_provider == "custom":
        _model_flow_custom(config)
    elif selected_provider.startswith("custom:") and selected_provider in _custom_provider_map:
        _model_flow_named_custom(config, _custom_provider_map[selected_provider])
    elif selected_provider == "remove-custom":
        _remove_custom_provider(config)
    elif selected_provider == "kimi-coding":
        _model_flow_kimi(config, current_model)
    elif selected_provider in ("zai", "minimax", "minimax-cn"):
        _model_flow_api_key_provider(config, selected_provider, current_model)


def _prompt_provider_choice(choices):
    """Mostrar menú de selección de proveedor. Devuelve índice o None."""
    try:
        from simple_term_menu import TerminalMenu
        menu_items = [f"  {c}" for c in choices]
        menu = TerminalMenu(
            menu_items, cursor_index=0,
            menu_cursor="-> ", menu_cursor_style=("fg_green", "bold"),
            menu_highlight_style=("fg_green",),
            cycle_cursor=True, clear_screen=False,
            title="Select provider:",
        )
        idx = menu.show()
        print()
        return idx
    except (ImportError, NotImplementedError):
        pass

    # Fallback: numbered list
    print("Select provider:")
    for i, c in enumerate(choices, 1):
        print(f"  {i}. {c}")
    print()
    while True:
        try:
            val = input(f"Choice [1-{len(choices)}]: ").strip()
            if not val:
                return None
            idx = int(val) - 1
            if 0 <= idx < len(choices):
                return idx
            print(f"Please enter 1-{len(choices)}")
        except ValueError:
            print("Please enter a number")
        except (KeyboardInterrupt, EOFError):
            print()
            return None


def _model_flow_openrouter(config, current_model=""):
    """OpenRouter provider: ensure API key, then pick model."""
    from hermes_cli.auth import _prompt_model_selection, _save_model_choice, deactivate_provider
    from hermes_cli.config import get_env_value, save_env_value

    api_key = get_env_value("OPENROUTER_API_KEY")
    if not api_key:
        print("No OpenRouter API key configured.")
        print("Get one at: https://openrouter.ai/keys")
        print()
        try:
            key = input("OpenRouter API key (or Enter to cancel): ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            return
        if not key:
            print("Cancelled.")
            return
        save_env_value("OPENROUTER_API_KEY", key)
        print("API key saved.")
        print()

    from hermes_cli.models import model_ids
    openrouter_models = model_ids()

    selected = _prompt_model_selection(openrouter_models, current_model=current_model)
    if selected:
        # Limpiar cualquier punto final personalizado y establecer proveedor en openrouter
        if get_env_value("OPENAI_BASE_URL"):
            save_env_value("OPENAI_BASE_URL", "")
            save_env_value("OPENAI_API_KEY", "")
        _save_model_choice(selected)

        # Actualizar proveedor de configuración y desactivar cualquier proveedor OAuth
        from hermes_cli.config import load_config, save_config
        cfg = load_config()
        model = cfg.get("model")
        if not isinstance(model, dict):
            model = {"default": model} if model else {}
            cfg["model"] = model
        model["provider"] = "openrouter"
        model["base_url"] = OPENROUTER_BASE_URL
        save_config(cfg)
        deactivate_provider()
        print(f"Default model set to: {selected} (via OpenRouter)")
    else:
        print("No change.")


def _model_flow_nous(config, current_model=""):
    """Nous Portal provider: ensure logged in, then pick model."""
    from hermes_cli.auth import (
        get_provider_auth_state, _prompt_model_selection, _save_model_choice,
        _update_config_for_provider, resolve_nous_runtime_credentials,
        fetch_nous_models, AuthError, format_auth_error,
        _login_nous, PROVIDER_REGISTRY,
    )
    from hermes_cli.config import get_env_value, save_env_value
    import argparse

    state = get_provider_auth_state("nous")
    if not state or not state.get("access_token"):
        print("Not logged into Nous Portal. Starting login...")
        print()
        try:
            mock_args = argparse.Namespace(
                portal_url=None, inference_url=None, client_id=None,
                scope=None, no_browser=False, timeout=15.0,
                ca_bundle=None, insecure=False,
            )
            _login_nous(mock_args, PROVIDER_REGISTRY["nous"])
        except SystemExit:
            print("Login cancelled or failed.")
            return
        except Exception as exc:
            print(f"Login failed: {exc}")
            return
        # _login_nous ya maneja la selección de modelo + actualización de configuración
        return

    # Ya conectado — obtener modelos y seleccionar
    print("Fetching models from Nous Portal...")
    try:
        creds = resolve_nous_runtime_credentials(min_key_ttl_seconds=5 * 60)
        model_ids = fetch_nous_models(
            inference_base_url=creds.get("base_url", ""),
            api_key=creds.get("api_key", ""),
        )
    except Exception as exc:
        relogin = isinstance(exc, AuthError) and exc.relogin_required
        msg = format_auth_error(exc) if isinstance(exc, AuthError) else str(exc)
        if relogin:
            print(f"Session expired: {msg}")
            print("Re-authenticating with Nous Portal...\n")
            try:
                mock_args = argparse.Namespace(
                    portal_url=None, inference_url=None, client_id=None,
                    scope=None, no_browser=False, timeout=15.0,
                    ca_bundle=None, insecure=False,
                )
                _login_nous(mock_args, PROVIDER_REGISTRY["nous"])
            except Exception as login_exc:
                print(f"Re-login failed: {login_exc}")
            return
        print(f"Could not fetch models: {msg}")
        return

    if not model_ids:
        print("No models returned by the inference API.")
        return

    selected = _prompt_model_selection(model_ids, current_model=current_model)
    if selected:
        _save_model_choice(selected)
        # Reactivar Nous como proveedor y actualizar configuración
        inference_url = creds.get("base_url", "")
        _update_config_for_provider("nous", inference_url)
        # Limpiar cualquier punto final personalizado que pueda causar conflicto
        if get_env_value("OPENAI_BASE_URL"):
            save_env_value("OPENAI_BASE_URL", "")
            save_env_value("OPENAI_API_KEY", "")
        print(f"Default model set to: {selected} (via Nous Portal)")
    else:
        print("No change.")


def _model_flow_openai_codex(config, current_model=""):
    """OpenAI Codex provider: ensure logged in, then pick model."""
    from hermes_cli.auth import (
        get_codex_auth_status, _prompt_model_selection, _save_model_choice,
        _update_config_for_provider, _login_openai_codex,
        PROVIDER_REGISTRY, DEFAULT_CODEX_BASE_URL,
    )
    from hermes_cli.codex_models import get_codex_model_ids
    from hermes_cli.config import get_env_value, save_env_value
    import argparse

    status = get_codex_auth_status()
    if not status.get("logged_in"):
        print("Not logged into OpenAI Codex. Starting login...")
        print()
        try:
            mock_args = argparse.Namespace()
            _login_openai_codex(mock_args, PROVIDER_REGISTRY["openai-codex"])
        except SystemExit:
            print("Login cancelled or failed.")
            return
        except Exception as exc:
            print(f"Login failed: {exc}")
            return

    _codex_token = None
    try:
        from hermes_cli.auth import resolve_codex_runtime_credentials
        _codex_creds = resolve_codex_runtime_credentials()
        _codex_token = _codex_creds.get("api_key")
    except Exception:
        pass
    codex_models = get_codex_model_ids(access_token=_codex_token)

    selected = _prompt_model_selection(codex_models, current_model=current_model)
    if selected:
        _save_model_choice(selected)
        _update_config_for_provider("openai-codex", DEFAULT_CODEX_BASE_URL)
        # Limpiar variables de entorno de punto final personalizado que de otro modo anularían Codex.
        if get_env_value("OPENAI_BASE_URL"):
            save_env_value("OPENAI_BASE_URL", "")
            save_env_value("OPENAI_API_KEY", "")
        print(f"Default model set to: {selected} (via OpenAI Codex)")
    else:
        print("No change.")


def _model_flow_custom(config):
    """Punto final personalizado: recopilar URL, clave de API y nombre del modelo.

    Guarda automáticamente el punto final en ``custom_providers`` en config.yaml
    para que aparezca en el menú del proveedor en ejecuciones posteriores.
    """
    from hermes_cli.auth import _save_model_choice, deactivate_provider
    from hermes_cli.config import get_env_value, save_env_value, load_config, save_config

    current_url = get_env_value("OPENAI_BASE_URL") or ""
    current_key = get_env_value("OPENAI_API_KEY") or ""

    print("Custom OpenAI-compatible endpoint configuration:")
    if current_url:
        print(f"  Current URL: {current_url}")
    if current_key:
        print(f"  Current key: {current_key[:8]}...")
    print()

    try:
        base_url = input(f"API base URL [{current_url or 'e.g. https://api.example.com/v1'}]: ").strip()
        api_key = input(f"API key [{current_key[:8] + '...' if current_key else 'optional'}]: ").strip()
        model_name = input("Model name (e.g. gpt-4, llama-3-70b): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return

    if not base_url and not current_url:
        print("No URL provided. Cancelled.")
        return

    # Validar formato de URL
    effective_url = base_url or current_url
    if not effective_url.startswith(("http://", "https://")):
        print(f"Invalid URL: {effective_url} (must start with http:// or https://)")
        return

    effective_key = api_key or current_key

    if base_url:
        save_env_value("OPENAI_BASE_URL", base_url)
    if api_key:
        save_env_value("OPENAI_API_KEY", api_key)

    if model_name:
        _save_model_choice(model_name)

        # Actualizar configuración y desactivar cualquier proveedor OAuth
        cfg = load_config()
        model = cfg.get("model")
        if not isinstance(model, dict):
            model = {"default": model} if model else {}
            cfg["model"] = model
        model["provider"] = "custom"
        model["base_url"] = effective_url
        save_config(cfg)
        deactivate_provider()

        print(f"Default model set to: {model_name} (via {effective_url})")
    else:
        if base_url or api_key:
            deactivate_provider()
        print("Endpoint saved. Use `/model` in chat or `hermes model` to set a model.")

    # Guardar automáticamente en custom_providers para que aparezca en el menú la próxima vez
    _save_custom_provider(effective_url, effective_key, model_name or "")


def _save_custom_provider(base_url, api_key="", model=""):
    """Guardar un punto final personalizado en custom_providers en config.yaml.

    Desuplicado por base_url — si la URL ya existe, actualiza el
    nombre del modelo pero no agrega una entrada duplicada.
    Genera automáticamente un nombre para mostrar desde el nombre de host de la URL.
    """
    from hermes_cli.config import load_config, save_config

    cfg = load_config()
    providers = cfg.get("custom_providers") or []
    if not isinstance(providers, list):
        providers = []

    # Comprobar si esta URL ya está guardada — actualizar modelo si es así
    for entry in providers:
        if isinstance(entry, dict) and entry.get("base_url", "").rstrip("/") == base_url.rstrip("/"):
            if model and entry.get("model") != model:
                entry["model"] = model
                cfg["custom_providers"] = providers
                save_config(cfg)
            return  # already saved, updated model if needed

    # Generar automáticamente un nombre a partir de la URL
    import re
    clean = base_url.replace("https://", "").replace("http://", "").rstrip("/")
    # Eliminar el sufijo /v1 para nombres más limpios
    clean = re.sub(r"/v1/?$", "", clean)
    # Usar hostname:port como el nombre
    name = clean.split("/")[0]
    # Mayúsculas para legibilidad
    if "localhost" in name or "127.0.0.1" in name:
        name = f"Local ({name})"
    elif "runpod" in name.lower():
        name = f"RunPod ({name})"
    else:
        name = name.capitalize()

    entry = {"name": name, "base_url": base_url}
    if api_key:
        entry["api_key"] = api_key
    if model:
        entry["model"] = model

    providers.append(entry)
    cfg["custom_providers"] = providers
    save_config(cfg)
    print(f"  💾 Saved to custom providers as \"{name}\" (edit in config.yaml)")


def _remove_custom_provider(config):
    """Permitir que el usuario elimine un proveedor personalizado guardado de config.yaml."""
    from hermes_cli.config import load_config, save_config

    cfg = load_config()
    providers = cfg.get("custom_providers") or []
    if not isinstance(providers, list) or not providers:
        print("No custom providers configured.")
        return

    print("Remove a custom provider:\n")

    choices = []
    for entry in providers:
        if isinstance(entry, dict):
            name = entry.get("name", "unnamed")
            url = entry.get("base_url", "")
            short_url = url.replace("https://", "").replace("http://", "").rstrip("/")
            choices.append(f"{name} ({short_url})")
        else:
            choices.append(str(entry))
    choices.append("Cancel")

    try:
        from simple_term_menu import TerminalMenu
        menu = TerminalMenu(
            [f"  {c}" for c in choices], cursor_index=0,
            menu_cursor="-> ", menu_cursor_style=("fg_red", "bold"),
            menu_highlight_style=("fg_red",),
            cycle_cursor=True, clear_screen=False,
            title="Select provider to remove:",
        )
        idx = menu.show()
        print()
    except (ImportError, NotImplementedError):
        for i, c in enumerate(choices, 1):
            print(f"  {i}. {c}")
        print()
        try:
            val = input(f"Choice [1-{len(choices)}]: ").strip()
            idx = int(val) - 1 if val else None
        except (ValueError, KeyboardInterrupt, EOFError):
            idx = None

    if idx is None or idx >= len(providers):
        print("No change.")
        return

    removed = providers.pop(idx)
    cfg["custom_providers"] = providers
    save_config(cfg)
    removed_name = removed.get("name", "unnamed") if isinstance(removed, dict) else str(removed)
    print(f"✅ Removed \"{removed_name}\" from custom providers.")


def _model_flow_named_custom(config, provider_info):
    """Handle a named custom provider from config.yaml custom_providers list.

    If the entry has a saved model name, activates it immediately.
    Otherwise probes the endpoint's /models API to let the user pick one.
    """
    from hermes_cli.auth import _save_model_choice, deactivate_provider
    from hermes_cli.config import save_env_value, load_config, save_config
    from hermes_cli.models import fetch_api_models

    name = provider_info["name"]
    base_url = provider_info["base_url"]
    api_key = provider_info.get("api_key", "")
    saved_model = provider_info.get("model", "")

    # If a model is saved, just activate immediately — no probing needed
    if saved_model:
        save_env_value("OPENAI_BASE_URL", base_url)
        if api_key:
            save_env_value("OPENAI_API_KEY", api_key)
        _save_model_choice(saved_model)

        cfg = load_config()
        model = cfg.get("model")
        if not isinstance(model, dict):
            model = {"default": model} if model else {}
            cfg["model"] = model
        model["provider"] = "custom"
        model["base_url"] = base_url
        save_config(cfg)
        deactivate_provider()

        print(f"✅ Switched to: {saved_model}")
        print(f"   Provider: {name} ({base_url})")
        return

    # No saved model — probe endpoint and let user pick
    print(f"  Provider: {name}")
    print(f"  URL:      {base_url}")
    print()
    print("No model saved for this provider. Fetching available models...")
    models = fetch_api_models(api_key, base_url, timeout=8.0)

    if models:
        print(f"Found {len(models)} model(s):\n")
        try:
            from simple_term_menu import TerminalMenu
            menu_items = [f"  {m}" for m in models] + ["  Cancel"]
            menu = TerminalMenu(
                menu_items, cursor_index=0,
                menu_cursor="-> ", menu_cursor_style=("fg_green", "bold"),
                menu_highlight_style=("fg_green",),
                cycle_cursor=True, clear_screen=False,
                title=f"Select model from {name}:",
            )
            idx = menu.show()
            print()
            if idx is None or idx >= len(models):
                print("Cancelled.")
                return
            model_name = models[idx]
        except (ImportError, NotImplementedError):
            for i, m in enumerate(models, 1):
                print(f"  {i}. {m}")
            print(f"  {len(models) + 1}. Cancel")
            print()
            try:
                val = input(f"Choice [1-{len(models) + 1}]: ").strip()
                if not val:
                    print("Cancelled.")
                    return
                idx = int(val) - 1
                if idx < 0 or idx >= len(models):
                    print("Cancelled.")
                    return
                model_name = models[idx]
            except (ValueError, KeyboardInterrupt, EOFError):
                print("\nCancelled.")
                return
    else:
        print("Could not fetch models from endpoint. Enter model name manually.")
        try:
            model_name = input("Model name: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            return
        if not model_name:
            print("No model specified. Cancelled.")
            return

    # Activar y guardar el modelo en la entrada custom_providers
    save_env_value("OPENAI_BASE_URL", base_url)
    if api_key:
        save_env_value("OPENAI_API_KEY", api_key)
    _save_model_choice(model_name)

    cfg = load_config()
    model = cfg.get("model")
    if not isinstance(model, dict):
        model = {"default": model} if model else {}
        cfg["model"] = model
    model["provider"] = "custom"
    model["base_url"] = base_url
    save_config(cfg)
    deactivate_provider()

    # Guardar el nombre del modelo en la entrada custom_providers para la próxima vez
    _save_custom_provider(base_url, api_key, model_name)

    print(f"\n✅ Model set to: {model_name}")
    print(f"   Provider: {name} ({base_url})")


# Listas de modelos seleccionados para proveedores de clave de API directa
_PROVIDER_MODELS = {
    "zai": [
        "glm-5",
        "glm-4.7",
        "glm-4.5",
        "glm-4.5-flash",
    ],
    "kimi-coding": [
        "kimi-for-coding",
        "kimi-k2.5",
        "kimi-k2-thinking",
        "kimi-k2-thinking-turbo",
        "kimi-k2-turbo-preview",
        "kimi-k2-0905-preview",
    ],
    "minimax": [
        "MiniMax-M2.5",
        "MiniMax-M2.5-highspeed",
        "MiniMax-M2.1",
    ],
    "minimax-cn": [
        "MiniMax-M2.5",
        "MiniMax-M2.5-highspeed",
        "MiniMax-M2.1",
    ],
}


def _model_flow_kimi(config, current_model=""):
    """Selección de modelo Kimi / Moonshot con enrutamiento automático de puntos finales.

    - Claves sk-kimi-* → api.kimi.com/coding/v1  (Plan de Codificación Kimi)
    - Otras claves   → api.moonshot.ai/v1      (Moonshot heredado)

    Sin solicitud de URL base manual — el punto final se determina por el prefijo de clave.
    """
    from hermes_cli.auth import (
        PROVIDER_REGISTRY, KIMI_CODE_BASE_URL, _prompt_model_selection,
        _save_model_choice, deactivate_provider,
    )
    from hermes_cli.config import get_env_value, save_env_value, load_config, save_config

    provider_id = "kimi-coding"
    pconfig = PROVIDER_REGISTRY[provider_id]
    key_env = pconfig.api_key_env_vars[0] if pconfig.api_key_env_vars else ""
    base_url_env = pconfig.base_url_env_var or ""

    # Paso 1: Comprobar / pedir clave de API
    existing_key = ""
    for ev in pconfig.api_key_env_vars:
        existing_key = get_env_value(ev) or os.getenv(ev, "")
        if existing_key:
            break

    if not existing_key:
        print(f"No {pconfig.name} API key configured.")
        if key_env:
            try:
                new_key = input(f"{key_env} (or Enter to cancel): ").strip()
            except (KeyboardInterrupt, EOFError):
                print()
                return
            if not new_key:
                print("Cancelled.")
                return
            save_env_value(key_env, new_key)
            existing_key = new_key
            print("API key saved.")
            print()
    else:
        print(f"  {pconfig.name} API key: {existing_key[:8]}... ✓")
        print()

    # Paso 2: Detectar automáticamente punto final del prefijo de clave
    is_coding_plan = existing_key.startswith("sk-kimi-")
    if is_coding_plan:
        effective_base = KIMI_CODE_BASE_URL
        print(f"  Detected Kimi Coding Plan key → {effective_base}")
    else:
        effective_base = pconfig.inference_base_url
        print(f"  Using Moonshot endpoint → {effective_base}")
    # Limpiar cualquier anulación de URL base manual para que la detección automática funcione en tiempo de ejecución
    if base_url_env and get_env_value(base_url_env):
        save_env_value(base_url_env, "")
    print()

    # Paso 3: Selección de modelo — mostrar modelos apropiados para el punto final
    if is_coding_plan:
        # Coding Plan models (kimi-for-coding first)
        model_list = [
            "kimi-for-coding",
            "kimi-k2.5",
            "kimi-k2-thinking",
            "kimi-k2-thinking-turbo",
        ]
    else:
        # Legacy Moonshot models
        model_list = _PROVIDER_MODELS.get(provider_id, [])

    if model_list:
        selected = _prompt_model_selection(model_list, current_model=current_model)
    else:
        try:
            selected = input("Enter model name: ").strip()
        except (KeyboardInterrupt, EOFError):
            selected = None

    if selected:
        # Limpiar punto final personalizado si está configurado (evitar confusión)
        if get_env_value("OPENAI_BASE_URL"):
            save_env_value("OPENAI_BASE_URL", "")
            save_env_value("OPENAI_API_KEY", "")

        _save_model_choice(selected)

        # Actualizar configuración con proveedor y URL base
        cfg = load_config()
        model = cfg.get("model")
        if not isinstance(model, dict):
            model = {"default": model} if model else {}
            cfg["model"] = model
        model["provider"] = provider_id
        model["base_url"] = effective_base
        save_config(cfg)
        deactivate_provider()

        endpoint_label = "Kimi Coding" if is_coding_plan else "Moonshot"
        print(f"Default model set to: {selected} (via {endpoint_label})")
    else:
        print("No change.")


def _model_flow_api_key_provider(config, provider_id, current_model=""):
    """Flujo genérico para proveedores de clave de API (z.ai, MiniMax)."""
    from hermes_cli.auth import (
        PROVIDER_REGISTRY, _prompt_model_selection, _save_model_choice,
        _update_config_for_provider, deactivate_provider,
    )
    from hermes_cli.config import get_env_value, save_env_value, load_config, save_config

    pconfig = PROVIDER_REGISTRY[provider_id]
    key_env = pconfig.api_key_env_vars[0] if pconfig.api_key_env_vars else ""
    base_url_env = pconfig.base_url_env_var or ""

    # Comprobar / pedir clave de API
    existing_key = ""
    for ev in pconfig.api_key_env_vars:
        existing_key = get_env_value(ev) or os.getenv(ev, "")
        if existing_key:
            break

    if not existing_key:
        print(f"No {pconfig.name} API key configured.")
        if key_env:
            try:
                new_key = input(f"{key_env} (or Enter to cancel): ").strip()
            except (KeyboardInterrupt, EOFError):
                print()
                return
            if not new_key:
                print("Cancelled.")
                return
            save_env_value(key_env, new_key)
            print("API key saved.")
            print()
    else:
        print(f"  {pconfig.name} API key: {existing_key[:8]}... ✓")
        print()

    # Anulación de URL base opcional
    current_base = ""
    if base_url_env:
        current_base = get_env_value(base_url_env) or os.getenv(base_url_env, "")
    effective_base = current_base or pconfig.inference_base_url

    try:
        override = input(f"Base URL [{effective_base}]: ").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        override = ""
    if override and base_url_env:
        save_env_value(base_url_env, override)
        effective_base = override

    # Selección de modelo
    model_list = _PROVIDER_MODELS.get(provider_id, [])
    if model_list:
        selected = _prompt_model_selection(model_list, current_model=current_model)
    else:
        try:
            selected = input("Model name: ").strip()
        except (KeyboardInterrupt, EOFError):
            selected = None

    if selected:
        # Limpiar punto final personalizado si está configurado (evitar confusión)
        if get_env_value("OPENAI_BASE_URL"):
            save_env_value("OPENAI_BASE_URL", "")
            save_env_value("OPENAI_API_KEY", "")

        _save_model_choice(selected)

        # Actualizar configuración con proveedor y URL base
        cfg = load_config()
        model = cfg.get("model")
        if not isinstance(model, dict):
            model = {"default": model} if model else {}
            cfg["model"] = model
        model["provider"] = provider_id
        model["base_url"] = effective_base
        save_config(cfg)
        deactivate_provider()

        print(f"Default model set to: {selected} (via {pconfig.name})")
    else:
        print("No change.")


def cmd_login(args):
    """Autentica Hermes CLI con un proveedor."""
    from hermes_cli.auth import login_command
    login_command(args)


def cmd_logout(args):
    """Limpia autenticacion del proveedor."""
    from hermes_cli.auth import logout_command
    logout_command(args)


def cmd_status(args):
    """Muestra estado de todos los componentes."""
    from hermes_cli.status import show_status
    show_status(args)


def cmd_cron(args):
    """Gestion de trabajos cron."""
    from hermes_cli.cron import cron_command
    cron_command(args)


def cmd_doctor(args):
    """Verifica configuracion y dependencias."""
    from hermes_cli.doctor import run_doctor
    run_doctor(args)


def cmd_config(args):
    """Gestion de configuracion."""
    from hermes_cli.config import config_command
    config_command(args)


def cmd_version(args):
    """Muestra version."""
    print(f"Hermes Agent v{__version__} ({__release_date__})")
    print(f"Proyecto: {PROJECT_ROOT}")
    
    # Mostrar version de Python
    print(f"Python: {sys.version.split()[0]}")
    
    # Comprobar dependencias principales
    try:
        import openai
        print(f"OpenAI SDK: {openai.__version__}")
    except ImportError:
        print("OpenAI SDK: No instalado")


def cmd_uninstall(args):
    """Desinstala Hermes Agent."""
    from hermes_cli.uninstall import run_uninstall
    run_uninstall(args)


def _update_via_zip(args):
    """Actualiza Hermes Agent descargando un archivo ZIP.
    
    Se usa en Windows cuando el I/O de archivos git esta roto (antivirus, controladores de filtro NTFS
    causando errores 'Argumento invalido' en la creacion de archivos).
    """
    import shutil
    import tempfile
    import zipfile
    from urllib.request import urlretrieve
    
    branch = "main"
    zip_url = f"https://github.com/NousResearch/hermes-agent/archive/refs/heads/{branch}.zip"
    
    print("→ Descargando ultima version...")
    try:
        tmp_dir = tempfile.mkdtemp(prefix="hermes-update-")
        zip_path = os.path.join(tmp_dir, f"hermes-agent-{branch}.zip")
        urlretrieve(zip_url, zip_path)
        
        print("→ Extrayendo...")
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(tmp_dir)
        
        # Los ZIP de GitHub se extraen a hermes-agent-<rama>/
        extracted = os.path.join(tmp_dir, f"hermes-agent-{branch}")
        if not os.path.isdir(extracted):
            # Intentar encontrarlo
            for d in os.listdir(tmp_dir):
                candidate = os.path.join(tmp_dir, d)
                if os.path.isdir(candidate) and d != "__MACOSX":
                    extracted = candidate
                    break
        
        # Copiar archivos actualizados sobre la instalación existente, preservando venv/node_modules/.git
        preserve = {'venv', 'node_modules', '.git', '__pycache__', '.env'}
        update_count = 0
        for item in os.listdir(extracted):
            if item in preserve:
                continue
            src = os.path.join(extracted, item)
            dst = os.path.join(str(PROJECT_ROOT), item)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            update_count += 1
        
        print(f"✓ Updated {update_count} items from ZIP")
        
        # Limpiar
        shutil.rmtree(tmp_dir, ignore_errors=True)
        
    except Exception as e:
        print(f"✗ ZIP update failed: {e}")
        sys.exit(1)
    
    # Reinstalar dependencias de Python
    print("→ Updating Python dependencies...")
    import subprocess
    uv_bin = shutil.which("uv")
    if uv_bin:
        subprocess.run(
            [uv_bin, "pip", "install", "-e", ".", "--quiet"],
            cwd=PROJECT_ROOT, check=True,
            env={**os.environ, "VIRTUAL_ENV": str(PROJECT_ROOT / "venv")}
        )
    else:
        venv_pip = PROJECT_ROOT / "venv" / ("Scripts" if sys.platform == "win32" else "bin") / "pip"
        if venv_pip.exists():
            subprocess.run([str(venv_pip), "install", "-e", ".", "--quiet"], cwd=PROJECT_ROOT, check=True)
    
    # Sincronizar habilidades
    try:
        from tools.skills_sync import sync_skills
        print("→ Syncing bundled skills...")
        result = sync_skills(quiet=True)
        if result["copied"]:
            print(f"  + {len(result['copied'])} new: {', '.join(result['copied'])}")
        if result.get("updated"):
            print(f"  ↑ {len(result['updated'])} updated: {', '.join(result['updated'])}")
        if result.get("user_modified"):
            print(f"  ~ {len(result['user_modified'])} user-modified (kept)")
        if result.get("cleaned"):
            print(f"  − {len(result['cleaned'])} removed from manifest")
        if not result["copied"] and not result.get("updated"):
            print("  ✓ Skills are up to date")
    except Exception:
        pass
    
    print()
    print("✓ Update complete!")


def cmd_update(args):
    """Update Hermes Agent to the latest version."""
    import subprocess
    import shutil
    
    print("⚕ Updating Hermes Agent...")
    print()
    
    # Try git-based update first, fall back to ZIP download on Windows
    # when git file I/O is broken (antivirus, NTFS filter drivers, etc.)
    use_zip_update = False
    git_dir = PROJECT_ROOT / '.git'
    
    if not git_dir.exists():
        if sys.platform == "win32":
            use_zip_update = True
        else:
            print("✗ Not a git repository. Please reinstall:")
            print("  curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash")
            sys.exit(1)
    
    # On Windows, git can fail with "unable to write loose object file: Invalid argument"
    # due to filesystem atomicity issues. Set the recommended workaround.
    if sys.platform == "win32" and git_dir.exists():
        subprocess.run(
            ["git", "-c", "windows.appendAtomically=false", "config", "windows.appendAtomically", "false"],
            cwd=PROJECT_ROOT, check=False, capture_output=True
        )

    if use_zip_update:
        # ZIP-based update for Windows when git is broken
        _update_via_zip(args)
        return

    # Fetch and pull
    try:
        print("→ Fetching updates...")
        git_cmd = ["git"]
        if sys.platform == "win32":
            git_cmd = ["git", "-c", "windows.appendAtomically=false"]
        
        subprocess.run(git_cmd + ["fetch", "origin"], cwd=PROJECT_ROOT, check=True)
        
        # Get current branch
        result = subprocess.run(
            git_cmd + ["rev-parse", "--abbrev-ref", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        branch = result.stdout.strip()
        
        # Comprobar si hay actualizaciones
        result = subprocess.run(
            git_cmd + ["rev-list", f"HEAD..origin/{branch}", "--count"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        commit_count = int(result.stdout.strip())
        
        if commit_count == 0:
            print("✓ Already up to date!")
            return
        
        print(f"→ Found {commit_count} new commit(s)")
        print("→ Pulling updates...")
        subprocess.run(git_cmd + ["pull", "origin", branch], cwd=PROJECT_ROOT, check=True)
        
        # Reinstall Python dependencies (prefer uv for speed, fall back to pip)
        print("→ Updating Python dependencies...")
        uv_bin = shutil.which("uv")
        if uv_bin:
            subprocess.run(
                [uv_bin, "pip", "install", "-e", ".", "--quiet"],
                cwd=PROJECT_ROOT, check=True,
                env={**os.environ, "VIRTUAL_ENV": str(PROJECT_ROOT / "venv")}
            )
        else:
            venv_pip = PROJECT_ROOT / "venv" / ("Scripts" if sys.platform == "win32" else "bin") / "pip"
            if venv_pip.exists():
                subprocess.run([str(venv_pip), "install", "-e", ".", "--quiet"], cwd=PROJECT_ROOT, check=True)
            else:
                subprocess.run(["pip", "install", "-e", ".", "--quiet"], cwd=PROJECT_ROOT, check=True)
        
        # Comprobar dependencias de Node.js
        if (PROJECT_ROOT / "package.json").exists():
            import shutil
            if shutil.which("npm"):
                print("→ Updating Node.js dependencies...")
                subprocess.run(["npm", "install", "--silent"], cwd=PROJECT_ROOT, check=False)
        
        print()
        print("✓ Code updated!")
        
        # Sincronizar habilidades incluidas (copia nuevas, actualiza cambios, respeta eliminaciones del usuario)
        try:
            from tools.skills_sync import sync_skills
            print()
            print("→ Syncing bundled skills...")
            result = sync_skills(quiet=True)
            if result["copied"]:
                print(f"  + {len(result['copied'])} new: {', '.join(result['copied'])}")
            if result.get("updated"):
                print(f"  ↑ {len(result['updated'])} updated: {', '.join(result['updated'])}")
            if result.get("user_modified"):
                print(f"  ~ {len(result['user_modified'])} user-modified (kept)")
            if result.get("cleaned"):
                print(f"  − {len(result['cleaned'])} removed from manifest")
            if not result["copied"] and not result.get("updated"):
                print("  ✓ Skills are up to date")
        except Exception as e:
            logger.debug("Skills sync during update failed: %s", e)
        
        # Comprobar migraciones de configuración
        print()
        print("→ Checking configuration for new options...")
        
        from hermes_cli.config import (
            get_missing_env_vars, get_missing_config_fields, 
            check_config_version, migrate_config
        )
        
        missing_env = get_missing_env_vars(required_only=True)
        missing_config = get_missing_config_fields()
        current_ver, latest_ver = check_config_version()
        
        needs_migration = missing_env or missing_config or current_ver < latest_ver
        
        if needs_migration:
            print()
            if missing_env:
                print(f"  ⚠️  {len(missing_env)} new required setting(s) need configuration")
            if missing_config:
                print(f"  ℹ️  {len(missing_config)} new config option(s) available")
            
            print()
            response = input("Would you like to configure them now? [Y/n]: ").strip().lower()
            
            if response in ('', 'y', 'yes'):
                print()
                results = migrate_config(interactive=True, quiet=False)
                
                if results["env_added"] or results["config_added"]:
                    print()
                    print("✓ Configuration updated!")
            else:
                print()
                print("Skipped. Run 'hermes config migrate' later to configure.")
        else:
            print("  ✓ Configuration is up to date")
        
        print()
        print("✓ Update complete!")
        
        # Reinicio automático del gateway si se está ejecutando como servicio systemd
        try:
            check = subprocess.run(
                ["systemctl", "--user", "is-active", "hermes-gateway"],
                capture_output=True, text=True, timeout=5,
            )
            if check.stdout.strip() == "active":
                print()
                print("→ Gateway service is running — restarting to pick up changes...")
                restart = subprocess.run(
                    ["systemctl", "--user", "restart", "hermes-gateway"],
                    capture_output=True, text=True, timeout=15,
                )
                if restart.returncode == 0:
                    print("✓ Gateway restarted.")
                else:
                    print(f"⚠ Gateway restart failed: {restart.stderr.strip()}")
                    print("  Try manually: hermes gateway restart")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass  # No systemd (macOS, WSL1, etc.) — skip silently
        
        print()
        print("Tip: You can now select a provider and model:")
        print("  hermes model              # Select provider and model")
        
    except subprocess.CalledProcessError as e:
        if sys.platform == "win32":
            print(f"⚠ Git update failed: {e}")
            print("→ Falling back to ZIP download...")
            print()
            _update_via_zip(args)
        else:
            print(f"✗ Update failed: {e}")
            sys.exit(1)


def _coalesce_session_name_args(argv: list) -> list:
    """Join unquoted multi-word session names after -c/--continue and -r/--resume.

    When a user types ``hermes -c Pokemon Agent Dev`` without quoting the
    session name, argparse sees three separate tokens.  This function merges
    them into a single argument so argparse receives
    ``['-c', 'Pokemon Agent Dev']`` instead.

    Tokens are collected after the flag until we hit another flag (``-*``)
    or a known top-level subcommand.
    """
    _SUBCOMMANDS = {
        "chat", "model", "gateway", "setup", "whatsapp", "login", "logout",
        "status", "cron", "doctor", "config", "pairing", "skills", "tools",
        "sessions", "insights", "version", "update", "uninstall",
    }
    _SESSION_FLAGS = {"-c", "--continue", "-r", "--resume"}

    result = []
    i = 0
    while i < len(argv):
        token = argv[i]
        if token in _SESSION_FLAGS:
            result.append(token)
            i += 1
            # Collect subsequent non-flag, non-subcommand tokens as one name
            parts: list = []
            while i < len(argv) and not argv[i].startswith("-") and argv[i] not in _SUBCOMMANDS:
                parts.append(argv[i])
                i += 1
            if parts:
                result.append(" ".join(parts))
        else:
            result.append(token)
            i += 1
    return result


def main():
    """Main entry point for hermes CLI."""
    parser = argparse.ArgumentParser(
        prog="hermes",
        description="Hermes Agent - AI assistant with tool-calling capabilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    hermes                        Start interactive chat
    hermes chat -q "Hello"        Single query mode
    hermes -c                     Resume the most recent session
    hermes -c "my project"        Resume a session by name (latest in lineage)
    hermes --resume <session_id>  Resume a specific session by ID
    hermes setup                  Run setup wizard
    hermes logout                 Clear stored authentication
    hermes model                  Select default model
    hermes config                 View configuration
    hermes config edit            Edit config in $EDITOR
    hermes config set model gpt-4 Set a config value
    hermes gateway                Run messaging gateway
    hermes -w                     Start in isolated git worktree
    hermes gateway install        Install as system service
    hermes sessions list          List past sessions
    hermes sessions browse        Interactive session picker
    hermes sessions rename ID T   Rename/title a session
    hermes update                 Update to latest version

For more help on a command:
    hermes <command> --help
"""
    )
    
    parser.add_argument(
        "--version", "-V",
        action="store_true",
        help="Mostrar versión y salir"
    )
    parser.add_argument(
        "--resume", "-r",
        metavar="SESSION",
        default=None,
        help="Reanudar una sesión anterior por ID o título"
    )
    parser.add_argument(
        "--continue", "-c",
        dest="continue_last",
        nargs="?",
        const=True,
        default=None,
        metavar="SESSION_NAME",
        help="Resume a session by name, or the most recent if no name given"
    )
    parser.add_argument(
        "--worktree", "-w",
        action="store_true",
        default=False,
        help="Ejecutar en un worktree git aislado (para agentes paralelos)"
    )
    parser.add_argument(
        "--yolo",
        action="store_true",
        default=False,
        help="Bypass all dangerous command approval prompts (use at your own risk)"
    )
    parser.add_argument(
        "--pass-session-id",
        action="store_true",
        default=False,
        help="Include the session ID in the agent's system prompt"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")
    
    # =========================================================================
    # chat command
    # =========================================================================
    chat_parser = subparsers.add_parser(
        "chat",
        help="Chat interactivo con el agente",
        description="Start an interactive chat session with Hermes Agent"
    )
    chat_parser.add_argument(
        "-q", "--query",
        help="Consulta única (modo no interactivo)"
    )
    chat_parser.add_argument(
        "-m", "--model",
        help="Modelo a usar (ej: anthropic/claude-sonnet-4)"
    )
    chat_parser.add_argument(
        "-t", "--toolsets",
        help="Toolsets separados por comas a habilitar"
    )
    chat_parser.add_argument(
        "--provider",
        choices=["auto", "openrouter", "nous", "openai-codex", "zai", "kimi-coding", "minimax", "minimax-cn"],
        default=None,
        help="Proveedor de inferencia (predeterminado: auto)"
    )
    chat_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Salida de modo verboso"
    )
    chat_parser.add_argument(
        "-Q", "--quiet",
        action="store_true",
        help="Modo de silencio para uso programático: suprimir banner, spinner y vistas previas de herramientas. Solo mostrar la respuesta final e información de sesión."
    )
    chat_parser.add_argument(
        "--resume", "-r",
        metavar="SESSION_ID",
        help="Reanudar una sesión anterior por ID (mostrado al salir)"
    )
    chat_parser.add_argument(
        "--continue", "-c",
        dest="continue_last",
        nargs="?",
        const=True,
        default=None,
        metavar="SESSION_NAME",
        help="Resume a session by name, or the most recent if no name given"
    )
    chat_parser.add_argument(
        "--worktree", "-w",
        action="store_true",
        default=False,
        help="Ejecutar en un worktree git aislado (para agentes paralelos en el mismo repo)"
    )
    chat_parser.add_argument(
        "--checkpoints",
        action="store_true",
        default=False,
        help="Habilitar checkpoints del sistema de archivos antes de operaciones destructivas de archivos (usa /rollback para restaurar)"
    )
    chat_parser.add_argument(
        "--yolo",
        action="store_true",
        default=False,
        help="Bypass all dangerous command approval prompts (use at your own risk)"
    )
    chat_parser.add_argument(
        "--pass-session-id",
        action="store_true",
        default=False,
        help="Include the session ID in the agent's system prompt"
    )
    chat_parser.set_defaults(func=cmd_chat)

    # =========================================================================
    # comando de modelo
    # =========================================================================
    model_parser = subparsers.add_parser(
        "model",
        help="Seleccionar proveedor y modelo predeterminado",
        description="Interactively select your inference provider and default model"
    )
    model_parser.set_defaults(func=cmd_model)

    # =========================================================================
    # gateway command
    # =========================================================================
    gateway_parser = subparsers.add_parser(
        "gateway",
        help="Gestión del gateway de mensajería",
        description="Manage the messaging gateway (Telegram, Discord, WhatsApp)"
    )
    gateway_subparsers = gateway_parser.add_subparsers(dest="gateway_command")
    
    # gateway run (default)
    gateway_run = gateway_subparsers.add_parser("run", help="Ejecutar gateway en primer plano")
    gateway_run.add_argument("-v", "--verbose", action="store_true")
    gateway_run.add_argument("--replace", action="store_true",
                             help="Reemplazar cualquier instancia de gateway existente (útil para systemd)")
    
    # gateway start
    gateway_start = gateway_subparsers.add_parser("start", help="Iniciar servicio del gateway")
    
    # gateway stop
    gateway_stop = gateway_subparsers.add_parser("stop", help="Detener servicio del gateway")
    
    # gateway restart
    gateway_restart = gateway_subparsers.add_parser("restart", help="Reiniciar servicio del gateway")
    
    # gateway status
    gateway_status = gateway_subparsers.add_parser("status", help="Mostrar estado del gateway")
    gateway_status.add_argument("--deep", action="store_true", help="Comprobación de estado profundo")
    
    # gateway install
    gateway_install = gateway_subparsers.add_parser("install", help="Instalar gateway como servicio")
    gateway_install.add_argument("--force", action="store_true", help="Forzar reinstalación")
    
    # gateway uninstall
    gateway_uninstall = gateway_subparsers.add_parser("uninstall", help="Uninstall gateway service")

    # gateway setup
    gateway_setup = gateway_subparsers.add_parser("setup", help="Configure messaging platforms")

    gateway_parser.set_defaults(func=cmd_gateway)
    
    # =========================================================================
    # setup command
    # =========================================================================
    setup_parser = subparsers.add_parser(
        "setup",
        help="Interactive setup wizard",
        description="Configure Hermes Agent with an interactive wizard. "
                    "Run a specific section: hermes setup model|terminal|gateway|tools|agent"
    )
    setup_parser.add_argument(
        "section",
        nargs="?",
        choices=["model", "terminal", "gateway", "tools", "agent"],
        default=None,
        help="Run a specific setup section instead of the full wizard"
    )
    setup_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Non-interactive mode (use defaults/env vars)"
    )
    setup_parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset configuration to defaults"
    )
    setup_parser.set_defaults(func=cmd_setup)

    # =========================================================================
    # whatsapp command
    # =========================================================================
    whatsapp_parser = subparsers.add_parser(
        "whatsapp",
        help="Set up WhatsApp integration",
        description="Configure WhatsApp and pair via QR code"
    )
    whatsapp_parser.set_defaults(func=cmd_whatsapp)

    # =========================================================================
    # login command
    # =========================================================================
    login_parser = subparsers.add_parser(
        "login",
        help="Authenticate with an inference provider",
        description="Run OAuth device authorization flow for Hermes CLI"
    )
    login_parser.add_argument(
        "--provider",
        choices=["nous", "openai-codex"],
        default=None,
        help="Provider to authenticate with (default: nous)"
    )
    login_parser.add_argument(
        "--portal-url",
        help="Portal base URL (default: production portal)"
    )
    login_parser.add_argument(
        "--inference-url",
        help="Inference API base URL (default: production inference API)"
    )
    login_parser.add_argument(
        "--client-id",
        default=None,
        help="OAuth client id to use (default: hermes-cli)"
    )
    login_parser.add_argument(
        "--scope",
        default=None,
        help="OAuth scope to request"
    )
    login_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not attempt to open the browser automatically"
    )
    login_parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="HTTP request timeout in seconds (default: 15)"
    )
    login_parser.add_argument(
        "--ca-bundle",
        help="Path to CA bundle PEM file for TLS verification"
    )
    login_parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS verification (testing only)"
    )
    login_parser.set_defaults(func=cmd_login)

    # =========================================================================
    # logout command
    # =========================================================================
    logout_parser = subparsers.add_parser(
        "logout",
        help="Clear authentication for an inference provider",
        description="Remove stored credentials and reset provider config"
    )
    logout_parser.add_argument(
        "--provider",
        choices=["nous", "openai-codex"],
        default=None,
        help="Provider to log out from (default: active provider)"
    )
    logout_parser.set_defaults(func=cmd_logout)

    # =========================================================================
    # status command
    # =========================================================================
    status_parser = subparsers.add_parser(
        "status",
        help="Show status of all components",
        description="Display status of Hermes Agent components"
    )
    status_parser.add_argument(
        "--all",
        action="store_true",
        help="Show all details (redacted for sharing)"
    )
    status_parser.add_argument(
        "--deep",
        action="store_true",
        help="Run deep checks (may take longer)"
    )
    status_parser.set_defaults(func=cmd_status)
    
    # =========================================================================
    # cron command
    # =========================================================================
    cron_parser = subparsers.add_parser(
        "cron",
        help="Cron job management",
        description="Manage scheduled tasks"
    )
    cron_subparsers = cron_parser.add_subparsers(dest="cron_command")
    
    # cron list
    cron_list = cron_subparsers.add_parser("list", help="List scheduled jobs")
    cron_list.add_argument("--all", action="store_true", help="Include disabled jobs")
    
    # cron status
    cron_subparsers.add_parser("status", help="Check if cron scheduler is running")
    
    # cron tick (mostly for debugging)
    cron_subparsers.add_parser("tick", help="Run due jobs once and exit")
    
    cron_parser.set_defaults(func=cmd_cron)
    
    # =========================================================================
    # doctor command
    # =========================================================================
    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Check configuration and dependencies",
        description="Diagnose issues with Hermes Agent setup"
    )
    doctor_parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to fix issues automatically"
    )
    doctor_parser.set_defaults(func=cmd_doctor)
    
    # =========================================================================
    # config command
    # =========================================================================
    config_parser = subparsers.add_parser(
        "config",
        help="View and edit configuration",
        description="Manage Hermes Agent configuration"
    )
    config_subparsers = config_parser.add_subparsers(dest="config_command")
    
    # config show (default)
    config_show = config_subparsers.add_parser("show", help="Show current configuration")
    
    # config edit
    config_edit = config_subparsers.add_parser("edit", help="Open config file in editor")
    
    # config set
    config_set = config_subparsers.add_parser("set", help="Set a configuration value")
    config_set.add_argument("key", nargs="?", help="Configuration key (e.g., model, terminal.backend)")
    config_set.add_argument("value", nargs="?", help="Value to set")
    
    # config path
    config_path = config_subparsers.add_parser("path", help="Print config file path")
    
    # config env-path
    config_env = config_subparsers.add_parser("env-path", help="Print .env file path")
    
    # config check
    config_check = config_subparsers.add_parser("check", help="Check for missing/outdated config")
    
    # config migrate
    config_migrate = config_subparsers.add_parser("migrate", help="Update config with new options")
    
    config_parser.set_defaults(func=cmd_config)
    
    # =========================================================================
    # pairing command
    # =========================================================================
    pairing_parser = subparsers.add_parser(
        "pairing",
        help="Manage DM pairing codes for user authorization",
        description="Approve or revoke user access via pairing codes"
    )
    pairing_sub = pairing_parser.add_subparsers(dest="pairing_action")

    pairing_list_parser = pairing_sub.add_parser("list", help="Show pending + approved users")

    pairing_approve_parser = pairing_sub.add_parser("approve", help="Approve a pairing code")
    pairing_approve_parser.add_argument("platform", help="Platform name (telegram, discord, slack, whatsapp)")
    pairing_approve_parser.add_argument("code", help="Pairing code to approve")

    pairing_revoke_parser = pairing_sub.add_parser("revoke", help="Revoke user access")
    pairing_revoke_parser.add_argument("platform", help="Platform name")
    pairing_revoke_parser.add_argument("user_id", help="User ID to revoke")

    pairing_clear_parser = pairing_sub.add_parser("clear-pending", help="Clear all pending codes")

    def cmd_pairing(args):
        from hermes_cli.pairing import pairing_command
        pairing_command(args)

    pairing_parser.set_defaults(func=cmd_pairing)

    # =========================================================================
    # skills command
    # =========================================================================
    skills_parser = subparsers.add_parser(
        "skills",
        help="Search, install, configure, and manage skills",
        description="Search, install, inspect, audit, configure, and manage skills from GitHub, ClawHub, and other registries."
    )
    skills_subparsers = skills_parser.add_subparsers(dest="skills_action")

    skills_browse = skills_subparsers.add_parser("browse", help="Browse all available skills (paginated)")
    skills_browse.add_argument("--page", type=int, default=1, help="Page number (default: 1)")
    skills_browse.add_argument("--size", type=int, default=20, help="Results per page (default: 20)")
    skills_browse.add_argument("--source", default="all",
                               choices=["all", "official", "github", "clawhub", "lobehub"],
                               help="Filter by source (default: all)")

    skills_search = skills_subparsers.add_parser("search", help="Search skill registries")
    skills_search.add_argument("query", help="Search query")
    skills_search.add_argument("--source", default="all", choices=["all", "official", "github", "clawhub", "lobehub"])
    skills_search.add_argument("--limit", type=int, default=10, help="Max results")

    skills_install = skills_subparsers.add_parser("install", help="Install a skill")
    skills_install.add_argument("identifier", help="Skill identifier (e.g. openai/skills/skill-creator)")
    skills_install.add_argument("--category", default="", help="Category folder to install into")
    skills_install.add_argument("--force", action="store_true", help="Install despite caution verdict")

    skills_inspect = skills_subparsers.add_parser("inspect", help="Preview a skill without installing")
    skills_inspect.add_argument("identifier", help="Skill identifier")

    skills_list = skills_subparsers.add_parser("list", help="List installed skills")
    skills_list.add_argument("--source", default="all", choices=["all", "hub", "builtin", "local"])

    skills_audit = skills_subparsers.add_parser("audit", help="Re-scan installed hub skills")
    skills_audit.add_argument("name", nargs="?", help="Specific skill to audit (default: all)")

    skills_uninstall = skills_subparsers.add_parser("uninstall", help="Remove a hub-installed skill")
    skills_uninstall.add_argument("name", help="Skill name to remove")

    skills_publish = skills_subparsers.add_parser("publish", help="Publish a skill to a registry")
    skills_publish.add_argument("skill_path", help="Path to skill directory")
    skills_publish.add_argument("--to", default="github", choices=["github", "clawhub"], help="Target registry")
    skills_publish.add_argument("--repo", default="", help="Target GitHub repo (e.g. openai/skills)")

    skills_snapshot = skills_subparsers.add_parser("snapshot", help="Export/import skill configurations")
    snapshot_subparsers = skills_snapshot.add_subparsers(dest="snapshot_action")
    snap_export = snapshot_subparsers.add_parser("export", help="Export installed skills to a file")
    snap_export.add_argument("output", help="Output JSON file path")
    snap_import = snapshot_subparsers.add_parser("import", help="Import and install skills from a file")
    snap_import.add_argument("input", help="Input JSON file path")
    snap_import.add_argument("--force", action="store_true", help="Force install despite caution verdict")

    skills_tap = skills_subparsers.add_parser("tap", help="Manage skill sources")
    tap_subparsers = skills_tap.add_subparsers(dest="tap_action")
    tap_subparsers.add_parser("list", help="List configured taps")
    tap_add = tap_subparsers.add_parser("add", help="Add a GitHub repo as skill source")
    tap_add.add_argument("repo", help="GitHub repo (e.g. owner/repo)")
    tap_rm = tap_subparsers.add_parser("remove", help="Remove a tap")
    tap_rm.add_argument("name", help="Tap name to remove")

    # config sub-action: interactive enable/disable
    skills_subparsers.add_parser("config", help="Interactive skill configuration — enable/disable individual skills")

    def cmd_skills(args):
        # Route 'config' action to skills_config module
        if getattr(args, 'skills_action', None) == 'config':
            from hermes_cli.skills_config import skills_command as skills_config_command
            skills_config_command(args)
        else:
            from hermes_cli.skills_hub import skills_command
            skills_command(args)

    skills_parser.set_defaults(func=cmd_skills)

    # =========================================================================
    # tools command
    # =========================================================================
    tools_parser = subparsers.add_parser(
        "tools",
        help="Configure which tools are enabled per platform",
        description="Interactive tool configuration — enable/disable tools for CLI, Telegram, Discord, etc."
    )
    tools_parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a summary of enabled tools per platform and exit"
    )

    def cmd_tools(args):
        from hermes_cli.tools_config import tools_command
        tools_command(args)

    tools_parser.set_defaults(func=cmd_tools)
    # =========================================================================
    # sessions command
    # =========================================================================
    sessions_parser = subparsers.add_parser(
        "sessions",
        help="Manage session history (list, rename, export, prune, delete)",
        description="View and manage the SQLite session store"
    )
    sessions_subparsers = sessions_parser.add_subparsers(dest="sessions_action")

    sessions_list = sessions_subparsers.add_parser("list", help="List recent sessions")
    sessions_list.add_argument("--source", help="Filter by source (cli, telegram, discord, etc.)")
    sessions_list.add_argument("--limit", type=int, default=20, help="Max sessions to show")

    sessions_export = sessions_subparsers.add_parser("export", help="Export sessions to a JSONL file")
    sessions_export.add_argument("output", help="Output JSONL file path")
    sessions_export.add_argument("--source", help="Filter by source")
    sessions_export.add_argument("--session-id", help="Export a specific session")

    sessions_delete = sessions_subparsers.add_parser("delete", help="Delete a specific session")
    sessions_delete.add_argument("session_id", help="Session ID to delete")
    sessions_delete.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")

    sessions_prune = sessions_subparsers.add_parser("prune", help="Delete old sessions")
    sessions_prune.add_argument("--older-than", type=int, default=90, help="Delete sessions older than N days (default: 90)")
    sessions_prune.add_argument("--source", help="Only prune sessions from this source")
    sessions_prune.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")

    sessions_stats = sessions_subparsers.add_parser("stats", help="Show session store statistics")

    sessions_rename = sessions_subparsers.add_parser("rename", help="Set or change a session's title")
    sessions_rename.add_argument("session_id", help="Session ID to rename")
    sessions_rename.add_argument("title", nargs="+", help="New title for the session")

    sessions_browse = sessions_subparsers.add_parser(
        "browse",
        help="Interactive session picker — browse, search, and resume sessions",
    )
    sessions_browse.add_argument("--source", help="Filter by source (cli, telegram, discord, etc.)")
    sessions_browse.add_argument("--limit", type=int, default=50, help="Max sessions to load (default: 50)")

    def cmd_sessions(args):
        import json as _json
        try:
            from hermes_state import SessionDB
            db = SessionDB()
        except Exception as e:
            print(f"Error: Could not open session database: {e}")
            return

        action = args.sessions_action

        if action == "list":
            sessions = db.list_sessions_rich(source=args.source, limit=args.limit)
            if not sessions:
                print("No sessions found.")
                return
            from datetime import datetime
            import time as _time

            def _relative_time(ts):
                """Format a timestamp as relative time (e.g., '2h ago', 'yesterday')."""
                if not ts:
                    return "?"
                delta = _time.time() - ts
                if delta < 60:
                    return "just now"
                elif delta < 3600:
                    mins = int(delta / 60)
                    return f"{mins}m ago"
                elif delta < 86400:
                    hours = int(delta / 3600)
                    return f"{hours}h ago"
                elif delta < 172800:
                    return "yesterday"
                elif delta < 604800:
                    days = int(delta / 86400)
                    return f"{days}d ago"
                else:
                    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")

            has_titles = any(s.get("title") for s in sessions)
            if has_titles:
                print(f"{'Title':<22} {'Preview':<40} {'Last Active':<13} {'ID'}")
                print("─" * 100)
            else:
                print(f"{'Preview':<50} {'Last Active':<13} {'Src':<6} {'ID'}")
                print("─" * 90)
            for s in sessions:
                last_active = _relative_time(s.get("last_active"))
                preview = s.get("preview", "")[:38] if has_titles else s.get("preview", "")[:48]
                if has_titles:
                    title = (s.get("title") or "—")[:20]
                    sid = s["id"][:20]
                    print(f"{title:<22} {preview:<40} {last_active:<13} {sid}")
                else:
                    sid = s["id"][:20]
                    print(f"{preview:<50} {last_active:<13} {s['source']:<6} {sid}")

        elif action == "export":
            if args.session_id:
                data = db.export_session(args.session_id)
                if not data:
                    print(f"Session '{args.session_id}' not found.")
                    return
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(_json.dumps(data, ensure_ascii=False) + "\n")
                print(f"Exported 1 session to {args.output}")
            else:
                sessions = db.export_all(source=args.source)
                with open(args.output, "w", encoding="utf-8") as f:
                    for s in sessions:
                        f.write(_json.dumps(s, ensure_ascii=False) + "\n")
                print(f"Exported {len(sessions)} sessions to {args.output}")

        elif action == "delete":
            if not args.yes:
                confirm = input(f"Delete session '{args.session_id}' and all its messages? [y/N] ")
                if confirm.lower() not in ("y", "yes"):
                    print("Cancelled.")
                    return
            if db.delete_session(args.session_id):
                print(f"Deleted session '{args.session_id}'.")
            else:
                print(f"Session '{args.session_id}' not found.")

        elif action == "prune":
            days = args.older_than
            source_msg = f" from '{args.source}'" if args.source else ""
            if not args.yes:
                confirm = input(f"Delete all ended sessions older than {days} days{source_msg}? [y/N] ")
                if confirm.lower() not in ("y", "yes"):
                    print("Cancelled.")
                    return
            count = db.prune_sessions(older_than_days=days, source=args.source)
            print(f"Pruned {count} session(s).")

        elif action == "rename":
            title = " ".join(args.title)
            try:
                if db.set_session_title(args.session_id, title):
                    print(f"Session '{args.session_id}' renamed to: {title}")
                else:
                    print(f"Session '{args.session_id}' not found.")
            except ValueError as e:
                print(f"Error: {e}")

        elif action == "browse":
            limit = getattr(args, "limit", 50) or 50
            source = getattr(args, "source", None)
            sessions = db.list_sessions_rich(source=source, limit=limit)
            db.close()
            if not sessions:
                print("No sessions found.")
                return

            selected_id = _session_browse_picker(sessions)
            if not selected_id:
                print("Cancelled.")
                return

            # Launch hermes --resume <id> by replacing the current process
            print(f"Resuming session: {selected_id}")
            import shutil
            hermes_bin = shutil.which("hermes")
            if hermes_bin:
                os.execvp(hermes_bin, ["hermes", "--resume", selected_id])
            else:
                # Fallback: re-invoke via python -m
                os.execvp(
                    sys.executable,
                    [sys.executable, "-m", "hermes_cli.main", "--resume", selected_id],
                )
            return  # won't reach here after execvp

        elif action == "stats":
            total = db.session_count()
            msgs = db.message_count()
            print(f"Total sessions: {total}")
            print(f"Total messages: {msgs}")
            for src in ["cli", "telegram", "discord", "whatsapp", "slack"]:
                c = db.session_count(source=src)
                if c > 0:
                    print(f"  {src}: {c} sessions")
            db_path = db.db_path
            if db_path.exists():
                size_mb = os.path.getsize(db_path) / (1024 * 1024)
                print(f"Database size: {size_mb:.1f} MB")

        else:
            sessions_parser.print_help()

        db.close()

    sessions_parser.set_defaults(func=cmd_sessions)

    # =========================================================================
    # insights command
    # =========================================================================
    insights_parser = subparsers.add_parser(
        "insights",
        help="Show usage insights and analytics",
        description="Analyze session history to show token usage, costs, tool patterns, and activity trends"
    )
    insights_parser.add_argument("--days", type=int, default=30, help="Number of days to analyze (default: 30)")
    insights_parser.add_argument("--source", help="Filter by platform (cli, telegram, discord, etc.)")

    def cmd_insights(args):
        try:
            from hermes_state import SessionDB
            from agent.insights import InsightsEngine

            db = SessionDB()
            engine = InsightsEngine(db)
            report = engine.generate(days=args.days, source=args.source)
            print(engine.format_terminal(report))
            db.close()
        except Exception as e:
            print(f"Error generating insights: {e}")

    insights_parser.set_defaults(func=cmd_insights)

    # =========================================================================
    # claw command (OpenClaw migration)
    # =========================================================================
    claw_parser = subparsers.add_parser(
        "claw",
        help="OpenClaw migration tools",
        description="Migrate settings, memories, skills, and API keys from OpenClaw to Hermes"
    )
    claw_subparsers = claw_parser.add_subparsers(dest="claw_action")

    # claw migrate
    claw_migrate = claw_subparsers.add_parser(
        "migrate",
        help="Migrate from OpenClaw to Hermes",
        description="Import settings, memories, skills, and API keys from an OpenClaw installation"
    )
    claw_migrate.add_argument(
        "--source",
        help="Path to OpenClaw directory (default: ~/.openclaw)"
    )
    claw_migrate.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be migrated without making changes"
    )
    claw_migrate.add_argument(
        "--preset",
        choices=["user-data", "full"],
        default="full",
        help="Migration preset (default: full). 'user-data' excludes secrets"
    )
    claw_migrate.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files (default: skip conflicts)"
    )
    claw_migrate.add_argument(
        "--migrate-secrets",
        action="store_true",
        help="Include allowlisted secrets (TELEGRAM_BOT_TOKEN, API keys, etc.)"
    )
    claw_migrate.add_argument(
        "--workspace-target",
        help="Absolute path to copy workspace instructions into"
    )
    claw_migrate.add_argument(
        "--skill-conflict",
        choices=["skip", "overwrite", "rename"],
        default="skip",
        help="How to handle skill name conflicts (default: skip)"
    )
    claw_migrate.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompts"
    )

    def cmd_claw(args):
        from hermes_cli.claw import claw_command
        claw_command(args)

    claw_parser.set_defaults(func=cmd_claw)

    # =========================================================================
    # version command
    # =========================================================================
    version_parser = subparsers.add_parser(
        "version",
        help="Show version information"
    )
    version_parser.set_defaults(func=cmd_version)
    
    # =========================================================================
    # comando de actualización
    # =========================================================================
    update_parser = subparsers.add_parser(
        "update",
        help="Update Hermes Agent to the latest version",
        description="Pull the latest changes from git and reinstall dependencies"
    )
    update_parser.set_defaults(func=cmd_update)
    
    # =========================================================================
    # uninstall command
    # =========================================================================
    uninstall_parser = subparsers.add_parser(
        "uninstall",
        help="Uninstall Hermes Agent",
        description="Remove Hermes Agent from your system. Can keep configs/data for reinstall."
    )
    uninstall_parser.add_argument(
        "--full",
        action="store_true",
        help="Full uninstall - remove everything including configs and data"
    )
    uninstall_parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompts"
    )
    uninstall_parser.set_defaults(func=cmd_uninstall)
    
    # =========================================================================
    # Parse and execute
    # =========================================================================
    # Pre-process argv so unquoted multi-word session names after -c / -r
    # are merged into a single token before argparse sees them.
    # e.g. ``hermes -c Pokemon Agent Dev`` → ``hermes -c 'Pokemon Agent Dev'``
    _processed_argv = _coalesce_session_name_args(sys.argv[1:])
    args = parser.parse_args(_processed_argv)
    
    # Handle --version flag
    if args.version:
        cmd_version(args)
        return
    
    # Handle top-level --resume / --continue as shortcut to chat
    if (args.resume or args.continue_last) and args.command is None:
        args.command = "chat"
        args.query = None
        args.model = None
        args.provider = None
        args.toolsets = None
        args.verbose = False
        if not hasattr(args, "worktree"):
            args.worktree = False
        cmd_chat(args)
        return
    
    # Default to chat if no command specified
    if args.command is None:
        args.query = None
        args.model = None
        args.provider = None
        args.toolsets = None
        args.verbose = False
        args.resume = None
        args.continue_last = None
        if not hasattr(args, "worktree"):
            args.worktree = False
        cmd_chat(args)
        return
    
    # Execute the command
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
