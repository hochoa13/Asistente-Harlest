#!/usr/bin/env python3
"""CLI del Skills Hub — interfaz unificada para el Hermes Skills Hub.

Da soporte tanto a:
    - `hermes skills <subcomando>` (punto de entrada CLI vía argparse)
    - `/skills <subcomando>` (slash command en el chat interactivo)

Toda la lógica vive en funciones compartidas ``do_*``. El punto de entrada CLI
y el manejador del slash command son *wrappers* ligeros que sólo parsean
argumentos y delegan.
"""

import json
import shutil
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Imports diferidos para evitar dependencias circulares y arranque lento.
# tools.skills_hub y tools.skills_guard se importan dentro de las funciones.

_console = Console()


# ---------------------------------------------------------------------------
# Funciones compartidas do_*
# ---------------------------------------------------------------------------

def _resolve_short_name(name: str, sources, console: Console) -> str:
    """Resuelve un nombre corto de *skill* (por ejemplo ``pptx``) a un
    identificador completo buscando en todas las fuentes.

    Si se encuentra exactamente una coincidencia, devuelve su identificador.
    Si hay varias, las muestra y pide al usuario que use el identificador
    completo. Devuelve cadena vacía si no se encuentra nada o es ambiguo.
    """
    from tools.skills_hub import unified_search

    c = console or _console
    c.print(f"[dim]Resolviendo '{name}'...[/]")

    results = unified_search(name, sources, source_filter="all", limit=20)

    # Filtrar coincidencias exactas por nombre (case-insensitive)
    exact = [r for r in results if r.name.lower() == name.lower()]

    if len(exact) == 1:
        c.print(f"[dim]Resuelto a: {exact[0].identifier}[/]")
        return exact[0].identifier

    if len(exact) > 1:
        c.print(f"\n[yellow]Se encontraron múltiples skills llamadas '{name}':[/]")
        table = Table()
        table.add_column("Source", style="dim")
        table.add_column("Trust", style="dim")
        table.add_column("Identifier", style="bold cyan")
        for r in exact:
            trust_style = {"builtin": "bright_cyan", "trusted": "green", "community": "yellow"}.get(r.trust_level, "dim")
            trust_label = "oficial" if r.source == "official" else r.trust_level
            table.add_row(r.source, f"[{trust_style}]{trust_label}[/]", r.identifier)
        c.print(table)
        c.print("[bold]Usa el identificador completo para instalar una específica.[/]\n")
        return ""

    # Sin coincidencia exacta: comprobar si hay coincidencias parciales para sugerir
    if results:
        c.print(f"[yellow]No hay coincidencia exacta para '{name}'. ¿Quizás quisiste decir una de estas?[/]")
        for r in results[:5]:
            c.print(f"  [cyan]{r.name}[/] — {r.identifier}")
        c.print()
        return ""

    c.print(f"[bold red]Error:[/] No se encontró ninguna *skill* llamada '{name}' en ninguna fuente.\n")
    return ""


def do_search(query: str, source: str = "all", limit: int = 10,
              console: Optional[Console] = None) -> None:
    """Busca en los registros y muestra los resultados en una tabla Rich."""
    from tools.skills_hub import GitHubAuth, create_source_router, unified_search

    c = console or _console
    c.print(f"\n[bold]Buscando:[/] {query}")

    auth = GitHubAuth()
    sources = create_source_router(auth)
    results = unified_search(query, sources, source_filter=source, limit=limit)

    if not results:
        c.print("[dim]No se encontraron skills que coincidan con tu búsqueda.[/]\n")
        return

    table = Table(title=f"Skills Hub — {len(results)} resultado(s)")
    table.add_column("Nombre", style="bold cyan")
    table.add_column("Descripción", max_width=60)
    table.add_column("Fuente", style="dim")
    table.add_column("Confianza", style="dim")
    table.add_column("Identificador", style="dim")

    for r in results:
        trust_style = {"builtin": "bright_cyan", "trusted": "green", "community": "yellow"}.get(r.trust_level, "dim")
        trust_label = "oficial" if r.source == "official" else r.trust_level
        table.add_row(
            r.name,
            r.description[:60] + ("..." if len(r.description) > 60 else ""),
            r.source,
            f"[{trust_style}]{trust_label}[/]",
            r.identifier,
        )

    c.print(table)
    c.print("[dim]Usa: hermes skills inspect <identificador> para previsualizar, "
        "hermes skills install <identificador> para instalar[/]\n")


def do_browse(page: int = 1, page_size: int = 20, source: str = "all",
              console: Optional[Console] = None) -> None:
    """Navega por todas las skills disponibles en los registros, con paginación.

    Las skills oficiales siempre se muestran primero, independientemente del
    filtro de fuente.
    """
    from tools.skills_hub import (
        GitHubAuth, create_source_router, OptionalSkillSource, SkillMeta,
    )

    # Limitar page_size a un rango seguro
    page_size = max(1, min(page_size, 100))

    c = console or _console

    auth = GitHubAuth()
    sources = create_source_router(auth)

    # Recoger resultados de todas las fuentes (o filtradas)
    # Se usa query vacía para obtener todo; los límites por fuente evitan sobrecarga
    _TRUST_RANK = {"builtin": 3, "trusted": 2, "community": 1}
    _PER_SOURCE_LIMIT = {"official": 100, "github": 100, "clawhub": 50,
                         "claude-marketplace": 50, "lobehub": 50}

    all_results: list = []
    source_counts: dict = {}

    for src in sources:
        sid = src.source_id()
        if source != "all" and sid != source and sid != "official":
            # Always include official source for the "first" placement
            continue
        try:
            limit = _PER_SOURCE_LIMIT.get(sid, 50)
            results = src.search("", limit=limit)
            source_counts[sid] = len(results)
            all_results.extend(results)
        except Exception:
            continue

    if not all_results:
        c.print("[dim]No skills found in the Skills Hub.[/]\n")
        return

    # Desduplicar por nombre, prefiriendo mayor nivel de confianza
    seen: dict = {}
    for r in all_results:
        rank = _TRUST_RANK.get(r.trust_level, 0)
        if r.name not in seen or rank > _TRUST_RANK.get(seen[r.name].trust_level, 0):
            seen[r.name] = r
    deduped = list(seen.values())

    # Ordenar: oficiales primero, luego por nivel de confianza (desc), luego alfabético
    deduped.sort(key=lambda r: (
        -_TRUST_RANK.get(r.trust_level, 0),
        r.source != "official",
        r.name.lower(),
    ))

    # Paginación
    total = len(deduped)
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    end = min(start + page_size, total)
    page_items = deduped[start:end]

    # Contar oficiales vs otras
    official_count = sum(1 for r in deduped if r.source == "official")

    # Cabecera
    source_label = f"— {source}" if source != "all" else "— todas las fuentes"
    c.print(f"\n[bold]Skills Hub — Navegar {source_label}[/]"
            f"  [dim]({total} skills, página {page}/{total_pages})[/]")
    if official_count > 0 and page == 1:
        c.print(f"[bright_cyan]★ {official_count} skill(s) opcional(es) oficial(es) de Harold Hernandez Ochoa[/]")
    c.print()

    # Construir tabla
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Nombre", style="bold cyan", max_width=25)
    table.add_column("Descripción", max_width=50)
    table.add_column("Fuente", style="dim", width=12)
    table.add_column("Confianza", width=10)

    for i, r in enumerate(page_items, start=start + 1):
        trust_style = {"builtin": "bright_cyan", "trusted": "green",
                   "community": "yellow"}.get(r.trust_level, "dim")
        trust_label = "★ oficial" if r.source == "official" else r.trust_level

        desc = r.description[:50]
        if len(r.description) > 50:
            desc += "..."

        table.add_row(
            str(i),
            r.name,
            desc,
            r.source,
            f"[{trust_style}]{trust_label}[/]",
        )

    c.print(table)

    # Pistas de navegación
    nav_parts = []
    if page > 1:
        nav_parts.append(f"[cyan]--page {page - 1}[/] ← anterior")
    if page < total_pages:
        nav_parts.append(f"[cyan]--page {page + 1}[/] → siguiente")

    if nav_parts:
        c.print(f"  {' | '.join(nav_parts)}")

    # Resumen de fuentes
    if source == "all" and source_counts:
        parts = [f"{sid}: {ct}" for sid, ct in sorted(source_counts.items())]
        c.print(f"  [dim]Fuentes: {', '.join(parts)}[/]")

    c.print("[dim]Usa: hermes skills inspect <identificador> para previsualizar, "
            "hermes skills install <identificador> para instalar[/]\n")


def do_install(identifier: str, category: str = "", force: bool = False,
               console: Optional[Console] = None) -> None:
    """Descarga, pone en cuarentena, escanea, confirma e instala una skill."""
    from tools.skills_hub import (
        GitHubAuth, create_source_router, ensure_hub_dirs,
        quarantine_bundle, install_from_quarantine, HubLockFile,
    )
    from tools.skills_guard import scan_skill, should_allow_install, format_scan_report

    c = console or _console
    ensure_hub_dirs()

    # Resolver qué adaptador de fuente maneja este identificador
    auth = GitHubAuth()
    sources = create_source_router(auth)

    # Si el identificador parece un nombre corto (sin barras), resolverlo vía búsqueda
    if "/" not in identifier:
        identifier = _resolve_short_name(identifier, sources, c)
        if not identifier:
            return

    c.print(f"\n[bold]Obteniendo:[/] {identifier}")

    bundle = None
    for src in sources:
        bundle = src.fetch(identifier)
        if bundle:
            break

    if not bundle:
        c.print(f"[bold red]Error:[/] No se pudo obtener '{identifier}' desde ninguna fuente.\n")
        return

    # Autodetectar categoría para skills oficiales (por ejemplo "official/autonomous-ai-agents/blackbox")
    if bundle.source == "official" and not category:
        id_parts = bundle.identifier.split("/")  # ["official", "category", "skill"]
        if len(id_parts) >= 3:
            category = id_parts[1]

    # Comprobar si ya está instalada
    lock = HubLockFile()
    existing = lock.get_installed(bundle.name)
    if existing:
        c.print(f"[yellow]Advertencia:[/] '{bundle.name}' ya está instalada en {existing['install_path']}")
        if not force:
            c.print("Usa --force para reinstalar.\n")
            return

    # Poner el paquete en cuarentena
    q_path = quarantine_bundle(bundle)
    c.print(f"[dim]Puesto en cuarentena en {q_path.relative_to(q_path.parent.parent.parent)}[/]")

    # Escaneo
    c.print("[bold]Ejecutando escaneo de seguridad...[/]")
    result = scan_skill(q_path, source=identifier)
    c.print(format_scan_report(result))

    # Comprobar política de instalación
    allowed, reason = should_allow_install(result, force=force)
    if not allowed:
        c.print(f"\n[bold red]Instalación bloqueada:[/] {reason}")
        # Limpiar cuarentena
        shutil.rmtree(q_path, ignore_errors=True)
        from tools.skills_hub import append_audit_log
        append_audit_log("BLOCKED", bundle.name, bundle.source,
                         bundle.trust_level, result.verdict,
                         f"{len(result.findings)}_findings")
        return

    # Confirmar con el usuario — mostrar advertencia según la fuente
    if not force:
        c.print()
        if bundle.source == "official":
            c.print(Panel(
                "[bold bright_cyan]Esta es una skill opcional oficial mantenida por Harold Hernandez Ochoa.[/]\n\n"
                "Viene incluida con hermes-agent pero no está activada por defecto.\n"
                "Instalarla la copiará a tu directorio de skills donde el agente podrá usarla.\n\n"
                f"Los archivos estarán en: [cyan]~/.hermes/skills/{category + '/' if category else ''}{bundle.name}/[/]",
                title="Skill oficial",
                border_style="bright_cyan",
            ))
        else:
            c.print(Panel(
                "[bold yellow]Estás instalando una skill de terceros bajo tu propia responsabilidad.[/]\n\n"
                "Las skills externas pueden contener instrucciones que influyen en el comportamiento del agente,\n"
                "comandos de shell y scripts. Incluso después del escaneo automático deberías\n"
                "revisar los archivos instalados antes de usarlos.\n\n"
                f"Los archivos estarán en: [cyan]~/.hermes/skills/{category + '/' if category else ''}{bundle.name}/[/]",
                title="Aviso",
                border_style="yellow",
            ))
        c.print(f"[bold]¿Instalar '{bundle.name}'?[/]")
        try:
            answer = input("Confirmar [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = "n"
        if answer not in ("y", "yes"):
            c.print("[dim]Instalación cancelada.[/]\n")
            shutil.rmtree(q_path, ignore_errors=True)
            return

    # Instalar
    install_dir = install_from_quarantine(q_path, bundle.name, category, bundle, result)
    from tools.skills_hub import SKILLS_DIR
    c.print(f"[bold green]Instalada:[/] {install_dir.relative_to(SKILLS_DIR)}")
    c.print(f"[dim]Archivos: {', '.join(bundle.files.keys())}[/]\n")


def do_inspect(identifier: str, console: Optional[Console] = None) -> None:
    """Previsualiza el contenido de SKILL.md de una skill sin instalarla."""
    from tools.skills_hub import GitHubAuth, create_source_router

    c = console or _console
    auth = GitHubAuth()
    sources = create_source_router(auth)

    if "/" not in identifier:
        identifier = _resolve_short_name(identifier, sources, c)
        if not identifier:
            return

    meta = None
    for src in sources:
        meta = src.inspect(identifier)
        if meta:
            break

    if not meta:
        c.print(f"[bold red]Error:[/] No se pudo encontrar '{identifier}' en ninguna fuente.\n")
        return

    # También obtener el contenido completo para la previsualización
    bundle = None
    for src in sources:
        bundle = src.fetch(identifier)
        if bundle:
            break

    c.print()
    trust_style = {"builtin": "bright_cyan", "trusted": "green", "community": "yellow"}.get(meta.trust_level, "dim")
    trust_label = "oficial" if meta.source == "official" else meta.trust_level

    info_lines = [
        f"[bold]Nombre:[/] {meta.name}",
        f"[bold]Descripción:[/] {meta.description}",
        f"[bold]Fuente:[/] {meta.source}",
        f"[bold]Confianza:[/] [{trust_style}]{trust_label}[/]",
        f"[bold]Identificador:[/] {meta.identifier}",
    ]
    if meta.tags:
        info_lines.append(f"[bold]Tags:[/] {', '.join(meta.tags)}")

    c.print(Panel("\n".join(info_lines), title=f"Skill: {meta.name}"))

    if bundle and "SKILL.md" in bundle.files:
        content = bundle.files["SKILL.md"]
        # Mostrar las primeras 50 líneas como vista previa
        lines = content.split("\n")
        preview = "\n".join(lines[:50])
        if len(lines) > 50:
            preview += f"\n\n... ({len(lines) - 50} líneas más)"
        c.print(Panel(preview, title="Vista previa de SKILL.md", subtitle="hermes skills install <id> para instalar"))

    c.print()


def do_list(source_filter: str = "all", console: Optional[Console] = None) -> None:
    """Lista las skills instaladas, diferenciando hub, builtin y locales."""
    from tools.skills_hub import HubLockFile, ensure_hub_dirs
    from tools.skills_sync import _read_manifest
    from tools.skills_tool import _find_all_skills

    c = console or _console
    ensure_hub_dirs()
    lock = HubLockFile()
    hub_installed = {e["name"]: e for e in lock.list_installed()}
    builtin_names = set(_read_manifest())

    all_skills = _find_all_skills()

    table = Table(title="Skills instaladas")
    table.add_column("Nombre", style="bold cyan")
    table.add_column("Categoría", style="dim")
    table.add_column("Fuente", style="dim")
    table.add_column("Confianza", style="dim")

    hub_count = 0
    builtin_count = 0
    local_count = 0

    for skill in sorted(all_skills, key=lambda s: (s.get("category") or "", s["name"])):
        name = skill["name"]
        category = skill.get("category", "")
        hub_entry = hub_installed.get(name)

        if hub_entry:
            source_type = "hub"
            source_display = hub_entry.get("source", "hub")
            trust = hub_entry.get("trust_level", "community")
            hub_count += 1
        elif name in builtin_names:
            source_type = "builtin"
            source_display = "builtin"
            trust = "builtin"
            builtin_count += 1
        else:
            source_type = "local"
            source_display = "local"
            trust = "local"
            local_count += 1

        if source_filter != "all" and source_filter != source_type:
            continue

        trust_style = {"builtin": "bright_cyan", "trusted": "green", "community": "yellow", "local": "dim"}.get(trust, "dim")
        trust_label = "oficial" if source_display == "official" else trust
        table.add_row(name, category, source_display, f"[{trust_style}]{trust_label}[/]")

    c.print(table)
    c.print(
        f"[dim]{hub_count} instaladas desde hub, {builtin_count} builtin, {local_count} locales[/]\n"
    )


def do_audit(name: Optional[str] = None, console: Optional[Console] = None) -> None:
    """Ejecuta de nuevo el escaneo de seguridad sobre skills instaladas desde el hub."""
    from tools.skills_hub import HubLockFile, SKILLS_DIR
    from tools.skills_guard import scan_skill, format_scan_report

    c = console or _console
    lock = HubLockFile()
    installed = lock.list_installed()

    if not installed:
        c.print("[dim]No hay skills instaladas desde el hub para auditar.[/]\n")
        return

    targets = installed
    if name:
        targets = [e for e in installed if e["name"] == name]
        if not targets:
            c.print(f"[bold red]Error:[/] '{name}' no es una skill instalada desde el hub.\n")
            return

    c.print(f"\n[bold]Auditando {len(targets)} skill(s)...[/]\n")

    for entry in targets:
        skill_path = SKILLS_DIR / entry["install_path"]
        if not skill_path.exists():
            c.print(f"[yellow]Advertencia:[/] {entry['name']} — ruta inexistente: {entry['install_path']}")
            continue

        result = scan_skill(skill_path, source=entry.get("identifier", entry["source"]))
        c.print(format_scan_report(result))
        c.print()


def do_uninstall(name: str, console: Optional[Console] = None) -> None:
    """Elimina una skill instalada desde el hub, con confirmación."""
    from tools.skills_hub import uninstall_skill

    c = console or _console

    c.print(f"\n[bold]¿Desinstalar '{name}'?[/]")
    try:
        answer = input("Confirmar [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        answer = "n"
    if answer not in ("y", "yes"):
        c.print("[dim]Cancelado.[/]\n")
        return

    success, msg = uninstall_skill(name)
    if success:
        c.print(f"[bold green]{msg}[/]\n")
    else:
        c.print(f"[bold red]Error:[/] {msg}\n")


def do_tap(action: str, repo: str = "", console: Optional[Console] = None) -> None:
    """Gestiona *taps* (fuentes personalizadas de repositorios GitHub)."""
    from tools.skills_hub import TapsManager

    c = console or _console
    mgr = TapsManager()

    if action == "list":
        taps = mgr.list_taps()
        if not taps:
            c.print("[dim]No hay taps personalizados configurados. Usando sólo las fuentes por defecto.[/]\n")
            return
        table = Table(title="Taps configurados")
        table.add_column("Repo", style="bold cyan")
        table.add_column("Ruta", style="dim")
        for t in taps:
            table.add_row(t["repo"], t.get("path", "skills/"))
        c.print(table)
        c.print()

    elif action == "add":
        if not repo:
            c.print("[bold red]Error:[/] Se requiere repo. Uso: hermes skills tap add owner/repo\n")
            return
        if mgr.add(repo):
            c.print(f"[bold green]Tap añadido:[/] {repo}\n")
        else:
            c.print(f"[yellow]El tap ya existe:[/] {repo}\n")

    elif action == "remove":
        if not repo:
            c.print("[bold red]Error:[/] Se requiere repo. Uso: hermes skills tap remove owner/repo\n")
            return
        if mgr.remove(repo):
            c.print(f"[bold green]Tap eliminado:[/] {repo}\n")
        else:
            c.print(f"[bold red]Error:[/] Tap no encontrado: {repo}\n")

    else:
        c.print(f"[bold red]Acción de tap desconocida:[/] {action}. Usa: list, add, remove\n")


def do_publish(skill_path: str, target: str = "github", repo: str = "",
               console: Optional[Console] = None) -> None:
    """Publica una skill local en un registro (PR en GitHub o envío a ClawHub)."""
    from tools.skills_hub import GitHubAuth, SKILLS_DIR
    from tools.skills_guard import scan_skill, format_scan_report

    c = console or _console
    path = Path(skill_path)

    # Resolver ruta relativa al directorio de skills si no es absoluta
    if not path.is_absolute():
        path = SKILLS_DIR / path
    if not path.exists() or not (path / "SKILL.md").exists():
        c.print(f"[bold red]Error:[/] No se encontró SKILL.md en {path}\n")
        return

    # Validar la skill
    import yaml
    skill_md = (path / "SKILL.md").read_text(encoding="utf-8")
    fm = {}
    if skill_md.startswith("---"):
        import re
        match = re.search(r'\n---\s*\n', skill_md[3:])
        if match:
            try:
                fm = yaml.safe_load(skill_md[3:match.start() + 3]) or {}
            except yaml.YAMLError:
                pass

    name = fm.get("name", path.name)
    description = fm.get("description", "")
    if not description:
        c.print("[bold red]Error:[/] SKILL.md debe tener una 'description' en el frontmatter.\n")
        return

    # Autoescaneo antes de publicar
    c.print(f"[bold]Escaneando '{name}' antes de publicar...[/]")
    result = scan_skill(path, source="self")
    c.print(format_scan_report(result))
    if result.verdict == "dangerous":
        c.print("[bold red]No se puede publicar una skill con veredicto DANGEROUS.[/]\n")
        return

    if target == "github":
        if not repo:
            c.print("[bold red]Error:[/] --repo es obligatorio para publicar en GitHub.\n"
                "Uso: hermes skills publish <ruta> --to github --repo owner/repo\n")
            return

        auth = GitHubAuth()
        if not auth.is_authenticated():
            c.print("[bold red]Error:[/] Se requiere autenticación de GitHub.\n"
                "Configura GITHUB_TOKEN en ~/.hermes/.env o ejecuta 'gh auth login'.\n")
            return

        c.print(f"[bold]Publicando '{name}' en {repo}...[/]")
        success, msg = _github_publish(path, name, repo, auth)
        if success:
            c.print(f"[bold green]{msg}[/]\n")
        else:
            c.print(f"[bold red]Error:[/] {msg}\n")

    elif target == "clawhub":
        c.print("[yellow]La publicación en ClawHub aún no está soportada. "
                "Envía manualmente en https://clawhub.ai/submit[/]\n")
    else:
        c.print(f"[bold red]Destino desconocido:[/] {target}. Usa 'github' o 'clawhub'.\n")


def _github_publish(skill_path: Path, skill_name: str, target_repo: str,
                    auth) -> tuple:
    """Crea un PR a un repo de GitHub con la skill. Devuelve (éxito, mensaje)."""
    import httpx

    headers = auth.get_headers()

    # 1. Hacer fork del repo
    try:
        resp = httpx.post(
            f"https://api.github.com/repos/{target_repo}/forks",
            headers=headers, timeout=30,
        )
        if resp.status_code in (200, 202):
            fork = resp.json()
            fork_repo = fork["full_name"]
        elif resp.status_code == 403:
            return False, "El token de GitHub no tiene permisos para hacer fork de repos"
        else:
            return False, f"Fallo al hacer fork de {target_repo}: {resp.status_code}"
    except httpx.HTTPError as e:
        return False, f"Error de red al hacer fork del repo: {e}"

    # 2. Obtener rama por defecto
    try:
        resp = httpx.get(
            f"https://api.github.com/repos/{target_repo}",
            headers=headers, timeout=15,
        )
        default_branch = resp.json().get("default_branch", "main")
    except Exception:
        default_branch = "main"

    # 3. Obtener el SHA base del árbol
    try:
        resp = httpx.get(
            f"https://api.github.com/repos/{fork_repo}/git/refs/heads/{default_branch}",
            headers=headers, timeout=15,
        )
        base_sha = resp.json()["object"]["sha"]
    except Exception as e:
        return False, f"Fallo al obtener la rama base: {e}"

    # 4. Crear rama nueva
    branch_name = f"add-skill-{skill_name}"
    try:
        httpx.post(
            f"https://api.github.com/repos/{fork_repo}/git/refs",
            headers=headers, timeout=15,
            json={"ref": f"refs/heads/{branch_name}", "sha": base_sha},
        )
    except Exception as e:
        return False, f"Fallo al crear la rama: {e}"

    # 5. Subir archivos de la skill
    for f in skill_path.rglob("*"):
        if not f.is_file():
            continue
        rel = str(f.relative_to(skill_path))
        upload_path = f"skills/{skill_name}/{rel}"
        try:
            import base64
            content_b64 = base64.b64encode(f.read_bytes()).decode()
            httpx.put(
                f"https://api.github.com/repos/{fork_repo}/contents/{upload_path}",
                headers=headers, timeout=15,
                json={
                    "message": f"Add {skill_name} skill: {rel}",
                    "content": content_b64,
                    "branch": branch_name,
                },
            )
        except Exception as e:
            return False, f"Fallo al subir {rel}: {e}"

    # 6. Crear PR
    try:
        resp = httpx.post(
            f"https://api.github.com/repos/{target_repo}/pulls",
            headers=headers, timeout=15,
            json={
                "title": f"Add skill: {skill_name}",
                "body": f"Submitting the `{skill_name}` skill via Hermes Skills Hub.\n\n"
                        f"This skill was scanned by the Hermes Skills Guard before submission.",
                "head": f"{fork_repo.split('/')[0]}:{branch_name}",
                "base": default_branch,
            },
        )
        if resp.status_code == 201:
            pr_url = resp.json().get("html_url", "")
            return True, f"PR creado: {pr_url}"
        else:
            return False, f"Fallo al crear el PR: {resp.status_code} {resp.text[:200]}"
    except httpx.HTTPError as e:
        return False, f"Error de red al crear el PR: {e}"


def do_snapshot_export(output_path: str, console: Optional[Console] = None) -> None:
    """Exporta la configuración actual de skills del hub a un JSON portátil."""
    from tools.skills_hub import HubLockFile, TapsManager

    c = console or _console
    lock = HubLockFile()
    taps = TapsManager()

    installed = lock.list_installed()
    tap_list = taps.list_taps()

    snapshot = {
        "hermes_version": "0.1.0",
        "exported_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
        "skills": [
            {
                "name": entry["name"],
                "source": entry.get("source", ""),
                "identifier": entry.get("identifier", ""),
                "category": str(Path(entry.get("install_path", "")).parent)
                            if "/" in entry.get("install_path", "") else "",
            }
            for entry in installed
        ],
        "taps": tap_list,
    }

    out = Path(output_path)
    out.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n")
    c.print(f"[bold green]Snapshot exportado:[/] {out}")
    c.print(f"[dim]{len(installed)} skill(s), {len(tap_list)} tap(s)[/]\n")


def do_snapshot_import(input_path: str, force: bool = False,
                       console: Optional[Console] = None) -> None:
    """Reinstala skills desde un archivo snapshot."""
    from tools.skills_hub import TapsManager

    c = console or _console
    inp = Path(input_path)
    if not inp.exists():
        c.print(f"[bold red]Error:[/] Archivo no encontrado: {inp}\n")
        return

    try:
        snapshot = json.loads(inp.read_text())
    except json.JSONDecodeError:
        c.print(f"[bold red]Error:[/] JSON no válido en {inp}\n")
        return

    # Restaurar taps primero
    taps = snapshot.get("taps", [])
    if taps:
        mgr = TapsManager()
        for tap in taps:
            repo = tap.get("repo", "")
            if repo:
                mgr.add(repo, tap.get("path", "skills/"))
        c.print(f"[dim]Restaurados {len(taps)} tap(s)[/]")

    # Instalar skills
    skills = snapshot.get("skills", [])
    if not skills:
        c.print("[dim]No hay skills en el snapshot para instalar.[/]\n")
        return

    c.print(f"[bold]Importando {len(skills)} skill(s) desde el snapshot...[/]\n")
    for entry in skills:
        identifier = entry.get("identifier", "")
        category = entry.get("category", "")
        if not identifier:
            c.print(f"[yellow]Saltando entrada sin identificador: {entry.get('name', '?')}[/]")
            continue

        c.print(f"[bold]--- {entry.get('name', identifier)} ---[/]")
        do_install(identifier, category=category, force=force, console=c)

    c.print("[bold green]Importación del snapshot completada.[/]\n")


# ---------------------------------------------------------------------------
# CLI argparse entry point
# ---------------------------------------------------------------------------

def skills_command(args) -> None:
    """Router para `hermes skills <subcommand>` — llamado desde hermes_cli/main.py."""
    action = getattr(args, "skills_action", None)

    if action == "browse":
        do_browse(page=args.page, page_size=args.size, source=args.source)
    elif action == "search":
        do_search(args.query, source=args.source, limit=args.limit)
    elif action == "install":
        do_install(args.identifier, category=args.category, force=args.force)
    elif action == "inspect":
        do_inspect(args.identifier)
    elif action == "list":
        do_list(source_filter=args.source)
    elif action == "audit":
        do_audit(name=getattr(args, "name", None))
    elif action == "uninstall":
        do_uninstall(args.name)
    elif action == "publish":
        do_publish(
            args.skill_path,
            target=getattr(args, "to", "github"),
            repo=getattr(args, "repo", ""),
        )
    elif action == "snapshot":
        snap_action = getattr(args, "snapshot_action", None)
        if snap_action == "export":
            do_snapshot_export(args.output)
        elif snap_action == "import":
            do_snapshot_import(args.input, force=getattr(args, "force", False))
        else:
            _console.print("Uso: hermes skills snapshot [export|import]\n")
    elif action == "tap":
        tap_action = getattr(args, "tap_action", None)
        repo = getattr(args, "repo", "") or getattr(args, "name", "")
        if not tap_action:
            _console.print("Uso: hermes skills tap [list|add|remove]\n")
            return
        do_tap(tap_action, repo=repo)
    else:
        _console.print("Uso: hermes skills [browse|search|install|inspect|list|audit|uninstall|publish|snapshot|tap]\n")
        _console.print("Ejecuta 'hermes skills <command> --help' para más detalles.\n")


# ---------------------------------------------------------------------------
# Slash command entry point (/skills in chat)
# ---------------------------------------------------------------------------

def handle_skills_slash(cmd: str, console: Optional[Console] = None) -> None:
    """Parsea y despacha `/skills <subcomando> [args]` desde la interfaz de chat.

    Ejemplos:
        /skills search kubernetes
        /skills install openai/skills/skill-creator
        /skills install openai/skills/skill-creator --force
        /skills inspect openai/skills/skill-creator
        /skills list
        /skills list --source hub
        /skills audit
        /skills audit my-skill
        /skills uninstall my-skill
        /skills tap list
        /skills tap add owner/repo
        /skills tap remove owner/repo
    """
    c = console or _console
    parts = cmd.strip().split()

    # Quitar el "/skills" inicial si está presente
    if parts and parts[0].lower() == "/skills":
        parts = parts[1:]

    if not parts:
        _print_skills_help(c)
        return

    action = parts[0].lower()
    args = parts[1:]

    if action == "browse":
        page = 1
        page_size = 20
        source = "all"
        i = 0
        while i < len(args):
            if args[i] == "--page" and i + 1 < len(args):
                try:
                    page = int(args[i + 1])
                except ValueError:
                    pass
                i += 2
            elif args[i] == "--size" and i + 1 < len(args):
                try:
                    page_size = int(args[i + 1])
                except ValueError:
                    pass
                i += 2
            elif args[i] == "--source" and i + 1 < len(args):
                source = args[i + 1]
                i += 2
            else:
                i += 1
        do_browse(page=page, page_size=page_size, source=source, console=c)

    elif action == "search":
        if not args:
            c.print("[bold red]Uso:[/] /skills search <query> [--source github] [--limit N]\n")
            return
        source = "all"
        limit = 10
        query_parts = []
        i = 0
        while i < len(args):
            if args[i] == "--source" and i + 1 < len(args):
                source = args[i + 1]
                i += 2
            elif args[i] == "--limit" and i + 1 < len(args):
                try:
                    limit = int(args[i + 1])
                except ValueError:
                    pass
                i += 2
            else:
                query_parts.append(args[i])
                i += 1
        do_search(" ".join(query_parts), source=source, limit=limit, console=c)

    elif action == "install":
        if not args:
            c.print("[bold red]Uso:[/] /skills install <identifier> [--category <cat>] [--force]\n")
            return
        identifier = args[0]
        category = ""
        force = "--force" in args
        for i, a in enumerate(args):
            if a == "--category" and i + 1 < len(args):
                category = args[i + 1]
        do_install(identifier, category=category, force=force, console=c)

    elif action == "inspect":
        if not args:
            c.print("[bold red]Uso:[/] /skills inspect <identifier>\n")
            return
        do_inspect(args[0], console=c)

    elif action == "list":
        source_filter = "all"
        if "--source" in args:
            idx = args.index("--source")
            if idx + 1 < len(args):
                source_filter = args[idx + 1]
        do_list(source_filter=source_filter, console=c)

    elif action == "audit":
        name = args[0] if args else None
        do_audit(name=name, console=c)

    elif action == "uninstall":
        if not args:
            c.print("[bold red]Uso:[/] /skills uninstall <name>\n")
            return
        do_uninstall(args[0], console=c)

    elif action == "publish":
        if not args:
            c.print("[bold red]Uso:[/] /skills publish <skill-path> [--to github] [--repo owner/repo]\n")
            return
        skill_path = args[0]
        target = "github"
        repo = ""
        for i, a in enumerate(args):
            if a == "--to" and i + 1 < len(args):
                target = args[i + 1]
            if a == "--repo" and i + 1 < len(args):
                repo = args[i + 1]
        do_publish(skill_path, target=target, repo=repo, console=c)

    elif action == "snapshot":
        if not args:
            c.print("[bold red]Uso:[/] /skills snapshot export <file> | /skills snapshot import <file>\n")
            return
        snap_action = args[0]
        if snap_action == "export" and len(args) > 1:
            do_snapshot_export(args[1], console=c)
        elif snap_action == "import" and len(args) > 1:
            force = "--force" in args
            do_snapshot_import(args[1], force=force, console=c)
        else:
            c.print("[bold red]Uso:[/] /skills snapshot export <file> | /skills snapshot import <file>\n")

    elif action == "tap":
        if not args:
            do_tap("list", console=c)
            return
        tap_action = args[0]
        repo = args[1] if len(args) > 1 else ""
        do_tap(tap_action, repo=repo, console=c)

    elif action in ("help", "--help", "-h"):
        _print_skills_help(c)

    else:
        c.print(f"[bold red]Acción desconocida:[/] {action}")
        _print_skills_help(c)


def _print_skills_help(console: Console) -> None:
    """Imprime la ayuda para el comando /skills."""
    console.print(Panel(
        "[bold]Comandos del Skills Hub:[/]\n\n"
        "  [cyan]browse[/] [--source official]   Navega por todas las skills disponibles (paginado)\n"
        "  [cyan]search[/] <query>              Busca skills en los registros\n"
        "  [cyan]install[/] <identifier>        Instala una skill (con escaneo de seguridad)\n"
        "  [cyan]inspect[/] <identifier>        Previsualiza una skill sin instalarla\n"
        "  [cyan]list[/] [--source hub|builtin|local] Lista las skills instaladas\n"
        "  [cyan]audit[/] [name]                Reescanea las skills del hub por seguridad\n"
        "  [cyan]uninstall[/] <name>            Elimina una skill instalada desde el hub\n"
        "  [cyan]publish[/] <path> --repo <r>   Publica una skill en GitHub vía PR\n"
        "  [cyan]snapshot[/] export|import      Exporta/importa configuraciones de skills\n"
        "  [cyan]tap[/] list|add|remove         Gestiona fuentes de skills\n",
        title="/skills",
    ))
