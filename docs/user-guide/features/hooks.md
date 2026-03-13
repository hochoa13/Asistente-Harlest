---
sidebar_position: 6
title: "Event Ganchos"
description: "Ejecutar custom code at key lifecycle points — log activity, send alerts, post to webhooks"
---

# Event Ganchos

The Ganchos system lets you Ejecutar custom code at key points in the agent lifecycle — session creation, slash commands, each herramienta-calling step, and more. Ganchos fire automatically during gateway operation without blocking the main agent tubería.

## Creating a Hook

Each hook is a directorio under `~/.hermes/Ganchos/` containing two files:

```
~/.hermes/hooks/
└── my-hook/
    ├── HOOK.yaml      # Declares which events to listen for
    └── handler.py     # Python handler function
```

### HOOK.yaml

```yaml
name: my-hook
description: Log all agent activity to a file
events:
  - agent:start
  - agent:end
  - agent:step
```

La lista `events` determina qué eventos disparan tu manejador. Puedes suscribirte a cualquier combinación de eventos, incluyendo comodines como `command:*`.

### handler.py

```python
import json
from datetime import datetime
from pathlib import Path

LOG_FILE = Path.home() / ".hermes" / "hooks" / "my-hook" / "activity.log"

async def handle(event_type: str, context: dict):
    """Called for each subscribed event. Must be named 'handle'."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event": event_type,
        **context,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
```

**Reglas del manejador:**
- Debe ser nombrado `handle`
- Recibe `event_type` (string) y `context` (dict)
- Puede ser `async def` o `def` regular — ambos funcionan
- Los errores se capturan y registran, nunca bloqueando el agente

## Eventos Disponibles

| Evento | Cuándo se dispara | Claves de contexto |
|-------|---------------|--------------|
| `gateway:startup` | El proceso del gateway inicial iza | `platforms` (lista de nombres de plataforma activos) |
| `session:start` | Nueva sesión de mensajería creada | `platform`, `user_id`, `session_id`, `session_key` |
| `session:reset` | El usuario ejecutó `/new` o `/reset` | `platform`, `user_id`, `session_key` |
| `agent:start` | El agente comienza a procesar un mensaje | `platform`, `user_id`, `session_id`, `message` |
| `agent:step` | Cada iteración del bucle de llamada de herramientas | `platform`, `user_id`, `session_id`, `iteration`, `tool_names` |
| `agent:end` | El agente termina de procesar | `platform`, `user_id`, `session_id`, `message`, `response` |
| `command:*` | Cualquier comando slash ejecutado | `platform`, `user_id`, `command`, `args` |

### Coincidencia de Comodín

Los manejadores registrados para `command:*` se disparan para cualquier evento `command:` (`command:model`, `command:reset`, etc.). Monitorea todos los comandos slash con una sola suscripción.

## Ejemplos

### Alerta de Telegram en Tareas Largas

Send yourself a message when the agent takes more than 10 steps:

```yaml
# ~/.hermes/hooks/long-task-alert/HOOK.yaml
name: long-task-alert
description: Alert when agent is taking many steps
events:
  - agent:step
```

```python
# ~/.hermes/hooks/long-task-alert/handler.py
import os
import httpx

THRESHOLD = 10
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_HOME_CHANNEL")

async def handle(event_type: str, context: dict):
    iteration = context.get("iteration", 0)
    if iteration == THRESHOLD and BOT_TOKEN and CHAT_ID:
        tools = ", ".join(context.get("tool_names", []))
        text = f"⚠️ Agent has been running for {iteration} steps. Last tools: {tools}"
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": CHAT_ID, "text": text},
            )
```

### comando Uso Logger

Rastrea qué comandos slash se usan:

```yaml
# ~/.hermes/hooks/command-logger/HOOK.yaml
name: command-logger
description: Log slash command usage
events:
  - command:*
```

```python
# ~/.hermes/hooks/command-logger/handler.py
import json
from datetime import datetime
from pathlib import Path

LOG = Path.home() / ".hermes" / "logs" / "command_usage.jsonl"

def handle(event_type: str, context: dict):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now().isoformat(),
        "command": context.get("command"),
        "args": context.get("args"),
        "platform": context.get("platform"),
        "user": context.get("user_id"),
    }
    with open(LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
```

### Webhook de Inicio de Sesión

POST a un servicio externo en nuevas sesiones:

```yaml
# ~/.hermes/hooks/session-webhook/HOOK.yaml
name: session-webhook
description: Notify external service on new sessions
events:
  - session:start
  - session:reset
```

```python
# ~/.hermes/hooks/session-webhook/handler.py
import httpx

WEBHOOK_URL = "https://your-service.example.com/hermes-events"

async def handle(event_type: str, context: dict):
    async with httpx.AsyncClient() as client:
        await client.post(WEBHOOK_URL, json={
            "event": event_type,
            **context,
        }, timeout=5)
```

## Cómo Funciona

1. Al inicio del gateway, `HookRegistry.discover_and_load()` escanea `~/.hermes/hooks/`
2. Cada subdirectorio con `HOOK.yaml` + `handler.py` se carga dinámicamente
3. Los manejadores se registran para sus eventos declarados
4. En cada punto del ciclo de vida, `hooks.emit()` dispara todos los manejadores coincidentes
5. Los errores en cualquier manejador se capturan y registran — un gancho roto nunca bloquea el agente

:::información
Los ganchos solo se disparan en el **gateway** (Telegram, Discord, Slack, WhatsApp). La CLI actualmente no carga ganchos.
:::
