---
title: Memoria honcho
description: Sistema de memoria nativo de IA para modelado de usuario persistente entre sesiones y personalización.
sidebar_label: Memoria honcho
sidebar_position: 8
---

# Memoria honcho

[honcho](https://honcho.dev) es un sistema de memoria nativo de IA que le da a Hermes comprensión persistente entre sesiones de los usuarios. Mientras que Hermes tiene memoria incorporada (`memory.md` y `USER.md`), honcho añade una capa más profunda de **modelado de usuario** — aprendiendo preferencias, objetivos, estilo de comunicación y contexto entre conversaciones a través de una arquitectura de par dialecto donde tanto el usuario como la IA construyen representaciones a lo largo del tiempo.

## Trabaja Junto con Memoria Incorporada

Hermes tiene dos sistemas de memoria que pueden trabajar juntos o configurarse por separado. En modo `hybrid` (el predeterminado), ambos se ejecutan lado a lado — honcho añade modelado de usuario entre sesiones mientras que los archivos locales manejan notas a nivel de agente.

| Caracter\u00edstica | Memoria Incorporada | Memoria honcho |
|---------|----------------|----------------|\n| Almacenamiento | Archivos locales (`~/.hermes/memories/`) | API honcho alojada en la nube |
| Alcance | Notas a nivel de agente y perfil de usuario | Modelado de usuario profundo a trav\u00e9s de razonamiento dial\u00e9ctico |
| Persistencia | Entre sesiones en la misma m\u00e1quina | Entre sesiones, m\u00e1quinas y plataformas |
| Consulta | Inyectada en indicador del sistema autom\u00e1ticamente | Precargada + bajo demanda a trav\u00e9s de herramientas |
| Contenido | Curado manualmente por el agente | Aprendido autom\u00e1ticamente de conversaciones |
| Superficie de escritura | Herramienta `memory` (agregar/reemplazar/eliminar) | Herramienta `honcho_conclude` (persistir hechos) |

Establecer `memoryMode` to `honcho` to Usar honcho exclusively. See [Memoria Modes](#Memoria-modes) for per-peer Configuración.


## Configuración

### Interactive Configuración

```bash
hermes honcho setup
```

The Configuración wizard walks through clave API, peer names, workspace, Memoria mode, write frequency, Recuerdos mode, and session strategy. It offers to Instalar `honcho-ai` if missing.

### Manual Configuración

#### 1. Instalar the Client Library

```bash
pip install 'honcho-ai>=2.0.1'
```

#### 2. Obtener una Clave API

Ve a [app.honcho.dev](https://app.honcho.dev) > Settings > API Keys.

#### 3. Configurar

honcho lee desde `~/.honcho/config.json` (compartido en todas las aplicaciones habilitadas para honcho):

```json
{
  "apiKey": "your-honcho-api-key",
  "hosts": {
    "hermes": {
      "workspace": "hermes",
      "peerName": "your-name",
      "aiPeer": "hermes",
      "memoryMode": "hybrid",
      "writeFrequency": "async",
      "recallMode": "hybrid",
      "sessionStrategy": "per-session",
      "enabled": true
    }
  }
}
```

`apiKey` vive en la raíz porque es una credencial compartida en todas las herramientas habilitadas para honcho. Todas las otras configuraciones están alcanzadas bajo `hosts.hermes`. El asistente `hermes honcho setup` escribe esta estructura automáticamente.

O establece la clave API como variable de entorno:

```bash
hermes config set HONCHO_API_KEY your-key
```

:::información
Cuando una clave API está presente (ya sea en `~/.honcho/config.json` o como `HONCHO_API_KEY`), honcho auto-habilita a menos que se establezca explícitamente a `"enabled": false`.
:::

## Configuración

### Global Config (`~/.honcho/config.json`)

Settings are scoped to `hosts.hermes` and fall back to root-level globals when the host field is absent. Root-level keys are managed by the user or the honcho CLI -- Hermes only writes to its own host block (except `apiKey`, which is a shared credential at root).

**Root-level (shared)**

| Field | Default | Description |
|-------|---------|-------------|
| `apiKey` | — | honcho clave API (required, shared across all hosts) |
| `sessions` | `{}` | Manual session name overrides per directorio (shared) |

**Host-level (`hosts.hermes`)**

| Field | Default | Description |
|-------|---------|-------------|
| `workspace` | `"hermes"` | Workspace identifier |
| `peerName` | *(derived)* | Your identity name for user modeling |
| `aiPeer` | `"hermes"` | AI assistant identity name |
| `entorno` | `"production"` | honcho entorno |
| `enabled` | *(auto)* | Auto-enables when clave API is present |
| `saveMessages` | `true` | Whether to sync messages to honcho |
| `memoryMode` | `"hybrid"` | Memoria mode: `hybrid` or `honcho` |
| `writeFrequency` | `"async"` | When to write: `async`, `turn`, `session`, or integer N |
| `recallMode` | `"hybrid"` | Retrieval strategy: `hybrid`, `context`, or `Herramientas` |
| `sessionStrategy` | `"per-session"` | How sessions are scoped |
| `sessionPeerPrefix` | `false` | Prefix session names with peer name |
| `contextTokens` | *(honcho default)* | Max tokens for auto-injected context |
| `dialecticReasoningLevel` | `"low"` | Floor for dialectic reasoning: `minimal` / `low` / `medium` / `high` / `max` |
| `dialecticMaxChars` | `600` | Char cap on dialectic results injected into system prompt |
| `linkedHosts` | `[]` | Other host keys whose workspaces to cross-reference |

All host-level fields fall back to the equivalent root-level key if not Establecer under `hosts.hermes`. Existing configs with settings at root level continue to work.

### Memoria Modes

| Mode | Effect |
|------|--------|
| `hybrid` | Write to both honcho and local files (default) |
| `honcho` | honcho only — skip local archivo writes |

Memoria mode can be Establecer globally or per-peer (user, agent1, agent2, etc):

```json
{
  "memoryMode": {
    "default": "hybrid",
    "hermes": "honcho"
  }
}
```

To Deshabilitar honcho entirely, Establecer `enabled: false` or remove the clave API.

### Recuerdos Modes

Controls how honcho context reaches the agent:

| Mode | Behavior |
|------|----------|
| `hybrid` | Auto-injected context + honcho Herramientas available (default) |
| `context` | Auto-injected context only — honcho Herramientas hidden |
| `Herramientas` | honcho Herramientas only — no auto-injected context |

### Write Frequency

| Setting | Behavior |
|---------|----------|
| `async` | Background thread writes (zero blocking, default) |
| `turn` | Synchronous write after each turn |
| `session` | Batched write at session end |
| *integer N* | Write every N turns |

### Session Strategies

| Strategy | Session key | Usar case |
|----------|-------------|----------|
| `per-session` | Unique per Ejecutar | Default. Fresh session every time. |
| `per-directorio` | CWD basename | Each project gets its own session. |
| `per-repo` | Git repo root name | Groups subdirectories under one session. |
| `global` | Fixed `"global"` | Single cross-project session. |

Resolution order: manual map > session title > strategy-derived key > platform key.

### Multi-host Configuración

Multiple honcho-enabled Herramientas share `~/.honcho/config.json`. Each herramienta writes only to its own host block, reads its host block first, and falls back to root-level globals:

```json
{
  "apiKey": "your-key",
  "peerName": "eri",
  "hosts": {
    "hermes": {
      "workspace": "my-workspace",
      "aiPeer": "hermes-assistant",
      "memoryMode": "honcho",
      "linkedHosts": ["claude-code"],
      "contextTokens": 2000,
      "dialecticReasoningLevel": "medium"
    },
    "claude-code": {
      "workspace": "my-workspace",
      "aiPeer": "clawd"
    }
  }
}
```

Resolution: `hosts.<herramienta>` field > root-level field > default. In this Ejemplo, both Herramientas share the root `apiKey` and `peerName`, but each has its own `aiPeer` and workspace settings.

### Hermes Config (`~/.hermes/config.yaml`)

Intentionally minimal — most Configuración comes from `~/.honcho/config.json`:

```yaml
honcho: {}
```

## Cómo Funciona

### Tubería de Contexto Asincrónico

El contexto de honcho se obtiene de forma asincrónica para evitar bloquear la ruta de respuesta:

```
Giro N:
  mensaje del usuario
    → consume contexto en caché (de la obtención en segundo plano del giro anterior)
    → inyecta en indicador del sistema (representación del usuario, representación de IA, dialéctico)
    → llamada LLM
    → respuesta
    → dispara obtención en segundo plano para el próximo giro
         → obtiene contexto    ─┐
         → obtiene dialéctico  ─┴→ en caché para Giro N+1
```

El Giro 1 es un inicio frío (sin caché). Todos los giros posteriores consumen resultados en caché con cero latencia HTTP en la ruta de respuesta. El indicador del sistema en el giro 1 usa solo contexto estático para preservar hits de caché de prefijo en el proveedor LLM.

### Arquitectura de Doble Par

Tanto el usuario como la IA tienen representaciones de pares en honcho:

- **Par de usuario** — observado a partir de mensajes del usuario. honcho aprende preferencias, objetivos, estilo de comunicación.
- **Par de IA** — observado a partir de mensajes del asistente (`observe_me=True`). honcho construye una representación del conocimiento y comportamiento del agente.

Ambas representaciones se inyectan en el indicador del sistema cuando están disponibles.

### Nivel de Razonamiento Dinámico

Las consultas dialécticas escalan el esfuerzo de razonamiento con la complejidad del mensaje:

| Longitud del mensaje | Nivel de razonamiento |
|----------------|-----------------|
| < 120 caracteres | Predeterminado de configuración (típicamente `low`) |
| 120-400 caracteres | Un nivel por encima del predeterminado (límite: `high`) |
| > 400 caracteres | Dos niveles por encima del predeterminado (límite: `high`) |

Nunca se selecciona `max` automáticamente.

### Integración Gateway

La puerta de enlace crea instancias `AIAgent` de corta duración por solicitud. Los gestores de honcho son propiedad de la capa de sesión de la puerta de enlace (diccionario `_honcho_managers`) para que persistan en las solicitudes dentro de la misma sesión y se limpien en límites de sesión reales (reinicio, reanudación, expiración, parada del servidor).

## Herramientas

Cuando honcho está activo, cuatro herramientas están disponibles. La disponibilidad se controla dinámicamente — son invisibles cuando honcho está deshabilitado.

### `honcho_profile`

Retrieval de tarjeta de pares rápido (sin LLM). Devuelve una lista curada de hechos clave sobre el usuario.

### `honcho_search`

Búsqueda semántica sobre la Memoria (sin LLM). Devuelve fragmentos sin procesar clasificados por relevancia. Más barato y más rápido que `honcho_context` — bueno para búsquedas fácticas.

Parámetros:
- `query` (string) — consulta de búsqueda
- `max_tokens` (integer, opcional) — presupuesto de tokens de resultado

### `honcho_context`

Pregunta y respuesta dialéctica impulsada por el LLM de honcho. Sintetiza una respuesta a partir del historial de conversación acumulado.

Parámetros:
- `query` (string) — pregunta en lenguaje natural
- `peer` (string, opcional) — `"user"` (predeterminado) o `"ai"`. Consultar `"ai"` pregunta sobre el historial e identidad propios del asistente.

Ejemplos de consultas que el agente podría hacer:

```
"¿Cuáles son los objetivos principales de este usuario?"
"¿Qué estilo de comunicación prefiere este usuario?"
"¿Qué temas ha discutido recientemente este usuario?"
"¿Cuál es el nivel de pericia técnica de este usuario?"
```

### `honcho_conclude`

Escribe un hecho en la Memoria de honcho. Usa cuando el usuario afirma explícitamente una preferencia, corrección o contexto de proyecto que vale la pena recordar. Se alimenta en la tarjeta de pares del usuario y la representación.

Parámetros:
- `conclusion` (string) — el hecho a persistir

## Comandos CLI

```
hermes honcho setup                        # Asistente de configuración interactivo
hermes honcho status                       # Mostrar estado de configuración y conexión
hermes honcho sessions                     # Listar asignaciones de directorio → nombre de sesión
hermes honcho map <name>                   # Asignar directorio actual a un nombre de sesión
hermes honcho peer                         # Mostrar nombres de pares y configuración dialéctica
hermes honcho peer --user NAME             # Establecer nombre de par de usuario
hermes honcho peer --ai NAME               # Establecer nombre de par de IA
hermes honcho peer --reasoning LEVEL       # Establecer nivel de razonamiento dialéctico
hermes honcho mode                         # Mostrar modo de memoria actual
hermes honcho mode [hybrid|honcho]         # Establecer modo de memoria
hermes honcho tokens                       # Mostrar configuración de presupuesto de tokens
hermes honcho tokens --context N           # Establecer límite de token de contexto
hermes honcho tokens --dialectic N         # Establecer límite de caracteres dialéctico
hermes honcho identity                     # Mostrar identidad de par de IA
hermes honcho identity <file>              # Sembrar identidad de par de IA desde archivo (SOUL.md, etc.)
hermes honcho migrate                      # Guía de migración: OpenClaw → Hermes + Honcho
```

### Integración Doctor

`hermes doctor` incluye una sección honcho que valida configuración, clave API y estado de conexión.

## Migración

### Desde Memoria Local

Cuando honcho se activa en una instancia con historial local existente, la migración se ejecuta automáticamente:

1. **Historial de conversación** — los mensajes anteriores se cargan como un archivo de transcripción XML
2. **Archivos de Memoria** — `Memoria.md`, `USER.md` y `alma.md` existentes se cargan para contexto

### Desde OpenClaw

```bash
hermes honcho migrate
```

Guida a través de la conversión de una configuración nativa de honcho de OpenClaw al formato `~/.honcho/config.json` compartido.

## Identidad de Par de IA

honcho puede construir una representación del asistente de IA a lo largo del tiempo (a través de `observe_me=True`). También puedes sembrar el par de IA explícitamente:

```bash
hermes honcho identity ~/.hermes/SOUL.md
```

Esto carga el contenido del archivo a través de la tubería de observación de honcho. La representación del par de IA se inyecta entonces en el indicador del sistema junto con la del usuario, dando al agente conciencia de su identidad acumulada propia.

```bash
hermes honcho identity --show
```

Muestra la representación actual del par de IA de honcho.

## Casos de Uso

- **Respuestas personalizadas** — honcho aprende cómo cada usuario prefiere comunicarse
- **Seguimiento de objetivos** — recuerda en qué están trabajando los usuarios entre sesiones
- **Adaptación de pericia** — ajusta la profundidad técnica según la historia del usuario
- **Memoria entre plataformas** — el mismo conocimiento del usuario en CLI, Telegram, Discord, etc.
- **Soporte multiusuario** — cada usuario (a través de plataformas de mensajería) obtiene su propio modelo de usuario

:::tip
honcho es completamente opcional — cero cambio de comportamiento cuando está deshabilitado o sin configurar. Todas las llamadas a honcho no son fatales; si el servicio no es accesible, el agente continúa normalmente.
:::
