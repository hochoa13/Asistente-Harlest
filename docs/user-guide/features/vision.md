---
title: Visión & Pegar Imagen
description: Pega imágenes desde tu Portapapeles en la CLI de Hermes para análisis multimodal de Visión.
sidebar_label: Visión & Pegar Imagen
sidebar_position: 7
---

# Visión & Pegar Imagen

Hermes Agent admite **Visión multimodal** — puedes pegar imágenes desde tu Portapapeles directamente en la CLI y pedirle al agente que las analice, describa o trabaje con ellas. Las imágenes se envían al modelo como bloques de contenido codificados en base64, por lo que cualquier modelo con capacidad de Visión puede procesarlas.

## Cómo Funciona

1. Copia una imagen a tu Portapapeles (Captura de pantalla, imagen del Navegador, etc.)
2. Céla usando uno de los métodos a continuación
3. Escribe tu pregunta y presiona Enter
4. La imagen aparece como una insignia `[\ud83d\udcc8 Imagen #1]` arriba de la entrada
5. Al enviar, la imagen se envía al modelo como un bloque de contenido de Visión

Puedes adjuntar múltiples imágenes antes de enviar — cada una obtiene su propia insignia. Presiona `Ctrl+C` para limpiar todas las imágenes adjuntas.

Las imágenes se guardan en `~/.hermes/images/` como archivos PNG con nombres de archivo con marca de tiempo.

## Métodos de Pegado

Cómo celas una imagen depende de tu entorno de terminal. No todos los métodos funcionan en todas partes — aquí está el desglose completo:

### Comando `/paste`

**El método más confiable. Funciona en todas partes.**

```
/paste
```

Escribe `/paste` y presiona Enter. Hermes verifica tu Portapapeles en busca de una imagen y la adjunta. Esto funciona en cada entorno porque llama explícitamente al backend del Portapapeles — sin preocupación por intercepciones de bindings de teclado de terminal.

### Ctrl+V / Cmd+V (Pegado Entre Corchetes)

Cuando pegas texto que está en el Portapapeles junto con una imagen, Hermes verifica automáticamente si hay una imagen también. Esto funciona cuando:
- Tu Portapapeles contiene **tanto texto como una imagen** (algunas aplicaciones ponen ambos cuando copias)
- Tu terminal admite pegado entre corchetes (la mayoría de los terminales modernos lo hacen)

:::warning
Si tu Portapapeles tiene **solo una imagen** (sin texto), Ctrl+V no hace nada en la mayoría de los terminales. Los terminales solo pueden pegar texto — no hay mecanismo estándar para pegar datos de imagen binaria. Usa `/paste` o Alt+V en su lugar.
:::

### Alt+V

Las combinaciones de teclas Alt pasan a través de la mayoría de emuladores de terminal (se envían como ESC + tecla en lugar de ser interceptadas). Presiona `Alt+V` para verifica el Portapapeles en busca de una imagen.

:::caution
**No funciona en la terminal integrada de VSCode.** VSCode intercepta muchas combinaciones Alt+tecla para su propia interfaz de usuario. Usa `/paste` en su lugar.
:::

### Ctrl+V (Raw — Solo Linux)

En terminales de escritorio Linux (GNOME Terminal, Konsole, Alacritty, etc.), `Ctrl+V` **no** es el atajo de pegado — `Ctrl+Shift+V` lo es. Entonces `Ctrl+V` envía un byte sin procesar a la aplicación, y Hermes lo captura para verifica el Portapapeles. Esto solo funciona en terminales de escritorio Linux con acceso a Portapapeles X11 o Wayland.

## Compatibilidad de Plataforma

| Entorno | `/paste` | Ctrl+V texto+imagen | Alt+V | Notas |
|---|:---:|:---:|:---:|---|
| **macOS Terminal / iTerm2** | ✅ | ✅ | ✅ | Mejor experiencia — `osascript` siempre disponible |
| **Linux X11 desktop** | ✅ | ✅ | ✅ | Requiere `xclip` (`apt install xclip`) |
| **Linux Wayland desktop** | ✅ | ✅ | ✅ | Requiere `wl-paste` (`apt install wl-clipboard`) |
| **WSL2 (Windows Terminal)** | ✅ | ✅¹ | ✅ | Usa `powershell.exe` — sin instalación extra necesaria |
| **VSCode Terminal (local)** | ✅ | ✅¹ | ❌ | VSCode intercepta Alt+key |
| **VSCode Terminal (ssh)** | ❌² | ❌² | ❌ | Portapapeles remoto no accesible |
| **ssh terminal (any)** | ❌² | ❌² | ❌² | Portapapeles remoto no accesible |

¹ Solo cuando el Portapapeles tiene tanto texto como una imagen (Portapapeles solo con imagen = nada sucede)
² Ver [ssh & Sesiones Remoto](#ssh--remote-sessions) a continuación

## Configuración Especística de Plataforma

### macOS

**No requiere configuración.** Hermes usa `osascript` (incorporado en macOS) para leer el Portapapeles. Para un mejor rendimiento, opcionalmente instala `pngpaste`:

```bash
brew install pngpaste
```

### Linux (X11)

Instala `xclip`:

```bash
# Ubuntu/Debian
sudo apt install xclip

# Fedora
sudo dnf install xclip

# Arch
sudo pacman -S xclip
```

### Linux (Wayland)

Los escritorios Linux modernos (Ubuntu 22.04+, Fedora 34+) a menudo usan Wayland por defecto. Instala `wl-clipboard`:

```bash
# Ubuntu/Debian
sudo apt install wl-clipboard

# Fedora
sudo dnf install wl-clipboard

# Arch
sudo pacman -S wl-clipboard
```

:::tip Cómo Veriftcar si estás en Wayland
```bash
echo $XDG_SESSION_TYPE
# "wayland" = Wayland, "x11" = X11, "tty" = no display server
```
:::

### WSL2

**No requiere configuración extra.** Hermes detecta WSL2 automáticamente (a través de `/proc/version`) y usa `powershell.exe` para acceder al Portapapeles de Windows a través de .NET's `System.Windows.Forms.Clipboard`. Esto está incorporado en la interoperabilidad de Windows de WSL2 — `powershell.exe` está disponible por defecto.

Los datos del Portapapeles se transfieren como PNG codificado en base64 sobre stdout, por lo que no se necesita conversión de ruta de archivo o archivos temporales.

:::info Nota de WSLg
Si estás ejecutando WSLg (WSL2 con soporte de GUI), Hermes intenta la ruta de PowerShell primero, luego retrocede a `wl-paste`. El puente de Portapapeles de WSLg solo admite formato BMP para imágenes — Hermes convierte automáticamente BMP a PNG usando Pillow (si está instalado) o el comando `convert` de ImageMagick.
:::

#### Verifica el acceso del Portapapeles WSL2

```bash
# 1. Verifica la detección de WSL
grep -i microsoft /proc/version

# 2. Verifica que PowerShell sea accesible
which powershell.exe

# 3. Copia una imagen, luego verifica
powershell.exe -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Clipboard]::ContainsImage()"
# Should print "True"
```

## ssh & Sesiones Remoto

**El pegado del Portapapeles no funciona a través de ssh.** Cuando te conectas por ssh a una máquina remota, la CLI de Hermes se ejecuta en el host remoto. Todas las Herramientas del Portapapeles (`xclip`, `wl-paste`, `powershell.exe`, `osascript`) leen el Portapapeles de la máquina en la que se ejecutan — que es el servidor remoto, no tu máquina local. Tu Portapapeles local no es accesible desde el lado remoto.

### Soluciones Alternativas para ssh

1. **Carga el archivo de imagen** — Guarda la imagen locálmente, cárgala en el servidor remoto a través de `scp`, el explorador de archivos de VSCode (arrastra y suelta) o cualquier método de transferencia de archivos. Luego ház referencia a ella por ruta. *(Se planifica un comando `/attach <filepath>` para una versión futura.)*

2. **Usa una URL** — Si la imagen es accesible en línea, simplemente pega la URL en tu mensaje. El agente puede usar `vision_analyze` para ver cualquier URL de imagen directamente.

3. **Reenvío X11** — Conectáte con `ssh -X` para reenviar X11. Esto permite que `xclip` en la máquina remota acceda a tu Portapapeles X11 local. Requiere un servidor X ejecutándose localmente (XQuartz en macOS, incorporado en escritorios X11 de Linux). Lento para imágenes grandes.

4. **Usa una plataforma de mensajería** — Envía imágenes a Hermes a través de Telegram, Discord, Slack o WhatsApp. Estas plataformas manejan la carga de imagen nativamente y no se ven afectadas por limitaciones de Portapapeles/terminal.

## Por Qué los Terminales No Pueden Pegar Imágenes

Esto es una fuente común de confusión, así que aquí está la explicación técnica:

Los terminales son interfaces **basadas en texto**. Cuando presionas Ctrl+V (o Cmd+V), el emulador de terminal:

1. Lee el Portapapeles en busca de contenido **texto**
2. Lo envuelve en secuencias de escape de [pegado entre corchetes](https://en.wikipedia.org/wiki/Bracketed-paste)
3. Lo envía a la aplicación a través de la secuencia de texto del terminal

Si el Portapapeles contiene solo una imagen (sin texto), el terminal no tiene nada que enviar. No hay una secuencia de escape de terminal estándar para datos de imagen binaria. El terminal simplemente no hace nada.

Es por eso que Hermes usa una verificación de Portapapeles separada — en lugar de recibir datos de imagen a través del evento de pegado de terminal, llama a herramientas a nivel del SO (`osascript`, `powershell.exe`, `xclip`, `wl-paste`) directamente a través de subproceso para leer el Portapapeles de forma independiente.

## Modelos Admitidos

El pegado de imagen funciona con cualquier modelo con capacidad de Visión. La imagen se envía como una URL de datos codificada en base64 en el formato de contenido de Visión de OpenAI:

```json
{
  "type": "image_url",
  "image_url": {
    "url": "data:image/png;base64,..."
  }
}
```

La mayoría de los modelos modernos admiten este formato, incluidos GPT-4 Visión, Claude (con Visión), Gemini y modelos multimodales de código abierto servidos a través de openrouter.
