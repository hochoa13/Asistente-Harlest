---
sidebar_position: 7
title: "Delegación de Subagentes"
description: "Genera instancias de agentes hijo aisladas para flujos de trabajo paralelos con delegate_task"
---

# Delegación de Subagentes

La herramienta `delegate_task` genera instancias de AIAgent hijo con contexto aislado, conjuntos de herramientas restringidos y sus propias sesiones de terminal. Cada hijo obtiene una conversación fresca y trabaja independientemente — solo su resumen final entra en el contexto del padre.

## Tarea Única

```python
delegate_task(
    goal="Debug why tests fail",
    context="Error: assertion in test_foo.py line 42",
    toolsets=["terminal", "file"]
)
```

## Lote Paralelo

Hasta 3 subagentes concurrentes:

```python
delegate_task(tasks=[
    {"goal": "Search topic A", "toolsets": ["web"]},
    {"goal": "Search topic B", "toolsets": ["web"]},
    {"goal": "Fix the build", "toolsets": ["terminal", "file"]}
])
```

## Cómo Funciona el Contexto del Subagente

:::advertencia Crítico: Los subagentes no Saben Nada
Los subagentes comienzan con una **conversación completamente fresca**. No tienen conocimiento del historial de conversación del padre, llamadas de herramientas anteriores o nada discutido antes de la delegación. El único contexto del subagente proviene de los campos `goal` y `context` que proporcionas.
:::

Esto significa que debes pasar **todo** lo que el subagente necesita:

```python
# MAL - el subagente no tiene idea qué es "el error"
delegate_task(goal="Fix the error")

# BIEN - el subagente tiene todo el contexto que necesita
delegate_task(
    goal="Fix the TypeError in api/handlers.py",
    context="""El archivo api/handlers.py tiene un TypeError en la línea 47:
    'NoneType' object has no attribute 'get'.
    La función process_request() recibe un dict de parse_body(),
    pero parse_body() devuelve None cuando Content-Type está ausente.
    El proyecto está en /home/user/myproject y usa Python 3.11."""
)
```

El subagente recibe un indicador del sistema enfocado construido a partir de tu goal y context, instruyéndole a completar la tarea y proporcionar un resumen estructurado de qué hizo, qué encontró, qué archivos modificó y cualquier problema encontrado.

## Ejemplos Prácticos

### Búsqueda Paralela

Búsqueda de múltiples temas simultáneamente y recopilación de resúmenes:

```python
delegate_task(tasks=[
    {
        "goal": "Search the current state of WebAssembly in 2025",
        "context": "Focus on: browser support, non-browser runtimes, language support",
        "toolsets": ["web"]
    },
    {
        "goal": "Search the current state of RISC-V adoption in 2025",
        "context": "Focus on: server chips, embedded systems, software ecosystem",
        "toolsets": ["web"]
    },
    {
        "goal": "Search quantum computing progress in 2025",
        "context": "Focus on: error correction breakthroughs, practical applications, key players",
        "toolsets": ["web"]
    }
])
```

### Revisión de Código + Arreglo

Delega un flujo de trabajo de revisión y arreglo a un contexto fresco:

```python
delegate_task(
    goal="Review the authentication module for security issues and fix any found",
    context="""Project at /home/user/webapp.
    Auth module files: src/auth/login.py, src/auth/jwt.py, src/auth/middleware.py.
    The project uses Flask, PyJWT, and bcrypt.
    Focus on: SQL injection, JWT validation, password handling, session management.
    Fix any issues found and run the test suite (pytest tests/auth/).""",
    toolsets=["terminal", "file"]
)
```

### Refactorización Multi-Archivo

Delega una tarea de refactorización grande que inundaría el contexto del padre:

```python
delegate_task(
    goal="Refactor all Python files in src/ to replace print() with proper logging",
    context="""Project at /home/user/myproject.
    Use the 'logging' module with logger = logging.getLogger(__name__).
    Replace print() calls with appropriate log levels:
    - print(f"Error: ...") -> logger.error(...)
    - print(f"Warning: ...") -> logger.warning(...)
    - print(f"Debug: ...") -> logger.debug(...)
    - Other prints -> logger.info(...)
    Don't change print() in test files or CLI output.
    Run pytest after to verify nothing broke.""",
    toolsets=["terminal", "file"]
)
```

## Detalles del Modo de Lote

Cuando proporcionas un array `tasks`, los subagentes se ejecutan en **paralelo** usando un thread pool:

- **Concurrencia máxima:** 3 tareas (el array `tasks` se trunca a 3 si es más largo)
- **Thread pool:** Usa `ThreadPoolExecutor` con `MAX_CONCURRENT_CHILDREN = 3` workers
- **Visualización del progreso:** En modo CLI, una vista de árbol muestra llamadas de herramientas de cada subagente en tiempo real con líneas de finalización por tarea. En modo gateway, el progreso se agrupa en lotes y se envía al callback de progreso del padre
- **Ordenamiento de resultados:** Los resultados se ordenan por índice de tarea para coincidir con el orden de entrada independientemente del orden de finalización
- **Propagación de interrupción:** Interrumpir al padre (p. ej., enviar un nuevo mensaje) interrumpe todos los hijos activos

La delegación de tarea única se ejecuta directamente sin gastos generales del thread pool.

## Anulación de Modelo

Puedes usar un modelo diferente para subagentes — útil para delegar tareas simples a modelos más baratos/rápidos:

```python
delegate_task(
    goal="Summarize this README file",
    context="File at /project/README.md",
    toolsets=["file"],
    model="google/gemini-flash-2.0"  # Modelo más barato para tareas simples
)
```

Si se omite, los subagentes usan el mismo modelo que el padre.

## Consejos de Selección de Conjunto de Herramientas

El parámetro `toolsets` controla a qué herramientas tiene acceso el subagente. Elige basándote en la tarea:

| Patrón de Conjunto de Herramientas | Caso de Uso |
|----------------|----------|
| `["terminal", "file"]` | Trabajo de código, depuración, edición de archivos, compilaciones |
| `["web"]` | Búsqueda, verificación de hechos, búsqueda de documentación |
| `["terminal", "file", "web"]` | Tareas full-stack (predeterminado) |
| `["file"]` | Análisis de solo lectura, revisión de código sin ejecución |
| `["terminal"]` | Administración del sistema, gestión de procesos |

Ciertos conjuntos de herramientas siempre están **bloqueados** para subagentes independientemente de lo que especifiques:
- `delegate` — sin delegación recursiva (evita generación infinita)
- `clarify` — los subagentes no pueden interactuar con el usuario
- `memory` — sin escrituras a memoria persistente compartida
- `code_execution` — los hijos deben razonar paso a paso
- `send_message` — sin efectos secundarios entre plataformas (p. ej., enviar mensajes de Telegram)

## Iteraciones Máximas

Cada subagente tiene un límite de iteración (predeterminado: 50) que controla cuántos turnos de llamada de herramienta puede tomar:

```python
delegate_task(
    goal="Quick file check",
    context="Check if /etc/nginx/nginx.conf exists and print its first 10 lines",
    max_iterations=10  # Tarea simple, no necesita muchos turnos
)
```

## Límite de Profundidad

La delegación tiene un **límite de profundidad de 2** — un padre (profundidad 0) puede generar hijos (profundidad 1), pero los hijos no pueden delegar más. Esto evita cadenas de delegación recursiva desenfrenada.

## Propiedades Clave

- Cada subagente obtiene su **propia sesión de terminal** (separada del padre)
- **Sin delegación anidada** — los hijos no pueden delegar más (sin nietos)
- Los subagentes **no pueden** llamar a: `delegate_task`, `clarify`, `memory`, `send_message`, `execute_code`
- **Propagación de interrupción** — interrumpir al padre interrumpe todos los hijos activos
- Solo el resumen final entra en el contexto del padre, manteniendo eficiente el uso de tokens
- Los subagentes heredan la **clave API y configuración del proveedor** del padre

## Delegación vs execute_code

| Factor | delegate_task | execute_code |
|--------|--------------|-------------|
| **Razonamiento** | Bucle completo de razonamiento de LLM | Solo ejecución de Python |
| **Contexto** | Conversación aislada fresca | Sin conversación, solo script |
| **Acceso a herramientas** | Todas las herramientas no bloqueadas con razonamiento | 7 herramientas a través de RPC, sin razonamiento |
| **Paralelismo** | Hasta 3 subagentes concurrentes | Script único |
| **Mejor para** | Tareas complejas que requieren juicio | Tuberías mecánicas de múltiples pasos |
| **Costo de token** | Más alto (bucle LLM completo) | Más bajo (solo stdout devuelto) |
| **User interaction** | None (subagentes can't clarify) | None |

**Rule of thumb:** Usar `delegate_task` when the subtask requires reasoning, judgment, or multi-step problem solving. Usar `execute_code` when you need mechanical data processing or scripted workflows.

## Configuración

```yaml
# In ~/.hermes/config.yaml
delegation:
  max_iterations: 50                        # Max turns per child (default: 50)
  default_toolsets: ["terminal", "file", "web"]  # Default toolsets
```

:::Consejo
The agent handles Delegación automatically based on the task complexity. You don't need to explicitly ask it to delegate — it will do so when it makes sense.
:::
