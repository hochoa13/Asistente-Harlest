---
sidebar_position: 7
title: "Email"
description: "Configura Hermes Agent como asistente de correo electrónico a través de IMAP/SMTP"
---

# Configuración de Email

Hermes puede recibir y responder correos electrónicos usando protocolos IMAP y SMTP estándar. Envía un correo a la dirección del agente y responde en hilo — no se necesita cliente especial ni API de bot. Funciona con Gmail, Outlook, Yahoo, Fastmail, o cualquier proveedor que soporte IMAP/SMTP.

:::info Sin Dependencias Externas
El adaptador de Email usa módulos integrados de Python: `imaplib`, `smtplib`, y `email`. No se requieren paquetes adicionales ni servicios externos.
:::

---

## Requisitos Previos

- **Una cuenta de correo dedicada** para tu agente Hermes (no uses tu correo personal)
- **IMAP habilitado** en la cuenta de email
- **Una contraseña de aplicación** si usas Gmail u otro proveedor con 2FA

### Configuración de Gmail

1. Habilita Autenticación de dos Factores en tu Cuenta de Google
2. Ve a [App Passwords](https://myaccount.google.com/apppasswords)
3. Crea una nueva App Password (selecciona "Mail" u "Other")
4. Copia la contraseña de 16 caracteres — la usarás en lugar de tu contraseña regular

### Outlook / Microsoft 365

1. Ve a [Configuración de Seguridad](https://account.microsoft.com/security)
2. Habilita 2FA si no está activo
3. Crea una App Password en "Additional security options"
4. Host IMAP: `outlook.office365.com`, Host SMTP: `smtp.office365.com`

### Otros Proveedores

La mayoría de proveedores de email soportan IMAP/SMTP. Consulta la documentación de tu proveedor para:
- Host y puerto IMAP (usualmente puerto 993 con SSL)
- Host y puerto SMTP (usualmente puerto 587 con STARTTLS)
- Si se requieren contraseñas de aplicación

---

## Paso 1: Configurar Hermes

La forma más fácil:

```bash
hermes gateway setup
```

Selecciona **Email** del menú de plataformas. El asistente te pide tu dirección de correo, contraseña, hosts IMAP/SMTP, y remitentes autorizados.

### Configuración Manual

Añade a `~/.hermes/.env`:

```bash
# Requerido
EMAIL_ADDRESS=hermes@gmail.com
EMAIL_PASSWORD=abcd efgh ijkl mnop    # App password (no tu contraseña regular)
EMAIL_IMAP_HOST=imap.gmail.com
EMAIL_SMTP_HOST=smtp.gmail.com

# Seguridad (recomendado)
EMAIL_ALLOWED_USERS=your@email.com,colleague@work.com

# Opcional
EMAIL_IMAP_PORT=993                    # Default: 993 (IMAP SSL)
EMAIL_SMTP_PORT=587                    # Default: 587 (SMTP STARTTLS)
EMAIL_POLL_INTERVAL=15                 # Segundos entre verificaciones de bandeja (default: 15)
EMAIL_HOME_ADDRESS=your@email.com      # Destino de entrega predeterminado para trabajos cron
```

---

## Paso 2: Iniciar la Puerta de Enlace

```bash
hermes gateway              # Ejecutar en primer plano
hermes gateway install      # Instalar como servicio del sistema
```

Al iniciar, el adaptador:
1. Prueba conexiones IMAP y SMTP
2. Marca todos los correos existentes en la bandeja como "vistos" (solo procesa correos nuevos)
3. Comienza a sondear nuevos correos

---

## Cómo Funciona

### Recibiendo Mensajes

El adaptador sondea la bandeja IMAP para mensajes NO VISTOS en un intervalo configurable (default: 15 segundos). Para cada correo nuevo:

- **Línea de asunto** se incluye como contexto (ej. `[Subject: Deploy to production]`)
- **Correos de respuesta** (asunto comenzando con `Re:`) omiten el prefijo de asunto — el contexto del hilo ya está establecido
- **Archivos adjuntos** se almacenan en caché localmente:
  - Imágenes (JPEG, PNG, GIF, WebP) → disponibles para la herramienta de visión
  - Documentos (PDF, ZIP, etc.) → disponibles para acceso de archivos
- **Correos solo HTML** tienen etiquetas eliminadas para extracción de texto plano
- **Automensajes** se filtran para prevenir bucles de respuesta

### Enviando Respuestas

Las respuestas se envían a través de SMTP con encabezados de threading de correo adecuados:

- **In-Reply-To** y **References** mantienen el hilo
- **Línea de asunto** conservada con prefijo `Re:` (sin `Re: Re:` duplicado)
- **Message-ID** generada con el dominio del agente
- Las respuestas se envían como texto plano (UTF-8)

### Archivos Adjuntos

El agente puede enviar archivos adjuntos en respuestas. Incluye `MEDIA:/path/to/file` en la respuesta y el archivo se adjunta al correo saliente.

---

## Control de Acceso

El acceso a correo electrónico sigue el mismo patrón que todas las otras plataformas de Hermes:

1. **`EMAIL_ALLOWED_USERS` establecida** → solo se procesan correos de esas direcciones
2. **Sin lista blanca establecida** → remitentes desconocidos reciben un código de emparejamiento
3. **`EMAIL_ALLOW_ALL_USERS=true`** → se aceptan todos los remitentes (usar con cuidado)

:::warning
**Siempre configura `EMAIL_ALLOWED_USERS`.** Sin ella, cualquiera que conozca la dirección de correo del agente podría enviar comandos. El agente tiene acceso a terminal de forma predeterminada.
:::

---

## Solución de Problemas

| Problema | Solución |
|---------|----------|
| **"IMAP connection failed"** al inicio | Verifica `EMAIL_IMAP_HOST` y `EMAIL_IMAP_PORT`. Asegúrate de que IMAP está habilitado en la cuenta. Para Gmail, habilítalo en Configuración → Reenvío y POP/IMAP. |
| **"SMTP connection failed"** al inicio | Verifica `EMAIL_SMTP_HOST` y `EMAIL_SMTP_PORT`. Comprueba que tu contraseña sea correcta (usa App Password para Gmail). |
| **Los mensajes no se reciben** | Comprueba que `EMAIL_ALLOWED_USERS` incluya el correo del remitente. Verifica la carpeta de spam — algunos proveedores marcan respuestas automatizadas. |
| **"Authentication failed"** | Para Gmail, debes usar una App Password, no tu contraseña regular. Asegúrate de que 2FA esté habilitado primero. |
| **Respuestas duplicadas** | Asegúrate de que solo una instancia de gateway esté ejecutándose. Comprueba `hermes gateway status`. |
| **Respuesta lenta** | El intervalo de sondeo predeterminado es 15 segundos. Reduce con `EMAIL_POLL_INTERVAL=5` para respuesta más rápida (pero más conexiones IMAP). |
| **Las respuestas no están enhebrando** | El adaptador usa encabezados In-Reply-To. Algunos clientes de correo (especialmente basados en web) pueden no enhebrar correctamente con mensajes automatizados. |

---

## Seguridad

:::warning
**Usa una cuenta de correo dedicada.** No uses tu correo personal — el agente almacena la contraseña en `.env` y tiene acceso completo a la bandeja a través de IMAP.
:::

- Usa **App Passwords** en lugar de tu contraseña principal (requerido para Gmail con 2FA)
- Establece `EMAIL_ALLOWED_USERS` para restringir quién puede interactuar con el agente
- La contraseña se almacena en `~/.hermes/.env` — protege este archivo (`chmod 600`)
- IMAP usa SSL (puerto 993) y SMTP usa STARTTLS (puerto 587) de forma predeterminada — las conexiones están encriptadas

---

## Referencia de Variables de Entorno

| Variable | Requerida | Default | Descripción |
|----------|----------|---------|-------------|
| `EMAIL_ADDRESS` | Sí | — | Dirección de correo del agente |
| `EMAIL_PASSWORD` | Sí | — | Contraseña de correo o app password |
| `EMAIL_IMAP_HOST` | Sí | — | Host del servidor IMAP (ej. `imap.gmail.com`) |
| `EMAIL_SMTP_HOST` | Sí | — | Host del servidor SMTP (ej. `smtp.gmail.com`) |
| `EMAIL_IMAP_PORT` | No | `993` | Puerto del servidor IMAP |
| `EMAIL_SMTP_PORT` | No | `587` | Puerto del servidor SMTP |
| `EMAIL_POLL_INTERVAL` | No | `15` | Segundos entre verificaciones de bandeja |
| `EMAIL_ALLOWED_USERS` | No | — | Direcciones de remitentes autorizadas separadas por comas |
| `EMAIL_HOME_ADDRESS` | No | — | Destino de entrega predeterminado para trabajos cron |
| `EMAIL_ALLOW_ALL_USERS` | No | `false` | Permitir todos los remitentes (no recomendado) |
