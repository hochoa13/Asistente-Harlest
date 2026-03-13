# Configuration.md — Spanish Translation Plan

**File:** `docs/user-guide/configuration.md`
**Total Sections:** 40+
**Code blocks to preserve:** All bash/yaml/text blocks remain unchanged
**Status:** Ready for multi_replace_string_in_file application

---

## Section 1: Frontmatter Description (Line 3)

### English (Current)
```
description: "Configure Hermes Agent — config.yaml, providers, models, API keys, and more"
```

### Spanish Translation
```
description: "Configura Hermes Agent — config.yaml, proveedores, modelos, claves API, y más"
```

---

## Section 2: Main Heading & Intro (Lines 6-8)

### English (Current)
```
# Configuration

All settings are stored in the `~/.hermes/` directory for easy access.
```

### Spanish Translation
```
# Configuración

Todos los ajustes se almacenan en el directorio `~/.hermes/` para un fácil acceso.
```

---

## Section 3: Directory Structure Heading & Intro (Lines 10-23)

### English (Current)
```
## Directory Structure
```

### Spanish Translation
```
## Estructura de directorio
```

---

## Section 4: Managing Configuration Heading (Lines 25-42)

### English (Current)
```
## Managing Configuration
```

### Spanish Translation
```
## Gestión de configuración
```

### Text to Replace (Lines 27-29)
```
hermes config              # View current configuration
hermes config edit         # Open config.yaml in your editor
hermes config set KEY VAL  # Set a specific value
hermes config check        # Check for missing options (after updates)
hermes config migrate      # Interactively add missing options

# Examples:
```

### Spanish Translation
```
hermes config              # Vea la configuración actual
hermes config edit         # Abre config.yaml en tu editor
hermes config set KEY VAL  # Establece un valor específico
hermes config check        # Verifica opciones faltantes (después de actualizaciones)
hermes config migrate      # Agrega interactivamente opciones faltantes

# Ejemplos:
```

### Tip Text (Line 37-39)
English:
```
The `hermes config set` command automatically routes values to the right file — API keys are saved to `.env`, everything else to `config.yaml`.
```

Spanish:
```
El comando `hermes config set` automáticamente enruta los valores al archivo correcto — las claves API se guardan en `.env`, todo lo demás en `config.yaml`.
```

---

## Section 5: Configuration Precedence (Lines 44-61)

### Heading
English: `## Configuration Precedence`
Spanish: `## Precedencia de configuración`

### Intro Text (Line 47)
English: `Settings are resolved in this order (highest priority first):`
Spanish: `Los ajustes se resuelven en este orden (mayor prioridad primero):`

### List Items (Lines 49-52)
English:
```
1. **CLI arguments** — e.g., `hermes chat --model anthropic/claude-sonnet-4` (per-invocation override)
2. **`~/.hermes/config.yaml`** — the primary config file for all non-secret settings
3. **`~/.hermes/.env`** — fallback for env vars; **required** for secrets (API keys, tokens, passwords)
4. **Built-in defaults** — hardcoded safe defaults when nothing else is set
```

Spanish:
```
1. **Argumentos CLI** — p. ej., `hermes chat --model anthropic/claude-sonnet-4` (anulación por invocación)
2. **`~/.hermes/config.yaml`** — el archivo de configuración principal para todos los ajustes no secretos
3. **`~/.hermes/.env`** — respaldo para variables de entorno; **requerido** para secretos (claves API, tokens, contraseñas)
4. **Valores por defecto integrados** — valores predeterminados seguros codificados cuando nada más está configurado
```

### Info Box (Lines 54-57)
English: `Secrets (API keys, bot tokens, passwords) go in `.env`. Everything else (model, terminal backend, compression settings, memory limits, toolsets) goes in `config.yaml`. When both are set, `config.yaml` wins for non-secret settings.`

Spanish: `Los secretos (claves API, tokens de bots, contraseñas) van en `.env`. Todo lo demás (modelo, backend de terminal, ajustes de compresión, límites de memoria, conjuntos de herramientas) va en `config.yaml`. Cuando ambos están configurados, `config.yaml` gana para ajustes no secretos.`

---

## Section 6: Inference Providers (Lines 63-93)

### Heading
English: `## Inference Providers`
Spanish: `## Proveedores de inferencia`

### Intro (Lines 65-66)
English: `You need at least one way to connect to an LLM. Use `hermes model` to switch providers and models interactively, or configure directly:`
Spanish: `Necesitas al menos una forma de conectar a un LLM. Usa `hermes model` para cambiar proveedores y modelos interactivamente, o configura directamente:`

### Info Box (Lines 80-81)
English: `The OpenAI Codex provider authenticates via device code (open a URL, enter a code). Credentials are stored at `~/.codex/auth.json` and auto-refresh. No Codex CLI installation required.`
Spanish: `El proveedor OpenAI Codex se autentica mediante código de dispositivo (abre una URL, ingresa un código). Las credenciales se almacenan en `~/.codex/auth.json` y se actualizan automáticamente. No se requiere instalación de Codex CLI.`

### Warning Box (Lines 84-87)
English: `Even when using Nous Portal, Codex, or a custom endpoint, some tools (vision, web summarization, MoA) use a separate "auxiliary" model — by default Gemini Flash via OpenRouter. An `OPENROUTER_API_KEY` enables these tools automatically. You can also configure which model and provider these tools use — see [Auxiliary Models](#auxiliary-models) below.`
Spanish: `Incluso cuando usas Nous Portal, Codex, o un punto de conexión personalizado, algunas herramientas (visión, resumen web, MoA) usan un modelo "auxiliar" separado — por defecto Gemini Flash a través de OpenRouter. Una `OPENROUTER_API_KEY` habilita estas herramientas automáticamente. También puedes configurar qué modelo y proveedor utilizan estas herramientas — ver [Modelos auxiliares](#auxiliary-models) abajo.`

---

## Section 7: Anthropic (Native) (Lines 95-130)

### Heading
English: `### Anthropic (Native)`
Spanish: `### Anthropic (Nativa)`

### Intro (Lines 97-98)
English: `Use Claude models directly through the Anthropic API — no OpenRouter proxy needed. Supports three auth methods:`
Spanish: `Usa modelos Claude directamente a través de la API de Anthropic — no se necesita proxy OpenRouter. Admite tres métodos de autenticación:`

### Comment in bash (Lines 100-101)
English: `# With an API key (pay-per-token)`
Spanish: `# Con una clave API (pago por token)`

### Comment (Line 105)
English: `# With a Claude Code setup-token (Pro/Max subscription)`
Spanish: `# Con un token de configuración de Claude Code (suscripción Pro/Max)`

### Comment (Line 109)
English: `# Auto-detect Claude Code credentials (if you have Claude Code installed)`
Spanish: `# Detectar automáticamente credenciales de Claude Code (si tienes Claude Code instalado)`

### Text (Line 112)
English: `Or set it permanently:`
Spanish: `O establécelo permanentemente:`

### Tip (Line 125)
English: `_provider claude` and `--provider claude-code` also work as shorthand for `--provider anthropic`._
Spanish: `_provider claude` y `--provider claude-code` también funcionan como abreviaturas para `--provider anthropic`._

---

## Section 8: First-Class Chinese AI Providers (Lines 152-178)

### Heading
English: `### First-Class Chinese AI Providers`
Spanish: `### Proveedores de IA chinos de primera clase`

### Intro (Lines 154-155)
English: `These providers have built-in support with dedicated provider IDs. Set the API key and use `--provider` to select:`
Spanish: `Estos proveederes tienen soporte integrado con IDs de proveedor dedicados. Establece la clave API y usa `--provider` para seleccionar:`

### Comment 1 (Line 157)
English: `# z.ai / ZhipuAI GLM`
Spanish: `# z.ai / ZhipuAI GLM`

### Comment 2 (Lines 159-160)
English: `# Requires: GLM_API_KEY in ~/.hermes/.env`
Spanish: `# Requiere: GLM_API_KEY en ~/.hermes/.env`

### Comment 3 (Line 162)
English: `# Kimi / Moonshot AI`
Spanish: `# Kimi / Moonshot AI`

### Comment 4 (Lines 164-165)
English: `# Requires: KIMI_API_KEY in ~/.hermes/.env`
Spanish: `# Requiere: KIMI_API_KEY en ~/.hermes/.env`

### Comment 5 (Line 167)
English: `# MiniMax (global endpoint)`
Spanish: `# MiniMax (punto de conexión global)`

### Comment 6 (Lines 169-170)
English: `# Requires: MINIMAX_API_KEY in ~/.hermes/.env`
Spanish: `# Requiere: MINIMAX_API_KEY en ~/.hermes/.env`

### Comment 7 (Line 172)
English: `# MiniMax (China endpoint)`
Spanish: `# MiniMax (punto de conexión de China)`

### Comment 8 (Lines 174-175)
English: `# Requires: MINIMAX_CN_API_KEY in ~/.hermes/.env`
Spanish: `# Requiere: MINIMAX_CN_API_KEY en ~/.hermes/.env`

### Intro to YAML (Line 177)
English: `Or set the provider permanently in `config.yaml`:`
Spanish: `O establece el proveedor permanentemente en `config.yaml`:`

### Closing text (Line 184)
English: `Base URLs can be overridden with `GLM_BASE_URL`, `KIMI_BASE_URL`, `MINIMAX_BASE_URL`, or `MINIMAX_CN_BASE_URL` environment variables.`
Spanish: `Las URL base se pueden anular con variables de entorno `GLM_BASE_URL`, `KIMI_BASE_URL`, `MINIMAX_BASE_URL`, o `MINIMAX_CN_BASE_URL`.`

---

## Section 9: Custom & Self-Hosted LLM Providers (Lines 180-194)

### Heading
English: `## Custom & Self-Hosted LLM Providers`
Spanish: `## Proveedores de LLM personalizados y autoalojados`

### Intro (Lines 182-183)
English: `Hermes Agent works with **any OpenAI-compatible API endpoint**. If a server implements `/v1/chat/completions`, you can point Hermes at it. This means you can use local models, GPU inference servers, multi-provider routers, or any third-party API.`
Spanish: `Hermes Agent funciona con **cualquier punto de conexión de API compatible con OpenAI**. Si un servidor implementa `/v1/chat/completions`, puedes apuntar Hermes a él. Esto significa que puedes usar modelos locales, servidores de inferencia GPU, enrutadores multipropósito, o cualquier API de terceros.`

### Subheading (Line 186)
English: `### General Setup`
Spanish: `### Configuración general`

### Intro (Lines 188-189)
English: `Two ways to configure a custom endpoint:`
Spanish: `Dos formas de configurar un punto de conexión personalizado:`

### Label (Line 191)
English: `**Interactive (recommended):**`
Spanish: `**Interactivo (recomendado):**`

### Comment (Line 194)
English: `# Select "Custom endpoint (self-hosted / VLLM / etc.)"`
Spanish: `# Selecciona "Custom endpoint (self-hosted / VLLM / etc.)"`

### Comment (Line 195)
English: `# Enter: API base URL, API key, Model name`
Spanish: `# Ingresa: URL base de API, clave de API, nombre del modelo`

### Label (Line 198)
English: `**Manual (`.env` file):**`
Spanish: `**Manual (archivo `.env`):**`

### Comment (Line 200)
English: `# Add to ~/.hermes/.env`
Spanish: `# Agrega a ~/.hermes/.env`

### Closing text (Lines 207-208)
English: `Everything below follows this same pattern — just change the URL, key, and model name.`
Spanish: `Todo lo siguiente sigue el mismo patrón — solo cambia la URL, la clave y el nombre del modelo.`

---

## Section 10: Ollama (Lines 196-220)

### Heading
English: `### Ollama — Local Models, Zero Config`
Spanish: `### Ollama — Modelos locales, cero configuración`

### Intro (Lines 213-214)
English: `[Ollama](https://ollama.com/) runs open-weight models locally with one command. Best for: quick local experimentation, privacy-sensitive work, offline use.`
Spanish: `[Ollama](https://ollama.com/) ejecuta modelos de peso abierto localmente con un comando. Mejor para: experimentación local rápida, trabajo sensible a la privacidad, uso sin conexión.`

### Comment 1 (Line 216)
English: `# Install and run a model`
Spanish: `# Instala y ejecuta un modelo`

### Comment 2 (Line 219)
English: `# Configure Hermes`
Spanish: `# Configura Hermes`

### Comment (Line 223)
English: `# Any non-empty string`
Spanish: `# Cualquier cadena no vacía`

### Note (Lines 228-229)
English: `Ollama's OpenAI-compatible endpoint supports chat completions, streaming, and tool calling (for supported models). No GPU required for smaller models — Ollama handles CPU inference automatically.`
Spanish: `El punto de conexión compatible con OpenAI de Ollama admite finalizaciones de chat, transmisión y llamadas de herramientas (para modelos compatibles). No se requiere GPU para modelos más pequeños — Ollama maneja la inferencia de CPU automáticamente.`

### Tip (Lines 232-233)
English: `List available models with `ollama list`. Pull any model from the [Ollama library](https://ollama.com/library) with `ollama pull <model>`.`
Spanish: `Enumera los modelos disponibles con `ollama list`. Extrae cualquier modelo de la [biblioteca de Ollama](https://ollama.com/library) con `ollama pull <model>`.`

---

## Section 11: vLLM (Lines 222-246)

### Heading
English: `### vLLM — High-Performance GPU Inference`
Spanish: `### vLLM — Inferencia de GPU de alto rendimiento`

### Intro (Lines 239-240)
English: `[vLLM](https://docs.vllm.ai/) is the standard for production LLM serving. Best for: maximum throughput on GPU hardware, serving large models, continuous batching.`
Spanish: `[vLLM](https://docs.vllm.ai/) es el estándar para servir LLM en producción. Mejor para: máximo rendimiento en hardware GPU, servir modelos grandes, procesamiento por lotes continuo.`

### Comment (Line 242)
English: `# Start vLLM server`
Spanish: `# Inicia servidor vLLM`

### Comment (Line 244)
English: `# Multi-GPU`
Spanish: `# GPU múltiple`

### Comment (Line 247)
English: `# Configure Hermes`
Spanish: `# Configura Hermes`

### Closing text (Line 254)
English: `vLLM supports tool calling, structured output, and multi-modal models. Use `--enable-auto-tool-choice` and `--tool-call-parser hermes` for Hermes-format tool calling with NousResearch models.`
Spanish: `vLLM admite llamadas de herramientas, salida estructurada y modelos multimodales. Usa `--enable-auto-tool-choice` y `--tool-call-parser hermes` para llamadas de herramientas en formato Hermes con modelos de NousResearch.`

---

## Section 12: SGLang (Lines 248-273)

### Heading
English: `### SGLang — Fast Serving with RadixAttention`
Spanish: `### SGLang — Servicio rápido con RadixAttention`

### Intro (Lines 256-257)
English: `[SGLang](https://github.com/sgl-project/sglang) is an alternative to vLLM with RadixAttention for KV cache reuse. Best for: multi-turn conversations (prefix caching), constrained decoding, structured output.`
Spanish: `[SGLang](https://github.com/sgl-project/sglang) es una alternativa a vLLM con RadixAttention para reutilización de caché KV. Mejor para: conversaciones multi-turno (caché de prefijo), decodificación restringida, salida estructurada.`

### Comment (Line 259)
English: `# Start SGLang server`
Spanish: `# Inicia servidor SGLang`

### Comment (Line 266)
English: `# Configure Hermes`
Spanish: `# Configura Hermes`

---

## Section 13: llama.cpp / llama-server (Lines 275-302)

### Heading
English: `### llama.cpp / llama-server — CPU & Metal Inference`
Spanish: `### llama.cpp / llama-server — Inferencia de CPU y Metal`

### Intro (Lines 277-278)
English: `[llama.cpp](https://github.com/ggml-org/llama.cpp) runs quantized models on CPU, Apple Silicon (Metal), and consumer GPUs. Best for: running models without a datacenter GPU, Mac users, edge deployment.`
Spanish: `[llama.cpp](https://github.com/ggml-org/llama.cpp) ejecuta modelos cuantizados en CPU, Apple Silicon (Metal) y GPU de consumidor. Mejor para: ejecutar modelos sin una GPU de centro de datos, usuarios de Mac, implementación perimetral.`

### Comment (Line 280)
English: `# Build and start llama-server`
Spanish: `# Construye e inicia llama-server`

### Comment (Line 287)
English: `# Configure Hermes`
Spanish: `# Configura Hermes`

### Tip (Lines 293-294)
English: `Download GGUF models from [Hugging Face](https://huggingface.co/models?library=gguf). Q4_K_M quantization offers the best balance of quality vs. memory usage.`
Spanish: `Descarga modelos GGUF de [Hugging Face](https://huggingface.co/models?library=gguf). La cuantización Q4_K_M ofrece el mejor equilibrio de calidad frente al uso de memoria.`

---

## Section 14: LiteLLM Proxy (Lines 304-329)

### Heading
English: `### LiteLLM Proxy — Multi-Provider Gateway`
Spanish: `### LiteLLM Proxy — Puerta de enlace multipropósito`

### Intro (Lines 306-307)
English: `[LiteLLM](https://docs.litellm.ai/) is an OpenAI-compatible proxy that unifies 100+ LLM providers behind a single API. Best for: switching between providers without config changes, load balancing, fallback chains, budget controls.`
Spanish: `[LiteLLM](https://docs.litellm.ai/) es un proxy compatible con OpenAI que unifica más de 100 proveedores de LLM detrás de una única API. Mejor para: cambiar entre proveedores sin cambios de configuración, equilibrio de carga, cadenas de respaldo, controles de presupuesto.`

### Comment (Line 309)
English: `# Install and start`
Spanish: `# Instala e inicia`

### Comment (Line 312)
English: `# Or with a config file for multiple models:`
Spanish: `# O con un archivo de configuración para múltiples modelos:`

### Comment (Line 315)
English: `# Configure Hermes`
Spanish: `# Configura Hermes`

### Intro to YAML (Line 320)
English: `Example `litellm_config.yaml` with fallback:`
Spanish: `Ejemplo de `litellm_config.yaml` con respaldo:`

---

## Section 15: ClawRouter (Lines 331-363)

### Heading
English: `### ClawRouter — Cost-Optimized Routing`
Spanish: `### ClawRouter — Enrutamiento optimizado por costo`

### Intro (Lines 333-334)
English: `[ClawRouter](https://github.com/BlockRunAI/ClawRouter) by BlockRunAI is a local routing proxy that auto-selects models based on query complexity. It classifies requests across 14 dimensions and routes to the cheapest model that can handle the task. Payment is via USDC cryptocurrency (no API keys).`
Spanish: `[ClawRouter](https://github.com/BlockRunAI/ClawRouter) de BlockRunAI es un proxy de enrutamiento local que selecciona automáticamente modelos según la complejidad de la consulta. Clasifica solicitudes en 14 dimensiones y enruta al modelo más barato que pueda manejar la tarea. El pago es a través de criptomoneda USDC (sin claves API).`

### Comment (Line 336)
English: `# Install and start`
Spanish: `# Instala e inicia`

### Comment (Line 339)
English: `# Configure Hermes`
Spanish: `# Configura Hermes`

### Text (Line 342)
English: `Routing profiles:`
Spanish: `Perfiles de enrutamiento:`

### Column headers for table (Line 343)
No translation needed (table cell headers remain in English, same as table structure)

### Note (Line 361)
English: `ClawRouter requires a USDC-funded wallet on Base or Solana for payment. All requests route through BlockRun's backend API. Run `npx @blockrun/clawrouter doctor` to check wallet status.`
Spanish: `ClawRouter requiere una billetera financiada con USDC en Base o Solana para el pago. Todas las solicitudes se enrutan a través de la API de backend de BlockRun. Ejecuta `npx @blockrun/clawrouter doctor` para verificar el estado de la billetera.`

---

## Section 16: Other Compatible Providers (Lines 365-403)

### Heading
English: `### Other Compatible Providers`
Spanish: `### Otros proveedores compatibles`

### Intro (Line 367-368)
English: `Any service with an OpenAI-compatible API works. Some popular options:`
Spanish: `Cualquier servicio con una API compatible con OpenAI funciona. Algunas opciones populares:`

### Comment (Line 389)
English: `# Example: Together AI`
Spanish: `# Ejemplo: Together AI`

---

## Section 17: Choosing the Right Setup (Lines 405-426)

### Heading
English: `### Choosing the Right Setup`
Spanish: `### Elegir la configuración correcta`

### Table Header
English: `Use Case`
Spanish: `Caso de uso`

English: `Recommended`
Spanish: `Recomendado`

### Use cases in table:
- "Just want it to work" → "Solo quiero que funcione"
- "Local models, easy setup" → "Modelos locales, configuración fácil"
- "Production GPU serving" → "Servicio de GPU en producción"
- "Mac / no GPU" → "Mac / sin GPU"
- "Multi-provider routing" → "Enrutamiento multipropósito"
- "Cost optimization" → "Optimización de costos"
- "Maximum privacy" → "Privacidad máxima"
- "Enterprise / Azure" → "Empresarial / Azure"
- "Chinese AI models" → "Modelos de IA chinos"

### Tip (Lines 424-425)
English: `You can switch between providers at any time with `hermes model` — no restart required. Your conversation history, memory, and skills carry over regardless of which provider you use.`
Spanish: `Puedes cambiar entre proveedores en cualquier momento con `hermes model` — no se requiere reinicio. Tu historial de conversación, memoria y habilidades se transfieren independientemente del proveedor que uses.`

---

## Section 18: Optional API Keys (Lines 428-441)

### Heading
English: `## Optional API Keys`
Spanish: `## Claves API opcionales`

### Table headers
English: `Feature` → Spanish: `Función`
English: `Provider` → Spanish: `Proveedor`
English: `Env Variable` → Spanish: `Variable de entorno`

### Features in table (with translations):
- "Web scraping" → "Raspado web"
- "Browser automation" → "Automatización del navegador"
- "Image generation" → "Generación de imágenes"
- "Premium TTS voices" → "Voces TTS premium"
- "OpenAI TTS + voice transcription" → "TTS de OpenAI + transcripción de voz"
- "RL Training" → "Entrenamiento de RL"
- "Cross-session user modeling" → "Modelado de usuario entre sesiones"

---

## Section 19: Self-Hosting Firecrawl (Lines 443-465)

### Heading
English: `### Self-Hosting Firecrawl`
Spanish: `### Alojamiento propio de Firecrawl`

### Intro (Line 445-446)
English: `By default, Hermes uses the [Firecrawl cloud API](https://firecrawl.dev/) for web search and scraping. If you prefer to run Firecrawl locally, you can point Hermes at a self-hosted instance instead.`
Spanish: `Por defecto, Hermes utiliza la [API en la nube de Firecrawl](https://firecrawl.dev/) para búsqueda y raspado web. Si prefieres ejecutar Firecrawl localmente, puedes apuntar Hermes a una instancia autoalojada en su lugar.`

### Subheading (Line 449)
English: `**What you get:**`
Spanish: `**Lo que obtienes:**`

### Text (Line 449)
English: `No API key required, no rate limits, no per-page costs, full data sovereignty.`
Spanish: `Sin clave API requerida, sin límites de velocidad, sin costos por página, soberanía de datos completa.`

### Subheading (Line 451)
English: `**What you lose:**`
Spanish: `**Lo que pierdes:**`

### Text (Line 451)
English: `The cloud version uses Firecrawl's proprietary "Fire-engine" for advanced anti-bot bypassing (Cloudflare, CAPTCHAs, IP rotation). Self-hosted uses basic fetch + Playwright, so some protected sites may fail. Search uses DuckDuckGo instead of Google.`
Spanish: `La versión en la nube usa el "Fire-engine" propietario de Firecrawl para eludir anti-bots avanzado (Cloudflare, CAPTCHAs, rotación de IP). El autoalojado usa fetch básico + Playwright, por lo que algunos sitios protegidos pueden fallar. La búsqueda usa DuckDuckGo en lugar de Google.`

### Subheading (Line 454)
English: `**Setup:**`
Spanish: `**Configuración:**`

### Step 1 (Lines 456-458)
English: `Clone and start the Firecrawl Docker stack (5 containers: API, Playwright, Redis, RabbitMQ, PostgreSQL — requires ~4-8 GB RAM):`
Spanish: `Clona e inicia la pila de Docker de Firecrawl (5 contenedores: API, Playwright, Redis, RabbitMQ, PostgreSQL — requiere ~4-8 GB de RAM):`

### Comment (Line 460)
English: `# In .env, set: USE_DB_AUTHENTICATION=false`
Spanish: `# En .env, establece: USE_DB_AUTHENTICATION=false`

### Step 2 (Line 464)
English: `Point Hermes at your instance (no API key needed):`
Spanish: `Apunta Hermes a tu instancia (sin clave API requerida):`

### Closing (Line 467)
English: `You can also set both `FIRECRAWL_API_KEY` and `FIRECRAWL_API_URL` if your self-hosted instance has authentication enabled.`
Spanish: `También puedes establecer tanto `FIRECRAWL_API_KEY` como `FIRECRAWL_API_URL` si tu instancia autoalojada tiene autenticación habilitada.`

---

## Section 20: OpenRouter Provider Routing (Lines 467-485)

### Heading
English: `## OpenRouter Provider Routing`
Spanish: `## Enrutamiento de proveedor de OpenRouter`

### Intro (Lines 469-470)
English: `When using OpenRouter, you can control how requests are routed across providers. Add a `provider_routing` section to `~/.hermes/config.yaml`:`
Spanish: `Cuando uses OpenRouter, puedes controlar cómo se enrutan las solicitudes a través de proveedores. Agrega una sección `provider_routing` a `~/.hermes/config.yaml`:`

### Comments (Lines 472-476)
English:
```
# 572
sort: "throughput"          # "price" (default), "throughput", or "latency"
# only: ["anthropic"]      # Only use these providers
# ignore: ["deepinfra"]    # Skip these providers
# order: ["anthropic", "google"]  # Try providers in this order
# require_parameters: true  # Only use providers that support all request params
# data_collection: "deny"   # Exclude providers that may store/train on data
```

Spanish:
```
sort: "throughput"          # "price" (por defecto), "throughput" or "latency"
# only: ["anthropic"]      # Solo usa estos proveedores
# ignore: ["deepinfra"]    # Omite estos proveedores
# order: ["anthropic", "google"]  # Intenta proveedores en este orden
# require_parameters: true  # Solo usa proveedores que soporten todos los parámetros de solicitud
# data_collection: "deny"   # Excluye proveedores que puedan almacenar/entrenar con datos
```

### Closing (Line 479)
English: `**Shortcuts:** Append `:nitro` to any model name for throughput sorting (e.g., `anthropic/claude-sonnet-4:nitro`), or `:floor` for price sorting.`
Spanish: `**Atajos:** Agrega `:nitro` a cualquier nombre de modelo para ordenamiento de rendimiento (p. ej., `anthropic/claude-sonnet-4:nitro`), o `:floor` para ordenamiento de precio.`

---

## Section 21: Terminal Backend Configuration (Lines 487-517)

### Heading
English: `## Terminal Backend Configuration`
Spanish: `## Configuración de backend de terminal`

### Intro (Line 489)
English: `Configure which environment the agent uses for terminal commands:`
Spanish: `Configura qué entorno utiliza el agente para los comandos de terminal:`

### Comments
- `local` stays the same
- "or: docker, ssh, singularity, modal, daytona" → "o: docker, ssh, singularity, modal, daytona"
- "Current directory ("." = current dir)" → "Directorio actual ("." = directorio actual)"
- "Command timeout in seconds" → "Tiempo de espera de comando en segundos"
- "Docker-specific settings" → "Ajustes específicos de Docker"
- "Share host directories with the container" → "Comparte directorios del host con el contenedor"
- "Container resource limits (docker, singularity, modal, daytona)" → "Límites de recursos del contenedor (docker, singularity, modal, daytona)"
- "CPU cores" → "Núcleos de CPU"
- "MB (default 5GB)" → "MB (predeterminado 5GB)"
- "MB (default 50GB)" → "MB (predeterminado 50GB)"
- "Persist filesystem across sessions" → "Persiste el sistema de archivos entre sesiones"

---

## Section 22: Docker Volume Mounts (Lines 519-542)

### Heading
English: `### Docker Volume Mounts`
Spanish: `### Montajes de volumen de Docker`

### Intro (Lines 521-522)
English: `When using the Docker backend, `docker_volumes` lets you share host directories with the container. Each entry uses standard Docker `-v` syntax: `host_path:container_path[:options]`.`
Spanish: `Cuando usas el backend de Docker, `docker_volumes` te permite compartir directorios del host con el contenedor. Cada entrada usa la sintaxis estándar de Docker `-v`: `host_path:container_path[:options]`.`

### Comments
- "Read-write (default)" → "Lectura-escritura (predeterminado)"
- "Read-only" → "Solo lectura"
- "Agent writes, you read" → "El agente escribe, tú lees"

### Closing (Lines 535-537)
English: `This is useful for:`
Spanish: `Esto es útil para:`

### Bullet points (Lines 537-539)
English:
```
- **Providing files** to the agent (datasets, configs, reference code)
- **Receiving files** from the agent (generated code, reports, exports)
- **Shared workspaces** where both you and the agent access the same files
```

Spanish:
```
- **Proporcionar archivos** al agente (conjuntos de datos, configuraciones, código de referencia)
- **Recibir archivos** del agente (código generado, informes, exportaciones)
- **Espacios de trabajo compartidos** donde tanto tú como el agente acceden a los mismos archivos
```

### Reference (Line 541)
English: `See [Code Execution](features/code-execution.md) and the [Terminal section of the README](features/tools.md) for details on each backend.`
Spanish: `Consulta [Ejecución de código](features/code-execution.md) y la [sección Terminal del README](features/tools.md) para detalles sobre cada backend.`

---

## Section 23: Memory Configuration (Lines 544-550)

### Heading
English: `## Memory Configuration`
Spanish: `## Configuración de memoria`

### Comments
- "~800 tokens" → "~800 tokens" (same)
- "~500 tokens" → "~500 tokens" (same)

---

## Section 24: Git Worktree Isolation (Lines 552-573)

### Heading
English: `## Git Worktree Isolation`
Spanish: `## Aislamiento de Worktree de Git`

### Intro (Line 554)
English: `Enable isolated git worktrees for running multiple agents in parallel on the same repo:`
Spanish: `Habilita worktrees de git aislados para ejecutar múltiples agentes en paralelo en el mismo repositorio:`

### Comments
- "Always create a worktree (same as hermes -w)" → "Siempre crea un worktree (igual que hermes -w)"
- "Default — only when -w flag is passed" → "Predeterminado — solo cuando se pasa el indicador -w"

### Closing (Lines 563-565)
English: `When enabled, each CLI session creates a fresh worktree under `.worktrees/` with its own branch. Agents can edit files, commit, push, and create PRs without interfering with each other. Clean worktrees are removed on exit; dirty ones are kept for manual recovery.`
Spanish: `Cuando se habilita, cada sesión de CLI crea un worktree fresco bajo `.worktrees/` con su propia rama. Los agentes pueden editar archivos, confirmar, enviar y crear PRs sin interferir entre sí. Los worktrees limpios se eliminan al salir; los sucios se guardan para recuperación manual.`

### Subheading (Line 567)
English: `You can also list gitignored files to copy into worktrees via `.worktreeinclude` in your repo root:`
Spanish: `También puedes enumerar archivos gitignore para copiar en worktrees a través de `.worktreeinclude` en la raíz de tu repositorio:`

---

## Section 25: Context Compression (Lines 575-583)

### Heading
English: `## Context Compression`
Spanish: `## Compresión de contexto`

### Comments
- "Compress at 85% of context limit" → "Comprimir al 85% del límite de contexto"
- "Model for summarization" → "Modelo para resumen"
- "auto", "openrouter", "nous", "main" → no translation (these are provider names)

---

## Section 26: Iteration Budget Pressure (Lines 585-604)

### Heading
English: `## Iteration Budget Pressure`
Spanish: `## Presión de presupuesto de iteración`

### Intro (Lines 587-588)
English: `When the agent is working on a complex task with many tool calls, it can burn through its iteration budget (default: 90 turns) without realizing it's running low. Budget pressure automatically warns the model as it approaches the limit:`
Spanish: `Cuando el agente está trabajando en una tarea compleja con muchas llamadas de herramientas, pueden quemar su presupuesto de iteración (predeterminado: 90 turnos) sin darse cuenta de que se está agotando. La presión de presupuesto advierte automáticamente al modelo a medida que se acerca el límite:`

### Table header
English: `Threshold` → Spanish: `Umbral`
English: `Level` → Spanish: `Nivel`
English: `What the model sees` → Spanish: `Lo que ve el modelo`

### Threshold values (Line 591-593)
English:
```
| **70%** | Caution | `[BUDGET: 63/90. 27 iterations left. Start consolidating.]` |
| **90%** | Warning | `[BUDGET WARNING: 81/90. Only 9 left. Respond NOW.]` |
```

Spanish:
```
| **70%** | Precaución | `[BUDGET: 63/90. 27 iterations left. Start consolidating.]` |
| **90%** | Advertencia | `[BUDGET WARNING: 81/90. Only 9 left. Respond NOW.]` |
```

### Closing (Lines 599-600)
English: `Warnings are injected into the last tool result's JSON (as a `_budget_warning` field) rather than as separate messages — this preserves prompt caching and doesn't disrupt the conversation structure.`
Spanish: `Las advertencias se inyectan en el JSON del último resultado de herramienta (como un campo `_budget_warning`) en lugar de como mensajes separados — esto preserva el almacenamiento en caché de indicadores y no interrumpe la estructura de la conversación.`

### Comment
- "Max iterations per conversation turn (default: 90)" → "Máximo de iteraciones por turno de conversación (predeterminado: 90)"

### Closing (Lines 603-604)
English: `Budget pressure is enabled by default. The agent sees warnings naturally as part of tool results, encouraging it to consolidate its work and deliver a response before running out of iterations.`
Spanish: `La presión de presupuesto está habilitada de forma predeterminada. El agente ve las advertencias naturalmente como parte de los resultados de las herramientas, lo que lo anima a consolidar su trabajo y entregar una respuesta antes de quedarse sin iteraciones.`

---

## Section 27: Auxiliary Models (Lines 606-682)

### Heading
English: `## Auxiliary Models`
Spanish: `## Modelos auxiliares`

### Intro (Lines 608-609)
English: `Hermes uses lightweight "auxiliary" models for side tasks like image analysis, web page summarization, and browser screenshot analysis. By default, these use **Gemini Flash** via OpenRouter or Nous Portal — you don't need to configure anything.`
Spanish: `Hermes utiliza modelos "auxiliares" livianos para tareas secundarias como análisis de imágenes, resumen de páginas web y análisis de capturas de pantalla del navegador. Por defecto, estos utilizan **Gemini Flash** a través de OpenRouter o Nous Portal — no necesitas configurar nada.`

### Closing (Lines 611-613)
English: `To use a different model, add an `auxiliary` section to `~/.hermes/config.yaml`:`
Spanish: `Para usar un modelo diferente, agrega una sección `auxiliary` a `~/.hermes/config.yaml`:`

### Comments
- "Image analysis (vision_analyze tool + browser screenshots)" → "Análisis de imágenes (herramienta vision_analyze + capturas de pantalla del navegador)"
- "Web page summarization + browser page text extraction" → "Resumen de página web + extracción de texto de página del navegador"

### Subheading (Line 625)
English: `### Changing the Vision Model`
Spanish: `### Cambiar el modelo de visión`

### Text (Line 627)
English: `To use GPT-4o instead of Gemini Flash for image analysis:`
Spanish: `Para usar GPT-4o en lugar de Gemini Flash para análisis de imágenes:`

### Text (Line 633)
English: `Or via environment variable (in `~/.hermes/.env`):`
Spanish: `O a través de variable de entorno (en `~/.hermes/.env`):`

### Subheading (Line 639)
English: `### Provider Options`
Spanish: `### Opciones de proveedor`

### Table (Lines 641-649)
English headers:
```
| Provider | Description | Requirements |
```
Spanish headers:
```
| Proveedor | Descripción | Requisitos |
```

### Provider descriptions (translations):
- "Best available (default). Vision tries OpenRouter → Nous → Codex." → "Mejor disponible (predeterminado). La visión intenta OpenRouter → Nous → Codex."
- "Force OpenRouter — routes to any model (Gemini, GPT-4o, Claude, etc.)" → "Fuerza OpenRouter — enruta a cualquier modelo (Gemini, GPT-4o, Claude, etc.)"
- "Force Nous Portal" → "Fuerza Nous Portal"
- "Force Codex OAuth (ChatGPT account). Supports vision (gpt-5.3-codex)." → "Fuerza Codex OAuth (cuenta ChatGPT). Soporta visión (gpt-5.3-codex)."
- "Use your custom endpoint (`OPENAI_BASE_URL` + `OPENAI_API_KEY`). Works with OpenAI, local models, or any OpenAI-compatible API." → "Usa tu punto de conexión personalizado (`OPENAI_BASE_URL` + `OPENAI_API_KEY`). Funciona con OpenAI, modelos locales o cualquier API compatible con OpenAI."

### Requirements column:
- "—" stays the same
- "`OPENROUTER_API_KEY`" stays the same
- "`hermes login`" stays the same
- "`hermes model` → Codex" stays the same
- "`OPENAI_BASE_URL` + `OPENAI_API_KEY`" stays the same

### Subheading (Line 651)
English: `### Common Setups`
Spanish: `### Configuraciones comunes`

### Setup headers (translations):
1. "Using OpenAI API key for vision:" → "Usar clave API de OpenAI para visión:"
2. "Using OpenRouter for vision (route to any model):" → "Usar OpenRouter para visión (enruta a cualquier modelo):"
3. "Using Codex OAuth (ChatGPT Pro/Plus account — no API key needed):" → "Usar Codex OAuth (cuenta ChatGPT Pro/Plus — sin clave API requerida):"
4. "Using a local/self-hosted model:" → "Usar un modelo local/autoalojado:"

### Comment (Line 658)
English: `# In ~/.hermes/.env:`
Spanish: `# En ~/.hermes/.env:`

### Comment (Line 660)
English: `# uses your ChatGPT OAuth token`
Spanish: `# usa tu token OAuth de ChatGPT`

### Comment (Line 663)
English: `# model defaults to gpt-5.3-codex (supports vision)`
Spanish: `# el modelo por defecto es gpt-5.3-codex (soporta visión)`

### Comment (Line 666)
English: `# uses your OPENAI_BASE_URL endpoint`
Spanish: `# usa tu punto de conexión OPENAI_BASE_URL`

### Tip (Line 670)
English: `If you use Codex OAuth as your main model provider, vision works automatically — no extra configuration needed. Codex is included in the auto-detection chain for vision.`
Spanish: `Si usas Codex OAuth como tu proveedor de modelo principal, la visión funciona automáticamente — no se necesita configuración adicional. Codex se incluye en la cadena de detección automática para visión.`

### Warning (Lines 673-675)
English: `**Vision requires a multimodal model.** If you set `provider: "main"`, make sure your endpoint supports multimodal/vision — otherwise image analysis will fail.`
Spanish: `**La visión requiere un modelo multimodal.** Si configuraste `provider: "main"`, asegúrate de que tu punto de conexión soporta multimodal/visión — de lo contrario, el análisis de imágenes fallará.`

### Subheading (Line 678)
English: `### Environment Variables`
Spanish: `### Variables de entorno`

### Intro (Line 680)
English: `You can also configure auxiliary models via environment variables instead of `config.yaml`:`
Spanish: `También puedes configurar modelos auxiliares a través de variables de entorno en lugar de `config.yaml`:`

### Table (Lines 682-688)
English headers:
```
| Setting | Environment Variable |
```
Spanish headers:
```
| Ajuste | Variable de entorno |
```

### Settings (translations):
- "Vision provider" → "Proveedor de visión"
- "Vision model" → "Modelo de visión"
- "Web extract provider" → "Proveedor de extracción web"
- "Web extract model" → "Modelo de extracción web"
- "Compression provider" → "Proveedor de compresión"
- "Compression model" → "Modelo de compresión"

### Tip (Lines 691-692)
English: `Run `hermes config` to see your current auxiliary model settings. Overrides only show up when they differ from the defaults.`
Spanish: `Ejecuta `hermes config` para ver tus ajustes de modelo auxiliar actuales. Las anulaciones solo aparecen cuando difieren de los valores predeterminados.`

---

## Section 28: Reasoning Effort (Lines 684-707)

### Heading
English: `## Reasoning Effort`
Spanish: `## Esfuerzo de razonamiento`

### Intro (Line 686)
English: `Control how much "thinking" the model does before responding:`
Spanish: `Controla cuánto "pensamiento" hace el modelo antes de responder:`

### Comment
- "empty = medium (default). Options: xhigh (max), high, medium, low, minimal, none" → "vacío = medio (predeterminado). Opciones: xhigh (máximo), alto, medio, bajo, mínimo, ninguno"

### Text (Lines 691-693)
English: `When unset (default), reasoning effort defaults to "medium" — a balanced level that works well for most tasks. Setting a value overrides it — higher reasoning effort gives better results on complex tasks at the cost of more tokens and latency.`
Spanish: `Cuando no está configurado (predeterminado), el esfuerzo de razonamiento por defecto es "medio" — un nivel equilibrado que funciona bien para la mayoría de las tareas. Establecer un valor lo anula — el esfuerzo de razonamiento más alto da mejores resultados en tareas complejas al costo de más tokens y latencia.`

### Text (Lines 695-697)
English: `You can also change the reasoning effort at runtime with the `/reasoning` command:`
Spanish: `También puedes cambiar el esfuerzo de razonamiento en tiempo de ejecución con el comando `/reasoning`:`

### Comments
- "Show current effort level and display state" → "Mostrar nivel de esfuerzo actual y estado de pantalla"
- "Set reasoning effort to high" → "Establecer esfuerzo de razonamiento a alto"
- "Disable reasoning" → "Deshabilitar razonamiento"
- "Show model thinking above each response" → "Mostrar pensamiento del modelo encima de cada respuesta"
- "Hide model thinking" → "Ocultar pensamiento del modelo"

---

## Section 29: TTS Configuration (Lines 709-720)

### Heading
English: `## TTS Configuration`
Spanish: `## Configuración de TTS`

### Comment examples
- "322 voices, 74 languages" → "322 voces, 74 idiomas"
- All provider names stay in English

---

## Section 30: Display Settings (Lines 722-750)

### Heading
English: `## Display Settings`
Spanish: `## Ajustes de pantalla`

### Comment
- "Compact output mode (less whitespace)" → "Modo de salida compacta (menos espacios en blanco)"
- "Default personality for the CLI" → "Personalidad predeterminada para CLI"
- "show previous messages on resume" → "mostrar mensajes anteriores al reanudar"
- "one-liner only" → "solo una línea"
- "Play terminal bell when agent finishes (great for long tasks)" → "Reproduce campana de terminal cuando el agente termina (excelente para tareas largas)"
- "Show model reasoning/thinking above each response (toggle with /reasoning show|hide)" → "Mostrar razonamiento/pensamiento del modelo encima de cada respuesta (alternar con /reasoning show|hide)"

### Table headers
English: `Mode` → Spanish: `Modo`
English: `What you see` → Spanish: `Lo que ves`

### Modes (translations):
- "Silent — just the final response" → "Silencioso — solo la respuesta final"
- "Tool indicator only when the tool changes" → "Indicador de herramienta solo cuando cambia la herramienta"
- "Every tool call with a short preview (default)" → "Cada llamada de herramienta con una vista previa corta (predeterminado)"
- "Full args, results, and debug logs" → "Argumentos completos, resultados y registros de depuración"

---

## Section 31: Speech-to-Text (STT) (Lines 752-757)

### Heading
English: `## Speech-to-Text (STT)`
Spanish: `## Conversión de voz a texto (STT)`

### Comment
- "STT provider" → "Proveedor de STT"

### Text
English: `Requires `VOICE_TOOLS_OPENAI_KEY` in `.env` for OpenAI STT.`
Spanish: `Requiere `VOICE_TOOLS_OPENAI_KEY` en `.env` para STT de OpenAI.`

---

## Section 32: Quick Commands (Lines 759-783)

### Heading
English: `## Quick Commands`
Spanish: `## Comandos rápidos`

### Intro (Lines 761-762)
English: `Define custom commands that run shell commands without invoking the LLM — zero token usage, instant execution. Especially useful from messaging platforms (Telegram, Discord, etc.) for quick server checks or utility scripts.`
Spanish: `Define comandos personalizados que ejecuten comandos de shell sin invocar el LLM — cero uso de tokens, ejecución instantánea. Especialmente útil desde plataformas de mensajería (Telegram, Discord, etc.) para verificaciones rápidas del servidor o scripts de utilidad.`

### Usage (Lines 775-776)
English: `Usage: type `/status`, `/disk`, `/update`, or `/gpu` in the CLI or any messaging platform. The command runs locally on the host and returns the output directly — no LLM call, no tokens consumed.`
Spanish: `Uso: escribe `/status`, `/disk`, `/update`, o `/gpu` en CLI o en cualquier plataforma de mensajería. El comando se ejecuta localmente en el host y devuelve la salida directamente — sin llamada LLM, sin tokens consumidos.`

### Bullet points (Lines 778-783)
English:
```
- **30-second timeout** — long-running commands are killed with an error message
- **Priority** — quick commands are checked before skill commands, so you can override skill names
- **Type** — only `exec` is supported (runs a shell command); other types show an error
- **Works everywhere** — CLI, Telegram, Discord, Slack, WhatsApp, Signal
```

Spanish:
```
- **Tiempo de espera de 30 segundos** — los comandos de larga duración se matan con un mensaje de error
- **Prioridad** — los comandos rápidos se comprueban antes de los comandos de habilidad, por lo que puedes anular nombres de habilidad
- **Tipo** — solo `exec` se admite (ejecuta un comando de shell); otros tipos muestran un error
- **Funciona en todas partes** — CLI, Telegram, Discord, Slack, WhatsApp, Signal
```

---

## Section 33: Human Delay (Lines 785-791)

### Heading
English: `## Human Delay`
Spanish: `## Retardo humano`

### Intro (Line 787)
English: `Simulate human-like response pacing in messaging platforms:`
Spanish: `Simula ritmo de respuesta similar al humano en plataformas de mensajería:`

### Comments
- "off | natural | custom" → "off | natural | custom" (stay the same, these are mode values)
- "Minimum delay (custom mode)" → "Retardo mínimo (modo personalizado)"
- "Maximum delay (custom mode)" → "Retardo máximo (modo personalizado)"

---

## Section 34: Code Execution (Lines 793-799)

### Heading
English: `## Code Execution`
Spanish: `## Ejecución de código`

### Intro (Line 795)
English: `Configure the sandboxed Python code execution tool:`
Spanish: `Configura la herramienta de ejecución de código Python aislada:`

### Comments
- "Max execution time in seconds" → "Tiempo máximo de ejecución en segundos"
- "Max tool calls within code execution" → "Máximo de llamadas de herramienta dentro de la ejecución de código"

---

## Section 35: Browser (Lines 801-807)

### Heading
English: `## Browser`
Spanish: `## Navegador`

### Intro (Line 803)
English: `Configure browser automation behavior:`
Spanish: `Configura el comportamiento de automatización del navegador:`

### Comments
- "Seconds before auto-closing idle sessions" → "Segundos antes de cerrar automáticamente sesiones inactivas"
- "Auto-record browser sessions as WebM videos to ~/.hermes/browser_recordings/" → "Graba automáticamente sesiones del navegador como videos WebM en ~/.hermes/browser_recordings/"

---

## Section 36: Checkpoints (Lines 809-815)

### Heading
English: `## Checkpoints`
Spanish: `## Puntos de control`

### Intro (Line 811)
English: `Automatic filesystem snapshots before destructive file operations. See the [Checkpoints feature page](/docs/user-guide/features/checkpoints) for details.`
Spanish: `Instantáneas automáticas del sistema de archivos antes de operaciones destructivas de archivos. Consulta la [página de características de Checkpoints](/docs/user-guide/features/checkpoints) para detalles.`

### Comments
- "Enable automatic checkpoints (also: hermes --checkpoints)" → "Habilita puntos de control automáticos (también: hermes --checkpoints)"
- "Max checkpoints to keep per directory" → "Máximo de puntos de control para mantener por directorio"

---

## Section 37: Delegation (Lines 817-836)

### Heading
English: `## Delegation`
Spanish: `## Delegación`

### Intro (Line 819)
English: `Configure subagent behavior for the delegate tool:`
Spanish: `Configura el comportamiento del subagente para la herramienta de delegación:`

### Comment
- "Max iterations per subagent" → "Máximo de iteraciones por subagente"
- "Toolsets available to subagents" → "Conjuntos de herramientas disponibles para subagentes"
- "Override model (empty = inherit parent)" → "Anular modelo (vacío = heredar del padre)"
- "Override provider (empty = inherit parent)" → "Anular proveedor (vacío = heredar del padre)"

### Subheading (Line 829)
English: `**Subagent provider:model override:**`
Spanish: `**Anulación de proveedor:modelo de subagente:**`

### Text (Lines 829-831)
English: `By default, subagents inherit the parent agent's provider and model. Set `delegation.provider` and `delegation.model` to route subagents to a different provider:model pair — e.g., use a cheap/fast model for narrowly-scoped subtasks while your primary agent runs an expensive reasoning model.`
Spanish: `Por defecto, los subagentes heredan el proveedor y modelo del agente padre. Establece `delegation.provider` y `delegation.model` para enrutar subagentes a un par proveedor:modelo diferente — p. ej., usa un modelo barato/rápido para subtareas de alcance limitado mientras tu agente principal ejecuta un modelo de razonamiento costoso.`

### Text (Line 833)
English: `The delegation provider uses the same credential resolution as CLI/gateway startup. All configured providers are supported: `openrouter`, `nous`, `zai`, `kimi-coding`, `minimax`, `minimax-cn`. When a provider is set, the system automatically resolves the correct base URL, API key, and API mode — no manual credential wiring needed.`
Spanish: `El proveedor de delegación utiliza la misma resolución de credenciales que el inicio de CLI/gateway. Se admiten todos los proveedores configurados: `openrouter`, `nous`, `zai`, `kimi-coding`, `minimax`, `minimax-cn`. Cuando se establece un proveedor, el sistema automáticamente resuelve la URL base, clave API y modo API correcto — no se necesita enrutamiento manual de credenciales.`

### Subheading (Line 835)
English: `**Precedence:**`
Spanish: `**Precedencia:**`

### Text (Line 835-836)
English: `_`delegation.provider` in config → parent provider (inherited). `delegation.model` in config → parent model (inherited). Setting just `model` without `provider` changes only the model name while keeping the parent's credentials (useful for switching models within the same provider like OpenRouter)._`
Spanish: `_`delegation.provider` en config → proveedor padre (heredado). `delegation.model` en config → modelo padre (heredado). Establecer solo `model` sin `provider` cambia solo el nombre del modelo mientras se mantienen las credenciales del padre (útil para cambiar modelos dentro del mismo proveedor como OpenRouter)._`

---

## Section 38: Clarify (Lines 838-842)

### Heading
English: `## Clarify`
Spanish: `## Aclarar`

### Intro (Line 840)
English: `Configure the clarification prompt behavior:`
Spanish: `Configura el comportamiento de la solicitud de aclaración:`

### Comment
- "Seconds to wait for user clarification response" → "Segundos para esperar respuesta de aclaración del usuario"

---

## Section 39: Context Files (Lines 844-857)

### Heading
English: `## Context Files (SOUL.md, AGENTS.md)`
Spanish: `## Archivos de contexto (SOUL.md, AGENTS.md)`

### Intro (Line 846)
English: `Drop these files in your project directory and the agent automatically picks them up:`
Spanish: `Suelta estos archivos en tu directorio de proyecto y el agente los captura automáticamente:`

### Table (Lines 848-853)
English headers:
```
| File | Purpose |
```
Spanish headers:
```
| Archivo | Propósito |
```

### Files and purposes (translations):
- "Project-specific instructions, coding conventions" → "Instrucciones específicas del proyecto, convenciones de codificación"
- "Persona definition — the agent embodies this personality" → "Definición de persona — el agente encarna esta personalidad"
- "Cursor IDE rules (also detected)" → "Reglas de IDE Cursor (también detectadas)"
- "Cursor rule files (also detected)" → "Archivos de regla de Cursor (también detectados)"

### Bullet points (Lines 855-857)
English:
```
- **AGENTS.md** is hierarchical: if subdirectories also have AGENTS.md, all are combined.
- **SOUL.md** checks cwd first, then `~/.hermes/SOUL.md` as a global fallback.
- All context files are capped at 20,000 characters with smart truncation.
```

Spanish:
```
- **AGENTS.md** es jerárquico: si los subdirectorios también tienen AGENTS.md, todos se combinan.
- **SOUL.md** verifica primero cwd, luego `~/.hermes/SOUL.md` como respaldo global.
- Todos los archivos de contexto se cap en 20.000 caracteres con truncamiento inteligente.
```

---

## Section 40: Working Directory (Lines 859-872)

### Heading
English: `## Working Directory`
Spanish: `## Directorio de trabajo`

### Table (Lines 861-866)
English headers:
```
| Context | Default |
```
Spanish headers:
```
| Contexto | Predeterminado |
```

### Contexts (translations):
- "Current directory where you run the command" → "Directorio actual donde ejecutas el comando"
- "Home directory `~` (override with `MESSAGING_CWD`)" → "Directorio de inicio `~` (anula con `MESSAGING_CWD`)"
- "User's home directory inside the container or remote machine" → "Directorio de inicio del usuario dentro del contenedor o máquina remota"

### Intro (Line 868)
English: `Override the working directory:`
Spanish: `Anula el directorio de trabajo:`

### Comments
- "In ~/.hermes/.env or ~/.hermes/config.yaml:" → "En ~/.hermes/.env o ~/.hermes/config.yaml:"
- "Gateway sessions" → "Sesiones de puerta de enlace"
- "All terminal sessions" → "Todas las sesiones de terminal"

---

## Summary of Translation Metrics

- **Total sections:** 40
- **Headings to translate:** 40
- **Table headers to translate:** 8
- **Informational boxes (tips, warnings, notes):** 20+
- **Comments in code blocks to translate:** 50+
- **Prose sections to translate:** 80+
- **Code blocks to preserve exactly:** 30+
- **File paths to preserve:** 100+
- **Command names to preserve:** 50+
- **Environment variable names to preserve:** 30+
- **Provider names to preserve:** 15+
- **Model names to preserve:** 25+

## Special Translation Notes

1. **Provider names remain in English:**
   - OpenRouter, Anthropic, OpenAI, Nous, Codex, Azure OpenAI, etc.

2. **Keep these unchanged:**
   - All file paths (~/. hermes/, ~/.codex/, etc.)
   - All environment variable names (OPENAI_API_KEY, etc.)
   - All command names (hermes config, hermes model, etc.)
   - All code blocks (YAML, bash, etc.)
   - All table structures
   - All URLs and links
   - All model names (claude-sonnet-4, gpt-4o, etc.)

3. **Translate:**
   - All section headings
   - All prose text
   - All explanations and descriptions
   - All comments in YAML examples (not code syntax)
   - All tip/warning/info box text
   - All list items
   - All table cell content (except URLs and technical names)

