---
sidebar_position: 1
title: "Herramientas & Herramientasets"
description: "Descripción General of Hermes Agent's Herramientas — what's available, how Conjuntos de herramientas work, and backends de terminal"
---

# Herramientas & Herramientasets

Herramientas are functions that extend the agent's capabilities. They're organized into logical **Conjuntos de herramientas** that can be enabled or disabled per platform.

## Available Herramientas

| Category | Herramientas | Description |
|----------|-------|-------------|
| **Web** | `web_buscar`, `web_extract` | Search the web, extract page content |
| **Terminal** | `terminal`, `process` | Execute commands (local/docker/singularity/modal/daytona/ssh backends), manage background processes |
| **archivo** | `read_file`, `write_file`, `patch`, `buscar_files` | Read, write, edit, and buscar files |
| **Navegador** | `browser_navigate`, `browser_click`, `browser_type`, `browser_console`, etc. | Full Navegador automation via Navegadorbase |
| **Visión** | `vision_analyze` | Análisis de Imágenes via multimodal models |
| **Image Gen** | `image_generate` | Generate images (FLUX via FAL) |
| **TTS** | `text_to_speech` | Texto a Voz (Edge TTS / ElevenLabs / OpenAI) |
| **Reasoning** | `mixture_of_agents` | Multi-model reasoning |
| **Habilidades** | `skills_list`, `skill_view`, `skill_manage` | Find, view, Crear, and manage Habilidades |
| **Todo** | `todo` | Read/write task list for multi-step planning |
| **Memoria** | `Memoria` | Persistent notes + user profile across sessions |
| **Session Search** | `session_buscar` | Search + summarize past conversations (FTS5) |
| **Cronjob** | `schedule_cronjob`, `list_cronjobs`, `remove_cronjob` | Scheduled task gestión |
| **Ejecución de Código** | `execute_code` | Ejecutar Python scripts that call Herramientas via RPC sandbox segura |
| **Delegación** | `delegate_task` | Spawn subagentes with isolated context |
| **Clarify** | `clarify` | Ask the user multiple-choice or open-ended questions |
| **MCP** | Auto-discovered | External Herramientas from MCP servers |

## Using Herramientasets

```bash
# Use specific toolsets
hermes chat --toolsets "web,terminal"

# See all available tools
hermes tools

# Configure tools per platform (interactive)
hermes tools
```

**Available Conjuntos de herramientas:** `web`, `terminal`, `archivo`, `Navegador`, `Visión`, `image_gen`, `moa`, `Habilidades`, `TTS`, `todo`, `Memoria`, `session_buscar`, `cronjob`, `code_execution`, `Delegación`, `clarify`, and more.

## backends de terminal

The terminal herramienta can execute commands in different environments:

| Backend | Description | Usar Case |
|---------|-------------|----------|
| `local` | Ejecutar on your machine (default) | Development, trusted tasks |
| `docker` | Isolated containers | Security, reproducibility |
| `ssh` | Remote server | Aislamiento en sandbox segura, keep agent away from its own code |
| `singularity` | HPC containers | Cluster computing, rootless |
| `modal` | Cloud execution | Serverless, scale |

### Configuración

```yaml
# In ~/.hermes/config.yaml
terminal:
  backend: local    # or: docker, ssh, singularity, modal, daytona
  cwd: "."          # Working directory
  timeout: 180      # Command timeout in seconds
```

### docker Backend

```yaml
terminal:
  backend: docker
  docker_image: python:3.11-slim
```

### ssh Backend

Recommended for security — agent can't modify its own code:

```yaml
terminal:
  backend: ssh
```
```bash
# Set credentials in ~/.hermes/.env
TERMINAL_SSH_HOST=my-server.example.com
TERMINAL_SSH_USER=myuser
TERMINAL_SSH_KEY=~/.ssh/id_rsa
```

### singularity/Apptainer

```bash
# Pre-build SIF for parallel workers
apptainer build ~/python.sif docker://python:3.11-slim

# Configure
hermes config set terminal.backend singularity
hermes config set terminal.singularity_image ~/python.sif
```

### modal (Serverless Cloud)

```bash
uv pip install "swe-rex[modal]"
modal setup
hermes config set terminal.backend modal
```

### Container Resources

Configurar CPU, Memoria, disk, and persistence for all container backends:

```yaml
terminal:
  backend: docker  # or singularity, modal, daytona
  container_cpu: 1              # CPU cores (default: 1)
  container_memory: 5120        # Memoria in MB (default: 5GB)
  container_disk: 51200         # Disk in MB (default: 50GB)
  container_persistent: true    # Persist filesystem across sessions (default: true)
```

When `container_persistent: true`, installed packages, files, and config survive across sessions.

### Container Security

All container backends Ejecutar with security hardening:

- Read-only root filesystem (docker)
- All Linux capabilities dropped
- No privilege escalation
- PID limits (256 processes)
- Full namespace isolation
- Persistent workspace via volumes, not writable root layer

## Background Process Management

Iniciar background processes and manage them:

```python
terminal(command="pytest -v tests/", background=true)
# Returns: {"session_id": "proc_abc123", "pid": 12345}

# Then manage with the process tool:
process(action="list")       # Show all running processes
process(action="poll", session_id="proc_abc123")   # Check status
process(action="wait", session_id="proc_abc123")   # Block until done
process(action="log", session_id="proc_abc123")    # Full output
process(action="kill", session_id="proc_abc123")   # Terminate
process(action="write", session_id="proc_abc123", data="y")  # Send input
```

PTY mode (`pty=true`) enables interactive CLI Herramientas like Codex and Claude Code.

## Sudo Support

If a comando needs sudo, you'll be prompted for your password (cached for the session). Or Establecer `SUDO_PASSWORD` in `~/.hermes/.env`.

:::Advertencia
On messaging platforms, if sudo fails, the output includes a Consejo to add `SUDO_PASSWORD` to `~/.hermes/.env`.
:::
