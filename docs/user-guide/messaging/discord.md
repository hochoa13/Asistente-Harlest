---
sidebar_position: 3
title: "Discord"
description: "Configura Hermes Agent como un bot Discord"
---

# Discord Configuración

Hermes Agent integrates with Discord as a bot, letting you chat with your AI assistant through direct mensajes or server canals. The bot recibirs your mensajes, processes them through the Hermes Agent pipeline (including tool use, memory, and reasoning), and responds in real time. It supports text, voice mensajes, file attachments, and slash commands.

This guía walks you through the full setup process — from creating your bot on Discord's Developer Portal to enviaring your first mensaje.

## Step 1: Create a Discord Application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and sign in with your Discord account.
2. Click **New Application** in the top-right corner.
3. Enter a name for your application (e.g., "Hermes Agent") and accept the Developer Terms of Service.
4. Click **Create**.

You'll land on the **General Information** page. Note the **Application ID** — you'll need it later to build the invite URL.

## Step 2: Create the Bot

1. In the left sidebar, click **Bot**.
2. Discord automatically creates a bot usuario for your application. You'll see the bot's usuarioname, which you can customize.
3. Under **Authorization Flow**:
   - Set **Public Bot** to **OFF** — this prevents other people from inviting your bot to their servers.
   - Leave **Require OAuth2 Code Grant** set to **OFF**.

:::tip
You can set a custom avatar and banner for your bot on this page. This is what usuarios will see in Discord.
:::

## Step 3: Enable Privileged Gateway Intenciones

This is the most critical step in the entire setup. Without the correct intents enabled, your bot will connect to Discord but **will not be able to read mensaje content**.

On the **Bot** page, scroll down to **Privileged Gateway Intenciones**. You'll see three toggles:

| Intent | Purpose | Required? |
|--------|---------|-----------|
| **Presence Intent** | See usuario online/offline status | Optional |
| **Server Members Intent** | Access the member list | Optional |
| **Message Content Intent** | Read the text content of mensajes | **Required** |

**Enable Message Content Intent** by toggling it **ON**. Without this, your bot recibirs mensaje events but the mensaje text is empty — the bot literally cannot see what you typed.

:::warning[This is the #1 reason Discord bots don't work]
If your bot is online but never responds to mensajes, the **Message Content Intent** is almost certainly disabled. Go back to the [Developer Portal](https://discord.com/developers/applications), select your application → Bot → Privileged Gateway Intenciones, and make sure **Message Content Intent** is toggled ON. Click **Save Changes**.
:::

**Regarding server count:**
- If your bot is in **fewer than 100 servers**, you can simply toggle intents on and off freely.
- If your bot is in **100 or more servers**, Discord requires you to submit a verification application to use privileged intents. For personal use, this is not a concern.

Click **Save Changes** at the bottom of the page.

## Step 4: Get the Token del Bot

The bot token is the credential Hermes Agent uses to log in as your bot. Still on the **Bot** page:

1. Under the **Token** section, click **Reset Token**.
2. If you have two-factor autenticación enabled on your Discord account, enter your 2FA code.
3. Discord will display your new token. **Copy it immediately.**

:::warning[Token shown only once]
The token is only displayed once. If you lose it, you'll need to reset it and generate a new one. Never share your token publicly or commit it to Git — anyone with this token has full control of your bot.
:::

Store the token somewhere safe (a password manager, for example). You'll need it in Step 8.

## Step 5: Generate the Invite URL

You need an OAuth2 URL to invite the bot to your server. There are two ways to do this:

### Option A: Using the Instalación Tab (Recommended)

1. In the left sidebar, click **Instalación**.
2. Under **Instalación Contexts**, enable **Guild Install**.
3. For **Install Link**, select **Discord Provided Link**.
4. Under **Default Install Settings** for Guild Install:
   - **Scopes**: select `bot` and `applications.commands`
   - **Permissions**: select the permisos listed below.

### Option B: Manual URL

You can construct the invite URL directly using this format:

```
https://discord.com/oauth2/authorize?client_id=YOUR_APP_ID&scope=bot+applications.commands&permisos=274878286912
```

Replace `YOUR_APP_ID` with the Application ID from Step 1.

### Required Permissions

These are the minimum permisos your bot needs:

- **View Channels** — see the canals it has access to
- **Send Messages** — respond to your mensajes
- **Embed Links** — format rich responses
- **Attach Files** — enviar images, audio, and file outputs
- **Read Message History** — maintain conversation context

### Recommended Additional Permissions

- **Send Messages in Threads** — respond in thread conversations
- **Add Reactions** — react to mensajes for acknowledgment

### Permission Integers

| Level | Permissions Integer | What's Included |
|-------|-------------------|-----------------|
| Minimal | `117760` | View Channels, Send Messages, Read Message History, Attach Files |
| Recommended | `274878286912` | All of the above plus Embed Links, Send Messages in Threads, Add Reactions |

## Step 6: Invite to Your Server

1. Open the invite URL in your browser (from the Instalación tab or the manual URL you constructed).
2. In the **Add to Server** dropdown, select your server.
3. Click **Continue**, then **Authorize**.
4. Complete the CAPTCHA if prompted.

:::info
You need the **Manage Server** permiso on the Discord server to invite a bot. If you don't see your server in the dropdown, ask a server admin to use the invite link instead.
:::

After authorizing, the bot will appear in your server's member list (it will show as offline until you start the Hermes gateway).

## Step 7: Find Your Discord User ID

Hermes Agent uses your Discord User ID to control who can interact with the bot. To find it:

1. Open Discord (desktop or web app).
2. Go to **Settings** → **Advanced** → toggle **Developer Mode** to **ON**.
3. Close settings.
4. Right-click your own usuarioname (in a mensaje, the member list, or your profile) → **Copy User ID**.

Your User ID is a long number like `284102345871466496`.

:::tip
Developer Mode also lets you copy **Channel IDs** and **Server IDs** the same way — right-click the canal or server name and select Copy ID. You'll need a Channel ID if you want to set a home canal manually.
:::

## Step 8: Configure Hermes Agent

### Option A: Interactive Configuración (Recommended)

Run the guíad setup command:

```bash
hermes gateway setup
```

Select **Discord** when prompted, then paste your bot token and usuario ID when asked.

### Option B: Manual Configuración

Add the following to your `~/.hermes/.env` file:

```bash
# Required
DISCORD_BOT_TOKEN=your-bot-token-from-developer-portal
DISCORD_ALLOWED_USERS=284102345871466496

# Multiple allowed usuarios (comma-separated)
# DISCORD_ALLOWED_USERS=284102345871466496,198765432109876543
```

### Start the Gateway

Once configuraciónured, start the Discord gateway:

```bash
hermes gateway
```

The bot should come online in Discord within a few seconds. Send it a mensaje — either a DM or in a canal it can see — to test.

:::tip
You can run `hermes gateway` in the background or as a systemd service for persistent operation. Ver la deployment docs for details.
:::

## Home Channel

You can designate a "home canal" where the bot enviars proactive mensajes (such as cron job output, reminders, and notifications). There are two ways to set it:

### Using the Slash Command

Type `/sethome` in any Discord canal where the bot is present. That canal becomes the home canal.

### Manual Configuración

Add these to your `~/.hermes/.env`:

```bash
DISCORD_HOME_CHANNEL=123456789012345678
DISCORD_HOME_CHANNEL_NAME="#bot-updates"
```

Replace the ID with the actual canal ID (right-click → Copy Channel ID with Developer Mode on).

## Bot Behavior

- **Server canals**: The bot responds to all mensajes from allowed usuarios in canals it can access. It does **not** require a mention or prefix — any mensaje from an allowed usuario is treated as a prompt.
- **Direct mensajes**: DMs always work, even without the Message Content Intent enabled (Discord exempts DMs from this requirement). However, you should still enable the intent for server canal support.
- **Conversations**: Each canal or DM maintains its own conversation context.

## Voice Messages

Hermes Agent supports Discord voice mensajes:

- **Incoming voice mensajes** are automatically transcribed using Whisper (requires `VOICE_TOOLS_OPENAI_KEY` to be set in your environment).
- **Text-to-speech**: When TTS is enabled, the bot can enviar spoken responses as MP3 file attachments.

## Solución de Problemas

### Bot is online but not responding to mensajes

**Cause**: Message Content Intent is disabled.

**Fix**: Go to [Developer Portal](https://discord.com/developers/applications) → your app → Bot → Privileged Gateway Intenciones → enable **Message Content Intent** → Save Changes. Restart the gateway.

### "Disallowed Intenciones" error on startup

**Cause**: Your code requests intents that aren't enabled in the Developer Portal.

**Fix**: Enable all three Privileged Gateway Intenciones (Presence, Server Members, Message Content) in the Bot settings, then restart.

### Bot can't see mensajes in a specific canal

**Cause**: The bot's role doesn't have permiso to view that canal.

**Fix**: In Discord, go to the canal's settings → Permissions → add the bot's role with **View Channel** and **Read Message History** enabled.

### 403 Forbidden errors

**Cause**: The bot is missing required permisos.

**Fix**: Re-invite the bot with the correct permisos using the URL from Step 5, or manually adjust the bot's role permisos in Server Settings → Roles.

### Bot is offline

**Cause**: The Hermes gateway isn't running, or the token is incorrect.

**Fix**: Check that `hermes gateway` is running. Verify `DISCORD_BOT_TOKEN` in your `.env` file. If you recently reset the token, update it.

### "User not allowed" / Bot ignores you

**Cause**: Your User ID isn't in `DISCORD_ALLOWED_USERS`.

**Fix**: Add your User ID to `DISCORD_ALLOWED_USERS` in `~/.hermes/.env` and restart the gateway.

## Security

:::warning
Always set `DISCORD_ALLOWED_USERS` to restrict who can interact with the bot. Without it, the gateway denies all usuarios by default as a safety measure. Only add User IDs of people you trust — authorized usuarios have full access to the agent's capabilities, including tool use and system access.
:::

For more information on securing your Hermes Agent deployment, see the [Security Guide](../security.md).
