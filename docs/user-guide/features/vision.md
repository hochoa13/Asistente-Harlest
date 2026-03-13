---
title: Visión & Image Paste
description: Paste images from your Portapapeles into the Hermes CLI for multimodal Visión analysis.
sidebar_label: Visión & Image Paste
sidebar_position: 7
---

# Visión & Image Paste

Hermes Agent supports **multimodal Visión** — you can paste images from your Portapapeles directly into the CLI and ask the agent to analyze, describe, or work with them. Images are sent to the model as base64-encoded content blocks, so any Visión-capable model can process them.

## How It Works

1. Copy an image to your Portapapeles (Captura de pantalla, Navegador image, etc.)
2. Attach it using one of the methods below
3. escribir your question and press Enter
4. The image appears as a `[📎 Image #1]` badge above the input
5. On submit, the image is sent to the model as a Visión content block

You can attach multiple images before sending — each gets its own badge. Press `Ctrl+C` to clear all attached images.

Images are saved to `~/.hermes/images/` as PNG files with timestamped filenames.

## métodos de pegado

How you attach an image depends on your terminal entorno. Not all methods work everywhere — here's the full breakdown:

### `/paste` comando

**The most reliable method. Works everywhere.**

```
/paste
```

escribir `/paste` and press Enter. Hermes checks your Portapapeles for an image and attaches it. This works in every entorno because it explicitly calls the Portapapeles backend — no terminal keybinding interception to worry about.

### Ctrl+V / Cmd+V (Bracketed Paste)

When you paste text that's on the Portapapeles alongside an image, Hermes automatically checks for an image too. This works when:
- Your Portapapeles contains **both text and an image** (some apps put both on the Portapapeles when you copy)
- Your terminal supports bracketed paste (most modern terminals do)

:::Advertencia
If your Portapapeles has **only an image** (no text), Ctrl+V does nothing in most terminals. Terminals can only paste text — there's no standard mechanism to paste binary image data. Usar `/paste` or Alt+V instead.
:::

### Alt+V

Alt key combinations pass through most terminal emulators (they're sent as ESC + key rather than being intercepted). Press `Alt+V` to Verificar the Portapapeles for an image.

:::caution
**Does not work in VSCode's integrated terminal.** VSCode intercepts many Alt+key combos for its own UI. Usar `/paste` instead.
:::

### Ctrl+V (Raw — Linux Only)

On Linux desktop terminals (GNOME Terminal, Konsole, Alacritty, etc.), `Ctrl+V` is **not** the paste shortcut — `Ctrl+Shift+V` is. So `Ctrl+V` sends a raw byte to the application, and Hermes catches it to Verificar the Portapapeles. This only works on Linux desktop terminals with X11 or Wayland Portapapeles access.

## compatibilidad de plataforma

| entorno | `/paste` | Ctrl+V text+image | Alt+V | Notes |
|---|:---:|:---:|:---:|---|
| **macOS Terminal / iTerm2** | ✅ | ✅ | ✅ | Best experience — `osascript` always available |
| **Linux X11 desktop** | ✅ | ✅ | ✅ | Requires `xclip` (`apt Instalar xclip`) |
| **Linux Wayland desktop** | ✅ | ✅ | ✅ | Requires `wl-paste` (`apt Instalar wl-Portapapeles`) |
| **WSL2 (Windows Terminal)** | ✅ | ✅¹ | ✅ | Uses `powershell.exe` — no extra Instalar needed |
| **VSCode Terminal (local)** | ✅ | ✅¹ | ❌ | VSCode intercepts Alt+key |
| **VSCode Terminal (ssh)** | ❌² | ❌² | ❌ | Remote Portapapeles not accessible |
| **ssh terminal (any)** | ❌² | ❌² | ❌² | Remote Portapapeles not accessible |

¹ Only when Portapapeles has both text and an image (image-only Portapapeles = nothing happens)
² See [ssh & Remote Sesiones](#ssh--remote-sessions) below

## específico de plataforma Configuración

### macOS

**No Configuración required.** Hermes uses `osascript` (built into macOS) to read the Portapapeles. For faster performance, optionally Instalar `pngpaste`:

```bash
brew install pngpaste
```

### Linux (X11)

Instalar `xclip`:

```bash
# Ubuntu/Debian
sudo apt install xclip

# Fedora
sudo dnf install xclip

# Arch
sudo pacman -S xclip
```

### Linux (Wayland)

Modern Linux desktops (Ubuntu 22.04+, Fedora 34+) often Usar Wayland by default. Instalar `wl-Portapapeles`:

```bash
# Ubuntu/Debian
sudo apt install wl-clipboard

# Fedora
sudo dnf install wl-clipboard

# Arch
sudo pacman -S wl-clipboard
```

:::Consejo Cómo Verificar if you're on Wayland
```bash
echo $XDG_SESSION_TYPE
# "wayland" = Wayland, "x11" = X11, "tty" = no display server
```
:::

### WSL2

**No extra Configuración required.** Hermes detects WSL2 automatically (via `/proc/version`) and uses `powershell.exe` to access the Windows Portapapeles through .NET's `System.Windows.Forms.Portapapeles`. This is built into WSL2's Windows interop — `powershell.exe` is available by default.

The Portapapeles data is transferred as base64-encoded PNG over stdout, so no archivo ruta conversion or temp files are needed.

:::Información WSLg Note
If you're running WSLg (WSL2 with GUI support), Hermes tries the PowerShell ruta first, then falls back to `wl-paste`. WSLg's Portapapeles bridge only supports BMP format for images — Hermes auto-converts BMP to PNG using Pillow (if installed) or ImageMagick's `convert` comando.
:::

#### Verify WSL2 Portapapeles access

```bash
# 1. Check WSL detection
grep -i microsoft /proc/version

# 2. Check PowerShell is accessible
which powershell.exe

# 3. Copy an image, then check
powershell.exe -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Clipboard]::ContainsImage()"
# Should print "True"
```

## ssh & Remote Sesiones

**Portapapeles paste does not work over ssh.** When you ssh into a remote machine, the Hermes CLI runs on the remote host. All Portapapeles Herramientas (`xclip`, `wl-paste`, `powershell.exe`, `osascript`) read the Portapapeles of the machine they Ejecutar on — which is the remote server, not your local machine. Your local Portapapeles is inaccessible from the remote side.

### Workarounds for ssh

1. **Upload the image archivo** — Save the image locally, upload it to the remote server via `scp`, VSCode's archivo explorer (drag-and-drop), or any archivo transfer method. Then reference it by ruta. *(A `/attach <filepath>` comando is planned for a future release.)*

2. **Usar a URL** — If the image is accessible online, just paste the URL in your message. The agent can Usar `vision_analyze` to look at any image URL directly.

3. **X11 forwarding** — Connect with `ssh -X` to forward X11. This lets `xclip` on the remote machine access your local X11 Portapapeles. Requires an X server running locally (XQuartz on macOS, built-in on Linux X11 desktops). Slow for large images.

4. **Usar a messaging platform** — Send images to Hermes via Telegram, Discord, Slack, or WhatsApp. These platforms handle image upload natively and are not affected by Portapapeles/terminal limitations.

## Why Terminals Can't Paste Images

This is a common source of confusion, so here's the technical explanation:

Terminals are **text-based** interfaces. When you press Ctrl+V (or Cmd+V), the terminal emulator:

1. Reads the Portapapeles for **text content**
2. Wraps it in [bracketed paste](https://en.wikipedia.org/wiki/Bracketed-paste) escape sequences
3. Sends it to the application through the terminal's text stream

If the Portapapeles contains only an image (no text), the terminal has nothing to send. There is no standard terminal escape sequence for binary image data. The terminal simply does nothing.

This is why Hermes uses a separate Portapapeles Verificar — instead of receiving image data through the terminal paste event, it calls OS-level Herramientas (`osascript`, `powershell.exe`, `xclip`, `wl-paste`) directly via subproceso to read the Portapapeles independently.

## Supported Models

Image paste works with any Visión-capable model. The image is sent as a base64-encoded data URL in the OpenAI Visión content format:

```json
{
  "type": "image_url",
  "image_url": {
    "url": "data:image/png;base64,..."
  }
}
```

Most modern models support this format, including GPT-4 Visión, Claude (with Visión), Gemini, and open-source multimodal models served through openrouter.
