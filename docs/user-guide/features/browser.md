---
title: Navegador Automation
description: control cloud browsers with Navegadorbase integration for web interaction, form filling, scraping, and more.
sidebar_label: Navegador
sidebar_position: 5
---

# Navegador Automation

Hermes Agent includes a full Navegador automation conjunto de herramientas powered by [Navegadorbase](https://browserbase.com), enabling the agent to navegar websites, interact with page elements, fill forms, and extract information — all running in cloud-hosted browsers with built-in anti-bot características furtivas.

## Descripción General

The herramientas de navegador Usar the `agent-Navegador` CLI with Navegadorbase cloud execution. Pages are represented as **árboles de accesibilidad** (text-based snapshots), making them ideal for LLM agents. Interactive elements Obtener ref IDs (like `@e1`, `@e2`) that the agent uses for clicking and typing.

Key capabilities:

- **Cloud execution** — no local Navegador needed
- **Built-in stealth** — random fingerprints, CAPTCHA solving, residential proxies
- **Session isolation** — each task gets its own Navegador session
- **Automatic cleanup** — inactive sessions are closed after a timeout
- **Visión analysis** — Captura de pantalla + AI analysis for visual understanding

## Configuración

### Required entorno Variables

```bash
# Add to ~/.hermes/.env
BROWSERBASE_API_KEY=your-api-key-here
BROWSERBASE_PROJECT_ID=your-project-id-here
```

Obtener your credenciales at [browserbase.com](https://browserbase.com).

### Optional entorno Variables

```bash
# Residential proxies for better CAPTCHA solving (default: "true")
BROWSERBASE_PROXIES=true

# Advanced stealth with custom Chromium — requires Scale Plan (default: "false")
BROWSERBASE_ADVANCED_STEALTH=false

# Session reconnection after disconnects — requires paid plan (default: "true")
BROWSERBASE_KEEP_ALIVE=true

# Custom session timeout in milliseconds (default: project default)
# Ejemplos: 600000 (10min), 1800000 (30min)
BROWSERBASE_SESSION_TIMEOUT=600000

# Inactivity timeout before auto-cleanup in seconds (default: 300)
BROWSER_INACTIVITY_TIMEOUT=300
```

### Instalar agent-Navegador CLI

```bash
npm install -g agent-browser
# Or install locally in the repo:
npm install
```

:::Información
The `Navegador` conjunto de herramientas must be included in your config's `Conjuntos de herramientas` list or enabled via `hermes config Establecer Conjuntos de herramientas '["hermes-cli", "Navegador"]'`.
:::

## Available Herramientas

### `browser_navigate`

navegar to a URL. Must be called before any other Navegador herramienta. Initializes the Navegadorbase session.

```
Navigate to https://github.com/NousRebuscar
```

:::Consejo
For simple information retrieval, prefer `web_buscar` or `web_extract` — they are faster and cheaper. Usar herramientas de navegador when you need to **interact** with a page (hacer clic buttons, fill forms, handle dynamic content).
:::

### `browser_snapshot`

Obtener a text-based snapshot of the current page's accessibility tree. Returns interactive elements with ref IDs like `@e1`, `@e2` for Usar with `browser_click` and `browser_type`.

- **`full=false`** (default): Compact view showing only interactive elements
- **`full=true`**: Completo page content

Snapshots over 8000 characters are automatically summarized by an LLM.

### `browser_click`

hacer clic an element identified by its ref ID from the snapshot.

```
Click @e5 to press the "Sign In" button
```

### `browser_type`

escribir text into an input field. Clears the field first, then types the new text.

```
Type "hermes agent" into the buscar field @e3
```

### `browser_scroll`

desplazar the page up or down to reveal more content.

```
Scroll down to see more results
```

### `browser_press`

Press a keyboard key. Useful for submitting forms or navigation.

```
Press Enter to submit the form
```

Supported keys: `Enter`, `Tab`, `Escape`, `ArrowDown`, `ArrowUp`, and more.

### `browser_back`

navegar back to the previous page in Navegador history.

### `browser_get_images`

List all images on the current page with their URLs and alt text. Useful for finding images to analyze.

### `browser_vision`

Take a Captura de pantalla and analyze it with Visión AI. Usar this when text snapshots don't capture Importante visual information — especially useful for CAPTCHAs, complex layouts, or visual verification challenges.

The Captura de pantalla is saved persistently and the archivo ruta is returned alongside the AI analysis. On messaging platforms (Telegram, Discord, Slack, WhatsApp), you can ask the agent to share the Captura de pantalla — it will be sent as a native photo attachment via the `MEDIA:` mechanism.

```
What does the chart on this page show?
```

Screenshots are stored in `~/.hermes/browser_screenshots/` and automatically cleaned up after 24 hours.

### `browser_console`

Obtener Navegador console output (log/warn/error messages) and uncaught JavaScript exceptions from the current page. Essential for detecting silent JS errors that don't appear in the accessibility tree.

```
Check the browser console for any JavaScript errors
```

Usar `clear=True` to clear the console after reading, so subsequent calls only show new messages.

### `browser_close`

Close the Navegador session and release resources. Call this when done to free up Navegadorbase session quota.

## Practical Ejemplos

### Filling Out a Web Form

```
User: Sign up for an account on example.com with my email john@example.com

Agent workflow:
1. browser_navigate("https://example.com/signup")
2. browser_snapshot()  → sees form fields with refs
3. browser_type(ref="@e3", text="john@example.com")
4. browser_type(ref="@e5", text="SecurePass123")
5. browser_click(ref="@e8")  → clicks "Create Account"
6. browser_snapshot()  → confirms success
7. browser_close()
```

### Rebuscaring Dynamic Content

```
User: What are the top trending repos on GitHub right now?

Agent workflow:
1. browser_navigate("https://github.com/trending")
2. browser_snapshot(full=true)  → reads trending repo list
3. Returns formatted results
4. browser_close()
```

## grabación de sesión

Automatically record Navegador sessions as WebM video files:

```yaml
browser:
  record_sessions: true  # default: false
```

When enabled, recording starts automatically on the first `browser_navigate` and saves to `~/.hermes/browser_recordings/` when the session closes. Works in both local and cloud (Navegadorbase) modes. Recordings older than 72 hours are automatically cleaned up.

## Stealth Características

Navegadorbase provides automatic stealth capabilities:

| Feature | Default | Notes |
|---------|---------|-------|
| Basic Stealth | Always on | Random fingerprints, viewport randomization, CAPTCHA solving |
| Residential Proxies | On | Routes through residential IPs for better access |
| Advanced Stealth | Off | Custom Chromium build, requires Scale Plan |
| Keep Alive | On | Session reconnection after network hiccups |

:::note
If paid features aren't available on your plan, Hermes automatically falls back — first disabling `keepAlive`, then proxies — so browsing still works on free plans.
:::

## Session Management

- Each task gets an isolated Navegador session via Navegadorbase
- Sesiones are automatically cleaned up after inactivity (default: 5 minutes)
- A background thread checks every 30 seconds for stale sessions
- Emergency cleanup runs on process exit to prevent orphaned sessions
- Sesiones are released via the Navegadorbase API (`REQUEST_RELEASE` status)

## Limitations

- **Requires Navegadorbase account** — no local Navegador fallback
- **Requires `agent-Navegador` CLI** — must be installed via npm
- **Text-based interaction** — relies on accessibility tree, not pixel coordinates
- **Snapshot size** — large pages may be truncated or LLM-summarized at 8000 characters
- **Session timeout** — sessions expire based on your Navegadorbase plan settings
- **Cost** — each session consumes Navegadorbase credits; Usar `browser_close` when done
- **No archivo downloads** — cannot download files from the Navegador
