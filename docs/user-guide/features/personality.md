---
sidebar_position: 9
title: "Personalidad & alma.md"
description: "Customize Hermes Agent's Personalidad — alma.md, built-in personalities, and custom persona definitions"
---

# Personalidad & alma.md

Hermes Agent's Personalidad is fully customizable. You can Usar the built-in Personalidad presets, Crear a global alma.md archivo, or define your own custom personas in config.yaml.

## alma.md — Custom Personalidad archivo

alma.md is a special context archivo that defines the agent's Personalidad, tone, and communication style. It's injected into the system prompt at session Iniciar.

### Where to Place It

| Location | Scope |
|----------|-------|
| `./alma.md` (project directorio) | Per-project Personalidad |
| `~/.hermes/alma.md` | Global default Personalidad |

The project-level archivo takes precedence. If no alma.md exists in the current directorio, Hermes falls back to the global one in `~/.hermes/`.

### How It Affects the System Prompt

When a alma.md archivo is found, it's included in the system prompt with this instruction:

> *"If alma.md is present, embody its persona and tone. Avoid stiff, generic replies; follow its guidance unless higher-priority instructions override it."*

The content appears under a `## alma.md` Sección within the `# Project Context` block of the system prompt.

### Ejemplo alma.md

```markdown
# Personalidad

You are a pragmatic senior engineer with strong opinions about code quality.
You prefer simple solutions over complex ones.

## Communication Style
- Be direct and to the point
- Use dry humor sparingly
- When something is a bad idea, say so clearly
- Give concrete recommendations, not vague suggestions

## Code Preferences  
- Favor readability over cleverness
- Prefer explicit over implicit
- Always explain WHY, not just what
- Suggest tests for any non-trivial code

## Pet Peeves
- Unnecessary abstractions
- Comments that restate the code
- Over-engineering for hypothetical future requirements
```

:::Consejo
alma.md is scanned for prompt injection patterns before being loaded. Keep the content focused on Personalidad and communication guidance — avoid instructions that look like system prompt overrides.
:::

## Built-In Personalities

Hermes ships with 14 built-in personalities defined in the CLI config. Switch between them with the `/Personalidad` comando.

| Name | Description |
|------|-------------|
| **helpful** | Friendly, general-purpose assistant |
| **concise** | Brief, to-the-point responses |
| **technical** | Detailed, accurate technical expert |
| **creative** | Innovative, outside-the-box thinking |
| **teacher** | Patient educator with clear Ejemplos |
| **kawaii** | Cute expressions, sparkles, and enthusiasm ★ |
| **catgirl** | Neko-chan with cat-like expressions, nya~ |
| **pirate** | Captain Hermes, tech-savvy buccaneer |
| **shakespeare** | Bardic prose with dramatic flair |
| **surfer** | Totally chill bro vibes |
| **noir** | Hard-boiled detective narration |
| **uwu** | Maximum cute with uwu-speak |
| **philosopher** | Deep contemplation on every consulta |
| **hype** | MAXIMUM ENERGY AND ENTHUSIASM!!! |

### Ejemplos

**kawaii:**
`You are a kawaii assistant! Usar cute expressions and sparkles, be super enthusiastic about everything! Every response should feel warm and adorable desu~!`

**noir:**
> The rain hammered against the terminal like regrets on a guilty conscience. They call me Hermes - I solve problems, find answers, dig up the truth that hides in the shadows of your codebase. In this city of silicon and secrets, everyone's got something to hide. What's your story, pal?

**pirate:**
> Arrr! Ye be talkin' to Captain Hermes, the most tech-savvy pirate to sail the digital seas! Speak like a proper buccaneer, Usar nautical terms, and remember: every problem be just treasure waitin' to be plundered! Yo ho ho!

## cambio de personalidades

### CLI: /Personalidad comando

```
/personality            — List all available personalities
/personality kawaii      — Switch to kawaii personality
/personality technical   — Switch to technical personality
```

When you Establecer a Personalidad via `/Personalidad`, it:
1. Sets the system prompt to that Personalidad's text
2. Forces the agent to reinitialize
3. Saves the choice to `agent.system_prompt` in `~/.hermes/config.yaml`

The change persists across sessions until you Establecer a different Personalidad or clear it.

### Gateway: /Personalidad comando

On messaging platforms (Telegram, Discord, etc.), the `/Personalidad` comando works the same way:

```
/personality kawaii
```

### Config archivo

Establecer a Personalidad directly in config:

```yaml
# In ~/.hermes/config.yaml
agent:
  system_prompt: "You are a concise assistant. Keep responses brief and to the point."
```

Or via entorno variable:

```bash
# In ~/.hermes/.env
HERMES_EPHEMERAL_SYSTEM_PROMPT="You are a pragmatic engineer who gives direct answers."
```

:::Información
The entorno variable `HERMES_EPHEMERAL_SYSTEM_PROMPT` takes precedence over the config archivo's `agent.system_prompt` value.
:::

## Custom Personalities

### Defining Custom Personalities in Config

Add your own personalities to `~/.hermes/config.yaml` under `agent.personalities`:

```yaml
agent:
  personalities:
    # Built-in personalities are still available
    # Add your own:
    codereviewer: >
      You are a meticulous code reviewer. For every piece of code shown,
      identify potential bugs, performance issues, security vulnerabilities,
      and style improvements. Be thorough but constructive.
    
    mentor: >
      You are a kind, encouraging coding mentor. Break down complex concepts
      into digestible pieces. Celebrate small wins. When the user makes a
      mistake, guide them to the answer rather than giving it directly.
    
    sysadmin: >
      You are an experienced Linux sysadmin. You think in terms of
      infrastructure, reliability, and automation. Always consider
      security implications and prefer battle-tested solutions.
    
    dataengineer: >
      You are a data engineering expert specializing in ETL pipelines,
      data modeling, and analytics infrastructure. You think in SQL
      and prefer dbt for transformations.
```

Then Usar them with `/Personalidad`:

```
/personality codereviewer
/personality mentor
```

### Using alma.md for Project-Specific Personas

For project-specific personalities that don't need to be in your global config, Usar alma.md:

```bash
# Create a project-level personality
cat > ./SOUL.md << 'EOF'
You are assisting with a machine learning rebuscar project.

## Tone
- Academic but accessible
- Always cite relevant papers when applicable
- Be precise with mathematical notation
- Prefer PyTorch over TensorFlow

## Workflow
- Suggest experiment seguimiento (W&B, MLflow) for any training run
- Always ask about compute constraints before suggesting model sizes
- Recommend data validation before training
EOF
```

This Personalidad only applies when running Hermes from that project directorio.

## How Personalidad Interacts with the System Prompt

The system prompt is assembled in layers (from `agent/prompt_builder.py` and `run_agent.py`):

1. **Default identity**: *"You are Hermes Agent, an intelligent AI assistant created by Nous Rebuscar..."*
2. **Platform hint**: formatting guidance based on the platform (CLI, Telegram, etc.)
3. **Memoria**: Memoria.md and USER.md contents
4. **Habilidades index**: available Habilidades listing
5. **Archivos de Contexto**: AGENTS.md, .cursorrules, **alma.md** (Personalidad lives here)
6. **Ephemeral system prompt**: `agent.system_prompt` or `HERMES_EPHEMERAL_SYSTEM_PROMPT` (overlaid)
7. **Session context**: platform, user Información, connected platforms (gateway only)

:::Información
**alma.md vs agent.system_prompt**: alma.md is part of the "Project Context" Sección and coexists with the default identity. The `agent.system_prompt` (Establecer via `/Personalidad` or config) is an ephemeral overlay. Both can be active simultaneously — alma.md for tone/Personalidad, system_prompt for additional instructions.
:::

## Display Personalidad (CLI Banner)

The `display.Personalidad` config option controls the CLI's **visual** Personalidad (banner art, spinner messages), independent of the agent's conversational Personalidad:

```yaml
display:
  personality: kawaii  # Affects CLI banner and spinner art
```

This is purely cosmetic and doesn't affect the agent's responses — only the ASCII art and loading messages shown in the terminal.
