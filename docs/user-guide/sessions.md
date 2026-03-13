---
sidebar_position: 7
title: "Sesiones"
description: "Persistencia de sesión, reanudación, búsqueda, gestión y seguimiento de sesiones por plataforma"
---

# Sesiones

Hermes Agent guarda automáticamente cada conversación como una sesión. Las sesiones permiten reanudar conversaciones, búsqueda entre sesiones e historial completo de conversación gestión.

## Cómo Funcionan las Sesiones

Cada conversación — ya sea desde la CLI, Telegram, Discord, WhatsApp o Slack — se almacena como una sesión con historial completo de mensajes. Las sesiones se rastrean en dos sistemas complementarios:

1. **Base de datos SQLite** (`~/.hermes/state.db`) — metadatos estructurados de sesión con búsqueda de texto completo FTS5
2. **Transcripciones JSONL** (`~/.hermes/sessions/`) — transcripciones de conversación sin procesar, incluidas llamadas de herramientas (puerta de enlace)

La base de datos SQLite almacena:
- ID de sesión, plataforma de origen, ID de usuario
- **Título de sesión** (nombre único y legible para humanos)
- Nombre del modelo y configuración
- Instantánea del prompt del sistema
- Historial completo de mensajes (rol, contenido, llamadas de herramientas, resultados de herramientas)
- Conteos de tokens (entrada/salida)
- Marcas de tiempo (iniciado_en, finalizado_en)
- ID de sesión padre (para división de sesión desencadenada por compresión)

### Fuentes de Sesión

Cada sesión está etiquetada con su plataforma de origen:

| Origen | Descripción |
|--------|-------------|
| `cli` | CLI interactiva (`hermes` o `hermes chat`) |
| `telegram` | Mensajería Telegram |
| `discord` | Servidor Discord/MD |
| `whatsapp` | Mensajería WhatsApp |
| `slack` | Espacio de trabajo Slack |

### Reanudación de Sesión Anterior

Para continuar una conversación anterior desde la CLI, use:

```bash
hermes resume
```

Busca la sesión más reciente de `cli` desde la base de datos SQLite y carga todo su historial de conversación.

### Reanudar por Nombre

Si ha asignado un título a una sesión, puede reanudarlo por nombre:

```bash
# Reanudar una sesión nombrada
hermes resume "mi proyecto"

# Si hay variantes de linaje (mi proyecto, mi proyecto #2, mi proyecto #3),
# automáticamente reanuda la más reciente
hermes resume "mi proyecto"   # → reanuda "mi proyecto #3"
```

### Reanudar Sesión Específica

```bash
# Reanudar una sesión específica por ID
hermes sessions resume 20250305_091523_a1b2c3d4

# Reanudar por título
hermes sessions resume "refactorización auth"
```

Los ID de sesión se muestran cuando sale de una sesión CLI, y se pueden encontrar con `hermes list`.

### Resumen de Conversación al Reanudar

Cuando se reanuda una sesión, Hermes muestra un resumen compacto de la conversación anterior en un panel con estilo antes del indicador de entrada:

```text
╭──────────────────────── Conversación Anterior ──────────────────────╮
│   ● Usted: ¿Qué es Python?                                          │
│   ◆ Hermes: Python es un lenguaje de programación de alto nivel.    │
│   ● Usted: ¿Cómo lo instalo?                                        │
│   ◆ Hermes: [3 llamadas de herramientas: buscar, extraer, terminal]│
│   ◆ Hermes: Puedes descargar Python desde python.org...            │
╰────────────────────────────────────────────────────────────────────╯
```

El resumen:
- Muestra **mensajes del usuario** (●oro) y **respuestas del asistente** (◆ verde)
- **Trunca** mensajes largos (300 caracteres para usuario, 200 caracteres / 3 líneas para asistente)
- **Colapsa** llamadas de herramientas a un conteo con nombres de herramientas (p. ej., `[3 llamadas de herramientas: terminal, buscar_web]`)
- **Oculta** mensajes del sistema, resultados de herramientas y razonamiento interno
- **Limita** a los últimos 10 intercambios con un indicador "... N mensajes anteriores ..."
- Usa **estilo atenuado** para distinguirse de la conversación activa

Para deshabilitar el resumen y mantener el comportamiento de una línea minimal, establezca en `~/.hermes/config.yaml`:

```yaml
display:
  reanudar_display: minimal   # predeterminado: full
```

:::tip
Los ID de sesión siguen el formato `YYYYMMDD_HHMMSS_<8-char-hex>`, p. ej. `20250305_091523_a1b2c3d4`. Puede reanudar por ID o por título — ambos funcionan con `resume`.
:::

## Nombrado de Sesiones

Dé a las sesiones títulos legibles para que pueda encontrarlas y reanudelas fácilmente.

### Establecer un Título

Use el comando de barra `/title` dentro de cualquier sesión de chat (CLI o puerta de enlace):

```
/title mi proyecto de búsqueda
```

El título se aplica inmediatamente. Si la sesión aún no se ha creado en la base de datos (por ejemplo, ejecuta `/title` antes de enviar su primer mensaje), se pone en cola y se aplica una vez que comienza la sesión.

También puede renombrar sesiones existentes desde la línea de comandos:

```bash
hermes sessions rename 20250305_091523_a1b2c3d4 "refactorización módulo auth"
```

### Reglas de Título

- **Único** — dos sesiones no pueden compartir el mismo título
- **Máx. 100 caracteres** — mantiene la salida de listado limpia
- **Sanitizado** — los caracteres de control, caracteres de ancho cero y anulaciones RTL se eliminan automáticamente
- **Unicode normal está bien** — emoji, CJK, caracteres acentuados, todo funciona

### Linaje Automático en Compresión

Cuando el contexto de una sesión se comprime (manualmente vía `/compress` o automáticamente), Hermes crea una nueva sesión de continuación. Si la original tenía un título, la nueva sesión obtiene automáticamente un título numerado:

```
"mi proyecto" → "mi proyecto #2" → "mi proyecto #3"
```

Cuando reanuda por nombre (`hermes resume "mi proyecto"`), automáticamente elige la sesión más reciente de la linaje.

### /title en Plataformas de Mensajería

El comando `/title` funciona en todas las plataformas de puerta de enlace (Telegram, Discord, Slack, WhatsApp):

- `/title Mi Búsqueda` — establecer el título de la sesión
- `/title` — mostrar el título actual

## Comandos de Gestión de Sesión

Hermes proporciona un conjunto completo de comandos de gestión de sesión vía `hermes sessions`:

### Listar Sesiones

```bash
# Listar sesiones recientes (predeterminado: 20 últimas)
hermes sessions list

# Filtrar por plataforma
hermes sessions list --source telegram

# Mostrar más sesiones
hermes sessions list --limit 50
```

Cuando las sesiones tienen títulos, la salida muestra títulos, vistas previas y marcas de tiempo relativas:

```
Título                 Vista Previa                             Última Actividad   ID
────────────────────────────────────────────────────────────────────────────────────────────────
refactorización auth   Ayúdame a refactorizar el módulo auth   hace 2h            20250305_091523_a
mi proyecto #3         ¿Puedes revisar los fallos de prueba?  ayer               20250304_143022_e
—                      ¿Cuál es el clima en Las Vegas?         hace 3d            20250303_101500_f
```

Cuando no hay sesiones con títulos, se usa un formato más simple:

```
Vista Previa                                         Última Actividad   Origen    ID
──────────────────────────────────────────────────────────────────────────────────────────────
Ayúdame a refactorizar el módulo auth               hace 2h            cli       20250305_091523_a
¿Cuál es el clima en Las Vegas?                     hace 3d            tele      20250303_101500_f
```

### Exportar Sesiones

```bash
# Exportar todas las sesiones a un archivo JSONL
hermes sessions export copia_seguridad.jsonl

# Exportar sesiones de una plataforma específica
hermes sessions export historial_telegram.jsonl --source telegram

# Exportar una sesión específica
hermes sessions export sesion.jsonl --session-id 20250305_091523_a1b2c3d4
```

Los archivos exportados contienen un objeto JSON por línea con todos los metadatos de sesión y mensajes.

### Eliminar una Sesión

```bash
# Eliminar una sesión específica (con confirmación)
hermes sessions delete 20250305_091523_a1b2c3d4

# Eliminar sin confirmación
hermes sessions delete 20250305_091523_a1b2c3d4 --yes
```

### Renombrar una Sesión

```bash
# Establecer o cambiar el título de una sesión
hermes sessions rename 20250305_091523_a1b2c3d4 "depuración flujo auth"

# Los títulos de varias palabras no necesitan comillas en la CLI
hermes sessions rename 20250305_091523_a1b2c3d4 depuración flujo auth
```

Si el título ya está siendo utilizado por otra sesión, se muestra un error.

### Purgar Sesiones Antiguas

```bash
# Eliminar sesiones finalizadas más antiguas que 90 días (predeterminado)
hermes sessions prune

# Umbral de edad personalizado
hermes sessions prune --older-than 30

# Solo purgar sesiones de una plataforma específica
hermes sessions prune --source telegram --older-than 60

# Omitir confirmación
hermes sessions prune --older-than 30 --yes
```

:::info
La purgación solo elimina sesiones **finalizadas** (sesiones que se han terminado explícitamente o se han restablecido automáticamente). Las sesiones activas nunca se purguan.
:::

### Estadísticas de Sesión

```bash
hermes sessions stats
```

Output:

```
Sesiones totales: 142
Mensajes totales: 3847
  cli: 89 sesiones
  telegram: 38 sesiones
  discord: 15 sesiones
Tamaño de base de datos: 12.4 MB
```

Para análisis más profundos — uso de tokens, estimaciones de costos, desglose de herramientas y patrones de actividad — use [`hermes insights`](/docs/reference/cli-commands#insights).

## Herramienta de Búsqueda de Sesión

El agente tiene una herramienta `session_buscar` integrada que realiza búsqueda de texto completo en todas las conversaciones pasadas usando el motor FTS5 de SQLite.

### Cómo Funciona

1. FTS5 busca mensajes coincidentes clasificados por relevancia
2. Agrupa resultados por sesión, toma las N sesiones únicas principales (predeterminado 3)
3. Carga el historial de conversación de cada sesión, trunca a ~100K caracteres centrado en los resultados
4. Envía a un modelo de resumen rápido para resúmenes enfocados
5. Devuelve resúmenes por sesión con metadatos y contexto circundante

### Sintaxis de Consulta FTS5

La búsqueda admite la sintaxis de consulta estándar FTS5:

- Palabras clave simples: `docker deployment`
- Frases: `"frase exacta"`
- Booleano: `docker OR kubernetes`, `python NOT java`
- Prefijo: `deploy*`

### Cuándo Se Usa

Se le solicita automáticamente al agente que use búsqueda de sesión:

> *"Cuando el usuario hace referencia a algo de una conversación pasada o sospecha que existe contexto previo relevante, use session_buscar para recuperarlo antes de pedirle que se repita".*

## Seguimiento de Sesión por Plataforma

### Sesiones de Puerta de Enlace

En plataformas de mensajería, las sesiones se codifican mediante una clave de sesión determinista construida a partir de la fuente de mensaje:

| Tipo de Chat | Formato de Clave | Ejemplo |
|-----------|-----------|---------|
| MD de Telegram | `agent:main:telegram:dm` | Una sesión por bot |
| MD de Discord | `agent:main:discord:dm` | Una sesión por bot |
| MD de WhatsApp | `agent:main:whatsapp:dm:<chat_id>` | Por usuario (multiusuario) |
| Chat de grupo | `agent:main:<platform>:group:<chat_id>` | Por grupo |
| Canal | `agent:main:<platform>:channel:<chat_id>` | Por canal |

:::info
Los MD de WhatsApp incluyen el ID de chat en la clave de sesión porque múltiples usuarios pueden enviar MD al bot. Otras plataformas usan una sola sesión MD ya que el bot está configurado por usuario a través de listas de permitir.
:::

### Políticas de Restablecimiento de Sesión

Las sesiones de puerta de enlace se restablecen automáticamente según políticas configurables:

- **inactivo** — restablecer después de N minutos de inactividad
- **diario** — restablecer a una hora específica cada día
- **ambos** — restablecer en el que venga primero (inactivo o diario)
- **ninguno** — nunca restabler automáticamente

Antes de que una sesión se restablezca automáticamente, se le da al agente un turno para guardar cualquier memoria o habilidad importante de la conversación.

Las sesiones con **procesos de fondo activos** nunca se restablecen automáticamente, independientemente de la política.

## Ubicaciones de Almacenamiento

| Qué | Ruta | Descripción |
|------|------|-------------|
| Base de datos SQLite | `~/.hermes/state.db` | Todos los metadatos de sesión + mensajes con FTS5 |
| Transcripciones de puerta de enlace | `~/.hermes/sessions/` | Transcripciones JSONL por sesión + índice sessions.json |
| Índice de puerta de enlace | `~/.hermes/sessions/sessions.json` | Asigna claves de sesión a ID de sesión activos |

La base de datos SQLite usa modo WAL para lectores concurrentes y un escritor único, lo cual se adapta bien a la arquitectura de múltiples plataformas de la puerta de enlace.

### Esquema de Base de Datos

Tablas clave en `state.db`:

- **sesiones** — metadatos de sesión (id, origen, user_id, modelo, título, marcas de tiempo, conteos de tokens). Los títulos tienen un índice único (los títulos NULL están permitidos, solo los títulos NO NULL deben ser únicos).
- **mensajes** — historial completo de mensajes (rol, contenido, llamadas_herramientas, nombre_herramienta, conteo_tokens)
- **mensajes_fts** — tabla virtual FTS5 para búsqueda de texto completo en el contenido de mensajes

## Caducidad de Sesión y Limpieza

### Limpieza Automática

- Las sesiones de puerta de enlace se restablecen automáticamente según la política de restablecimiento configurada
- Antes del restablecimiento, el agente guarda memorias y habilidades de la sesión que expira
- Las sesiones finalizadas permanecen en la base de datos hasta que se purguen

### Limpieza Manual

```bash
# Purgar sesiones más antiguas que 90 días
hermes sessions prune

# Eliminar una sesión específica
hermes sessions delete <session_id>

# Exportar antes de purgar (copia de seguridad)
hermes sessions export copia_seguridad.jsonl
hermes sessions prune --older-than 30 --yes
```

:::tip
La base de datos crece lentamente (típico: 10-15 MB para cientos de sesiones). La purgación es principalmente útil para eliminar conversaciones antiguas que ya no necesita para recuperación de búsqueda.
:::
