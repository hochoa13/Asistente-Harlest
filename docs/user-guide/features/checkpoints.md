# Filesystem Puntos de control

Hermes can automatically snapshot your working directorio before making archivo changes, giving you a safety net to roll back if something goes wrong.

## How It Works

When enabled, Hermes takes a **one-time snapshot** at the Iniciar of each conversation turn before the first archivo-modifying operation (`write_file` or `patch`). This creates a point-in-time backup you can restore to at any time.

Under the hood, Puntos de control Usar a **shadow git repository** stored at `~/.hermes/Puntos de control/`. This is completely separate from your project's git — no `.git` directorio is created in your project, and your own git history is never touched.

## Enabling Puntos de control

### Per-session (CLI flag)

```bash
hermes --checkpoints
```

### Permanently (config.yaml)

```yaml
# ~/.hermes/config.yaml
checkpoints:
  enabled: true
  max_snapshots: 50  # max checkpoints per directory (default: 50)
```

## Rolling Back

Usar the `/Deshacer` slash comando:

```
/rollback          # List all available checkpoints
/rollback 1        # Restore to checkpoint #1 (most recent)
/rollback 3        # Restore to checkpoint #3 (further back)
/rollback abc1234  # Restore by git commit hash
```

Ejemplo output:

```
📸 Puntos de Control for /home/user/project:

  1. abc1234  2026-03-10 14:22  before write_file
  2. def5678  2026-03-10 14:15  before patch
  3. ghi9012  2026-03-10 14:08  before write_file

Use /rollback <number> to restore, e.g. /rollback 1
```

When you restore, Hermes automatically takes a **pre-Deshacer snapshot** first — so you can always undo your undo.

## What Gets Checkpointed

Puntos de control capture the entire working directorio (the project root), excluding common large/sensitive patterns:

- `node_modules/`, `dist/`, `build/`
- `.env`, `.env.*`
- `__pycache__/`, `*.pyc`
- `.venv/`, `venv/`
- `.git/`
- `.DS_Store`, `*.log`

## Performance

Puntos de control are designed to be lightweight:

- **Once per turn** — only the first archivo operation triggers a snapshot, not every write
- **Skips large directories** — directories with >50,000 files are skipped automatically
- **Skips when nothing changed** — if no files were modified since the last punto de control, no commit is created
- **Non-blocking** — if a punto de control fails for any reason, the archivo operation proceeds normally

## How It Determines the Project Root

When you write to a archivo like `src/components/Button.tsx`, Hermes walks up the directorio tree looking for project markers (`.git`, `pyproject.toml`, `package.json`, `Cargo.toml`, etc.) to find the project root. This ensures the entire project is checkpointed, not just the archivo's parent directorio.

## Platforms

Puntos de control work on both:
- **CLI** — uses your current working directorio
- **Gateway** (Telegram, Discord, etc.) — uses `MESSAGING_CWD`

The `/Deshacer` comando is available on all platforms.

## Preguntas frecuentes

**Does this conflict with my project's git?**
No. Puntos de control Usar a completely separate shadow git repository via `GIT_DIR` entorno variables. Your project's `.git/` is never touched.

**How much disk space do Puntos de control Usar?**
Git is very efficient at storing diffs. For most projects, punto de control data is negligible. Old Puntos de control are pruned when `max_snapshots` is exceeded.

**Can I punto de control without git installed?**
No — git must be available on your ruta. If it's not installed, Puntos de control silently Deshabilitar.

**Can I roll back across sessions?**
Yes! Puntos de control persist in `~/.hermes/Puntos de control/` and survive across sessions. You can roll back to a punto de control from yesterday.
