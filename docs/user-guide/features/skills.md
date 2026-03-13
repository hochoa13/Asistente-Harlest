---
sidebar_position: 2
title: "Habilidades System"
description: "On-demand knowledge documents — divulgación progresiva, agent-managed Habilidades, and the Habilidades Hub"
---

# Habilidades System

Habilidades are on-demand knowledge documents the agent can load when needed. They follow a **divulgación progresiva** pattern to minimize token Uso and are compatible with the [agentskills.io](https://agentskills.io/specification) open standard.

All Habilidades live in **`~/.hermes/Habilidades/`** — a single directorio that serves as the source of truth. On fresh Instalar, bundled Habilidades are copied from the repo. Hub-installed and agent-created Habilidades also go here. The agent can modify or delete any habilidad.

## Using Habilidades

Every installed habilidad is automatically available as a slash comando:

```bash
# In the CLI or any messaging platform:
/gif-buscar funny cats
/axolotl help me fine-tune Llama 3 on my dataset
/github-pr-workflow create a PR for the auth refactor

# Just the skill name loads it and lets the agent ask what you need:
/excalidraw
```

You can also interact with Habilidades through natural conversation:

```bash
hermes chat --toolsets skills -q "What skills do you have?"
hermes chat --toolsets skills -q "Show me the axolotl skill"
```

## divulgación progresiva

Habilidades Usar a token-efficient loading pattern:

```
Level 0: skills_list()           → [{name, description, category}, ...]   (~3k tokens)
Level 1: skill_view(name)        → Full content + metadata       (varies)
Level 2: skill_view(name, path)  → Specific reference file       (varies)
```

The agent only loads the full habilidad content when it actually needs it.

## formato habilidad.md

```markdown
---
name: my-skill
description: Brief description of what this skill does
version: 1.0.0
platforms: [macos, linux]     # Optional — restrict to specific OS platforms
metadata:
  hermes:
    tags: [python, automation]
    category: devops
    fallback_for_toolsets: [web]    # Optional — conditional activation (see below)
    requires_toolsets: [terminal]   # Optional — conditional activation (see below)
---

# Skill Title

## When to Use
Trigger conditions for this skill.

## Procedure
1. Step one
2. Step two

## Pitfalls
- Known failure modes and fixes

## Verification
Cómo confirm it worked.
```

### específico de plataforma Habilidades

Habilidades can restrict themselves to specific operating systems using the `platforms` field:

| Value | Matches |
|-------|---------|
| `macos` | macOS (Darwin) |
| `linux` | Linux |
| `windows` | Windows |

```yaml
platforms: [macos]            # macOS only (e.g., iMessage, Apple Reminders, FindMy)
platforms: [macos, linux]     # macOS and Linux
```

When Establecer, the habilidad is automatically hidden from the system prompt, `skills_list()`, and slash commands on incompatible platforms. If omitted, the habilidad loads on all platforms.

### activación condicional (fallback Habilidades)

Habilidades can automatically show or hide themselves based on which Herramientas are available in the current session. This is most useful for **fallback Habilidades** — free or local alternatives that should only appear when a premium herramienta is unavailable.

```yaml
metadata:
  hermes:
    fallback_for_toolsets: [web]      # Show ONLY when these toolsets are unavailable
    requires_toolsets: [terminal]     # Show ONLY when these toolsets are available
    fallback_for_tools: [web_buscar]  # Show ONLY when these specific tools are unavailable
    requires_tools: [terminal]        # Show ONLY when these specific tools are available
```

| Field | Behavior |
|-------|----------|
| `fallback_for_toolsets` | habilidad is **hidden** when the listed Conjuntos de herramientas are available. Shown when they're missing. |
| `fallback_for_tools` | Same, but checks individual Herramientas instead of Conjuntos de herramientas. |
| `requires_toolsets` | habilidad is **hidden** when the listed Conjuntos de herramientas are unavailable. Shown when they're present. |
| `requires_tools` | Same, but checks individual Herramientas. |

**Ejemplo:** The built-in `duckduckgo-buscar` habilidad uses `fallback_for_toolsets: [web]`. When you have `FIRECRAWL_API_KEY` Establecer, the web conjunto de herramientas is available and the agent uses `web_buscar` — the DuckDuckGo habilidad stays hidden. If the clave API is missing, the web conjunto de herramientas is unavailable and the DuckDuckGo habilidad automatically appears as a fallback.

Habilidades without any conditional fields behave exactly as before — they're always shown.

## habilidad directorio Structure

```
~/.hermes/skills/                  # Single source of truth
├── mlops/                         # Category directory
│   ├── axolotl/
│   │   ├── SKILL.md               # Main instructions (required)
│   │   ├── references/            # Additional docs
│   │   ├── templates/             # Output formats
│   │   └── assets/                # Supplementary files
│   └── vllm/
│       └── SKILL.md
├── devops/
│   └── deploy-k8s/                # Agent-created skill
│       ├── SKILL.md
│       └── references/
├── .hub/                          # Habilidades Hub state
│   ├── lock.json
│   ├── quarantine/
│   └── audit.log
└── .bundled_manifest              # Tracks seeded bundled skills
```

## Agent-Managed Habilidades (skill_manage herramienta)

The agent can Crear, update, and delete its own Habilidades via the `skill_manage` herramienta. This is the agent's **procedural Memoria** — when it figures out a non-trivial workflow, it saves the approach as a habilidad for future reuse.

### When the Agent Creates Habilidades

- After completing a complex task (5+ Llamadas de Herramientas) successfully
- When it hit errors or dead ends and found the working ruta
- When the user corrected its approach
- When it discovered a non-trivial workflow

### Actions

| Action | Usar for | Key params |
|--------|---------|------------|
| `Crear` | New habilidad from scratch | `name`, `content` (full habilidad.md), optional `category` |
| `patch` | Targeted fixes (preferred) | `name`, `old_string`, `new_string` |
| `edit` | Major structural rewrites | `name`, `content` (full habilidad.md replacement) |
| `delete` | Remove a habilidad entirely | `name` |
| `write_file` | Add/update supporting files | `name`, `file_path`, `file_content` |
| `remove_file` | Remove a supporting archivo | `name`, `file_path` |

:::Consejo
The `patch` action is preferred for updates — it's more token-efficient than `edit` because only the changed text appears in the herramienta call.
:::

## Habilidades Hub

Browse, buscar, Instalar, and manage Habilidades from online registries and official optional Habilidades:

```bash
hermes skills browse                     # Browse all hub skills (official first)
hermes skills browse --source official   # Browse only official optional skills
hermes skills buscar kubernetes          # Search all sources
hermes skills install openai/skills/k8s  # Install with security scan
hermes skills inspect openai/skills/k8s  # Preview before installing
hermes skills list --source hub          # List hub-installed skills
hermes skills audit                      # Re-scan all hub skills
hermes skills uninstall k8s              # Remove a hub skill
hermes skills publish skills/my-skill --to github --repo owner/repo
hermes skills snapshot export setup.json # Export skill config
hermes skills tap add myorg/skills-repo  # Add a custom source
```

All hub-installed Habilidades go through a **security scanner** that checks for data exfiltration, prompt injection, destructive commands, and other threats.

### Trust Levels

| Level | Source | política |
|-------|--------|--------|
| `builtin` | Ships with Hermes | Always trusted |
| `official` | `optional-Habilidades/` in the repo | Builtin trust, no third-party Advertencia |
| `trusted` | openai/Habilidades, anthropics/Habilidades | Trusted sources |
| `community` | Everything else | Any findings = blocked unless `--force` |

### Slash Commands (Inside Chat)

All the same commands work with `/Habilidades` prefix:

```
/skills browse
/skills buscar kubernetes
/skills install openai/skills/skill-creator
/skills list
```
