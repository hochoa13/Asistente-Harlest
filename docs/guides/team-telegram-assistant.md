---
sidebar_position: 3
title: "Tutorial: Asistente de Equipo Telegram"
description: "Guía paso a paso para configurar un bot Telegram que todo tu equipo pueda usar for code help, research, system admin, and more"
---

# Configura un Asistente de Equipo Telegram

Este tutorial te guía a través de la configuración de un bot de Telegram impulsado por Hermes Agent que múltiples miembros del equipo pueden usar. Al final, tu equipo tendrá un asistente de IA compartido al que pueden enviar mensajes para obtener ayuda con código, investigación, administración de sistemas y cualquier otra cosa — asegurado con autorización por usuario.

## Qué Estamos Construyendo

Un bot de Telegram que:

- **Cualquier miembro del equipo autorizado** puede DM para obtener ayuda — revisiones de código, investigación, comandos de shell, depuración
- **Se ejecuta en tu servidor** con acceso completo a herramientas — terminal, edición de archivos, búsqueda web, ejecución de código
- **Sesiones por usuario** — cada persona obtiene su propio contexto de conversación
- **Seguro por defecto** — solo los usuarios aprobados pueden interactuar, con dos métodos de autorización
- **Tareas programadas** — puestas al día diarias, verificaciones de salud y recordatorios entregados a un canal de equipo

---

## Requisitos Previos

Antes de comenzar, asegúrate de tener:

- **Hermes Agent instalado** en un servidor o VPS (no tu laptop — el bot necesita estar en ejecución). Sigue la [guía de instalación](/getting-started/learning-path) si aún no lo has hecho.
- **Una cuenta de Telegram** para ti (el propietario del bot)
- **Un proveedor de LLM configurado** — como mínimo, una clave API para OpenAI, Anthropic u otro proveedor compatible en `~/.hermes/.env`

:::tip
Un VPS de $5/mes es suficiente para ejecutar el gateway. Hermes en sí es ligero — las llamadas a la API de LLM son lo que cuesta dinero, y suceden de forma remota.
:::

---

## Paso 1: Crea un Bot de Telegram

Cada bot de Telegram comienza con **@BotFather** — el bot oficial de Telegram para crear bots.

1. **Abre Telegram** y busca `@BotFather`, o ve a [t.me/BotFather](https://t.me/BotFather)

2. **Envía `/newbot`** — BotFather te preguntará dos cosas:
   - **Nombre para mostrar** — lo que ven los usuarios (por ejemplo, `Asistente Team Hermes`)
   - **Nombre de usuario** — debe terminar en `bot` (por ejemplo, `miequipo_hermes_bot`)

3. **Copia el token del bot** — BotFather responde con algo como:
   ```
   Usa este token para acceder a la API HTTP:
   7123456789:AAH1bGciOiJSUzI1NiIsInR5cCI6Ikp...
   ```
   Guarda este token — lo necesitarás en el próximo paso.

4. **Establece una descripción** (opcional pero recomendado):
   ```
   /setdescription
   ```
   Elige tu bot, luego ingresa algo como:
   ```
   Asistente de IA del equipo impulsado por Hermes Agent. Envíame un DM para obtener ayuda con código, investigación, depuración y más.
   ```

5. **Establece comandos del bot** (opcional — da a los usuarios un menú de comando):
   ```
   /setcommands
   ```
   Elige tu bot, luego pega:
   ```
   new - Comienza una conversación nueva
   model - Mostrar o cambiar el modelo de IA
   status - Mostrar información de sesión
   help - Mostrar comandos disponibles
   stop - Detener la tarea actual
   ```

:::warning
Mantén tu token de bot en secreto. Cualquiera con el token puede controlar el bot. Si se filtra, usa `/revoke` en BotFather para generar uno nuevo.
:::

---

## Paso 2: Configura el Gateway

Tienes dos opciones: el asistente de configuración interactiva (recomendado) o configuración manual.

### Opción A: Configuración Interactiva (Recomendada)

```bash
hermes gateway setup
```

Esto te guía a través de todo con selección de tecla de flecha. Elige **Telegram**, pega tu token de bot e ingresa tu ID de usuario cuando se solicite.

### Opción B: Configuración Manual

Añade estas líneas a `~/.hermes/.env`:

```bash
# Token del bot de Telegram de BotFather
TELEGRAM_BOT_TOKEN=7123456789:AAH1bGciOiJSUzI1NiIsInR5cCI6Ikp...

# Your Telegram user ID (numeric)
TELEGRAM_ALLOWED_USERS=123456789
```

### Finding Your User ID

Your Telegram user ID is a numeric value (not your username). To find it:

1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. It instantly replies with your numeric user ID
3. Copy that number into `TELEGRAM_ALLOWED_USERS`

:::info
Telegram user IDs are permanent numbers like `123456789`. They're different from your `@username`, which can change. Always use the numeric ID for allowlists.
:::

---

## Paso 3: Start the Gateway

### Quick Test

Run the gateway in the foreground first to make sure everything works:

```bash
hermes gateway
```

You should see output like:

```
[Gateway] Starting Hermes Gateway...
[Gateway] Telegram adapter connected
[Gateway] Cron scheduler started (tick every 60s)
```

Open Telegram, find your bot, and send it a message. If it replies, you're in business. Press `Ctrl+C` to stop.

### Production: Install as a Service

For a persistent deployment that survives reboots:

```bash
hermes gateway install
```

This creates a **systemd** service (Linux) or **launchd** service (macOS) that runs automatically.

```bash
# Linux — manage the service
hermes gateway start
hermes gateway stop
hermes gateway status

# View live logs
journalctl --user -u hermes-gateway -f

# Keep running after SSH logout
sudo loginctl enable-linger $USER
```

```bash
# macOS — manage the service
launchctl start ai.hermes.gateway
launchctl stop ai.hermes.gateway
tail -f ~/.hermes/logs/gateway.log
```

### Verify It's Running

```bash
hermes gateway status
```

Then send a test message to your bot on Telegram. You should get a response within a few seconds.

---

## Paso 4: Set Up Team Access

Now let's give your teammates access. There are two approaches.

### Approach A: Static Allowlist

Collect each team member's Telegram user ID (have them message [@userinfobot](https://t.me/userinfobot)) and add them as a comma-separated list:

```bash
# In ~/.hermes/.env
TELEGRAM_ALLOWED_USERS=123456789,987654321,555555555
```

Restart the gateway after changes:

```bash
hermes gateway stop && hermes gateway start
```

### Approach B: DM Pairing (Recommended for Teams)

DM pairing is more flexible — you don't need to collect user IDs upfront. Here's how it works:

1. **Teammate DMs the bot** — since they're not on the allowlist, the bot replies with a one-time pairing code:
   ```
   🔐 Pairing code: XKGH5N7P
   Send this code to the bot owner for approval.
   ```

2. **Teammate sends you the code** (via any channel — Slack, email, in person)

3. **You approve it** on the server:
   ```bash
   hermes pairing approve telegram XKGH5N7P
   ```

4. **They're in** — the bot immediately starts responding to their messages

**Managing paired users:**

```bash
# See all pending and approved users
hermes pairing list

# Revoke someone's access
hermes pairing revoke telegram 987654321

# Clear expired pending codes
hermes pairing clear-pending
```

:::tip
DM pairing is ideal for teams because you don't need to restart the gateway when adding new users. Approvals take effect immediately.
:::

### Seguridad Considerations

- **Never set `GATEWAY_ALLOW_ALL_USERS=true`** on a bot with terminal access — anyone who finds your bot could run commands on your server
- Pairing codes expire after **1 hour** and use cryptographic randomness
- Rate limiting prevents brute-force attacks: 1 request per user per 10 minutes, max 3 pending codes per platform
- After 5 failed approval attempts, the platform enters a 1-hour lockout
- All pairing data is stored with `chmod 0600` permissions

---

## Step 5: Configure the Bot

### Set a Home Channel

A **home channel** is where the bot delivers cron job results and proactive messages. Without one, scheduled tasks have nowhere to send output.

**Option 1:** Use the `/sethome` command in any Telegram group or chat where the bot is a member.

**Option 2:** Set it manually in `~/.hermes/.env`:

```bash
TELEGRAM_HOME_CHANNEL=-1001234567890
TELEGRAM_HOME_CHANNEL_NAME="Team Updates"
```

To find a channel ID, add [@userinfobot](https://t.me/userinfobot) to the group — it will report the group's chat ID.

### Configure Tool Progress Display

Control how much detail the bot shows when using tools. In `~/.hermes/config.yaml`:

```yaml
display:
  tool_progress: new    # off | new | all | verbose
```

| Mode | What You See |
|------|-------------|
| `off` | Clean responses only — no tool activity |
| `new` | Brief status for each new tool call (recommended for messaging) |
| `all` | Every tool call with details |
| `verbose` | Full tool output including command results |

Users can also change this per-session with the `/verbose` command in chat.

### Set Up a Personality with SOUL.md

Customize how the bot communicates by creating `~/.hermes/SOUL.md`:

```markdown
# Soul
You are a helpful team assistant. Be concise and technical.
Use code blocks for any code. Skip pleasantries — the team
values directness. When debugging, always ask for error logs
before guessing at solutions.
```

### Add Project Context

If your team works on specific projects, create context files so the bot knows your stack:

```markdown
<!-- ~/.hermes/AGENTS.md -->
# Team Context
- We use Python 3.12 with FastAPI and SQLAlchemy
- Frontend is React with TypeScript
- CI/CD runs on GitHub Actions
- Production deploys to AWS ECS
- Always suggest writing tests for new code
```

:::info
Context files are injected into every session's system prompt. Keep them concise — every character counts against your token budget.
:::

---

## Step 6: Set Up Scheduled Tasks

With the gateway running, you can schedule recurring tasks that deliver results to your team channel.

### Daily Standup Summary

Message the bot on Telegram:

```
Every weekday at 9am, check the GitHub repository at
github.com/myorg/myproject for:
1. Pull requests opened/merged in the last 24 hours
2. Issues created or closed
3. Any CI/CD failures on the main branch
Format as a brief standup-style summary.
```

The agent creates a cron job automatically and delivers results to the chat where you asked (or the home channel).

### Server Health Check

```
Every 6 hours, check disk usage with 'df -h', memory with 'free -h',
and Docker container status with 'docker ps'. Report anything unusual —
partitions above 80%, containers that have restarted, or high memory usage.
```

### Managing Scheduled Tasks

```bash
# From the CLI
hermes cron list          # View all scheduled jobs
hermes cron status        # Check if scheduler is running

# From Telegram chat
/cron list                # View jobs
/cron remove <job_id>     # Remove a job
```

:::warning
Cron job prompts run in completely fresh sessions with no memory of prior conversations. Make sure each prompt contains **all** the context the agent needs — file paths, URLs, server addresses, and clear instructions.
:::

---

## Production Tips

### Use Docker for Safety

On a shared team bot, use Docker as the terminal backend so agent commands run in a container instead of on your host:

```bash
# In ~/.hermes/.env
TERMINAL_BACKEND=docker
TERMINAL_DOCKER_IMAGE=nikolaik/python-nodejs:python3.11-nodejs20
```

Or in `~/.hermes/config.yaml`:

```yaml
terminal:
  backend: docker
  container_cpu: 1
  container_memory: 5120
  container_persistent: true
```

This way, even if someone asks the bot to run something destructive, your host system is protected.

### Monitor the Gateway

```bash
# Check if the gateway is running
hermes gateway status

# Watch live logs (Linux)
journalctl --user -u hermes-gateway -f

# Watch live logs (macOS)
tail -f ~/.hermes/logs/gateway.log
```

### Keep Hermes Updated

From Telegram, send `/update` to the bot — it will pull the latest version and restart. Or from the server:

```bash
hermes update
hermes gateway stop && hermes gateway start
```

### Log Locations

| What | Location |
|------|----------|
| Gateway logs | `journalctl --user -u hermes-gateway` (Linux) or `~/.hermes/logs/gateway.log` (macOS) |
| Cron job output | `~/.hermes/cron/output/{job_id}/{timestamp}.md` |
| Cron job definitions | `~/.hermes/cron/jobs.json` |
| Pairing data | `~/.hermes/pairing/` |
| Session history | `~/.hermes/sessions/` |

---

## Going Further

You've got a working team Telegram assistant. Here are some next steps:

- **[Seguridad Guide](/user-guide/security)** — deep dive into authorization, container isolation, and command approval
- **[Messaging Gateway](/user-guide/messaging)** — full reference for gateway architecture, session management, and chat commands
- **[Telegram Setup](/user-guide/messaging/telegram)** — platform-specific details including voice messages and TTS
- **[Scheduled Tasks](/user-guide/features/cron)** — advanced cron scheduling with delivery options and cron expressions
- **[Context Files](/user-guide/features/context-files)** — AGENTS.md, SOUL.md, and .cursorrules for project knowledge
- **[Personality](/user-guide/features/personality)** — built-in personality presets and custom persona definitions
- **Add more platforms** — the same gateway can simultaneously run [Discord](/user-guide/messaging/discord), [Slack](/user-guide/messaging/slack), and [WhatsApp](/user-guide/messaging/whatsapp)

---

*Questions or issues? Open an issue on GitHub — contributions are welcome.*
