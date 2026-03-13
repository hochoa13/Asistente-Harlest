---
sidebar_position: 5
title: "Tareas Programadas (Cron)"
description: "Programa tareas automatizadas con lenguaje natural — trabajos cron, opciones de entrega y el programador de gateway"
---

# Tareas Programadas (Cron)

Programa tareas para ejecutarse automáticamente con lenguaje natural o expresiones Cron. El agente puede auto-programarse usando la herramienta `schedule_cronjob` desde cualquier plataforma.

## Creando Tareas Programadas

### En la CLI

Usa el comando slash `/cron`:

```
/cron add 30m "Remind me to check the build"
/cron add "every 2h" "Check server status"
/cron add "0 9 * * *" "Morning briefing"
/cron list
/cron remove <job_id>
```

### A Través de Conversación Natural

Simplemente pídele al agente en cualquier plataforma:

```
Every morning at 9am, check Hacker News for AI news and send me a summary on Telegram.
```

El agente usará la herramienta `schedule_cronjob` para configurarlo.

## Cómo Funciona

**La ejecución de cron es manejada por el daemon gateway.** El gateway marca el programador cada 60 segundos, ejecutando cualquier trabajo vencido en sesiones de agente aisladas:

```bash
hermes gateway install     # Instalar como servicio del sistema (recomendado)
hermes gateway             # O ejecutar en primer plano

hermes cron list           # Ver trabajos programados
hermes cron status         # Comprobar si el gateway se está ejecutando
```

### El Programador de Gateway

El programador se ejecuta como un thread de fondo dentro del proceso del gateway. En cada marca (cada 60 segundos):

1. Carga todos los trabajos desde `~/.hermes/cron/jobs.json`
2. Verifica cada `next_run_at` del trabajo habilitado contra la hora actual
3. Para cada trabajo vencido, genera una sesión `AIAgent` fresca con el indicador del trabajo
4. El agente se ejecuta hasta finalizar con acceso completo a herramientas
5. La respuesta final se entrega al destino configurado
6. El recuento de ejecución del trabajo se incrementa y se calcula el próximo tiempo de ejecución
7. Los trabajos que alcanzan su límite de repetición se auto-eliminan

Un **bloqueo basado en archivo** (`~/.hermes/cron/.tick.lock`) evita ejecución duplicada si múltiples procesos se superponen (p. ej., gateway + marca manual).

:::información
Aunque no se configuren plataformas de mensajería, el gateway se mantiene en ejecución para Cron. Un bloqueo de archivo evita ejecución duplicada si múltiples procesos se superponen.
:::

## Opciones de Entrega

Cuando programas trabajos, especificas dónde va la salida:

| Opción | Descripción | Ejemplo |
|--------|-------------|---------|
| `"origin"` | Back to where the job was created | Default on messaging platforms |
| `"local"` | Save to local files only (`~/.hermes/Cron/output/`) | Default on CLI |
| `"Telegram"` | Telegram home channel | Uses `TELEGRAM_HOME_CHANNEL` env var |
| `"Discord"` | Discord home channel | Uses `DISCORD_HOME_CHANNEL` env var |
| `"Telegram:123456"` | Specific Telegram chat by ID | For directing output to a specific chat |
| `"Discord:987654"` | Specific Discord channel by ID | For directing output to a specific channel |

**How `"origin"` works:** When a job is created from a messaging platform, Hermes records the source platform and chat ID. When the job runs and deliver is `"origin"`, the output is sent back to that exact platform and chat. If origin Información isn't available (e.g., job created from CLI), delivery falls back to local.

**How platform names work:** When you specify a bare platform name like `"Telegram"`, Hermes first checks if the job's origin matches that platform and uses the origin chat ID. Otherwise, it falls back to the platform's home channel configured via entorno variable (e.g., `TELEGRAM_HOME_CHANNEL`).

La respuesta final del agente se entrega autom\u00e1ticamente — **no** necesitas incluir `send_message` en el indicador de Cron.

El agente conoce tus plataformas conectadas y canales de inicio — elegirá defaults sensatos.

## Formatos de Programaci\u00f3n

### Retrasos Relativos (Una Sola Ejecución)

Ejecutar una vez después de un retraso:

```
30m     → Ejecutar una vez en 30 minutos
2h      → Ejecutar una vez en 2 horas
1d      → Ejecutar una vez en 1 día
```

Unidades soportadas: `m`/`min`/`minutes`, `h`/`hr`/`hours`, `d`/`day`/`days`.

### Intervalos (Recurrentes)

Ejecutar repetidamente en intervalos fijos:

```
every 30m    → Cada 30 minutos
every 2h     → Cada 2 horas
every 1d     → Cada día
```

### Expresiones Cron

Sintaxis cron estándar de 5 campos para programación precisa:

```
0 9 * * *       → Diariamente a las 9:00 AM
0 9 * * 1-5     → Días de semana a las 9:00 AM
0 */6 * * *     → Cada 6 horas
30 8 1 * *      → Primero de cada mes a las 8:30 AM
0 0 * * 0       → Cada domingo a medianoche
```

#### Hoja de Trucos de Expresiones Cron

```
┌───── minuto (0-59)
│ ┌───── hora (0-23)
│ │ ┌───── día del mes (1-31)
│ │ │ ┌───── mes (1-12)
│ │ │ │ ┌───── día de la semana (0-7, 0 y 7 = domingo)
│ │ │ │ │
* * * * *

Caracteres especiales:
  *     Cualquier valor
  ,     Separador de lista (1,3,5)
  -     Rango (1-5)
  /     Valores de paso (*/15 = cada 15)
```

:::nota
Las expresiones cron requieren el paquete Python `croniter`. Instala con `pip install croniter` si no está disponible ya.
:::

### Marcas de Tiempo ISO

Ejecutar una vez a una fecha/hora específica:

```
2026-03-15T09:00:00    → Una sola ejecución a las 9:00 AM del 15 de marzo de 2026
```

## Comportamiento de Repetición

El parámetro `repeat` controla cuántas veces se ejecuta un trabajo:

| Tipo de Programación | Repetición Predeterminada | Comportamiento |
|--------------|----------------|-------|
| Una sola ejecución (`30m`, timestamp) | 1 (Ejecutar una vez) | Se ejecuta una vez, luego auto-eliminado |
| Intervalo (`every 2h`) | Siempre (`null`) | Se ejecuta indefinidamente hasta eliminación |
| Expresión cron | Siempre (`null`) | Se ejecuta indefinidamente hasta eliminación |

Puedes anular el predeterminado:

```python
schedule_cronjob(
    prompt="...",
    schedule="every 2h",
    repeat=5  # Ejecutar exactamente 5 veces, luego auto-eliminar
)
```

Cuando un trabajo alcanza su límite de repetición, se elimina automáticamente de la lista de trabajos.

## Ejemplos del Mundo Real

### Reporte Diario de Standup

```
Programa un reporte de standup diario: Cada día de semana a las 9am, verifica el
repositorio de GitHub en github.com/myorg/myproject para:
1. Pull requests abiertos/fusionados en las últimas 24 horas
2. Issues creados o cerrados
3. Cualquier fallo de CI/CD en la rama principal
Formatea como un resumen estilo standup breve. Entrega a telegram.
```

El agente crea:
```python
schedule_cronjob(
    prompt="Check github.com/myorg/myproject for PRs, issues, and CI status from the last 24 hours. Format as a standup report.",
    schedule="0 9 * * 1-5",
    name="Daily Standup Report",
    deliver="telegram"
)
```

### Verificación de Copia de Seguridad Semanal

```
Cada domingo a las 2am, verifica que existan copias de seguridad en /data/backups/
each day of the past week. Check file sizes are > 1MB. Report any
gaps or suspiciously small files.
```

### Monitoring Alerts

```
Every 15 minutes, curl https://api.myservice.com/health and verify
it returns HTTP 200 with {"status": "ok"}. If it fails, include the
error details and response code. Deliver to telegram:123456789.
```

```python
schedule_cronjob(
    prompt="Run 'curl -s -o /dev/null -w \"%{http_code}\" https://api.myservice.com/health' and verify it returns 200. Also fetch the full response with 'curl -s https://api.myservice.com/health' and check for {\"status\": \"ok\"}. Report the result.",
    schedule="every 15m",
    name="API Health Check",
    deliver="telegram:123456789"
)
```

### Periodic Disk Uso Verificar

```python
schedule_cronjob(
    prompt="Check disk usage with 'df -h' and report any partitions above 80% usage. Also check Docker disk usage with 'docker system df' if Docker is installed.",
    schedule="0 8 * * *",
    name="Disk Uso Report",
    deliver="origin"
)
```

## Managing Jobs

```bash
# CLI commands
hermes cron list           # View all scheduled jobs
hermes cron status         # Check if the scheduler is running

# Slash commands (inside chat)
/cron list
/cron remove <job_id>
```

The agent can also manage jobs conversationally:
- `list_cronjobs` — Shows all jobs with IDs, schedules, repeat status, and next Ejecutar times
- `remove_cronjob` — Removes a job by ID (Usar `list_cronjobs` to find the ID)

## Job Storage

Jobs are stored as JSON in `~/.hermes/Cron/jobs.json`. Output from job runs is saved to `~/.hermes/Cron/output/{job_id}/{timestamp}.md`.

The storage uses atomic archivo writes (temp archivo + rename) to prevent corruption from concurrent access.

## Self-Contained Prompts

:::Advertencia Importante
Cron job prompts Ejecutar in a **completely fresh agent session** with zero Memoria of any prior conversation. The prompt must contain **everything** the agent needs:

- Full context and background
- Specific archivo paths, URLs, server addresses
- Clear instructions and success criteria
- Any credenciales or Configuración details

**BAD:** `"Verificar on that server issue"`
**GOOD:** `"ssh into server 192.168.1.100 as user 'deploy', Verificar if nginx is running with 'systemctl status nginx', and verify https://Ejemplo.com returns HTTP 200."`
:::

## Security

:::Advertencia
Scheduled task prompts are scanned for instruction-override patterns (prompt injection). Jobs matching threat patterns like credential exfiltration, ssh backdoor attempts, or prompt injection are blocked at creation time. Content with invisible Unicode characters (zero-width spaces, directional overrides) is also rejected.
:::
