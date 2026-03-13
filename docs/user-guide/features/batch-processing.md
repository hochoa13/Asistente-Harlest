---
sidebar_position: 12
title: "Procesamiento por Lotes"
description: "Generate agent trajectories at scale — parallel processing, puntos de control, and conjunto de herramientas distributions"
---

# Procesamiento por Lotes

Procesamiento por lotes lets you Ejecutar the Hermes agent across hundreds or thousands of prompts in parallel, generating structured trajectory data. This is primarily used for **generación de datos de entrenamiento** — producing ShareGPT-format trajectories with herramienta Uso statistics that can be used for fine-tuning or evaluation.

## Descripción General

The batch runner (`batch_runner.py`) processes a JSONL dataset of prompts, running each through a full agent session with herramienta access. Each prompt gets its own isolated entorno. The output is structured trajectory data with full conversation history, herramienta call statistics, and reasoning coverage metrics.

## Quick Iniciar

```bash
# Basic batch run
python batch_runner.py \
    --dataset_file=data/prompts.jsonl \
    --batch_size=10 \
    --run_name=my_first_run \
    --model=anthropic/claude-sonnet-4-20250514 \
    --num_workers=4

# Resume an interrupted run
python batch_runner.py \
    --dataset_file=data/prompts.jsonl \
    --batch_size=10 \
    --run_name=my_first_run \
    --reanudar

# List available toolset distributions
python batch_runner.py --list_distributions
```

## formato de dataset

The input dataset is a JSONL archivo (one JSON object per line). Each entry must have a `prompt` field:

```jsonl
{"prompt": "Write a Python function that finds the longest palindromic substring"}
{"prompt": "Create a REST API endpoint for user authentication using Flask"}
{"prompt": "Debug this error: TypeError: cannot unpack non-iterable NoneType object"}
```

Entries can optionally include:
- `image` or `docker_image`: A container image to Usar for this prompt's sandbox segura (works with docker, modal, and singularity backends)
- `cwd`: Working directorio override for the task's terminal session

## Configuración Opciones

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--dataset_file` | (required) | ruta to JSONL dataset |
| `--batch_size` | (required) | Prompts per batch |
| `--run_name` | (required) | Name for this Ejecutar (used for output dir and puntos de control) |
| `--distribution` | `"default"` | Herramientaset distribution to sample from |
| `--model` | `claude-sonnet-4-20250514` | Model to Usar |
| `--base_url` | `https://openrouter.ai/API/v1` | API base URL |
| `--api_key` | (env var) | clave API for model |
| `--max_turns` | `10` | Maximum herramienta-calling iterations per prompt |
| `--num_workers` | `4` | Parallel worker processes |
| `--reanudar` | `false` | Resume from punto de control |
| `--verbose` | `false` | Habilitar verbose logging |
| `--max_samples` | all | Only process first N samples from dataset |
| `--max_tokens` | model default | Maximum tokens per model response |

### Enrutamiento de Proveedor (openrouter)

| Parameter | Description |
|-----------|-------------|
| `--providers_allowed` | Comma-separated Proveedores to allow (e.g., `"anthropic,openai"`) |
| `--providers_ignored` | Comma-separated Proveedores to ignorar (e.g., `"together,deepinfra"`) |
| `--providers_order` | Comma-separated preferred provider order |
| `--provider_sort` | Sort by `"price"`, `"throughput"`, or `"latency"` |

### Reasoning control

| Parameter | Description |
|-----------|-------------|
| `--reasoning_effort` | Effort level: `xhigh`, `high`, `medium`, `low`, `minimal`, `none` |
| `--reasoning_disabled` | Completoly Deshabilitar reasoning/thinking tokens |

### Advanced Opciones

| Parameter | Description |
|-----------|-------------|
| `--ephemeral_system_prompt` | System prompt used during execution but NOT saved to trajectories |
| `--log_prefix_chars` | Characters to show in log previews (default: 100) |
| `--prefill_messages_file` | ruta to JSON archivo with prefill messages for few-shot priming |

## Herramientaset Distributions

Each prompt gets a randomly sampled Establecer of Conjuntos de herramientas from a **distribution**. This ensures datos de entrenamiento covers diverse herramienta combinations. Usar `--list_distributions` to see all available distributions.

Distributions define probability weights for each conjunto de herramientas combination. Por ejemplo, a "default" distribution might assign high probability to `["terminal", "archivo", "web"]` and lower probability to web-only or archivo-only combinations.

## Output Format

All output goes to `data/<run_name>/`:

```
data/my_run/
├── trajectories.jsonl    # Combined final output (all batches merged)
├── batch_0.jsonl         # Individual batch results
├── batch_1.jsonl
├── ...
├── checkpoint.json       # Resume checkpoint
└── statistics.json       # Aggregate tool usage stats
```

### formato de trayectoria

Each line in `trajectories.jsonl` is a JSON object:

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

The `conversations` field uses a ShareGPT-like format with `from` and `value` fields. herramienta stats are normalized to include all possible Herramientas with zero defaults, ensuring consistent esquema across entries for HuggingFace datasets compatibility.

## puntos de control

The batch runner has robust puntos de control for fault tolerance:

- **punto de control archivo:** Saved after each batch completes, seguimiento which prompt indices are done
- **Content-based reanudar:** On `--reanudar`, the runner scans existing batch files and matches completed prompts by their actual text content (not just indices), enabling recovery even if the dataset order changes
- **Failed prompts:** Only successfully completed prompts are marked as done — failed prompts will be retried on reanudar
- **Batch merging:** On completion, all batch files (including from previous runs) are merged into a single `trajectories.jsonl`

### How Resume Works

1. Scan all `batch_*.jsonl` files for completed prompts (by content matching)
2. Filter the dataset to exclude already-completed prompts
3. Re-batch the remaining prompts
4. Process only the remaining prompts
5. Merge all batch files (old + new) into final output

## Quality Filtering

The batch runner applies automatic quality filtering:

- **No-reasoning filter:** Samples where zero assistant turns contain reasoning (no `<REASONING_SCRATCHPAD>` or native thinking tokens) are discarded
- **Corrupted entry filter:** Entries with hallucinated herramienta names (not in the valid herramienta list) are filtered out during the final merge
- **Reasoning statistics:** Tracks percentage of turns with/without reasoning across the entire Ejecutar

## Statistics

After completion, the runner prints comprehensive statistics:

- **herramienta Uso:** Call counts, success/failure rates per herramienta
- **Reasoning coverage:** Percentage of assistant turns with reasoning
- **Samples discarded:** Count of samples filtered for lacking reasoning
- **Duration:** Total processing time

Statistics are also saved to `statistics.json` for programmatic analysis.

## Usar Cases

### generación de datos de entrenamiento

Generate diverse herramienta-Usar trajectories for fine-tuning:

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
