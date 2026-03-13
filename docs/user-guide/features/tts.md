---
sidebar_position: 9
title: "voz & TTS"
description: "Texto a Voz and voz message transcription across all platforms"
---

# voz & TTS

Hermes Agent supports both Texto a Voz output and voz message transcription across all messaging platforms.

## Texto a Voz

Convert text to Habla with three Proveedores:

| Provider | Quality | Cost | clave API |
|----------|---------|------|---------|
| **Edge TTS** (default) | Good | Free | None needed |
| **ElevenLabs** | Excellent | Paid | `ELEVENLABS_API_KEY` |
| **OpenAI TTS** | Good | Paid | `VOICE_TOOLS_OPENAI_KEY` |

### entrega de plataforma

| Platform | Delivery | Format |
|----------|----------|--------|
| Telegram | voz bubble (plays inline) | Opus `.ogg` |
| Discord | Audio archivo attachment | MP3 |
| WhatsApp | Audio archivo attachment | MP3 |
| CLI | Saved to `~/.hermes/audio_cache/` | MP3 |

### Configuración

```yaml
# In ~/.hermes/config.yaml
tts:
  provider: "edge"              # "edge" | "elevenlabs" | "openai"
  edge:
    voice: "en-US-AriaNeural"   # 322 voices, 74 languages
  elevenlabs:
    voice_id: "pNInz6obpgDQGcFmaJgB"  # Adam
    model_id: "eleven_multilingual_v2"
  openai:
    model: "gpt-4o-mini-tts"
    voice: "alloy"              # alloy, echo, fable, onyx, nova, shimmer
```

### Telegram voz Bubbles & ffmpeg

Telegram voz bubbles require Opus/OGG Audio format:

- **OpenAI and ElevenLabs** produce Opus natively — no extra Configuración
- **Edge TTS** (default) outputs MP3 and needs **ffmpeg** to convert:

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Fedora
sudo dnf install ffmpeg
```

Without ffmpeg, Edge TTS Audio is sent as a regular Audio archivo (playable, but shows as a rectangular player instead of a voz bubble).

:::Consejo
If you want voz bubbles without installing ffmpeg, switch to the OpenAI or ElevenLabs provider.
:::

## voz Message Transcription

voz messages sent on Telegram, Discord, WhatsApp, or Slack are automatically transcribed and injected as text into the conversation. The agent sees the transcript as normal text.

| Provider | Model | Quality | Cost |
|----------|-------|---------|------|
| **OpenAI Whisper** | `whisper-1` (default) | Good | Low |
| **OpenAI GPT-4o** | `gpt-4o-mini-transcribe` | Better | Medium |
| **OpenAI GPT-4o** | `gpt-4o-transcribe` | Best | Higher |

Requires `VOICE_TOOLS_OPENAI_KEY` in `~/.hermes/.env`.

### Configuración

```yaml
# In ~/.hermes/config.yaml
stt:
  enabled: true
  model: "whisper-1"
```
