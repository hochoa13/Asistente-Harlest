---
sidebar_position: 5
title: "Signal"
description: "Configuración de Signal — Mensajería privada con cifrado de extremo a extremo"
---

# Configuración de Signal

Signal es una aplicación de mensajería de código abierto con cifrado de extremo a extremo de forma predeterminada. Hermes se conecta a través de [signal-cli](https://github.com/AsamK/signal-cli/), un cliente sin interfaz gráfica que se ejecuta como daemon.

## Requisitos Previos

- **signal-cli** (Java 17 o superior)
- **Signal app** instalado en tu teléfono
- **Cuenta de Signal** vinculada a un número de teléfono

## Instalación

### Linux (apt)

```bash
sudo apt-get install default-jre
wget https://github.com/AsamK/signal-cli/releases/download/v0.13.10/signal-cli-0.13.10.tar.gz
tar xzf signal-cli-0.13.10.tar.gz
sudo mv signal-cli-0.13.10 /opt/signal-cli
sudo ln -s /opt/signal-cli/bin/signal-cli /usr/local/bin/signal-cli

# O usando Homebrew si está disponible:
brew install signal-cli
```

### macOS (Homebrew)

```bash
brew install signal-cli
```

### Docker (Alternativa)

```bash
docker pull bbernhard/signal-cli-rest-api:latest
docker run -d --name signal-cli \
  -p 8080:8080 \
  -v signal-cli-config:/home/signal-cli/.local/share/signal-cli \
  bbernhard/signal-cli-rest-api:latest
```

## Vinculación de Cuenta

### Opción 1: Código QR (Recomendado)

```bash
signal-cli --config ~/.signal-cli link --use-voice
# Aparecerá un código QR
# Abre Signal en tu teléfono → Ajustes → Dispositivos vinculados → Añadir dispositivo
# Escanea el código QR
```

### Opción 2: URI Manual

```bash
signal-cli --config ~/.signal-cli link --use-voice
# Proporciona un URI como: ts://XXXXXXXXXXX...
# Cópialo a `~/.signal-cli/config.json` en libsignal_encrypted.json
```

## Configuración de Hermes

### Opción 1: Asistente Interactivo

```bash
hermes gateway setup
# Selecciona Signal, proporciona el número de teléfono
```

### Opción 2: Manual .env

```bash
SIGNAL_PHONE_NUMBER="+15551234567"
SIGNAL_CLI_PATH="/usr/local/bin/signal-cli"    # Ruta opcional
SIGNAL_ALLOWED_USERS="+15559876543"            # Números autorizados
GATEWAY_ALLOW_ALL_USERS=false                  # Denegar por defecto
```

### Opción 3: Docker con REST API

```bash
SIGNAL_USE_REST_API=true
SIGNAL_REST_API_URL="http://localhost:8080"
SIGNAL_PHONE_NUMBER="+15551234567"
```

## Iniciando el Daemon

```bash
# Ejecución interactiva con logs:
signal-cli --config ~/.signal-cli daemon

# O en segundo plano con nohup:
nohup signal-cli --config ~/.signal-cli daemon > ~/.signal-cli/daemon.log 2>&1 &

# Verificar con:
ps aux | grep signal-cli
```

## Control de Acceso

### Permitir Números Específicos

```bash
SIGNAL_ALLOWED_USERS="+15551111111,+15552222222,+15553333333"
```

### Emparejamiento de MD

Si un número desconocido intenta contactar:

```bash
# Recibirá: "Código de emparejamiento: XKGH5N7P"
# Aprueba con:
hermes pairing approve signal XKGH5N7P
```

### Políticas de Grupo

Se pueden configurar políticas de aceptación de grupo en `~/.hermes/config.yaml`:

```yaml
gatewayPlatformSettings:
  signal:
    allowGroupRequests: true       # Aceptar invitaciones de grupo
    blockListedContacts: []        # Bloquear números específicos
```

## Características

### Archivos Adjuntos

Signal soporta:
- Imágenes (JPEG, PNG)
- Documentos (PDF, Office)
- Archivos (ZIP, TAR)

Los archivos se descargan a `~/.hermes/attachments/signal/`.

### Indicadores de Escritura

Los indicadores de escritura se envían automáticamente cuando el bot está escribiendo.

### Privacidad: Números Ocultos

En logs y salida, los números de teléfono se oscurecen automáticamente:
```
Mensaje de +155***4567
```

### Monitoreo de Salud

Signal-CLI se supervisa continuamente. Si falla, se reinicia automáticamente con backoff exponencial.

## Solución de Problemas

| Problema | Causa | Solución |
|----------|-------|----------|
| "command not found: signal-cli" | signal-cli no instalado | `which signal-cli` y reinstalar |
| "Link with URI has failed" | Formato URI incorrecto | Vuelve a ejecutar `signal-cli link --use-voice` |
| "Failed to decrypt message" | Problema de sincronización | Resincroniza el dispositivo: `signal-cli -c ~/.signal-cli daemon --verbose` |
| "No se envían mensajes" | Daemon no corriendo | Verifica: `ps aux \| grep signal-cli` |
| "Permission denied ~/.signal-cli" | Permisos de carpeta | `chmod 700 ~/.signal-cli` |
| Puerto 8080 en uso (Docker) | Conflicto de puerto | Usa `-p 8081:8080` en lugar de `-p 8080:8080` |
| "Unknown group" | Grupo no sincronizado | Envía un mensaje de grupo desde Signal app |
| Timeout en recepción | Red lenta/bloqueada | Aumenta `SIGNAL_POLL_INTERVAL` a 10000 ms |
| "Untrusted identity key" | Cambio de clave de identidad | Ejecuta `signal-cli -c ~/.signal-cli updateAccountIdentity` |

## Variables de Entorno

```bash
SIGNAL_PHONE_NUMBER          # Número de teléfono del bot (requerido, formato E.164 +15551234567)
SIGNAL_CLI_PATH              # Ruta a signal-cli (default: /usr/local/bin/signal-cli)
SIGNAL_USE_REST_API          # Usar REST API en lugar de daemon (true/false)
SIGNAL_REST_API_URL          # URL de REST API (ej. http://localhost:8080)
SIGNAL_ALLOWED_USERS         # Números autorizados separados por comas (ej. +15551111111,+15552222222)
SIGNAL_POLL_INTERVAL         # Intervalo de polling en ms (default: 5000)
SIGNAL_DATA_DIR              # Directorio de datos de signal-cli (default: ~/.signal-cli)
SIGNAL_REPLY_WITH_TEXT_QUOTE # Incluir cita de texto en respuestas (true/false)
```

## Seguridad

⚠️ **Advertencias Importantes:**

- **No compartas números de teléfono**: Los números vinculados a Hermes están expuestos en logs
- **Dedica un número**: Usa un número de teléfono separado para Hermes, no tu número personal
- **Protege `.signal-cli/`**: Los datos de cifrado se almacenan aquí
  ```bash
  chmod 700 ~/.signal-cli
  chmod 600 ~/.signal-cli/config.json
  ```
- **Rotación de contraseñas**: Si cambia tu contraseña Signal, actualiza la configuración
- **Salida de logs**: Los usuarios pueden ver mensajes en el registro con `/status`

## Siguiente Paso Recomendado

Lee sobre [Control de Acceso](../security.md) para configurar allowlists y emparejamiento.

Select **Signal** from the platform menu. The wizard will:

1. Check if signal-cli is installed
2. Prompt for the HTTP URL (default: `http://127.0.0.1:8080`)
3. Test connectivity to the daemon
4. Ask for your account phone number
5. Configure allowed usuarios and access policies

### Manual Configuración

Add to `~/.hermes/.env`:

```bash
# Required
SIGNAL_HTTP_URL=http://127.0.0.1:8080
SIGNAL_ACCOUNT=+1234567890

# Security (recommended)
SIGNAL_ALLOWED_USERS=+1234567890,+0987654321    # Comma-separated E.164 numbers or UUIDs

# Optional
SIGNAL_GROUP_ALLOWED_USERS=grupoId1,grupoId2     # Enable grupos (omit to disable, * for all)
SIGNAL_HOME_CHANNEL=+1234567890                  # Default delivery target for cron jobs
```

Then start the gateway:

```bash
hermes gateway              # Foreground
hermes gateway install      # Install as a system service
```

---

## Access Control

### DM Access

DM access follows the same pattern as all other Hermes platforms:

1. **`SIGNAL_ALLOWED_USERS` set** → only those usuarios can mensaje
2. **No allowlist set** → unknown usuarios get a DM pairing code (approve via `hermes pairing approve signal CODE`)
3. **`SIGNAL_ALLOW_ALL_USERS=true`** → anyone can mensaje (use with caution)

### Group Access

Group access is controlled by the `SIGNAL_GROUP_ALLOWED_USERS` env var:

| Configuración | Behavior |
|---------------|----------|
| Not set (default) | All grupo mensajes are ignored. The bot only responds to DMs. |
| Set with grupo IDs | Only listed grupos are monitored (e.g., `grupoId1,grupoId2`). |
| Set to `*` | The bot responds in any grupo it's a member of. |

---

## Features

### Attachments

The adapter supports enviaring and receiving:

- **Images** — PNG, JPEG, GIF, WebP (auto-detected via magic bytes)
- **Audio** — MP3, OGG, WAV, M4A (voice mensajes transcribed if Whisper is configuraciónured)
- **Documents** — PDF, ZIP, and other file types

Attachment size limit: **100 MB**.

### Typing Indicators

The bot enviars typing indicators while processing mensajes, refreshing every 8 seconds.

### Phone Number Redaction

All phone numbers are automatically redacted in logs:
- `+15551234567` → `+155****4567`
- This applies to both Hermes gateway logs and the global redaction system

### Health Monitoring

The adapter monitors the SSE connection and automatically reconnects if:
- The connection drops (with exponential backoff: 2s → 60s)
- No activity is detected for 120 seconds (pings signal-cli to verify)

---

## Solución de Problemas

| Problem | Solution |
|---------|----------|
| **"Cannot reach signal-cli"** during setup | Ensure signal-cli daemon is running: `signal-cli --account +YOUR_NUMBER daemon --http 127.0.0.1:8080` |
| **Messages not recibird** | Check that `SIGNAL_ALLOWED_USERS` includes the enviarer's number in E.164 format (with `+` prefix) |
| **"signal-cli not found on PATH"** | Install signal-cli and ensure it's in your PATH, or use Docker |
| **Connection keeps dropping** | Check signal-cli logs for errors. Ensure Java 17+ is installed. |
| **Group mensajes ignored** | `SIGNAL_GROUP_POLICY` defaults to `disabled`. Set to `allowlist` or `open`. |
| **Bot responds to everyone** | Set `SIGNAL_DM_POLICY=pairing` or `allowlist` and configuraciónure `SIGNAL_ALLOWED_USERS` |
| **Duplicate mensajes** | Ensure only one signal-cli instance is listening on your phone number |

---

## Security

:::warning
**Always configuraciónure access controls.** The bot has terminal access by default. Without `SIGNAL_ALLOWED_USERS` or DM pairing, the gateway denies all incoming mensajes as a safety measure.
:::

- Phone numbers are redacted in all log output
- Use `SIGNAL_DM_POLICY=pairing` (default) for safe onboarding of new usuarios
- Keep grupos disabled unless you specifically need grupo support
- Signal's end-to-end encryption protects mensaje content in transit
- The signal-cli session data in `~/.local/share/signal-cli/` contains account credentials — protect it like a password

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SIGNAL_HTTP_URL` | Yes | — | signal-cli HTTP endpoint |
| `SIGNAL_ACCOUNT` | Yes | — | Bot phone number (E.164) |
| `SIGNAL_ALLOWED_USERS` | No | — | Comma-separated phone numbers/UUIDs |
| `SIGNAL_GROUP_ALLOWED_USERS` | No | — | Group IDs to monitor, or `*` for all (omit to disable grupos) |
| `SIGNAL_HOME_CHANNEL` | No | — | Default delivery target for cron jobs |
