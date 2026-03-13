---
sidebar_position: 9
title: "Voz y TTS"
description: "Texto a voz y transcripción de mensajes de voz en todas las plataformas"
---

# Voz y TTS

Hermes Agent admite tanto la salida de texto a voz como la transcripción de mensajes de voz en todas las plataformas de mensajería.

## Texto a Voz

Convierte texto a voz con tres proveedores:

| Proveedor | Calidad | Costo | Clave API |
|----------|---------|------|---------|
| **Edge TTS** (predeterminado) | Buena | Gratis | Ninguno necesario |
| **ElevenLabs** | Excelente | Pagado | `ELEVENLABS_API_KEY` |
| **OpenAI TTS** | Buena | Pagado | `VOICE_TOOLS_OPENAI_KEY` |

### Entrega por Plataforma

| Plataforma | Entrega | Formato |
|----------|----------|--------|
| Telegram | Burbuja de voz (reproduce en línea) | Opus `.ogg` |
| Discord | Archivo adjunto de audio | MP3 |
| WhatsApp | Archivo adjunto de audio | MP3 |
| CLI | Guardado en `~/.hermes/audio_cache/` | MP3 |

### Configuración

```yaml
# En ~/.hermes/config.yaml
tts:
  provider: "edge"              # "edge" | "elevenlabs" | "openai"
  edge:
    voice: "en-US-AriaNeural"   # 322 voces, 74 idiomas
  elevenlabs:
    voice_id: "pNInz6obpgDQGcFmaJgB"  # Adam
    model_id: "eleven_multilingual_v2"
  openai:
    model: "gpt-4o-mini-tts"
    voice: "alloy"              # alloy, echo, fable, onyx, nova, shimmer
```

### Burbujas de Voz en Telegram y ffmpeg

Las burbujas de voz en Telegram requieren formato de audio Opus/OGG:

- **OpenAI y ElevenLabs** producen Opus nativamente — sin configuración extra
- **Edge TTS** (predeterminado) produce MP3 y necesita **ffmpeg** para convertir:

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Fedora
sudo dnf install ffmpeg
```

Sin ffmpeg, el audio de Edge TTS se envía como archivo de audio normal (reproducible, pero se muestra como un reproductor rectangular en lugar de una burbuja de voz).

:::consejo
Si quieres burbujas de voz sin instalar ffmpeg, cambia al proveedor OpenAI o ElevenLabs.
:::

## Transcripción de Mensajes de Voz

Los mensajes de voz enviados en Telegram, Discord, WhatsApp o Slack se transcriben automáticamente e inyectan como texto en la conversación. El agente ve la transcripción como texto normal.

| Proveedor | Modelo | Calidad | Costo |
|----------|-------|---------|------|
| **OpenAI Whisper** | `whisper-1` (predeterminado) | Buena | Bajo |
| **OpenAI GPT-4o** | `gpt-4o-mini-transcribe` | Mejor | Medio |
| **OpenAI GPT-4o** | `gpt-4o-transcribe` | Mejor | Más alto |

Requiere `VOICE_TOOLS_OPENAI_KEY` en `~/.hermes/.env`.

### Configuración

```yaml
# En ~/.hermes/config.yaml
stt:
  enabled: true
  model: "whisper-1"
```
