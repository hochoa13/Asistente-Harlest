---
title: Enrutamiento de Proveedor
description: Configura las preferencias de proveedor de openrouter para optimizar por costo, velocidad o calidad.
sidebar_label: Enrutamiento de Proveedor
sidebar_position: 7
---

# Enrutamiento de Proveedor

Cuando usas [openrouter](https://openrouter.ai) como tu proveedor de LLM, Hermes Agent admite **Enrutamiento de Proveedor** — control granular sobre qué Proveedores de IA subyacentes manejan tus solicitudes y cómo se priorizan.

openrouter enruta solicitudes a muchos Proveedores (ej., Anthropic, Google, AWS Bedrock, Together AI). El Enrutamiento de Proveedor te permite optimizar por costo, velocidad, calidad o aplicar Requisitos de proveedor específicos.

## Configuración

Agrega una sección `provider_routing` a tu `~/.hermes/config.yaml`:

```yaml
provider_routing:
  sort: "price"           # Cómo clasificar proveedores
  only: []                # Lista blanca: solo usar estos proveedores
  ignore: []              # Lista negra: nunca usar estos proveedores
  order: []               # Orden explícito de prioridad de proveedor
  require_parameters: false  # Solo usar proveedores que soporten todos los parámetros
  data_collection: null   # Controlar recopilación de datos ("allow" o "deny")
```

:::info
El Enrutamiento de Proveedor solo se aplica cuando usas openrouter. No tiene efecto con conexiones directas de proveedor (ej., conectar directamente a la API de Anthropic).
:::

## Opciones

### `sort`

Controla cómo openrouter clasifica los Proveedores disponibles para tu solicitud.

| Valor | Descripción |
|-------|-------------|
| `"price"` | Proveedor más barato primero |
| `"throughput"` | Tokens más rápidos por segundo primero |
| `"latency"` | Menor tiempo para primer token primero |

```yaml
provider_routing:
  sort: "price"
```

### `only`

Lista blanca de nombres de proveedor. Cuando se establece, **solo** se usarán estos Proveedores. Todos los demás se excluyen.

```yaml
provider_routing:
  only:
    - "Anthropic"
    - "Google"
```

### `ignore`

Lista negra de nombres de proveedor. Estos Proveedores **nunca** se usarán, incluso si ofrecen la opción más barata o más rápida.

```yaml
provider_routing:
  ignore:
    - "Together"
    - "DeepInfra"
```

### `order`

Orden de prioridad explícito. Los Proveedores enumerados primero son preferidos. Los Proveedores no enumerados se usan como alternativas.

```yaml
provider_routing:
  order:
    - "Anthropic"
    - "Google"
    - "AWS Bedrock"
```

### `require_parameters`

Cuando es `true`, openrouter solo enrutará a Proveedores que soporten **todos** los Parámetros en tu solicitud (como `temperature`, `top_p`, `tools`, etc.). Esto evita caidas silenciosas de parámetros.

```yaml
provider_routing:
  require_parameters: true
```

### `data_collection`

Controla si los Proveedores pueden usar tus indicadores para entrenamiento. Las opciones son `"allow"` o `"deny"`.

```yaml
provider_routing:
  data_collection: "deny"
```

## Ejemplos Prácticos

### Optimizar por Costo

Enruta al proveedor más barato disponible. Bueno para uso de alto volumen y desarrollo:

```yaml
provider_routing:
  sort: "price"
```

### Optimizar por Velocidad

Prioriza Proveedores de baja latencia para uso interactivo:

```yaml
provider_routing:
  sort: "latency"
```

### Optimizar por Rendimiento

Mejor para generación de texto largo donde importa tokens por segundo:

```yaml
provider_routing:
  sort: "throughput"
```

### Bloquear a Proveedores Específicos

Asegura que todas las solicitudes pasen por un proveedor específico por consistencia:

```yaml
provider_routing:
  only:
    - "Anthropic"
```

### Evitar Proveedores Específicos

Excluye Proveedores que no deseas usar (ej., por privacidad de datos):

```yaml
provider_routing:
  ignore:
    - "Together"
    - "Lepton"
  data_collection: "deny"
```

### Orden Preferido con Alternativas

Intenta tus Proveedores preferidos primero, cambia a otros si no están disponibles:

```yaml
provider_routing:
  order:
    - "Anthropic"
    - "Google"
  require_parameters: true
```

## Cómo Funciona

Las preferencias de Enrutamiento de Proveedor se pasan a la API de openrouter a través del campo `extra_body.provider` en cada llamada de API. Esto se aplica a ambos:

- **Modo CLI** — configurado en `~/.hermes/config.yaml`, cargado al inicio
- **Modo Gateway** — mismo archivo de configuración, cargado cuando se inicia la puerta de enlace

La configuración de enrutamiento se lee desde `config.yaml` y se pasa como Parámetros al crear el `AIAgent`:

```
providers_allowed  ← from provider_routing.only
providers_ignored  ← from provider_routing.ignore
providers_order    ← from provider_routing.order
provider_sort      ← from provider_routing.sort
provider_require_parameters ← from provider_routing.require_parameters
provider_data_collection    ← from provider_routing.data_collection
```

:::tip
Puedes combinar múltiples Opciones. Por ejemplo, ordena por precio pero excluye ciertos Proveedores y requiere soporte de parámetros:

```yaml
provider_routing:
  sort: "price"
  ignore: ["Together"]
  require_parameters: true
  data_collection: "deny"
```
:::

## Comportamiento Predeterminado

Cuando no se configura una sección `provider_routing` (el predeterminado), openrouter usa su lógica de enrutamiento predeterminada, que generalmente equilibra costo y disponibilidad automáticamente.
