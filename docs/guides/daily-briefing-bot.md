---
sidebar_position: 2
title: "Tutorial: Bot de Resumen Diario"
description: "Construye un bot de resumen diario automatizado que investiga temas, resume hallazgos y los entrega a Telegram o Discord cada mañana"
---

# Tutorial: Construye un Bot de Resumen Diario

En este tutorial, construirás un bot de resumen personal que se despierta cada mañana, investiga temas que te importan, resume los hallazgos y entrega un resumen conciso directo a tu Telegram o Discord.

Al final, tendrás un flujo de trabajo completamente automatizado que combina **búsqueda web**, **programación cron**, **delegación** y **entrega de mensajes** — sin código requerido.

## Qué Estamos Construyendo

Aquí está el flujo:

1. **8:00 AM** — El planificador cron dispara tu trabajo
2. **Hermes se inicia** con una sesión nueva del agente y tu prompt
3. **Búsqueda web** obtiene las últimas noticias sobre tus temas
4. **Resumen** lo destila en un formato de informe limpio
5. **Entrega** envía el informe a tu Telegram o Discord

Todo funciona automáticamente. Solo lees tu informe con tu café matutino.

## Requisitos Previos

Antes de comenzar, asegúrate de tener:

- **Hermes Agent instalado** — consulta la [guía de instalación](/docs/getting-started/installation)
- **Gateway en ejecución** — el demonio de puerta de enlace maneja la ejecución de cron:
  ```bash
  hermes gateway install   # Instalar como servicio del sistema (recomendado)
  # o
  hermes gateway           # Ejecutar en primer plano
  ```
- **Clave API de Firecrawl** — establece `FIRECRAWL_API_KEY` en tu entorno para búsqueda web
- **Mensajería configurada** (opcional pero recomendado) — [Telegram](/docs/user-guide/messaging/telegram) o Discord configurado con un canal de inicio

:::tip Sin mensajería, sin problema
Aún puedes seguir este tutorial usando `deliver: "local"`. Los resúmenes se guardarán en `~/.hermes/cron/output/` y puedes leerlos en cualquier momento.
:::

## Paso 1: Prueba el Flujo Manualmente

Antes de automatizar nada, asegurémonos de que el resumen funciona. Inicia una sesión de chat:

```bash
hermes
```

Luego ingresa este prompt:

```
Busca las últimas noticias sobre agentes de IA y LLMs de código abierto.
Resume las 3 historias principales en un formato de resumen conciso con enlaces.
```

Hermes buscará en la web, leerá los resultados y producirá algo como:

```
☀️ Tu Resumen de IA — 8 de Marzo, 2026

1. Qwen 3 lanzado con 235B parámetros
   El último modelo de peso abierto de Alibaba coincide con GPT-4.5 en varios
   puntos de referencia mientras permanece completamente de código abierto.
   → https://qwenlm.github.io/blog/qwen3/

2. LangChain Lanza Estándar de Protocolo de Agentes
   Un nuevo estándar abierto para comunicación entre agentes gana
   adopción de 15 marcos principales en su primera semana.
   → https://blog.langchain.dev/agent-protocol/

3. Comienza la Aplicación de la Ley de IA de la UE para Modelos de Propósito General
   Los primeros cronogramas de cumplimiento se cumplen, con modelos de código abierto
   recibiendo exenciones por debajo del umbral de 10M parámetros.
   → https://artificialintelligenceact.eu/updates/

---
3 historias • Fuentes buscadas: 8 • Generado por Hermes Agent
```

Si esto funciona, estás listo para automatizarlo.

:::tip Itera en el formato
Prueba diferentes prompts hasta obtener un resultado que te encante. Añade instrucciones como "usa encabezados con emoji" o "mantén cada resumen bajo 2 oraciones." Lo que decidas se incluye en el trabajo cron.
:::

## Paso 2: Crea el Trabajo Cron

Ahora programemos esto para ejecutarse automáticamente cada mañana. Puedes hacerlo de dos maneras.

### Opción A: Lenguaje Natural (en chat)

Solo dile a Hermes lo que quieres:

```
Cada mañana a las 8am, busca las últimas noticias sobre agentes de IA
y LLMs de código abierto. Resume las 3 historias principales en un
resumen conciso con enlaces. Usa un tono amable y profesional. Entrega a Telegram.
```

Hermes will create the cron job for you using the `schedule_cronjob` tool.

### Option B: CLI Slash Command

Use the `/cron` command for more control:

```
/cron add "0 8 * * *" "Search the web for the latest news about AI agents and open source LLMs. Find at least 5 recent articles from the past 24 hours. Summarize the top 3 most important stories in a concise daily briefing format. For each story include: a clear headline, a 2-sentence summary, and the source URL. Use a friendly, professional tone. Format with emoji bullet points and end with a total story count."
```

### The Golden Rule: Self-Contained Prompts

:::warning Critical concept
Cron jobs run in a **completely fresh session** — no memory of your previous conversations, no context about what you "set up earlier." Your prompt must contain **everything** the agent needs to do the job.
:::

**Bad prompt:**
```
Do my usual morning briefing.
```

**Good prompt:**
```
Search the web for the latest news about AI agents and open source LLMs.
Find at least 5 recent articles from the past 24 hours. Summarize the
top 3 most important stories in a concise daily briefing format. For each
story include: a clear headline, a 2-sentence summary, and the source URL.
Use a friendly, professional tone. Format with emoji bullet points.
```

The good prompt is specific about **what to search**, **how many articles**, **what format**, and **what tone**. It's everything the agent needs in one shot.

## Paso 3: Customize the Briefing

Once the basic briefing works, you can get creative.

### Multi-Topic Briefings

Cover several areas in one briefing:

```
/cron add "0 8 * * *" "Create a morning briefing covering three topics. For each topic, search the web for recent news from the past 24 hours and summarize the top 2 stories with links.

Topics:
1. AI and machine learning — focus on open source models and agent frameworks
2. Cryptocurrency — focus on Bitcoin, Ethereum, and regulatory news
3. Space exploration — focus on SpaceX, NASA, and commercial space

Format as a clean briefing with section headers and emoji. End with today's date and a motivational quote."
```

### Using Delegation for Parallel Research

For faster briefings, tell Hermes to delegate each topic to a sub-agent:

```
/cron add "0 8 * * *" "Create a morning briefing by delegating research to sub-agents. Delegate three parallel tasks:

1. Delegate: Search for the top 2 AI/ML news stories from the past 24 hours with links
2. Delegate: Search for the top 2 cryptocurrency news stories from the past 24 hours with links
3. Delegate: Search for the top 2 space exploration news stories from the past 24 hours with links

Collect all results and combine them into a single clean briefing with section headers, emoji formatting, and source links. Add today's date as a header."
```

Each sub-agent searches independently and in parallel, then the main agent combines everything into one polished briefing. See the [Delegation docs](/docs/user-guide/features/delegation) for more on how this works.

### Weekday-Only Schedule

Don't need briefings on weekends? Use a cron expression that targets Monday–Friday:

```
/cron add "0 8 * * 1-5" "Search for the latest AI and tech news..."
```

### Twice-Daily Briefings

Get a morning overview and an evening recap:

```
/cron add "0 8 * * *" "Morning briefing: search for AI news from the past 12 hours..."
/cron add "0 18 * * *" "Evening recap: search for AI news from the past 12 hours..."
```

### Adding Personal Context with Memory

If you have [memory](/docs/user-guide/features/memory) enabled, you can store preferences that persist across sessions. But remember — cron jobs run in fresh sessions without conversational memory. To add personal context, bake it directly into the prompt:

```
/cron add "0 8 * * *" "You are creating a briefing for a senior ML engineer who cares about: PyTorch ecosystem, transformer architectures, open-weight models, and AI regulation in the EU. Skip stories about product launches or funding rounds unless they involve open source.

Search for the latest news on these topics. Summarize the top 3 stories with links. Be concise and technical — this reader doesn't need basic explanations."
```

:::tip Tailor the persona
Including details about who the briefing is *for* dramatically improves relevance. Tell the agent your role, interests, and what to skip.
:::

## Paso 4: Manage Your Jobs

### List All Scheduled Jobs

In chat:
```
/cron list
```

Or from the terminal:
```bash
hermes cron list
```

You'll see output like:

```
ID          | Name              | Schedule    | Next Run           | Deliver
------------|-------------------|-------------|--------------------|--------
a1b2c3d4    | Morning Briefing  | 0 8 * * *   | 2026-03-09 08:00   | telegram
e5f6g7h8    | Evening Recap     | 0 18 * * *  | 2026-03-08 18:00   | telegram
```

### Remove a Job

In chat:
```
/cron remove a1b2c3d4
```

Or ask conversationally:
```
Remove my morning briefing cron job.
```

Hermes will use `list_cronjobs` to find it and `remove_cronjob` to delete it.

### Check Gateway Status

Make sure the scheduler is actually running:

```bash
hermes cron status
```

If the gateway isn't running, your jobs won't execute. Install it as a system service for reliability:

```bash
hermes gateway install
```

## Going Further

You've built a working daily briefing bot. Here are some directions to explore next:

- **[Scheduled Tasks (Cron)](/docs/user-guide/features/cron)** — Full reference for schedule formats, repeat limits, and delivery options
- **[Delegation](/docs/user-guide/features/delegation)** — Deep dive into parallel sub-agent workflows
- **[Messaging Platforms](/docs/user-guide/messaging)** — Set up Telegram, Discord, or other delivery targets
- **[Memory](/docs/user-guide/features/memory)** — Persistent context across sessions
- **[Tips y Mejores Prácticas](/docs/guides/tips)** — More prompt engineering advice

:::tip What else can you schedule?
The briefing bot pattern works for anything: competitor monitoring, GitHub repo summaries, weather forecasts, portfolio tracking, server health checks, or even a daily joke. If you can describe it in a prompt, you can schedule it.
:::
