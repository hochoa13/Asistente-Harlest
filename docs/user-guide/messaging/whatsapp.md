---
sidebar_position: 5
title: "WhatsApp"
description: "Configura Hermes Agent como un bot WhatsApp a través del puente Baileys integrado"
---

# Configuración de WhatsApp

Hermes Agent se conecta a WhatsApp a través de un puente integrado usando [whatsapp-web.js](https://github.com/pedroslopez/whatsapp-web.js) (basado en Baileys). Esto funciona emulando una sesión de WhatsApp Web — **no** a través de la API oficial de WhatsApp Business. No requieres una cuenta de desarrollador de Meta ni verificación empresarial.

:::warning[API No Oficial — Riesgo de Restricción]
WhatsApp **no apoya** oficialmente bots de terceros fuera de la API Business. Usar whatsapp-web.js lleva un pequeño riesgo de restricciones de cuenta. Para minimizar el riesgo:
- **Usa un número de teléfono dedicado** para el bot (no tu número personal)
- **No envíes mensajes masivos/spam** — mantén el uso conversacional
- **No automatices mensajes salientes** a personas que no hayan escrito primero
:::

:::warning[Actualizaciones de Protocolo de WhatsApp Web]
WhatsApp periódicamente actualiza su protocolo web, lo que puede romper temporalmente la compatibilidad con whatsapp-web.js. Cuando esto sucede, Hermes actualiza la dependencia del puente. Si el bot deja de funcionar después de una actualización de WhatsApp, obtén la última versión de Hermes y vuelve a emparejar.
:::

## Dos Modos

| Modo | Cómo funciona | Mejor para |
|------|-------------|-----------|
| **Número de bot separado** (recomendado) | Dedica un número de teléfono al bot. Las personas envían mensajes a ese número directamente. | UX limpia, múltiples usuarios, riesgo menor de restricción |
| **Auto-chat personal** | Usa tu propio WhatsApp. Tú te envías mensajes a ti mismo para hablar con el agente. | Configuración rápida, usuario único, pruebas |

## Requisitos Previos

- **Node.js v18+** y **npm** — el puente de WhatsApp se ejecuta como un proceso Node.js
- **Un teléfono con WhatsApp** instalado (para escanear el código QR)

**En servidores Linux sin cabezal**, también necesitas dependencias de Chromium/Puppeteer:

```bash
# Debian / Ubuntu
sudo apt-get install -y \
  libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
  libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
  libpango-1.0-0 libcairo2 libasound2 libxshmfence1

# Fedora / RHEL
sudo dnf install -y \
  nss atk at-spi2-atk cups-libs libdrm libxkbcommon \
  libXcomposite libXdamage libXrandr mesa-libgbm \
  pango cairo alsa-lib
```

## Paso 1: Ejecutar el Asistente de Configuración

```bash
hermes whatsapp
```

El asistente:

1. Te preguntará qué modo deseas (**bot** o **self-chat**)
2. Instalará dependencias del puente si es necesario
3. Mostrará un **código QR** en tu terminal
4. Esperará a que lo escanees

**Para escanear el código QR:**

1. Abre WhatsApp en tu teléfono
2. Ve a **Configuración → Dispositivos Vinculados**
3. Toque **Vincular un Dispositivo**
4. Apunta tu cámara al código QR de la terminal

Una vez emparejado, el asistente confirma la conexión y sale. Tu sesión se guarda automáticamente.

:::tip
Si el código QR se ve borroso, asegúrate de que tu terminal tenga al menos 60 columnas de ancho y admita Unicode. También puedes probar un emulador de terminal diferente.
:::

## Paso 2: Obtener un Segundo Número de Teléfono (Modo Bot)

Para el modo bot, necesitas un número de teléfono que no esté ya registrado con WhatsApp. Tres opciones:

| Opción | Costo | Notas |
|--------|------|-------|
| **Google Voice** | Gratis | Solo EE.UU. Obtén un número en [voice.google.com](https://voice.google.com). Verifica WhatsApp vía SMS a través de la aplicación Google Voice. |
| **SIM Prepago** | $5–15 una vez | Cualquier operador. Activa, verifica WhatsApp, luego el SIM puede quedarse en un cajón. El número debe mantenerse activo (hacer una llamada cada 90 días). |
| **Servicios VoIP** | Gratis–$5/mes | TextNow, TextFree, o similares. Algunos números VoIP están bloqueados por WhatsApp — prueba algunos si el primero no funciona. |

Después de obtener el número:

1. Instala WhatsApp en un teléfono (o usa la aplicación WhatsApp Business con SIM dual)
2. Registra el nuevo número con WhatsApp
3. Ejecuta `hermes whatsapp` y escanea el código QR desde esa cuenta de WhatsApp

## Paso 3: Configurar Hermes

Añade lo siguiente a tu archivo `~/.hermes/.env`:

```bash
# Requerido
WHATSAPP_ENABLED=true
WHATSAPP_MODE=bot                          # "bot" o "self-chat"
WHATSAPP_ALLOWED_USERS=15551234567         # Números de teléfono separados por comas (con código de país, sin +)

# Opcional
WHATSAPP_HOME_CONTACT=15551234567          # Contacto predeterminado para mensajes proactivos/programados
```

Luego inicia la puerta de enlace:

```bash
hermes gateway              # Primer plano
hermes gateway install      # Instalar como servicio del sistema
```

La puerta de enlace inicia automáticamente el puente de WhatsApp usando la sesión guardada.

## Persistencia de Sesión

La estrategia `LocalAuth` de whatsapp-web.js guarda tu sesión en la carpeta `.wwebjs_auth` dentro de tu directorio de datos de Hermes (`~/.hermes/`). Esto significa:

- **Las sesiones sobreviven a los reinicios** — no necesitas volver a escanear el código QR cada vez
- Los datos de sesión incluyen claves de cifrado y credenciales de dispositivo
- **No compartas ni confirmes la carpeta `.wwebjs_auth`** — otorga acceso completo a la cuenta de WhatsApp

## Reemparejamiento

Si la sesión se rompe (reinicio del teléfono, actualización de WhatsApp, desvinculación manual), verás errores de conexión en los registros de la puerta de enlace. Para solucionarlo:

```bash
hermes whatsapp
```

Esto genera un nuevo código QR. Escanéalo de nuevo y la sesión se restablece. La puerta de enlace maneja **desconexiones temporales** (interrupciones de red, teléfono desconectándose brevemente) automáticamente con lógica de reconexión.

## Mensajes de Voz

Hermes Agent admite mensajes de voz en WhatsApp:

- **Entrada**: Los mensajes de voz (`.ogg` opus) se transcriben automáticamente usando Whisper (requiere `VOICE_TOOLS_OPENAI_KEY`)
- **Salida**: Las respuestas TTS se envían como adjuntos de archivo de audio MP3
- Las respuestas del agente van prefijadas con "⚕ **Hermes Agent**" para fácil identificación

## Solución de Problemas

| Problema | Solución |
|----------|----------|
| **El código QR no escanea** | Asegúrate de que la terminal sea lo suficientemente ancha (60+ columnas). Prueba un terminal diferente. Asegúrate de estar escaneando desde la cuenta de WhatsApp correcta (número del bot, no personal). |
| **El código QR vence** | Los códigos QR se actualizan cada ~20 segundos. Si vence, reinicia `hermes whatsapp`. |
| **La sesión no persiste** | Verifica que `~/.hermes/.wwebjs_auth/` exista y sea escribible. En Docker, móntalo como un volumen. |
| **Deslogueado inesperadamente** | WhatsApp desvincula dispositivos después de ~14 días de inactividad del teléfono. Mantén el teléfono encendido y conectado a WiFi. Vuelve a emparejar con `hermes whatsapp`. |
| **"El contexto de ejecución fue destruido"** | Chromium se bloqueó. Instala las dependencias de Puppeteer listadas en Requisitos Previos. En servidores con poca RAM, añade espacio de intercambio. |
| **El bot deja de funcionar después de una actualización de WhatsApp** | Actualiza Hermes para obtener la última versión del puente, luego vuelve a emparejar. |
| **Los mensajes no se están recibiendo** | Verifica que `WHATSAPP_ALLOWED_USERS` incluya el número del remitente (con código de país, sin `+` ni espacios). |

## Seguridad

:::warning
**Siempre establece `WHATSAPP_ALLOWED_USERS`** con números de teléfono (incluyendo código de país, sin el `+`) de usuarios autorizados. Sin esta configuración, la puerta de enlace **negará todos los mensajes entrantes** como medida de seguridad.
:::

- La carpeta `.wwebjs_auth` contiene credenciales de sesión completas — protégela como una contraseña
- Establece permisos de archivo: `chmod 700 ~/.hermes/.wwebjs_auth`
- Usa un **número de teléfono dedicado** para el bot para aislar el riesgo de tu cuenta personal
- Si sospechas compromiso, desvincula el dispositivo desde WhatsApp → Configuración → Dispositivos Vinculados
- Los números de teléfono en los registros están parcialmente redactados, pero revisa tu política de retención de registros
