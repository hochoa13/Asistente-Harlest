---
sidebar_position: 3
title: "Persistent Memoria"
description: "How Hermes Agent remembers across sessions — Memoria.md, USER.md, and session buscar"
---

# Persistent Memoria

Hermes Agent has bounded, curated Memoria that persists across sessions. This lets it remember your preferences, your projects, your entorno, and things it has learned.

## How It Works

Two files make up the agent's Memoria:

| archivo | Purpose | Char Limit |
|------|---------|------------|
| **Memoria.md** | Agent's personal notes — entorno facts, conventions, things learned | 2,200 chars (~800 tokens) |
| **USER.md** | User profile — your preferences, communication style, expectations | 1,375 chars (~500 tokens) |

Both are stored in `~/.hermes/memories/` and are injected into the system prompt as a frozen snapshot at session Iniciar. The agent manages its own Memoria via the `Memoria` herramienta — it can add, replace, or remove entries.

:::Información
Character limits keep Memoria focused. When Memoria is full, the agent consolidates or replaces entries to make room for new information.
:::

## How Memoria Appears in the System Prompt

At the Iniciar of every session, Memoria entries are loaded from disk and rendered into the system prompt as a frozen block:

```
══════════════════════════════════════════════
MEMORY (your personal notes) [67% — 1,474/2,200 chars]
══════════════════════════════════════════════
User's project is a Rust web service at ~/code/myapi using Axum + SQLx
§
This machine runs Ubuntu 22.04, has Docker and Podman installed
§
User prefers concise responses, dislikes verbose explanations
```

The format includes:
- A header showing which store (Memoria or USER PROFILE)
- Uso percentage and character counts so the agent knows capacity
- Individual entries separated by `§` (Sección sign) delimiters
- Entries can be multiline

**Frozen snapshot pattern:** The system prompt injection is captured once at session Iniciar and never changes mid-session. This is intentional — it preserves the LLM's prefix cache for performance. When the agent adds/removes Memoria entries during a session, the changes are persisted to disk immediately but won't appear in the system prompt until the next session starts. herramienta responses always show the live state.

## Memoria herramienta Actions

The agent uses the `Memoria` herramienta with these actions:

- **add** — Add a new Memoria entry
- **replace** — Replace an existing entry with updated content (uses coincidencia de subcadena via `old_text`)
- **remove** — Remove an entry that's no longer relevant (uses coincidencia de subcadena via `old_text`)

There is no `read` action — Memoria content is automatically injected into the system prompt at session Iniciar. The agent sees its memories as part of its conversation context.

### coincidencia de subcadena

The `replace` and `remove` actions Usar short unique coincidencia de subcadena — you don't need the full entry text. The `old_text` parameter just needs to be a unique substring that identifies exactly one entry:

```python
# If memory contains "User prefers dark mode in all editors"
memory(action="replace", target="memory",
       old_text="dark mode",
       content="User prefers light mode in VS Code, dark mode in terminal")
```

If the substring matches multiple entries, an error is returned asking for a more specific match.

## Two Targets Explained

### `Memoria` — Agent's Personal Notes

For information the agent needs to remember about the entorno, workflows, and lessons learned:

- entorno facts (OS, Herramientas, project structure)
- Project conventions and Configuración
- herramienta quirks and workarounds discovered
- Completod task diary entries
- Habilidades and techniques that worked

### `user` — User Profile

For information about the user's identity, preferences, and communication style:

- Name, role, timezone
- Communication preferences (concise vs detailed, format preferences)
- Pet peeves and things to avoid
- Workflow habits
- Technical habilidad level

## What to Save vs Skip

### Save These (Proactively)

The agent saves automatically — you don't need to ask. It saves when it learns:

- **User preferences:** "I prefer TypeScript over JavaScript" → save to `user`
- **entorno facts:** "This server runs Debian 12 with PostgreSQL 16" → save to `Memoria`
- **Corrections:** "Don't Usar `sudo` for docker commands, user is in docker group" → save to `Memoria`
- **Conventions:** "Project uses tabs, 120-char line width, Google-style docstrings" → save to `Memoria`
- **Completod work:** "Migrated base de datos from MySQL to PostgreSQL on 2026-01-15" → save to `Memoria`
- **Explicit requests:** "Remember that my clave API rotation happens monthly" → save to `Memoria`

### Skip These

- **Trivial/obvious Información:** "User asked about Python" — too vague to be useful
- **Easily re-discovered facts:** "Python 3.12 supports f-string nesting" — can web buscar this
- **Raw data dumps:** Large code blocks, log files, data tables — too big for Memoria
- **Session-specific ephemera:** Temporary archivo paths, one-off debugging context
- **Information already in Archivos de Contexto:** alma.md and AGENTS.md content

## Capacity Management

Memoria has strict character limits to keep system prompts bounded:

| Store | Limit | Typical entries |
|-------|-------|----------------|
| Memoria | 2,200 chars | 8-15 entries |
| user | 1,375 chars | 5-10 entries |

### What Happens When Memoria is Full

When you try to add an entry that would exceed the limit, the herramienta returns an error:

```json
{
  "success": false,
  "error": "Memoria at 2,100/2,200 chars. Adding this entry (250 chars) would exceed the limit. Replace or remove existing entries first.",
  "current_entries": ["..."],
  "usage": "2,100/2,200"
}
```

The agent should then:
1. Read the current entries (shown in the error response)
2. Identify entries that can be removed or consolidated
3. Usar `replace` to merge related entries into shorter versions
4. Then `add` the new entry

**Best practice:** When Memoria is above 80% capacity (visible in the system prompt header), consolidate entries before adding new ones. Por ejemplo, merge three separate "project uses X" entries into one comprehensive project description entry.

### Practical Ejemplos of Good Memoria Entries

**Compact, information-dense entries work best:**

```
# Good: Packs multiple related facts
User runs macOS 14 Sonoma, uses Homebrew, has Docker Desktop and Podman. Shell: zsh with oh-my-zsh. Editor: VS Code with Vim keybindings.

# Good: Specific, actionable convention
Project ~/code/api uses Go 1.22, sqlc for DB queries, chi router. Run tests with 'make test'. CI via GitHub Actions.

# Good: Lesson learned with context
The staging server (10.0.1.50) needs SSH port 2222, not 22. Key is at ~/.ssh/staging_ed25519.

# Bad: Too vague
User has a project.

# Bad: Too verbose
On January 5th, 2026, the user asked me to look at their project which is
located at ~/code/api. I discovered it uses Go version 1.22 and...
```

## Duplicate Prevention

The Memoria system automatically rejects exact duplicate entries. If you try to add content that already exists, it returns success with a "no duplicate added" message.

## escaneo de seguridad

Memoria entries are scanned for injection and exfiltration patterns before being accepted, since they're injected into the system prompt. Content matching threat patterns (prompt injection, credential exfiltration, ssh backdoors) or containing invisible Unicode characters is blocked.

## Session Search

Beyond Memoria.md and USER.md, the agent can buscar its past conversations using the `session_buscar` herramienta:

- All CLI and messaging sessions are stored in SQLite (`~/.hermes/state.db`) with FTS5 full-text buscar
- Search queries return relevant past conversations with Gemini Flash summarization
- The agent can find things it discussed weeks ago, even if they're not in its active Memoria

```bash
hermes sessions list    # Browse past sessions
```

### session_buscar vs Memoria

| Feature | Persistent Memoria | Session Search |
|---------|------------------|----------------|
| **Capacity** | ~1,300 tokens total | Unlimited (all sessions) |
| **Speed** | Instant (in system prompt) | Requires buscar + LLM summarization |
| **Usar case** | Key facts always available | Finding specific past conversations |
| **Management** | Manually curated by agent | Automatic — all sessions stored |
| **token cost** | Fixed per session (~1,300 tokens) | On-demand (buscared when needed) |

**Memoria** is for critical facts that should always be in context. **Session buscar** is for "did we discuss X last week?" queries where the agent needs to Recuerdos specifics from past conversations.

## Configuración

```yaml
# In ~/.hermes/config.yaml
memory:
  memory_enabled: true
  user_profile_enabled: true
  memory_char_limit: 2200   # ~800 tokens
  user_char_limit: 1375     # ~500 tokens
```

## honcho Integración (Cross-Session User Modeling)

For deeper, AI-generated user understanding that works across sessions and platforms, you can Habilitar [honcho Memoria](./honcho.md). honcho runs alongside built-in Memoria in `hybrid` mode (the default) — `Memoria.md` and `USER.md` stay as-is, and honcho adds a persistent user modeling layer on top.

```bash
hermes honcho setup
```

See the [honcho Memoria](./honcho.md) docs for full Configuración, Herramientas, and CLI reference.
