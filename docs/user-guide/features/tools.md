---
sidebar_position: 1
title: "Herramientas y Conjuntos de Herramientas"
description: "Descripción General de las Herramientas de Hermes Agent — qué hay disponible, cómo funcionan los conjuntos de herramientas y backends de terminal"
---

# Herramientas y Conjuntos de Herramientas

Las Herramientas son funciones que amplían las capacidades del agente. Se organizan en **Conjuntos de Herramientas** lógicos que se pueden habilitar o deshabilitar por plataforma.

## Herramientas Disponibles

| Categoría | Herramientas | Descripción |
|----------|-------|-------------|
| **Web** | `web_search`, `web_extract` | Busca en la web, extrae contenido de página |
| **Terminal** | `terminal`, `process` | Ejecuta comandos (backends local/docker/singularity/modal/daytona/ssh), gestiona procesos en segundo plano |
| **Archivo** | `read_file`, `write_file`, `patch`, `search_files` | Lee, escribe, edita y busca archivos |
| **Navegador** | `browser_navigate`, `browser_click`, `browser_type`, `browser_console`, etc. | Automatización completa de navegador a través de Browserbase |
| **Visión** | `vision_analyze` | Análisis de imágenes a través de modelos multimodales |
| **Generación de Imágenes** | `image_generate` | Genera imágenes (FLUX a través de FAL) |
| **TTS** | `text_to_speech` | Texto a voz (Edge TTS / ElevenLabs / OpenAI) |
| **Razonamiento** | `mixture_of_agents` | Razonamiento multi-modelo |
| **Habilidades** | `skills_list`, `skill_view`, `skill_manage` | Busca, visualiza, crea y gestiona habilidades |
| **Tareas Pendientes** | `todo` | Lee/escribe lista de tareas para planificación de múltiples pasos |
| **Memoria** | `memory` | Notas persistentes + perfil de usuario entre sesiones |
| **Búsqueda de Sesión** | `session_search` | Busca + resume conversaciones pasadas (FTS5) |
| **Cron** | `schedule_cronjob`, `list_cronjobs`, `remove_cronjob` | Gestión de tareas programadas |
| **Ejecución de Código** | `execute_code` | Ejecuta scripts Python que llaman a herramientas a través de sandbox RPC |
| **Delegación** | `delegate_task` | Genera subagentes con contexto aislado |
| **Aclaración** | `clarify` | Haz preguntas de opción múltiple o abiertas al usuario |
| **MCP** | Auto-descubierto | Herramientas externas de servidores MCP |

## Usando Conjuntos de Herramientas

```bash
# Usa conjuntos de herramientas específicos
hermes chat --toolsets "web,terminal"

# Ve todas las herramientas disponibles
hermes tools

# Configura herramientas por plataforma (interactivo)
hermes tools
```

**Conjuntos de herramientas disponibles:** `web`, `terminal`, `file`, `browser`, `vision`, `image_gen`, `moa`, `skills`, `tts`, `todo`, `memory`, `session_search`, `cronjob`, `code_execution`, `delegation`, `clarify`, y más.

## Backends de Terminal

La herramienta terminal puede ejecutar comandos en diferentes entornos:

| Backend | Descripción | Caso de Uso |
|---------|-------------|----------|
| `local` | Ejecuta en tu máquina (predeterminado) | Desarrollo, tareas confiables |
| `docker` | Contenedores aislados | Seguridad, reproducibilidad |
| `ssh` | Servidor remoto | Sandboxing, mantén el agente lejos de su propio código |
| `singularity` | Contenedores HPC | Computación en clústeres, sin privilegios |
| `modal` | Ejecución en la nube | Sin servidor, escala |

### Configuración

```yaml
# En ~/.hermes/config.yaml
terminal:
  backend: local    # o: docker, ssh, singularity, modal, daytona
  cwd: "."          # Directorio de trabajo
  timeout: 180      # Tiempo de espera del comando en segundos
```

### Backend Docker

```yaml
terminal:
  backend: docker
  docker_image: python:3.11-slim
```

### Backend SSH

Recomendado para seguridad — el agente no puede modificar su propio código:

```yaml
terminal:
  backend: ssh
```

```bash
# Establece credenciales en ~/.hermes/.env
TERMINAL_SSH_HOST=my-server.example.com
TERMINAL_SSH_USER=myuser
TERMINAL_SSH_KEY=~/.ssh/id_rsa
```

### Singularity/Apptainer

```bash
# Pre-construye SIF para workers paralelos
apptainer build ~/python.sif docker://python:3.11-slim

# Configura
hermes config set terminal.backend singularity
hermes config set terminal.singularity_image ~/python.sif
```

### Modal (Nube Sin Servidor)

```bash
uv pip install "swe-rex[modal]"
modal setup
hermes config set terminal.backend modal
```

### Recursos de Contenedor

Configura CPU, memoria, disco y persistencia para todos los backends de contenedor:

```yaml
terminal:
  backend: docker  # o singularity, modal, daytona
  container_cpu: 1              # Núcleos de CPU (predeterminado: 1)
  container_memory: 5120        # Memoria en MB (predeterminado: 5GB)
  container_disk: 51200         # Disco en MB (predeterminado: 50GB)
  container_persistent: true    # Persiste sistema de archivos entre sesiones (predeterminado: true)
```

Cuando `container_persistent: true`, los paquetes instalados, archivos y configuración persisten entre sesiones.

### Seguridad de Contenedor

Todos los backends de contenedor se ejecutan con endurecimiento de seguridad:

- Sistema de archivos raíz de solo lectura (Docker)
- Todas las capacidades de Linux eliminadas
- Sin escalada de privilegios
- Límites de PID (256 procesos)
- Aislamiento completo de namespaces
- Espacio de trabajo persistente a través de volúmenes, no capa raíz escribible

## Gestión de Procesos en Segundo Plano

Inicia procesos en segundo plano y gestiónalos:

```python
terminal(command="pytest -v tests/", background=true)
# Devuelve: {"session_id": "proc_abc123", "pid": 12345}

# Luego gestiona con la herramienta process:
process(action="list")       # Muestra todos los procesos en ejecución
process(action="poll", session_id="proc_abc123")   # Verifica estado
process(action="wait", session_id="proc_abc123")   # Bloquea hasta completar
process(action="log", session_id="proc_abc123")    # Salida completa
process(action="kill", session_id="proc_abc123")   # Termina
process(action="write", session_id="proc_abc123", data="y")  # Envía entrada
```

El modo PTY (`pty=true`) habilita herramientas CLI interactivas como Codex y Claude Code.

## Soporte Sudo

Si un comando necesita sudo, se te pedirá tu contraseña (almacenada en caché para la sesión). O establece `SUDO_PASSWORD` en `~/.hermes/.env`.

:::advertencia
En plataformas de mensajería, si sudo falla, la salida incluye un consejo para agregar `SUDO_PASSWORD` a `~/.hermes/.env`.
:::
