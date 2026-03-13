---
title: Enrutamiento de Proveedor
description: Configurar openrouter provider preferences to optimize for cost, speed, or quality.
sidebar_label: Enrutamiento de Proveedor
sidebar_position: 7
---

# Enrutamiento de Proveedor

When using [openrouter](https://openrouter.ai) as your LLM provider, Hermes Agent supports **Enrutamiento de Proveedores** — fine-grained control over which underlying AI Proveedores handle your requests and how they're prioritized.

openrouter routes requests to many Proveedores (e.g., Anthropic, Google, AWS Bedrock, Together AI). Enrutamiento de Proveedores lets you optimize for cost, speed, quality, or enforce specific provider Requisitos.

## Configuración

Add a `provider_routing` Sección to your `~/.hermes/config.yaml`:

```yaml
provider_routing:
  sort: "price"           # Cómo rank providers
  only: []                # Whitelist: only use these providers
  ignore: []              # Blacklist: never use these providers
  order: []               # Explicit provider priority order
  require_parameters: false  # Only use providers that support all parameters
  data_collection: null   # Control data collection ("allow" or "deny")
```

:::Información
Enrutamiento de Proveedores only applies when using openrouter. It has no effect with direct provider connections (e.g., connecting directly to the Anthropic API).
:::

## Opciones

### `sort`

Controls how openrouter ranks available Proveedores for your request.

| Value | Description |
|-------|-------------|
| `"price"` | Cheapest provider first |
| `"throughput"` | Fastest tokens-per-second first |
| `"latency"` | Lowest time-to-first-token first |

```yaml
provider_routing:
  sort: "price"
```

### `only`

lista blanca of provider names. When Establecer, **only** these Proveedores will be used. All others are excluded.

```yaml
provider_routing:
  only:
    - "Anthropic"
    - "Google"
```

### `ignorar`

Blacklist of provider names. These Proveedores will **never** be used, even if they offer the cheapest or fastest option.

```yaml
provider_routing:
  ignore:
    - "Together"
    - "DeepInfra"
```

### `order`

Explicit priority order. Proveedores listed first are preferred. Unlisted Proveedores are used as fallbacks.

```yaml
provider_routing:
  order:
    - "Anthropic"
    - "Google"
    - "AWS Bedrock"
```

### `require_parameters`

When `true`, openrouter will only route to Proveedores that support **all** Parámetros in your request (like `temperature`, `top_p`, `Herramientas`, etc.). This avoids silent parameter drops.

```yaml
provider_routing:
  require_parameters: true
```

### `data_collection`

Controls whether Proveedores can Usar your prompts for training. Opciones are `"allow"` or `"deny"`.

```yaml
provider_routing:
  data_collection: "deny"
```

## Practical Ejemplos

### Optimize for Cost

Route to the cheapest available provider. Good for high-volume Uso and development:

```yaml
provider_routing:
  sort: "price"
```

### Optimize for Speed

Prioritize low-latency Proveedores for interactive Usar:

```yaml
provider_routing:
  sort: "latency"
```

### Optimize for Throughput

Best for long-form generation where tokens-per-second matters:

```yaml
provider_routing:
  sort: "throughput"
```

### Lock to Specific Proveedores

Ensure all requests go through a specific provider for consistency:

```yaml
provider_routing:
  only:
    - "Anthropic"
```

### Avoid Specific Proveedores

Exclude Proveedores you don't want to Usar (e.g., for data privacy):

```yaml
provider_routing:
  ignore:
    - "Together"
    - "Lepton"
  data_collection: "deny"
```

### Preferred Order with Fallbacks

Try your preferred Proveedores first, fall back to others if unavailable:

```yaml
provider_routing:
  order:
    - "Anthropic"
    - "Google"
  require_parameters: true
```

## How It Works

Enrutamiento de Proveedores preferences are passed to the openrouter API via the `extra_body.provider` field on every API call. This applies to both:

- **CLI mode** — configured in `~/.hermes/config.yaml`, loaded at startup
- **Gateway mode** — same config archivo, loaded when the gateway starts

The routing config is read from `config.yaml` and passed as Parámetros when creating the `AIAgent`:

```
providers_allowed  ← from provider_routing.only
providers_ignored  ← from provider_routing.ignore
providers_order    ← from provider_routing.order
provider_sort      ← from provider_routing.sort
provider_require_parameters ← from provider_routing.require_parameters
provider_data_collection    ← from provider_routing.data_collection
```

:::Consejo
You can combine multiple Opciones. Por ejemplo, sort by price but exclude certain Proveedores and require parameter support:

```yaml
provider_routing:
  sort: "price"
  ignore: ["Together"]
  require_parameters: true
  data_collection: "deny"
```
:::

## Default Behavior

When no `provider_routing` Sección is configured (the default), openrouter uses its own default routing logic, which generally balances cost and availability automatically.
