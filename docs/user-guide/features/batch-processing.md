---
sidebar_position: 12
title: "Procesamiento por Lotes"
description: "Genera trayectorias de agentes a escala — procesamiento paralelo, puntos de control y distribuciones de conjuntos de herramientas"
---

# Procesamiento por Lotes

El procesamiento por lotes te permite ejecutar el agente Hermes en paralelo a través de cientos o miles de indicaciones, generando datos de trayectoria estructurados. Se utiliza principalmente para **generación de datos de entrenamiento** — produciendo trayectorias en formato ShareGPT con estadísticas de uso de herramientas que se pueden usar para ajuste fino o evaluación.

## Descripción General

El ejecutor de lotes (`batch_runner.py`) procesa un conjunto de datos JSONL de indicaciones, ejecutando cada una a través de una sesión de agente completa con acceso a herramientas. Cada indicación obtiene su propio entorno aislado. La salida es datos de trayectoria estructurados con historial completo de conversación, estadísticas de llamadas de herramientas y métricas de cobertura de razonamiento.

## Inicio Rápido

```bash
# Ejecución básica de lotes
python batch_runner.py \
    --dataset_file=data/prompts.jsonl \
    --batch_size=10 \
    --run_name=my_first_run \
    --model=anthropic/claude-sonnet-4-20250514 \
    --num_workers=4

# Reanudar una ejecución interrumpida
python batch_runner.py \
    --dataset_file=data/prompts.jsonl \
    --batch_size=10 \
    --run_name=my_first_run \
    --reanudar

# Listar distribuciones de conjuntos de herramientas disponibles
python batch_runner.py --list_distributions
```

## Formato de Conjunto de Datos

El conjunto de datos de entrada es un archivo JSONL (un objeto JSON por línea). Cada entrada debe tener un campo `prompt`:

```jsonl
{"prompt": "Write a Python function that finds the longest palindromic substring"}
{"prompt": "Create a REST API endpoint for user authentication using Flask"}
{"prompt": "Debug this error: TypeError: cannot unpack non-iterable NoneType object"}
```

Las entradas pueden incluir opcionalmente:
- `image` o `docker_image`: Una imagen de contenedor a usar para la zona de pruebas segura de esta indicación (funciona con backends docker, modal y singularity)
- `cwd`: Anulación del directorio de trabajo para la sesión de terminal de la tarea

## Opciones de Configuración

| Parámetro | Predeterminado | Descripción |
|-----------|---------|-------------|
| `--dataset_file` | (requerido) | Ruta al conjunto de datos JSONL |
| `--batch_size` | (requerido) | Indicaciones por lote |
| `--run_name` | (requerido) | Nombre para esta ejecución (se usa para directorio de salida y puntos de control) |
| `--distribution` | `"default"` | Distribución de conjunto de herramientas a partir de la cual muestrear |
| `--model` | `claude-sonnet-4-20250514` | Modelo a usar |
| `--base_url` | `https://openrouter.ai/API/v1` | URL base de API |
| `--api_key` | (variable de entorno) | Clave API para el modelo |
| `--max_turns` | `10` | Máximo de iteraciones de llamada de herramientas por indicación |
| `--num_workers` | `4` | Procesos de trabajo paralelos |
| `--reanudar` | `false` | Reanudar desde punto de control |
| `--verbose` | `false` | Habilitar registro detallado |
| `--max_samples` | todo | Solo procesar las primeras N muestras del conjunto de datos |
| `--max_tokens` | predeterminado del modelo | Máximo de tokens por respuesta del modelo |

### Enrutamiento de Proveedor (OpenRouter)

| Parámetro | Descripción |
|-----------|-------------|
| `--providers_allowed` | Proveedores separados por comas a permitir (p. ej., `"anthropic,openai"`) |
| `--providers_ignored` | Proveedores separados por comas a ignorar (p. ej., `"together,deepinfra"`) |
| `--providers_order` | Orden de proveedores preferidos separados por comas |
| `--provider_sort` | Ordenar por `"price"`, `"throughput"` o `"latency"` |

### Control de Razonamiento

| Parámetro | Descripción |
|-----------|-------------|
| `--reasoning_effort` | Nivel de esfuerzo: `xhigh`, `high`, `medium`, `low`, `minimal`, `none` |
| `--reasoning_disabled` | Deshabilitar completamente tokens de razonamiento/pensamiento |

### Opciones Avanzadas

| Parámetro | Descripción |
|-----------|-------------|
| `--ephemeral_system_prompt` | Indicación del sistema utilizada durante la ejecución pero NO guardada en trayectorias |
| `--log_prefix_chars` | Caracteres a mostrar en vistas previas de registro (predeterminado: 100) |
| `--prefill_messages_file` | Ruta al archivo JSON con mensajes de relleno previo para iniciación con pocos ejemplos |

## Distribuciones de Conjuntos de Herramientas

Cada indicación obtiene un conjunto muestreado aleatoriamente de conjuntos de herramientas de una **distribución**. Esto asegura que los datos de entrenamiento cubran combinaciones diversas de herramientas. Usa `--list_distributions` para ver todas las distribuciones disponibles.

Las distribuciones definen pesos de probabilidad para cada combinación de conjunto de herramientas. Por ejemplo, una distribución "default" podría asignar alta probabilidad a `["terminal", "archivo", "web"]` y menor probabilidad a combinaciones solo web o solo archivo.

## Formato de Salida

Toda la salida va a `data/<run_name>/`:

```
data/my_run/
├── trajectories.jsonl    # Salida final combinada (todos los lotes fusionados)
├── batch_0.jsonl         # Resultados del lote individual
├── batch_1.jsonl
├── ...
├── checkpoint.json       # Punto de control para reanudar
└── statistics.json       # Estadísticas de uso de herramientas agregadas
```

### Formato de Trayectoria

Cada línea en `trajectories.jsonl` es un objeto JSON:

```json
{
  "prompt_index": 42,
  "conversations": [
    {"from": "human", "value": "Write a function..."},
    {"from": "gpt", "value": "I'll create that function...",
     "tool_calls": [...]},
    {"from": "tool", "value": "..."},
    {"from": "gpt", "value": "Here's the completed function..."}
  ],
  "metadata": {
    "batch_num": 2,
    "timestamp": "2026-01-15T10:30:00",
    "model": "anthropic/claude-sonnet-4-20250514"
  },
  "completed": true,
  "partial": false,
  "api_calls": 3,
  "toolsets_used": ["terminal", "file"],
  "tool_stats": {
    "terminal": {"count": 2, "success": 2, "failure": 0},
    "read_file": {"count": 1, "success": 1, "failure": 0}
  },
  "tool_error_counts": {
    "terminal": 0,
    "read_file": 0
  }
}
```

El campo `conversations` usa un formato similar a ShareGPT con campos `from` y `value`. Las estadísticas de herramientas se normalizan para incluir todas las herramientas posibles con ceros por defecto, asegurando un esquema consistente entre entradas para compatibilidad con conjuntos de datos de HuggingFace.

## Puntos de Control

El ejecutor de lotes tiene puntos de control robustos para tolerancia a fallos:

- **Archivo de punto de control:** Se guarda después de que cada lote se completa, rastreando qué índices de indicación están hechos
- **Reanudar basado en contenido:** En `--reanudar`, el ejecutor escanea archivos de lotes existentes y coincide las indicaciones completadas por su contenido de texto real (no solo índices), permitiendo recuperación incluso si el orden del conjunto de datos cambia
- **Indicaciones fallidas:** Solo las indicaciones completadas con éxito se marcan como hechas — las indicaciones fallidas se reintentarán al reanudar
- **Fusión de lotes:** Al completarse, todos los archivos de lotes (incluidos de ejecuciones anteriores) se fusionan en un único `trajectories.jsonl`

### Cómo Funciona Reanudar

1. Escanear todos los archivos `batch_*.jsonl` para indicaciones completadas (por coincidencia de contenido)
2. Filtrar el conjunto de datos para excluir indicaciones ya completadas
3. Re-dividir en lotes las indicaciones restantes
4. Procesar solo las indicaciones restantes
5. Fusionar todos los archivos de lotes (antiguos + nuevos) en la salida final

## Filtrado de Calidad

El ejecutor de lotes aplica filtrado automático de calidad:

- **Filtro sin razonamiento:** Las muestras donde ningún turno del asistente contiene razonamiento (sin `<REASONING_SCRATCHPAD>` o tokens de pensamiento nativos) se descartan
- **Filtro de entrada corrupta:** Las entradas con nombres de herramientas alucinadas (no en la lista válida de herramientas) se filtran durante la fusión final
- **Estadísticas de razonamiento:** Rastrea el porcentaje de turnos con/sin razonamiento en toda la ejecución

## Estadísticas

Después de la finalización, el ejecutor imprime estadísticas completas:

- **Uso de herramientas:** Recuentos de llamadas, tasas de éxito/fallo por herramienta
- **Cobertura de razonamiento:** Porcentaje de turnos del asistente con razonamiento
- **Muestras descartadas:** Recuento de muestras filtradas por falta de razonamiento
- **Duración:** Tiempo total de procesamiento

Las estadísticas también se guardan en `statistics.json` para análisis programático.

## Casos de Uso

### Generación de Datos de Entrenamiento

Genera trayectorias diversas de uso de herramientas para ajuste fino:

```bash
python batch_runner.py \
    --dataset_file=data/coding_prompts.jsonl \
    --batch_size=20 \
    --run_name=coding_v1 \
    --model=anthropic/claude-sonnet-4-20250514 \
    --num_workers=8 \
    --distribution=default \
    --max_turns=15
```

### Model Evaluation

Evaluate how well a model uses Herramientas across standardized prompts:

```bash
python batch_runner.py \
    --dataset_file=data/eval_suite.jsonl \
    --batch_size=10 \
    --run_name=eval_gpt4 \
    --model=openai/gpt-4o \
    --num_workers=4 \
    --max_turns=10
```

### Per-Prompt Container Images

For benchmarks requiring specific environments, each prompt can specify its own container image:

```jsonl
{"prompt": "Install numpy and compute eigenvalues of a 3x3 matrix", "image": "python:3.11-slim"}
{"prompt": "Compile this Rust program and run it", "image": "rust:1.75"}
{"prompt": "Set up a Node.js Express server", "image": "node:20-alpine", "cwd": "/app"}
```

The batch runner verifies docker images are accessible before running each prompt.
