---
sidebar_position: 4
title: "MCP (Protocolo de Contexto de Modelo)"
description: "Conecta Hermes Agent a servidores de herramientas externas vía MCP — bases de datos, APIs, sistemas de archivos y más"
---

# MCP (Protocolo de Contexto de Modelo)

MCP permite que Hermes Agent se conecte a servidores de herramientas externas — dándole al agente acceso a bases de datos, APIs, sistemas de archivos y más sin cambios de código.

## Descripción General

El [Protocolo de Contexto de Modelo](https://modelcontextprotocol.io/) (MCP) es un estándar abierto para conectar agentes de IA a herramientas externas y fuentes de datos. Los servidores MCP exponen herramientas sobre un protocolo RPC ligero, y Hermes Agent puede conectarse a cualquier servidor compatible automáticamente.

Lo que esto significa para usted:

- **Miles de herramientas listas para usar** — explore el [directorio de servidores MCP](https://github.com/modelcontextprotocol/servers) para servidores que cubren GitHub, Slack, bases de datos, sistemas de archivos, web scraping y más
- **No se necesitan cambios de código** — agregue algunas líneas a `~/.hermes/config.yaml` y las herramientas aparecen junto con las integradas
- **Mezclar y combinar** — ejecute múltiples servidores MCP simultáneamente, combinando servidores basados en stdio e HTTP
- **Seguro de forma predeterminada** — las variables de entorno están filtradas y las credenciales se eliminan de los mensajes de error

## Requisitos previos

```bash
pip install hermes-agent[mcp]
```

| Tipo de Servidor | Tiempo de ejecución necesario | Ejemplo |
|-------------|---------------|---------|
| HTTP/remoto | Nada extra | `url: "https://mcp.example.com"` |
| Basado en npm (npx) | Node.js 18+ | `command: "npx"` |
| Basado en Python | uv (recomendado) | `command: "uvx"` |

## Configuración

Los servidores MCP se configuran en `~/.hermes/config.yaml` bajo la clave `mcp_servers`.

### Servidores Stdio

Los servidores Stdio se ejecutan como subprocesos locales, comunicándose sobre stdin/stdout:

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]
    env: {}

  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxx"
```

| Clave | Requerida | Descripción |
|-----|----------|-------------|
| `command` | Sí | Ejecutable a executar (`npx`, `uvx`, `python`) |
| `args` | No | Argumentos de línea de comandos |
| `env` | No | Variables de entorno para el subproceso |

:::info Seguridad
Solo las variables `env` listadas explícitamente más una línea base segura (`PATH`, `HOME`, `USER`, `LANG`, `SHELL`, `TMPDIR`, `XDG_*`) se pasan al subproceso. Sus claves API y secretos **no** se filtran.
:::

### Servidores HTTP

```yaml
mcp_servers:
  remote_api:
    url: "https://my-mcp-server.example.com/mcp"
    headers:
      Authorization: "Bearer sk-xxxxxxxxxxxx"
```

### Tiempos de espera por servidor

```yaml
mcp_servers:
  slow_database:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-postgres"]
    env:
      DATABASE_URL: "postgres://user:pass@localhost/mydb"
    timeout: 300          # Tiempo de espera de llamada de herramienta (predeterminado: 120s)
    connect_timeout: 90   # Tiempo de espera de conexión inicial (predeterminado: 60s)
```

### Ejemplo de configuración mixta

```yaml
mcp_servers:
  # Sistema de archivos local vía stdio
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]

  # API de GitHub vía stdio con autenticación
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxx"

  # Base de datos remota vía HTTP
  company_db:
    url: "https://mcp.internal.company.com/db"
    headers:
      Authorization: "Bearer sk-xxxxxxxxxxxx"
    timeout: 180

  # Servidor basado en Python vía uvx
  memory:
    command: "uvx"
    args: ["mcp-server-memory"]
```

## Traducción desde la configuración de Claude Desktop

Muchos documentos de servidores MCP muestran el formato JSON de Claude Desktop. Aquí está la traducción:

**JSON de Claude Desktop:**
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    }
  }
}
```

**YAML de Hermes:**
```yaml
mcp_servers:                          # mcpServers → mcp_servers (snake_case)
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
```

Reglas: `mcpServers` → `mcp_servers` (snake_case), JSON → YAML. Las claves como `command`, `args`, `env` son idénticas.

## Cómo Funciona

### Registro de herramientas

Cada herramienta MCP se registra con un nombre prefijado:

```
mcp_{server_name}_{tool_name}
```

| Nombre del Servidor | Nombre de herramienta MCP | Registrado como |
|-------------|--------------|---------------|
| `filesystem` | `read_file` | `mcp_filesystem_read_file` |
| `github` | `create-issue` | `mcp_github_create_issue` |
| `my-api` | `query.data` | `mcp_my_api_query_data` |

Las herramientas aparecen junto con herramientas integradas — el agente las llama como cualquier otra herramienta.

:::info
Además de las herramientas propias del servidor, cada servidor MCP también obtiene 4 herramientas de utilidad registradas automáticamente: `list_resources`, `read_resource`, `list_prompts` y `get_prompt`. Estos permiten que el agente descubra y use recursos y mensajes MCP expuestos por el servidor.
:::

### Reconexión

Si un servidor MCP se desconecta, Hermes se reconecta automáticamente con retroceso exponencial (1s, 2s, 4s, 8s, 16s — máx 5 intentos). Los fallos de conexión inicial se reportan inmediatamente.

### Apagado

Al salir del agente, todas las conexiones del servidor MCP se cierran correctamente.

## Servidores MCP Populares

| Servidor | Paquete | Descripción |
|--------|---------|-------------|
| Sistema de archivos | `@modelcontextprotocol/server-filesystem` | Leer/escribir/buscar archivos locales |
| GitHub | `@modelcontextprotocol/server-github` | Problemas, PRs, repositorios, búsqueda de código |
| Git | `@modelcontextprotocol/server-git` | Operaciones Git en repositorios locales |
| Fetch | `@modelcontextprotocol/server-fetch` | Obtención HTTP y contenido web |
| Memoria | `@modelcontextprotocol/server-memory` | Memoria de clave-valor persistente |
| SQLite | `@modelcontextprotocol/server-sqlite` | Consultar bases de datos SQLite |
| PostgreSQL | `@modelcontextprotocol/server-postgres` | Consultar bases de datos PostgreSQL |
| Búsqueda Brave | `@modelcontextprotocol/server-brave-search` | Búsqueda web vía API de Brave |
| Puppeteer | `@modelcontextprotocol/server-puppeteer` | Automatización de navegador |

### Configuraciones de ejemplo

```yaml
mcp_servers:
  # Sin clave API
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]

  git:
    command: "uvx"
    args: ["mcp-server-git", "--repository", "/home/user/my-repo"]

  fetch:
    command: "uvx"
    args: ["mcp-server-fetch"]

  sqlite:
    command: "uvx"
    args: ["mcp-server-sqlite", "--db-path", "/home/user/data.db"]

  # Requiere clave API
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxx"

  brave_search:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-brave-search"]
    env:
      BRAVE_API_KEY: "BSA_xxxxxxxxxxxx"
```

## Solución de Problemas

### "MCP SDK not available"

```bash
pip install hermes-agent[mcp]
```

### El servidor no llega a iniciar

El comando del servidor MCP (`npx`, `uvx`) no está en PATH. Instale el tiempo de ejecución necesario:

```bash
# Para servidores basados en npm
npm install -g npx    # o asegúrese de que Node.js 18+ esté instalado

# Para servidores basados en Python
pip install uv        # luego use "uvx" como comando
```

### El servidor se conecta pero las herramientas fallan con errores de autenticación

Asegúrese de que la clave esté en el bloque `env` del servidor:

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_your_actual_token"  # Verifique esto
```

### Tiempo de espera de conexión

Aumente `connect_timeout` para servidores de inicio lento:

```yaml
mcp_servers:
  slow_server:
    command: "npx"
    args: ["-y", "heavy-server-package"]
    connect_timeout: 120   # predeterminado es 60
```

### Recargar servidores MCP

Puede recargar servidores MCP sin reiniciar Hermes:

- En la CLI: el agente se reconecta automáticamente
- En mensajería: envíe `/reload-mcp`

## Muestreo (Solicitudes de LLM iniciadas por el servidor)

La capacidad `sampling/createMessage` de MCP permite que los servidores MCP soliciten finalizaciones de LLM a través del agente Hermes. Esto permite flujos de trabajo de agente-en-bucle donde los servidores pueden aprovechar el LLM durante la ejecución de herramientas — por ejemplo, un servidor de base de datos pidiendo al LLM que interprete resultados de consulta, o un servidor de análisis de código solicitando al LLM que revise los hallazgos.

### Cómo Funciona

Cuando un servidor MCP envía una solicitud `sampling/createMessage`:

1. La devolución de llamada de muestreo valida contra límites de velocidad y lista blanca de modelos
2. Resuelve qué modelo usar (anulación de config > sugerencia del servidor > predeterminado)
3. Convierte mensajes MCP a formato compatible con OpenAI
4. Descarga la llamada LLM a un hilo vía `asyncio.to_thread()` (sin bloqueo)
5. Devuelve la respuesta (texto o uso de herramienta) de vuelta al servidor

### Configuración

El muestreo está **habilitado de forma predeterminada** para todos los servidores MCP. No se necesita configuración adicional — si tiene un cliente LLM auxiliar configurado, el muestreo funciona automáticamente.

```yaml
mcp_servers:
  analysis_server:
    command: "npx"
    args: ["-y", "my-analysis-server"]
    sampling:
      enabled: true           # predeterminado: true
      model: "gemini-3-flash" # anular modelo (opcional)
      max_tokens_cap: 4096    # máx tokens por solicitud (predeterminado: 4096)
      timeout: 30             # tiempo de espera de llamada LLM en segundos (predeterminado: 30)
      max_rpm: 10             # máx solicitudes por minuto (predeterminado: 10)
      allowed_models: []      # lista blanca de modelos (vacío = permitir todos)
      max_tool_rounds: 5      # máx rondas de uso de herramienta consecutivas (0 = deshabilitar)
      log_level: "info"       # verbosidad de auditoría: debug, info, warning
```

### Uso de herramientas en muestreo

Los servidores pueden incluir `tools` y `toolChoice` en solicitudes de muestreo, habilitando flujos de trabajo de múltiples turnos aumentados por herramientas dentro de una sola sesión de muestreo. La devolución de llamada reenvía definiciones de herramientas al LLM, maneja respuestas de uso de herramientas con tipos `ToolUseContent` apropiados, y aplica `max_tool_rounds` para prevenir bucles infinitos.

### Seguridad

- **Limitación de velocidad**: Ventana deslizante por servidor (predeterminado: 10 req/min)
- **Límite de tokens**: Los servidores no pueden solicitar más que `max_tokens_cap` (predeterminado: 4096)
- **Lista blanca de modelos**: `allowed_models` restringe qué modelos puede usar un servidor
- **Límite de bucle de herramientas**: `max_tool_rounds` cubre rondas de uso de herramientas consecutivas
- **Eliminación de credenciales**: Las respuestas de LLM se desinfectan antes de devolverse al servidor
- **Sin bloqueo**: Las llamadas LLM se ejecutan en un hilo separado vía `asyncio.to_thread()`
- **Errores tipados**: Todos los fallos devuelven `ErrorData` estructurado por especificación MCP

Para deshabilitar el muestreo para servidores que no son de confianza:

```yaml
mcp_servers:
  untrusted:
    command: "npx"
    args: ["-y", "untrusted-server"]
    sampling:
      enabled: false
```
