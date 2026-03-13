---
sidebar_position: 1
title: "Telegram"
description: "Configura Hermes Agent como un bot de Telegram"
---

# Configuración de Telegram

Hermes Agent se integra con Telegram como un bot conversacional completo. Una vez conectado, puedes chatear con tu agente desde cualquier dispositivo, enviar notas de voz que se transcriben automáticamente, recibir resultados de tareas programadas y usar el agente en chats grupales. La integración está construida sobre [python-telegram-bot](https://python-telegram-bot.org/) y admite texto, voz, imágenes y adjuntos de archivos.

## Paso 1: Crear un Bot con BotFather

Todo bot de Telegram requiere un token de API emitido por [@BotFather](https://t.me/BotFather), la herramienta oficial de gestión de bots de Telegram.

1. Abre Telegram y busca **@BotFather**, o visita [t.me/BotFather](https://t.me/BotFather)
2. Envía `/newbot`
3. Elige un **nombre para mostrar** (p. ej., "Hermes Agent") — puede ser cualquier cosa
4. Elige un **nombre de usuario** — debe ser único y terminar en `bot` (p. ej., `mi_hermes_bot`)
5. BotFather responde con tu **token de API**. Se ve así:

```
123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
```

:::warning
Mantén tu token de bot en secreto. Cualquiera con este token puede controlar tu bot. Si se filtra, revócalo inmediatamente con `/revoke` en BotFather.
:::

## Paso 2: Personalizar tu Bot (Opcional)

Estos comandos de BotFather mejoran la experiencia del usuario. Envía un mensaje a @BotFather y utiliza:

| Comando | Propósito |
|---------|-----------|
| `/setdescription` | El texto "¿Qué puede hacer este bot?" mostrado antes de que un usuario comience a chatear |
| `/setabouttext` | Texto corto en la página de perfil del bot |
| `/setuserpic` | Carga un avatar para tu bot |
| `/setcommands` | Define el menú de comandos (el botón `/` en el chat) |
| `/setprivacy` | Controla si el bot ve todos los mensajes grupales (ver Paso 3) |

:::tip
Para `/setcommands`, un conjunto útil de inicio:

```
help - Mostrar información de ayuda
new - Iniciar una nueva conversación
sethome - Establecer este chat como canal principal
```
:::

## Paso 3: Modo Privado (Crítico para Grupos)

Los bots de Telegram tienen un **modo privado** que está **habilitado por defecto**. Esta es la fuente más común de confusión al usar bots en grupos.

**Con modo privado ACTIVADO**, tu bot solo puede ver:
- Mensajes que comienzan con un comando `/`
- Respuestas directas a los propios mensajes del bot
- Mensajes de servicio (miembros que se unen/salen, mensajes fijados, etc.)
- Mensajes de canales donde el bot es administrador

**Con modo privado DESACTIVADO**, el bot recibe todos los mensajes del grupo.

### Cómo desactivar el modo privado

1. Envía un mensaje a **@BotFather**
2. Envía `/mybots`
3. Selecciona tu bot
4. Ve a **Configuración del Bot → Privacidad del Grupo → Desactivar**

:::warning
**Debes remover y volver a añadir el bot a cualquier grupo** después de cambiar la configuración de privacidad. Telegram cachea el estado de privacidad cuando un bot se une a un grupo, y no se actualizará hasta que el bot se remueva y se vuelva a añadir.
:::

:::tip
Una alternativa a desactivar el modo privado: promover el bot a **administrador del grupo**. Los bots administrador siempre reciben todos los mensajes independientemente de la configuración de privacidad, y esto evita la necesidad de alternar el modo privado global.
:::

## Paso 4: Encontrar tu ID de Usuario

Hermes Agent utiliza IDs numéricos de usuario de Telegram para controlar el acceso. Tu ID de usuario **no** es tu nombre de usuario — es un número como `123456789`.

**Método 1 (recomendado):** Envía un mensaje a [@userinfobot](https://t.me/userinfobot) — responde instantáneamente con tu ID de usuario.

**Método 2:** Envía un mensaje a [@get_id_bot](https://t.me/get_id_bot) — otra opción confiable.

Guarda este número; lo necesitarás para el siguiente paso.

## Paso 5: Configurar Hermes

### Opción A: Configuración Interactiva (Recomendado)

```bash
hermes gateway setup
```

Selecciona **Telegram** cuando se te solicite. El asistente te pide tu token de bot e IDs de usuario permitidos, luego escribe la configuración por ti.

### Opción B: Configuración Manual

Añade lo siguiente a `~/.hermes/.env`:

```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
TELEGRAM_ALLOWED_USERS=123456789    # Separados por comas para múltiples usuarios
```

### Iniciar la Puerta de Enlace

```bash
hermes gateway
```

El bot debe estar en línea en cuestión de segundos. Envíale un mensaje en Telegram para verificar.

## Canal Principal

Usa el comando `/sethome` en cualquier chat de Telegram (DM o grupo) para designarlo como **canal principal**. Las tareas programadas (trabajos cron) entregan sus resultados a este canal.

También puedes configurarlo manualmente en `~/.hermes/.env`:

```bash
TELEGRAM_HOME_CHANNEL=-1001234567890
TELEGRAM_HOME_CHANNEL_NAME="Mis Notas"
```

:::tip
Los IDs de chat de grupo son números negativos (p. ej., `-1001234567890`). Tu ID de chat DM personal es el mismo que tu ID de usuario.
:::

## Mensajes de Voz

### Voz Entrante (Voz a Texto)

Los mensajes de voz que envías en Telegram se transcriben automáticamente usando la API Whisper de OpenAI e se inyectan como texto en la conversación. Esto requiere `VOICE_TOOLS_OPENAI_KEY` en `~/.hermes/.env`.

### Voz Saliente (Texto a Voz)

Cuando el agente genera audio mediante TTS, se entrega como **burbujas de voz** nativas de Telegram — el tipo redondo, reproducible en línea.

- **OpenAI y ElevenLabs** producen Opus nativamente — no se necesita configuración adicional
- **Edge TTS** (el proveedor predeterminado gratuito) genera MP3 y requiere **ffmpeg** para convertir a Opus:

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

Sin ffmpeg, el audio de Edge TTS se envía como un archivo de audio regular (aún reproducible, pero usa el reproductor rectangular en lugar de una burbuja de voz).

Configura el proveedor de TTS en tu `config.yaml` bajo la clave `tts.provider`.

## Uso en Chats Grupales

Hermes Agent funciona en chats grupales de Telegram con algunas consideraciones:

- **Modo privado** determina qué mensajes puede ver el bot (ver [Paso 3](#paso-3-modo-privado-crítico-para-grupos))
- Cuando el modo privado está activado, **menciona el bot** (p. ej., `@mi_hermes_bot ¿cuál es el clima?`) o **responde a sus mensajes** para interactuar
- Cuando el modo privado está desactivado (o el bot es administrador), el bot ve todos los mensajes y puede participar naturalmente
- `TELEGRAM_ALLOWED_USERS` sigue siendo aplicable — solo los usuarios autorizados pueden activar el bot, incluso en grupos

## Características Recientes de la API de Bot (2024–2025)

- **Política de privacidad:** Telegram ahora requiere que los bots tengan una política de privacidad. Establece una vía BotFather con `/setprivacy_policy`, o Telegram puede generar automáticamente un marcador de posición. Esto es particularmente importante si tu bot es público.
- **Transmisión de mensajes:** La API de Bot 9.x añadió soporte para transmitir respuestas largas, lo que puede mejorar la latencia percibida para respuestas largas del agente.

## Solución de Problemas

| Problema | Solución |
|----------|----------|
| El bot no responde en absoluto | Verifica que `TELEGRAM_BOT_TOKEN` sea correcto. Revisa los registros de `hermes gateway` en busca de errores. |
| El bot responde con "no autorizado" | Tu ID de usuario no está en `TELEGRAM_ALLOWED_USERS`. Verifica nuevamente con @userinfobot. |
| El bot ignora los mensajes del grupo | El modo privado probablemente está activado. Desactívalo (Paso 3) o haz que el bot sea administrador del grupo. **Recuerda remover y volver a añadir el bot después de cambiar la privacidad.** |
| Los mensajes de voz no se transcriben | Comprueba que `VOICE_TOOLS_OPENAI_KEY` esté configurado y sea válido en `~/.hermes/.env`. |
| Las respuestas de voz son archivos, no burbujas | Instala `ffmpeg` (necesario para la conversión de Opus de Edge TTS). |
| Token de bot revocado/inválido | Genera un nuevo token vía `/revoke` luego `/newbot` o `/token` en BotFather. Actualiza tu archivo `.env`. |

## Aprobación de Ejecución

Cuando el agente intenta ejecutar un comando potencialmente peligroso, te pide aprobación en el chat:

> ⚠️ Este comando es potencialmente peligroso (eliminación recursiva). Responde "sí" para aprobar.

Responde "sí"/"s" para aprobar o "no"/"n" para denegar.

## Seguridad

:::warning
Siempre establece `TELEGRAM_ALLOWED_USERS` para restringir quién puede interactuar con tu bot. Sin esto, la puerta de enlace deniega a todos los usuarios por defecto como medida de seguridad.
:::

Nunca compartas tu token de bot públicamente. Si se compromete, revócalo inmediatamente vía el comando `/revoke` de BotFather.
