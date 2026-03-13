---
sidebar_position: 8
title: "Ejecución de Código"
description: "Ejecución de Python en zona de pruebas con acceso a herramientas RPC — colapsa flujos de trabajo de múltiples pasos en un solo turno"
---

# Ejecución de Código (Llamada Programática de Herramientas)

La herramienta `execute_code` permite que el agente escriba scripts de Python que llamen herramientas de Hermes de forma programática, colapsando flujos de trabajo de múltiples pasos en un solo turno de LLM. El script se ejecuta en un proceso hijo en zona de pruebas en el host del agente, comunicándose a través de RPC de socket de dominio Unix.

## Cómo Funciona

1. El agente escribe un script de Python usando `from hermes_tools import ...`
2. Hermes genera un módulo stub `hermes_tools.py` con funciones RPC
3. Hermes abre un socket de dominio Unix e inicia un thread oyente RPC
4. El script se ejecuta en un proceso hijo — las llamadas de herramientas viajan sobre el socket de vuelta a Hermes
5. Solo la salida `print()` del script se devuelve al LLM; los resultados intermedios de herramientas nunca entran en la ventana de contexto

```python
# El agente puede escribir scripts como:
from hermes_tools import web_search, web_extract

results = web_search("Python 3.13 features", limit=5)
for r in results["data"]["web"]:
    content = web_extract([r["url"]])
    # ... filtrar y procesar ...
print(summary)
```

**Herramientas disponibles en zona de pruebas:** `web_search`, `web_extract`, `read_file`, `write_file`, `search_files`, `patch`, `terminal` (solo primer plano).

## Cuándo el Agente Usa Esto

El agente usa `execute_code` cuando hay:

- **3+ llamadas de herramientas** con lógica de procesamiento entre ellas
- Filtrado masivo de datos o ramificación condicional
- Bucles sobre resultados

El beneficio clave: los resultados intermedios de herramientas nunca entran en la ventana de contexto — solo la salida final `print()` regresa, reduciendo drásticamente el uso de tokens.

## Ejemplos Prácticos

### Tubería de Procesamiento de Datos

```python
from hermes_tools import search_files, read_file
import json

# Encuentra todos los archivos de configuración y extrae configuración de base de datos
matches = search_files("database", path=".", file_glob="*.yaml", limit=20)
configs = []
for match in matches.get("matches", []):
    content = read_file(match["path"])
    configs.append({"file": match["path"], "preview": content["content"][:200]})

print(json.dumps(configs, indent=2))
```

### Búsqueda Web Multi-Paso

```python
from hermes_tools import web_search, web_extract
import json

# Busca, extrae y resume en un turno
results = web_search("Rust async runtime comparison 2025", limit=5)
summaries = []
for r in results["data"]["web"]:
    page = web_extract([r["url"]])
    for p in page.get("results", []):
        if p.get("content"):
            summaries.append({
                "title": r["title"],
                "url": r["url"],
                "excerpt": p["content"][:500]
            })

print(json.dumps(summaries, indent=2))
```

### Refactorización Masiva de Archivos

```python
from hermes_tools import search_files, read_file, patch

# Encuentra todos los archivos Python usando API deprecada y corrígelos
matches = search_files("old_api_call", path="src/", file_glob="*.py")
fixed = 0
for match in matches.get("matches", []):
    result = patch(
        path=match["path"],
        old_string="old_api_call(",
        new_string="new_api_call(",
        replace_all=True
    )
    if "error" not in str(result):
        fixed += 1

print(f"Fixed {fixed} files out of {len(matches.get('matches', []))} matches")
```

### Tubería de Compilación y Prueba

```python
from hermes_tools import terminal, read_file
import json

# Ejecuta pruebas, analiza resultados y reporta
result = terminal("cd /project && python -m pytest --tb=short -q 2>&1", timeout=120)
output = result.get("output", "")

# Analiza salida de prueba
passed = output.count(" passed")
failed = output.count(" failed")
errors = output.count(" error")

report = {
    "passed": passed,
    "failed": failed,
    "errors": errors,
    "exit_code": result.get("exit_code", -1),
    "summary": output[-500:] if len(output) > 500 else output
}

print(json.dumps(report, indent=2))
```

## Límites de Recursos

| Resource | Limit | Notes |
|----------|-------|-------|
| **Timeout** | 5 minutes (300s) | Script is killed with SIGTERM, then SIGKILL after 5s grace |
| **Stdout** | 50 KB | Output truncated with `[output truncated at 50KB]` notice |
| **Stderr** | 10 KB | Included in output on non-zero exit for debugging |
| **Llamadas de Herramientas** | 50 per execution | Error returned when limit reached |

All limits are configurable via `config.yaml`:

```yaml
# In ~/.hermes/config.yaml
code_execution:
  timeout: 300       # Max seconds per script (default: 300)
  max_tool_calls: 50 # Max tool calls per execution (default: 50)
```

## How Llamadas de Herramientas Work Inside Scripts

When your script calls a function like `web_buscar("consulta")`:

1. The call is serialized to JSON and sent over a Unix domain socket to the parent process
2. The parent dispatches through the standard `handle_function_call` Manejador
3. The result is sent back over the socket
4. The function returns the parsed result

This means Llamadas de Herramientas inside scripts behave identically to normal Llamadas de Herramientas — same rate limits, same manejo de errores, same capabilities. The only restriction is that `terminal()` is foreground-only (no `background`, `pty`, or `check_interval` Parámetros).

## manejo de errores

Cuando un script falla, el agente recibe información de error estructurada:

- **Código de salida distinto de cero**: stderr se incluye en la salida para que el agente vea el traceback completo
- **Tiempo de espera**: El script se mata y el agente ve `"Script timed out after 300s and was killed."`
- **Interrupción**: Si el usuario envía un nuevo mensaje durante la ejecución, el script se termina y el agente ve `[execution interrupted — user sent a new message]`
- **Límite de llamadas de herramientas**: Cuando se alcanza el límite de 50 llamadas, las llamadas de herramientas posteriores devuelven un mensaje de error

La respuesta siempre incluye `status` (success/error/timeout/interrupted), `output`, `tool_calls_made` y `duration_seconds`.

## Seguridad

:::danger Modelo de Seguridad
El proceso hijo se ejecuta con un **entorno mínimo**. Las claves API, tokens y credenciales se eliminan completamente. El script accede a herramientas exclusivamente a través del canal RPC — no puede leer secretos de variables de entorno.
:::

Las variables de entorno que contienen `KEY`, `token`, `SECRET`, `PASSWORD`, `CREDENTIAL`, `PASSWD` o `AUTH` en sus nombres se excluyen. Solo se pasan variables de sistema seguras (`PATH`, `HOME`, `LANG`, `SHELL`, `PYTHONPATH`, `VIRTUAL_ENV`, etc.).

El script se ejecuta en un directorio temporal que se limpia después de la ejecución. El proceso hijo se ejecuta en su propio grupo de procesos para que pueda ser eliminado limpiamente en tiempo de espera o interrupción.

## execute_code vs terminal

| Caso de Uso | execute_code | terminal |
|----------|-------------|----------|
| Flujos de trabajo de múltiples pasos con llamadas de herramientas entre | ✅ | ❌ |
| Comando shell simple | ❌ | ✅ |
| Filtrado/procesamiento de salidas grandes de herramientas | ✅ | ❌ |
| Ejecución de una suite de compilación o prueba | ❌ | ✅ |
| Bucles sobre resultados de búsqueda | ✅ | ❌ |
| Procesos interactivos/de fondo | ❌ | ✅ |
| Necesita claves API en el entorno | ❌ | ✅ |

**Regla de oro:** Usa `execute_code` cuando necesites llamar herramientas de Hermes de forma programática con lógica entre llamadas. Usa `terminal` para ejecutar comandos shell, compilaciones y procesos.

## Soporte de Plataforma

La Ejecución de Código requiere sockets de dominio Unix y está disponible **solo en Linux y macOS**. Se desactiva automáticamente en Windows — el agente vuelve a llamadas de herramientas secuenciales regulares.
