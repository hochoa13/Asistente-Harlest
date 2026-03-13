---
sidebar_position: 1
title: "Inicio Rápido"
description: "Tu primera conversación con Hermes Agent — de instalar a chatear en 2 minutos"
---

# Inicio Rápido

Esta guía te camina a través de instalar Hermes Agent, configurar un proveedor y tener tu primera conversación. Al final, conocerás las características clave y cómo explorar más.

## 1. Instala Hermes Agent

Ejecuta el instalador de una línea:

```bash
# Linux / macOS / WSL2
curl -fsSL https://raw.githubusercontent.com/hochoa13/Asistente-Harlest/main/scripts/install.sh | bash
```

:::tip Usuarios de Windows
Instala [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install) primero, luego ejecuta el comando anterior dentro de tu terminal WSL2.
:::

Después de que termine, recarga tu shell:

```bash
source ~/.bashrc   # or source ~/.zshrc
```

## 2. Configura un Proveedor

El instalador configura tu proveedor LLM automáticamente. Para cambiarlo después, usa uno de estos comandos:

```bash
hermes model       # Elige tu proveedor LLM y modelo
hermes tools       # Configura qué herramientas están habilitadas
hermes setup       # O configura todo de una vez
```

`hermes model` te camina a través de seleccionar un proveedor de inferencia:

| Proveedor | Qué es | Cómo configurar |
|----------|--------|----------------|
| **Portal de Nous** | Basado en suscripción, sin configuración | Inicio de sesión OAuth vía `hermes model` |
| **OpenAI Codex** | ChatGPT OAuth, usa modelos Codex | Autenticación de código de dispositivo vía `hermes model` |
| **Anthropic** | Modelos Claude directamente (Pro/Max o clave API) | Clave API o token de configuración Claude Code |
| **OpenRouter** | Más de 200 modelos, paga por uso | Ingresa tu clave API |
| **Endpoint Personalizado** | VLLM, SGLang, cualquier API compatible con OpenAI | Establece URL base + clave API |

:::tip
Puedes cambiar proveedores en cualquier momento con `hermes model` — sin cambios de código, sin bloqueo.
:::

## 3. Empieza a Chatear

```bash
hermes
```

¡Eso es todo! Verás un banner de bienvenida con tu modelo, herramientas disponibles y habilidades. Escribe un mensaje y presiona Enter.

```
❯ ¿Con qué puedo ayudarte?
```

El agente tiene acceso a herramientas para búsqueda web, operaciones de archivos, comandos de terminal y más — todo listo para usar.

## 4. Prueba Características Clave

### Pídele que use la terminal

```
❯ ¿Cuál es mi uso del disco? Muestra los 5 directorios más grandes.
```

El agente ejecutará comandos de terminal en tu nombre y te mostrará los resultados.

### Usa comandos slash

Escribe `/` para ver un menú desplegable de autocompletar con todos los comandos:

| Comando | Qué hace |
|---------|----------|
| `/help` | Muestra todos los comandos disponibles |
| `/tools` | Lista las herramientas disponibles |
| `/model` | Cambia modelos de forma interactiva |
| `/personality pirate` | Prueba una personalidad divertida |
| `/save` | Guarda la conversación |

### Entrada multilínea

Presiona `Alt+Enter` o `Ctrl+J` para añadir una nueva línea. Excelente para pegar código o escribir prompts detallados.

### Interrumpe el agente

Si el agente está tardando demasiado, simplemente escribe un nuevo mensaje y presiona Enter — interrumpe la tarea actual y cambia a tus nuevas instrucciones. `Ctrl+C` también funciona.

### Reanuda una sesión

Cuando salgas, hermes imprime un comando de reanudación:

```bash
hermes --continue    # Reanuda la sesión más reciente
hermes -c            # Forma abreviada
```

## 5. Explora Más

Aquí hay algunas cosas que puedes probar a continuación:

### Configura una terminal sandboxed

Por seguridad, ejecuta el agente en un contenedor Docker o en un servidor remoto:

```bash
hermes config set terminal.backend docker    # Aislamiento Docker
hermes config set terminal.backend ssh       # Servidor remoto
```

### Conecta plataformas de mensajería

Chatea con Hermes desde tu teléfono vía Telegram, Discord, Slack o WhatsApp:

```bash
hermes gateway setup    # Configuración interactiva de plataformas
```

### Programa tareas automatizadas

```
❯ Cada mañana a las 9am, revisa Hacker News para noticias de IA y envíame un resumen en Telegram.
```

El agente configurará un trabajo cron que se ejecuta automáticamente a través de la puerta de enlace.

### Busca e instala habilidades

```bash
hermes skills search kubernetes
hermes skills install openai/skills/k8s
```

O usa el comando slash `/skills` dentro del chat.

### Prueba servidores MCP

Conéctate a herramientas externas a través del Protocolo de Contexto de Modelo:

```yaml
# Añade a ~/.hermes/config.yaml
mcp_servers:
  github:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxx"
```

---

## Referencia Rápida

| Comando | Descripción |
|---------|-------------|
| `hermes` | Empieza a chatear |
| `hermes model` | Elige tu proveedor LLM y modelo |
| `hermes tools` | Configura qué herramientas están habilitadas por plataforma |
| `hermes setup` | Asistente de configuración completo (configura todo de una vez) |
| `hermes doctor` | Diagnostica problemas |
| `hermes update` | Actualiza a la última versión |
| `hermes gateway` | Inicia la puerta de enlace de mensajería |
| `hermes --continue` | Reanuda la última sesión |

## Próximos Pasos

- **[Guía CLI](../user-guide/cli.md)** — Domina la interfaz de terminal
- **[Configuración](../user-guide/configuration.md)** — Personaliza tu configuración
- **[Puerta de Enlace de Mensajería](../user-guide/messaging/index.md)** — Conecta Telegram, Discord, Slack, WhatsApp
- **[Herramientas y Conjuntos](../user-guide/features/tools.md)** — Explora capacidades disponibles
