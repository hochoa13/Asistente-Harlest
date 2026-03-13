---
sidebar_position: 3
title: "Memoria Persistente"
description: "Cómo recuerda Hermes Agent entre sesiones — Memoria.md, USER.md, y búsqueda de sesión"
---

# Memoria Persistente

Hermes Agent tiene una Memoria limitada y curada que persiste entre sesiones. Esto le permite recordar tus preferencias, tus proyectos, tu entorno y las cosas que ha aprendido.

## Cómo Funciona

Dos archivos conforman la Memoria del agente:

| archivo | Propósito | Límite de Caracteres |
|------|---------|------------|
| **Memoria.md** | Notas personales del agente — hechos del entorno, convenciones, cosas aprendidas | 2.200 caracteres (~800 tokens) |
| **USER.md** | Perfil de usuario — tus preferencias, estilo de comunicación, expectativas | 1.375 caracteres (~500 tokens) |

Ambos se almacenan en `~/.hermes/memories/` e se inyectan en el indicador del sistema como una instantánea congelada al inicio de la sesión. El agente gestiona su propia Memoria a través de la herramienta `memory` — puede agregar, reemplazar o eliminar entradas.

:::info
Los límites de caracteres mantienen la Memoria enfocada. Cuando la Memoria está llena, el agente consolida o reemplaza entradas para dejar espacio para información nueva.
:::

## Cómo Aparece la Memoria en el Indicador del Sistema

Al inicio de cada sesión, las entradas de Memoria se cargan desde el disco y se procesan en el indicador del sistema como un bloque congelado:

```
══════════════════════════════════════════════
MEMORIA (tus notas personales) [67% — 1.474/2.200 caracteres]
═════════════════════════════════════════════
User's project is a Rust web service at ~/code/myapi using Axum + SQLx
§
This machine runs Ubuntu 22.04, has Docker and Podman installed
§
User prefers concise responses, dislikes verbose explanations
```

El formato incluye:
- Un encabezado que muestra cuál tienda (Memoria o PERFIL DE USUARIO)
- Porcentaje de uso y conteos de caracteres para que el agente conozca la capacidad
- Entradas individuales separadas por delimitadores `§` (signo de sección)
- Las entradas pueden ser multilínea

**Patrón de instantánea congelada:** La inyección del indicador del sistema se captura una sola vez al inicio de la sesión y nunca cambia durante la sesión. Esto es intencional — preserva la caché de prefijo del LLM para el rendimiento. Cuando el agente agrega/elimina entradas de Memoria durante una sesión, los cambios se persisten en el disco inmediatamente pero no aparecerán en el indicador del sistema hasta que comience la próxima sesión. Las respuestas de las herramientas siempre muestran el estado actual.

## Acciones de la Herramienta Memoria

El agente utiliza la herramienta `memory` con estas acciones:

- **add** — Agregar una nueva entrada de Memoria
- **replace** — Reemplazar una entrada existente con contenido actualizado (utiliza coincidencia de subcadena a través de `old_text`)
- **remove** — Eliminar una entrada que ya no es relevante (utiliza coincidencia de subcadena a través de `old_text`)

No hay una acción `read` — el contenido de la Memoria se inyecta automáticamente en el indicador del sistema al inicio de la sesión. El agente ve sus recuerdos como parte de su contexto de conversación.

### Coincidencia de Subcadena

Las acciones `replace` y `remove` utilizan una coincidencia de subcadena única y corta — no necesitas el texto completo de la entrada. El parámetro `old_text` solo necesita ser una subcadena única que identifique exactamente una entrada:

```python
# Si memory contiene "User prefers dark mode in all editors"
memory(action="replace", target="memory",
       old_text="dark mode",
       content="User prefers light mode in VS Code, dark mode in terminal")
```

Si la subcadena coincide con múltiples entradas, se devuelve un error pidiendo una coincidencia más específica.

## Dos Objetivos Explicados

### `memory` — Notas Personales del Agente

Para información que el agente necesita recordar sobre el entorno, flujos de trabajo y lecciones aprendidas:

- Hechos del entorno (OS, herramientas, estructura del proyecto)
- Convenciones del proyecto y configuración
- Peculiaridades de herramientas y soluciones alternativas descubiertas
- Entradas de diario de tareas completadas
- Habilidades y técnicas que funcionaron

### `user` — Perfil de Usuario

Para información sobre la identidad, preferencias y estilo de comunicación del usuario:

- Nombre, rol, zona horaria
- Preferencias de comunicación (conciso vs detallado, preferencias de formato)
- Manías y cosas a evitar
- Hábitos de flujo de trabajo
- Nivel de habilidad técnica

## Qué Guardar vs Qué Omitir

### Guardar Esto (Proactivamente)

El agente guarda automáticamente — no necesitas pedirlo. Guarda cuando aprende:

- **Preferencias del usuario:** "Prefiero TypeScript a JavaScript" → guardar en `user`
- **Hechos del entorno:** "Este servidor ejecuta Debian 12 con PostgreSQL 16" → guardar en `memory`
- **Correcciones:** "No usar `sudo` para comandos docker, el usuario está en el grupo docker" → guardar en `memory`
- **Convenciones:** "El proyecto utiliza tabs, ancho de línea de 120 caracteres, docstrings al estilo Google" → guardar en `memory`
- **Trabajo completado:** "Base de datos migrada de MySQL a PostgreSQL en 2026-01-15" → guardar en `memory`
- **Solicitudes explícitas:** "Recuerda que mi rotación de clave API ocurre mensualmente" → guardar en `memory`

### Omitir Esto

- **Información trivial/obvia:** "El usuario preguntó sobre Python" — demasiado vago para ser útil
- **Hechos fácilmente redescubiertos:** "Python 3.12 admite anidamiento de f-strings" — se puede buscar esto en la web
- **Volcados de datos sin procesar:** Bloques de código grandes, archivos de registro, tablas de datos — demasiado grande para Memoria
- **Efemérides específicas de sesión:** Rutas de archivo temporales, contexto de depuración de una sola vez
- **Información ya en Archivos de Contexto:** contenido de alma.md y AGENTS.md

## Gestión de Capacidad

Memoria tiene límites estrictos de caracteres para mantener los indicadores del sistema limitados:

| Tienda | Límite | Entradas Típicas |
|-------|-------|----------------|
| memory | 2.200 caracteres | 8-15 entradas |
| user | 1.375 caracteres | 5-10 entradas |

### Qué Sucede Cuando la Memoria Está Llena

Cuando intentas agregar una entrada que excedería el límite, la herramienta devuelve un error:

```json
{
  "success": false,
  "error": "Memoria at 2,100/2,200 chars. Adding this entry (250 chars) would exceed the limit. Replace or remove existing entries first.",
  "current_entries": ["..."],
  "usage": "2,100/2,200"
}
```

El agente debería entonces:
1. Leer las entradas actuales (mostradas en la respuesta de error)
2. Identificar entradas que se pueden eliminar o consolidar
3. Usar `replace` para fusionar entradas relacionadas en versiones más cortas
4. Luego `add` la nueva entrada

**Mejor práctica:** Cuando la Memoria está por encima de la capacidad del 80% (visible en el encabezado del indicador del sistema), consolida entradas antes de agregar nuevas. Por ejemplo, fusiona tres entradas separadas de "el proyecto usa X" en una sola entrada de descripción de proyecto integral.

### Ejemplos Prácticos de Buenas Entradas de Memoria

**Las entradas compactas y densas en información funcionan mejor:**

```
# Bueno: Empaqueta múltiples hechos relacionados
User runs macOS 14 Sonoma, uses Homebrew, has Docker Desktop and Podman. Shell: zsh with oh-my-zsh. Editor: VS Code with Vim keybindings.

# Bueno: Convención específica y accionable
Project ~/code/api uses Go 1.22, sqlc for DB queries, chi router. Run tests with 'make test'. CI via GitHub Actions.

# Bueno: Lección aprendida con contexto
The staging server (10.0.1.50) needs SSH port 2222, not 22. Key is at ~/.ssh/staging_ed25519.

# Malo: Demasiado vago
User has a project.

# Malo: Demasiado verboso
On January 5th, 2026, the user asked me to look at their project which is
located at ~/code/api. I discovered it uses Go version 1.22 and...
```

## Prevención de Duplicados

El sistema de Memoria rechaza automáticamente entradas exactamente duplicadas. Si intentas agregar contenido que ya existe, devuelva éxito con un mensaje "no duplicate added".

## Escaneo de Seguridad

Las entradas de Memoria se escanean en busca de patrones de inyección y exfiltración antes de ser aceptadas, ya que se inyectan en el indicador del sistema. El contenido que coincide con patrones de amenaza (inyección de indicador, exfiltración de credenciales, puertas traseras ssh) o que contiene caracteres Unicode invisibles se bloquea.

## Búsqueda de Sesión

Más allá de Memoria.md y USER.md, el agente puede buscar sus conversaciones pasadas utilizando la herramienta `session_search`:

- Todas las sesiones de CLI y mensajería se almacenan en SQLite (`~/.hermes/state.db`) con búsqueda de texto completo FTS5
- Las consultas de búsqueda devuelven conversaciones pasadas relevantes con resumen de Gemini Flash
- El agente puede encontrar cosas que discutió hace semanas, incluso si no están en su Memoria activa

```bash
hermes sessions list    # Browse past sessions
```

### Búsqueda de Sesión vs Memoria

| Característica | Memoria Persistente | Búsqueda de Sesión |
|---------|------------------|----------------
| **Capacidad** | ~1.300 tokens total | Ilimitado (todas las sesiones) |
| **Velocidad** | Instantáneo (en indicador del sistema) | Requiere búsqueda + resumen de LLM |
| **Caso de uso** | Hechos clave siempre disponibles | Encontrar conversaciones pasadas específicas |
| **Gestión** | Curado manualmente por agente | Automático — todas las sesiones almacenadas |
| **Costo de token** | Fijo por sesión (~1.300 tokens) | Bajo demanda (buscado cuando es necesario) |

**Memoria** es para hechos críticos que siempre deben estar en contexto. **Búsqueda de Sesión** es para consultas "¿discutimos X la semana pasada?" donde el agente necesita recordar detalles específicos de conversaciones pasadas.

## Configuración

```yaml
# In ~/.hermes/config.yaml
memory:
  memory_enabled: true
  user_profile_enabled: true
  memory_char_limit: 2200   # ~800 tokens
  user_char_limit: 1375     # ~500 tokens
```

## Integración Honcho (Modelado de Usuario Entre Sesiones)

Para una comprensión de usuario más profunda y generada por IA que funcione entre sesiones y plataformas, puedes habilitar [Memoria honcho](./honcho.md). honcho se ejecuta junto a la Memoria incorporada en modo `hybrid` (el predeterminado) — `Memoria.md` y `USER.md` permanecen como están, y honcho agrega una capa de modelado de usuario persistente encima.

```bash
hermes honcho setup
```

Ver la documentación [Memoria honcho](./honcho.md) para referencia completa de Configuración, Herramientas y CLI.
