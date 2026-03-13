---
sidebar_position: 8
title: "Seguridad"
description: "Modelo de seguridad, aprobación de comandos peligrosos, autorización de usuarios, aislamiento de contenedores y mejores prácticas de implementación en producción"
---

# Seguridad

Hermes Agent está diseñado con un modelo de seguridad de defensa en profundidad. Esta página cubre cada límite de seguridad — desde aprobación de comandos hasta aislamiento de contenedores hasta autorización de usuarios en plataformas de mensajería.

## Descripción General

El modelo de seguridad tiene cinco capas:

1. **Autorización de usuario** — quién puede hablar con el agente (listas blancas, emparejamiento de MD)
2. **Aprobación de comandos peligrosos** — intervención humana para operaciones destructivas
3. **Aislamiento de contenedor** — aislamiento de Docker/Singularity/Modal con configuración endurecida
4. **Filtrado de credenciales MCP** — aislamiento de variables de entorno para subprocesos MCP
5. **Escaneo de archivos de contexto** — detección de inyección de indicación en archivos de proyecto

## Aprobación de comandos peligrosos

Antes de ejecutar cualquier comando, Hermes lo verifica contra una lista curada de patrones peligrosos. Si se encuentra una coincidencia, el usuario debe aprobarlo explícitamente.

### Qué desencadena la aprobación

Los siguientes patrones desencadenan avisos de aprobación (definidos en `tools/approval.py`):

| Patrón | Descripción |
|---------|-------------|
| `rm -r` / `rm --recursive` | Eliminación recursiva |
| `rm ... /` | Eliminar en ruta raíz |
| `chmod 777` | Permisos grabables por todo el mundo |
| `mkfs` | Formatear sistema de archivos |
| `dd if=` | Copia de disco |
| `DROP TABLE/DATABASE` | SQL DROP |
| `DELETE FROM` (sin WHERE) | SQL DELETE sin WHERE |
| `TRUNCATE TABLE` | SQL TRUNCATE |
| `> /etc/` | Sobrescribir configuración del sistema |
| `systemctl stop/disable/mask` | Detener/deshabilitar servicios del sistema |
| `kill -9 -1` | Matar todos los procesos |
| `curl ... \| sh` | Conducir contenido remoto a shell |
| `bash -c`, `python -e` | Ejecución de shell/script vía banderas |
| `find -exec rm`, `find -delete` | Buscar con acciones destructivas |
| Patrones de bomba de tenedor | Bombas de tenedor |

:::info
**Omisión de contenedor**: Al ejecutar en backends `docker`, `singularity`, `modal` o `daytona`, las verificaciones de comandos peligrosos se **omiten** porque el contenedor en sí es el límite de seguridad. Los comandos destructivos dentro de un contenedor no pueden dañar al host.
:::

### Flujo de aprobación (CLI)

En la CLI interactiva, los comandos peligrosos muestran un mensaje de aprobación en línea:

```
  ⚠️  COMANDO PELIGROSO: eliminación recursiva
      rm -rf /tmp/old-project

      [u]na vez  |  [s]esión  |  [s]iempre  |  [b]loquear

      Opción [u/s/s/B]:
```

Las cuatro opciones:

- **una vez** — permitir esta ejecución única
- **sesión** — permitir este patrón para el resto de la sesión
- **siempre** — agregar a la lista blanca permanente (guardada en `config.yaml`)
- **bloquear** (por defecto) — bloquear el comando

### Flujo de aprobación (Puerta de enlace/Mensajería)

En plataformas de mensajería, el agente envía los detalles del comando peligroso al chat y espera que el usuario responda:

- Responda **sí**, **y**, **apruebo**, **ok** o **adelante** para aprobar
- Responda **no**, **n**, **niego** o **cancelar** para negar

La variable de entorno `HERMES_EXEC_ASK=1` se establece automáticamente cuando se ejecuta la puerta de enlace.

### Lista blanca permanente

Los comandos aprobados con "siempre" se guardan en `~/.hermes/config.yaml`:

```yaml
# Patrones de comandos peligrosos permitidos permanentemente
command_allowlist:
  - rm
  - systemctl
```

Estos patrones se cargan al iniciarse y se aprueban silenciosamente en todas las sesiones futuras.

:::tip
Use `hermes config edit` para revisar o eliminar patrones de su lista blanca permanente.
:::

## Autorización de usuario (Puerta de enlace)

Al ejecutar la puerta de enlace de mensajería, Hermes controla quién puede interactuar con el bot a través de un sistema de autorización en capas.

### Orden de verificación de autorización

El método `_is_user_authorized()` verifica en este orden:

1. **Bandera permitir todo por plataforma** (p. ej., `DISCORD_ALLOW_ALL_USERS=true`)
2. **Lista aprobada de emparejamiento de MD** (usuarios aprobados vía códigos de emparejamiento)
3. **Listas blancas específicas de plataforma** (p. ej., `TELEGRAM_ALLOWED_USERS=12345,67890`)
4. **Lista blanca global** (`GATEWAY_ALLOWED_USERS=12345,67890`)
5. **Permitir todo global** (`GATEWAY_ALLOW_ALL_USERS=true`)
6. **Predeterminado: negar**

### Listas blancas de plataforma

Establezca las ID de usuario permitidas como valores separados por comas en `~/.hermes/.env`:

```bash
# Listas blancas específicas de plataforma
TELEGRAM_ALLOWED_USERS=123456789,987654321
DISCORD_ALLOWED_USERS=111222333444555666
WHATSAPP_ALLOWED_USERS=15551234567
SLACK_ALLOWED_USERS=U01ABC123

# Lista blanca entre plataformas (verificada para todas las plataformas)
GATEWAY_ALLOWED_USERS=123456789

# Permitir todo por plataforma (usar con cuidado)
DISCORD_ALLOW_ALL_USERS=true

# Permitir todo global (usar con extrema precaución)
GATEWAY_ALLOW_ALL_USERS=true
```

:::warning
Si **no se configuran listas blancas** y `GATEWAY_ALLOW_ALL_USERS` no está establecido, **todos los usuarios se niegan**. La puerta de enlace registra una advertencia al iniciar:

```
No se han configurado listas blancas de usuario. Se negarán todos los usuarios no autorizados.
Establezca GATEWAY_ALLOW_ALL_USERS=true en ~/.hermes/.env para permitir acceso abierto,
o configure listas blancas de plataforma (p. ej., TELEGRAM_ALLOWED_USERS=su_id).
```
:::

### DM Pairing System

For more flexible authorization, Hermes includes a code-based pairing system. Instead of requiring user IDs upfront, unknown users receive a one-time pairing code that the bot owner approves via the CLI.

**How it works:**

1. An unknown user sends a DM to the bot
2. The bot replies with an 8-character pairing code
3. The bot owner runs `hermes pairing approve <platform> <code>` on the CLI
4. The user is permanently approved for that platform

**Security features** (based on OWASP + NIST SP 800-63-4 guidance):

| Feature | Details |
|---------|---------|
| Code format | 8-char from 32-char unambiguous alphabet (no 0/O/1/I) |
| Randomness | Cryptographic (`secrets.choice()`) |
| Code TTL | 1 hour expiry |
| Rate limiting | 1 request per user per 10 minutes |
| Pending limit | Max 3 pending codes per platform |
| Lockout | 5 failed approval attempts → 1-hour lockout |
| File security | `chmod 0600` on all pairing data files |
| Logging | Codes are never logged to stdout |

**Comandos CLI de emparejamiento:**

```bash
# Listar usuarios pendientes y aprobados
hermes pairing list

# Aprobar un código de emparejamiento
hermes pairing approve telegram ABC12DEF

# Revocar acceso de un usuario
hermes pairing revoke telegram 123456789

# Limpiar todos los códigos pendientes
hermes pairing clear-pending
```

**Almacenamiento:** Los datos de emparejamiento se almacenan en `~/.hermes/pairing/` con archivos JSON por plataforma:
- `{plataforma}-pending.json` — solicitudes de emparejamiento pendientes
- `{plataforma}-approved.json` — usuarios aprobados
- `_rate_limits.json` — rastreo de límite de velocidad y bloqueo

## Aislamiento de contenedor

Cuando se usa el backend de terminal `docker`, Hermes aplica un endurecimiento de seguridad estricto a cada contenedor.

### Banderas de seguridad de Docker

Cada contenedor se ejecuta con estas banderas (definidas en `tools/environments/docker.py`):

```python
_SECURITY_ARGS = [
    "--cap-drop", "ALL",                          # Soltar TODAS las capacidades de Linux
    "--security-opt", "no-new-privileges",         # Bloquear escalada de privilegios
    "--pids-limit", "256",                         # Limitar recuento de procesos
    "--tmpfs", "/tmp:rw,nosuid,size=512m",         # /tmp de tamaño limitado
    "--tmpfs", "/var/tmp:rw,noexec,nosuid,size=256m",  # /var/tmp sin ejecución
    "--tmpfs", "/run:rw,noexec,nosuid,size=64m",   # /run sin ejecución
]
```

### Límites de recursos

Los recursos del contenedor se configuran en `~/.hermes/config.yaml`:

```yaml
terminal:
  backend: docker
  docker_image: "nikolaik/python-nodejs:python3.11-nodejs20"
  container_cpu: 1        # N\u00facleo de CPU
  container_memory: 5120  # MB (predeterminado 5GB)
  container_disk: 51200   # MB (predeterminado 50GB, requiere overlay2 en XFS)
  container_persistent: true  # Persistir sistema de archivos entre sesiones
```

### Persistencia del sistema de archivos

- **Modo persistente** (`container_persistent: true`): Bind-monta `/workspace` y `/root` desde `~/.hermes/sandboxes/docker/<task_id>/`
- **Modo ef\u00edmero** (`container_persistent: false`): Usa tmpfs para espacio de trabajo \u2014 todo se pierde al limpiar

:::tip
Para implementaciones de puerta de enlace en producci\u00f3n, use el backend `docker`, `modal` o `daytona` para aislar los comandos del agente de su sistema anfitri\u00f3n. Esto elimina la necesidad de aprobaci\u00f3n de comandos peligrosos.\n:::

## Comparaci\u00f3n de seguridad del backend de terminal

| Backend | Aislamiento | Verificaci\u00f3n de comando peligroso | Mejor para |\n|---------|-----------|-------------------|----------|\n| **local** | Ninguno \u2014 se ejecuta en anfitri\u00f3n | \u2705 S\u00ed | Desarrollo, usuarios de confianza |\n| **ssh** | M\u00e1quina remota | \u2705 S\u00ed | Ejecutar en un servidor separado |\n| **docker** | Contenedor | \u274c Omitido (contenedor es l\u00edmite) | Puerta de enlace de producci\u00f3n |\n| **singularity** | Contenedor | \u274c Omitido | Entornos HPC |\n| **modal** | Arena de nube | \u274c Omitido | Aislamiento de nube escalable |\n| **daytona** | Arena de nube | \u274c Omitido | Espacios de trabajo en la nube persistentes |

## Manejo de credenciales MCP

Los subprocesos del servidor MCP (Protocolo de Contexto de Modelo) reciben un **entorno filtrado** para prevenir filtración accidental de credenciales.

### Variables de entorno seguras

Solo estas variables se pasan del anfitrión a los subprocesos stdio MCP:

```
PATH, HOME, USER, LANG, LC_ALL, TERM, SHELL, TMPDIR
```

Más cualquier variable `XDG_*`. Todas las otras variables de entorno (claves API, tokens, secretos) se **eliminan**.

Las variables definidas explícitamente en la configuración `env` del servidor MCP se pasan a través:

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_..."  # Solo esto se pasa
```

### Redacción de credenciales

Los mensajes de error de herramientas MCP se desinfectan antes de devolverse al LLM. Los siguientes patrones se reemplazan con `[REDACTADO]`:

- PAT de GitHub (`ghp_...`)
- Claves de estilo OpenAI (`sk-...`)
- Tokens de portador
- Parámetros `token=`, `key=`, `API_KEY=`, `password=`, `secret=`

### Protección contra inyección de archivos de contexto

Los archivos de contexto (AGENTS.md, .cursorrules, SOUL.md) se escanean para detectar inyección de indicación antes de incluirse en el mensaje del sistema. El escáner comprueba:

- Instrucciones para ignorar/desatender instrucciones previas
- Comentarios HTML ocultos con palabras clave sospechosas
- Intentos de leer secretos (`.env`, `credentials`, `.netrc`)
- Exfiltración de credenciales vía `curl`
- Caracteres Unicode invisibles (espacios de ancho cero, anulaciones bidireccionales)

Los archivos bloqueados muestran una advertencia:

```
[BLOQUEADO: AGENTS.md contenía potencial inyección de indicación (prompt_injection). Contenido no cargado.]
```

## Mejores prácticas para implementación en producción

### Lista de verificación de implementación de puerta de enlace

1. **Establecer listas blancas explícitas** — nunca use `GATEWAY_ALLOW_ALL_USERS=true` en producción
2. **Usar backend de contenedor** — establezca `terminal.backend: docker` en config.yaml
3. **Restringir límites de recursos** — establezca límites apropiados de CPU, memoria y disco
4. **Almacenar secretos de forma segura** — mantenga claves API en `~/.hermes/.env` con permisos de archivo adecuados
5. **Habilitar emparejamiento de MD** — use códigos de emparejamiento en lugar de codificar ID de usuario
6. **Revisar lista blanca de comandos** — auditar periódicamente `command_allowlist` en config.yaml
7. **Establecer `MESSAGING_CWD`** — no dejes que el agente opere desde directorios sensibles
8. **Ejecutar como no root** — nunca ejecute la puerta de enlace como root
9. **Monitorear registros** — verifique `~/.hermes/logs/` para intentos de acceso no autorizados
10. **Mantenerse actualizado** — ejecute `hermes update` regularmente para parches de seguridad

### Aseguramiento de claves API

```bash
# Establecer permisos apropiados en el archivo .env
chmod 600 ~/.hermes/.env

# Mantener claves separadas para diferentes servicios
# Nunca confirmar archivos .env al control de versiones
```

### Aislamiento de red

Para máxima seguridad, ejecute la puerta de enlace en una máquina o VM separada:

```yaml
terminal:
  backend: ssh
  ssh_host: "agent-worker.local"
  ssh_user: "hermes"
  ssh_key: "~/.ssh/hermes_agent_key"
```

Esto mantiene las conexiones de mensajería de la puerta de enlace separadas de la ejecución de comandos del agente.
