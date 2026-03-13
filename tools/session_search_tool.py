#!/usr/bin/env python3
"""
Session Search Tool - Recuperación de Conversación a Largo Plazo

Busca transcripciones de sesiones pasadas en SQLite vía FTS5, luego resume las
sesiones principales coincidentes usando un modelo barato/rápido (mismo patrón que web_extract).
Devuelve resúmenes enfocados de conversaciones pasadas en lugar de transcripciones sin procesar,
manteniendo la ventana de contexto del modelo principal limpia.

Flujo:
  1. La búsqueda FTS5 encuentra mensajes coincidentes clasificados por relevancia
  2. Agrupa por sesión, toma las N sesiones únicas principales (predeterminado 3)
  3. Carga la conversación de cada sesión, trunca a ~100k caracteres centrado en coincidencias
  4. Envía a Gemini Flash con un prompt de sumarización enfocado
  5. Devuelve resúmenes por sesión con metadatos
"""

import asyncio
import concurrent.futures
import json
import os
import logging
from typing import Dict, Any, List, Optional, Union

from agent.auxiliary_client import async_call_llm
MAX_SESSION_CHARS = 100_000
MAX_SUMMARY_TOKENS = 10000


def _format_timestamp(ts: Union[int, float, str, None]) -> str:
    """Convierte una marca de tiempo Unix (float/int) o cadena ISO a una fecha legible para humanos.

    Devuelve "unknown" para None, str(ts) si la conversión falla.
    """
    if ts is None:
        return "unknown"
    try:
        if isinstance(ts, (int, float)):
            from datetime import datetime
            dt = datetime.fromtimestamp(ts)
            return dt.strftime("%B %d, %Y at %I:%M %p")
        if isinstance(ts, str):
            if ts.replace(".", "").replace("-", "").isdigit():
                from datetime import datetime
                dt = datetime.fromtimestamp(float(ts))
                return dt.strftime("%B %d, %Y at %I:%M %p")
            return ts
    except (ValueError, OSError, OverflowError) as e:
        # Registra errores específicos para depuración mientras maneja elegantemente casos extremos
        logging.debug("Falló al formatear marca de tiempo %s: %s", ts, e)
    except Exception as e:
        logging.debug("Error inesperado formateando marca de tiempo %s: %s", ts, e)
    return str(ts)


def _format_conversation(messages: List[Dict[str, Any]]) -> str:
    """Formatea mensajes de sesión en una transcripción legible para sumarización."""
    parts = []
    for msg in messages:
        role = msg.get("role", "unknown").upper()
        content = msg.get("content") or ""
        tool_name = msg.get("tool_name")

        if role == "TOOL" and tool_name:
            # Trunca salidas largas de herramientas
            if len(content) > 500:
                content = content[:250] + "\n...[truncado]...\n" + content[-250:]
            parts.append(f"[TOOL:{tool_name}]: {content}")
        elif role == "ASSISTANT":
            # Incluye nombres de llamadas de herramienta si están presentes
            tool_calls = msg.get("tool_calls")
            if tool_calls and isinstance(tool_calls, list):
                tc_names = []
                for tc in tool_calls:
                    if isinstance(tc, dict):
                        name = tc.get("name") or tc.get("function", {}).get("name", "?")
                        tc_names.append(name)
                if tc_names:
                    parts.append(f"[ASSISTANT]: [Llamadas: {', '.join(tc_names)}]")
                if content:
                    parts.append(f"[ASSISTANT]: {content}")
            else:
                parts.append(f"[ASSISTANT]: {content}")
        else:
            parts.append(f"[{role}]: {content}")

    return "\n\n".join(parts)


def _truncate_around_matches(
    full_text: str, query: str, max_chars: int = MAX_SESSION_CHARS
) -> str:
    """
    Trunca una transcripción de conversación a max_chars, centrada alrededor
    de donde aparecen los términos de consulta. Mantiene contenido cerca de coincidencias, recorta los bordes.
    """
    if len(full_text) <= max_chars:
        return full_text

    # Encuentra la primera ocurrencia de cualquier término de consulta
    query_terms = query.lower().split()
    text_lower = full_text.lower()
    first_match = len(full_text)
    for term in query_terms:
        pos = text_lower.find(term)
        if pos != -1 and pos < first_match:
            first_match = pos

    if first_match == len(full_text):
        # No se encontró coincidencia, toma desde el inicio
        first_match = 0

    # Centra la ventana alrededor de la primera coincidencia
    half = max_chars // 2
    start = max(0, first_match - half)
    end = min(len(full_text), start + max_chars)
    if end - start < max_chars:
        start = max(0, end - max_chars)

    truncated = full_text[start:end]
    prefix = "...[conversación anterior truncada]...\n\n" if start > 0 else ""
    suffix = "\n\n...[conversación posterior truncada]..." if end < len(full_text) else ""
    return prefix + truncated + suffix


async def _summarize_session(
    conversation_text: str, query: str, session_meta: Dict[str, Any]
) -> Optional[str]:
    """Resume una conversación de sesión única enfocada en la consulta de búsqueda."""
    system_prompt = (
        "Estás revisando una transcripción de una conversación pasada para ayudar a recordar lo que sucedió. "
        "Resume la conversación con enfoque en el tema de búsqueda. Incluye:\n"
        "1. Lo que el usuario preguntó o quería lograr\n"
        "2. Qué acciones se tomaron y cuáles fueron los resultados\n"
        "3. Decisiones clave, soluciones encontradas o conclusiones alcanzadas\n"
        "4. Cualquier comando específico, archivo, URL o detalle técnico que fue importante\n"
        "5. Cualquier cosa que quedó sin resolver o fue notable\n\n"
        "Sé exhaustivo pero conciso. Preserva detalles específicos (comandos, rutas, mensajes de error) "
        "que serían útiles para recordar. Escribe en tiempo pasado como un resumen factual."
    )

    source = session_meta.get("source", "unknown")
    started = _format_timestamp(session_meta.get("started_at"))

    user_prompt = (
        f"Tema de búsqueda: {query}\n"
        f"Fuente de sesión: {source}\n"
        f"Fecha de sesión: {started}\n\n"
        f"TRANSCRIPCIÓN DE CONVERSACIÓN:\n{conversation_text}\n\n"
        f"Resume esta conversación con enfoque en: {query}"
    )

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await async_call_llm(
                task="session_search",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=MAX_SUMMARY_TOKENS,
            )
            return response.choices[0].message.content.strip()
        except RuntimeError:
            logging.warning("No hay modelo auxiliar disponible para sumarización de sesión")
            return None
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(1 * (attempt + 1))
            else:
                logging.warning(f"La sumarización de sesión falló después de {max_retries} intentos: {e}")
                return None


def session_search(
    query: str,
    role_filter: str = None,
    limit: int = 3,
    db=None,
    current_session_id: str = None,
) -> str:
    """
    Busca sesiones pasadas y devuelve resúmenes enfocados de conversaciones coincidentes.

    Usa FTS5 para encontrar coincidencias, luego resume las sesiones principales con Gemini Flash.
    La sesión actual se excluye de los resultados ya que el agente ya tiene ese contexto.
    """
    if db is None:
        return json.dumps({"success": False, "error": "Base de datos de sesión no disponible."}, ensure_ascii=False)

    if not query or not query.strip():
        return json.dumps({"success": False, "error": "La consulta no puede estar vacía."}, ensure_ascii=False)

    query = query.strip()
    limit = min(limit, 5)  # Limita a 5 sesiones para evitar demasiadas llamadas LLM

    try:
        # Analiza filtro de rol
        role_list = None
        if role_filter and role_filter.strip():
            role_list = [r.strip() for r in role_filter.split(",") if r.strip()]

        # Búsqueda FTS5 -- obtiene coincidencias clasificadas por relevancia
        raw_results = db.search_messages(
            query=query,
            role_filter=role_list,
            limit=50,  # Obtén más coincidencias para encontrar sesiones únicas
            offset=0,
        )

        if not raw_results:
            return json.dumps({
                "success": True,
                "query": query,
                "results": [],
                "count": 0,
                "message": "No se encontraron sesiones coincidentes.",
            }, ensure_ascii=False)

        # Resuelve sesiones secundarias a su padre — la delegación almacena contenido detallado
        # en sesiones secundarias, pero la conversación del usuario es la principal.
        def _resolve_to_parent(session_id: str) -> str:
            """Camina la cadena de delegación para encontrar el ID de sesión padre raíz."""
            visited = set()
            sid = session_id
            while sid and sid not in visited:
                visited.add(sid)
                try:
                    session = db.get_session(sid)
                    if not session:
                        break
                    parent = session.get("parent_session_id")
                    if parent:
                        sid = parent
                    else:
                        break
                except Exception as e:
                    logging.debug("Error resolving parent for session %s: %s", sid, e)
                    break
            return sid

        # Group by resolved (parent) session_id, dedup, skip current session
        seen_sessions = {}
        for result in raw_results:
            raw_sid = result["session_id"]
            resolved_sid = _resolve_to_parent(raw_sid)
            # Omite la sesión actual — el agente ya tiene ese contexto
            if current_session_id and resolved_sid == current_session_id:
                continue
            if current_session_id and raw_sid == current_session_id:
                continue
            if resolved_sid not in seen_sessions:
                result = dict(result)
                result["session_id"] = resolved_sid
                seen_sessions[resolved_sid] = result
            if len(seen_sessions) >= limit:
                break

        # Prepara todas las sesiones para sumarización paralela
        tasks = []
        for session_id, match_info in seen_sessions.items():
            try:
                messages = db.get_messages_as_conversation(session_id)
                if not messages:
                    continue
                session_meta = db.get_session(session_id) or {}
                conversation_text = _format_conversation(messages)
                conversation_text = _truncate_around_matches(conversation_text, query)
                tasks.append((session_id, match_info, conversation_text, session_meta))
            except Exception as e:
                logging.warning(f"Falló al preparar sesión {session_id}: {e}")

        # Resumir todas las sesiones en paralelo
        async def _summarize_all() -> List[Union[str, Exception]]:
            """Resume todas las sesiones en paralelo."""
            coros = [
                _summarize_session(text, query, meta)
                for _, _, text, meta in tasks
            ]
            return await asyncio.gather(*coros, return_exceptions=True)

        try:
            asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                results = pool.submit(lambda: asyncio.run(_summarize_all())).result(timeout=60)
        except RuntimeError:
            # Sin bucle de eventos en ejecución, crear uno nuevo
            results = asyncio.run(_summarize_all())
        except concurrent.futures.TimeoutError:
            logging.warning("La sumarización de sesión agotó el tiempo después de 60 segundos")
            return json.dumps({
                "success": False,
                "error": "La sumarización de sesión agotó el tiempo. Intenta una consulta más específica o reduce el límite.",
            }, ensure_ascii=False)

        summaries = []
        for (session_id, match_info, _, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                logging.warning(f"Failed to summarize session {session_id}: {result}")
                continue
            if result:
                summaries.append({
                    "session_id": session_id,
                    "when": _format_timestamp(match_info.get("session_started")),
                    "source": match_info.get("source", "unknown"),
                    "model": match_info.get("model"),
                    "summary": result,
                })

        return json.dumps({
            "success": True,
            "query": query,
            "results": summaries,
            "count": len(summaries),
            "sessions_searched": len(seen_sessions),
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"success": False, "error": f"La búsqueda falló: {str(e)}"}, ensure_ascii=False)


def check_session_search_requirements() -> bool:
    """Requiere base de datos de estado SQLite y un modelo de texto auxiliar."""
    try:
        from hermes_state import DEFAULT_DB_PATH
        return DEFAULT_DB_PATH.parent.exists()
    except ImportError:
        return False


SESSION_SEARCH_SCHEMA = {
    "name": "session_search",
    "description": (
        "Busca tu memoria a largo plazo de conversaciones pasadas. Esta es tu memoria — "
        "cada sesión pasada es búsqueda, y esta herramienta resume lo que sucedió.\n\n"
        "USA ESTO PROACTIVAMENTE cuando:\n"
        "- El usuario dice 'hicimos esto antes', 'recuerdas cuando', 'última vez', 'como mencioné'\n"
        "- El usuario pregunta sobre un tema en el que trabajaste antes pero no está en contexto actual\n"
        "- El usuario hace referencia a un proyecto, persona o concepto que parece familiar pero no está en memoria\n"
        "- Quieres verificar si resolviste un problema similar antes\n"
        "- El usuario pregunta '¿qué hicimos sobre X?' o '¿cómo arreglamos Y?'\n\n"
        "No dudes en buscar — es rápido y barato. Mejor buscar y confirmar "
        "que adivinar o pedir al usuario que se repita.\n\n"
        "Sintaxis de búsqueda: palabras clave unidas con OR para recuerdo amplio (elevenlabs OR baseten OR funding), "
        "frases para coincidencia exacta (\"docker networking\"), booleano (python NOT java), prefijo (deploy*). "
        "IMPORTANTE: Usa OR entre palabras clave para mejores resultados — FTS5 por defecto usa AND que pierde "
        "sesiones que solo mencionan algunos términos. Si una consulta OR amplia no devuelve nada, intenta búsquedas "
        "individuales de palabras clave en paralelo. Devuelve resúmenes de las sesiones más relevantes."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Consulta de búsqueda — palabras clave, frases o expresiones booleanas para encontrar en sesiones pasadas.",
            },
            "role_filter": {
                "type": "string",
                "description": "Opcional: busca solo mensajes de roles específicos (separados por comas). P. ej. 'usuario,asistente' para omitir salidas de herramientas.",
            },
            "limit": {
                "type": "integer",
                "description": "Máximo de sesiones a resumir (predeterminado: 3, máximo: 5).",
                "default": 3,
            },
        },
        "required": ["query"],
    },
}


# --- Registry ---
from tools.registry import registry

registry.register(
    name="session_search",
    toolset="session_search",
    schema=SESSION_SEARCH_SCHEMA,
    handler=lambda args, **kw: session_search(
        query=args.get("query", ""),
        role_filter=args.get("role_filter"),
        limit=args.get("limit", 3),
        db=kw.get("db"),
        current_session_id=kw.get("current_session_id")),
    check_fn=check_session_search_requirements,
)
