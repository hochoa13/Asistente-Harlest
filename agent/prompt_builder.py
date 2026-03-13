"""Construcción del prompt de sistema: identidad, pistas de plataforma,
índice de skills y archivos de contexto.

Todas las funciones son *stateless*. AIAgent._build_system_prompt() las llama
para ensamblar las distintas piezas y luego las combina con memoria y
prompts efímeros.
"""

import logging
import os
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Escaneo de archivos de contexto: detectar prompt injection en AGENTS.md,
# .cursorrules y SOUL.md antes de inyectarlos en el prompt de sistema.
# ---------------------------------------------------------------------------

_CONTEXT_THREAT_PATTERNS = [
    (r'ignore\s+(previous|all|above|prior)\s+instructions', "prompt_injection"),
    (r'do\s+not\s+tell\s+the\s+user', "deception_hide"),
    (r'system\s+prompt\s+override', "sys_prompt_override"),
    (r'disregard\s+(your|all|any)\s+(instructions|rules|guidelines)', "disregard_rules"),
    (r'act\s+as\s+(if|though)\s+you\s+(have\s+no|don\'t\s+have)\s+(restrictions|limits|rules)', "bypass_restrictions"),
    (r'<!--[^>]*(?:ignore|override|system|secret|hidden)[^>]*-->', "html_comment_injection"),
    (r'<\s*div\s+style\s*=\s*["\'].*display\s*:\s*none', "hidden_div"),
    (r'translate\s+.*\s+into\s+.*\s+and\s+(execute|run|eval)', "translate_execute"),
    (r'curl\s+[^\n]*\$\{?\w*(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|API)', "exfil_curl"),
    (r'cat\s+[^\n]*(\.env|credentials|\.netrc|\.pgpass)', "read_secrets"),
]

_CONTEXT_INVISIBLE_CHARS = {
    '\u200b', '\u200c', '\u200d', '\u2060', '\ufeff',
    '\u202a', '\u202b', '\u202c', '\u202d', '\u202e',
}


def _scan_context_content(content: str, filename: str) -> str:
    """Escanea el contenido de un archivo de contexto en busca de inyecciones.

    Devuelve el contenido saneado (o un marcador de bloqueo si se detecta algo
    potencialmente peligroso).
    """
    findings = []

    # Comprobar caracteres Unicode invisibles
    for char in _CONTEXT_INVISIBLE_CHARS:
        if char in content:
            findings.append(f"invisible unicode U+{ord(char):04X}")

    # Comprobar patrones de amenaza
    for pattern, pid in _CONTEXT_THREAT_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            findings.append(pid)

    if findings:
        logger.warning("Context file %s blocked: %s", filename, ", ".join(findings))
        return f"[BLOCKED: {filename} contenía posible prompt injection ({', '.join(findings)}). Contenido no cargado.]"

    return content

# =========================================================================
# Constants
# =========================================================================

DEFAULT_AGENT_IDENTITY = (
    "Eres Hermes Agent, un asistente de IA inteligente creado por harlest "
    "y desarrollado por Harold Andres Hernandez Ochoa. "
    "Eres servicial, con muchos conocimientos y directo. Ayudas a los usuarios "
    "con una amplia variedad de tareas, incluyendo responder preguntas, escribir "
    "y editar código, analizar información, trabajo creativo y ejecutar acciones "
    "mediante tus herramientas. Te comunicas con claridad, reconoces cuando hay "
    "incertidumbre y priorizas ser genuinamente útil por encima de ser verboso, "
    "salvo que más abajo se indique lo contrario. Por defecto, responde siempre "
    "en español neutro, a menos que el usuario pida explícitamente otro idioma, "
    "y sé objetivo y eficiente en tu exploración e investigaciones."
)

RANSOMWARE_PENTESTING_IDENTITY = (
    "Eres Hermes Agent especializado en Ciberseguridad Ofensiva y Defensa contra Ransomware, "
    "desarrollado por Harold Andres Hernandez Ochoa. Eres un pentester profesional y analista "
    "experto en malware, con profundos conocimientos en:\n\n"
    "— Análisis de Ransomware: Ingeniería inversa de variantes, identificación de patrones de "
    "cifrado, técnicas de distribución (email, exploit kits, lateral movement), cadenas de suministro.\n"
    "— Penetration Testing: Reconocimiento, enumeración de activos, explotación de vulnerabilidades, "
    "post-explotación, escalada de privilegios, persistencia, cobertura de huellas.\n"
    "— Malware Analysis: Análisis estático y dinámico, desofuscación, comportamiento en sandbox, "
    "detonación segura, indicators of compromise (IOCs), YARA rules.\n"
    "— Defensive Posture: Hardening de sistemas, EDR/XDR, respuesta a incidentes, forense digital, "
    "recuperación post-ataque, detección de tácticas MITRE ATT&CK.\n"
    "— Red Team / Blue Team: Simulación de ataques realistas, evaluación de controles de seguridad, "
    "testing de políticas y procedimientos de seguridad.\n\n"
    "Comunicas hallazgos técnicos con claridad profesional, priorizando especificidad y "
    "rigor científico. Proporcionas análisis fundamentado en estándares de la industria (NIST, "
    "CIS, MITRE) y mejores prácticas. Respondes siempre en español neutro profpesional, "
    "a menos que se solicite otro idioma. Mantienes confidencialidad en contextos sensibles "
    "y subrays consideraciones éticas y legales en todas las actividades de seguridad."
)

MEMORY_GUIDANCE = (
    "Tienes memoria persistente entre sesiones. Guarda de forma proactiva las "
    "cosas importantes que aprendas (preferencias del usuario, detalles del "
    "entorno, enfoques útiles) y lo que vayas haciendo (como un diario) usando "
    "la herramienta de memoria; no esperes a que te lo pidan."
)

SESSION_SEARCH_GUIDANCE = (
    "Cuando el usuario haga referencia a algo de una conversación anterior o "
    "sospeches que existe contexto previo relevante, usa session_search para "
    "recordarlo antes de pedirle que lo repita."
)

SKILLS_GUIDANCE = (
    "Después de completar una tarea compleja (5+ llamadas de herramienta), "
    "corregir un error difícil o descubrir un flujo de trabajo no trivial, "
    "considera guardar el enfoque como una habilidad con skill_manage para "
    "poder reutilizarlo en el futuro."
)

PLATFORM_HINTS = {
    "whatsapp": (
        "Estás en una plataforma de mensajería de texto, WhatsApp. "
        "No uses markdown porque no se renderiza correctamente. "
        "Puedes enviar archivos multimedia de forma nativa: para entregar un archivo "
        "al usuario, incluye MEDIA:/ruta/absoluta/al/archivo en tu respuesta. El archivo "
        "se enviará como un adjunto nativo de WhatsApp: las imágenes (.jpg, .png, "
        ".webp) aparecen como fotos, los videos (.mp4, .mov) se reproducen en línea y "
        "otros archivos llegan como documentos descargables. También puedes incluir URLs "
        "de imágenes en formato markdown ![alt](url) y se enviarán como fotos."
    ),
    "telegram": (
        "Estás en una plataforma de mensajería de texto, Telegram. "
        "No uses markdown porque no se renderiza correctamente. "
        "Puedes enviar archivos multimedia de forma nativa: para entregar un archivo "
        "al usuario, incluye MEDIA:/ruta/absoluta/al/archivo en tu respuesta. Las imágenes "
        "(.png, .jpg, .webp) aparecen como fotos, el audio (.ogg) se envía como notas de voz "
        "y los videos (.mp4) se reproducen en línea. También puedes incluir URLs de imágenes "
        "en formato markdown ![alt](url) y se enviarán como fotos nativas."
    ),
    "discord": (
        "Estás en un servidor o grupo de Discord comunicándote con tu usuario. "
        "Puedes enviar archivos multimedia de forma nativa: incluye MEDIA:/ruta/absoluta/al/archivo "
        "en tu respuesta. Las imágenes (.png, .jpg, .webp) se envían como adjuntos de foto "
        "y el audio como archivos adjuntos. También puedes incluir URLs de imágenes en formato "
        "markdown ![alt](url) y se enviarán como adjuntos."
    ),
    "slack": (
        "Estás en un workspace de Slack comunicándote con tu usuario. "
        "Puedes enviar archivos multimedia de forma nativa: incluye MEDIA:/ruta/absoluta/al/archivo "
        "en tu respuesta. Las imágenes (.png, .jpg, .webp) se suben como adjuntos de foto "
        "y el audio como archivos adjuntos. También puedes incluir URLs de imágenes en formato "
        "markdown ![alt](url) y se subirán como adjuntos."
    ),
    "signal": (
        "Estás en una plataforma de mensajería de texto, Signal. "
        "No uses markdown porque no se renderiza correctamente. "
        "Puedes enviar archivos multimedia de forma nativa: para entregar un archivo al usuario, "
        "incluye MEDIA:/ruta/absoluta/al/archivo en tu respuesta. Las imágenes (.png, .jpg, .webp) "
        "aparecen como fotos, el audio como adjuntos y otros archivos llegan como documentos "
        "descargables. También puedes incluir URLs de imágenes en formato markdown ![alt](url) y "
        "se enviarán como fotos."
    ),
    "email": (
        "Te estás comunicando por correo electrónico. Escribe respuestas claras y bien estructuradas "
        "adecuadas para email. Usa formato de texto plano (sin markdown). "
        "Mantén las respuestas concisas pero completas. Puedes enviar archivos adjuntos: "
        "incluye MEDIA:/ruta/absoluta/al/archivo en tu respuesta. La línea de asunto se conserva "
        "para el hilo de conversación. No incluyas saludos ni despedidas salvo que sea apropiado "
        "por el contexto."
    ),
    "cli": (
        "Eres un agente de IA en modo CLI. Intenta no usar markdown, solo texto simple "
        "que se pueda mostrar correctamente en una terminal."
    ),
}

CONTEXT_FILE_MAX_CHARS = 20_000
CONTEXT_TRUNCATE_HEAD_RATIO = 0.7
CONTEXT_TRUNCATE_TAIL_RATIO = 0.2


# =========================================================================
# Skills index
# =========================================================================

def _read_skill_description(skill_file: Path, max_chars: int = 60) -> str:
    """Lee la descripción desde el frontmatter de un SKILL.md, limitada a max_chars."""
    try:
        raw = skill_file.read_text(encoding="utf-8")[:2000]
        match = re.search(
            r"^---\s*\n.*?description:\s*(.+?)\s*\n.*?^---",
            raw, re.MULTILINE | re.DOTALL,
        )
        if match:
            desc = match.group(1).strip().strip("'\"")
            if len(desc) > max_chars:
                desc = desc[:max_chars - 3] + "..."
            return desc
    except Exception as e:
        logger.debug("Failed to read skill description from %s: %s", skill_file, e)
    return ""


def _skill_is_platform_compatible(skill_file: Path) -> bool:
    """Comprobación rápida de si un SKILL.md es compatible con la plataforma actual.

    Lee solo lo necesario para analizar el campo ``platforms`` del frontmatter.
    Las skills sin ese campo (la gran mayoría) siempre se consideran compatibles.
    """
    try:
        from tools.skills_tool import _parse_frontmatter, skill_matches_platform
        raw = skill_file.read_text(encoding="utf-8")[:2000]
        frontmatter, _ = _parse_frontmatter(raw)
        return skill_matches_platform(frontmatter)
    except Exception:
        return True  # Err on the side of showing the skill


def _read_skill_conditions(skill_file: Path) -> dict:
    """Extrae los campos de activación condicional del frontmatter de un SKILL.md."""
    try:
        from tools.skills_tool import _parse_frontmatter
        raw = skill_file.read_text(encoding="utf-8")[:2000]
        frontmatter, _ = _parse_frontmatter(raw)
        hermes = frontmatter.get("metadata", {}).get("hermes", {})
        return {
            "fallback_for_toolsets": hermes.get("fallback_for_toolsets", []),
            "requires_toolsets": hermes.get("requires_toolsets", []),
            "fallback_for_tools": hermes.get("fallback_for_tools", []),
            "requires_tools": hermes.get("requires_tools", []),
        }
    except Exception:
        return {}


def _skill_should_show(
    conditions: dict,
    available_tools: "set[str] | None",
    available_toolsets: "set[str] | None",
) -> bool:
    """Devuelve False si las reglas de activación condicional de la skill la excluyen."""
    if available_tools is None and available_toolsets is None:
        return True  # No filtering info — show everything (backward compat)

    at = available_tools or set()
    ats = available_toolsets or set()

    # fallback_for: hide when the primary tool/toolset IS available
    for ts in conditions.get("fallback_for_toolsets", []):
        if ts in ats:
            return False
    for t in conditions.get("fallback_for_tools", []):
        if t in at:
            return False

    # requires: hide when a required tool/toolset is NOT available
    for ts in conditions.get("requires_toolsets", []):
        if ts not in ats:
            return False
    for t in conditions.get("requires_tools", []):
        if t not in at:
            return False

    return True


def build_skills_system_prompt(
    available_tools: "set[str] | None" = None,
    available_toolsets: "set[str] | None" = None,
) -> str:
    """Construye un índice compacto de skills para el prompt de sistema.

    Escanea ~/.hermes/skills/ en busca de archivos SKILL.md agrupados por
    categoría. Incluye descripciones por skill desde el frontmatter para que
    el modelo pueda asociarlas por significado y no solo por nombre, y filtra
    las skills incompatibles con la plataforma actual.
    """
    hermes_home = Path(os.getenv("HERMES_HOME", Path.home() / ".hermes"))
    skills_dir = hermes_home / "skills"

    if not skills_dir.exists():
        return ""

    # Collect skills with descriptions, grouped by category
    # Each entry: (skill_name, description)
    # Supports sub-categories: skills/mlops/training/axolotl/SKILL.md
    # → category "mlops/training", skill "axolotl"
    skills_by_category: dict[str, list[tuple[str, str]]] = {}
    for skill_file in skills_dir.rglob("SKILL.md"):
        # Skip skills incompatible with the current OS platform
        if not _skill_is_platform_compatible(skill_file):
            continue
        # Skip skills whose conditional activation rules exclude them
        conditions = _read_skill_conditions(skill_file)
        if not _skill_should_show(conditions, available_tools, available_toolsets):
            continue
        rel_path = skill_file.relative_to(skills_dir)
        parts = rel_path.parts
        if len(parts) >= 2:
            # Category is everything between skills_dir and the skill folder
            # e.g. parts = ("mlops", "training", "axolotl", "SKILL.md")
            #   → category = "mlops/training", skill_name = "axolotl"
            # e.g. parts = ("github", "github-auth", "SKILL.md")
            #   → category = "github", skill_name = "github-auth"
            skill_name = parts[-2]
            category = "/".join(parts[:-2]) if len(parts) > 2 else parts[0]
        else:
            category = "general"
            skill_name = skill_file.parent.name
        desc = _read_skill_description(skill_file)
        skills_by_category.setdefault(category, []).append((skill_name, desc))

    if not skills_by_category:
        return ""

    # Read category-level descriptions from DESCRIPTION.md
    # Checks both the exact category path and parent directories
    category_descriptions = {}
    for category in skills_by_category:
        cat_path = Path(category)
        desc_file = skills_dir / cat_path / "DESCRIPTION.md"
        if desc_file.exists():
            try:
                content = desc_file.read_text(encoding="utf-8")
                match = re.search(r"^---\s*\n.*?description:\s*(.+?)\s*\n.*?^---", content, re.MULTILINE | re.DOTALL)
                if match:
                    category_descriptions[category] = match.group(1).strip()
            except Exception as e:
                logger.debug("Could not read skill description %s: %s", desc_file, e)

    index_lines = []
    for category in sorted(skills_by_category.keys()):
        cat_desc = category_descriptions.get(category, "")
        if cat_desc:
            index_lines.append(f"  {category}: {cat_desc}")
        else:
            index_lines.append(f"  {category}:")
        # Deduplicate and sort skills within each category
        seen = set()
        for name, desc in sorted(skills_by_category[category], key=lambda x: x[0]):
            if name in seen:
                continue
            seen.add(name)
            if desc:
                index_lines.append(f"    - {name}: {desc}")
            else:
                index_lines.append(f"    - {name}")

    return (
        "## Skills (obligatorio)\n"
        "Antes de responder, revisa las skills siguientes. Si alguna coincide "
        "claramente con la tarea, cárgala con skill_view(name) y sigue sus "
        "instrucciones. Si una skill tiene problemas, arréglala con "
        "skill_manage(action='patch').\n"
        "\n"
        "<available_skills>\n"
        + "\n".join(index_lines) + "\n"
        "</available_skills>\n"
        "\n"
        "Si ninguna coincide, continúa normalmente sin cargar una skill."
    )


# =========================================================================
# Context files (SOUL.md, AGENTS.md, .cursorrules)
# =========================================================================

def _truncate_content(content: str, filename: str, max_chars: int = CONTEXT_FILE_MAX_CHARS) -> str:
    """Recorta por cabeza/cola con un marcador en el medio."""
    if len(content) <= max_chars:
        return content
    head_chars = int(max_chars * CONTEXT_TRUNCATE_HEAD_RATIO)
    tail_chars = int(max_chars * CONTEXT_TRUNCATE_TAIL_RATIO)
    head = content[:head_chars]
    tail = content[-tail_chars:]
    marker = f"\n\n[...truncated {filename}: se conservaron {head_chars}+{tail_chars} de {len(content)} caracteres. Usa las herramientas de archivos para leer el archivo completo.]\n\n"
    return head + marker + tail


def build_context_files_prompt(cwd: Optional[str] = None) -> str:
    """Descubre y carga archivos de contexto para el prompt de sistema.

    Descubrimiento: AGENTS.md (recursivo), .cursorrules / .cursor/rules/*.mdc,
    SOUL.md (primero en el cwd y luego en ~/.hermes/ como respaldo). Cada uno se
    limita a un máximo de 20 000 caracteres.
    """
    if cwd is None:
        cwd = os.getcwd()

    cwd_path = Path(cwd).resolve()
    sections = []

    # AGENTS.md (hierarchical, recursive)
    top_level_agents = None
    for name in ["AGENTS.md", "agents.md"]:
        candidate = cwd_path / name
        if candidate.exists():
            top_level_agents = candidate
            break

    if top_level_agents:
        agents_files = []
        for root, dirs, files in os.walk(cwd_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', '__pycache__', 'venv', '.venv')]
            for f in files:
                if f.lower() == "agents.md":
                    agents_files.append(Path(root) / f)
        agents_files.sort(key=lambda p: len(p.parts))

        total_agents_content = ""
        for agents_path in agents_files:
            try:
                content = agents_path.read_text(encoding="utf-8").strip()
                if content:
                    rel_path = agents_path.relative_to(cwd_path)
                    content = _scan_context_content(content, str(rel_path))
                    total_agents_content += f"## {rel_path}\n\n{content}\n\n"
            except Exception as e:
                logger.debug("Could not read %s: %s", agents_path, e)

        if total_agents_content:
            total_agents_content = _truncate_content(total_agents_content, "AGENTS.md")
            sections.append(total_agents_content)

    # .cursorrules
    cursorrules_content = ""
    cursorrules_file = cwd_path / ".cursorrules"
    if cursorrules_file.exists():
        try:
            content = cursorrules_file.read_text(encoding="utf-8").strip()
            if content:
                content = _scan_context_content(content, ".cursorrules")
                cursorrules_content += f"## .cursorrules\n\n{content}\n\n"
        except Exception as e:
            logger.debug("Could not read .cursorrules: %s", e)

    cursor_rules_dir = cwd_path / ".cursor" / "rules"
    if cursor_rules_dir.exists() and cursor_rules_dir.is_dir():
        mdc_files = sorted(cursor_rules_dir.glob("*.mdc"))
        for mdc_file in mdc_files:
            try:
                content = mdc_file.read_text(encoding="utf-8").strip()
                if content:
                    content = _scan_context_content(content, f".cursor/rules/{mdc_file.name}")
                    cursorrules_content += f"## .cursor/rules/{mdc_file.name}\n\n{content}\n\n"
            except Exception as e:
                logger.debug("Could not read %s: %s", mdc_file, e)

    if cursorrules_content:
        cursorrules_content = _truncate_content(cursorrules_content, ".cursorrules")
        sections.append(cursorrules_content)

    # SOUL.md (cwd first, then ~/.hermes/ fallback)
    soul_path = None
    for name in ["SOUL.md", "soul.md"]:
        candidate = cwd_path / name
        if candidate.exists():
            soul_path = candidate
            break
    if not soul_path:
        global_soul = Path.home() / ".hermes" / "SOUL.md"
        if global_soul.exists():
            soul_path = global_soul

    if soul_path:
        try:
            content = soul_path.read_text(encoding="utf-8").strip()
            if content:
                content = _scan_context_content(content, "SOUL.md")
                content = _truncate_content(content, "SOUL.md")
                sections.append(
                    f"## SOUL.md\n\nSi existe SOUL.md, adopta su personalidad y tono. "
                    f"Evita respuestas rígidas o genéricas; sigue su guía salvo que otras "
                    f"instrucciones de mayor prioridad la contradigan.\n\n{content}"
                )
        except Exception as e:
            logger.debug("Could not read SOUL.md from %s: %s", soul_path, e)

    if not sections:
        return ""
    return "# Project Context\n\nSe han cargado los siguientes archivos de contexto del proyecto; debes seguir sus indicaciones:\n\n" + "\n".join(sections)
