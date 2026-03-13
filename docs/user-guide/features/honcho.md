---
title: honcho Memoria
description: AI-native persistent Memoria for cross-session user modeling and personalization.
sidebar_label: honcho Memoria
sidebar_position: 8
---

# honcho Memoria

[honcho](https://honcho.dev) is an AI-native Memoria system that gives Hermes persistent, cross-session understanding of users. While Hermes has built-in Memoria (`Memoria.md` and `USER.md`), honcho adds a deeper layer of **user modeling** — learning preferences, goals, communication style, and context across conversations via a arquitectura de doble par where both the user and the AI build representations over time.

## Works Alongside Built-in Memoria

Hermes has two Memoria systems that can work together or be configured separately. In `hybrid` mode (the default), both Ejecutar side by side — honcho adds cross-session user modeling while local files handle agent-level notes.

| Feature | Built-in Memoria | honcho Memoria |
|---------|----------------|---------------|
| Storage | Local files (`~/.hermes/memories/`) | Cloud-hosted honcho API |
| Scope | Agent-level notes and user profile | Deep user modeling via dialectic reasoning |
| Persistence | Across sessions on same machine | Across sessions, machines, and platforms |
| consulta | Injected into system prompt automatically | Prefetched + on-demand via Herramientas |
| Content | Manually curated by the agent | Automatically learned from conversations |
| Write surface | `Memoria` herramienta (add/replace/remove) | `honcho_conclude` herramienta (persist facts) |

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

#### 2. Obtener an clave API

Go to [app.honcho.dev](https://app.honcho.dev) > Settings > claves API.

#### 3. Configurar

honcho reads from `~/.honcho/config.json` (shared across all honcho-enabled applications):

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

`apiKey` lives at the root because it is a shared credential across all honcho-enabled Herramientas. All other settings are scoped under `hosts.hermes`. The `hermes honcho Configuración` wizard writes this structure automatically.

Or Establecer the clave API as an entorno variable:

```bash
hermes config set HONCHO_API_KEY your-key
```

:::Información
When an clave API is present (either in `~/.honcho/config.json` or as `HONCHO_API_KEY`), honcho auto-enables unless explicitly Establecer to `"enabled": false`.
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

## How It Works

### contexto asincrónico tubería

honcho context is fetched asynchronously to avoid blocking the response ruta:

```
Turn N:
  user message
    → consume cached context (from previous turn's background fetch)
    → inject into system prompt (user representation, AI representation, dialectic)
    → LLM call
    → response
    → fire background fetch for next turn
         → fetch context    ─┐
         → fetch dialectic  ─┴→ cache for Turn N+1
```

Turn 1 is a cold Iniciar (no cache). All subsequent turns consume cached results with zero HTTP latency on the response ruta. The system prompt on turn 1 uses only static context to preserve prefix cache hits at the LLM provider.

### arquitectura de doble par

Both the user and AI have peer representations in honcho:

- **User peer** — observed from user messages. honcho learns preferences, goals, communication style.
- **AI peer** — observed from assistant messages (`observe_me=True`). honcho builds a representation of the agent's knowledge and behavior.

Both representations are injected into the system prompt when available.

### Dynamic Reasoning Level

Dialectic queries scale reasoning effort with message complexity:

| Message length | Reasoning level |
|----------------|-----------------|
| < 120 chars | Config default (typically `low`) |
| 120-400 chars | One level above default (cap: `high`) |
| > 400 chars | Two levels above default (cap: `high`) |

`max` is never selected automatically.

### Gateway Integración

The gateway creates short-lived `AIAgent` instances per request. honcho managers are owned at the gateway session layer (`_honcho_managers` dict) so they persist across requests within the same session and flush at real session boundaries (reset, reanudar, expiry, server Detener).

## Herramientas

When honcho is active, four Herramientas become available. Availability is gated dynamically — they are invisible when honcho is disabled.

### `honcho_profile`

Fast peer card retrieval (no LLM). Returns a curated list of key facts about the user.

### `honcho_buscar`

Semantic buscar over Memoria (no LLM). Returns raw excerpts ranked by relevance. Cheaper and faster than `honcho_context` — good for factual lookups.

Parámetros:
- `consulta` (string) — buscar consulta
- `max_tokens` (integer, optional) — result token budget

### `honcho_context`

Dialectic Q&A powered by honcho's LLM. Synthesizes an answer from accumulated conversation history.

Parámetros:
- `consulta` (string) — natural language question
- `peer` (string, optional) — `"user"` (default) or `"ai"`. Querying `"ai"` asks about the assistant's own history and identity.

Ejemplo queries the agent might make:

```
"What are this user's main goals?"
"What communication style does this user prefer?"
"What topics has this user discussed recently?"
"What is this user's technical expertise level?"
```

### `honcho_conclude`

Writes a fact to honcho Memoria. Usar when the user explicitly states a preference, correction, or project context worth remembering. Feeds into the user's peer card and representation.

Parámetros:
- `conclusion` (string) — the fact to persist

## CLI Commands

```
hermes honcho setup                        # Interactive setup wizard
hermes honcho status                       # Show config and connection status
hermes honcho sessions                     # List directory → session name mappings
hermes honcho map <name>                   # Map current directory to a session name
hermes honcho peer                         # Show peer names and dialectic settings
hermes honcho peer --user NAME             # Set user peer name
hermes honcho peer --ai NAME               # Set AI peer name
hermes honcho peer --reasoning LEVEL       # Set dialectic reasoning level
hermes honcho mode                         # Show current memory mode
hermes honcho mode [hybrid|honcho]         # Set memory mode
hermes honcho tokens                       # Show token budget settings
hermes honcho tokens --context N           # Set context token cap
hermes honcho tokens --dialectic N         # Set dialectic char cap
hermes honcho identity                     # Show AI peer identity
hermes honcho identity <file>              # Seed AI peer identity from file (SOUL.md, etc.)
hermes honcho migrate                      # Migración guide: OpenClaw → Hermes + Honcho
```

### Doctor Integración

`hermes doctor` includes a honcho Sección that validates config, clave API, and connection status.

## Migración

### From Local Memoria

When honcho activates on an instance with existing local history, migration runs automatically:

1. **Conversation history** — prior messages are uploaded as an XML transcript archivo
2. **Memoria files** — existing `Memoria.md`, `USER.md`, and `alma.md` are uploaded for context

### From OpenClaw

```bash
hermes honcho migrate
```

Walks through converting an OpenClaw native honcho Configuración to the shared `~/.honcho/config.json` format.

## AI Peer Identity

honcho can build a representation of the AI assistant over time (via `observe_me=True`). You can also seed the AI peer explicitly:

```bash
hermes honcho identity ~/.hermes/SOUL.md
```

This uploads the archivo content through honcho's observation tubería. The AI peer representation is then injected into the system prompt alongside the user's, giving the agent awareness of its own accumulated identity.

```bash
hermes honcho identity --show
```

Shows the current AI peer representation from honcho.

## Usar Cases

- **Personalized responses** — honcho learns how each user prefers to communicate
- **Goal seguimiento** — remembers what users are working toward across sessions
- **Expertise adaptation** — adjusts technical depth based on user's background
- **Cross-platform Memoria** — same user understanding across CLI, Telegram, Discord, etc.
- **Multi-user support** — each user (via messaging platforms) gets their own user model

:::Consejo
honcho is fully opt-in — zero behavior change when disabled or unconfigured. All honcho calls are non-fatal; if the service is unreachable, the agent continues normally.
:::
