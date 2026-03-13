---
title: Automatización de Navegador
description: Controla navegadores en la nube con integración Browserbase para interacción web, relleno de formularios, scraping y mucho más.
sidebar_label: Navegador
sidebar_position: 5
---

# Automatización de Navegador

Hermes Agent incluye un conjunto completo de herramientas de automatización de navegador impulsado por [Browserbase](https://browserbase.com), permitiendo que el agente navegue sitios web, interactúe con elementos de la página, rellene formularios y extraiga información — todo ejecutándose en navegadores alojados en la nube con características antibots sigilosas integradas.

## Descripción General

Las herramientas de navegador usan el CLI `agent-browser` con ejecución en la nube de Browserbase. Las páginas se representan como **árboles de accesibilidad** (instantáneas basadas en texto), lo que los hace ideales para agentes LLM. Los elementos interactivos obtienen IDs de referencia (como `@e1`, `@e2`) que el agente usa para hacer clic y escribir.

Capacidades clave:

- **Ejecución en la nube** — no se necesita navegador local
- **Sigilo integrado** — huellas dactilares aleatorias, resolución de CAPTCHA, proxies residenciales
- **Aislamiento de sesión** — cada tarea obtiene su propia sesión de navegador
- **Limpieza automática** — las sesiones inactivas se cierran después de un tiempo de espera
- **Análisis de visión** — Captura de pantalla + análisis de IA para comprensión visual

## Configuración

### Variables de Entorno Requeridas

```bash
# Agregar a ~/.hermes/.env
BROWSERBASE_API_KEY=your-api-key-here
BROWSERBASE_PROJECT_ID=your-project-id-here
```

Obtén tus credenciales en [browserbase.com](https://browserbase.com).

### Variables de Entorno Opcionales

```bash
# Proxies residenciales para mejor resolución de CAPTCHA (predeterminado: "true")
BROWSERBASE_PROXIES=true

# Sigilo avanzado con Chromium personalizado — requiere Plan Scale (predeterminado: "false")
BROWSERBASE_ADVANCED_STEALTH=false

# Reconexión de sesión después de desconexiones — requiere plan de pago (predeterminado: "true")
BROWSERBASE_KEEP_ALIVE=true

# Tiempo de espera de sesión personalizado en milisegundos (predeterminado: proyecto predeterminado)
# Ejemplos: 600000 (10min), 1800000 (30min)
BROWSERBASE_SESSION_TIMEOUT=600000

# Tiempo de espera de inactividad antes de limpieza automática en segundos (predeterminado: 300)
BROWSER_INACTIVITY_TIMEOUT=300
```

### Instalar CLI de agent-browser

```bash
npm install -g agent-browser
# O instalar localmente en el repositorio:
npm install
```

:::información
El conjunto de herramientas `Browser` debe estar incluido en la lista `toolsets` de tu configuración o habilitado via `hermes config set toolsets '["hermes-cli", "browser"]'`.
:::

## Herramientas Disponibles

### `browser_navigate`

Navega a una URL. Debe llamarse antes que cualquier otra herramienta de navegador. Inicializa la sesión de Browserbase.

```
Navigate to https://github.com/NousSearch
```

:::consejo
Para recuperación simple de información, prefiere `web_search` o `web_extract` — son más rápidas y económicas. Usa herramientas de navegador cuando necesites **interactuar** con una página (hacer clic en botones, rellenar formularios, manejar contenido dinámico).
:::

### `browser_snapshot`

Obtén una instantánea basada en texto del árbol de accesibilidad de la página actual. Devuelve elementos interactivos con IDs de referencia como `@e1`, `@e2` para usar con `browser_click` y `browser_type`.

- **`full=false`** (predeterminado): Vista compacta mostrando solo elementos interactivos
- **`full=true`**: Contenido completo de la página

Las instantáneas de más de 8000 caracteres se resumen automáticamente por un LLM.

### `browser_click`

Haz clic en un elemento identificado por su ID de referencia de la instantánea.

```
Click @e5 to press the "Sign In" button
```

### `browser_type`

Escribe texto en un campo de entrada. Primero limpia el campo, luego escribe el nuevo texto.

```
Type "hermes agent" into the search field @e3
```

### `browser_scroll`

Desplázate hacia arriba o hacia abajo en la página para revelar más contenido.

```
Scroll down to see more results
```

### `browser_press`

Presiona una tecla del teclado. Útil para enviar formularios o navegación.

```
Press Enter to submit the form
```

Teclas soportadas: `Enter`, `Tab`, `Escape`, `ArrowDown`, `ArrowUp` y más.

### `browser_back`

Navega a la página anterior en el historial del navegador.

### `browser_get_images`

Lista todas las imágenes en la página actual con sus URLs y texto alternativo. Útil para encontrar imágenes a analizar.

### `browser_vision`

Toma una captura de pantalla y analízala con IA de Visión. Usa esto cuando las instantáneas de texto no capturen información visual importante — especialmente útil para CAPTCHAs, diseños complejos o desafíos de verificación visual.

La captura de pantalla se guarda persistentemente y la ruta del archivo se devuelve junto con el análisis de IA. En plataformas de mensajería (Telegram, Discord, Slack, WhatsApp), puedes pedirle al agente que comparta la captura de pantalla — se enviará como un archivo adjunto de foto nativa a través del mecanismo `MEDIA:`.

```
What does the chart on this page show?
```

Las capturas de pantalla se almacenan en `~/.hermes/browser_screenshots/` y se limpian automáticamente después de 24 horas.

### `browser_console`

Obtén la salida de la consola del navegador (mensajes de registro/advertencia/error) y excepciones de JavaScript no capturadas de la página actual. Esencial para detectar errores de JS silenciosos que no aparecen en el árbol de accesibilidad.

```
Check the browser console for any JavaScript errors
```

Usa `clear=True` para limpiar la consola después de leer, para que las llamadas posteriores solo muestren mensajes nuevos.

### `browser_close`

Cierra la sesión del navegador y libera recursos. Llama a esto cuando termines para liberar la cuota de sesión de Browserbase.

## Ejemplos Prácticos

### Rellenando un Formulario Web

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

### Búsqueda de Contenido Dinámico

```
User: What are the top trending repos on GitHub right now?

Agent workflow:
1. browser_navigate("https://github.com/trending")
2. browser_snapshot(full=true)  → reads trending repo list
3. Returns formatted results
4. browser_close()
```

## Grabación de Sesión

Graba automáticamente sesiones de navegador como archivos de video WebM:

```yaml
browser:
  record_sessions: true  # predeterminado: false
```

Cuando está habilitado, la grabación se inicia automáticamente en el primer `browser_navigate` y se guarda en `~/.hermes/browser_recordings/` cuando se cierra la sesión. Funciona en modos locales y en la nube (Browserbase). Las grabaciones más antiguas de 72 horas se limpian automáticamente.

## Características de Sigilo

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
