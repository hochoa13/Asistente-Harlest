---
sidebar_position: 1
title: "Telegram"
description: "Configura Hermes Agent como un bot de Telegram"
---

# Telegram Configuración

Hermes Agent integrates with Telegram as a full-featured conversational bot. Once connected, you can chat with your agent from any device, enviar voice memos that get auto-transcribed, recibir scheduled task results, and use the agent in grupo chats. The integration is built on [python-telegram-bot](https://python-telegram-bot.org/) and supports text, voice, images, and file attachments.

## Step 1: Create a Bot via BotFather

Every Telegram bot requires an API token issued by [@BotFather](https://t.me/BotFather), Telegram's official bot management tool.

1. Open Telegram and search for **@BotFather**, or visit [t.me/BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Choose a **display name** (e.g., "Hermes Agent") — this can be anything
4. Choose a **usuarioname** — this must be unique and end in `bot` (e.g., `my_hermes_bot`)
5. BotFather replies with your **API token**. It looks like this:

```
123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
```

:::warning
Keep your bot token secret. Anyone with this token can control your bot. If it leaks, revoke it immediately via `/revoke` in BotFather.
:::

## Step 2: Customize Your Bot (Optional)

These BotFather commands improve the usuario experience. Message @BotFather and use:

| Command | Purpose |
|---------|---------|
| `/setdescription` | The "What can this bot do?" text shown before a usuario starts chatting |
| `/setabouttext` | Short text on the bot's profile page |
| `/setusuariopic` | Upload an avatar for your bot |
| `/setcommands` | Define the command menu (the `/` button in chat) |
| `/setprivacy` | Control whether the bot sees all grupo mensajes (see Step 3) |

:::tip
For `/setcommands`, a useful starting set:

```
help - Show help information
new - Start a new conversation
sethome - Set this chat as the home canal
```
:::

## Step 3: Privacy Mode (Critical for Groups)

Telegram bots have a **privacy mode** that is **enabled by default**. This is the single most common source of confusion when using bots in grupos.

**With privacy mode ON**, your bot can only see:
- Messages that start with a `/` command
- Replies directly to the bot's own mensajes
- Service mensajes (member joins/leaves, pinned mensajes, etc.)
- Messages in canals where the bot is an admin

**With privacy mode OFF**, the bot recibirs every mensaje in the grupo.

### How to disable privacy mode

1. Message **@BotFather**
2. Send `/mybots`
3. Select your bot
4. Go to **Bot Settings → Group Privacy → Turn off**

:::warning
**You must remove and re-add the bot to any grupo** after changing the privacy setting. Telegram caches the privacy state when a bot joins a grupo, and it will not update until the bot is removed and re-added.
:::

:::tip
An alternative to disabling privacy mode: promote the bot to **grupo admin**. Admin bots always recibir all mensajes regardless of the privacy setting, and this avoids needing to toggle the global privacy mode.
:::

## Step 4: Find Your User ID

Hermes Agent uses numeric Telegram usuario IDs to control access. Your usuario ID is **not** your usuarioname — it's a number like `123456789`.

**Method 1 (recommended):** Message [@usuarioinfobot](https://t.me/usuarioinfobot) — it instantly replies with your usuario ID.

**Method 2:** Message [@get_id_bot](https://t.me/get_id_bot) — another reliable option.

Save this number; you'll need it for the next step.

## Step 5: Configure Hermes

### Option A: Interactive Configuración (Recommended)

```bash
hermes gateway setup
```

Select **Telegram** when prompted. The wizard asks for your bot token and allowed usuario IDs, then writes the configuraciónuration for you.

### Option B: Manual Configuración

Add the following to `~/.hermes/.env`:

```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
TELEGRAM_ALLOWED_USERS=123456789    # Comma-separated for multiple usuarios
```

### Start the Gateway

```bash
hermes gateway
```

The bot should come online within seconds. Send it a mensaje on Telegram to verify.

## Home Channel

Use the `/sethome` command in any Telegram chat (DM or grupo) to designate it as the **home canal**. Scheduled tasks (cron jobs) deliver their results to this canal.

You can also set it manually in `~/.hermes/.env`:

```bash
TELEGRAM_HOME_CHANNEL=-1001234567890
TELEGRAM_HOME_CHANNEL_NAME="My Notes"
```

:::tip
Group chat IDs are negative numbers (e.g., `-1001234567890`). Your personal DM chat ID is the same as your usuario ID.
:::

## Voice Messages

### Incoming Voice (Speech-to-Text)

Voice mensajes you enviar on Telegram are automatically transcribed using OpenAI's Whisper API and injected as text into the conversation. This requires `VOICE_TOOLS_OPENAI_KEY` in `~/.hermes/.env`.

### Outgoing Voice (Text-to-Speech)

When the agent generates audio via TTS, it's delivered as native Telegram **voice bubbles** — the round, inline-playable kind.

- **OpenAI and ElevenLabs** produce Opus natively — no extra setup needed
- **Edge TTS** (the default free provider) outputs MP3 and requires **ffmpeg** to convert to Opus:

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

Without ffmpeg, Edge TTS audio is sent as a regular audio file (still playable, but uses the rectangular player instead of a voice bubble).

Configure the TTS provider in your `configuración.yaml` under the `tts.provider` key.

## Group Chat Usage

Hermes Agent works in Telegram grupo chats with a few considerations:

- **Privacy mode** determines what mensajes the bot can see (see [Step 3](#step-3-privacy-mode-critical-for-grupos))
- When privacy mode is on, **@mention the bot** (e.g., `@my_hermes_bot what's the weather?`) or **reply to its mensajes** to interact
- When privacy mode is off (or bot is admin), the bot sees all mensajes and can participate naturally
- `TELEGRAM_ALLOWED_USERS` still applies — only authorized usuarios can trigger the bot, even in grupos

## Recent Bot API Features (2024–2025)

- **Privacy policy:** Telegram now requires bots to have a privacy policy. Set one via BotFather with `/setprivacy_policy`, or Telegram may auto-generate a placeholder. This is particularly important if your bot is public-facing.
- **Message streaming:** Bot API 9.x added support for streaming long responses, which can improve perceived latency for lengthy agent replies.

## Solución de Problemas

| Problem | Solution |
|---------|----------|
| Bot not responding at all | Verify `TELEGRAM_BOT_TOKEN` is correct. Check `hermes gateway` logs for errors. |
| Bot responds with "unauthorized" | Your usuario ID is not in `TELEGRAM_ALLOWED_USERS`. Double-check with @usuarioinfobot. |
| Bot ignores grupo mensajes | Privacy mode is likely on. Disable it (Step 3) or make the bot a grupo admin. **Remember to remove and re-add the bot after changing privacy.** |
| Voice mensajes not transcribed | Check that `VOICE_TOOLS_OPENAI_KEY` is set and valid in `~/.hermes/.env`. |
| Voice replies are files, not bubbles | Install `ffmpeg` (needed for Edge TTS Opus conversion). |
| Bot token revoked/invalid | Generate a new token via `/revoke` then `/newbot` or `/token` in BotFather. Update your `.env` file. |

## Exec Approval

When the agent tries to run a potentially dangerous command, it asks you for approval in the chat:

> ⚠️ This command is potentially dangerous (recursive delete). Reply "yes" to approve.

Reply "yes"/"y" to approve or "no"/"n" to deny.

## Security

:::warning
Always set `TELEGRAM_ALLOWED_USERS` to restrict who can interact with your bot. Without it, the gateway denies all usuarios by default as a safety measure.
:::

Never share your bot token publicly. If compromised, revoke it immediately via BotFather's `/revoke` command.

Para más detalles, ver the [Security documentation](/usuario-guía/security). You can also use [DM pairing](/usuario-guía/messaging#dm-pairing-alternative-to-allowlists) for a more dynamic approach to usuario authorization.
