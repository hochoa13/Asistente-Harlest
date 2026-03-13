---
sidebar_position: 3
title: "Discord"
description: "Configura Hermes Agent como un bot Discord"
---

# Configuración de Discord

Hermes Agent se integra con Discord como un bot, permitiéndote chatear con tu asistente de IA a través de mensajes directos o canales del servidor. El bot recibe tus mensajes, los procesa a través de la tubería de Hermes Agent (incluyendo uso de herramientas, memoria y razonamiento), y responde en tiempo real. Admite texto, mensajes de voz, adjuntos de archivos y comandos de barra.

Esta guía te acompaña en el proceso de configuración completo — desde crear tu bot en el Portal de Desarrolladores de Discord hasta enviar tu primer mensaje.

## Paso 1: Crear una Aplicación Discord

1. Ve al [Portal de Desarrolladores de Discord](https://discord.com/developers/applications) e inicia sesión con tu cuenta de Discord.
2. Haz clic en **Nueva Aplicación** en la esquina superior derecha.
3. Ingresa un nombre para tu aplicación (p. ej., "Hermes Agent") y acepta los Términos de Servicio del Desarrollador.
4. Haz clic en **Crear**.

Aterrizarás en la página **Información General**. Nota el **ID de Aplicación** — lo necesitarás más adelante para construir la URL de invitación.

## Paso 2: Crear el Bot

1. En la barra lateral izquierda, haz clic en **Bot**.
2. Discord crea automáticamente un usuario bot para tu aplicación. Verás el nombre de usuario del bot, que puedes personalizar.
3. En **Flujo de Autorización**:
   - Establece **Bot Público** en **DESACTIVADO** — esto previene que otras personas inviten tu bot a sus servidores.
   - Deja **Requerir Concesión de Código OAuth2** establecido en **DESACTIVADO**.

:::tip
Puedes establecer un avatar y pancarta personalizados para tu bot en esta página. Esto es lo que los usuarios verán en Discord.
:::

## Paso 3: Habilitar Intenciones de Puerta de Enlace Privilegiadas

Este es el paso más crítico en toda la configuración. Sin los intents correctos habilitados, tu bot se conectará a Discord pero **no podrá leer el contenido del mensaje**.

En la página **Bot**, desplázate hacia abajo a **Intenciones de Puerta de Enlace Privilegiadas**. Verás tres alternadores:

| Intent | Propósito | ¿Requerido? |
|--------|-----------|-----------|
| **Intent de Presencia** | Ver estado en línea/desconectado de usuarios | Opcional |
| **Intent de Miembros del Servidor** | Acceder a la lista de miembros | Opcional |
| **Intent de Contenido de Mensaje** | Leer el contenido de texto de los mensajes | **Requerido** |

**Habilita el Intent de Contenido de Mensaje** alternándolo **ACTIVADO**. Sin esto, tu bot recibe eventos de mensaje pero el texto del mensaje está vacío — el bot literalmente no puede ver lo que escribiste.

:::warning[Esta es la #1 razón por la que los bots Discord no funcionan]
Si tu bot está en línea pero nunca responde a mensajes, el **Intent de Contenido de Mensaje** casi seguramente está deshabilitado. Ve atrás al [Portal de Desarrolladores](https://discord.com/developers/applications), selecciona tu aplicación → Bot → Intenciones de Puerta de Enlace Privilegiadas, y asegúrate de que **Intent de Contenido de Mensaje** está alternado ACTIVADO. Haz clic en **Guardar Cambios**.
:::

**Respecto a la cantidad de servidores:**
- Si tu bot está en **menos de 100 servidores**, puedes simplemente alternar intents libremente.
- Si tu bot está en **100 o más servidores**, Discord requiere que envíes una solicitud de verificación para usar intents privilegiados. Para uso personal, esto no es una preocupación.

Haz clic en **Guardar Cambios** en la parte inferior de la página.

## Paso 4: Obtener el Token del Bot

El token del bot es la credencial que Hermes Agent utiliza para iniciar sesión como tu bot. Aún en la página **Bot**:

1. Bajo la sección **Token**, haz clic en **Restablecer Token**.
2. Si tienes autenticación de dos factores habilitada en tu cuenta de Discord, ingresa tu código 2FA.
3. Discord mostrará tu nuevo token. **Cópialo inmediatamente.**

:::warning[Token mostrado solo una vez]
El token se muestra solo una vez. Si lo pierdes, necesitarás restablecerlo y generar uno nuevo. Nunca compartas tu token públicamente o lo confirmes a Git — cualquiera con este token tiene control total de tu bot.
:::

Almacena el token en algún lugar seguro (un gestor de contraseñas, por ejemplo). Lo necesitarás en el Paso 8.

## Paso 5: Generar la URL de Invitación

Necesitas una URL de OAuth2 para invitar el bot a tu servidor. Hay dos formas de hacer esto:

### Opción A: Usar la Pestaña de Instalación (Recomendado)

1. En la barra lateral izquierda, haz clic en **Instalación**.
2. Bajo **Contextos de Instalación**, habilita **Instalación de Gremio**.
3. Para **Enlace de Instalación**, selecciona **Enlace Proporcionado por Discord**.
4. Bajo **Configuración de Instalación Predeterminada** para Instalación de Gremio:
   - **Ámbitos**: selecciona `bot` y `applications.commands`
   - **Permisos**: selecciona los permisos listados a continuación.

### Opción B: URL Manual

Puedes construir la URL de invitación directamente usando este formato:

```
https://discord.com/oauth2/authorize?client_id=TU_ID_APLICACION&scope=bot+applications.commands&permissions=274878286912
```

Reemplaza `TU_ID_APLICACION` con el ID de Aplicación del Paso 1.

### Permisos Requeridos

Estos son los permisos mínimos que tu bot necesita:

- **Ver Canales** — ver los canales a los que tiene acceso
- **Enviar Mensajes** — responder a tus mensajes
- **Incrustar Enlaces** — formatear respuestas ricas
- **Adjuntar Archivos** — enviar imágenes, audio y salidas de archivos
- **Leer Historial de Mensajes** — mantener contexto de conversación

### Permisos Recomendados Adicionales

- **Enviar Mensajes en Hilos** — responder en conversaciones de hilos
- **Añadir Reacciones** — reaccionar a mensajes para reconocimiento

### Números de Permiso

| Nivel | Número de Permisos | Qué se Incluye |
|-------|-------------------|----------------|
| Mínimo | `117760` | Ver Canales, Enviar Mensajes, Leer Historial de Mensajes, Adjuntar Archivos |
| Recomendado | `274878286912` | Todos los anteriores más Incrustar Enlaces, Enviar Mensajes en Hilos, Añadir Reacciones |

## Paso 6: Invitar a tu Servidor

1. Abre la URL de invitación en tu navegador (de la pestaña de Instalación o la URL manual que construiste).
2. En el menú desplegable **Añadir a Servidor**, selecciona tu servidor.
3. Haz clic en **Continuar**, luego en **Autorizar**.
4. Completa el CAPTCHA si se te solicita.

:::info
Necesitas el permiso **Gestionar Servidor** en el servidor Discord para invitar un bot. Si no ves tu servidor en el menú desplegable, pide a un administrador del servidor que use el enlace de invitación en su lugar.
:::

Después de autorizar, el bot aparecerá en la lista de miembros de tu servidor (mostrará como desconectado hasta que inicies la puerta de enlace Hermes).

## Paso 7: Encontrar tu ID de Usuario de Discord

Hermes Agent utiliza tu ID de Usuario de Discord para controlar quién puede interactuar con el bot. Para encontrarlo:

1. Abre Discord (aplicación de escritorio o web).
2. Ve a **Configuración** → **Avanzado** → alterna **Modo de Desarrollador** a **ACTIVADO**.
3. Cierra configuración.
4. Haz clic derecho en tu propio nombre de usuario (en un mensaje, la lista de miembros, o tu perfil) → **Copiar ID de Usuario**.

Tu ID de Usuario es un número largo como `284102345871466496`.

:::tip
El Modo de Desarrollador también te permite copiar **IDs de Canal** e **IDs de Servidor** de la misma manera — haz clic derecho en el nombre del canal o servidor y selecciona Copiar ID. Necesitarás un ID de Canal si deseas establecer un canal principal manualmente.
:::

## Paso 8: Configurar Hermes Agent

### Opción A: Configuración Interactiva (Recomendado)

Ejecuta el comando de configuración guiado:

```bash
hermes gateway setup
```

Selecciona **Discord** cuando se te solicite, luego pega tu token de bot e ID de usuario cuando se te pregunte.

### Opción B: Configuración Manual

Añade lo siguiente a tu archivo `~/.hermes/.env`:

```bash
# Requerido
DISCORD_BOT_TOKEN=tu-token-de-bot-del-portal-desarrollador
DISCORD_ALLOWED_USERS=284102345871466496

# Múltiples usuarios permitidos (separados por comas)
# DISCORD_ALLOWED_USERS=284102345871466496,198765432109876543
```

### Iniciar la Puerta de Enlace

Una vez configurado, inicia la puerta de enlace Discord:

```bash
hermes gateway
```

El bot debe estar en línea en Discord en cuestión de segundos. Envíale un mensaje — ya sea un DM o en un canal que pueda ver — para probar.

:::tip
Puedes ejecutar `hermes gateway` en segundo plano o como un servicio systemd para operación persistente. Ver la documentación de despliegue para detalles.
:::

## Canal Principal

Puedes designar un "canal principal" donde el bot envía mensajes proactivos (tales como salida de trabajos cron, recordatorios y notificaciones). Hay dos formas de establecerlo:

### Usando el Comando de Barra

Escribe `/sethome` en cualquier canal Discord donde el bot esté presente. Ese canal se convierte en el canal principal.

### Configuración Manual

Añade estas variables a tu `~/.hermes/.env`:

```bash
DISCORD_HOME_CHANNEL=123456789012345678
DISCORD_HOME_CHANNEL_NAME="#actualizaciones-bot"
```

Reemplaza el ID con el ID real del canal (haz clic derecho → Copiar ID de Canal con Modo de Desarrollador activado).

## Comportamiento del Bot

- **Canales del servidor**: El bot responde a todos los mensajes de usuarios permitidos en canales a los que puede acceder. **No** requiere una mención o prefijo — cualquier mensaje de un usuario permitido se trata como un aviso.
- **Mensajes directos**: Los DMs siempre funcionan, incluso sin el Intent de Contenido de Mensaje habilitado (Discord exime los DMs de este requisito). Sin embargo, aún debes habilitar el intent para soporte de canal de servidor.
- **Conversaciones**: Cada canal o DM mantiene su propio contexto de conversación.

## Mensajes de Voz

Hermes Agent admite mensajes de voz de Discord:

- Los **mensajes de voz entrantes** se transcriben automáticamente usando Whisper (requiere `VOICE_TOOLS_OPENAI_KEY` configurado en tu ambiente).
- **Texto a voz**: Cuando TTS está habilitado, el bot puede enviar respuestas habladas como adjuntos de archivo MP3.

## Solución de Problemas

### El bot está en línea pero no responde a mensajes

**Causa**: El Intent de Contenido de Mensaje está deshabilitado.

**Solución**: Ve a [Portal de Desarrolladores](https://discord.com/developers/applications) → tu aplicación → Bot → Intenciones de Puerta de Enlace Privilegiadas → habilita **Intent de Contenido de Mensaje** → Guardar Cambios. Reinicia la puerta de enlace.

### Error "Intents Desautorizados" al iniciar

**Causa**: Tu código solicita intents que no están habilitados en el Portal de Desarrolladores.

**Solución**: Habilita los tres Intents de Puerta de Enlace Privilegiados (Presencia, Miembros del Servidor, Contenido de Mensaje) en la configuración del Bot, luego reinicia.

### El bot no puede ver mensajes en un canal específico

**Causa**: El rol del bot no tiene permiso para ver ese canal.

**Solución**: En Discord, ve a la configuración del canal → Permisos → añade el rol del bot con **Ver Canal** y **Leer Historial de Mensajes** habilitados.

### Errores 403 Prohibido

**Causa**: Al bot le faltan permisos requeridos.

**Solución**: Vuelve a invitar al bot con los permisos correctos usando la URL del Paso 5, o ajusta manualmente los permisos del rol del bot en Configuración del Servidor → Roles.

### El bot está desconectado

**Causa**: La puerta de enlace Hermes no está ejecutándose, o el token es incorrecto.

**Solución**: Verifica que `hermes gateway` esté ejecutándose. Verifica `DISCORD_BOT_TOKEN` en tu archivo `.env`. Si recientemente restableciste el token, actualízalo.

### "Usuario no permitido" / El bot te ignora

**Causa**: Tu ID de Usuario no está en `DISCORD_ALLOWED_USERS`.

**Solución**: Añade tu ID de Usuario a `DISCORD_ALLOWED_USERS` en `~/.hermes/.env` y reinicia la puerta de enlace.

## Seguridad

:::warning
Siempre establece `DISCORD_ALLOWED_USERS` para restringir quién puede interactuar con el bot. Sin esto, la puerta de enlace deniega a todos los usuarios por defecto como medida de seguridad. Solo añade IDs de Usuario de personas en las que confías — los usuarios autorizados tienen acceso completo a las capacidades del agente, incluyendo uso de herramientas y acceso al sistema.
:::

Para más información sobre asegurar tu despliegue de Hermes Agent, ver la [Guía de Seguridad](../security.md).
