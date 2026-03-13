---
sidebar_position: 2
title: "Configuración"
description: "Configura Hermes Agent — config.yaml, proveedores, modelos, claves API, y más"
---

# Configuración

Todos los ajustes se almacenan en el directorio `~/.hermes/` para un fácil acceso.

## Estructura de directorio

```text
~/.hermes/
├── config.yaml     # Settings (model, terminal, TTS, compression, etc.)
├── .env            # API keys and secrets
├── auth.json       # OAuth provider credentials (Nous Portal, etc.)
├── SOUL.md         # Opcional: persona global (el agente encarna esta personalidad)
├── memories/       # Memoria persistente (MEMORY.md, USER.md)
├── skills/         # Habilidades creadas por agente (gestionadas a través de herramienta skill_manage)
├── cron/           # Trabajos programados
├── sessions/       # Sesiones de puerta de enlace
└── logs/           # Registros (errors.log, gateway.log — secretos redactados automáticamente)
```

## Gestión de configuración

```bash
hermes config              # Vea la configuración actual
hermes config edit         # Abre config.yaml en tu editor
hermes config set KEY VAL  # Establece un valor específico
hermes config check        # Verifica opciones faltantes (después de actualizaciones)
hermes config migrate      # Agrega interactivamente opciones faltantes

# Ejemplos:
hermes config set model anthropic/claude-opus-4
hermes config set terminal.backend docker
hermes config set OPENROUTER_API_KEY sk-or-...  # Se guarda en .env
```

:::tip
El comando `hermes config set` enruta automáticamente los valores al archivo correcto — las claves API se guardan en `.env`, todo lo demás en `config.yaml`.
:::

## Precedencia de configuración

Los ajustes se resuelven en este orden (mayor prioridad primero):

1. **Argumentos CLI** — p. ej., `hermes chat --model anthropic/claude-sonnet-4` (anulación por invocación)
2. **`~/.hermes/config.yaml`** — el archivo de configuración principal para todos los ajustes no secretos
3. **`~/.hermes/.env`** — respaldo para variables de entorno; **requerido** para secretos (claves API, tokens, contraseñas)
4. **Valores por defecto integrados** — valores predeterminados seguros codificados cuando nada más está configurado

:::info Regla General
Los secretos (claves API, tokens de bot, contraseñas) van en `.env`. Todo lo demás (modelo, backend de terminal, configuración de compresión, límites de memoria, conjuntos de herramientas) va en `config.yaml`. Cuando ambos están configurados, `config.yaml` prevalece para configuraciones no secretas.
:::

## Proveedores de inferencia

Necesitas al menos una forma de conectar a un LLM. Usa `hermes model` para cambiar proveedores y modelos interactivamente, o configura directamente:

| Proveedor | Configuración |
|----------|-------|
| **Nous Portal** | `hermes model` (OAuth, subscription-based) |
| **OpenAI Codex** | `hermes model` (ChatGPT OAuth, uses Codex models) |
| **Anthropic** | `hermes model` (API key, setup-token, or Claude Code auto-detect) |
| **OpenRouter** | `OPENROUTER_API_KEY` in `~/.hermes/.env` |
| **z.ai / GLM** | `GLM_API_KEY` in `~/.hermes/.env` (provider: `zai`) |
| **Kimi / Moonshot** | `KIMI_API_KEY` in `~/.hermes/.env` (provider: `kimi-coding`) |
| **MiniMax** | `MINIMAX_API_KEY` in `~/.hermes/.env` (provider: `minimax`) |
| **MiniMax China** | `MINIMAX_CN_API_KEY` in `~/.hermes/.env` (provider: `minimax-cn`) |
| **Custom Endpoint** | `OPENAI_BASE_URL` + `OPENAI_API_KEY` in `~/.hermes/.env` |

:::info Nota sobre Codex
El proveedor OpenAI Codex se autentica mediante código de dispositivo (abre una URL, ingresa un código). Las credenciales se almacenan en `~/.codex/auth.json` y se actualizan automáticamente. No se requiere instalación de CLI de Codex.
:::

:::warning
Incluso cuando uses Nous Portal, Codex o un punto de extremo personalizado, algunas herramientas (visión, resumen web, MoA) utilizan un modelo "auxiliar" separado — por defecto Gemini Flash a través de OpenRouter. Una `OPENROUTER_API_KEY` habilita estas herramientas automáticamente. También puedes configurar qué modelo y proveedor utilizan estas herramientas — consulta [Modelos auxiliares](#modelos-auxiliares) a continuación.
:::

### Anthropic (Nativo)

Utiliza modelos Claude directamente a través de la API de Anthropic — no se necesita proxy de OpenRouter. Admite tres métodos de autenticación:

```bash
# Con una clave API (pago por token)
export ANTHROPIC_API_KEY=sk-ant-api03-...
hermes chat --provider anthropic --model claude-sonnet-4-6

# Con un token de configuración de Claude Code (suscripción Pro/Max)
export ANTHROPIC_API_KEY=sk-ant-oat01-...  # de 'claude setup-token'
hermes chat --provider anthropic

# Autodetectar credenciales de Claude Code (si tienes Claude Code instalado)
hermes chat --provider anthropic  # lee ~/.claude.json automáticamente
```

O establécelo permanentemente:
```yaml
model:
  provider: "anthropic"
  default: "claude-sonnet-4-6"
```

:::tip Alias
`--provider claude` y `--provider claude-code` también funcionan como abreviatura para `--provider anthropic`.
:::

### Proveedores de IA chinos de primera clase

Estos proveedores tienen soporte integrado con ID de proveedor dedicados. Establece la clave API y usa `--provider` para seleccionar:

```bash
# z.ai / ZhipuAI GLM
hermes chat --provider zai --model glm-4-plus
# Requiere: GLM_API_KEY en ~/.hermes/.env

# Kimi / Moonshot AI
hermes chat --provider kimi-coding --model moonshot-v1-auto
# Requiere: KIMI_API_KEY en ~/.hermes/.env

# MiniMax (punto de extremo global)
hermes chat --provider minimax --model MiniMax-Text-01
# Requiere: MINIMAX_API_KEY en ~/.hermes/.env

# MiniMax (punto de extremo de China)
hermes chat --provider minimax-cn --model MiniMax-Text-01
# Requiere: MINIMAX_CN_API_KEY en ~/.hermes/.env
```

O establece el proveedor permanentemente en `config.yaml`:
```yaml
model:
  provider: "zai"       # o: kimi-coding, minimax, minimax-cn
  default: "glm-4-plus"
```

Las URLs base se pueden anular con variables de entorno `GLM_BASE_URL`, `KIMI_BASE_URL`, `MINIMAX_BASE_URL` o `MINIMAX_CN_BASE_URL`.

## Proveedores de LLM personalizados y auto-alojados

Hermes Agent funciona con **cualquier punto de extremo de API compatible con OpenAI**. Si un servidor implementa `/v1/chat/completions`, puedes apuntar Hermes a él. Esto significa que puedes usar modelos locales, servidores de inferencia de GPU, enrutadores multi-proveedor o cualquier API de terceros.

### Configuración general

Dos formas de configurar un punto de extremo personalizado:

**Interactivo (recomendado):**
```bash
hermes model
# Selecciona "Custom endpoint (self-hosted / VLLM / etc.)"
# Ingresa: URL base de API, clave de API, nombre del modelo
```

**Manual (archivo `.env`):**
```bash
# Agrega a ~/.hermes/.env
OPENAI_BASE_URL=http://localhost:8000/v1
OPENAI_API_KEY=your-key-or-dummy
LLM_MODEL=your-model-name
```

Todo lo que sigue utiliza el mismo patrón — simplemente cambia la URL, clave y nombre del modelo.

---

### Ollama — Modelos locales, sin configuración

[Ollama](https://ollama.com/) ejecuta modelos de peso abierto localmente con un comando. Mejor para: experimentación local rápida, trabajo sensible a la privacidad, uso sin conexión.

```bash
# Instala y ejecuta un modelo
ollama pull llama3.1:70b
ollama serve   # Se inicia en el puerto 11434

# Configura Hermes
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama           # Cualquier cadena no vacía
LLM_MODEL=llama3.1:70b
```

El punto de extremo compatible con OpenAI de Ollama admite finalizaciones de chat, streaming y llamadas de herramientas (para modelos compatibles). No se requiere GPU para modelos más pequeños — Ollama maneja la inferencia de CPU automáticamente.

:::tip
Lista los modelos disponibles con `ollama list`. Descarga cualquier modelo de la [biblioteca de Ollama](https://ollama.com/library) con `ollama pull <model>`.
:::

---

### vLLM — Inferencia de GPU de alto rendimiento

[vLLM](https://docs.vllm.ai/) es el estándar para servicio de LLM en producción. Mejor para: máximo rendimiento en hardware de GPU, servir modelos grandes, procesamiento por lotes continuo.

```bash
# Inicia el servidor vLLM
pip install vllm
vllm serve meta-llama/Llama-3.1-70B-Instruct \
  --port 8000 \
  --tensor-parallel-size 2    # Multi-GPU

# Configura Hermes
OPENAI_BASE_URL=http://localhost:8000/v1
OPENAI_API_KEY=dummy
LLM_MODEL=meta-llama/Llama-3.1-70B-Instruct
```

vLLM admite llamadas de herramientas, salida estructurada y modelos multimodales. Usa `--enable-auto-tool-choice` y `--tool-call-parser hermes` para llamadas de herramientas con formato Hermes con modelos de NousResearch.

---

### SGLang — Servicio rápido con RadixAttention

[SGLang](https://github.com/sgl-project/sglang) es una alternativa a vLLM con RadixAttention para reutilización de caché de KV. Mejor para: conversaciones multi-turno (almacenamiento en caché de prefijo), decodificación restringida, salida estructurada.

```bash
# Inicia el servidor SGLang
pip install sglang[all]
python -m sglang.launch_server \
  --model meta-llama/Llama-3.1-70B-Instruct \
  --port 8000 \
  --tp 2

# Configura Hermes
OPENAI_BASE_URL=http://localhost:8000/v1
OPENAI_API_KEY=dummy
LLM_MODEL=meta-llama/Llama-3.1-70B-Instruct
```

---

### llama.cpp / llama-server — Inferencia de CPU y Metal

[llama.cpp](https://github.com/ggml-org/llama.cpp) ejecuta modelos cuantificados en CPU, Apple Silicon (Metal) y GPUs de consumidor. Mejor para: ejecutar modelos sin una GPU de centro de datos, usuarios de Mac, implementación de perímetro.

```bash
# Compila e inicia llama-server
cmake -B build && cmake --build build --config Release
./build/bin/llama-server \
  -m models/llama-3.1-8b-instruct-Q4_K_M.gguf \
  --port 8080 --host 0.0.0.0

# Configura Hermes
OPENAI_BASE_URL=http://localhost:8080/v1
OPENAI_API_KEY=dummy
LLM_MODEL=llama-3.1-8b-instruct
```

:::tip
Descarga modelos GGUF desde [Hugging Face](https://huggingface.co/models?library=gguf). La cuantificación Q4_K_M ofrece el mejor equilibrio entre calidad y uso de memoria.
:::

---

### LiteLLM Proxy — Puerta de enlace multi-proveedor

[LiteLLM](https://docs.litellm.ai/) es un proxy compatible con OpenAI que unifica 100+ proveedores de LLM detrás de una single API. Mejor para: cambiar entre proveedores sin cambios de configuración, equilibrio de carga, cadenas de respaldo, controles de presupuesto.

```bash
# Instala e inicia
pip install litellm[proxy]
litellm --model anthropic/claude-sonnet-4 --port 4000

# O con un archivo de configuración para múltiples modelos:
litellm --config litellm_config.yaml --port 4000

# Configura Hermes
OPENAI_BASE_URL=http://localhost:4000/v1
OPENAI_API_KEY=sk-your-litellm-key
LLM_MODEL=anthropic/claude-sonnet-4
```

Ejemplo `litellm_config.yaml` con respaldo:
```yaml
model_list:
  - model_name: "best"
    litellm_params:
      model: anthropic/claude-sonnet-4
      api_key: sk-ant-...
  - model_name: "best"
    litellm_params:
      model: openai/gpt-4o
      api_key: sk-...
router_settings:
  routing_strategy: "latency-based-routing"
```

---

### ClawRouter — Enrutamiento optimizado de costos

[ClawRouter](https://github.com/BlockRunAI/ClawRouter) de BlockRunAI es un proxy de enrutamiento local que selecciona automáticamente modelos según la complejidad de la consulta. Clasifica solicitudes en 14 dimensiones y enruta al modelo más económico que pueda manejar la tarea. El pago se realiza mediante criptomoneda USDC (sin claves API).

```bash
# Instala e inicia
npx @blockrun/clawrouter    # Se inicia en el puerto 8402

# Configura Hermes
OPENAI_BASE_URL=http://localhost:8402/v1
OPENAI_API_KEY=dummy
LLM_MODEL=blockrun/auto     # o: blockrun/eco, blockrun/premium, blockrun/agentic
```

Perfiles de enrutamiento:
| Perfil | Estrategia | Ahorros |
|--------|-----------|---------|
| `blockrun/auto` | Calidad/costo equilibrado | 74-100% |
| `blockrun/eco` | Más barato posible | 95-100% |
| `blockrun/premium` | Modelos de mejor calidad | 0% |
| `blockrun/free` | Solo modelos gratuitos | 100% |
| `blockrun/agentic` | Optimizado para uso de herramientas | varía |

:::note
ClawRouter requiere una cartera financiada con USDC en Base o Solana para el pago. Todas las solicitudes se enrutan a través de la API de backend de BlockRun. Ejecuta `npx @blockrun/clawrouter doctor` para verificar el estado de la cartera.
:::

---

### Otros proveedores compatibles

Cualquier servicio con una API compatible con OpenAI funciona. Algunas opciones populares:

| Proveedor | URL base | Notas |
|-----------|----------|-------|
| [Together AI](https://together.ai) | `https://api.together.xyz/v1` | Modelos abiertos alojados en la nube |
| [Groq](https://groq.com) | `https://api.groq.com/openai/v1` | Inferencia ultra rápida |
| [DeepSeek](https://deepseek.com) | `https://api.deepseek.com/v1` | Modelos DeepSeek |
| [Fireworks AI](https://fireworks.ai) | `https://api.fireworks.ai/inference/v1` | Alojamiento rápido de modelos abiertos |
| [Cerebras](https://cerebras.ai) | `https://api.cerebras.ai/v1` | Inferencia con chips a escala de oblea |
| [Mistral AI](https://mistral.ai) | `https://api.mistral.ai/v1` | Modelos Mistral |
| [OpenAI](https://openai.com) | `https://api.openai.com/v1` | Acceso directo a OpenAI |
| [Azure OpenAI](https://azure.microsoft.com) | `https://YOUR.openai.azure.com/` | OpenAI empresarial |
| [LocalAI](https://localai.io) | `http://localhost:8080/v1` | Auto-alojado, multi-modelo |
| [Jan](https://jan.ai) | `http://localhost:1337/v1` | Aplicación de escritorio con modelos locales |

```bash
# Ejemplo: Together AI
OPENAI_BASE_URL=https://api.together.xyz/v1
OPENAI_API_KEY=your-together-key
LLM_MODEL=meta-llama/Llama-3.1-70B-Instruct-Turbo
```

---

### Elegir la configuración correcta

| Caso de uso | Recomendado |
|-----------|-----------|
| **Solo quiero que funcione** | OpenRouter (predeterminado) o Nous Portal |
| **Modelos locales, configuración sencilla** | Ollama |
| **Servicio de GPU en producción** | vLLM o SGLang |
| **Mac / sin GPU** | Ollama o llama.cpp |
| **Enrutamiento multi-proveedor** | LiteLLM Proxy u OpenRouter |
| **Optimización de costos** | ClawRouter u OpenRouter con `sort: "price"` |
| **Máxima privacidad** | Ollama, vLLM o llama.cpp (totalmente local) |
| **Empresa / Azure** | Azure OpenAI con punto de extremo personalizado |
| **Modelos de IA chinos** | z.ai (GLM), Kimi/Moonshot o MiniMax (proveedores de primera clase) |

:::tip
Puedes cambiar entre proveedores en cualquier momento con `hermes model` — no se requiere reinicio. Tu historial de conversación, memoria y habilidades persisten independientemente de qué proveedor uses.
:::

## Claves API opcionales

| Función | Proveedor | Variable de entorno |
|---------|-----------|-------------------|
| Raspado web | [Firecrawl](https://firecrawl.dev/) | `FIRECRAWL_API_KEY` |
| Automatización del navegador | [Browserbase](https://browserbase.com/) | `BROWSERBASE_API_KEY`, `BROWSERBASE_PROJECT_ID` |
| Generación de imágenes | [FAL](https://fal.ai/) | `FAL_KEY` |
| Voces TTS premium | [ElevenLabs](https://elevenlabs.io/) | `ELEVENLABS_API_KEY` |
| TTS de OpenAI + transcripción de voz | [OpenAI](https://platform.openai.com/api-keys) | `VOICE_TOOLS_OPENAI_KEY` |
| Entrenamiento de RL | [Tinker](https://tinker-console.thinkingmachines.ai/) + [WandB](https://wandb.ai/) | `TINKER_API_KEY`, `WANDB_API_KEY` |
| Modelado de usuario entre sesiones | [Honcho](https://honcho.dev/) | `HONCHO_API_KEY` |

### Alojamiento propio de Firecrawl

Por defecto, Hermes utiliza la [API en la nube de Firecrawl](https://firecrawl.dev/) para búsqueda y raspado web. Si prefieres ejecutar Firecrawl localmente, puedes apuntar Hermes a una instancia auto-alojada en su lugar.

**Lo que obtienes:** Sin clave API requerida, sin límites de velocidad, sin costos por página, soberanía de datos completa.

**Lo que pierdes:** La versión en la nube utiliza el "Fire-engine" propietario de Firecrawl para eludir protecciones anti-bots avanzadas (Cloudflare, CAPTCHAs, rotación de IP). El auto-alojado utiliza fetch básico + Playwright, por lo que algunos sitios protegidos pueden fallar. La búsqueda utiliza DuckDuckGo en lugar de Google.

**Configuración:**

1. Clona e inicia la pila de Docker de Firecrawl (5 contenedores: API, Playwright, Redis, RabbitMQ, PostgreSQL — requiere ~4-8 GB de RAM):
   ```bash
   git clone https://github.com/mendableai/firecrawl
   cd firecrawl
   # En .env, establece: USE_DB_AUTHENTICATION=false
   docker compose up -d
   ```

2. Apunta Hermes a tu instancia (sin clave API requerida):
   ```bash
   hermes config set FIRECRAWL_API_URL http://localhost:3002
   ```

También puedes establecer tanto `FIRECRAWL_API_KEY` como `FIRECRAWL_API_URL` si tu instancia auto-alojada tiene autenticación habilitada.

## Enrutamiento de proveedor de OpenRouter

Cuando uses OpenRouter, puedes controlar cómo se enrutan las solicitudes a través de proveedores. Agrega una sección `provider_routing` a `~/.hermes/config.yaml`:

```yaml
provider_routing:
  sort: "throughput"          # "price" (predeterminado), "throughput", o "latency"
  # only: ["anthropic"]      # Solo usa estos proveedores
  # ignore: ["deepinfra"]    # Omite estos proveedores
  # order: ["anthropic", "google"]  # Intenta proveedores en este orden
  # require_parameters: true  # Solo usa proveedores que soporten todos los parámetros de solicitud
  # data_collection: "deny"   # Excluye proveedores que puedan almacenar/entrenar con datos
```

**Atajos:** Agrega `:nitro` a cualquier nombre de modelo para ordenamiento de rendimiento (p. ej., `anthropic/claude-sonnet-4:nitro`), o `:floor` para ordenamiento de precio.

## Configuración de backend de terminal

Configura qué entorno utiliza el agente para comandos de terminal:

```yaml
terminal:
  backend: local    # o: docker, ssh, singularity, modal, daytona
  cwd: "."          # Directorio de trabajo ("." = directorio actual)
  timeout: 180      # Tiempo de espera del comando en segundos

  # Configuración específica de Docker
  docker_image: "nikolaik/python-nodejs:python3.11-nodejs20"
  docker_volumes:                    # Comparte directorios del host con el contenedor
    - "/home/user/projects:/workspace/projects"
    - "/home/user/data:/data:ro"     # :ro para solo lectura

  # Límites de recursos del contenedor (docker, singularity, modal, daytona)
  container_cpu: 1                   # Núcleos de CPU
  container_memory: 5120             # MB (predeterminado 5GB)
  container_disk: 51200              # MB (predeterminado 50GB)
  container_persistent: true         # Persisten el sistema de archivos en sesiones
```

### Montajes de volumen de Docker

Al usar el backend de Docker, `docker_volumes` te permite compartir directorios del host con el contenedor. Cada entrada utiliza la sintaxis estándar de Docker `-v`: `host_path:container_path[:options]`.

```yaml
terminal:
  backend: docker
  docker_volumes:
    - "/home/user/projects:/workspace/projects"   # Lectura-escritura (predeterminado)
    - "/home/user/datasets:/data:ro"              # Solo lectura
    - "/home/user/outputs:/outputs"               # El agente escribe, tú lees
```

Esto es útil para:
- **Proporcionar archivos** al agente (conjuntos de datos, configuraciones, código de referencia)
- **Recibir archivos** del agente (código generado, informes, exportaciones)
- **Espacios de trabajo compartidos** donde tú y el agente acceden a los mismos archivos

También se puede establecer mediante variable de entorno: `TERMINAL_DOCKER_VOLUMES='["/host:/container"]'` (matriz JSON).

Consulta [Code Execution](features/code-execution.md) y la [sección Terminal del README](features/tools.md) para obtener detalles sobre cada backend.

## Configuración de memoria

```yaml
memory:
  memory_enabled: true
  user_profile_enabled: true
  memory_char_limit: 2200   # ~800 tokens
  user_char_limit: 1375     # ~500 tokens
```

## Aislamiento de worktree de Git

Habilita worktrees de git aislados para ejecutar múltiples agentes en paralelo en el mismo repositorio:

```yaml
worktree: true    # Siempre crea un worktree (igual a hermes -w)
# worktree: false # Predeterminado — solo cuando se pasa la bandera -w
```

Cuando está habilitado, cada sesión de CLI crea un worktree fresco bajo `.worktrees/` con su propia rama. Los agentes pueden editar archivos, hacer commit, push y crear PRs sin interferirse entre sí. Los worktrees limpios se eliminan al salir; los sucios se guardan para recuperación manual.

También puedes enumerar archivos ignorados por git para copiar en worktrees a través de `.worktreeinclude` en la raíz de tu repositorio:

```
# .worktreeinclude
.env
.venv/
node_modules/
```

## Compresión de contexto

```yaml
compression:
  enabled: true
  threshold: 0.85              # Comprimir al 85% del límite de contexto
  summary_model: "google/gemini-3-flash-preview"   # Modelo para resumen
  # summary_provider: "auto"   # "auto", "openrouter", "nous", "main"
```

El `summary_model` debe admitir una longitud de contexto al menos tan grande como la de tu modelo principal, ya que recibe la sección intermedia completa de la conversación para compresión.

## Presión de presupuesto de iteración

Cuando el agente está trabajando en una tarea compleja con muchas llamadas de herramientas, puede quemar su presupuesto de iteración (predeterminado: 90 turnos) sin darse cuenta de que se está agotando. La presión de presupuesto advierte automáticamente al modelo a medida que se acerca al límite:

| Umbral | Nivel | Lo que ve el modelo |
|--------|-------|---------------------|
| **70%** | Precaución | `[BUDGET: 63/90. 27 iterations left. Start consolidating.]` |
| **90%** | Advertencia | `[BUDGET WARNING: 81/90. Only 9 left. Respond NOW.]` |

Las advertencias se inyectan en el JSON del último resultado de herramienta (como un campo `_budget_warning`) en lugar de como mensajes separados — esto preserva el almacenamiento en caché de indicadores y no interrumpe la estructura de la conversación.

```yaml
agent:
  max_turns: 90                # Máximo de iteraciones por turno de conversación (predeterminado: 90)
```

La presión de presupuesto está habilitada de forma predeterminada. El agente ve las advertencias naturalmente como parte de los resultados de las herramientas, lo que lo anima a consolidar su trabajo y entregar una respuesta antes de quedarse sin iteraciones.

## Modelos auxiliares

Hermes utiliza modelos "auxiliares" livianos para tareas secundarias como análisis de imágenes, resumen de páginas web y análisis de capturas de pantalla del navegador. Por defecto, estos utilizan **Gemini Flash** a través de OpenRouter o Nous Portal — no necesitas configurar nada.

Para usar un modelo diferente, agrega una sección `auxiliary` a `~/.hermes/config.yaml`:

```yaml
auxiliary:
  # Análisis de imágenes (herramienta vision_analyze + capturas de pantalla del navegador)
  vision:
    provider: "auto"           # "auto", "openrouter", "nous", "main"
    model: ""                  # p. ej. "openai/gpt-4o", "google/gemini-2.5-flash"

  # Resumen de página web + extracción de texto de página del navegador
  web_extract:
    provider: "auto"
    model: ""                  # p. ej. "google/gemini-2.5-flash"
```

### Cambiar el modelo de visión

Para usar GPT-4o en lugar de Gemini Flash para análisis de imágenes:

```yaml
auxiliary:
  vision:
    model: "openai/gpt-4o"
```

O a través de variable de entorno (en `~/.hermes/.env`):

```bash
AUXILIARY_VISION_MODEL=openai/gpt-4o
```

### Opciones de proveedor

| Proveedor | Descripción | Requisitos |
|-----------|-------------|-------------|
| `"auto"` | Mejor disponible (predeterminado). La visión intenta OpenRouter → Nous → Codex. | — |
| `"openrouter"` | Forzar OpenRouter — enruta a cualquier modelo (Gemini, GPT-4o, Claude, etc.) | `OPENROUTER_API_KEY` |
| `"nous"` | Forzar Nous Portal | `hermes login` |
| `"codex"` | Forzar Codex OAuth (cuenta ChatGPT). Admite visión (gpt-5.3-codex). | `hermes model` → Codex |
| `"main"` | Utiliza tu punto de extremo personalizado (`OPENAI_BASE_URL` + `OPENAI_API_KEY`). Funciona con OpenAI, modelos locales o cualquier API compatible con OpenAI. | `OPENAI_BASE_URL` + `OPENAI_API_KEY` |

### Configuraciones comunes

**Usar clave de API de OpenAI para visión:**
```yaml
# En ~/.hermes/.env:
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_API_KEY=sk-...

auxiliary:
  vision:
    provider: "main"
    model: "gpt-4o"       # o "gpt-4o-mini" para más económico
```

**Usar OpenRouter para visión** (enruta a cualquier modelo):
```yaml
auxiliary:
  vision:
    provider: "openrouter"
    model: "openai/gpt-4o"      # o "google/gemini-2.5-flash", etc.
```

**Usar Codex OAuth** (cuenta ChatGPT Pro/Plus — no se necesita clave API):
```yaml
auxiliary:
  vision:
    provider: "codex"     # utiliza tu token OAuth de ChatGPT
    # model toma el valor predeterminado gpt-5.3-codex (admite visión)
```

**Usar un modelo local/auto-alojado:**
```yaml
auxiliary:
  vision:
    provider: "main"      # utiliza tu punto de extremo OPENAI_BASE_URL
    model: "my-local-model"
```

:::tip
Si utilizas Codex OAuth como proveedor principal de modelos, la visión funciona automáticamente — no se requiere configuración adicional. Codex se incluye en la cadena de autodetección para visión.
:::

:::warning
**La visión requiere un modelo multimodal.** Si estableces `provider: "main"`, asegúrate de que tu punto de extremo admita multimodal/visión — de lo contrario, el análisis de imágenes fallará.
:::

### Variables de entorno

También puedes configurar modelos auxiliares mediante variables de entorno en lugar de `config.yaml`:

| Configuración | Variable de entorno |
|--------|---------------------|
| Proveedor de visión | `AUXILIARY_VISION_PROVIDER` |
| Modelo de visión | `AUXILIARY_VISION_MODEL` |
| Proveedor de extracción web | `AUXILIARY_WEB_EXTRACT_PROVIDER` |
| Modelo de extracción web | `AUXILIARY_WEB_EXTRACT_MODEL` |
| Proveedor de compresión | `CONTEXT_COMPRESSION_PROVIDER` |
| Modelo de compresión | `CONTEXT_COMPRESSION_MODEL` |

:::tip
Ejecuta `hermes config` para ver tu configuración actual de modelos auxiliares. Las anulaciones solo se muestran cuando difieren de los valores predeterminados.
:::

## Esfuerzo de razonamiento

Controla cuánto "pensamiento" hace el modelo antes de responder:

```yaml
agent:
  reasoning_effort: ""   # vacío = medio (predeterminado). Opciones: xhigh (máximo), high, medium, low, minimal, none
```

Cuando no se establece (predeterminado), el esfuerzo de razonamiento toma el valor predeterminado "medium" — un nivel equilibrado que funciona bien para la mayoría de tareas. Establecer un valor lo anula — un esfuerzo de razonamiento más alto da mejores resultados en tareas complejas al costo de más tokens y latencia.

También puedes cambiar el esfuerzo de razonamiento en tiempo de ejecución con el comando `/reasoning`:

```
/reasoning           # Mostrar el nivel de esfuerzo actual y estado de visualización
/reasoning high      # Establecer el esfuerzo de razonamiento a high
/reasoning none      # Desactivar razonamiento
/reasoning show      # Mostrar el pensamiento del modelo por encima de cada respuesta
/reasoning hide      # Ocultar el pensamiento del modelo
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

## Configuración de pantalla

```yaml
display:
  tool_progress: all    # off | new | all | verbose
  personality: "kawaii"  # Personalidad predeterminada para la CLI
  compact: false         # Modo de salida compacta (menos espacios en blanco)
  resume_display: full   # full (mostrar mensajes anteriores al reanudar) | minimal (solo una línea)
  bell_on_complete: false  # Tocar la campana de terminal cuando el agente termina (excelente para tareas largas)
  show_reasoning: false    # Mostrar razonamiento/pensamiento del modelo por encima de cada respuesta (alternar con /reasoning show|hide)
```

| Modo | Qué ves |
|------|---------|
| `off` | Silencioso — solo la respuesta final |
| `new` | Indicador de herramienta solo cuando la herramienta cambia |
| `all` | Cada llamada de herramienta con una vista previa corta (predeterminado) |
| `verbose` | Args completos, resultados y registros de depuración |

## Conversión de voz a texto (STT)

```yaml
stt:
  provider: "openai"           # Proveedor de STT
```

Requiere `VOICE_TOOLS_OPENAI_KEY` en `.env` para STT de OpenAI.

## Comandos rápidos

Define comandos personalizados que ejecutan comandos de shell sin invocar el LLM — cero uso de tokens, ejecución instantánea. Especialmente útil desde plataformas de mensajería (Telegram, Discord, etc.) para verificaciones rápidas del servidor o scripts de utilidad.

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

Uso: escribe `/status`, `/disk`, `/update` o `/gpu` en la CLI o en cualquier plataforma de mensajería. El comando se ejecuta localmente en el host y devuelve la salida directamente — sin llamada LLM, sin tokens consumidos.

- **Tiempo de espera de 30 segundos** — los comandos de larga duración se matan con un mensaje de error
- **Prioridad** — los comandos rápidos se verifican antes que los comandos de habilidad, por lo que puedes anular nombres de habilidades
- **Tipo** — solo se admite `exec` (ejecuta un comando de shell); otros tipos muestran un error
- **Funciona en todas partes** — CLI, Telegram, Discord, Slack, WhatsApp, Signal

## Retardo humano

Simula un ritmo de respuesta similar al humano en plataformas de mensajería:

```yaml
human_delay:
  mode: "off"                  # off | natural | custom
  min_ms: 500                  # Retardo mínimo (modo custom)
  max_ms: 2000                 # Retardo máximo (modo custom)
```

## Ejecución de código

Configura la herramienta de ejecución de código Python en sandbox:

```yaml
code_execution:
  timeout: 300                 # Tiempo máximo de ejecución en segundos
  max_tool_calls: 50           # Máximo de llamadas de herramientas dentro de la ejecución de código
```

## Navegador

Configura el comportamiento de automatización del navegador:

```yaml
browser:
  inactivity_timeout: 120        # Segundos antes de cerrar automáticamente sesiones inactivas
  record_sessions: false         # Grabar automáticamente sesiones del navegador como videos WebM en ~/.hermes/browser_recordings/
```

## Puntos de control

Instantáneas automáticas del sistema de archivos antes de operaciones destructivas. Consulta la [página de características de Puntos de control](/docs/user-guide/features/checkpoints) para obtener detalles.

```yaml
checkpoints:
  enabled: false                 # Habilitar puntos de control automáticos (también: hermes --checkpoints)
  max_snapshots: 50              # Máximo de puntos de control a mantener por directorio
```


## Delegación

Configura el comportamiento del subagente para la herramienta delegate:

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

**Anulación de proveedor:modelo del subagente:** Por defecto, los subagentes heredan el proveedor y modelo del agente padre. Establece `delegation.provider` y `delegation.model` para enrutar subagentes a un par proveedor:modelo diferente — p. ej., usa un modelo económico/rápido para subtareas de alcance estrecho mientras tu agente principal ejecuta un modelo de razonamiento costoso.

El proveedor de delegación utiliza la misma resolución de credenciales que la inicio de la CLI/gateway. Todos los proveedores configurados se admiten: `openrouter`, `nous`, `zai`, `kimi-coding`, `minimax`, `minimax-cn`. Cuando se establece un proveedor, el sistema resuelve automáticamente la URL base correcta, la clave de API y el modo de API — sin necesidad de cableado manual de credenciales.

**Precedencia:** `delegation.provider` en config → proveedor padre (heredado). `delegation.model` en config → modelo padre (heredado). Establecer solo `model` sin `provider` cambia solo el nombre del modelo mientras se mantienen las credenciales del padre (útil para cambiar modelos dentro del mismo proveedor como OpenRouter).

## Aclaración

Configura el comportamiento del aviso de aclaración:

```yaml
clarify:
  timeout: 120                 # Segundos para esperar la respuesta de aclaración del usuario
```

## Archivos de contexto (SOUL.md, AGENTS.md)

Coloca estos archivos en tu directorio de proyecto y el agente los detecta automáticamente:

| Archivo | Propósito |
|--------|---------|
| `AGENTS.md` | Instrucciones específicas del proyecto, convenciones de codificación |
| `SOUL.md` | Definición de personalidad — el agente encarna esta personalidad |
| `.cursorrules` | Reglas del IDE Cursor (también detectadas) |
| `.cursor/rules/*.mdc` | Archivos de reglas de Cursor (también detectados) |

- **AGENTS.md** es jerárquico: si los subdirectorios también tienen AGENTS.md, todos se combinan.
- **SOUL.md** verifica primero cwd, luego `~/.hermes/SOUL.md` como respaldo global.
- Todos los archivos de contexto tienen un límite de 20,000 caracteres con truncamiento inteligente.

## Directorio de trabajo

| Contexto | Predeterminado |
|---------|---------|
| **CLI (`hermes`)** | Directorio actual donde ejecutas el comando |
| **Gateway de mensajería** | Directorio de inicio `~` (anular con `MESSAGING_CWD`) |
| **Docker / Singularity / Modal / SSH** | Directorio de inicio del usuario dentro del contenedor o máquina remota |

Anula el directorio de trabajo:
```bash
# En ~/.hermes/.env o ~/.hermes/config.yaml:
MESSAGING_CWD=/home/myuser/projects    # Sesiones de gateway
TERMINAL_CWD=/workspace                # Todas las sesiones de terminal
```
