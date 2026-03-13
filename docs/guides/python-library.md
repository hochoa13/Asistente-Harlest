---
sidebar_position: 4
title: "Usando Hermes como una Librería Python"
description: "Integra AIAgent en tus propios scripts de Python, web apps, or automation pipelines — no CLI required"
---

# Usando Hermes como una Librería Python

Hermes no es solo una herramienta CLI. Puedes importar `AIAgent` directamente y usarlo programáticamente en tus propios scripts de Python, aplicaciones web o tuberías de automatización. Esta guía te muestra cómo.

---

## Instalación

Instala Hermes directamente desde el repositorio:

```bash
pip install git+https://github.com/hochoa13/Asistente-Harlest.git
```

O con [uv](https://docs.astral.sh/uv/):

```bash
uv pip install git+https://github.com/hochoa13/Asistente-Harlest.git
```

También puedes fijarlo en tu `requirements.txt`:

```text
hermes-agent @ git+https://github.com/hochoa13/Asistente-Harlest.git
```

:::tip
Las mismas variables de entorno utilizadas por la CLI se requieren al usar Hermes como una librería. Como mínimo, establece `OPENROUTER_API_KEY` (o `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` si usas acceso directo al proveedor).
:::

---

## Uso Básico

La forma más simple de usar Hermes es el método `chat()` — pasa un mensaje, obtén una cadena de regreso:

```python
from run_agent import AIAgent

agent = AIAgent(
    model="anthropic/claude-sonnet-4",
    quiet_mode=True,
)
response = agent.chat("¿Cuál es la capital de Francia?")
print(response)
```

`chat()` maneja el bucle de conversación completo internamente — llamadas a herramientas, reintentos, todo — y devuelve solo la respuesta de texto final.

:::warning
Siempre establece `quiet_mode=True` cuando incrustas Hermes en tu propio código. Sin él, el agente imprime giroscopios de CLI, indicadores de progreso y otra salida de terminal que ensuciará la salida de tu aplicación.
:::

---

## Control Completo de Conversación

Para mayor control sobre la conversación, usa `run_conversation()` directamente. Devuelve un diccionario con la respuesta completa, historial de mensajes y metadatos:

```python
agent = AIAgent(
    model="anthropic/claude-sonnet-4",
    quiet_mode=True,
)

result = agent.run_conversation(
    user_message="Busca características recientes de Python 3.13",
    task_id="mi-tarea-1",
)

print(result["final_response"])
print(f"Mensajes intercambiados: {len(result['messages'])}")
```

El diccionario devuelto contiene:
- **`final_response`** — La respuesta de texto final del agente
- **`messages`** — El historial completo de mensajes (sistema, usuario, asistente, llamadas a herramientas)
- **`task_id`** — El identificador de tarea utilizado para aislamiento de VM

También puedes pasar un mensaje de sistema personalizado que anule el prompt de sistema efímero para esa llamada:

```python
result = agent.run_conversation(
    user_message="Explica quicksort",
    system_message="Eres un tutor de informática. Usa analogías simples.",
)
```

---

## Configurando Herramientas

Controla qué conjuntos de herramientas tiene acceso el agente usando `enabled_toolsets` o `disabled_toolsets`:

```python
# Only enable web tools (browsing, search)
agent = AIAgent(
    model="anthropic/claude-sonnet-4",
    enabled_toolsets=["web"],
    quiet_mode=True,
)

# Enable everything except terminal access
agent = AIAgent(
    model="anthropic/claude-sonnet-4",
    disabled_toolsets=["terminal"],
    quiet_mode=True,
)
```

:::tip
Use `enabled_toolsets` when you want a minimal, locked-down agent (e.g., only web search for a research bot). Use `disabled_toolsets` when you want most capabilities but need to restrict specific ones (e.g., no terminal access in a shared environment).
:::

---

## Multi-turn Conversations

Maintain conversation state across multiple turns by passing the message history back in:

```python
agent = AIAgent(
    model="anthropic/claude-sonnet-4",
    quiet_mode=True,
)

# First turn
result1 = agent.run_conversation("My name is Alice")
history = result1["messages"]

# Second turn — agent remembers the context
result2 = agent.run_conversation(
    "What's my name?",
    conversation_history=history,
)
print(result2["final_response"])  # "Your name is Alice."
```

The `conversation_history` parameter accepts the `messages` list from a previous result. The agent copies it internally, so your original list is never mutated.

---

## Saving Trajectories

Enable trajectory saving to capture conversations in ShareGPT format — useful for generating training data or debugging:

```python
agent = AIAgent(
    model="anthropic/claude-sonnet-4",
    save_trajectories=True,
    quiet_mode=True,
)

agent.chat("Write a Python function to sort a list")
# Saves to trajectory_samples.jsonl in ShareGPT format
```

Each conversation is appended as a single JSONL line, making it easy to collect datasets from automated runs.

---

## Custom System Prompts

Use `ephemeral_system_prompt` to set a custom system prompt that guides the agent's behavior but is **not** saved to trajectory files (keeping your training data clean):

```python
agent = AIAgent(
    model="anthropic/claude-sonnet-4",
    ephemeral_system_prompt="You are a SQL expert. Only answer database questions.",
    quiet_mode=True,
)

response = agent.chat("How do I write a JOIN query?")
print(response)
```

This is ideal for building specialized agents — a code reviewer, a documentation writer, a SQL assistant — all using the same underlying tooling.

---

## Batch Processing

For running many prompts in parallel, Hermes includes `batch_runner.py`. It manages concurrent `AIAgent` instances with proper resource isolation:

```bash
python batch_runner.py --input prompts.jsonl --output results.jsonl
```

Each prompt gets its own `task_id` and isolated environment. If you need custom batch logic, you can build your own using `AIAgent` directly:

```python
import concurrent.futures
from run_agent import AIAgent

prompts = [
    "Explain recursion",
    "What is a hash table?",
    "How does garbage collection work?",
]

def process_prompt(prompt):
    # Create a fresh agent per task for thread safety
    agent = AIAgent(
        model="anthropic/claude-sonnet-4",
        quiet_mode=True,
        skip_memory=True,
    )
    return agent.chat(prompt)

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(process_prompt, prompts))

for prompt, result in zip(prompts, results):
    print(f"Q: {prompt}\nA: {result}\n")
```

:::warning
Always create a **new `AIAgent` instance per thread or task**. The agent maintains internal state (conversation history, tool sessions, iteration counters) that is not thread-safe to share.
:::

---

## Integration Ejemplos

### FastAPI Endpoint

```python
from fastapi import FastAPI
from pydantic import BaseModel
from run_agent import AIAgent

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    model: str = "anthropic/claude-sonnet-4"

@app.post("/chat")
async def chat(request: ChatRequest):
    agent = AIAgent(
        model=request.model,
        quiet_mode=True,
        skip_context_files=True,
        skip_memory=True,
    )
    response = agent.chat(request.message)
    return {"response": response}
```

### Discord Bot

```python
import discord
from run_agent import AIAgent

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith("!hermes "):
        query = message.content[8:]
        agent = AIAgent(
            model="anthropic/claude-sonnet-4",
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
            platform="discord",
        )
        response = agent.chat(query)
        await message.channel.send(response[:2000])

client.run("YOUR_DISCORD_TOKEN")
```

### CI/CD Pipeline Step

```python
#!/usr/bin/env python3
"""CI step: auto-review a PR diff."""
import subprocess
from run_agent import AIAgent

diff = subprocess.check_output(["git", "diff", "main...HEAD"]).decode()

agent = AIAgent(
    model="anthropic/claude-sonnet-4",
    quiet_mode=True,
    skip_context_files=True,
    skip_memory=True,
    disabled_toolsets=["terminal", "browser"],
)

review = agent.chat(
    f"Review this PR diff for bugs, security issues, and style problems:\n\n{diff}"
)
print(review)
```

---

## Key Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | `"anthropic/claude-opus-4.6"` | Model in OpenRouter format |
| `quiet_mode` | `bool` | `False` | Suppress CLI output |
| `enabled_toolsets` | `List[str]` | `None` | Whitelist specific toolsets |
| `disabled_toolsets` | `List[str]` | `None` | Blacklist specific toolsets |
| `save_trajectories` | `bool` | `False` | Save conversations to JSONL |
| `ephemeral_system_prompt` | `str` | `None` | Custom system prompt (not saved to trajectories) |
| `max_iterations` | `int` | `90` | Max tool-calling iterations per conversation |
| `skip_context_files` | `bool` | `False` | Skip loading AGENTS.md files |
| `skip_memory` | `bool` | `False` | Disable persistent memory read/write |
| `api_key` | `str` | `None` | API key (falls back to env vars) |
| `base_url` | `str` | `None` | Custom API endpoint URL |
| `platform` | `str` | `None` | Platform hint (`"discord"`, `"telegram"`, etc.) |

---

## Important Notes

:::tip
- Set **`skip_context_files=True`** if you don't want `AGENTS.md` files from the working directory loaded into the system prompt.
- Set **`skip_memory=True`** to prevent the agent from reading or writing persistent memory — recommended for stateless API endpoints.
- The `platform` parameter (e.g., `"discord"`, `"telegram"`) injects platform-specific formatting hints so the agent adapts its output style.
:::

:::warning
- **Thread safety**: Create one `AIAgent` per thread or task. Never share an instance across concurrent calls.
- **Resource cleanup**: The agent automatically cleans up resources (terminal sessions, browser instances) when a conversation ends. If you're running in a long-lived process, ensure each conversation completes normally.
- **Iteration limits**: The default `max_iterations=90` is generous. For simple Q&A use cases, consider lowering it (e.g., `max_iterations=10`) to prevent runaway tool-calling loops and control costs.
:::
