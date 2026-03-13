# Configuration.md — Translation Replacements (Ready to Apply)

This document contains all replacements formatted for `multi_replace_string_in_file` tool application.

**File:** `docs/user-guide/configuration.md`

---

## BATCH 1: Frontmatter & Main Headings (4 replacements)

### Replacement 1: Frontmatter description
**Line:** 3
**Type:** YAML frontmatter

Old String (with 2 lines context):
```
sidebar_position: 2
title: "Configuración"
description: "Configure Hermes Agent — config.yaml, providers, models, API keys, and more"
---
```

New String:
```
sidebar_position: 2
title: "Configuración"
description: "Configura Hermes Agent — config.yaml, proveedores, modelos, claves API, y más"
---
```

---

### Replacement 2: Main heading and intro text
**Lines:** 6-8
**Type:** Markdown heading + prose

Old String:
```
# Configuration

All settings are stored in the `~/.hermes/` directory for easy access.

## Directory Structure
```

New String:
```
# Configuración

Todos los ajustes se almacenan en el directorio `~/.hermes/` para un fácil acceso.

## Estructura de directorio
```

---

### Replacement 3: Managing Configuration heading
**Lines:** 25-27
**Type:** Markdown heading + command list

Old String:
```
## Managing Configuration

```bash
hermes config              # View current configuration
hermes config edit         # Open config.yaml in your editor
hermes config set KEY VAL  # Set a specific value
hermes config check        # Check for missing options (after updates)
hermes config migrate      # Interactively add missing options

# Examples:
```

New String:
```
## Gestión de configuración

```bash
hermes config              # Vea la configuración actual
hermes config edit         # Abre config.yaml en tu editor
hermes config set KEY VAL  # Establece un valor específico
hermes config check        # Verifica opciones faltantes (después de actualizaciones)
hermes config migrate      # Agrega interactivamente opciones faltantes

# Ejemplos:
```

---

### Replacement 4: Managing Configuration tip
**Lines:** 37-40
**Type:** Markdown tip box

Old String:
```
:::tip
The `hermes config set` command automatically routes values to the right file — API keys are saved to `.env`, everything else to `config.yaml`.
:::
```

New String:
```
:::tip
El comando `hermes config set` automáticamente enruta los valores al archivo correcto — las claves API se guardan en `.env`, todo lo demás en `config.yaml`.
:::
```

---

## BATCH 2: Configuration Precedence Section (3 replacements)

### Replacement 5: Configuration Precedence heading & intro
**Lines:** 44-49
**Type:** Markdown heading + list

Old String:
```
## Configuration Precedence

Settings are resolved in this order (highest priority first):

1. **CLI arguments** — e.g., `hermes chat --model anthropic/claude-sonnet-4` (per-invocation override)
```

New String:
```
## Precedencia de configuración

Los ajustes se resuelven en este orden (mayor prioridad primero):

1. **Argumentos CLI** — p. ej., `hermes chat --model anthropic/claude-sonnet-4` (anulación por invocación)
```

---

### Replacement 6: Configuration Precedence list items 2-4
**Lines:** 50-52
**Type:** Numbered list

Old String:
```
1. **CLI arguments** — e.g., `hermes chat --model anthropic/claude-sonnet-4` (per-invocation override)
2. **`~/.hermes/config.yaml`** — the primary config file for all non-secret settings
3. **`~/.hermes/.env`** — fallback for env vars; **required** for secrets (API keys, tokens, passwords)
4. **Built-in defaults** — hardcoded safe defaults when nothing else is set
```

New String:
```
1. **Argumentos CLI** — p. ej., `hermes chat --model anthropic/claude-sonnet-4` (anulación por invocación)
2. **`~/.hermes/config.yaml`** — el archivo de configuración principal para todos los ajustes no secretos
3. **`~/.hermes/.env`** — respaldo para variables de entorno; **requerido** para secretos (claves API, tokens, contraseñas)
4. **Valores por defecto integrados** — valores predeterminados seguros codificados cuando nada más está configurado
```

---

### Replacement 7: Configuration Precedence info box
**Lines:** 54-58
**Type:** Markdown info box

Old String:
```
:::info Rule of Thumb
Secrets (API keys, bot tokens, passwords) go in `.env`. Everything else (model, terminal backend, compression settings, memory limits, toolsets) goes in `config.yaml`. When both are set, `config.yaml` wins for non-secret settings.
:::
```

New String:
```
:::info Regla general
Los secretos (claves API, tokens de bots, contraseñas) van en `.env`. Todo lo demás (modelo, backend de terminal, ajustes de compresión, límites de memoria, conjuntos de herramientas) va en `config.yaml`. Cuando ambos están configurados, `config.yaml` gana para ajustes no secretos.
:::
```

---

## BATCH 3: Inference Providers Section (5 replacements)

### Replacement 8: Inference Providers heading & intro
**Lines:** 63-67
**Type:** Markdown heading + intro text

Old String:
```
## Inference Providers

You need at least one way to connect to an LLM. Use `hermes model` to switch providers and models interactively, or configure directly:

| Provider | Setup |
```

New String:
```
## Proveedores de inferencia

Necesitas al menos una forma de conectar a un LLM. Usa `hermes model` para cambiar proveedores y modelos interactivamente, o configura directamente:

| Proveedor | Configuración |
```

---

### Replacement 9: Inference Providers Codex note
**Lines:** 80-82
**Type:** Markdown info box

Old String:
```
:::info Codex Note
The OpenAI Codex provider authenticates via device code (open a URL, enter a code). Credentials are stored at `~/.codex/auth.json` and auto-refresh. No Codex CLI installation required.
:::
```

New String:
```
:::info Nota sobre Codex
El proveedor OpenAI Codex se autentica mediante código de dispositivo (abre una URL, ingresa un código). Las credenciales se almacenan en `~/.codex/auth.json` y se actualizan automáticamente. No se requiere instalación de Codex CLI.
:::
```

---

### Replacement 10: Inference Providers warning box
**Lines:** 84-88
**Type:** Markdown warning box

Old String:
```
:::warning
Even when using Nous Portal, Codex, or a custom endpoint, some tools (vision, web summarization, MoA) use a separate "auxiliary" model — by default Gemini Flash via OpenRouter. An `OPENROUTER_API_KEY` enables these tools automatically. You can also configure which model and provider these tools use — see [Auxiliary Models](#auxiliary-models) below.
:::
```

New String:
```
:::warning
Incluso cuando usas Nous Portal, Codex, o un punto de conexión personalizado, algunas herramientas (visión, resumen web, MoA) usan un modelo "auxiliar" separado — por defecto Gemini Flash a través de OpenRouter. Una `OPENROUTER_API_KEY` habilita estas herramientas automáticamente. También puedes configurar qué modelo y proveedor utilizan estas herramientas — ver [Modelos auxiliares](#auxiliary-models) abajo.
:::
```

---

## BATCH 4: Anthropic Section (3 replacements)

### Replacement 11: Anthropic heading & intro
**Lines:** 95-99
**Type:** Markdown heading + intro text

Old String:
```
### Anthropic (Native)

Use Claude models directly through the Anthropic API — no OpenRouter proxy needed. Supports three auth methods:

```bash
```

New String:
```
### Anthropic (Nativa)

Usa modelos Claude directamente a través de la API de Anthropic — no se necesita proxy OpenRouter. Admite tres métodos de autenticación:

```bash
```

---

### Replacement 12: Anthropic comments in code
**Lines:** 101-112
**Type:** Code comments in bash block

Old String:
```
```bash
# With an API key (pay-per-token)
export ANTHROPIC_API_KEY=sk-ant-api03-...
hermes chat --provider anthropic --model claude-sonnet-4-6

# With a Claude Code setup-token (Pro/Max subscription)
export ANTHROPIC_API_KEY=sk-ant-oat01-...  # from 'claude setup-token'
hermes chat --provider anthropic

# Auto-detect Claude Code credentials (if you have Claude Code installed)
hermes chat --provider anthropic  # reads ~/.claude.json automatically
```

Or set it permanently:
```

New String:
```
```bash
# Con una clave API (pago por token)
export ANTHROPIC_API_KEY=sk-ant-api03-...
hermes chat --provider anthropic --model claude-sonnet-4-6

# Con un token de configuración de Claude Code (suscripción Pro/Max)
export ANTHROPIC_API_KEY=sk-ant-oat01-...  # from 'claude setup-token'
hermes chat --provider anthropic

# Detectar automáticamente credenciales de Claude Code (si tienes Claude Code instalado)
hermes chat --provider anthropic  # reads ~/.claude.json automatically
```

O establécelo permanentemente:
```

---

### Replacement 13: Anthropic tip box
**Lines:** 125-127
**Type:** Markdown tip box

Old String:
```
:::tip Aliases
`--provider claude` and `--provider claude-code` also work as shorthand for `--provider anthropic`.
:::
```

New String:
```
:::tip Alias
`--provider claude` y `--provider claude-code` también funcionan como abreviaturas para `--provider anthropic`.
:::
```

---

## BATCH 5: Chinese AI Providers Section (3 replacements)

### Replacement 14: Chinese AI Providers heading & intro
**Lines:** 132-156
**Type:** Markdown heading + intro text

Old String:
```
### First-Class Chinese AI Providers

These providers have built-in support with dedicated provider IDs. Set the API key and use `--provider` to select:

```bash
# z.ai / ZhipuAI GLM
```

New String:
```
### Proveedores de IA chinos de primera clase

Estos proveederes tienen soporte integrado con IDs de proveedor dedicados. Establece la clave API y usa `--provider` para seleccionar:

```bash
# z.ai / ZhipuAI GLM
```

---

### Replacement 15: Chinese AI Providers comments
**Lines:** 157-176
**Type:** Code comments in bash block

Old String:
```bash
# z.ai / ZhipuAI GLM
hermes chat --provider zai --model glm-4-plus
# Requires: GLM_API_KEY in ~/.hermes/.env

# Kimi / Moonshot AI
hermes chat --provider kimi-coding --model moonshot-v1-auto
# Requires: KIMI_API_KEY in ~/.hermes/.env

# MiniMax (global endpoint)
hermes chat --provider minimax --model MiniMax-Text-01
# Requires: MINIMAX_API_KEY in ~/.hermes/.env

# MiniMax (China endpoint)
hermes chat --provider minimax-cn --model MiniMax-Text-01
# Requires: MINIMAX_CN_API_KEY in ~/.hermes/.env
```

Or set the provider permanently in `config.yaml`:
```

New String:
```bash
# z.ai / ZhipuAI GLM
hermes chat --provider zai --model glm-4-plus
# Requiere: GLM_API_KEY en ~/.hermes/.env

# Kimi / Moonshot AI
hermes chat --provider kimi-coding --model moonshot-v1-auto
# Requiere: KIMI_API_KEY en ~/.hermes/.env

# MiniMax (punto de conexión global)
hermes chat --provider minimax --model MiniMax-Text-01
# Requiere: MINIMAX_API_KEY en ~/.hermes/.env

# MiniMax (punto de conexión de China)
hermes chat --provider minimax-cn --model MiniMax-Text-01
# Requiere: MINIMAX_CN_API_KEY en ~/.hermes/.env
```

O establece el proveedor permanentemente en `config.yaml`:
```

---

### Replacement 16: Chinese AI Providers closing text
**Lines:** 183-185
**Type:** Prose text

Old String:
```
Base URLs can be overridden with `GLM_BASE_URL`, `KIMI_BASE_URL`, `MINIMAX_BASE_URL`, or `MINIMAX_CN_BASE_URL` environment variables.

## Custom & Self-Hosted LLM Providers
```

New String:
```
Las URL base se pueden anular con variables de entorno `GLM_BASE_URL`, `KIMI_BASE_URL`, `MINIMAX_BASE_URL`, o `MINIMAX_CN_BASE_URL`.

## Proveedores de LLM personalizados y autoalojados
```

---

## BATCH 6: Custom & Self-Hosted LLM Providers (2 replacements)

### Replacement 17: Custom LLM Providers intro
**Lines:** 182-195
**Type:** Markdown heading + intro + subheading

Old String:
```
## Custom & Self-Hosted LLM Providers

Hermes Agent works with **any OpenAI-compatible API endpoint**. If a server implements `/v1/chat/completions`, you can point Hermes at it. This means you can use local models, GPU inference servers, multi-provider routers, or any third-party API.

### General Setup

Two ways to configure a custom endpoint:

**Interactive (recommended):**
```bash
hermes model
# Select "Custom endpoint (self-hosted / VLLM / etc.)"
# Enter: API base URL, API key, Model name
```

**Manual (`.env` file):**
```bash
# Add to ~/.hermes/.env
OPENAI_BASE_URL=http://localhost:8000/v1
OPENAI_API_KEY=your-key-or-dummy
LLM_MODEL=your-model-name
```

Everything below follows this same pattern — just change the URL, key, and model name.
```

New String:
```
## Proveedores de LLM personalizados y autoalojados

Hermes Agent funciona con **cualquier punto de conexión de API compatible con OpenAI**. Si un servidor implementa `/v1/chat/completions`, puedes apuntar Hermes a él. Esto significa que puedes usar modelos locales, servidores de inferencia GPU, enrutadores multipropósito, o cualquier API de terceros.

### Configuración general

Dos formas de configurar un punto de conexión personalizado:

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

Todo lo siguiente sigue el mismo patrón — solo cambia la URL, la clave y el nombre del modelo.
```

---

## BATCH 7: Ollama Section (2 replacements)

### Replacement 18: Ollama heading & intro
**Lines:** 211-215
**Type:** Markdown heading + intro + comments

Old String:
```
### Ollama — Local Models, Zero Config

[Ollama](https://ollama.com/) runs open-weight models locally with one command. Best for: quick local experimentation, privacy-sensitive work, offline use.

```bash
# Install and run a model
```

New String:
```
### Ollama — Modelos locales, cero configuración

[Ollama](https://ollama.com/) ejecuta modelos de peso abierto localmente con un comando. Mejor para: experimentación local rápida, trabajo sensible a la privacidad, uso sin conexión.

```bash
# Instala y ejecuta un modelo
```

---

### Replacement 19: Ollama comments & closing
**Lines:** 216-230
**Type:** Code comments in bash block + prose

Old String:
```bash
# Install and run a model
ollama pull llama3.1:70b
ollama serve   # Starts on port 11434

# Configure Hermes
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama           # Any non-empty string
LLM_MODEL=llama3.1:70b
```

Ollama's OpenAI-compatible endpoint supports chat completions, streaming, and tool calling (for supported models). No GPU required for smaller models — Ollama handles CPU inference automatically.

:::tip
List available models with `ollama list`. Pull any model from the [Ollama library](https://ollama.com/library) with `ollama pull <model>`.
:::
```

New String:
```bash
# Instala y ejecuta un modelo
ollama pull llama3.1:70b
ollama serve   # Starts on port 11434

# Configura Hermes
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama           # Any non-empty string
LLM_MODEL=llama3.1:70b
```

El punto de conexión compatible con OpenAI de Ollama admite finalizaciones de chat, transmisión y llamadas de herramientas (para modelos compatibles). No se requiere GPU para modelos más pequeños — Ollama maneja la inferencia de CPU automáticamente.

:::tip
Enumera los modelos disponibles con `ollama list`. Extrae cualquier modelo de la [biblioteca de Ollama](https://ollama.com/library) con `ollama pull <model>`.
:::
```

---

## BATCH 8: vLLM Section (2 replacements)

### Replacement 20: vLLM heading & intro
**Lines:** 237-248
**Type:** Markdown heading + intro + code comments

Old String:
```
### vLLM — High-Performance GPU Inference

[vLLM](https://docs.vllm.ai/) is the standard for production LLM serving. Best for: maximum throughput on GPU hardware, serving large models, continuous batching.

```bash
# Start vLLM server
pip install vllm
vllm serve meta-llama/Llama-3.1-70B-Instruct \
  --port 8000 \
  --tensor-parallel-size 2    # Multi-GPU

# Configure Hermes
```

New String:
```
### vLLM — Inferencia de GPU de alto rendimiento

[vLLM](https://docs.vllm.ai/) es el estándar para servir LLM en producción. Mejor para: máximo rendimiento en hardware GPU, servir modelos grandes, procesamiento por lotes continuo.

```bash
# Inicia servidor vLLM
pip install vllm
vllm serve meta-llama/Llama-3.1-70B-Instruct \
  --port 8000 \
  --tensor-parallel-size 2    # GPU múltiple

# Configura Hermes
```

---

### Replacement 21: vLLM closing
**Lines:** 253-256
**Type:** Prose text

Old String:
```
vLLM supports tool calling, structured output, and multi-modal models. Use `--enable-auto-tool-choice` and `--tool-call-parser hermes` for Hermes-format tool calling with NousResearch models.

---
```

New String:
```
vLLM admite llamadas de herramientas, salida estructurada y modelos multimodales. Usa `--enable-auto-tool-choice` y `--tool-call-parser hermes` para llamadas de herramientas en formato Hermes con modelos de NousResearch.

---
```

---

## BATCH 9: SGLang Section (1 replacement)

### Replacement 22: SGLang heading & intro
**Lines:** 257-265
**Type:** Markdown heading + intro + code comments

Old String:
```
### SGLang — Fast Serving with RadixAttention

[SGLang](https://github.com/sgl-project/sglang) is an alternative to vLLM with RadixAttention for KV cache reuse. Best for: multi-turn conversations (prefix caching), constrained decoding, structured output.

```bash
# Start SGLang server
pip install sglang[all]
python -m sglang.launch_server \
  --model meta-llama/Llama-3.1-70B-Instruct \
  --port 8000 \
  --tp 2

# Configure Hermes
```

New String:
```
### SGLang — Servicio rápido con RadixAttention

[SGLang](https://github.com/sgl-project/sglang) es una alternativa a vLLM con RadixAttention para reutilización de caché KV. Mejor para: conversaciones multi-turno (caché de prefijo), decodificación restringida, salida estructurada.

```bash
# Inicia servidor SGLang
pip install sglang[all]
python -m sglang.launch_server \
  --model meta-llama/Llama-3.1-70B-Instruct \
  --port 8000 \
  --tp 2

# Configura Hermes
```

---

## BATCH 10: llama.cpp / llama-server Section (2 replacements)

### Replacement 23: llama.cpp heading & intro
**Lines:** 275-290
**Type:** Markdown heading + intro + code comments

Old String:
```
### llama.cpp / llama-server — CPU & Metal Inference

[llama.cpp](https://github.com/ggml-org/llama.cpp) runs quantized models on CPU, Apple Silicon (Metal), and consumer GPUs. Best for: running models without a datacenter GPU, Mac users, edge deployment.

```bash
# Build and start llama-server
cmake -B build && cmake --build build --config Release
./build/bin/llama-server \
  -m models/llama-3.1-8b-instruct-Q4_K_M.gguf \
  --port 8080 --host 0.0.0.0

# Configure Hermes
```

New String:
```
### llama.cpp / llama-server — Inferencia de CPU y Metal

[llama.cpp](https://github.com/ggml-org/llama.cpp) ejecuta modelos cuantizados en CPU, Apple Silicon (Metal) y GPU de consumidor. Mejor para: ejecutar modelos sin una GPU de centro de datos, usuarios de Mac, implementación perimetral.

```bash
# Construye e inicia llama-server
cmake -B build && cmake --build build --config Release
./build/bin/llama-server \
  -m models/llama-3.1-8b-instruct-Q4_K_M.gguf \
  --port 8080 --host 0.0.0.0

# Configura Hermes
```

---

### Replacement 24: llama.cpp tip box
**Lines:** 293-295
**Type:** Markdown tip box

Old String:
```
:::tip
Download GGUF models from [Hugging Face](https://huggingface.co/models?library=gguf). Q4_K_M quantization offers the best balance of quality vs. memory usage.
:::
```

New String:
```
:::tip
Descarga modelos GGUF de [Hugging Face](https://huggingface.co/models?library=gguf). La cuantización Q4_K_M ofrece el mejor equilibrio de calidad frente al uso de memoria.
:::
```

---

## BATCH 11: LiteLLM Proxy Section (2 replacements)

### Replacement 25: LiteLLM heading & intro
**Lines:** 304-316
**Type:** Markdown heading + intro + code comments

Old String:
```
### LiteLLM Proxy — Multi-Provider Gateway

[LiteLLM](https://docs.litellm.ai/) is an OpenAI-compatible proxy that unifies 100+ LLM providers behind a single API. Best for: switching between providers without config changes, load balancing, fallback chains, budget controls.

```bash
# Install and start
pip install litellm[proxy]
litellm --model anthropic/claude-sonnet-4 --port 4000

# Or with a config file for multiple models:
litellm --config litellm_config.yaml --port 4000

# Configure Hermes
```

New String:
```
### LiteLLM Proxy — Puerta de enlace multipropósito

[LiteLLM](https://docs.litellm.ai/) es un proxy compatible con OpenAI que unifica más de 100 proveedores de LLM detrás de una única API. Mejor para: cambiar entre proveedores sin cambios de configuración, equilibrio de carga, cadenas de respaldo, controles de presupuesto.

```bash
# Instala e inicia
pip install litellm[proxy]
litellm --model anthropic/claude-sonnet-4 --port 4000

# O con un archivo de configuración para múltiples modelos:
litellm --config litellm_config.yaml --port 4000

# Configura Hermes
```

---

### Replacement 26: LiteLLM example description
**Lines:** 320-322
**Type:** Prose text

Old String:
```
Example `litellm_config.yaml` with fallback:
```yaml
model_list:
```

New String:
```
Ejemplo de `litellm_config.yaml` con respaldo:
```yaml
model_list:
```

---

## BATCH 12: ClawRouter Section (2 replacements)

### Replacement 27: ClawRouter heading & intro
**Lines:** 331-341
**Type:** Markdown heading + intro + code comments

Old String:
```
### ClawRouter — Cost-Optimized Routing

[ClawRouter](https://github.com/BlockRunAI/ClawRouter) by BlockRunAI is a local routing proxy that auto-selects models based on query complexity. It classifies requests across 14 dimensions and routes to the cheapest model that can handle the task. Payment is via USDC cryptocurrency (no API keys).

```bash
# Install and start
npx @blockrun/clawrouter    # Starts on port 8402

# Configure Hermes
```

New String:
```
### ClawRouter — Enrutamiento optimizado por costo

[ClawRouter](https://github.com/BlockRunAI/ClawRouter) de BlockRunAI es un proxy de enrutamiento local que selecciona automáticamente modelos según la complejidad de la consulta. Clasifica solicitudes en 14 dimensiones y enruta al modelo más barato que pueda manejar la tarea. El pago es a través de criptomoneda USDC (sin claves API).

```bash
# Instala e inicia
npx @blockrun/clawrouter    # Starts on port 8402

# Configura Hermes
```

---

### Replacement 28: ClawRouter table header & note
**Lines:** 343-362
**Type:** Table header + note box

Old String:
```
Routing profiles:
| Profile | Strategy | Savings |
|---------|----------|---------|
| `blockrun/auto` | Balanced quality/cost | 74-100% |
| `blockrun/eco` | Cheapest possible | 95-100% |
| `blockrun/premium` | Best quality models | 0% |
| `blockrun/free` | Free models only | 100% |
| `blockrun/agentic` | Optimized for tool use | varies |

:::note
ClawRouter requires a USDC-funded wallet on Base or Solana for payment. All requests route through BlockRun's backend API. Run `npx @blockrun/clawrouter doctor` to check wallet status.
:::
```

New String:
```
Perfiles de enrutamiento:
| Perfil | Estrategia | Ahorros |
|--------|-----------|---------|
| `blockrun/auto` | Balanced quality/cost | 74-100% |
| `blockrun/eco` | Cheapest possible | 95-100% |
| `blockrun/premium` | Best quality models | 0% |
| `blockrun/free` | Free models only | 100% |
| `blockrun/agentic` | Optimized for tool use | varies |

:::note
ClawRouter requiere una billetera financiada con USDC en Base o Solana para el pago. Todas las solicitudes se enrutan a través de la API de backend de BlockRun. Ejecuta `npx @blockrun/clawrouter doctor` para verificar el estado de la billetera.
:::
```

---

## BATCH 13: Other Compatible Providers (1 replacement)

### Replacement 29: Other Compatible Providers heading & intro
**Lines:** 365-390
**Type:** Markdown heading + intro + table + code comment

Old String:
```
### Other Compatible Providers

Any service with an OpenAI-compatible API works. Some popular options:

| Provider | Base URL | Notes |
|----------|----------|-------|
| [Together AI](https://together.ai) | `https://api.together.xyz/v1` | Cloud-hosted open models |
| [Groq](https://groq.com) | `https://api.groq.com/openai/v1` | Ultra-fast inference |
| [DeepSeek](https://deepseek.com) | `https://api.deepseek.com/v1` | DeepSeek models |
| [Fireworks AI](https://fireworks.ai) | `https://api.fireworks.ai/inference/v1` | Fast open model hosting |
| [Cerebras](https://cerebras.ai) | `https://api.cerebras.ai/v1` | Wafer-scale chip inference |
| [Mistral AI](https://mistral.ai) | `https://api.mistral.ai/v1` | Mistral models |
| [OpenAI](https://openai.com) | `https://api.openai.com/v1` | Direct OpenAI access |
| [Azure OpenAI](https://azure.microsoft.com) | `https://YOUR.openai.azure.com/` | Enterprise OpenAI |
| [LocalAI](https://localai.io) | `http://localhost:8080/v1` | Self-hosted, multi-model |
| [Jan](https://jan.ai) | `http://localhost:1337/v1` | Desktop app with local models |

```bash
# Example: Together AI
```

New String:
```
### Otros proveedores compatibles

Cualquier servicio con una API compatible con OpenAI funciona. Algunas opciones populares:

| Proveedor | URL base | Notas |
|-----------|----------|-------|
| [Together AI](https://together.ai) | `https://api.together.xyz/v1` | Cloud-hosted open models |
| [Groq](https://groq.com) | `https://api.groq.com/openai/v1` | Ultra-fast inference |
| [DeepSeek](https://deepseek.com) | `https://api.deepseek.com/v1` | DeepSeek models |
| [Fireworks AI](https://fireworks.ai) | `https://api.fireworks.ai/inference/v1` | Fast open model hosting |
| [Cerebras](https://cerebras.ai) | `https://api.cerebras.ai/v1` | Wafer-scale chip inference |
| [Mistral AI](https://mistral.ai) | `https://api.mistral.ai/v1` | Mistral models |
| [OpenAI](https://openai.com) | `https://api.openai.com/v1` | Direct OpenAI access |
| [Azure OpenAI](https://azure.microsoft.com) | `https://YOUR.openai.azure.com/` | Enterprise OpenAI |
| [LocalAI](https://localai.io) | `http://localhost:8080/v1` | Self-hosted, multi-model |
| [Jan](https://jan.ai) | `http://localhost:1337/v1` | Desktop app with local models |

```bash
# Ejemplo: Together AI
```

---

## BATCH 14: Choosing the Right Setup (2 replacements)

### Replacement 30: Choosing heading & table headers
**Lines:** 405-410
**Type:** Markdown heading + table headers

Old String:
```
### Choosing the Right Setup

| Use Case | Recommended |
|----------|-------------|
| **Just want it to work** | OpenRouter (default) or Nous Portal |
```

New String:
```
### Elegir la configuración correcta

| Caso de uso | Recomendado |
|------------|-------------|
| **Solo quiero que funcione** | OpenRouter (default) or Nous Portal |
```

---

### Replacement 31: Choosing setup table & tip
**Lines:** 411-425
**Type:** Table content + tip box

Old String:
```
| **Just want it to work** | OpenRouter (default) or Nous Portal |
| **Local models, easy setup** | Ollama |
| **Production GPU serving** | vLLM or SGLang |
| **Mac / no GPU** | Ollama or llama.cpp |
| **Multi-provider routing** | LiteLLM Proxy or OpenRouter |
| **Cost optimization** | ClawRouter or OpenRouter with `sort: "price"` |
| **Maximum privacy** | Ollama, vLLM, or llama.cpp (fully local) |
| **Enterprise / Azure** | Azure OpenAI with custom endpoint |
| **Chinese AI models** | z.ai (GLM), Kimi/Moonshot, or MiniMax (first-class providers) |

:::tip
You can switch between providers at any time with `hermes model` — no restart required. Your conversation history, memory, and skills carry over regardless of which provider you use.
:::
```

New String:
```
| **Solo quiero que funcione** | OpenRouter (default) or Nous Portal |
| **Modelos locales, configuración fácil** | Ollama |
| **Servicio de GPU en producción** | vLLM or SGLang |
| **Mac / sin GPU** | Ollama or llama.cpp |
| **Enrutamiento multipropósito** | LiteLLM Proxy or OpenRouter |
| **Optimización de costos** | ClawRouter or OpenRouter with `sort: "price"` |
| **Privacidad máxima** | Ollama, vLLM, or llama.cpp (fully local) |
| **Empresarial / Azure** | Azure OpenAI with custom endpoint |
| **Modelos de IA chinos** | z.ai (GLM), Kimi/Moonshot, or MiniMax (first-class providers) |

:::tip
Puedes cambiar entre proveedores en cualquier momento con `hermes model` — no se requiere reinicio. Tu historial de conversación, memoria y habilidades se transfieren independientemente del proveedor que uses.
:::
```

---

## BATCH 15: Optional API Keys Section (2 replacements)

### Replacement 32: Optional API Keys heading & table header
**Lines:** 428-432
**Type:** Markdown heading + table header

Old String:
```
## Optional API Keys

| Feature | Provider | Env Variable |
|---------|----------|--------------|
| Web scraping | [Firecrawl](https://firecrawl.dev/) | `FIRECRAWL_API_KEY` |
```

New String:
```
## Claves API opcionales

| Función | Proveedor | Variable de entorno |
|---------|-----------|-------------------|
| Raspado web | [Firecrawl](https://firecrawl.dev/) | `FIRECRAWL_API_KEY` |
```

---

### Replacement 33: Optional API Keys table content
**Lines:** 433-441
**Type:** Table content

Old String:
```
| Raspado web | [Firecrawl](https://firecrawl.dev/) | `FIRECRAWL_API_KEY` |
| Browser automation | [Browserbase](https://browserbase.com/) | `BROWSERBASE_API_KEY`, `BROWSERBASE_PROJECT_ID` |
| Image generation | [FAL](https://fal.ai/) | `FAL_KEY` |
| Premium TTS voices | [ElevenLabs](https://elevenlabs.io/) | `ELEVENLABS_API_KEY` |
| OpenAI TTS + voice transcription | [OpenAI](https://platform.openai.com/api-keys) | `VOICE_TOOLS_OPENAI_KEY` |
| RL Training | [Tinker](https://tinker-console.thinkingmachines.ai/) + [WandB](https://wandb.ai/) | `TINKER_API_KEY`, `WANDB_API_KEY` |
| Cross-session user modeling | [Honcho](https://honcho.dev/) | `HONCHO_API_KEY` |
```

New String:
```
| Raspado web | [Firecrawl](https://firecrawl.dev/) | `FIRECRAWL_API_KEY` |
| Automatización del navegador | [Browserbase](https://browserbase.com/) | `BROWSERBASE_API_KEY`, `BROWSERBASE_PROJECT_ID` |
| Generación de imágenes | [FAL](https://fal.ai/) | `FAL_KEY` |
| Voces TTS premium | [ElevenLabs](https://elevenlabs.io/) | `ELEVENLABS_API_KEY` |
| TTS de OpenAI + transcripción de voz | [OpenAI](https://platform.openai.com/api-keys) | `VOICE_TOOLS_OPENAI_KEY` |
| Entrenamiento de RL | [Tinker](https://tinker-console.thinkingmachines.ai/) + [WandB](https://wandb.ai/) | `TINKER_API_KEY`, `WANDB_API_KEY` |
| Modelado de usuario entre sesiones | [Honcho](https://honcho.dev/) | `HONCHO_API_KEY` |
```

---

## BATCH 16: Self-Hosting Firecrawl (3 replacements)

### Replacement 34: Firecrawl heading & intro
**Lines:** 443-448
**Type:** Markdown heading + intro text

Old String:
```
### Self-Hosting Firecrawl

By default, Hermes uses the [Firecrawl cloud API](https://firecrawl.dev/) for web search and scraping. If you prefer to run Firecrawl locally, you can point Hermes at a self-hosted instance instead.

**What you get:**
```

New String:
```
### Alojamiento propio de Firecrawl

Por defecto, Hermes utiliza la [API en la nube de Firecrawl](https://firecrawl.dev/) para búsqueda y raspado web. Si prefieres ejecutar Firecrawl localmente, puedes apuntar Hermes a una instancia autoalojada en su lugar.

**Lo que obtienes:**
```

---

### Replacement 35: Firecrawl pros/cons & setup
**Lines:** 449-466
**Type:** Prose text + code comments

Old String:
```
**What you get:** No API key required, no rate limits, no per-page costs, full data sovereignty.

**What you lose:** The cloud version uses Firecrawl's proprietary "Fire-engine" for advanced anti-bot bypassing (Cloudflare, CAPTCHAs, IP rotation). Self-hosted uses basic fetch + Playwright, so some protected sites may fail. Search uses DuckDuckGo instead of Google.

**Setup:**

1. Clone and start the Firecrawl Docker stack (5 containers: API, Playwright, Redis, RabbitMQ, PostgreSQL — requires ~4-8 GB RAM):
   ```bash
   git clone https://github.com/mendableai/firecrawl
   cd firecrawl
   # In .env, set: USE_DB_AUTHENTICATION=false
   docker compose up -d
   ```

2. Point Hermes at your instance (no API key needed):
   ```bash
   hermes config set FIRECRAWL_API_URL http://localhost:3002
   ```

You can also set both `FIRECRAWL_API_KEY` and `FIRECRAWL_API_URL` if your self-hosted instance has authentication enabled.
```

New String:
```
**Lo que obtienes:** Sin clave API requerida, sin límites de velocidad, sin costos por página, soberanía de datos completa.

**Lo que pierdes:** La versión en la nube usa el "Fire-engine" propietario de Firecrawl para eludir anti-bots avanzado (Cloudflare, CAPTCHAs, rotación de IP). El autoalojado usa fetch básico + Playwright, por lo que algunos sitios protegidos pueden fallar. La búsqueda usa DuckDuckGo en lugar de Google.

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

También puedes establecer tanto `FIRECRAWL_API_KEY` como `FIRECRAWL_API_URL` si tu instancia autoalojada tiene autenticación habilitada.
```

---

## BATCH 17: OpenRouter Provider Routing (2 replacements)

### Replacement 36: OpenRouter heading & intro
**Lines:** 467-480
**Type:** Markdown heading + intro + code block

Old String:
```
## OpenRouter Provider Routing

When using OpenRouter, you can control how requests are routed across providers. Add a `provider_routing` section to `~/.hermes/config.yaml`:

```yaml
provider_routing:
  sort: "throughput"          # "price" (default), "throughput", or "latency"
  # only: ["anthropic"]      # Only use these providers
  # ignore: ["deepinfra"]    # Skip these providers
  # order: ["anthropic", "google"]  # Try providers in this order
  # require_parameters: true  # Only use providers that support all request params
  # data_collection: "deny"   # Exclude providers that may store/train on data
```

**Shortcuts:** Append `:nitro` to any model name for throughput sorting (e.g., `anthropic/claude-sonnet-4:nitro`), or `:floor` for price sorting.
```

New String:
```
## Enrutamiento de proveedor de OpenRouter

Cuando uses OpenRouter, puedes controlar cómo se enrutan las solicitudes a través de proveedores. Agrega una sección `provider_routing` a `~/.hermes/config.yaml`:

```yaml
provider_routing:
  sort: "throughput"          # "price" (por defecto), "throughput", or "latency"
  # only: ["anthropic"]      # Solo usa estos proveedores
  # ignore: ["deepinfra"]    # Omite estos proveedores
  # order: ["anthropic", "google"]  # Intenta proveedores en este orden
  # require_parameters: true  # Solo usa proveedores que soporten todos los parámetros de solicitud
  # data_collection: "deny"   # Excluye proveedores que puedan almacenar/entrenar con datos
```

**Atajos:** Agrega `:nitro` a cualquier nombre de modelo para ordenamiento de rendimiento (p. ej., `anthropic/claude-sonnet-4:nitro`), o `:floor` para ordenamiento de precio.
```

---

## BATCH 18: Terminal Backend Configuration (1 replacement)

### Replacement 37: Terminal Backend heading & intro
**Lines:** 487-520
**Type:** Markdown heading + intro + code block with comments

Old String:
```
## Terminal Backend Configuration

Configure which environment the agent uses for terminal commands:

```yaml
terminal:
  backend: local    # or: docker, ssh, singularity, modal, daytona
  cwd: "."          # Working directory ("." = current dir)
  timeout: 180      # Command timeout in seconds

  # Docker-specific settings
  docker_image: "nikolaik/python-nodejs:python3.11-nodejs20"
  docker_volumes:                    # Share host directories with the container
    - "/home/user/projects:/workspace/projects"
    - "/home/user/data:/data:ro"     # :ro for read-only

  # Container resource limits (docker, singularity, modal, daytona)
  container_cpu: 1                   # CPU cores
  container_memory: 5120             # MB (default 5GB)
  container_disk: 51200              # MB (default 50GB)
  container_persistent: true         # Persist filesystem across sessions
```
```

New String:
```
## Configuración de backend de terminal

Configura qué entorno utiliza el agente para los comandos de terminal:

```yaml
terminal:
  backend: local    # o: docker, ssh, singularity, modal, daytona
  cwd: "."          # Directorio actual ("." = directorio actual)
  timeout: 180      # Tiempo de espera de comando en segundos

  # Ajustes específicos de Docker
  docker_image: "nikolaik/python-nodejs:python3.11-nodejs20"
  docker_volumes:                    # Comparte directorios del host con el contenedor
    - "/home/user/projects:/workspace/projects"
    - "/home/user/data:/data:ro"     # :ro for read-only

  # Límites de recursos del contenedor (docker, singularity, modal, daytona)
  container_cpu: 1                   # Núcleos de CPU
  container_memory: 5120             # MB (predeterminado 5GB)
  container_disk: 51200              # MB (predeterminado 50GB)
  container_persistent: true         # Persiste el sistema de archivos entre sesiones
```
```

---

## BATCH 19: Docker Volume Mounts (1 replacement)

### Replacement 38: Docker Volume Mounts heading & intro
**Lines:** 519-544
**Type:** Markdown heading + intro + code block + prose

Old String:
```
### Docker Volume Mounts

When using the Docker backend, `docker_volumes` lets you share host directories with the container. Each entry uses standard Docker `-v` syntax: `host_path:container_path[:options]`.

```yaml
terminal:
  backend: docker
  docker_volumes:
    - "/home/user/projects:/workspace/projects"   # Read-write (default)
    - "/home/user/datasets:/data:ro"              # Read-only
    - "/home/user/outputs:/outputs"               # Agent writes, you read
```

This is useful for:
- **Providing files** to the agent (datasets, configs, reference code)
- **Receiving files** from the agent (generated code, reports, exports)
- **Shared workspaces** where both you and the agent access the same files

Can also be set via environment variable: `TERMINAL_DOCKER_VOLUMES='["/host:/container"]'` (JSON array).

See [Code Execution](features/code-execution.md) and the [Terminal section of the README](features/tools.md) for details on each backend.
```

New String:
```
### Montajes de volumen de Docker

Cuando usas el backend de Docker, `docker_volumes` te permite compartir directorios del host con el contenedor. Cada entrada usa la sintaxis estándar de Docker `-v`: `host_path:container_path[:options]`.

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
- **Espacios de trabajo compartidos** donde tanto tú como el agente acceden a los mismos archivos

También se puede establecer a través de variable de entorno: `TERMINAL_DOCKER_VOLUMES='["/host:/container"]'` (JSON array).

Consulta [Ejecución de código](features/code-execution.md) y la [sección Terminal del README](features/tools.md) para detalles sobre cada backend.
```

---

## BATCH 20: Memory & Git Worktree (2 replacements)

### Replacement 39: Memory heading (short section)
**Lines:** 544-550
**Type:** Markdown heading (short, no changes to YAML comments)

Old String:
```
## Memory Configuration

```yaml
memory:
```

New String:
```
## Configuración de memoria

```yaml
memory:
```

---

### Replacement 40: Git Worktree heading & intro
**Lines:** 552-567
**Type:** Markdown heading + intro + code block + prose

Old String:
```
## Git Worktree Isolation

Enable isolated git worktrees for running multiple agents in parallel on the same repo:

```yaml
worktree: true    # Always create a worktree (same as hermes -w)
# worktree: false # Default — only when -w flag is passed
```

When enabled, each CLI session creates a fresh worktree under `.worktrees/` with its own branch. Agents can edit files, commit, push, and create PRs without interfering with each other. Clean worktrees are removed on exit; dirty ones are kept for manual recovery.

You can also list gitignored files to copy into worktrees via `.worktreeinclude` in your repo root:
```

New String:
```
## Aislamiento de Worktree de Git

Habilita worktrees de git aislados para ejecutar múltiples agentes en paralelo en el mismo repositorio:

```yaml
worktree: true    # Siempre crea un worktree (igual que hermes -w)
# worktree: false # Predeterminado — solo cuando se pasa el indicador -w
```

Cuando se habilita, cada sesión de CLI crea un worktree fresco bajo `.worktrees/` con su propia rama. Los agentes pueden editar archivos, confirmar, enviar y crear PRs sin interferir entre sí. Los worktrees limpios se eliminan al salir; los sucios se guardan para recuperación manual.

También puedes enumerar archivos gitignore para copiar en worktrees a través de `.worktreeinclude` en la raíz de tu repositorio:
```

---

## BATCH 21: Context Compression & Iteration Budget (2 replacements)

### Replacement 41: Context Compression heading & intro
**Lines:** 575-583
**Type:** Markdown heading + code block with comments

Old String:
```
## Context Compression

```yaml
compression:
  enabled: true
  threshold: 0.85              # Compress at 85% of context limit
  summary_model: "google/gemini-3-flash-preview"   # Model for summarization
  # summary_provider: "auto"   # "auto", "openrouter", "nous", "main"
```
```

New String:
```
## Compresión de contexto

```yaml
compression:
  enabled: true
  threshold: 0.85              # Comprimir al 85% del límite de contexto
  summary_model: "google/gemini-3-flash-preview"   # Modelo para resumen
  # summary_provider: "auto"   # "auto", "openrouter", "nous", "main"
```
```

---

### Replacement 42: Iteration Budget heading & intro
**Lines:** 585-604
**Type:** Markdown heading + intro + table + code block + prose

Old String:
```
## Iteration Budget Pressure

When the agent is working on a complex task with many tool calls, it can burn through its iteration budget (default: 90 turns) without realizing it's running low. Budget pressure automatically warns the model as it approaches the limit:

| Threshold | Level | What the model sees |
|-----------|-------|---------------------|
| **70%** | Caution | `[BUDGET: 63/90. 27 iterations left. Start consolidating.]` |
| **90%** | Warning | `[BUDGET WARNING: 81/90. Only 9 left. Respond NOW.]` |

Warnings are injected into the last tool result's JSON (as a `_budget_warning` field) rather than as separate messages — this preserves prompt caching and doesn't disrupt the conversation structure.

```yaml
agent:
  max_turns: 90                # Max iterations per conversation turn (default: 90)
```

Budget pressure is enabled by default. The agent sees warnings naturally as part of tool results, encouraging it to consolidate its work and deliver a response before running out of iterations.
```

New String:
```
## Presión de presupuesto de iteración

Cuando el agente está trabajando en una tarea compleja con muchas llamadas de herramientas, pueden quemar su presupuesto de iteración (predeterminado: 90 turnos) sin darse cuenta de que se está agotando. La presión de presupuesto advierte automáticamente al modelo a medida que se acerca el límite:

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
```

---

## BATCH 23: Auxiliary Models - Part 1 (2 replacements)

### Replacement 43: Auxiliary Models heading & intro
**Lines:** 606-621
**Type:** Markdown heading + intro + code block with comments

Old String:
```
## Auxiliary Models

Hermes uses lightweight "auxiliary" models for side tasks like image analysis, web page summarization, and browser screenshot analysis. By default, these use **Gemini Flash** via OpenRouter or Nous Portal — you don't need to configure anything.

To use a different model, add an `auxiliary` section to `~/.hermes/config.yaml`:

```yaml
auxiliary:
  # Image analysis (vision_analyze tool + browser screenshots)
  vision:
    provider: "auto"           # "auto", "openrouter", "nous", "main"
    model: ""                  # e.g. "openai/gpt-4o", "google/gemini-2.5-flash"

  # Web page summarization + browser page text extraction
  web_extract:
    provider: "auto"
    model: ""                  # e.g. "google/gemini-2.5-flash"
```
```

New String:
```
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
```

---

### Replacement 44: Changing the Vision Model subheading & text
**Lines:** 625-638
**Type:** Markdown subheading + prose + code blocks

Old String:
```
### Changing the Vision Model

To use GPT-4o instead of Gemini Flash for image analysis:

```yaml
auxiliary:
  vision:
    model: "openai/gpt-4o"
```

Or via environment variable (in `~/.hermes/.env`):

```bash
AUXILIARY_VISION_MODEL=openai/gpt-4o
```
```

New String:
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
```

---

[Continued in next part due to length...]

