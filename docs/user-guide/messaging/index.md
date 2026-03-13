---
sidebar_position: 1
title: "Puerta de Enlace de Mensajería"
description: "Chatea con Hermes desde Telegram, Discord, Slack, WhatsApp, Signal o Email — descripción general de arquitectura y configuración"
---

# Puerta de Enlace de Mensajería

Chatea con Hermes desde Telegram, Discord, Slack, WhatsApp, Signal o Email. La puerta de enlace es un único proceso en segundo plano que se conecta a todas tus plataformas configuradas, gestiona sesiones, ejecuta trabajos cron y entrega mensajes de voz.

## Arquitectura

```text
┌─────────────────────────────────────────────────────────────────┐
│                   Puerta de Enlace Hermes                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ ┌────────┐ ┌───────┐│
│  │ Telegram │ │ Discord  │ │ WhatsApp │ │ Slack  │ │ Signal │ │ Email ││
│  │Adaptador │ │Adaptador │ │Adaptador │ │Adaptador│Adaptador│ │Adaptador││
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └───┬────┘ └───┬────┘ └──┬────┘│
│       │             │            │            │          │         │     │
│       └─────────────┼────────────┼────────────┼──────────┼─────────┘     │
│                           │                                     │
│                  ┌────────▼────────┐                            │
│                  │  Almacén de     │                            │
│                  │  Sesiones       │                            │
│                  │  (por chat)     │                            │
│                  └────────┬────────┘                            │
│                           │                                     │
│                  ┌────────▼────────┐                            │
│                  │   AIAgent       │                            │
│                  │   (run_agent)   │                            │
│                  └─────────────────┘                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

Cada adaptador de plataforma recibe mensajes, los enruta a través de un almacén de sesiones por chat y los envía al AIAgent para su procesamiento. La puerta de enlace también ejecuta el planificador cron, que se ejecuta cada 60 segundos para ejecutar cualquier trabajo que esté vencido.

## Configuración Rápida

La forma más fácil de configurar las plataformas de mensajería es el asistente interactivo:

```bash
hermes gateway setup        # Configuración interactiva para todas las plataformas de mensajería
```

Esto te guía a través de la configuración de cada plataforma con selección de teclas de dirección, muestra qué plataformas ya están configuradas y ofrece iniciar/reiniciar la puerta de enlace cuando hayas terminado.

## Comandos de la Puerta de Enlace

```bash
hermes gateway              # Ejecutar en primer plano
hermes gateway setup        # Configurar plataformas de mensajería interactivamente
hermes gateway install      # Instalar como servicio systemd (Linux) / launchd (macOS)
hermes gateway start        # Iniciar el servicio
hermes gateway stop         # Detener el servicio
hermes gateway status       # Comprobar el estado del servicio
```

## Comandos de Chat (Dentro de Mensajería)

| Comando | Descripción |
|---------|-------------|
| `/new` o `/reset` | Comienza una nueva conversación |
| `/model [provider:model]` | Mostrar o cambiar el modelo (admite sintaxis `provider:model`) |
| `/provider` | Mostrar proveedores disponibles con estado de autenticación |
| `/personality [name]` | Establecer una personalidad |
| `/retry` | Reintentar el último mensaje |
| `/undo` | Eliminar el último intercambio |
| `/status` | Mostrar información de la sesión |
| `/stop` | Detener el agente en ejecución |
| `/sethome` | Establecer este chat como canal principal |
| `/compress` | Comprimir manualmente el contexto de conversación |
| `/usage` | Mostrar uso de tokens para esta sesión |
| `/insights [days]` | Mostrar información de uso y análisis |
| `/reload-mcp` | Recargar servidores MCP desde la configuración |
| `/update` | Actualizar Hermes Agent a la versión más reciente |
| `/help` | Mostrar comandos disponibles |
| `/<skill-name>` | Invocar cualquier habilidad instalada |

## Gestión de Sesiones

### Persistencia de Sesiones

Las sesiones persisten a través de mensajes hasta que se restablecen. El agente recuerda el contexto de tu conversación.

### Políticas de Reinicio

Las sesiones se restablecen según políticas configurables:

| Política | Predeterminado | Descripción |
|----------|---------|-------------|
| Diaria | 4:00 AM | Reiniciar a una hora específica cada día |
| Inactiva | 120 min | Reiniciar después de N minutos de inactividad |
| Ambas | (combinadas) | La que se desencadene primero |

Configure per-platform overrides in `~/.hermes/gateway.json`:

```json
{
  "reset_by_platform": {
    "telegram": { "mode": "idle", "idle_minutes": 240 },
    "discord": { "mode": "idle", "idle_minutes": 60 }
  }
}
```

## Seguridad

**De forma predeterminada, la puerta de enlace deniega todos los usuarios que no estén en una lista blanca o emparejados mediante MD.** Este es el ajuste predeterminado seguro para un bot con acceso de terminal.

```bash
# Restringir a usuarios específicos (recomendado):
TELEGRAM_ALLOWED_USERS=123456789,987654321
DISCORD_ALLOWED_USERS=123456789012345678
SIGNAL_ALLOWED_USERS=+155****4567,+155****6543
EMAIL_ALLOWED_USERS=trusted@example.com,colleague@work.com

# O permitir
GATEWAY_ALLOWED_USERS=123456789,987654321

# O permitir explícitamente a todos los usuarios (NO recomendado para bots con acceso de terminal):
GATEWAY_ALLOW_ALL_USERS=true
```

### Emparejamiento de MD (Alternativa a Listas Blancas)

En lugar de configurar manualmente ID de usuarios, los usuarios desconocidos reciben un código de emparejamiento único cuando envían un MD al bot:

```bash
# El usuario ve: "Código de emparejamiento: XKGH5N7P"
# Los apruebas con:
hermes pairing approve telegram XKGH5N7P

# Otros comandos de emparejamiento:
hermes pairing list          # Ver usuarios pendientes + aprobados
hermes pairing revoke telegram 123456789  # Eliminar acceso
```

Los códigos de emparejamiento expiran después de 1 hora, están limitados en velocidad y utilizan aleatoriedad criptográfica.

## Interrumpiendo el Agente

Envía cualquier mensaje mientras el agente está trabajando para interrumpirlo. Comportamientos clave:

- **Los comandos de terminal en progreso se cierran inmediatamente** (SIGTERM, luego SIGKILL después de 1s)
- **Las llamadas de herramientas se cancelan** — solo se ejecuta la actualmente en ejecución, el resto se omiten
- **Múltiples mensajes se combinan** — los mensajes enviados durante la interrupción se unen en un solo aviso
- **Comando `/stop`** — interrumpe sin encolar un mensaje de seguimiento

## Notificaciones de Progreso de Herramientas

Controla cuánta actividad de herramientas se muestra en `~/.hermes/config.yaml`:

```yaml
display:
  tool_progress: all    # off | new | all | verbose
```

Cuando está habilitado, el bot envía mensajes de estado mientras funciona:

```text
💻 `ls -la`...
🔍 web_search...
📄 web_extract...
🐍 execute_code...
```

## Gestión de Servicios

### Linux (systemd)

```bash
hermes gateway install               # Instalar como servicio de usuario
systemctl --user start hermes-gateway
systemctl --user stop hermes-gateway
systemctl --user status hermes-gateway
journalctl --user -u hermes-gateway -f

# Habilitar lingering (mantiene la ejecución después del cierre de sesión)
sudo loginctl enable-linger $USER
```

### macOS (launchd)

```bash
hermes gateway install
launchctl start ai.hermes.gateway
launchctl stop ai.hermes.gateway
tail -f ~/.hermes/logs/gateway.log
```

## Conjuntos de Herramientas Específicos de Plataforma

Cada plataforma tiene su propio conjunto de herramientas:

| Plataforma | Conjunto de Herramientas | Capacidades |
|----------|---------|--------------|
| CLI | `hermes-cli` | Acceso completo |
| Telegram | `hermes-telegram` | Herramientas completas incluyendo terminal |
| Discord | `hermes-discord` | Herramientas completas incluyendo terminal |
| WhatsApp | `hermes-whatsapp` | Herramientas completas incluyendo terminal |
| Slack | `hermes-slack` | Herramientas completas incluyendo terminal |
| Signal | `hermes-signal` | Herramientas completas incluyendo terminal |
| Email | `hermes-email` | Herramientas completas incluyendo terminal |

## Próximos Pasos

- [Configuración de Telegram](telegram.md)
- [Configuración de Discord](discord.md)
- [Configuración de Slack](slack.md)
- [Configuración de WhatsApp](whatsapp.md)
- [Configuración de Signal](signal.md)
- [Configuración de Email](email.md)
