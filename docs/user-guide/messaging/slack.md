---
sidebar_position: 4
title: "Slack"
description: "Configura Hermes Agent como un bot Slack"
---

# Configuración de Slack

Hermes Agent se integra con Slack usando **Modo Socket**, un protocolo moderno basado en WebSocket que no requiere que expongas una URL pública. El bot recibe mensajes, los procesa a través de Hermes Agent (incluyendo uso de herramientas, memoria y razonamiento), y responde en tiempo real.

## Descripción General

| Componente | Detalles |
|-----------|----------|
| **Framework** | Bolt para Python (socket-mode-sync) |
| **Conexión** | Socket Mode (WebSocket, no se necesita URL pública) |
| **Tipo de Token** | `xoxb-` (token de bot) y `xapp-` (token de aplicación) |
| **Scopes Requeridos** | chat:write, app_mentions:read, channels:history, groups:history, im:history, im:read, im:write, users:read, files:write |
| **Eventos Requeridos** | message.im, message.channels, message.groups, app_mention |
| **Autenticación de Usuario** | Member IDs (xmppuser.slack.com) |

:::warning[RTM API Deprecation — Migración Requerida]
El **Trading Real-Time Messaging (RTM) API** será **descontinuado el 11 de marzo de 2025**. Todas las nuevas aplicaciones Slack deben usar **Socket Mode o el API de eventos**. Si tienes una aplicación Slack existente usando RTM, necesitarás migrar a Socket Mode (la opción más fácil) o al API de eventos de suscripción. Esta guía cubre Socket Mode, que es el método recomendado.
:::

## Paso 1: Crear una Aplicación Slack

1. Ve a [api.slack.com/apps](https://api.slack.com/apps)
2. Haz clic en **Create New App**
3. Elige **From scratch**
4. Ingresa un nombre para la aplicación (p. ej., "Hermes Agent")
5. Selecciona tu espacio de trabajo Slack
6. Haz clic en **Create App**

Serás llevado a la página **App Configuration** (Configuración de Aplicación).

## Paso 2: Configurar Ámbitos del Token del Bot

Los "scopes" definen qué capacidades tiene tu bot.

1. En la barra lateral izquierda, haz clic en **OAuth & Permissions**
2. Desplázate a **Scopes** → **Bot Token Scopes**
3. Haz clic en **Add an OAuth Scope** y añade cada uno de estos:

| Scope | Propósito |
|-------|-----------|
| `chat:write` | Enviar mensajes |
| `app_mentions:read` | Leer menciones @bot |
| `channels:history` | Leer historial de canales públicos |
| `groups:history` | Leer historial de canales privados |
| `im:history` | Leer historial de mensajes directos |
| `im:read` | Leer mensajes directos |
| `im:write` | Enviar mensajes directos |
| `users:read` | Leer información de usuarios |
| `files:write` | Cargar archivos e imágenes |

Cuando hayas añadido todos los scopes, desplázate hacia abajo para el siguiente paso.

## Paso 3: Habilitar Modo Socket

El Modo Socket permite que tu bot se conecte a través de una conexión WebSocket segura, eliminando la necesidad de exponer un servidor web público.

1. En la barra lateral izquierda, haz clic en **Socket Mode**
2. Alterna el switch **Enable Socket Mode** a **ACTIVADO**
3. Slack te marcará: "Has habilitado exitosamente el Modo Socket para tu aplicación."

Cuando habilitas Modo Socket, Slack automáticamente añade el scope `connections:write` a tu token de bot. Esto es necesario para que la conexión WebSocket funcione.

:::tip[¿Dónde está el archivo de certificado?]
A diferencia de las conexiones HTTP, Socket Mode no requiere archivos de certificado SSL/TLS. Tu cliente simplemente se conecta a `wss://wss-primary.slack.com` usando el socket mode framework (Bolt).
:::

## Paso 4: Suscribirse a Eventos

Tu bot necesita estar suscrito a tipos de eventos específicos para recibir mensajes.

1. En la barra lateral izquierda, haz clic en **Event Subscriptions**
2. Alterna el switch **Enable Events** a **ACTIVADO**
3. Slack mostrará una sección **Socket Mode** (ya que acabas de habilitar Socket Mode)
4. Bajo **Subscribe to bot events**, haz clic en **Add Bot User Event** y añade estos cuatro eventos (en orden):

| Evento | Propósito |
|-------|-----------|
| `message.im` | Mensajes directos al bot |
| `message.channels` | Mensajes en canales públicos |
| `message.groups` | Mensajes en canales privados |
| `app_mention` | Menciones @bot |

Estos cuatro eventos son **críticos** — sin ellos, tu bot nunca recibirá mensajes.

5. Haz clic en **Save Event Subscriptions**

## Paso 5: Instalar Aplicación en Espacio de Trabajo

1. En la barra lateral izquierda, haz clic en **Install App**
2. Bajo **Acciones**, haz clic en **Install to Workspace**
3. Te redirigirá a una pantalla de permisos. Revisa los permisos listados (los que configuraste en el Paso 2)
4. Haz clic en **Allow**

Slack te redirigirá de vuelta a la página de instalación. Verás el **Bot User OAuth Token** (comienza con `xoxb-`). **Cópialo y guárdalo en un lugar seguro** — lo necesitarás pronto.

:::warning[Token Mostrado Una Sola Vez]
Si saldas de la página sin copiar el token, necesitarás:
1. Ir a **OAuth & Permissions** en la barra lateral
2. Desplázate a **Bot User OAuth Token**
3. Haz clic en **Refresh Token** para generar uno nuevo
:::

## Paso 6: Encontrar IDs de Usuario para la Lista de Permitidos

Hermes Agent usa Member IDs de Slack para controlar quién puede usar el bot.

1. En Slack, abre tu perfil haciendo clic en tu foto de perfil
2. Haz clic en **Perfil**
3. Haz clic en los tres puntos (...) en la esquina superior derecha
4. Haz clic en **Copiar ID de Miembro**

Tu member ID se verá algo como `U035AXBCD1F`. (Si ves un formato de email como `xmppuser.slack.com`, eras en la página equivocada — haz clic en **Perfil** desde el menú de perfil.)

Repite esto para cualquier usuario que desees permitir.

## Paso 7: Configurar Hermes

### Opción A: Configuración Interactiva (Recomendado)

Ejecuta el comando de configuración guiado:

```bash
hermes gateway setup
```

Selecciona **Slack** cuando se te solicite, luego proporciona:
- Tu **Bot User OAuth Token** (xoxb-...)
- Tu **Member ID** (U...)

### Opción B: Configuración Manual

Añade lo siguiente a tu archivo `~/.hermes/.env`:

```bash
# Requerido
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_ALLOWED_USERS=U035AXBCD1F

# Múltiples usuarios permitidos (separados por comas)
# SLACK_ALLOWED_USERS=U035AXBCD1F,U024XYZABC9

# Opcional: canal principal
# SLACK_HOME_CHANNEL=C12345ABCDE
```

### Iniciar la Puerta de Enlace

Una vez configurado:

```bash
hermes gateway
```

El bot debe estar en línea en Slack en segundos. Envíale un DM para probar.

## Paso 8: Invitar el Bot a Canales

Ahora necesitas invitar el bot a los canales donde deseas que responda.

1. En Slack, abre un canal
2. En la barra lateral derecha, ve a la pestaña **Miembros** o **Info del Canal**
3. Haz clic en **Añadir personas** o el botón **+**
4. Busca **Hermes Agent** (o el nombre de tu bot) y haz clic para añadirlo

Repite esto para cada canal donde desees que el bot responda.

## Cómo Responde el Bot

- **Canales públicos/privados**: El bot responde a todos los mensajes de usuarios permitidos, **SIN** requerir una mención o prefijo. Simplemente escribe un mensaje en un canal donde el bot esté presente.
- **Mensajes directos**: Los DMs siempre funcionan si el usuario está en `SLACK_ALLOWED_USERS`.
- **Hilos**: Si un usuario inicia un hilo, el bot responderá en ese hilo.

## Canal Principal

Puedes designar un "canal principal" donde el bot envía notificaciones, recordatorios y otros mensajes proactivos.

### Usando el Comando de Barra

Escribe `/sethome` en Slack dentro del canal que desees establecer como principal.

### Configuración Manual

Encuentra el ID del canal deseado:

1. En Slack, abre el canal
2. Haz clic en el nombre del canal en la parte superior
3. En el panel de detalles a la derecha, busca **Canal ID** (algo como `C12345ABCDE`)
4. Cópialo

Luego añade a tu `~/.hermes/.env`:

```bash
SLACK_HOME_CHANNEL=C12345ABCDE
```

## Mensajes de Voz

Hermes Agent admite mensajes de voz en Slack:

- **Entrada**: Las grabaciones de voz de Slack se transcriben automáticamente usando Whisper (requiere `VOICE_TOOLS_OPENAI_KEY`)
- **Salida**: Las respuestas pueden incluir transcripción de voz o archivos de audios usando formato MP3

## Solución de Problemas

### El bot no responde a mensajes de canal

**Causa Más Probable**: Los eventos no están suscritos correctamente o el bot no está invitado al canal.

| Problema | Solución |
|----------|----------|
| Bot no invitado a canal | Invita el bot al canal (Paso 8) — búscalo en la lista de personas del canal e invítalo |
| Eventos no suscritos | Ve a Event Subscriptions en la configuración de la aplicación y confirma que `message.channels`, `message.groups`, `message.im` y `app_mention` están listados bajo "Subscribe to bot events" |
| Scope incompleto | Asegúrate de que `chat:write`, `channels:history`, `groups:history`, e `im:history` están listados bajo **Bot Token Scopes** en OAuth & Permissions |
| Modo Socket deshabilitado | Ve a **Socket Mode** en la configuración de la aplicación y confirma que está toggled **ACTIVADO** |
| Usuario no en lista permitida | Verifica tu `SLACK_ALLOWED_USERS` en `.env` |

### El bot no responde a mensajes directos

**Causa**: El usuario no está en `SLACK_ALLOWED_USERS` o el token es incorrecto.

**Solución**: 
1. Confirma el Member ID del usuario (Paso 6)
2. Añádelo a `SLACK_ALLOWED_USERS` en tu `.env` (separado por comas si hay múltiples)
3. Reinicia la puerta de enlace

### Error de autenticación al iniciar

**Causa**: Token de bot inválido o expirado.

**Solución**:
1. Ve a [api.slack.com/apps](https://api.slack.com/apps) y selecciona tu aplicación
2. Haz clic en **OAuth & Permissions**
3. Bajo **Bot User OAuth Token**, haz clic en **Refresh Token**
4. Copia el nuevo token
5. Actualiza `SLACK_BOT_TOKEN` en tu `.env`
6. Reinicia la puerta de enlace

## Lista de Verificación Rápida para Problemas de Mensajes de Canal

Si tu bot no responde a mensajes de canal, verifica esto manualmente:

1. ☐ El bot está invitado al canal (`message.channels` funciona solo si el bot está en el canal)
2. ☐ `message.channels` está listado en **Event Subscriptions** → **Subscribe to bot events**
3. ☐ `chat:write` y `channels:history` están en **OAuth & Permissions** → **Bot Token Scopes**
4. ☐ El usuario está en `SLACK_ALLOWED_USERS` en `~/.hermes/.env`
5. ☐ `hermes gateway` está ejecutándose
6. ☐ Socket Mode está **ACTIVADO** en la configuración de la aplicación
7. ☐ `SLACK_BOT_TOKEN` en tu `.env` comienza con `xoxb-`
8. ☐ Reiniciaste `hermes gateway` después de hacer cambios en `.env`

## Seguridad

- **Protege tu bot token**: Nunca lo compartas públicamente ni lo confirmes a Git. Si lo haces accidentalmente, ve a OAuth & Permissions en tu aplicación y haz clic en **Refresh Token** para invalidar el antiguo.
- **Rotación de token regular**: Considera refrescar tu token cada ~90 días como medida de seguridad.
- **Socket Mode**: Una ventaja de Socket Mode es que todo ocurre sobre una conexión outbound segura desde tu servidor a Slack — no hay servidores públicos expuestos que hacer parchear o asegurar.
