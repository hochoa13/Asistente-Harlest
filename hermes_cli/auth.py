"""Sistema de autenticación multi-proveedor para Hermes Agent.

Proporciona flujos OAuth de código de dispositivo (Nous Portal, futuro: OpenAI Codex) y
proveedores tradicionales de clave de API (OpenRouter, puntos finales personalizados). El estado
de autenticación se persiste en ~/.hermes/auth.json con bloqueos entre procesos.

Arquitectura:
- El registro ProviderConfig define proveedores OAuth conocidos
- El almacén de autenticación (auth.json) mantiene el estado de credenciales por proveedor
- resolve_provider() elige el proveedor activo mediante cadena de prioridad
- resolve_*_runtime_credentials() maneja actualización de tokens y generación de claves
- logout_command() es el punto de entrada CLI para borrar autenticación
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import stat
import base64
import hashlib
import subprocess
import threading
import time
import uuid
import webbrowser
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import yaml

from hermes_cli.config import get_hermes_home, get_config_path
from hermes_constants import OPENROUTER_BASE_URL

logger = logging.getLogger(__name__)

try:
    import fcntl
except Exception:
    fcntl = None
try:
    import msvcrt
except Exception:
    msvcrt = None

# =============================================================================
# Constantes
# =============================================================================

AUTH_STORE_VERSION = 1
AUTH_LOCK_TIMEOUT_SECONDS = 15.0

# Valores predeterminados de Nous Portal
DEFAULT_NOUS_PORTAL_URL = "https://portal.nousresearch.com"
DEFAULT_NOUS_INFERENCE_URL = "https://inference-api.nousresearch.com/v1"
DEFAULT_NOUS_CLIENT_ID = "hermes-cli"
DEFAULT_NOUS_SCOPE = "inference:mint_agent_key"
DEFAULT_AGENT_KEY_MIN_TTL_SECONDS = 30 * 60  # 30 minutos
ACCESS_TOKEN_REFRESH_SKEW_SECONDS = 120       # actualizar 2 min antes de vencimiento
DEVICE_AUTH_POLL_INTERVAL_CAP_SECONDS = 1     # encuestar como máximo cada 1s
DEFAULT_CODEX_BASE_URL = "https://chatgpt.com/backend-api/codex"
CODEX_OAUTH_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
CODEX_OAUTH_TOKEN_URL = "https://auth.openai.com/oauth/token"
CODEX_ACCESS_TOKEN_REFRESH_SKEW_SECONDS = 120


# =============================================================================
# Registro de Proveedores
# =============================================================================

@dataclass
class ProviderConfig:
    """Describe un proveedor de inferencia conocido."""
    id: str
    name: str
    auth_type: str  # "oauth_device_code", "oauth_external", o "api_key"
    portal_base_url: str = ""
    inference_base_url: str = ""
    client_id: str = ""
    scope: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)
    # Para proveedores con clave de API: variables de entorno a verificar (orden prioritario)
    api_key_env_vars: tuple = ()
    # Variable de entorno opcional para anulación de URL base
    base_url_env_var: str = ""


PROVIDER_REGISTRY: Dict[str, ProviderConfig] = {
    "nous": ProviderConfig(
        id="nous",
        name="Nous Portal",
        auth_type="oauth_device_code",
        portal_base_url=DEFAULT_NOUS_PORTAL_URL,
        inference_base_url=DEFAULT_NOUS_INFERENCE_URL,
        client_id=DEFAULT_NOUS_CLIENT_ID,
        scope=DEFAULT_NOUS_SCOPE,
    ),
    "openai-codex": ProviderConfig(
        id="openai-codex",
        name="OpenAI Codex",
        auth_type="oauth_external",
        inference_base_url=DEFAULT_CODEX_BASE_URL,
    ),
    "zai": ProviderConfig(
        id="zai",
        name="Z.AI / GLM",
        auth_type="api_key",
        inference_base_url="https://api.z.ai/api/paas/v4",
        api_key_env_vars=("GLM_API_KEY", "ZAI_API_KEY", "Z_AI_API_KEY"),
        base_url_env_var="GLM_BASE_URL",
    ),
    "kimi-coding": ProviderConfig(
        id="kimi-coding",
        name="Kimi / Moonshot",
        auth_type="api_key",
        inference_base_url="https://api.moonshot.ai/v1",
        api_key_env_vars=("KIMI_API_KEY",),
        base_url_env_var="KIMI_BASE_URL",
    ),
    "minimax": ProviderConfig(
        id="minimax",
        name="MiniMax",
        auth_type="api_key",
        inference_base_url="https://api.minimax.io/v1",
        api_key_env_vars=("MINIMAX_API_KEY",),
        base_url_env_var="MINIMAX_BASE_URL",
    ),
    "minimax-cn": ProviderConfig(
        id="minimax-cn",
        name="MiniMax (China)",
        auth_type="api_key",
        inference_base_url="https://api.minimaxi.com/v1",
        api_key_env_vars=("MINIMAX_CN_API_KEY",),
        base_url_env_var="MINIMAX_CN_BASE_URL",
    ),
}


# =============================================================================
# Detección de Punto Final de Kimi Code
# =============================================================================

# Kimi Code (platform.kimi.ai) emite claves con prefijo "sk-kimi-" que solo funcionan
# en api.kimi.com/coding/v1.  Las claves heredadas de platform.moonshot.ai funcionan en
# api.moonshot.ai/v1 (predeterminado).  Detectar automáticamente cuando el usuario no ha
# configurado KIMI_BASE_URL explícitamente.
KIMI_CODE_BASE_URL = "https://api.kimi.com/coding/v1"


def _resolve_kimi_base_url(api_key: str, default_url: str, env_override: str) -> str:
    """Devuelve la URL de base de Kimi correcta según el prefijo de la clave de API.

    Si el usuario ha configurado explícitamente KIMI_BASE_URL, eso siempre gana.
    De lo contrario, las claves con prefijo sk-kimi- se enrutan a api.kimi.com/coding/v1.
    """
    if env_override:
        return env_override
    if api_key.startswith("sk-kimi-"):
        return KIMI_CODE_BASE_URL
    return default_url


# =============================================================================
# Detección de Punto Final de Z.AI
# =============================================================================

# Z.AI tiene facturación separada para planes generales vs de codificación, y puntos finales
# globales vs de China.  Una clave que funciona en uno puede devolver "Saldo insuficiente" en
# otro.  Sondeamos en tiempo de configuración y almacenamos el punto final que funciona.

ZAI_ENDPOINTS = [
    # (id, base_url, default_model, label)
    ("global",        "https://api.z.ai/api/paas/v4",        "glm-5",   "Global"),
    ("cn",            "https://open.bigmodel.cn/api/paas/v4", "glm-5",   "China"),
    ("coding-global", "https://api.z.ai/api/coding/paas/v4",  "glm-4.7", "Global (Coding Plan)"),
    ("coding-cn",     "https://open.bigmodel.cn/api/coding/paas/v4", "glm-4.7", "China (Coding Plan)"),
]


def detect_zai_endpoint(api_key: str, timeout: float = 8.0) -> Optional[Dict[str, str]]:
    """Sondea puntos finales de z.ai para encontrar uno que acepte esta clave de API.

    Devuelve {"id": ..., "base_url": ..., "model": ..., "label": ...} para el
    primer punto final funcional, o None si todos fallan.
    """
    for ep_id, base_url, model, label in ZAI_ENDPOINTS:
        try:
            resp = httpx.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "stream": False,
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "ping"}],
                },
                timeout=timeout,
            )
            if resp.status_code == 200:
                logger.debug("Sondeo de punto final Z.AI: %s (%s) OK", ep_id, base_url)
                return {
                    "id": ep_id,
                    "base_url": base_url,
                    "model": model,
                    "label": label,
                }
            logger.debug("Sondeo de punto final Z.AI: %s devuelto %s", ep_id, resp.status_code)
        except Exception as exc:
            logger.debug("Sondeo de punto final Z.AI: %s falló: %s", ep_id, exc)
    return None


# =============================================================================
# Tipos de Error
# =============================================================================

class AuthError(RuntimeError):
    """Error de autenticación estructurado con pistas de mapeo UX."""

    def __init__(
        self,
        message: str,
        *,
        provider: str = "",
        code: Optional[str] = None,
        relogin_required: bool = False,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.code = code
        self.relogin_required = relogin_required


def format_auth_error(error: Exception) -> str:
    """Mapea fallos de autenticación a una guía concisa orientada al usuario."""
    if not isinstance(error, AuthError):
        return str(error)

    if error.relogin_required:
        return f"{error} Ejecuta `hermes model` para autenticarse de nuevo."

    if error.code == "subscription_required":
        raise AuthError(
            "No se encontro suscripcion activa pagada en Nous Portal. "
            "Por favor compra/activa una suscripcion, luego reinenta."
        )

    if error.code == "insufficient_credits":
        return (
            "Los creditos de suscripcion estan agotados. "
            "Recarga/renueva creditos en Nous Portal, luego reinenta."
        )

    if error.code == "temporarily_unavailable":
        return f"{error} Por favor reintenta en unos segundos."

    return str(error)


def _token_fingerprint(token: Any) -> Optional[str]:
    """Devuelve un huella digital hash corto para telemetría sin filtrar bytes de token."""
    if not isinstance(token, str):
        return None
    cleaned = token.strip()
    if not cleaned:
        return None
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()[:12]


def _oauth_trace_enabled() -> bool:
    raw = os.getenv("HERMES_OAUTH_TRACE", "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _oauth_trace(event: str, *, sequence_id: Optional[str] = None, **fields: Any) -> None:
    """Registra detalles del flujo OAuth cuando está habilitado HERMES_OAUTH_TRACE."""
    if not _oauth_trace_enabled():
        return
    payload: Dict[str, Any] = {"event": event}
    if sequence_id:
        payload["sequence_id"] = sequence_id
    payload.update(fields)
    logger.info("oauth_trace %s", json.dumps(payload, sort_keys=True, ensure_ascii=False))


# =============================================================================
# Almacén de Autenticación — capa de persistencia para ~/.hermes/auth.json
# =====================================================================================

def _auth_file_path() -> Path:
    return get_hermes_home() / "auth.json"


def _auth_lock_path() -> Path:
    return _auth_file_path().with_suffix(".lock")


_auth_lock_holder = threading.local()

@contextmanager
def _auth_store_lock(timeout_seconds: float = AUTH_LOCK_TIMEOUT_SECONDS):
    """Bloqueo de asesoría mutuo entre procesos para lecturas+escrituras de auth.json. Reentrante."""
    # Reentrante: si este hilo ya mantiene el bloqueo, solo cede.
    if getattr(_auth_lock_holder, "depth", 0) > 0:
        _auth_lock_holder.depth += 1
        try:
            yield
        finally:
            _auth_lock_holder.depth -= 1
        return

    lock_path = _auth_lock_path()
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    if fcntl is None and msvcrt is None:
        _auth_lock_holder.depth = 1
        try:
            yield
        finally:
            _auth_lock_holder.depth = 0
        return

    # En Windows, msvcrt.locking necesita el archivo con contenido y el
    # puntero del archivo en la posición 0.  Asegurar que el archivo de bloqueo tenga al menos 1 byte.
    if msvcrt and (not lock_path.exists() or lock_path.stat().st_size == 0):
        lock_path.write_text(" ", encoding="utf-8")

    with lock_path.open("r+" if msvcrt else "a+") as lock_file:
        deadline = time.time() + max(1.0, timeout_seconds)
        while True:
            try:
                if fcntl:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                else:
                    lock_file.seek(0)
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except (BlockingIOError, OSError, PermissionError):
                if time.time() >= deadline:
                    raise TimeoutError("Expiró tiempo esperando por bloqueo del almacén de autenticación")
                time.sleep(0.05)

        _auth_lock_holder.depth = 1
        try:
            yield
        finally:
            _auth_lock_holder.depth = 0
            if fcntl:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            elif msvcrt:
                try:
                    lock_file.seek(0)
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                except (OSError, IOError):
                    pass


def _load_auth_store(auth_file: Optional[Path] = None) -> Dict[str, Any]:
    auth_file = auth_file or _auth_file_path()
    if not auth_file.exists():
        return {"version": AUTH_STORE_VERSION, "providers": {}}

    try:
        raw = json.loads(auth_file.read_text())
    except Exception:
        return {"version": AUTH_STORE_VERSION, "providers": {}}

    if isinstance(raw, dict) and isinstance(raw.get("providers"), dict):
        return raw

    # Migrate from PR's "systems" format if present
    if isinstance(raw, dict) and isinstance(raw.get("systems"), dict):
        systems = raw["systems"]
        providers = {}
        if "nous_portal" in systems:
            providers["nous"] = systems["nous_portal"]
        return {"version": AUTH_STORE_VERSION, "providers": providers,
                "active_provider": "nous" if providers else None}

    return {"version": AUTH_STORE_VERSION, "providers": {}}


def _save_auth_store(auth_store: Dict[str, Any]) -> Path:
    auth_file = _auth_file_path()
    auth_file.parent.mkdir(parents=True, exist_ok=True)
    auth_store["version"] = AUTH_STORE_VERSION
    auth_store["updated_at"] = datetime.now(timezone.utc).isoformat()
    payload = json.dumps(auth_store, indent=2) + "\n"
    tmp_path = auth_file.with_name(f"{auth_file.name}.tmp.{os.getpid()}.{uuid.uuid4().hex}")
    try:
        with tmp_path.open("w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, auth_file)
        try:
            dir_fd = os.open(str(auth_file.parent), os.O_RDONLY)
        except OSError:
            dir_fd = None
        if dir_fd is not None:
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
    finally:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass
    # Restrict file permissions to owner only
    try:
        auth_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
    return auth_file


def _load_provider_state(auth_store: Dict[str, Any], provider_id: str) -> Optional[Dict[str, Any]]:
    """Devuelve el estado de autenticación persistido para un proveedor, o None."""
    providers = auth_store.get("providers")
    if not isinstance(providers, dict):
        return None
    state = providers.get(provider_id)
    return dict(state) if isinstance(state, dict) else None


def _save_provider_state(auth_store: Dict[str, Any], provider_id: str, state: Dict[str, Any]) -> None:
    """Guarda el estado de autenticación para un proveedor en el almacén."""
    providers = auth_store.setdefault("providers", {})
    if not isinstance(providers, dict):
        auth_store["providers"] = {}
        providers = auth_store["providers"]
    providers[provider_id] = state
    auth_store["active_provider"] = provider_id


def get_provider_auth_state(provider_id: str) -> Optional[Dict[str, Any]]:
    """Devuelve el estado de autenticación persistido para un proveedor, o None."""
    auth_store = _load_auth_store()
    return _load_provider_state(auth_store, provider_id)


def get_active_provider() -> Optional[str]:
    """Devuelve el ID del proveedor actualmente activo desde el almacén de autenticación."""
    auth_store = _load_auth_store()
    return auth_store.get("active_provider")


def clear_provider_auth(provider_id: Optional[str] = None) -> bool:
    """
    Borra el estado de autenticación para un proveedor. Usado por `hermes logout`.
    Si provider_id es None, borra el proveedor activo.
    Devuelve True si algo fue borrado.
    """
    with _auth_store_lock():
        auth_store = _load_auth_store()
        target = provider_id or auth_store.get("active_provider")
        if not target:
            return False

        providers = auth_store.get("providers", {})
        if target not in providers:
            return False

        del providers[target]
        if auth_store.get("active_provider") == target:
            auth_store["active_provider"] = None
        _save_auth_store(auth_store)
    return True


def deactivate_provider() -> None:
    """
    Borra active_provider en auth.json sin eliminar credenciales.
    Usado cuando el usuario cambia a un proveedor no-OAuth (OpenRouter, personalizado)
    para que la resolución automática no siga eligiendo el proveedor OAuth.
    """
    with _auth_store_lock():
        auth_store = _load_auth_store()
        auth_store["active_provider"] = None
        _save_auth_store(auth_store)


# =============================================================================
# Provider Resolution — picks which provider to use
# =============================================================================

def resolve_provider(
    requested: Optional[str] = None,
    *,
    explicit_api_key: Optional[str] = None,
    explicit_base_url: Optional[str] = None,
) -> str:
    """
    Determina cuál proveedor de inferencia usar.

    Prioridad (cuando requested="auto" o None):
    1. active_provider en auth.json con credenciales válidas
    2. CLI explícito api_key/base_url -> "openrouter"
    3. Variables de entorno OPENAI_API_KEY o OPENROUTER_API_KEY -> "openrouter"
    4. Claves de API específicas del proveedor (GLM, Kimi, MiniMax) -> ese proveedor
    5. Retroceso: "openrouter"
    """
    normalized = (requested or "auto").strip().lower()

    # Normalizar alias de proveedor
    _PROVIDER_ALIASES = {
        "glm": "zai", "z-ai": "zai", "z.ai": "zai", "zhipu": "zai",
        "kimi": "kimi-coding", "moonshot": "kimi-coding",
        "minimax-china": "minimax-cn", "minimax_cn": "minimax-cn",
    }
    normalized = _PROVIDER_ALIASES.get(normalized, normalized)

    if normalized in {"openrouter", "custom"}:
        return "openrouter"
    if normalized in PROVIDER_REGISTRY:
        return normalized
    if normalized != "auto":
        raise AuthError(
            f"Unknown provider '{normalized}'.",
            code="invalid_provider",
        )

    # Las credenciales CLI uno-a-uno explícitas siempre significan openrouter/customizado
    if explicit_api_key or explicit_base_url:
        return "openrouter"

    # Buscar en almacén de autenticación un proveedor OAuth activo
    try:
        auth_store = _load_auth_store()
        active = auth_store.get("active_provider")
        if active and active in PROVIDER_REGISTRY:
            status = get_auth_status(active)
            if status.get("logged_in"):
                return active
    except Exception as e:
        logger.debug("No se pudo detectar proveedor de autenticación activo: %s", e)

    if os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY"):
        return "openrouter"

    # Detectar automáticamente proveedores de clave de API comprobando sus variables de entorno
    for pid, pconfig in PROVIDER_REGISTRY.items():
        if pconfig.auth_type != "api_key":
            continue
        for env_var in pconfig.api_key_env_vars:
            if os.getenv(env_var, "").strip():
                return pid

    return "openrouter"


# =============================================================================
# Ayudantes de Marca de Tiempo / TTL
# =====================================================================================

def _parse_iso_timestamp(value: Any) -> Optional[float]:
    """Analiza una marca de tiempo ISO a un valor de época de Unix, o None."""
    if not isinstance(value, str) or not value:
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


def _is_expiring(expires_at_iso: Any, skew_seconds: int) -> bool:
    """Comprueba si una marca de tiempo de vencimiento está dentro del rango de sesgo."""
    expires_epoch = _parse_iso_timestamp(expires_at_iso)
    if expires_epoch is None:
        return True
    return expires_epoch <= (time.time() + skew_seconds)


def _coerce_ttl_seconds(expires_in: Any) -> int:
    """Convierte expires_in a segundos de TTL de entero, o 0 si no es válido."""
    try:
        ttl = int(expires_in)
    except Exception:
        ttl = 0
    return max(0, ttl)


def _optional_base_url(value: Any) -> Optional[str]:
    """Valida y limpia una URL base, devolviendo None si está vacía o inválida."""
    if not isinstance(value, str):
        return None
    cleaned = value.strip().rstrip("/")
    return cleaned if cleaned else None


def _decode_jwt_claims(token: Any) -> Dict[str, Any]:
    """Decodifica las primeras partes de un token JWT y devuelve los reclamos como dict."""
    if not isinstance(token, str) or token.count(".") != 2:
        return {}
    payload = token.split(".")[1]
    payload += "=" * ((4 - len(payload) % 4) % 4)
    try:
        raw = base64.urlsafe_b64decode(payload.encode("utf-8"))
        claims = json.loads(raw.decode("utf-8"))
    except Exception:
        return {}
    return claims if isinstance(claims, dict) else {}


def _codex_access_token_is_expiring(access_token: Any, skew_seconds: int) -> bool:
    """Decodifica JWT de Codex y comprueba si está venciendo."""
    claims = _decode_jwt_claims(access_token)
    exp = claims.get("exp")
    if not isinstance(exp, (int, float)):
        return False
    return float(exp) <= (time.time() + max(0, int(skew_seconds)))


# =============================================================================
# Detección de Sesión SSH / remota
# =============================================================================

def _is_remote_session() -> bool:
    """Detecta si se está ejecutando en una sesión SSH donde webbrowser.open() no funcionará."""
    return bool(os.getenv("SSH_CLIENT") or os.getenv("SSH_TTY"))


# =============================================================================
# Autenticación de OpenAI Codex — tokens almacenados en ~/.hermes/auth.json (no ~/.codex/)
#
# Hermes mantiene su propia sesión OAuth de Codex separada de la CLI de Codex
# y la extensión de VS Code. Esto previene conflictos de rotación de tokens de actualización
# donde la actualización de una aplicación invalida la sesión de otra.
# =====================================================================================

def _read_codex_tokens(*, _lock: bool = True) -> Dict[str, Any]:
    """Lee tokens OAuth de Codex del almacén de autenticación de Hermes (~/.hermes/auth.json).
    
    Devuelve dict con 'tokens' (access_token, refresh_token) y 'last_refresh'.
    Lanza AuthError si no hay tokens de Codex almacenados.
    """
    if _lock:
        with _auth_store_lock():
            auth_store = _load_auth_store()
    else:
        auth_store = _load_auth_store()
    state = _load_provider_state(auth_store, "openai-codex")
    if not state:
        raise AuthError(
            "No Codex credentials stored. Run `hermes login` to authenticate.",
            provider="openai-codex",
            code="codex_auth_missing",
            relogin_required=True,
        )
    tokens = state.get("tokens")
    if not isinstance(tokens, dict):
        raise AuthError(
            "El estado de autenticación de Codex no tiene tokens. Ejecuta `hermes login` para autenticarte de nuevo.",
            provider="openai-codex",
            code="codex_auth_invalid_shape",
            relogin_required=True,
        )
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    if not isinstance(access_token, str) or not access_token.strip():
        raise AuthError(
            "La autenticación de Codex no tiene access_token. Ejecuta `hermes login` para autenticarte de nuevo.",
            provider="openai-codex",
            code="codex_auth_missing_access_token",
            relogin_required=True,
        )
    if not isinstance(refresh_token, str) or not refresh_token.strip():
        raise AuthError(
            "Codex auth is missing refresh_token. Run `hermes login` to re-authenticate.",
            provider="openai-codex",
            code="codex_auth_missing_refresh_token",
            relogin_required=True,
        )
    return {
        "tokens": tokens,
        "last_refresh": state.get("last_refresh"),
    }


def _save_codex_tokens(tokens: Dict[str, str], last_refresh: str = None) -> None:
    """Guarda tokens OAuth de Codex en el almacén de autenticación de Hermes (~/.hermes/auth.json)."""
    if last_refresh is None:
        last_refresh = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with _auth_store_lock():
        auth_store = _load_auth_store()
        state = _load_provider_state(auth_store, "openai-codex") or {}
        state["tokens"] = tokens
        state["last_refresh"] = last_refresh
        state["auth_mode"] = "chatgpt"
        _save_provider_state(auth_store, "openai-codex", state)
        _save_auth_store(auth_store)


def _refresh_codex_auth_tokens(
    tokens: Dict[str, str],
    timeout_seconds: float,
) -> Dict[str, str]:
    """Actualiza el token de acceso de Codex usando el token de actualización.
    
    Guarda los nuevos tokens en el almacén de autenticación de Hermes automáticamente.
    """
    refresh_token = tokens.get("refresh_token")
    if not isinstance(refresh_token, str) or not refresh_token.strip():
        raise AuthError(
            "Codex auth is missing refresh_token. Run `hermes login` to re-authenticate.",
            provider="openai-codex",
            code="codex_auth_missing_refresh_token",
            relogin_required=True,
        )

    timeout = httpx.Timeout(max(5.0, float(timeout_seconds)))
    with httpx.Client(timeout=timeout, headers={"Accept": "application/json"}) as client:
        response = client.post(
            CODEX_OAUTH_TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": CODEX_OAUTH_CLIENT_ID,
            },
        )

    if response.status_code != 200:
        code = "codex_refresh_failed"
        message = f"Codex token refresh failed with status {response.status_code}."
        relogin_required = False
        try:
            err = response.json()
            if isinstance(err, dict):
                err_code = err.get("error")
                if isinstance(err_code, str) and err_code.strip():
                    code = err_code.strip()
                err_desc = err.get("error_description") or err.get("message")
                if isinstance(err_desc, str) and err_desc.strip():
                    message = f"Codex token refresh failed: {err_desc.strip()}"
        except Exception:
            pass
        if code in {"invalid_grant", "invalid_token", "invalid_request"}:
            relogin_required = True
        raise AuthError(
            message,
            provider="openai-codex",
            code=code,
            relogin_required=relogin_required,
        )

    try:
        refresh_payload = response.json()
    except Exception as exc:
        raise AuthError(
            "Codex token refresh returned invalid JSON.",
            provider="openai-codex",
            code="codex_refresh_invalid_json",
            relogin_required=True,
        ) from exc

    access_token = refresh_payload.get("access_token")
    if not isinstance(access_token, str) or not access_token.strip():
        raise AuthError(
            "Codex token refresh response was missing access_token.",
            provider="openai-codex",
            code="codex_refresh_missing_access_token",
            relogin_required=True,
        )

    updated_tokens = dict(tokens)
    updated_tokens["access_token"] = access_token.strip()
    next_refresh = refresh_payload.get("refresh_token")
    if isinstance(next_refresh, str) and next_refresh.strip():
        updated_tokens["refresh_token"] = next_refresh.strip()

    _save_codex_tokens(updated_tokens)
    return updated_tokens


def _import_codex_cli_tokens() -> Optional[Dict[str, str]]:
    """Intenta leer tokens de ~/.codex/auth.json (archivo compartido de CLI de Codex).
    
    Devuelve dict de tokens si es válido, None de otro modo. NO escribe en el archivo compartido.
    """
    codex_home = os.getenv("CODEX_HOME", "").strip()
    if not codex_home:
        codex_home = str(Path.home() / ".codex")
    auth_path = Path(codex_home).expanduser() / "auth.json"
    if not auth_path.is_file():
        return None
    try:
        payload = json.loads(auth_path.read_text())
        tokens = payload.get("tokens")
        if not isinstance(tokens, dict):
            return None
        if not tokens.get("access_token") or not tokens.get("refresh_token"):
            return None
        return dict(tokens)
    except Exception:
        return None


def resolve_codex_runtime_credentials(
    *,
    force_refresh: bool = False,
    refresh_if_expiring: bool = True,
    refresh_skew_seconds: int = CODEX_ACCESS_TOKEN_REFRESH_SKEW_SECONDS,
) -> Dict[str, Any]:
    """Resolve runtime credentials from Hermes's own Codex token store."""
    try:
        data = _read_codex_tokens()
    except AuthError as orig_err:
        # Only attempt migration when there are NO tokens stored at all
        # (code == "codex_auth_missing"), not when tokens exist but are invalid.
        if orig_err.code != "codex_auth_missing":
            raise

        # Migration: user had Codex as active provider with old storage (~/.codex/).
        cli_tokens = _import_codex_cli_tokens()
        if cli_tokens:
            logger.info("Migrating Codex credentials from ~/.codex/ to Hermes auth store")
            print("⚠️  Migrating Codex credentials to Hermes's own auth store.")
            print("   This avoids conflicts with Codex CLI and VS Code.")
            print("   Run `hermes login` to create a fully independent session.\n")
            _save_codex_tokens(cli_tokens)
            data = _read_codex_tokens()
        else:
            raise
    tokens = dict(data["tokens"])
    access_token = str(tokens.get("access_token", "") or "").strip()
    refresh_timeout_seconds = float(os.getenv("HERMES_CODEX_REFRESH_TIMEOUT_SECONDS", "20"))

    should_refresh = bool(force_refresh)
    if (not should_refresh) and refresh_if_expiring:
        should_refresh = _codex_access_token_is_expiring(access_token, refresh_skew_seconds)
    if should_refresh:
        # Re-read under lock to avoid racing with other Hermes processes
        with _auth_store_lock(timeout_seconds=max(float(AUTH_LOCK_TIMEOUT_SECONDS), refresh_timeout_seconds + 5.0)):
            data = _read_codex_tokens(_lock=False)
            tokens = dict(data["tokens"])
            access_token = str(tokens.get("access_token", "") or "").strip()

            should_refresh = bool(force_refresh)
            if (not should_refresh) and refresh_if_expiring:
                should_refresh = _codex_access_token_is_expiring(access_token, refresh_skew_seconds)

            if should_refresh:
                tokens = _refresh_codex_auth_tokens(tokens, refresh_timeout_seconds)
                access_token = str(tokens.get("access_token", "") or "").strip()

    base_url = (
        os.getenv("HERMES_CODEX_BASE_URL", "").strip().rstrip("/")
        or DEFAULT_CODEX_BASE_URL
    )

    return {
        "provider": "openai-codex",
        "base_url": base_url,
        "api_key": access_token,
        "source": "hermes-auth-store",
        "last_refresh": data.get("last_refresh"),
        "auth_mode": "chatgpt",
    }


# =============================================================================
# Ayudante de verificacion TLS
# =============================================================================

def _resolve_verify(
    *,
    insecure: Optional[bool] = None,
    ca_bundle: Optional[str] = None,
    auth_state: Optional[Dict[str, Any]] = None,
) -> bool | str:
    """Resuelve el estado de verificacion TLS para solicitudes httpx."""
    tls_state = auth_state.get("tls") if isinstance(auth_state, dict) else {}
    tls_state = tls_state if isinstance(tls_state, dict) else {}

    effective_insecure = (
        bool(insecure) if insecure is not None
        else bool(tls_state.get("insecure", False))
    )
    effective_ca = (
        ca_bundle
        or tls_state.get("ca_bundle")
        or os.getenv("HERMES_CA_BUNDLE")
        or os.getenv("SSL_CERT_FILE")
    )

    if effective_insecure:
        return False
    if effective_ca:
        return str(effective_ca)
    return True


# =============================================================================
# OAuth Device Code Flow — generic, parameterized by provider
# =============================================================================

def _request_device_code(
    client: httpx.Client,
    portal_base_url: str,
    client_id: str,
    scope: Optional[str],
) -> Dict[str, Any]:
    """POST to the device code endpoint. Returns device_code, user_code, etc."""
    response = client.post(
        f"{portal_base_url}/api/oauth/device/code",
        data={
            "client_id": client_id,
            **({"scope": scope} if scope else {}),
        },
    )
    response.raise_for_status()
    data = response.json()

    campos_requeridos = [
        "device_code", "user_code", "verification_uri",
        "verification_uri_complete", "expires_in", "interval",
    ]
    faltantes = [f for f in campos_requeridos if f not in data]
    if faltantes:
        raise ValueError(f"Respuesta de codigo de dispositivo sin campos: {', '.join(faltantes)}")
    return data


def _poll_for_token(
    client: httpx.Client,
    portal_base_url: str,
    client_id: str,
    device_code: str,
    expires_in: int,
    poll_interval: int,
) -> Dict[str, Any]:
    """Prueba repetidamente el servidor de tokens con el codigo de dispositivo."""
    """Poll the token endpoint until the user approves or the code expires."""
    deadline = time.time() + max(1, expires_in)
    current_interval = max(1, min(poll_interval, DEVICE_AUTH_POLL_INTERVAL_CAP_SECONDS))

    while time.time() < deadline:
        response = client.post(
            f"{portal_base_url}/api/oauth/token",
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "client_id": client_id,
                "device_code": device_code,
            },
        )

        if response.status_code == 200:
            payload = response.json()
            if "access_token" not in payload:
                raise ValueError("Token response did not include access_token")
            return payload

        try:
            error_payload = response.json()
        except Exception:
            response.raise_for_status()
            raise RuntimeError("Token endpoint returned a non-JSON error response")

        error_code = error_payload.get("error", "")
        if error_code == "authorization_pending":
            time.sleep(current_interval)
            continue
        if error_code == "slow_down":
            current_interval = min(current_interval + 1, 30)
            time.sleep(current_interval)
            continue

        description = error_payload.get("error_description") or "Unknown authentication error"
        raise RuntimeError(f"{error_code}: {description}")

    raise TimeoutError("Timed out waiting for device authorization")


# =============================================================================
# Nous Portal — token refresh, agent key minting, model discovery
# =============================================================================

def _refresh_access_token(
    *,
    client: httpx.Client,
    portal_base_url: str,
    client_id: str,
    refresh_token: str,
) -> Dict[str, Any]:
    response = client.post(
        f"{portal_base_url}/api/oauth/token",
        data={
            "grant_type": "refresh_token",
            "client_id": client_id,
            "refresh_token": refresh_token,
        },
    )

    if response.status_code == 200:
        payload = response.json()
        if "access_token" not in payload:
            raise AuthError("Respuesta de actualización sin access_token",
                            provider="nous", code="invalid_token", relogin_required=True)
        return payload

    try:
        error_payload = response.json()
    except Exception as exc:
        raise AuthError("Intercambio de token de actualización falló",
                        provider="nous", relogin_required=True) from exc

    code = str(error_payload.get("error", "invalid_grant"))
    description = str(error_payload.get("error_description") or "Intercambio de token de actualización falló")
    relogin = code in {"invalid_grant", "invalid_token"}
    raise AuthError(description, provider="nous", code=code, relogin_required=relogin)


def _mint_agent_key(
    *,
    client: httpx.Client,
    portal_base_url: str,
    access_token: str,
    min_ttl_seconds: int,
) -> Dict[str, Any]:
    """Acuna (o reutiliza) una clave de API de inferencia de corta duracion."""
    response = client.post(
        f"{portal_base_url}/api/oauth/agent-key",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"min_ttl_seconds": max(60, int(min_ttl_seconds))},
    )

    if response.status_code == 200:
        payload = response.json()
        if "api_key" not in payload:
            raise AuthError("Respuesta de acuñación sin api_key",
                            provider="nous", code="server_error")
        return payload

    try:
        error_payload = response.json()
    except Exception as exc:
        raise AuthError("Solicitud de acuñación de clave de agente falló",
                        provider="nous", code="server_error") from exc

    code = str(error_payload.get("error", "server_error"))
    description = str(error_payload.get("error_description") or "Solicitud de acuñación de clave de agente falló")
    relogin = code in {"invalid_token", "invalid_grant"}
    raise AuthError(description, provider="nous", code=code, relogin_required=relogin)


def fetch_nous_models(
    *,
    inference_base_url: str,
    api_key: str,
    timeout_seconds: float = 15.0,
    verify: bool | str = True,
) -> List[str]:
    """Obtiene IDs de modelos disponibles de la API de inferencia de Nous."""
    timeout = httpx.Timeout(timeout_seconds)
    with httpx.Client(timeout=timeout, headers={"Accept": "application/json"}, verify=verify) as client:
        response = client.get(
            f"{inference_base_url.rstrip('/')}/models",
            headers={"Authorization": f"Bearer {api_key}"},
        )

    if response.status_code != 200:
        description = f"Solicitud /models falló con estado {response.status_code}"
        try:
            err = response.json()
            description = str(err.get("error_description") or err.get("error") or description)
        except Exception as e:
            logger.debug("No se pudo analizar JSON de respuesta de error: %s", e)
        raise AuthError(description, provider="nous", code="models_fetch_failed")

    payload = response.json()
    data = payload.get("data")
    if not isinstance(data, list):
        return []

    model_ids: List[str] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        model_id = item.get("id")
        if isinstance(model_id, str) and model_id.strip():
            mid = model_id.strip()
            # Skip Hermes models — they're not reliable for agentic tool-calling
            if "hermes" in mid.lower():
                continue
            model_ids.append(mid)

    # Sort: prefer opus > pro > haiku/flash > sonnet (sonnet is cheap/fast,
    # users who want the best model should see opus first).
    def _model_priority(mid: str) -> tuple:
        low = mid.lower()
        if "opus" in low:
            return (0, mid)
        if "pro" in low and "sonnet" not in low:
            return (1, mid)
        if "sonnet" in low:
            return (3, mid)
        return (2, mid)

    model_ids.sort(key=_model_priority)
    return list(dict.fromkeys(model_ids))


def _agent_key_is_usable(state: Dict[str, Any], min_ttl_seconds: int) -> bool:
    """Comprueba si una clave de agente almacenada es válida y no está venciendo."""
    key = state.get("agent_key")
    if not isinstance(key, str) or not key.strip():
        return False
    return not _is_expiring(state.get("agent_key_expires_at"), min_ttl_seconds)


def resolve_nous_runtime_credentials(
    *,
    min_key_ttl_seconds: int = DEFAULT_AGENT_KEY_MIN_TTL_SECONDS,
    timeout_seconds: float = 15.0,
    insecure: Optional[bool] = None,
    ca_bundle: Optional[str] = None,
    force_mint: bool = False,
) -> Dict[str, Any]:
    """
    Resuelve credenciales de inferencia de Nous para uso en tiempo de ejecución.

    Garantiza que access_token sea válido (actualiza si es necesario) y que una clave
    de inferencia de corta duración esté presente con TTL mínimo (acuña/reutiliza según sea necesario).
    Los procesos concurrentes se coordinan a través del bloqueo del archivo del almacén de autenticación.

    Devuelve dict con: provider, base_url, api_key, key_id, expires_at,
    expires_in, source ("cache" o "portal").
    """
    min_key_ttl_seconds = max(60, int(min_key_ttl_seconds))
    sequence_id = uuid.uuid4().hex[:12]

    with _auth_store_lock():
        auth_store = _load_auth_store()
        state = _load_provider_state(auth_store, "nous")

        if not state:
            raise AuthError("Hermes no ha iniciado sesión en Nous Portal.",
                            provider="nous", relogin_required=True)

        portal_base_url = (
            _optional_base_url(state.get("portal_base_url"))
            or os.getenv("HERMES_PORTAL_BASE_URL")
            or os.getenv("NOUS_PORTAL_BASE_URL")
            or DEFAULT_NOUS_PORTAL_URL
        ).rstrip("/")
        inference_base_url = (
            _optional_base_url(state.get("inference_base_url"))
            or os.getenv("NOUS_INFERENCE_BASE_URL")
            or DEFAULT_NOUS_INFERENCE_URL
        ).rstrip("/")
        client_id = str(state.get("client_id") or DEFAULT_NOUS_CLIENT_ID)

        def _persist_state(reason: str) -> None:
            try:
                _save_provider_state(auth_store, "nous", state)
                _save_auth_store(auth_store)
            except Exception as exc:
                _oauth_trace(
                    "nous_state_persist_failed",
                    sequence_id=sequence_id,
                    reason=reason,
                    error_type=type(exc).__name__,
                )
                raise
            _oauth_trace(
                "nous_state_persisted",
                sequence_id=sequence_id,
                reason=reason,
                refresh_token_fp=_token_fingerprint(state.get("refresh_token")),
                access_token_fp=_token_fingerprint(state.get("access_token")),
            )

        verify = _resolve_verify(insecure=insecure, ca_bundle=ca_bundle, auth_state=state)
        timeout = httpx.Timeout(timeout_seconds if timeout_seconds else 15.0)
        _oauth_trace(
            "nous_runtime_credentials_start",
            sequence_id=sequence_id,
            force_mint=bool(force_mint),
            min_key_ttl_seconds=min_key_ttl_seconds,
            refresh_token_fp=_token_fingerprint(state.get("refresh_token")),
        )

        with httpx.Client(timeout=timeout, headers={"Accept": "application/json"}, verify=verify) as client:
            access_token = state.get("access_token")
            refresh_token = state.get("refresh_token")

            if not isinstance(access_token, str) or not access_token:
                raise AuthError("No se encontró token de acceso para inicio de sesión de Nous Portal.",
                                provider="nous", relogin_required=True)

            # Paso 1: actualizar token de acceso si está venciendo
            if _is_expiring(state.get("expires_at"), ACCESS_TOKEN_REFRESH_SKEW_SECONDS):
                if not isinstance(refresh_token, str) or not refresh_token:
                    raise AuthError("Sesión vencida y no hay token de actualización disponible.",
                                    provider="nous", relogin_required=True)

                _oauth_trace(
                    "refresh_start",
                    sequence_id=sequence_id,
                    reason="access_expiring",
                    refresh_token_fp=_token_fingerprint(refresh_token),
                )
                refreshed = _refresh_access_token(
                    client=client, portal_base_url=portal_base_url,
                    client_id=client_id, refresh_token=refresh_token,
                )
                now = datetime.now(timezone.utc)
                access_ttl = _coerce_ttl_seconds(refreshed.get("expires_in"))
                previous_refresh_token = refresh_token
                state["access_token"] = refreshed["access_token"]
                state["refresh_token"] = refreshed.get("refresh_token") or refresh_token
                state["token_type"] = refreshed.get("token_type") or state.get("token_type") or "Bearer"
                state["scope"] = refreshed.get("scope") or state.get("scope")
                refreshed_url = _optional_base_url(refreshed.get("inference_base_url"))
                if refreshed_url:
                    inference_base_url = refreshed_url
                state["obtained_at"] = now.isoformat()
                state["expires_in"] = access_ttl
                state["expires_at"] = datetime.fromtimestamp(
                    now.timestamp() + access_ttl, tz=timezone.utc
                ).isoformat()
                access_token = state["access_token"]
                refresh_token = state["refresh_token"]
                _oauth_trace(
                    "refresh_success",
                    sequence_id=sequence_id,
                    reason="access_expiring",
                    previous_refresh_token_fp=_token_fingerprint(previous_refresh_token),
                    new_refresh_token_fp=_token_fingerprint(refresh_token),
                )
                # Persistir inmediatamente para que los fallos de acuñación posteriores no puedan descartar tokens de actualización rotados.
                _persist_state("post_refresh_access_expiring")

            # Paso 2: acuñar clave de agente si falta o está venciendo
            used_cached_key = False
            mint_payload: Optional[Dict[str, Any]] = None

            if not force_mint and _agent_key_is_usable(state, min_key_ttl_seconds):
                used_cached_key = True
                _oauth_trace("agent_key_reuse", sequence_id=sequence_id)
            else:
                try:
                    _oauth_trace(
                        "mint_start",
                        sequence_id=sequence_id,
                        access_token_fp=_token_fingerprint(access_token),
                    )
                    mint_payload = _mint_agent_key(
                        client=client, portal_base_url=portal_base_url,
                        access_token=access_token, min_ttl_seconds=min_key_ttl_seconds,
                    )
                except AuthError as exc:
                    _oauth_trace(
                        "mint_error",
                        sequence_id=sequence_id,
                        code=exc.code,
                    )
                    # Ruta de reintento: el token de acceso puede estar obsoleto en el servidor a pesar de las comprobaciones locales
                    latest_refresh_token = state.get("refresh_token")
                    if (
                        exc.code in {"invalid_token", "invalid_grant"}
                        and isinstance(latest_refresh_token, str)
                        and latest_refresh_token
                    ):
                        _oauth_trace(
                            "refresh_start",
                            sequence_id=sequence_id,
                            reason="mint_retry_after_invalid_token",
                            refresh_token_fp=_token_fingerprint(latest_refresh_token),
                        )
                        refreshed = _refresh_access_token(
                            client=client, portal_base_url=portal_base_url,
                            client_id=client_id, refresh_token=latest_refresh_token,
                        )
                        now = datetime.now(timezone.utc)
                        access_ttl = _coerce_ttl_seconds(refreshed.get("expires_in"))
                        state["access_token"] = refreshed["access_token"]
                        state["refresh_token"] = refreshed.get("refresh_token") or latest_refresh_token
                        state["token_type"] = refreshed.get("token_type") or state.get("token_type") or "Bearer"
                        state["scope"] = refreshed.get("scope") or state.get("scope")
                        refreshed_url = _optional_base_url(refreshed.get("inference_base_url"))
                        if refreshed_url:
                            inference_base_url = refreshed_url
                        state["obtained_at"] = now.isoformat()
                        state["expires_in"] = access_ttl
                        state["expires_at"] = datetime.fromtimestamp(
                            now.timestamp() + access_ttl, tz=timezone.utc
                        ).isoformat()
                        access_token = state["access_token"]
                        refresh_token = state["refresh_token"]
                        _oauth_trace(
                            "refresh_success",
                            sequence_id=sequence_id,
                            reason="mint_retry_after_invalid_token",
                            previous_refresh_token_fp=_token_fingerprint(latest_refresh_token),
                            new_refresh_token_fp=_token_fingerprint(refresh_token),
                        )
                        # Persist retry refresh immediately for crash safety and cross-process visibility.
                        _persist_state("post_refresh_mint_retry")

                        mint_payload = _mint_agent_key(
                            client=client, portal_base_url=portal_base_url,
                            access_token=access_token, min_ttl_seconds=min_key_ttl_seconds,
                        )
                    else:
                        raise

            if mint_payload is not None:
                now = datetime.now(timezone.utc)
                state["agent_key"] = mint_payload.get("api_key")
                state["agent_key_id"] = mint_payload.get("key_id")
                state["agent_key_expires_at"] = mint_payload.get("expires_at")
                state["agent_key_expires_in"] = mint_payload.get("expires_in")
                state["agent_key_reused"] = bool(mint_payload.get("reused", False))
                state["agent_key_obtained_at"] = now.isoformat()
                minted_url = _optional_base_url(mint_payload.get("inference_base_url"))
                if minted_url:
                    inference_base_url = minted_url
                _oauth_trace(
                    "mint_success",
                    sequence_id=sequence_id,
                    reused=bool(mint_payload.get("reused", False)),
                )

            # Persist routing and TLS metadata for non-interactive refresh/mint
            state["portal_base_url"] = portal_base_url
            state["inference_base_url"] = inference_base_url
            state["client_id"] = client_id
            state["tls"] = {
                "insecure": verify is False,
                "ca_bundle": verify if isinstance(verify, str) else None,
            }

        _persist_state("resolve_nous_runtime_credentials_final")

    api_key = state.get("agent_key")
    if not isinstance(api_key, str) or not api_key:
        raise AuthError("Failed to resolve a Nous inference API key",
                        provider="nous", code="server_error")

    expires_at = state.get("agent_key_expires_at")
    expires_epoch = _parse_iso_timestamp(expires_at)
    expires_in = (
        max(0, int(expires_epoch - time.time()))
        if expires_epoch is not None
        else _coerce_ttl_seconds(state.get("agent_key_expires_in"))
    )

    return {
        "provider": "nous",
        "base_url": inference_base_url,
        "api_key": api_key,
        "key_id": state.get("agent_key_id"),
        "expires_at": expires_at,
        "expires_in": expires_in,
        "source": "cache" if used_cached_key else "portal",
    }


# =============================================================================
# Status helpers
# =============================================================================

def get_nous_auth_status() -> Dict[str, Any]:
    """Obtiene el estado de autenticacion de Nous Portal para mostrar en UI."""
    """Status snapshot for `hermes status` output."""
    state = get_provider_auth_state("nous")
    if not state:
        return {
            "logged_in": False,
            "portal_base_url": None,
            "inference_base_url": None,
            "access_expires_at": None,
            "agent_key_expires_at": None,
            "has_refresh_token": False,
        }
    return {
        "logged_in": bool(state.get("access_token")),
        "portal_base_url": state.get("portal_base_url"),
        "inference_base_url": state.get("inference_base_url"),
        "access_expires_at": state.get("expires_at"),
        "agent_key_expires_at": state.get("agent_key_expires_at"),
        "has_refresh_token": bool(state.get("refresh_token")),
    }


def get_codex_auth_status() -> Dict[str, Any]:
    """Obtiene el estado de autenticacion de OpenAI Codex para mostrar en UI."""
    """Status snapshot for Codex auth."""
    try:
        creds = resolve_codex_runtime_credentials()
        return {
            "logged_in": True,
            "auth_store": str(_auth_file_path()),
            "last_refresh": creds.get("last_refresh"),
            "auth_mode": creds.get("auth_mode"),
            "source": creds.get("source"),
        }
    except AuthError as exc:
        return {
            "logged_in": False,
            "auth_store": str(_auth_file_path()),
            "error": str(exc),
        }


def get_api_key_provider_status(provider_id: str) -> Dict[str, Any]:
    """Obtiene el estado de configuracion de un proveedor de clave de API."""
    """Status snapshot for API-key providers (z.ai, Kimi, MiniMax)."""
    pconfig = PROVIDER_REGISTRY.get(provider_id)
    if not pconfig or pconfig.auth_type != "api_key":
        return {"configured": False}

    api_key = ""
    key_source = ""
    for env_var in pconfig.api_key_env_vars:
        val = os.getenv(env_var, "").strip()
        if val:
            api_key = val
            key_source = env_var
            break

    env_url = ""
    if pconfig.base_url_env_var:
        env_url = os.getenv(pconfig.base_url_env_var, "").strip()

    if provider_id == "kimi-coding":
        base_url = _resolve_kimi_base_url(api_key, pconfig.inference_base_url, env_url)
    elif env_url:
        base_url = env_url
    else:
        base_url = pconfig.inference_base_url

    return {
        "configured": bool(api_key),
        "provider": provider_id,
        "name": pconfig.name,
        "key_source": key_source,
        "base_url": base_url,
        "logged_in": bool(api_key),  # compat with OAuth status shape
    }


def get_auth_status(provider_id: Optional[str] = None) -> Dict[str, Any]:
    """Generic auth status dispatcher."""
    target = provider_id or get_active_provider()
    if target == "nous":
        return get_nous_auth_status()
    if target == "openai-codex":
        return get_codex_auth_status()
    # API-key providers
    pconfig = PROVIDER_REGISTRY.get(target)
    if pconfig and pconfig.auth_type == "api_key":
        return get_api_key_provider_status(target)
    return {"logged_in": False}


def resolve_api_key_provider_credentials(provider_id: str) -> Dict[str, Any]:
    """Resuelve y devuelve las credenciales de un proveedor de clave de API."""
    """Resolve API key and base URL for an API-key provider.

    Returns dict with: provider, api_key, base_url, source.
    """
    pconfig = PROVIDER_REGISTRY.get(provider_id)
    if not pconfig or pconfig.auth_type != "api_key":
        raise AuthError(
            f"Provider '{provider_id}' is not an API-key provider.",
            provider=provider_id,
            code="invalid_provider",
        )

    api_key = ""
    key_source = ""
    for env_var in pconfig.api_key_env_vars:
        val = os.getenv(env_var, "").strip()
        if val:
            api_key = val
            key_source = env_var
            break

    env_url = ""
    if pconfig.base_url_env_var:
        env_url = os.getenv(pconfig.base_url_env_var, "").strip()

    if provider_id == "kimi-coding":
        base_url = _resolve_kimi_base_url(api_key, pconfig.inference_base_url, env_url)
    elif env_url:
        base_url = env_url.rstrip("/")
    else:
        base_url = pconfig.inference_base_url

    return {
        "provider": provider_id,
        "api_key": api_key,
        "base_url": base_url.rstrip("/"),
        "source": key_source or "default",
    }


# =============================================================================
# External credential detection
# =============================================================================

def detect_external_credentials() -> List[Dict[str, Any]]:
    """Scan for credentials from other CLI tools that Hermes can reuse.

    Returns a list of dicts, each with:
      - provider: str   -- Hermes provider id (e.g. "openai-codex")
      - path: str       -- filesystem path where creds were found
      - label: str      -- human-friendly description for the setup UI
    """
    found: List[Dict[str, Any]] = []

    # Codex CLI: ~/.codex/auth.json (importable, not shared)
    cli_tokens = _import_codex_cli_tokens()
    if cli_tokens:
        codex_path = Path.home() / ".codex" / "auth.json"
        found.append({
            "provider": "openai-codex",
            "path": str(codex_path),
            "label": f"Codex CLI credentials found ({codex_path}) — run `hermes login` to create a separate session",
        })

    return found


# =============================================================================
# CLI Commands — login / logout
# =============================================================================

def _update_config_for_provider(provider_id: str, inference_base_url: str) -> Path:
    """Actualiza config.yaml para activar un proveedor OAuth y establece su URL base de inferencia."""
    """Update config.yaml and auth.json to reflect the active provider."""
    # Set active_provider in auth.json so auto-resolution picks this provider
    with _auth_store_lock():
        auth_store = _load_auth_store()
        auth_store["active_provider"] = provider_id
        _save_auth_store(auth_store)

    # Update config.yaml model section
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    config: Dict[str, Any] = {}
    if config_path.exists():
        try:
            loaded = yaml.safe_load(config_path.read_text()) or {}
            if isinstance(loaded, dict):
                config = loaded
        except Exception:
            config = {}

    current_model = config.get("model")
    if isinstance(current_model, dict):
        model_cfg = dict(current_model)
    elif isinstance(current_model, str) and current_model.strip():
        model_cfg = {"default": current_model.strip()}
    else:
        model_cfg = {}

    model_cfg["provider"] = provider_id
    model_cfg["base_url"] = inference_base_url.rstrip("/")
    config["model"] = model_cfg

    config_path.write_text(yaml.safe_dump(config, sort_keys=False))
    return config_path


def _reset_config_provider() -> Path:
    """Elimina la seccion de proveedor de config.yaml para usar deteccion automatica."""
    """Reset config.yaml provider back to auto after logout."""
    config_path = get_config_path()
    if not config_path.exists():
        return config_path

    try:
        config = yaml.safe_load(config_path.read_text()) or {}
    except Exception:
        return config_path

    if not isinstance(config, dict):
        return config_path

    model = config.get("model")
    if isinstance(model, dict):
        model["provider"] = "auto"
        if "base_url" in model:
            model["base_url"] = OPENROUTER_BASE_URL
    config_path.write_text(yaml.safe_dump(config, sort_keys=False))
    return config_path


def _prompt_model_selection(model_ids: List[str], current_model: str = "") -> Optional[str]:
    """Interactive model selection. Puts current_model first with a marker. Returns chosen model ID or None."""
    # Reorder: current model first, then the rest (deduplicated)
    ordered = []
    if current_model and current_model in model_ids:
        ordered.append(current_model)
    for mid in model_ids:
        if mid not in ordered:
            ordered.append(mid)

    # Build display labels with marker on current
    def _label(mid):
        if mid == current_model:
            return f"{mid}  ← currently in use"
        return mid

    # Default cursor on the current model (index 0 if it was reordered to top)
    default_idx = 0

    # Try arrow-key menu first, fall back to number input
    try:
        from simple_term_menu import TerminalMenu
        choices = [f"  {_label(mid)}" for mid in ordered]
        choices.append("  Enter custom model name")
        choices.append("  Skip (keep current)")
        menu = TerminalMenu(
            choices,
            cursor_index=default_idx,
            menu_cursor="-> ",
            menu_cursor_style=("fg_green", "bold"),
            menu_highlight_style=("fg_green",),
            cycle_cursor=True,
            clear_screen=False,
            title="Select default model:",
        )
        idx = menu.show()
        if idx is None:
            return None
        print()
        if idx < len(ordered):
            return ordered[idx]
        elif idx == len(ordered):
            custom = input("Enter model name: ").strip()
            return custom if custom else None
        return None
    except (ImportError, NotImplementedError):
        pass

    # Fallback: numbered list
    print("Select default model:")
    for i, mid in enumerate(ordered, 1):
        print(f"  {i}. {_label(mid)}")
    n = len(ordered)
    print(f"  {n + 1}. Enter custom model name")
    print(f"  {n + 2}. Skip (keep current)")
    print()

    while True:
        try:
            choice = input(f"Choice [1-{n + 2}] (default: skip): ").strip()
            if not choice:
                return None
            idx = int(choice)
            if 1 <= idx <= n:
                return ordered[idx - 1]
            elif idx == n + 1:
                custom = input("Enter model name: ").strip()
                return custom if custom else None
            elif idx == n + 2:
                return None
            print(f"Please enter 1-{n + 2}")
        except ValueError:
            print("Please enter a number")
        except (KeyboardInterrupt, EOFError):
            return None


def _save_model_choice(model_id: str) -> None:
    """Guarda el ID del modelo seleccionado como default en el archivo de configuracion."""
    """Save the selected model to config.yaml (single source of truth).

    The model is stored in config.yaml only — NOT in .env.  This avoids
    conflicts in multi-agent setups where env vars would stomp each other.
    """
    from hermes_cli.config import save_config, load_config

    config = load_config()
    # Always use dict format so provider/base_url can be stored alongside
    if isinstance(config.get("model"), dict):
        config["model"]["default"] = model_id
    else:
        config["model"] = {"default": model_id}
    save_config(config)


def login_command(args) -> None:
    """Punto de entrada CLI para el comando `hermes login`."""
    """Deprecated: use 'hermes model' or 'hermes setup' instead."""
    print("The 'hermes login' command has been removed.")
    print("Use 'hermes model' to select a provider and model,")
    print("or 'hermes setup' for full interactive setup.")
    raise SystemExit(0)


def _login_openai_codex(args, pconfig: ProviderConfig) -> None:
    """Flujo interactivo de inicio de sesion para OpenAI Codex."""
    """OpenAI Codex login via device code flow. Tokens stored in ~/.hermes/auth.json."""

    # Check for existing Hermes-owned credentials
    try:
        existing = resolve_codex_runtime_credentials()
        print("Existing Codex credentials found in Hermes auth store.")
        try:
            reuse = input("Use existing credentials? [Y/n]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            reuse = "y"
        if reuse in ("", "y", "yes"):
            config_path = _update_config_for_provider("openai-codex", existing.get("base_url", DEFAULT_CODEX_BASE_URL))
            print()
            print("Login successful!")
            print(f"  Config updated: {config_path} (model.provider=openai-codex)")
            return
    except AuthError:
        pass

    # Check for existing Codex CLI tokens we can import
    cli_tokens = _import_codex_cli_tokens()
    if cli_tokens:
        print("Found existing Codex CLI credentials at ~/.codex/auth.json")
        print("Hermes will create its own session to avoid conflicts with Codex CLI / VS Code.")
        try:
            do_import = input("Import these credentials? (a separate login is recommended) [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            do_import = "n"
        if do_import in ("y", "yes"):
            _save_codex_tokens(cli_tokens)
            base_url = os.getenv("HERMES_CODEX_BASE_URL", "").strip().rstrip("/") or DEFAULT_CODEX_BASE_URL
            config_path = _update_config_for_provider("openai-codex", base_url)
            print()
            print("Credentials imported. Note: if Codex CLI refreshes its token,")
            print("Hermes will keep working independently with its own session.")
            print(f"  Config updated: {config_path} (model.provider=openai-codex)")
            return

    # Run a fresh device code flow — Hermes gets its own OAuth session
    print()
    print("Signing in to OpenAI Codex...")
    print("(Hermes creates its own session — won't affect Codex CLI or VS Code)")
    print()

    creds = _codex_device_code_login()

    # Save tokens to Hermes auth store
    _save_codex_tokens(creds["tokens"], creds.get("last_refresh"))
    config_path = _update_config_for_provider("openai-codex", creds.get("base_url", DEFAULT_CODEX_BASE_URL))
    print()
    print("Login successful!")
    print(f"  Auth state: ~/.hermes/auth.json")
    print(f"  Config updated: {config_path} (model.provider=openai-codex)")


def _codex_device_code_login() -> Dict[str, Any]:
    """Run the OpenAI device code login flow and return credentials dict."""
    import time as _time

    issuer = "https://auth.openai.com"
    client_id = CODEX_OAUTH_CLIENT_ID

    # Step 1: Request device code
    try:
        with httpx.Client(timeout=httpx.Timeout(15.0)) as client:
            resp = client.post(
                f"{issuer}/api/accounts/deviceauth/usercode",
                json={"client_id": client_id},
                headers={"Content-Type": "application/json"},
            )
    except Exception as exc:
        raise AuthError(
            f"Failed to request device code: {exc}",
            provider="openai-codex", code="device_code_request_failed",
        )

    if resp.status_code != 200:
        raise AuthError(
            f"Device code request returned status {resp.status_code}.",
            provider="openai-codex", code="device_code_request_error",
        )

    device_data = resp.json()
    user_code = device_data.get("user_code", "")
    device_auth_id = device_data.get("device_auth_id", "")
    poll_interval = max(3, int(device_data.get("interval", "5")))

    if not user_code or not device_auth_id:
        raise AuthError(
            "Device code response missing required fields.",
            provider="openai-codex", code="device_code_incomplete",
        )

    # Step 2: Show user the code
    print("To continue, follow these steps:\n")
    print(f"  1. Open this URL in your browser:")
    print(f"     \033[94m{issuer}/codex/device\033[0m\n")
    print(f"  2. Enter this code:")
    print(f"     \033[94m{user_code}\033[0m\n")
    print("Waiting for sign-in... (press Ctrl+C to cancel)")

    # Step 3: Poll for authorization code
    max_wait = 15 * 60  # 15 minutes
    start = _time.monotonic()
    code_resp = None

    try:
        with httpx.Client(timeout=httpx.Timeout(15.0)) as client:
            while _time.monotonic() - start < max_wait:
                _time.sleep(poll_interval)
                poll_resp = client.post(
                    f"{issuer}/api/accounts/deviceauth/token",
                    json={"device_auth_id": device_auth_id, "user_code": user_code},
                    headers={"Content-Type": "application/json"},
                )

                if poll_resp.status_code == 200:
                    code_resp = poll_resp.json()
                    break
                elif poll_resp.status_code in (403, 404):
                    continue  # User hasn't completed login yet
                else:
                    raise AuthError(
                        f"Device auth polling returned status {poll_resp.status_code}.",
                        provider="openai-codex", code="device_code_poll_error",
                    )
    except KeyboardInterrupt:
        print("\nLogin cancelled.")
        raise SystemExit(130)

    if code_resp is None:
        raise AuthError(
            "Login timed out after 15 minutes.",
            provider="openai-codex", code="device_code_timeout",
        )

    # Step 4: Exchange authorization code for tokens
    authorization_code = code_resp.get("authorization_code", "")
    code_verifier = code_resp.get("code_verifier", "")
    redirect_uri = f"{issuer}/deviceauth/callback"

    if not authorization_code or not code_verifier:
        raise AuthError(
            "Device auth response missing authorization_code or code_verifier.",
            provider="openai-codex", code="device_code_incomplete_exchange",
        )

    try:
        with httpx.Client(timeout=httpx.Timeout(15.0)) as client:
            token_resp = client.post(
                CODEX_OAUTH_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": authorization_code,
                    "redirect_uri": redirect_uri,
                    "client_id": client_id,
                    "code_verifier": code_verifier,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
    except Exception as exc:
        raise AuthError(
            f"Token exchange failed: {exc}",
            provider="openai-codex", code="token_exchange_failed",
        )

    if token_resp.status_code != 200:
        raise AuthError(
            f"Token exchange returned status {token_resp.status_code}.",
            provider="openai-codex", code="token_exchange_error",
        )

    tokens = token_resp.json()
    access_token = tokens.get("access_token", "")
    refresh_token = tokens.get("refresh_token", "")

    if not access_token:
        raise AuthError(
            "Token exchange did not return an access_token.",
            provider="openai-codex", code="token_exchange_no_access_token",
        )

    # Return tokens for the caller to persist (no longer writes to ~/.codex/)
    base_url = (
        os.getenv("HERMES_CODEX_BASE_URL", "").strip().rstrip("/")
        or DEFAULT_CODEX_BASE_URL
    )

    return {
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token,
        },
        "base_url": base_url,
        "last_refresh": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "auth_mode": "chatgpt",
        "source": "device-code",
    }


def _login_nous(args, pconfig: ProviderConfig) -> None:
    """Flujo de autorización de dispositivo de Nous Portal."""
    portal_base_url = (
        getattr(args, "portal_url", None)
        or os.getenv("HERMES_PORTAL_BASE_URL")
        or os.getenv("NOUS_PORTAL_BASE_URL")
        or pconfig.portal_base_url
    ).rstrip("/")
    requested_inference_url = (
        getattr(args, "inference_url", None)
        or os.getenv("NOUS_INFERENCE_BASE_URL")
        or pconfig.inference_base_url
    ).rstrip("/")
    client_id = getattr(args, "client_id", None) or pconfig.client_id
    scope = getattr(args, "scope", None) or pconfig.scope
    open_browser = not getattr(args, "no_browser", False)
    timeout_seconds = getattr(args, "timeout", None) or 15.0
    timeout = httpx.Timeout(timeout_seconds)

    insecure = bool(getattr(args, "insecure", False))
    ca_bundle = (
        getattr(args, "ca_bundle", None)
        or os.getenv("HERMES_CA_BUNDLE")
        or os.getenv("SSL_CERT_FILE")
    )
    verify: bool | str = False if insecure else (ca_bundle if ca_bundle else True)

    # Skip browser open in SSH sessions
    if _is_remote_session():
        open_browser = False

    print(f"Iniciando inicio de sesión de Hermes vía {pconfig.name}...")
    print(f"Portal: {portal_base_url}")
    if insecure:
        print("Verificación TLS: deshabilitada (--insecure)")
    elif ca_bundle:
        print(f"Verificación TLS: paquete de CA personalizado ({ca_bundle})")

    try:
        with httpx.Client(timeout=timeout, headers={"Accept": "application/json"}, verify=verify) as client:
            device_data = _request_device_code(
                client=client, portal_base_url=portal_base_url,
                client_id=client_id, scope=scope,
            )

            verification_url = str(device_data["verification_uri_complete"])
            user_code = str(device_data["user_code"])
            expires_in = int(device_data["expires_in"])
            interval = int(device_data["interval"])

            print()
            print("Para continuar:")
            print(f"  1. Abre: {verification_url}")
            print(f"  2. Si se te pide, ingresa código: {user_code}")

            if open_browser:
                opened = webbrowser.open(verification_url)
                if opened:
                    print("  (Se abrió navegador para verificación)")
                else:
                    print("  No se pudo abrir navegador automáticamente — utiliza la URL anterior.")

            effective_interval = max(1, min(interval, DEVICE_AUTH_POLL_INTERVAL_CAP_SECONDS))
            print(f"Esperando aprobación (sondeando cada {effective_interval}s)...")

            token_data = _poll_for_token(
                client=client, portal_base_url=portal_base_url,
                client_id=client_id, device_code=str(device_data["device_code"]),
                expires_in=expires_in, poll_interval=interval,
            )

        # Process token response
        now = datetime.now(timezone.utc)
        token_expires_in = _coerce_ttl_seconds(token_data.get("expires_in", 0))
        expires_at = now.timestamp() + token_expires_in
        inference_base_url = (
            _optional_base_url(token_data.get("inference_base_url"))
            or requested_inference_url
        )
        if inference_base_url != requested_inference_url:
            print(f"Utilizando URL de inferencia proporcionada por el portal: {inference_base_url}")

        auth_state = {
            "portal_base_url": portal_base_url,
            "inference_base_url": inference_base_url,
            "client_id": client_id,
            "scope": token_data.get("scope") or scope,
            "token_type": token_data.get("token_type", "Bearer"),
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
            "obtained_at": now.isoformat(),
            "expires_at": datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat(),
            "expires_in": token_expires_in,
            "tls": {
                "insecure": verify is False,
                "ca_bundle": verify if isinstance(verify, str) else None,
            },
            "agent_key": None,
            "agent_key_id": None,
            "agent_key_expires_at": None,
            "agent_key_expires_in": None,
            "agent_key_reused": None,
            "agent_key_obtained_at": None,
        }

        # Save auth state
        with _auth_store_lock():
            auth_store = _load_auth_store()
            _save_provider_state(auth_store, "nous", auth_state)
            saved_to = _save_auth_store(auth_store)

        config_path = _update_config_for_provider("nous", inference_base_url)
        print()
        print("¡Inicio de sesión exitoso!")
        print(f"  Estado de auth: {saved_to}")
        print(f"  Configuración actualizada: {config_path} (model.provider=nous)")

        # Mint an initial agent key and list available models
        try:
            runtime_creds = resolve_nous_runtime_credentials(
                min_key_ttl_seconds=5 * 60,
                timeout_seconds=timeout_seconds,
                insecure=insecure, ca_bundle=ca_bundle,
            )
            runtime_key = runtime_creds.get("api_key")
            runtime_base_url = runtime_creds.get("base_url") or inference_base_url
            if not isinstance(runtime_key, str) or not runtime_key:
                raise AuthError("No hay clave de API de tiempo de ejecución disponible para obtener modelos",
                                provider="nous", code="invalid_token")

            model_ids = fetch_nous_models(
                inference_base_url=runtime_base_url,
                api_key=runtime_key,
                timeout_seconds=timeout_seconds,
                verify=verify,
            )

            print()
            if model_ids:
                selected_model = _prompt_model_selection(model_ids)
                if selected_model:
                    _save_model_choice(selected_model)
                    print(f"Modelo predeterminado establecido en: {selected_model}")
            else:
                print("No fueron devueltos modelos por la API de inferencia.")
        except Exception as exc:
            message = format_auth_error(exc) if isinstance(exc, AuthError) else str(exc)
            print()
            print(f"Inicio de sesión exitoso, pero no se pudieron obtener modelos disponibles. Razón: {message}")

    except KeyboardInterrupt:
        print("\nInicio de sesión cancelado.")
        raise SystemExit(130)
    except Exception as exc:
        print(f"Fallo de inicio de sesión: {exc}")
        raise SystemExit(1)


def logout_command(args) -> None:
    """Borra el estado de autenticación para un proveedor."""
    provider_id = getattr(args, "provider", None)

    if provider_id and provider_id not in PROVIDER_REGISTRY:
        print(f"Proveedor desconocido: {provider_id}")
        raise SystemExit(1)

    active = get_active_provider()
    target = provider_id or active

    if not target:
        print("Ningún proveedor está actualmente conectado.")
        return

    provider_name = PROVIDER_REGISTRY[target].name if target in PROVIDER_REGISTRY else target

    if clear_provider_auth(target):
        _reset_config_provider()
        print(f"Has cerrado sesión de {provider_name}.")
        if os.getenv("OPENROUTER_API_KEY"):
            print("Hermes usará OpenRouter para inferencia.")
        else:
            print("Run `hermes model` or configure an API key to use Hermes.")
    else:
        print(f"No auth state found for {provider_name}.")
