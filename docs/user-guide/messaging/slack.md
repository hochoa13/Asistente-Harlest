---
sidebar_position: 4
title: "Slack"
description: "Configura Hermes Agent como un bot Slack usando Modo Socket"
---

# Slack Configuración

Connect Hermes Agent to Slack as a bot using Modo Socket. Modo Socket uses WebSockets instead of
public HTTP endpoints, so your Hermes instance doesn't need to be publicly accessible — it works
behind firewalls, on your laptop, or on a private server.

:::warning Classic Slack Apps Deprecated
Classic Slack apps (using RTM API) were **fully deprecated in March 2025**. Hermes uses the modern
Bolt SDK with Modo Socket. If you have an old classic app, you must create a new one following
the steps below.
:::

## Overview

| Component | Value |
|-----------|-------|
| **Library** | `@slack/bolt` (Modo Socket) |
| **Connection** | WebSocket — no public URL required |
| **Auth tokens needed** | Token del Bot (`xoxb-`) + App-Level Token (`xapp-`) |
| **User identification** | Slack Member IDs (e.g., `U01ABC2DEF3`) |

---

## Step 1: Create a Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click **Create New App**
3. Choose **From scratch**
4. Enter an app name (e.g., "Hermes Agent") and select your workspace
5. Click **Create App**

You'll land on the app's **Basic Information** page.

---

## Step 2: Configure Token del Bot Scopes

Navigate to **Features → OAuth & Permissions** in the sidebar. Scroll to **Scopes → Token del Bot Scopes** and add the following:

| Scope | Purpose |
|-------|---------|
| `chat:write` | Send mensajes as the bot |
| `app_mentions:read` | Detect when @mentioned in canals |
| `canals:history` | Read mensajes in public canals the bot is in |
| `canals:read` | List and get info about public canals |
| `grupos:history` | Read mensajes in private canals the bot is invited to |
| `im:history` | Read direct mensaje history |
| `im:read` | View basic DM info |
| `im:write` | Open and manage DMs |
| `usuarios:read` | Look up usuario information |
| `files:write` | Upload files (images, audio, documents) |

:::caution Missing scopes = missing features
Without `canals:history` and `grupos:history`, the bot **will not recibir mensajes in canals** —
it will only work in DMs. These are the most commonly missed scopes.
:::

**Optional scopes:**

| Scope | Purpose |
|-------|---------|
| `grupos:read` | List and get info about private canals |

---

## Step 3: Enable Modo Socket

Modo Socket lets the bot connect via WebSocket instead of requiring a public URL.

1. In the sidebar, go to **Settings → Modo Socket**
2. Toggle **Enable Modo Socket** to ON
3. You'll be prompted to create an **App-Level Token**:
   - Name it something like `hermes-socket` (the name doesn't matter)
   - Add the **`connections:write`** scope
   - Click **Generate**
4. **Copy the token** — it starts with `xapp-`. This is your `SLACK_APP_TOKEN`

:::tip
You can always find or regenerate app-level tokens under **Settings → Basic Information → App-Level Tokens**.
:::

---

## Step 4: Subscribe to Events

This step is critical — it controls what mensajes the bot can see.


1. In the sidebar, go to **Features → Event Subscriptions**
2. Toggle **Enable Events** to ON
3. Expand **Subscribe to bot events** and add:

| Event | Required? | Purpose |
|-------|-----------|---------|
| `mensaje.im` | **Yes** | Bot recibirs direct mensajes |
| `mensaje.canals` | **Yes** | Bot recibirs mensajes in **public** canals it's added to |
| `mensaje.grupos` | **Recommended** | Bot recibirs mensajes in **private** canals it's invited to |
| `app_mention` | **Yes** | Prevents Bolt SDK errors when bot is @mentioned |

4. Click **Save Changes** at the bottom of the page

:::danger Missing event subscriptions is the #1 setup issue
If the bot works in DMs but **not in canals**, you almost certainly forgot to add
`mensaje.canals` (for public canals) and/or `mensaje.grupos` (for private canals).
Without these events, Slack simply never delivers canal mensajes to the bot.
:::


---

## Step 5: Install App to Workspace

1. In the sidebar, go to **Settings → Install App**
2. Click **Install to Workspace**
3. Review the permisos and click **Allow**
4. After authorization, you'll see a **Bot User OAuth Token** starting with `xoxb-`
5. **Copy this token** — this is your `SLACK_BOT_TOKEN`

:::tip
If you change scopes or event subscriptions later, you **must reinstall the app** for the changes
to take effect. The Install App page will show a banner prompting you to do so.
:::

---

## Step 6: Find User IDs for the Allowlist

Hermes uses Slack **Member IDs** (not usuarionames or display names) for the allowlist.

To find a Member ID:

1. In Slack, click on the usuario's name or avatar
2. Click **View full profile**
3. Click the **⋮** (more) button
4. Select **Copy member ID**

Member IDs look like `U01ABC2DEF3`. You need your own Member ID at minimum.

---

## Step 7: Configure Hermes

Add the following to your `~/.hermes/.env` file:

```bash
# Required
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-token-here
SLACK_ALLOWED_USERS=U01ABC2DEF3              # Comma-separated Member IDs

# Optional
SLACK_HOME_CHANNEL=C01234567890              # Default canal for cron/scheduled mensajes
```

Or run the interactive setup:

```bash
hermes gateway setup    # Select Slack when prompted
```

Then start the gateway:

```bash
hermes gateway              # Foreground
hermes gateway install      # Install as a system service
```

---

## Step 8: Invite the Bot to Channels

After starting the gateway, you need to **invite the bot** to any canal where you want it to respond:

```
/invite @Hermes Agent
```

The bot will **not** automatically join canals. You must invite it to each canal individually.

---

## How the Bot Responds

Understanding how Hermes behaves in different contexts:

| Context | Behavior |
|---------|----------|
| **DMs** | Bot responds to every mensaje — no @mention needed |
| **Channels** | Bot **only responds when @mentioned** (e.g., `@Hermes Agent what time is it?`) |
| **Threads** | Bot replies in threads when the triggering mensaje is in a thread |

:::tip
In canals, always @mention the bot. Simply typing a mensaje without mentioning it will be ignored.
This is intentional — it prevents the bot from responding to every mensaje in busy canals.
:::

---


## Home Channel

Set `SLACK_HOME_CHANNEL` to a canal ID where Hermes will deliver scheduled mensajes,
cron job results, and other proactive notifications. To find a canal ID:

1. Right-click the canal name in Slack
2. Click **View canal details**
3. Scroll to the bottom — the Channel ID is shown there

```bash
SLACK_HOME_CHANNEL=C01234567890
```

Make sure the bot has been **invited to the canal** (`/invite @Hermes Agent`).

---

## Voice Messages

Hermes supports voice on Slack:

- **Incoming:** Voice/audio mensajes are automatically transcribed using Whisper (requires `VOICE_TOOLS_OPENAI_KEY`)
- **Outgoing:** TTS responses are sent as audio file attachments

---

## Solución de Problemas

| Problem | Solution |
|---------|----------|
| Bot doesn't respond to DMs | Verify `mensaje.im` is in your event subscriptions and the app is reinstalled |
| Bot works in DMs but not in canals | **Most common issue.** Add `mensaje.canals` and `mensaje.grupos` to event subscriptions, reinstall the app, and invite the bot to the canal with `/invite @Hermes Agent` |
| Bot doesn't respond to @mentions in canals | 1) Check `mensaje.canals` event is subscribed. 2) Bot must be invited to the canal. 3) Ensure `canals:history` scope is added. 4) Reinstall the app after scope/event changes |
| Bot ignores mensajes in private canals | Add both the `mensaje.grupos` event subscription and `grupos:history` scope, then reinstall the app and `/invite` the bot |
| "not_authed" or "invalid_auth" errors | Regenerate your Token del Bot and App Token, update `.env` |
| Bot responds but can't post in a canal | Invite the bot to the canal with `/invite @Hermes Agent` |
| "missing_scope" error | Add the required scope in OAuth & Permissions, then **reinstall** the app |
| Socket disconnects frequently | Check your network; Bolt auto-reconnects but unstable connections cause lag |
| Changed scopes/events but nothing changed | You **must reinstall** the app to your workspace after any scope or event subscription change |

### Quick Checklist

If the bot isn't working in canals, verify **all** of the following:

1. ✅ `mensaje.canals` event is subscribed (for public canals)
2. ✅ `mensaje.grupos` event is subscribed (for private canals)
3. ✅ `app_mention` event is subscribed
4. ✅ `canals:history` scope is added (for public canals)
5. ✅ `grupos:history` scope is added (for private canals)
6. ✅ App was **reinstalled** after adding scopes/events
7. ✅ Bot was **invited** to the canal (`/invite @Hermes Agent`)
8. ✅ You are **@mentioning** the bot in your mensaje

---

## Security

:::warning
**Always set `SLACK_ALLOWED_USERS`** with the Member IDs of authorized usuarios. Without this setting,
the gateway will **deny all mensajes** by default as a safety measure. Never share your bot tokens —
treat them like passwords.
:::

- Tokens should be stored in `~/.hermes/.env` (file permisos `600`)
- Rotate tokens periodically via the Slack app settings
- Audit who has access to your Hermes configuración directory
- Modo Socket means no public endpoint is exposed — one less attack surface
