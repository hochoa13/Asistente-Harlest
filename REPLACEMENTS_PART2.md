# Configuration.md — Translation Replacements PART 2 (Ready to Apply)

Continuation of detailed multi_replace_string_in_file formatted replacements.

**File:** `docs/user-guide/configuration.md`

---

## BATCH 23 continued: Auxiliary Models - Part 2 (3 replacements)

### Replacement 45: Provider Options subheading & table
**Lines:** 639-649
**Type:** Markdown subheading + table

Old String:
```
### Provider Options

| Provider | Description | Requirements |
|----------|-------------|-------------|
| `"auto"` | Best available (default). Vision tries OpenRouter → Nous → Codex. | — |
| `"openrouter"` | Force OpenRouter — routes to any model (Gemini, GPT-4o, Claude, etc.) | `OPENROUTER_API_KEY` |
| `"nous"` | Force Nous Portal | `hermes login` |
| `"codex"` | Force Codex OAuth (ChatGPT account). Supports vision (gpt-5.3-codex). | `hermes model` → Codex |
| `"main"` | Use your custom endpoint (`OPENAI_BASE_URL` + `OPENAI_API_KEY`). Works with OpenAI, local models, or any OpenAI-compatible API. | `OPENAI_BASE_URL` + `OPENAI_API_KEY` |
```

New String:
```
### Opciones de proveedor

| Proveedor | Descripción | Requisitos |
|-----------|------------|------------|
| `"auto"` | Mejor disponible (predeterminado). La visión intenta OpenRouter → Nous → Codex. | — |
| `"openrouter"` | Fuerza OpenRouter — enruta a cualquier modelo (Gemini, GPT-4o, Claude, etc.) | `OPENROUTER_API_KEY` |
| `"nous"` | Fuerza Nous Portal | `hermes login` |
| `"codex"` | Fuerza Codex OAuth (cuenta ChatGPT). Soporta visión (gpt-5.3-codex). | `hermes model` → Codex |
| `"main"` | Usa tu punto de conexión personalizado (`OPENAI_BASE_URL` + `OPENAI_API_KEY`). Funciona con OpenAI, modelos locales o cualquier API compatible con OpenAI. | `OPENAI_BASE_URL` + `OPENAI_API_KEY` |
```

---

### Replacement 46: Common Setups subheading & setup 1
**Lines:** 651-665
**Type:** Markdown subheading + setup examples

Old String:
```
### Common Setups

**Using OpenAI API key for vision:**
```yaml
# In ~/.hermes/.env:
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_API_KEY=sk-...

auxiliary:
  vision:
    provider: "main"
    model: "gpt-4o"       # or "gpt-4o-mini" for cheaper
```

**Using OpenRouter for vision** (route to any model):
```yaml
auxiliary:
  vision:
    provider: "openrouter"
    model: "openai/gpt-4o"      # or "google/gemini-2.5-flash", etc.
```
```

New String:
```
### Configuraciones comunes

**Usar clave API de OpenAI para visión:**
```yaml
# En ~/.hermes/.env:
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_API_KEY=sk-...

auxiliary:
  vision:
    provider: "main"
    model: "gpt-4o"       # or "gpt-4o-mini" for cheaper
```

**Usar OpenRouter para visión** (enruta a cualquier modelo):
```yaml
auxiliary:
  vision:
    provider: "openrouter"
    model: "openai/gpt-4o"      # or "google/gemini-2.5-flash", etc.
```
```

---

### Replacement 47: Common Setups setup 3 & 4
**Lines:** 658-668
**Type:** Setup examples with comments

Old String:
```
**Using Codex OAuth** (ChatGPT Pro/Plus account — no API key needed):
```yaml
auxiliary:
  vision:
    provider: "codex"     # uses your ChatGPT OAuth token
    # model defaults to gpt-5.3-codex (supports vision)
```

**Using a local/self-hosted model:**
```yaml
auxiliary:
  vision:
    provider: "main"      # uses your OPENAI_BASE_URL endpoint
    model: "my-local-model"
```
```

New String:
```
**Usar Codex OAuth** (cuenta ChatGPT Pro/Plus — sin clave API requerida):
```yaml
auxiliary:
  vision:
    provider: "codex"     # usa tu token OAuth de ChatGPT
    # el modelo por defecto es gpt-5.3-codex (soporta visión)
```

**Usar un modelo local/autoalojado:**
```yaml
auxiliary:
  vision:
    provider: "main"      # usa tu punto de conexión OPENAI_BASE_URL
    model: "my-local-model"
```
```

---

### Replacement 48: Auxiliary Tips & Warning
**Lines:** 670-676
**Type:** Markdown tip + warning boxes

Old String:
```
:::tip
If you use Codex OAuth as your main model provider, vision works automatically — no extra configuration needed. Codex is included in the auto-detection chain for vision.
:::

:::warning
**Vision requires a multimodal model.** If you set `provider: "main"`, make sure your endpoint supports multimodal/vision — otherwise image analysis will fail.
:::
```

New String:
```
:::tip
Si usas Codex OAuth como tu proveedor de modelo principal, la visión funciona automáticamente — no se necesita configuración adicional. Codex se incluye en la cadena de detección automática para visión.
:::

:::warning
**La visión requiere un modelo multimodal.** Si configuraste `provider: "main"`, asegúrate de que tu punto de conexión soporta multimodal/visión — de lo contrario, el análisis de imágenes fallará.
:::
```

---

## BATCH 24: Auxiliary Environment Variables (1 replacement)

### Replacement 49: Auxiliary Environment Variables section
**Lines:** 678-692
**Type:** Markdown subheading + intro + table + tip

Old String:
```
### Environment Variables

You can also configure auxiliary models via environment variables instead of `config.yaml`:

| Setting | Environment Variable |
|---------|---------------------|
| Vision provider | `AUXILIARY_VISION_PROVIDER` |
| Vision model | `AUXILIARY_VISION_MODEL` |
| Web extract provider | `AUXILIARY_WEB_EXTRACT_PROVIDER` |
| Web extract model | `AUXILIARY_WEB_EXTRACT_MODEL` |
| Compression provider | `CONTEXT_COMPRESSION_PROVIDER` |
| Compression model | `CONTEXT_COMPRESSION_MODEL` |

:::tip
Run `hermes config` to see your current auxiliary model settings. Overrides only show up when they differ from the defaults.
:::
```

New String:
```
### Variables de entorno

También puedes configurar modelos auxiliares a través de variables de entorno en lugar de `config.yaml`:

| Ajuste | Variable de entorno |
|--------|-------------------|
| Proveedor de visión | `AUXILIARY_VISION_PROVIDER` |
| Modelo de visión | `AUXILIARY_VISION_MODEL` |
| Proveedor de extracción web | `AUXILIARY_WEB_EXTRACT_PROVIDER` |
| Modelo de extracción web | `AUXILIARY_WEB_EXTRACT_MODEL` |
| Proveedor de compresión | `CONTEXT_COMPRESSION_PROVIDER` |
| Modelo de compresión | `CONTEXT_COMPRESSION_MODEL` |

:::tip
Ejecuta `hermes config` para ver tus ajustes de modelo auxiliar actuales. Las anulaciones solo aparecen cuando difieren de los valores predeterminados.
:::
```

---

## BATCH 25: Reasoning Effort (2 replacements)

### Replacement 50: Reasoning Effort heading & intro
**Lines:** 684-707
**Type:** Markdown heading + intro + code block + prose

Old String:
```
## Reasoning Effort

Control how much "thinking" the model does before responding:

```yaml
agent:
  reasoning_effort: ""   # empty = medium (default). Options: xhigh (max), high, medium, low, minimal, none
```

When unset (default), reasoning effort defaults to "medium" — a balanced level that works well for most tasks. Setting a value overrides it — higher reasoning effort gives better results on complex tasks at the cost of more tokens and latency.

You can also change the reasoning effort at runtime with the `/reasoning` command:

```
/reasoning           # Show current effort level and display state
/reasoning high      # Set reasoning effort to high
/reasoning none      # Disable reasoning
/reasoning show      # Show model thinking above each response
/reasoning hide      # Hide model thinking
```
```

New String:
```
## Esfuerzo de razonamiento

Controla cuánto "pensamiento" hace el modelo antes de responder:

```yaml
agent:
  reasoning_effort: ""   # vacío = medio (predeterminado). Opciones: xhigh (máximo), alto, medio, bajo, mínimo, ninguno
```

Cuando no está configurado (predeterminado), el esfuerzo de razonamiento por defecto es "medio" — un nivel equilibrado que funciona bien para la mayoría de las tareas. Establecer un valor lo anula — el esfuerzo de razonamiento más alto da mejores resultados en tareas complejas al costo de más tokens y latencia.

También puedes cambiar el esfuerzo de razonamiento en tiempo de ejecución con el comando `/reasoning`:

```
/reasoning           # Mostrar nivel de esfuerzo actual y estado de pantalla
/reasoning high      # Establecer esfuerzo de razonamiento a alto
/reasoning none      # Deshabilitar razonamiento
/reasoning show      # Mostrar pensamiento del modelo encima de cada respuesta
/reasoning hide      # Ocultar pensamiento del modelo
```
```

---

## BATCH 26: TTS & Display Settings (2 replacements)

### Replacement 51: TTS Configuration heading & code
**Lines:** 709-720
**Type:** Markdown heading + code block with comments

Old String:
```
## TTS Configuration

```yaml
tts:
  provider: "edge"              # "edge" | "elevenlabs" | "openai"
  edge:
    voice: "en-US-AriaNeural"   # 322 voices, 74 languages
  elevenlabs:
    voice_id: "pNInz6obpgDQGcFmaJgB"
    model_id: "eleven_multilingual_v2"
  openai:
    model: "gpt-4o-mini-tts"
    voice: "alloy"              # alloy, echo, fable, onyx, nova, shimmer
```
```

New String:
```
## Configuración de TTS

```yaml
tts:
  provider: "edge"              # "edge" | "elevenlabs" | "openai"
  edge:
    voice: "en-US-AriaNeural"   # 322 voces, 74 idiomas
  elevenlabs:
    voice_id: "pNInz6obpgDQGcFmaJgB"
    model_id: "eleven_multilingual_v2"
  openai:
    model: "gpt-4o-mini-tts"
    voice: "alloy"              # alloy, echo, fable, onyx, nova, shimmer
```
```

---

### Replacement 52: Display Settings heading & code
**Lines:** 722-750
**Type:** Markdown heading + code block with comments + table

Old String:
```
## Display Settings

```yaml
display:
  tool_progress: all    # off | new | all | verbose
  personality: "kawaii"  # Default personality for the CLI
  compact: false         # Compact output mode (less whitespace)
  resume_display: full   # full (show previous messages on resume) | minimal (one-liner only)
  bell_on_complete: false  # Play terminal bell when agent finishes (great for long tasks)
  show_reasoning: false    # Show model reasoning/thinking above each response (toggle with /reasoning show|hide)
```

| Mode | What you see |
|------|-------------|
| `off` | Silent — just the final response |
| `new` | Tool indicator only when the tool changes |
| `all` | Every tool call with a short preview (default) |
| `verbose` | Full args, results, and debug logs |
```

New String:
```
## Ajustes de pantalla

```yaml
display:
  tool_progress: all    # off | new | all | verbose
  personality: "kawaii"  # Personalidad predeterminada para CLI
  compact: false         # Modo de salida compacta (menos espacios en blanco)
  resume_display: full   # full (mostrar mensajes anteriores al reanudar) | minimal (solo una línea)
  bell_on_complete: false  # Reproduce campana de terminal cuando el agente termina (excelente para tareas largas)
  show_reasoning: false    # Mostrar razonamiento/pensamiento del modelo encima de cada respuesta (alternar con /reasoning show|hide)
```

| Modo | Lo que ves |
|------|------------|
| `off` | Silencioso — solo la respuesta final |
| `new` | Indicador de herramienta solo cuando cambia la herramienta |
| `all` | Cada llamada de herramienta con una vista previa corta (predeterminado) |
| `verbose` | Argumentos completos, resultados y registros de depuración |
```

---

## BATCH 27: STT, Quick Commands, & Human Delay (3 replacements)

### Replacement 53: STT Configuration heading
**Lines:** 752-757
**Type:** Markdown heading + code block + prose

Old String:
```
## Speech-to-Text (STT)

```yaml
stt:
  provider: "openai"           # STT provider
```

Requires `VOICE_TOOLS_OPENAI_KEY` in `.env` for OpenAI STT.
```

New String:
```
## Conversión de voz a texto (STT)

```yaml
stt:
  provider: "openai"           # Proveedor de STT
```

Requiere `VOICE_TOOLS_OPENAI_KEY` en `.env` para STT de OpenAI.
```

---

### Replacement 54: Quick Commands full section
**Lines:** 759-783
**Type:** Markdown heading + intro + code block + bullet points

Old String:
```
## Quick Commands

Define custom commands that run shell commands without invoking the LLM — zero token usage, instant execution. Especially useful from messaging platforms (Telegram, Discord, etc.) for quick server checks or utility scripts.

```yaml
quick_commands:
  status:
    type: exec
    command: systemctl status hermes-agent
  disk:
    type: exec
    command: df -h /
  update:
    type: exec
    command: cd ~/.hermes/hermes-agent && git pull && pip install -e .
  gpu:
    type: exec
    command: nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total --format=csv,noheader
```

Usage: type `/status`, `/disk`, `/update`, or `/gpu` in the CLI or any messaging platform. The command runs locally on the host and returns the output directly — no LLM call, no tokens consumed.

- **30-second timeout** — long-running commands are killed with an error message
- **Priority** — quick commands are checked before skill commands, so you can override skill names
- **Type** — only `exec` is supported (runs a shell command); other types show an error
- **Works everywhere** — CLI, Telegram, Discord, Slack, WhatsApp, Signal
```

New String:
```
## Comandos rápidos

Define comandos personalizados que ejecuten comandos de shell sin invocar el LLM — cero uso de tokens, ejecución instantánea. Especialmente útil desde plataformas de mensajería (Telegram, Discord, etc.) para verificaciones rápidas del servidor o scripts de utilidad.

```yaml
quick_commands:
  status:
    type: exec
    command: systemctl status hermes-agent
  disk:
    type: exec
    command: df -h /
  update:
    type: exec
    command: cd ~/.hermes/hermes-agent && git pull && pip install -e .
  gpu:
    type: exec
    command: nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total --format=csv,noheader
```

Uso: escribe `/status`, `/disk`, `/update`, o `/gpu` en CLI o en cualquier plataforma de mensajería. El comando se ejecuta localmente en el host y devuelve la salida directamente — sin llamada LLM, sin tokens consumidos.

- **Tiempo de espera de 30 segundos** — los comandos de larga duración se matan con un mensaje de error
- **Prioridad** — los comandos rápidos se comprueban antes de los comandos de habilidad, por lo que puedes anular nombres de habilidad
- **Tipo** — solo `exec` se admite (ejecuta un comando de shell); otros tipos muestran un error
- **Funciona en todas partes** — CLI, Telegram, Discord, Slack, WhatsApp, Signal
```

---

### Replacement 55: Human Delay heading & code
**Lines:** 785-791
**Type:** Markdown heading + code block with comments

Old String:
```
## Human Delay

Simulate human-like response pacing in messaging platforms:

```yaml
human_delay:
  mode: "off"                  # off | natural | custom
  min_ms: 500                  # Minimum delay (custom mode)
  max_ms: 2000                 # Maximum delay (custom mode)
```
```

New String:
```
## Retardo humano

Simula ritmo de respuesta similar al humano en plataformas de mensajería:

```yaml
human_delay:
  mode: "off"                  # off | natural | custom
  min_ms: 500                  # Retardo mínimo (modo personalizado)
  max_ms: 2000                 # Retardo máximo (modo personalizado)
```
```

---

## BATCH 28: Code Execution, Browser, Checkpoints (3 replacements)

### Replacement 56: Code Execution heading & code
**Lines:** 793-799
**Type:** Markdown heading + code block with comments

Old String:
```
## Code Execution

Configure the sandboxed Python code execution tool:

```yaml
code_execution:
  timeout: 300                 # Max execution time in seconds
  max_tool_calls: 50           # Max tool calls within code execution
```
```

New String:
```
## Ejecución de código

Configura la herramienta de ejecución de código Python aislada:

```yaml
code_execution:
  timeout: 300                 # Tiempo máximo de ejecución en segundos
  max_tool_calls: 50           # Máximo de llamadas de herramienta dentro de la ejecución de código
```
```

---

### Replacement 57: Browser heading & code
**Lines:** 801-807
**Type:** Markdown heading + code block with comments

Old String:
```
## Browser

Configure browser automation behavior:

```yaml
browser:
  inactivity_timeout: 120        # Seconds before auto-closing idle sessions
  record_sessions: false         # Auto-record browser sessions as WebM videos to ~/.hermes/browser_recordings/
```
```

New String:
```
## Navegador

Configura el comportamiento de automatización del navegador:

```yaml
browser:
  inactivity_timeout: 120        # Segundos antes de cerrar automáticamente sesiones inactivas
  record_sessions: false         # Graba automáticamente sesiones del navegador como videos WebM en ~/.hermes/browser_recordings/
```
```

---

### Replacement 58: Checkpoints heading & code & link
**Lines:** 809-815
**Type:** Markdown heading + prose + code block with comments

Old String:
```
## Checkpoints

Automatic filesystem snapshots before destructive file operations. See the [Checkpoints feature page](/docs/user-guide/features/checkpoints) for details.

```yaml
checkpoints:
  enabled: false                 # Enable automatic checkpoints (also: hermes --checkpoints)
  max_snapshots: 50              # Max checkpoints to keep per directory
```
```

New String:
```
## Puntos de control

Instantáneas automáticas del sistema de archivos antes de operaciones destructivas de archivos. Consulta la [página de características de Checkpoints](/docs/user-guide/features/checkpoints) para detalles.

```yaml
checkpoints:
  enabled: false                 # Habilita puntos de control automáticos (también: hermes --checkpoints)
  max_snapshots: 50              # Máximo de puntos de control para mantener por directorio
```
```

---

## BATCH 29: Delegation & Clarify (2 replacements)

### Replacement 59: Delegation heading & intro
**Lines:** 817-836
**Type:** Markdown heading + intro + code block with comments + prose

Old String:
```
## Delegation

Configure subagent behavior for the delegate tool:

```yaml
delegation:
  max_iterations: 50           # Max iterations per subagent
  default_toolsets:             # Toolsets available to subagents
    - terminal
    - file
    - web
  # model: "google/gemini-3-flash-preview"  # Override model (empty = inherit parent)
  # provider: "openrouter"                  # Override provider (empty = inherit parent)
```

**Subagent provider:model override:** By default, subagents inherit the parent agent's provider and model. Set `delegation.provider` and `delegation.model` to route subagents to a different provider:model pair — e.g., use a cheap/fast model for narrowly-scoped subtasks while your primary agent runs an expensive reasoning model.

The delegation provider uses the same credential resolution as CLI/gateway startup. All configured providers are supported: `openrouter`, `nous`, `zai`, `kimi-coding`, `minimax`, `minimax-cn`. When a provider is set, the system automatically resolves the correct base URL, API key, and API mode — no manual credential wiring needed.

**Precedence:** _`delegation.provider` in config → parent provider (inherited). `delegation.model` in config → parent model (inherited). Setting just `model` without `provider` changes only the model name while keeping the parent's credentials (useful for switching models within the same provider like OpenRouter)._
```

New String:
```
## Delegación

Configura el comportamiento del subagente para la herramienta de delegación:

```yaml
delegation:
  max_iterations: 50           # Máximo de iteraciones por subagente
  default_toolsets:             # Conjuntos de herramientas disponibles para subagentes
    - terminal
    - file
    - web
  # model: "google/gemini-3-flash-preview"  # Anular modelo (vacío = heredar del padre)
  # provider: "openrouter"                  # Anular proveedor (vacío = heredar del padre)
```

**Anulación de proveedor:modelo de subagente:** Por defecto, los subagentes heredan el proveedor y modelo del agente padre. Establece `delegation.provider` y `delegation.model` para enrutar subagentes a un par proveedor:modelo diferente — p. ej., usa un modelo barato/rápido para subtareas de alcance limitado mientras tu agente principal ejecuta un modelo de razonamiento costoso.

El proveedor de delegación utiliza la misma resolución de credenciales que el inicio de CLI/gateway. Se admiten todos los proveedores configurados: `openrouter`, `nous`, `zai`, `kimi-coding`, `minimax`, `minimax-cn`. Cuando se establece un proveedor, el sistema automáticamente resuelve la URL base, clave API y modo API correcto — no se necesita enrutamiento manual de credenciales.

**Precedencia:** _`delegation.provider` en config → proveedor padre (heredado). `delegation.model` en config → modelo padre (heredado). Establecer solo `model` sin `provider` cambia solo el nombre del modelo mientras se mantienen las credenciales del padre (útil para cambiar modelos dentro del mismo proveedor como OpenRouter)._
```

---

### Replacement 60: Clarify heading & code
**Lines:** 838-842
**Type:** Markdown heading + code block with comments

Old String:
```
## Clarify

Configure the clarification prompt behavior:

```yaml
clarify:
  timeout: 120                 # Seconds to wait for user clarification response
```
```

New String:
```
## Aclarar

Configura el comportamiento de la solicitud de aclaración:

```yaml
clarify:
  timeout: 120                 # Segundos para esperar respuesta de aclaración del usuario
```
```

---

## BATCH 30: Context Files & Working Directory (2 replacements)

### Replacement 61: Context Files heading & intro & table
**Lines:** 844-857
**Type:** Markdown heading + intro + table + bullet points

Old String:
```
## Context Files (SOUL.md, AGENTS.md)

Drop these files in your project directory and the agent automatically picks them up:

| File | Purpose |
|------|---------|
| `AGENTS.md` | Project-specific instructions, coding conventions |
| `SOUL.md` | Persona definition — the agent embodies this personality |
| `.cursorrules` | Cursor IDE rules (also detected) |
| `.cursor/rules/*.mdc` | Cursor rule files (also detected) |

- **AGENTS.md** is hierarchical: if subdirectories also have AGENTS.md, all are combined.
- **SOUL.md** checks cwd first, then `~/.hermes/SOUL.md` as a global fallback.
- All context files are capped at 20,000 characters with smart truncation.
```

New String:
```
## Archivos de contexto (SOUL.md, AGENTS.md)

Suelta estos archivos en tu directorio de proyecto y el agente los captura automáticamente:

| Archivo | Propósito |
|---------|-----------|
| `AGENTS.md` | Instrucciones específicas del proyecto, convenciones de codificación |
| `SOUL.md` | Definición de persona — el agente encarna esta personalidad |
| `.cursorrules` | Reglas de IDE Cursor (también detectadas) |
| `.cursor/rules/*.mdc` | Archivos de regla de Cursor (también detectados) |

- **AGENTS.md** es jerárquico: si los subdirectorios también tienen AGENTS.md, todos se combinan.
- **SOUL.md** verifica primero cwd, luego `~/.hermes/SOUL.md` como respaldo global.
- Todos los archivos de contexto se cap en 20.000 caracteres con truncamiento inteligente.
```

---

### Replacement 62: Working Directory heading & table & prose
**Lines:** 859-872
**Type:** Markdown heading + table + prose + code block with comments

Old String:
```
## Working Directory

| Context | Default |
|---------|---------|
| **CLI (`hermes`)** | Current directory where you run the command |
| **Messaging gateway** | Home directory `~` (override with `MESSAGING_CWD`) |
| **Docker / Singularity / Modal / SSH** | User's home directory inside the container or remote machine |

Override the working directory:
```bash
# In ~/.hermes/.env or ~/.hermes/config.yaml:
MESSAGING_CWD=/home/myuser/projects    # Gateway sessions
TERMINAL_CWD=/workspace                # All terminal sessions
```
```

New String:
```
## Directorio de trabajo

| Contexto | Predeterminado |
|----------|----------|
| **CLI (`hermes`)** | Directorio actual donde ejecutas el comando |
| **Puerta de enlace de mensajería** | Directorio de inicio `~` (anula con `MESSAGING_CWD`) |
| **Docker / Singularity / Modal / SSH** | Directorio de inicio del usuario dentro del contenedor o máquina remota |

Anula el directorio de trabajo:
```bash
# En ~/.hermes/.env o ~/.hermes/config.yaml:
MESSAGING_CWD=/home/myuser/projects    # Sesiones de puerta de enlace
TERMINAL_CWD=/workspace                # Todas las sesiones de terminal
```
```

---

## SUMMARY OF ALL REPLACEMENTS

**Total Replacements Created:** 62

**Organized by sections:**
- Batches 1-5: Basic headings and Inference Providers (10 replacements)
- Batches 6-12: LLM Provider options (Anthropic, Chinese, Custom, Ollama, vLLM, SGLang, llama.cpp, LiteLLM, ClawRouter) (13 replacements)
- Batches 13-17: Other providers, setup guidance, Optional API Keys, Firecrawl, OpenRouter (8 replacements)
- Batches 18-22: Terminal config, Docker volumes, Memory, Git Worktree, Context Compression, Iteration Budget (6 replacements)
- Batches 23-26: Auxiliary Models (full), Reasoning Effort, TTS, Display settings (9 replacements)
- Batches 27-30: STT, Quick Commands, Human Delay, Code Execution, Browser, Checkpoints, Delegation, Clarify, Context Files, Working Directory (10 replacements)

**All replacements are now ready for application via multi_replace_string_in_file tool**

---

## KEY TRANSLATION NOTES

1. **Preserved unchanged (all instances):**
   - Provider names (OpenRouter, Anthropic, Claude, Nous, Codex, Azure, etc.)
   - Environment variable names (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
   - Command names (hermes config, hermes model, etc.)
   - File paths (/.hermes/, ~/.codex/, etc.)
   - Model names (claude-sonnet-4, gpt-4o, llama3.1:70b, etc.)
   - All code blocks (bash, yaml, text blocks)
   - All URLs and links
   - Table structure and format

2. **Translated (with consistency):**
   - All major section headings
   - All prose text and explanations
   - All comments in code (non-syntax YAML comments)
   - All table headers and descriptive cell content
   - All tip/warning/info/note boxes
   - All bullet points and numbered lists
   - All inline descriptions

3. **Professional Spanish terminology used:**
   - "configuración" for configuration/settings
   - "proveedor" for provider
   - "modelo" for model
   - "clave API" for API key
   - "terminal" for terminal (command line)
   - "enrutamiento" for routing
   - "volumen" for volume
   - "contenedor" for container
   - "memoria" for memory
   - "variable de entorno" for environment variable

