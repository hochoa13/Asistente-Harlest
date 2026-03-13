#!/usr/bin/env python3
"""File Tools Module - LLM agent file manipulation tools."""

import json
import logging
import os
import threading
from typing import Optional
from tools.file_operations import ShellFileOperations
from agent.redact import redact_sensitive_text

logger = logging.getLogger(__name__)

_file_ops_lock = threading.Lock()
_file_ops_cache: dict = {}

# Track files read per task to detect re-read loops after context compression.
# Per task_id we store:
#   "last_key":     the key of the most recent read/search call (or None)
#   "consecutive":  how many times that exact call has been repeated in a row
#   "read_history": set of (path, offset, limit) tuples for get_read_files_summary
_read_tracker_lock = threading.Lock()
_read_tracker: dict = {}


def _get_file_ops(task_id: str = "default") -> ShellFileOperations:
    """Get or create ShellFileOperations for a terminal environment.

    Respects the TERMINAL_ENV setting -- if the task_id doesn't have an
    environment yet, creates one using the configured backend (local, docker,
    modal, etc.) rather than always defaulting to local.

    Thread-safe: uses the same per-task creation locks as terminal_tool to
    prevent duplicate sandbox creation from concurrent tool calls.
    """
    from tools.terminal_tool import (
        _active_environments, _env_lock, _create_environment,
        _get_env_config, _last_activity, _start_cleanup_thread,
        _check_disk_usage_warning,
        _creation_locks, _creation_locks_lock,
    )
    import time

    # Fast path: check cache -- but also verify the underlying environment
    # is still alive (it may have been killed by the cleanup thread).
    with _file_ops_lock:
        cached = _file_ops_cache.get(task_id)
    if cached is not None:
        with _env_lock:
            if task_id in _active_environments:
                _last_activity[task_id] = time.time()
                return cached
            else:
                # Environment was cleaned up -- invalidate stale cache entry
                with _file_ops_lock:
                    _file_ops_cache.pop(task_id, None)

    # Need to ensure the environment exists before building file_ops.
    # Acquire per-task lock so only one thread creates the sandbox.
    with _creation_locks_lock:
        if task_id not in _creation_locks:
            _creation_locks[task_id] = threading.Lock()
        task_lock = _creation_locks[task_id]

    with task_lock:
        # Double-check: another thread may have created it while we waited
        with _env_lock:
            if task_id in _active_environments:
                _last_activity[task_id] = time.time()
                terminal_env = _active_environments[task_id]
            else:
                terminal_env = None

        if terminal_env is None:
            from tools.terminal_tool import _task_env_overrides

            config = _get_env_config()
            env_type = config["env_type"]
            overrides = _task_env_overrides.get(task_id, {})

            if env_type == "docker":
                image = overrides.get("docker_image") or config["docker_image"]
            elif env_type == "singularity":
                image = overrides.get("singularity_image") or config["singularity_image"]
            elif env_type == "modal":
                image = overrides.get("modal_image") or config["modal_image"]
            elif env_type == "daytona":
                image = overrides.get("daytona_image") or config["daytona_image"]
            else:
                image = ""

            cwd = overrides.get("cwd") or config["cwd"]
            logger.info("Creating new %s environment for task %s...", env_type, task_id[:8])

            container_config = None
            if env_type in ("docker", "singularity", "modal", "daytona"):
                container_config = {
                    "container_cpu": config.get("container_cpu", 1),
                    "container_memory": config.get("container_memory", 5120),
                    "container_disk": config.get("container_disk", 51200),
                    "container_persistent": config.get("container_persistent", True),
                    "docker_volumes": config.get("docker_volumes", []),
                }
            terminal_env = _create_environment(
                env_type=env_type,
                image=image,
                cwd=cwd,
                timeout=config["timeout"],
                container_config=container_config,
                task_id=task_id,
            )

            with _env_lock:
                _active_environments[task_id] = terminal_env
                _last_activity[task_id] = time.time()

            _start_cleanup_thread()
            logger.info("%s environment ready for task %s", env_type, task_id[:8])

    # Build file_ops from the (guaranteed live) environment and cache it
    file_ops = ShellFileOperations(terminal_env)
    with _file_ops_lock:
        _file_ops_cache[task_id] = file_ops
    return file_ops


def clear_file_ops_cache(task_id: str = None):
    """Clear the file operations cache."""
    with _file_ops_lock:
        if task_id:
            _file_ops_cache.pop(task_id, None)
        else:
            _file_ops_cache.clear()


def read_file_tool(path: str, offset: int = 1, limit: int = 500, task_id: str = "default") -> str:
    """Read a file with pagination and line numbers."""
    try:
        file_ops = _get_file_ops(task_id)
        result = file_ops.read_file(path, offset, limit)
        if result.content:
            result.content = redact_sensitive_text(result.content)
        result_dict = result.to_dict()

        # Track reads to detect *consecutive* re-read loops.
        # The counter resets whenever any other tool is called in between,
        # so only truly back-to-back identical reads trigger warnings/blocks.
        read_key = ("read", path, offset, limit)
        with _read_tracker_lock:
            task_data = _read_tracker.setdefault(task_id, {
                "last_key": None, "consecutive": 0, "read_history": set(),
            })
            task_data["read_history"].add((path, offset, limit))
            if task_data["last_key"] == read_key:
                task_data["consecutive"] += 1
            else:
                task_data["last_key"] = read_key
                task_data["consecutive"] = 1
            count = task_data["consecutive"]

        if count >= 4:
            # Hard block: stop returning content to break the loop
            return json.dumps({
                "error": (
                    f"BLOCKED: You have read this exact file region {count} times in a row. "
                    "The content has NOT changed. You already have this information. "
                    "STOP re-reading and proceed with your task."
                ),
                "path": path,
                "already_read": count,
            }, ensure_ascii=False)
        elif count >= 3:
            result_dict["_warning"] = (
                f"You have read this exact file region {count} times consecutively. "
                "The content has not changed since your last read. Use the information you already have. "
                "If you are stuck in a loop, stop reading and proceed with writing or responding."
            )

        return json.dumps(result_dict, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def get_read_files_summary(task_id: str = "default") -> list:
    """Return a list of files read in this session for the given task.

    Used by context compression to preserve file-read history across
    compression boundaries.
    """
    with _read_tracker_lock:
        task_data = _read_tracker.get(task_id, {})
        read_history = task_data.get("read_history", set())
        seen_paths: dict = {}
        for (path, offset, limit) in read_history:
            if path not in seen_paths:
                seen_paths[path] = []
            seen_paths[path].append(f"lines {offset}-{offset + limit - 1}")
        return [
            {"path": p, "regions": regions}
            for p, regions in sorted(seen_paths.items())
        ]


def clear_read_tracker(task_id: str = None):
    """Clear the read tracker.

    Call with a task_id to clear just that task, or without to clear all.
    Should be called when a session is destroyed to prevent memory leaks
    in long-running gateway processes.
    """
    with _read_tracker_lock:
        if task_id:
            _read_tracker.pop(task_id, None)
        else:
            _read_tracker.clear()


def notify_other_tool_call(task_id: str = "default"):
    """Reset consecutive read/search counter for a task.

    Called by the tool dispatcher (model_tools.py) whenever a tool OTHER
    than read_file / search_files is executed.  This ensures we only warn
    or block on *truly consecutive* repeated reads — if the agent does
    anything else in between (write, patch, terminal, etc.) the counter
    resets and the next read is treated as fresh.
    """
    with _read_tracker_lock:
        task_data = _read_tracker.get(task_id)
        if task_data:
            task_data["last_key"] = None
            task_data["consecutive"] = 0


def write_file_tool(path: str, content: str, task_id: str = "default") -> str:
    """Write content to a file."""
    try:
        file_ops = _get_file_ops(task_id)
        result = file_ops.write_file(path, content)
        return json.dumps(result.to_dict(), ensure_ascii=False)
    except Exception as e:
        logger.error("write_file error: %s: %s", type(e).__name__, e)
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def patch_tool(mode: str = "replace", path: str = None, old_string: str = None,
               new_string: str = None, replace_all: bool = False, patch: str = None,
               task_id: str = "default") -> str:
    """Patch a file using replace mode or V4A patch format."""
    try:
        file_ops = _get_file_ops(task_id)
        
        if mode == "replace":
            if not path:
                return json.dumps({"error": "path required"})
            if old_string is None or new_string is None:
                return json.dumps({"error": "old_string and new_string required"})
            result = file_ops.patch_replace(path, old_string, new_string, replace_all)
        elif mode == "patch":
            if not patch:
                return json.dumps({"error": "patch content required"})
            result = file_ops.patch_v4a(patch)
        else:
            return json.dumps({"error": f"Unknown mode: {mode}"})
        
        result_dict = result.to_dict()
        result_json = json.dumps(result_dict, ensure_ascii=False)
        # Hint when old_string not found — saves iterations where the agent
        # retries with stale content instead of re-reading the file.
        if result_dict.get("error") and "Could not find" in str(result_dict["error"]):
            result_json += "\n\n[Hint: old_string not found. Use read_file to verify the current content, or search_files to locate the text.]"
        return result_json
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def search_tool(pattern: str, target: str = "content", path: str = ".",
                file_glob: str = None, limit: int = 50, offset: int = 0,
                output_mode: str = "content", context: int = 0,
                task_id: str = "default") -> str:
    """Search for content or files."""
    try:
        # Track searches to detect *consecutive* repeated search loops.
        search_key = ("search", pattern, target, str(path), file_glob or "")
        with _read_tracker_lock:
            task_data = _read_tracker.setdefault(task_id, {
                "last_key": None, "consecutive": 0, "read_history": set(),
            })
            if task_data["last_key"] == search_key:
                task_data["consecutive"] += 1
            else:
                task_data["last_key"] = search_key
                task_data["consecutive"] = 1
            count = task_data["consecutive"]

        if count >= 4:
            return json.dumps({
                "error": (
                    f"BLOCKED: You have run this exact search {count} times in a row. "
                    "The results have NOT changed. You already have this information. "
                    "STOP re-searching and proceed with your task."
                ),
                "pattern": pattern,
                "already_searched": count,
            }, ensure_ascii=False)

        file_ops = _get_file_ops(task_id)
        result = file_ops.search(
            pattern=pattern, path=path, target=target, file_glob=file_glob,
            limit=limit, offset=offset, output_mode=output_mode, context=context
        )
        if hasattr(result, 'matches'):
            for m in result.matches:
                if hasattr(m, 'content') and m.content:
                    m.content = redact_sensitive_text(m.content)
        result_dict = result.to_dict()

        if count >= 3:
            result_dict["_warning"] = (
                f"You have run this exact search {count} times consecutively. "
                "The results have not changed. Use the information you already have."
            )

        result_json = json.dumps(result_dict, ensure_ascii=False)
        # Hint when results were truncated — explicit next offset is clearer
        # than relying on the model to infer it from total_count vs match count.
        if result_dict.get("truncated"):
            next_offset = offset + limit
            result_json += f"\n\n[Hint: Results truncated. Use offset={next_offset} to see more, or narrow with a more specific pattern or file_glob.]"
        return result_json
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


FILE_TOOLS = [
    {"name": "read_file", "function": read_file_tool},
    {"name": "write_file", "function": write_file_tool},
    {"name": "patch", "function": patch_tool},
    {"name": "search_files", "function": search_tool}
]


def get_file_tools():
    """Get the list of file tool definitions."""
    return FILE_TOOLS


# ---------------------------------------------------------------------------
# Schemas + Registry
# ---------------------------------------------------------------------------
from tools.registry import registry


def _check_file_reqs():
    """Lazy wrapper to avoid circular import with tools/__init__.py."""
    from tools import check_file_requirements
    return check_file_requirements()

READ_FILE_SCHEMA = {
    "name": "read_file",
    "description": "Lee un archivo de texto con números de línea y paginación. Usa esto en lugar de cat/head/tail en la terminal. Formato de salida: 'LINE_NUM|CONTENT'. Sugiere nombres de archivos similares si no se encuentra. Usa offset y limit para archivos grandes. NOTA: No puede leer imágenes ni archivos binarios — usa vision_analyze para imágenes.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Ruta al archivo a leer (absoluta, relativa, o ~/ruta)"},
            "offset": {"type": "integer", "description": "Número de línea desde donde empezar a leer (basado en 1, predeterminado: 1)", "default": 1, "minimum": 1},
            "limit": {"type": "integer", "description": "Número máximo de líneas a leer (predeterminado: 500, máx: 2000)", "default": 500, "maximum": 2000}
        },
        "required": ["path"]
    }
}

WRITE_FILE_SCHEMA = {
    "name": "write_file",
    "description": "Escribe contenido en un archivo, reemplazando completamente el contenido existente. Usa esto en lugar de echo/cat heredoc en la terminal. Crea directorios padre automáticamente. SOBRESCRIBE el archivo completo — usa 'patch' para ediciones dirigidas.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Ruta del archivo a escribir (se creará si no existe, se sobrescribirá si aún existe)"},
            "content": {"type": "string", "description": "Contenido completo a escribir en el archivo"}
        },
        "required": ["path", "content"]
    }
}

PATCH_SCHEMA = {
    "name": "patch",
    "description": "Ediciones dirigidas de búsqueda y reemplazo en archivos. Usa esto en lugar de sed/awk en la terminal. Usa coincidencia difusa (9 estrategias) para que diferencias menores de espacios en blanco/indentación no la rompan. Devuelve un diff unificado. Ejecuta comprobaciones de sintaxis automáticamente después de editar.\n\nModo reemplazo (predeterminado): encuentra una cadena única y reemplazala.\nModo parche: aplica parches multi-archivo V4A para cambios en masa.",
    "parameters": {
        "type": "object",
        "properties": {
            "mode": {"type": "string", "enum": ["replace", "patch"], "description": "Modo de edición: 'replace' para búsqueda y reemplazo dirigidos, 'patch' para parches multi-archivo V4A", "default": "replace"},
            "path": {"type": "string", "description": "Ruta de archivo a editar (requerido para modo 'replace')"},
            "old_string": {"type": "string", "description": "Texto a encontrar en el archivo (requerido para modo 'replace'). Debe ser único en el archivo a menos que replace_all=true. Incluye suficiente contexto circundante para asegurar unicidad."},
            "new_string": {"type": "string", "description": "Texto de reemplazo (requerido para modo 'replace'). Puede ser cadena vacía para eliminar el texto coincidente."},
            "replace_all": {"type": "boolean", "description": "Reemplaza todas las ocurrencias en lugar de requerir una coincidencia única (predeterminado: false)", "default": False},
            "patch": {"type": "string", "description": "Contenido de parche en formato V4A (requerido para modo 'patch'). Formato:\n*** Begin Patch\n*** Update File: ruta/a/archivo\n@@ pista de contexto @@\n línea de contexto\n-línea eliminada\n+línea añadida\n*** End Patch"}
        },
        "required": ["mode"]
    }
}

SEARCH_FILES_SCHEMA = {
    "name": "search_files",
    "description": "Busca contenido de archivos o encuentra archivos por nombre. Usa esto en lugar de grep/rg/find/ls en la terminal. Respaldado por Ripgrep, más rápido que equivalentes de shell.\n\nBúsqueda de contenido (target='content'): Búsqueda de expresión regular dentro de archivos. Modos de salida: coincidencias completas con números de línea, solo rutas de archivo, o recuentos de coincidencias.\n\nBúsqueda de archivos (target='files'): Encuentra archivos por patrón glob (p. ej., '*.py', '*config*'). También usa esto en lugar de ls — resultados ordenados por tiempo de modificación.",
    "parameters": {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Patrón de expresión regular para búsqueda de contenido, o patrón glob (p. ej., '*.py') para búsqueda de archivos"},
            "target": {"type": "string", "enum": ["content", "files"], "description": "'content' busca dentro del contenido de archivos, 'files' busca archivos por nombre", "default": "content"},
            "path": {"type": "string", "description": "Directorio o archivo a buscar (predeterminado: directorio de trabajo actual)", "default": "."},
            "file_glob": {"type": "string", "description": "Filtra archivos por patrón en modo grep (p. ej., '*.py' para buscar solo en archivos Python)"},
            "limit": {"type": "integer", "description": "Número máximo de resultados a devolver (predeterminado: 50)", "default": 50},
            "offset": {"type": "integer", "description": "Omite los primeros N resultados para paginación (predeterminado: 0)", "default": 0},
            "output_mode": {"type": "string", "enum": ["content", "files_only", "count"], "description": "Formato de salida para modo grep: 'content' muestra líneas coincidentes con números de línea, 'files_only' lista rutas de archivos, 'count' muestra recuentos de coincidencias por archivo", "default": "content"},
            "context": {"type": "integer", "description": "Número de líneas de contexto antes y después de cada coincidencia (solo modo grep)", "default": 0}
        },
        "required": ["pattern"]
    }
}


def _handle_read_file(args, **kw):
    tid = kw.get("task_id") or "default"
    return read_file_tool(path=args.get("path", ""), offset=args.get("offset", 1), limit=args.get("limit", 500), task_id=tid)


def _handle_write_file(args, **kw):
    tid = kw.get("task_id") or "default"
    return write_file_tool(path=args.get("path", ""), content=args.get("content", ""), task_id=tid)


def _handle_patch(args, **kw):
    tid = kw.get("task_id") or "default"
    return patch_tool(
        mode=args.get("mode", "replace"), path=args.get("path"),
        old_string=args.get("old_string"), new_string=args.get("new_string"),
        replace_all=args.get("replace_all", False), patch=args.get("patch"), task_id=tid)


def _handle_search_files(args, **kw):
    tid = kw.get("task_id") or "default"
    target_map = {"grep": "content", "find": "files"}
    raw_target = args.get("target", "content")
    target = target_map.get(raw_target, raw_target)
    return search_tool(
        pattern=args.get("pattern", ""), target=target, path=args.get("path", "."),
        file_glob=args.get("file_glob"), limit=args.get("limit", 50), offset=args.get("offset", 0),
        output_mode=args.get("output_mode", "content"), context=args.get("context", 0), task_id=tid)


registry.register(name="read_file", toolset="file", schema=READ_FILE_SCHEMA, handler=_handle_read_file, check_fn=_check_file_reqs)
registry.register(name="write_file", toolset="file", schema=WRITE_FILE_SCHEMA, handler=_handle_write_file, check_fn=_check_file_reqs)
registry.register(name="patch", toolset="file", schema=PATCH_SCHEMA, handler=_handle_patch, check_fn=_check_file_reqs)
registry.register(name="search_files", toolset="file", schema=SEARCH_FILES_SCHEMA, handler=_handle_search_files, check_fn=_check_file_reqs)
