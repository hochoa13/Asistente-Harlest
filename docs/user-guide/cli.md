---
sidebar_position: 1
title: "Interfaz CLI"
description: "Domina la interfaz de terminal de Hermes Agent — comandos, atajos, personalidades y más"
---

# Interfaz CLI

La CLI de Hermes Agent es una interfaz de usuario de terminal completa (TUI) — no una UI web. Presenta edición multilínea, autocompletar de comandos slash, historial de conversaciones, interrupción-redirección y salida de herramientas en streaming. Construida para personas que viven en la terminal.

## Ejecutando la CLI

```bash
# Inicia una sesión interactiva (por defecto)
hermes

# Modo de consulta única (no interactivo)
hermes chat -q "Hola"

# Con un modelo específico
hermes chat --model "anthropic/claude-sonnet-4"

# Con un proveedor específico
hermes chat --provider nous        # Usa Portal de Nous
hermes chat --provider openrouter  # Fuerza OpenRouter

# Con conjuntos de herramientas específicos
hermes chat --toolsets "web,terminal,skills"

# Reanuda sesiones anteriores
hermes --continue             # Reanuda la sesión CLI más reciente (-c)
hermes --resume <session_id>  # Reanuda una sesión específica por ID (-r)

# Modo verbose (salida de depuración)
hermes chat --verbose

# Git worktree aislado (para ejecutar múltiples agentes en paralelo)
hermes -w                         # Modo interactivo en worktree
hermes -w -q "Arregla issue #123" # Consulta única en worktree
```

## Disposición de la Interfaz

```text
┌─────────────────────────────────────────────────┐
│  Logo ASCII de HERMES-AGENT                     │
│  ┌─────────────┐ ┌────────────────────────────┐ │
│  │  Caduceus   │ │ Modelo: claude-sonnet-4    │ │
│  │  Arte ASCII │ │ Terminal: local            │ │
│  │             │ │ Dir Trabajo: /home/usuario │ │
│  │             │ │ Herramientas Disponibles: 19 │
│  │             │ │ Habilidades Disponibles: 12  │
│  └─────────────┘ └────────────────────────────┘ │
├─────────────────────────────────────────────────┤
│ La salida de conversación se desplaza aquí...   │
│                                                 │
│   (◕‿◕✿) 🧠 pensando... (2.3s)                 │
│   ✧٩(ˊᗜˋ*)و✧ ¡lo tengo! (2.3s)                │
│                                                 │
│ Asistente: ¡Hola! ¿Cómo puedo ayudarte hoy?   │
├─────────────────────────────────────────────────┤
│ ❯ [Área de entrada fija en la parte inferior]   │
└─────────────────────────────────────────────────┘
```

El banner de bienvenida muestra tu modelo, el backend de terminal, el directorio de trabajo, las herramientas disponibles y las habilidades instaladas de un vistazo.

### Pantalla de Reanudación de Sesión

Al reanudar una sesión anterior (`hermes -c` o `hermes --resume <id>`), aparece un panel "Conversación Anterior" entre el banner y el prompt de entrada, mostrando un resumen compacto del historial de conversación. Ver [Sesiones — Recapitulación de Conversación al Reanudar](sessions.md#conversation-recap-on-resume) para detalles y configuración.

## Atajos de Teclado

| Tecla | Acción |
|-------|--------|
| `Enter` | Enviar mensaje |
| `Alt+Enter` o `Ctrl+J` | Nueva línea (entrada multilínea) |
| `Ctrl+C` | Interrumpe agente (pulsa dos veces en 2s para forzar salida) |
| `Ctrl+D` | Salir |
| `Tab` | Autocompletar comandos slash |

## Comandos Slash

Escribe `/` para ver un menú desplegable de autocompletar con todos los comandos disponibles.

### Navegación y Control

| Comando | Descripción |
|---------|-------------|
| `/help` | Muestra comandos disponibles |
| `/quit` | Salir de la CLI (también: `/exit`, `/q`) |
| `/clear` | Borra pantalla y reinicia conversación |
| `/new` | Inicia una nueva conversación |
| `/reset` | Reinicia solo la conversación (mantiene pantalla) |

### Herramientas y Configuración

| Comando | Descripción |
|---------|-------------|
| `/tools` | Lista todas las herramientas disponibles agrupadas por conjunto |
| `/toolsets` | Lista conjuntos disponibles con descripciones |
| `/model [proveedor:modelo]` | Muestra o cambia el modelo actual (soporta sintaxis `proveedor:modelo`) |
| `/provider` | Muestra proveedores disponibles con estado de autenticación |
| `/config` | Muestra configuración actual |
| `/prompt [texto]` | Ver/establecer/borrar prompt del sistema personalizado |
| `/personality [nombre]` | Establece una personalidad predefinida |
| `/reasoning [arg]` | Gestiona esfuerzo de razonamiento (`none`/`low`/`medium`/`high`/`xhigh`) y visualización (`show`/`hide`) |

### Gestión de Conversación

| Comando | Descripción |
|---------|-------------|
| `/history` | Muestra historial de conversación |
| `/retry` | Reintenta el último mensaje |
| `/undo` | Elimina el último intercambio usuario/asistente |
| `/save` | Guarda la conversación actual |
| `/compress` | Comprime manualmente contexto de conversación |
| `/usage` | Muestra uso de tokens para esta sesión |
| `/insights [--days N]` | Muestra insights de uso y análisis (últimos 30 días) |

### Habilidades y Programación

| Comando | Descripción |
|---------|-------------|
| `/cron` | Gestiona tareas programadas |
| `/skills` | Explora, busca, instala, inspecciona o gestiona habilidades |
| `/platforms` | Muestra estado de plataforma gateway/mensajería |
| `/verbose` | Ciclo de visualización de progreso: apagado → nuevo → todo → verbose |
| `/<nombre-habilidad>` | Invoca cualquier habilidad instalada (ej: `/axolotl`, `/gif-search`) |

:::tip
Los comandos son insensibles a mayúsculas — `/HELP` funciona igual que `/help`. La mayoría de comandos funcionan en medio de una conversación.
:::

## Comandos Rápidos

Puedes definir comandos personalizados que ejecuten comandos shell al instante sin invocar el LLM. Estos funcionan en la CLI y plataformas de mensajería (Telegram, Discord, etc.).

```yaml
# ~/.hermes/config.yaml
quick_commands:
  status:
    type: exec
    command: systemctl status hermes-agent
  gpu:
    type: exec
    command: nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
```

Luego escribe `/status` o `/gpu` en cualquier chat. Ver la [guía de Configuración](/docs/user-guide/configuration#quick-commands) para más ejemplos.

## Comandos Slash de Habilidades

Cada habilidad instalada en `~/.hermes/skills/` se registra automáticamente como comando slash. El nombre de la habilidad se convierte en el comando:

```
/gif-search gatos divertidos
/axolotl ayúdame a ajustar Llama 3 en mi conjunto de datos
/github-pr-workflow crear un PR para el refactor de autenticación

# Solo el nombre de la habilidad la carga y le permite al agente preguntar qué necesitas:
/excalidraw
```

## Personalidades

Establece una personalidad predefinida para cambiar el tono del agente:

```
/personality pirate
/personality kawaii
/personality concise
```

Las personalidades integradas incluyen: `helpful`, `concise`, `technical`, `creative`, `teacher`, `kawaii`, `catgirl`, `pirate`, `shakespeare`, `surfer`, `noir`, `uwu`, `philosopher`, `hype`.

También puedes definir personalidades personalizadas en `~/.hermes/config.yaml`:

```yaml
agent:
  personalities:
    helpful: "Eres un asistente de IA útil y amigable."
    kawaii: "¡Eres un asistente kawaii! Usa expresiones lindas..."
    pirate: "¡Arr! Estás hablando con el Capitán Hermes..."
    # ¡Añade las tuyas!
```

## Entrada Multilínea

Hay dos formas de ingresar mensajes multilínea:

1. **`Alt+Enter` o `Ctrl+J`** — inserta una nueva línea
2. **Continuación con barra invertida** — termina una línea con `\` para continuar:

```
❯ Escribe una función que:\
  1. Tome una lista de números\
  2. Devuelva la suma
```

:::info
Se admite pegar texto multilínea — usa `Alt+Enter` o `Ctrl+J` para insertar saltos de línea, o simplemente pega contenido directamente.
:::

## Interrumpiendo el Agente

Puedes interrumpir el agente en cualquier momento:

- **Escribe un nuevo mensaje + Enter** mientras el agente está trabajando — interrumpe y procesa tus nuevas instrucciones
- **`Ctrl+C`** — interrumpe la operación actual (pulsa dos veces en 2s para forzar salida)
- Los comandos de terminal en progreso se matan inmediatamente (SIGTERM, luego SIGKILL después de 1s)
- Múltiples mensajes escritos durante interrupción se combinan en un prompt

## Visualización del Progreso de Herramientas

La CLI muestra retroalimentación animada mientras el agente trabaja:

**Animación de pensamiento** (durante llamadas a API):
```
  ◜ (｡•́︿•̀｡) pensando... (1.2s)
  ◠ (⊙_⊙) contemplando... (2.4s)
  ✧٩(ˊᗜˋ*)و✧ ¡lo tengo! (3.1s)
```

**Feed de ejecución de herramientas:**
```
  ┊ 💻 terminal `ls -la` (0.3s)
  ┊ 🔍 búsqueda_web (1.2s)
  ┊ 📄 extracción_web (2.1s)
```

Cicla entre modos de visualización con `/verbose`: `apagado → nuevo → todo → verbose`.

## Gestión de Sesiones

### Reanudando Sesiones

Cuando salgas de una sesión CLI, se imprime un comando de reanudación:

```
Reanuda esta sesión con:
  hermes --resume 20260225_143052_a1b2c3

Sesión:         20260225_143052_a1b2c3
Duración:       12m 34s
Mensajes:       28 (5 usuario, 18 llamadas de herramientas)
```

Opciones de reanudación:

```bash
hermes --continue                          # Reanuda la sesión CLI más reciente
hermes -c                                  # Forma abreviada
hermes -c "mi proyecto"                    # Reanuda una sesión nombrada (última en linaje)
hermes --resume 20260225_143052_a1b2c3     # Reanuda una sesión específica por ID
hermes --resume "refactorización auth"     # Reanuda por título
hermes -r 20260225_143052_a1b2c3           # Forma abreviada
```

Reanudar restaura el historial de conversación completo desde SQLite. El agente ve todos los mensajes anteriores, llamadas de herramientas y respuestas — como si nunca te hubieras ido.

Usa `/title My Session Name` dentro de un chat para nombrar la sesión actual, o `hermes sessions rename <id> <title>` desde la línea de comandos. Usa `hermes sessions list` para examinar sesiones pasadas.

### Registro de Sesiones

Las sesiones se registran automáticamente en `~/.hermes/sessions/`:

```
sessions/
├── session_20260201_143052_a1b2c3.json
├── session_20260201_150217_d4e5f6.json
└── ...
```

### Compresión de Contexto

Las conversaciones largas se resumen automáticamente al aproximarse a los límites de contexto:

```yaml
# En ~/.hermes/config.yaml
compression:
  enabled: true
  threshold: 0.85    # Comprime al 85% del límite de contexto
  summary_model: "google/gemini-3-flash-preview"  # Modelo usado para resumen
```

Cuando se activa compresión, los turnos intermedios se resumen mientras que los primeros 3 y últimos 4 turnos siempre se preservan.

## Modo Silencioso

Por defecto, la CLI se ejecuta en modo silencioso que:
- Suprime registro verbose de herramientas
- Habilita retroalimentación animada estilo kawaii
- Mantiene la salida limpia y amigable

Para salida de depuración:
```bash
hermes chat --verbose
```
