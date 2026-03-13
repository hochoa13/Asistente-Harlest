"""Configuración de *skills* para Hermes Agent.
El comando `hermes skills` entra en este módulo.

Permite activar/desactivar *skills* individuales o categorías completas,
tanto de forma global como por plataforma.
La configuración se guarda en ~/.hermes/config.yaml bajo:

    skills:
        disabled: [skill-a, skill-b]          # lista global de skills deshabilitadas
        platform_disabled:                    # overrides por plataforma
            telegram: [skill-c]
            cli: []
"""
from typing import Dict, List, Optional, Set

from hermes_cli.config import load_config, save_config
from hermes_cli.colors import Colors, color

PLATFORMS = {
    "cli":      "🖥️  CLI",
    "telegram": "📱 Telegram",
    "discord":  "💬 Discord",
    "slack":    "💼 Slack",
    "whatsapp": "📱 WhatsApp",
    "signal":   "📡 Signal",
    "email":    "📧 Email",
}

# ─── Helpers de configuración ────────────────────────────────────────────────

def get_disabled_skills(config: dict, platform: Optional[str] = None) -> Set[str]:
    """Devuelve los nombres de *skills* deshabilitadas.

    Cuando se pasa una plataforma, usa la lista específica si existe; en caso
    contrario, cae en la lista global.
    """
    skills_cfg = config.get("skills", {})
    global_disabled = set(skills_cfg.get("disabled", []))
    if platform is None:
        return global_disabled
    platform_disabled = skills_cfg.get("platform_disabled", {}).get(platform)
    if platform_disabled is None:
        return global_disabled
    return set(platform_disabled)


def save_disabled_skills(config: dict, disabled: Set[str], platform: Optional[str] = None):
    """Persiste en la configuración los nombres de *skills* deshabilitadas."""
    config.setdefault("skills", {})
    if platform is None:
        config["skills"]["disabled"] = sorted(disabled)
    else:
        config["skills"].setdefault("platform_disabled", {})
        config["skills"]["platform_disabled"][platform] = sorted(disabled)
    save_config(config)


# ─── Descubrimiento de skills ────────────────────────────────────────────────

def _list_all_skills() -> List[dict]:
    """Devuelve todas las *skills* instaladas (ignorando si están deshabilitadas)."""
    try:
        from tools.skills_tool import _find_all_skills
        return _find_all_skills(skip_disabled=True)
    except Exception:
        return []


def _get_categories(skills: List[dict]) -> List[str]:
    """Devuelve los nombres de categoría únicos y ordenados (None → "sin categoría")."""
    return sorted({s["category"] or "sin categoría" for s in skills})


# ─── Selección de plataforma ─────────────────────────────────────────────────

def _select_platform() -> Optional[str]:
    """Pregunta al usuario qué plataforma configurar (o global)."""
    options = [("global", "Todas las plataformas (valor global por defecto)")] + list(PLATFORMS.items())
    print()
    print(color("  Configurar skills para:", Colors.BOLD))
    for i, (key, label) in enumerate(options, 1):
        print(f"  {i}. {label}")
    print()
    try:
        raw = input(color("  Selecciona [1]: ", Colors.YELLOW)).strip()
    except (KeyboardInterrupt, EOFError):
        return None
    if not raw:
        return None  # global
    try:
        idx = int(raw) - 1
        if 0 <= idx < len(options):
            key = options[idx][0]
            return None if key == "global" else key
    except ValueError:
        pass
    return None


# ─── Activar/desactivar por categoría ────────────────────────────────────────

def _toggle_by_category(skills: List[dict], disabled: Set[str]) -> Set[str]:
    """Activa/desactiva todas las *skills* de una categoría a la vez."""
    from hermes_cli.curses_ui import curses_checklist

    categories = _get_categories(skills)
    cat_labels = []
    # Una categoría está "habilitada" (marcada) cuando NO todas sus skills están deshabilitadas
    pre_selected = set()
    for i, cat in enumerate(categories):
        cat_skills = [s["name"] for s in skills if (s["category"] or "sin categoría") == cat]
        cat_labels.append(f"{cat} ({len(cat_skills)} skills)")
        if not all(s in disabled for s in cat_skills):
            pre_selected.add(i)

    chosen = curses_checklist(
        "Categorías — activar/desactivar categorías completas",
        cat_labels,
        pre_selected,
        cancel_returns=pre_selected,
    )

    new_disabled = set(disabled)
    for i, cat in enumerate(categories):
        cat_skills = {s["name"] for s in skills if (s["category"] or "sin categoría") == cat}
        if i in chosen:
            new_disabled -= cat_skills  # categoría habilitada → se quita de la lista de deshabilitadas
        else:
            new_disabled |= cat_skills  # categoría deshabilitada → se añade a la lista de deshabilitadas
    return new_disabled


# ─── Punto de entrada ────────────────────────────────────────────────────────

def skills_command(args=None):
    """Punto de entrada para el comando `hermes skills`."""
    from hermes_cli.curses_ui import curses_checklist

    config = load_config()
    skills = _list_all_skills()

    if not skills:
        print(color("  No hay skills instaladas.", Colors.DIM))
        return

    # Paso 1: seleccionar plataforma
    platform = _select_platform()
    platform_label = PLATFORMS.get(platform, "Todas las plataformas") if platform else "Todas las plataformas"

    # Paso 2: seleccionar modo — individual o por categoría
    print()
    print(color(f"  Configurar para: {platform_label}", Colors.DIM))
    print()
    print("  1. Activar/desactivar skills individuales")
    print("  2. Activar/desactivar por categoría")
    print()
    try:
        mode = input(color("  Selecciona [1]: ", Colors.YELLOW)).strip() or "1"
    except (KeyboardInterrupt, EOFError):
        return

    disabled = get_disabled_skills(config, platform)

    if mode == "2":
        new_disabled = _toggle_by_category(skills, disabled)
    else:
        # Construir etiquetas y mapear índices → nombres de skills
        labels = [
            f"{s['name']}  ({s['category'] or 'sin categoría'})  —  {s['description'][:55]}"
            for s in skills
        ]
        # "seleccionado" = habilitado (no deshabilitado) — coincide con la convención [✓]
        pre_selected = {i for i, s in enumerate(skills) if s["name"] not in disabled}
        chosen = curses_checklist(
            f"Skills para {platform_label}",
            labels,
            pre_selected,
            cancel_returns=pre_selected,
        )
        # Anything NOT chosen is disabled
        new_disabled = {skills[i]["name"] for i in range(len(skills)) if i not in chosen}

    if new_disabled == disabled:
        print(color("  Sin cambios.", Colors.DIM))
        return

    save_disabled_skills(config, new_disabled, platform)
    enabled_count = len(skills) - len(new_disabled)
    print(
        color(
            f"✓ Guardado: {enabled_count} habilitada(s), {len(new_disabled)} deshabilitada(s) ({platform_label}).",
            Colors.GREEN,
        )
    )
