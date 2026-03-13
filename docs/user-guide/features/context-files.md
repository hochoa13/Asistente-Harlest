---
sidebar_position: 8
title: "Archivos de Contexto"
description: "Project Archivos de Contexto — AGENTS.md, alma.md, and .cursorrules — automatically injected into every conversation"
---

# Archivos de Contexto

Hermes Agent automatically discovers and loads project Archivos de Contexto from your working directorio. These files are injected into the system prompt at the Iniciar of every session, giving the agent persistent knowledge about your project's conventions, architecture, and preferences.

## Supported Archivos de Contexto

| archivo | Purpose | Discovery |
|------|---------|-----------|
| **AGENTS.md** | Project instructions, conventions, architecture | Recursive (walks subdirectories) |
| **alma.md** | Personalidad and tone customization | CWD → `~/.hermes/alma.md` fallback |
| **.cursorrules** | Cursor IDE coding conventions | CWD only |
| **.cursor/rules/*.mdc** | Cursor IDE rule modules | CWD only |

## AGENTS.md

`AGENTS.md` is the primary project context archivo. It tells the agent how your project is structured, what conventions to follow, and any special instructions.

### descubrimiento jerárquico

Hermes walks the directorio tree starting from the working directorio and loads **all** `AGENTS.md` files found, sorted by depth. This supports monorepo-style setups:

```
my-project/
├── AGENTS.md              ← Top-level project context
├── frontend/
│   └── AGENTS.md          ← Frontend-specific instructions
├── backend/
│   └── AGENTS.md          ← Backend-specific instructions
└── shared/
    └── AGENTS.md          ← Shared library conventions
```

All four files are concatenated into a single context block with relative ruta headers.

:::Información
Directories that are skipped during the walk: `.`-prefixed dirs, `node_modules`, `__pycache__`, `venv`, `.venv`.
:::

### Ejemplo AGENTS.md

```markdown
# Project Context

This is a Next.js 14 web application with a Python FastAPI backend.

## Architecture
- Frontend: Next.js 14 with App Router in `/frontend`
- Backend: FastAPI in `/backend`, uses SQLAlchemy ORM
- Database: PostgreSQL 16
- Deployment: Docker Compose on a Hetzner VPS

## Conventions
- Use TypeScript strict mode for all frontend code
- Python code follows PEP 8, use type hints everywhere
- All API endpoints return JSON with `{data, error, meta}` shape
- Tests go in `__tests__/` directories (frontend) or `tests/` (backend)

## Important Notes
- Never modify migration files directly — use Alembic commands
- The `.env.local` file has real API keys, don't commit it
- Frontend port is 3000, backend is 8000, DB is 5432
```

## alma.md

`alma.md` controls the agent's Personalidad, tone, and communication style. See the [Personalidad](/docs/user-guide/features/Personalidad) page for full details.

**Discovery order:**

1. `alma.md` or `alma.md` in the current working directorio
2. `~/.hermes/alma.md` (global fallback)

When a alma.md is found, the agent is instructed:

> *"If alma.md is present, embody its persona and tone. Avoid stiff, generic replies; follow its guidance unless higher-priority instructions override it."*

## .cursorrules

Hermes is compatible with Cursor IDE's `.cursorrules` archivo and `.cursor/rules/*.mdc` rule modules. If these files exist in your project root, they're loaded alongside AGENTS.md.

This means your existing Cursor conventions automatically apply when using Hermes.

## How Archivos de Contexto Are Loaded

Archivos de Contexto are loaded by `build_context_files_prompt()` in `agent/prompt_builder.py`:

1. **At session Iniciar** — the function scans the working directorio
2. **Content is read** — each archivo is read as UTF-8 text
3. **Security scan** — content is checked for prompt injection patterns
4. **Truncation** — files exceeding 20,000 characters are head/tail truncated (70% head, 20% tail, with a marker in the middle)
5. **Assembly** — all sections are combined under a `# Project Context` header
6. **Injection** — the assembled content is added to the system prompt

The final prompt Sección looks like:

```
# Project Context

The following project context files have been loaded and should be followed:

## AGENTS.md

[Your AGENTS.md content here]

## .cursorrules

[Your .cursorrules content here]

## SOUL.md

If SOUL.md is present, embody its persona and tone...

[Your SOUL.md content here]
```

## Security: Prompt Injection Protection

All Archivos de Contexto are scanned for potential prompt injection before being included. The scanner checks for:

- **Instruction override attempts**: "ignorar previous instructions", "disregard your rules"
- **Deception patterns**: "do not tell the user"
- **System prompt overrides**: "system prompt override"
- **Hidden HTML comments**: `<!-- ignorar instructions -->`
- **Hidden div elements**: `<div style="display:none">`
- **Credential exfiltration**: `curl ... $API_KEY`
- **Secret archivo access**: `cat .env`, `cat credenciales`
- **Invisible characters**: zero-width spaces, bidirectional overrides, word joiners

If any threat pattern is detected, the archivo is blocked:

```
[BLOCKED: AGENTS.md contained potential prompt injection (prompt_injection). Content not loaded.]
```

:::Advertencia
This scanner protects against common injection patterns, but it's not a substitute for reviewing Archivos de Contexto in shared repositories. Always validate AGENTS.md content in projects you didn't author.
:::

## Size Limits

| Limit | Value |
|-------|-------|
| Max chars per archivo | 20,000 (~7,000 tokens) |
| Head truncation ratio | 70% |
| Tail truncation ratio | 20% |
| Truncation marker | 10% (shows char counts and suggests using archivo Herramientas) |

When a archivo exceeds 20,000 characters, the truncation message reads:

```
[...truncated AGENTS.md: kept 14000+4000 of 25000 chars. Use file tools to read the full file.]
```

## Consejos for Effective Archivos de Contexto

:::Consejo Mejores prácticas for AGENTS.md
1. **Keep it concise** — stay well under 20K chars; the agent reads it every turn
2. **Structure with headers** — Usar `##` sections for architecture, conventions, Importante notes
3. **Include concrete Ejemplos** — show preferred code patterns, API shapes, naming conventions
4. **Mention what NOT to do** — "never modify migration files directly"
5. **List key paths and ports** — the agent uses these for terminal commands
6. **Update as the project evolves** — stale context is worse than no context
:::

### Per-Subdirectory Context

For monorepos, put subdirectory-specific instructions in nested AGENTS.md files:

```markdown
<!-- frontend/AGENTS.md -->
# Frontend Context

- Use `pnpm` not `npm` for package gestión
- Components go in `src/components/`, pages in `src/app/`
- Use Tailwind CSS, never inline styles
- Run tests with `pnpm test`
```

```markdown
<!-- backend/AGENTS.md -->
# Backend Context

- Use `poetry` for dependency gestión
- Run the dev server with `poetry run uvicorn main:app --reload`
- All endpoints need OpenAPI docstrings
- Database models are in `models/`, schemas in `schemas/`
```
