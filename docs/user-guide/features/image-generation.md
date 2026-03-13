---
title: Generación de Imágenes
description: Genera imágenes de alta calidad usando FLUX 2 Pro con ampliación automática a través de FAL.ai.
sidebar_label: Generación de Imágenes
sidebar_position: 6
---

# Generación de Imágenes

Hermes Agent puede generar imágenes a partir de indicaciones de texto usando el modelo **FLUX 2 Pro** de FAL.ai con ampliación automática 2x a través del **Clarity Upscaler** para mejorar la calidad.

## Configuración

### Obtener una Clave FAL API

1. Regístrate en [fal.ai](https://fal.ai/)
2. Genera una clave API desde tu panel

### Configurar la Clave

```bash
# Agregar a ~/.hermes/.env
FAL_KEY=your-fal-api-key-here
```

### Instalar la Biblioteca del Cliente

```bash
pip install fal-client
```

:::información
La herramienta de generación de imágenes está disponible automáticamente cuando se establece `FAL_KEY`. No se requiere configuración adicional de conjunto de herramientas.
:::

## Cómo Funciona

Cuando le pides a Hermes que genere una imagen:

1. **Generación** — Tu indicación se envía al modelo FLUX 2 Pro (`fal-ai/FLUX-2-pro`)
2. **Ampliación** — La imagen generada se amplia automáticamente 2x usando Clarity Upscaler (`fal-ai/clarity-upscaler`)
3. **Entrega** — La URL de imagen ampliada se devuelve

Si la ampliación falla por cualquier motivo, se devuelve la imagen original como respaldo.

## Uso

Simplemente pídele a Hermes que cree una imagen:

```
Generate an image of a serene mountain landscape with cherry blossoms
```

```
Create a portrait of a wise old owl perched on an ancient tree branch
```

```
Make me a futuristic cityscape with flying cars and neon lights
```

## Parámetros

La herramienta `image_generate_tool` acepta estos parámetros:

| Parámetro | Predeterminado | Rango | Descripción |
|-----------|---------|-------|-------------|
| `prompt` | *(requerido)* | — | Descripción de texto de la imagen deseada |
| `aspect_ratio` | `"landscape"` | `landscape`, `square`, `portrait` | Relación de aspecto de imagen |
| `num_inference_steps` | `50` | 1–10 | Número de pasos de desruido (más = calidad más alta, más lento) |
| `guidance_scale` | `4.5` | 0.1–20.0 | Cuán fielmente seguir la indicación |
| `num_images` | `1` | 1–4 | Número de imágenes a generar |
| `output_format` | `"png"` | `png`, `jpeg` | Formato de archivo de imagen |
| `seed` | *(aleatorio)* | cualquier entero | Semilla aleatoria para resultados reproducibles |

## Relaciones de Aspecto

La herramienta usa nombres de relación de aspecto simplificados que se asignan a tamaños de imagen FLUX 2 Pro:

| Relación de Aspecto | Se Asigna a | Mejor para |
|-------------|---------|----------|
| `landscape` | `landscape_16_9` | Fondos de pantalla, pancartas, escenas |
| `square` | `square_hd` | Imágenes de perfil, publicaciones en redes sociales |
| `portrait` | `portrait_16_9` | Arte de personajes, fondos de pantalla de teléfono |

:::consejo
También puedes usar preajustes de tamaño FLUX 2 Pro sin procesar directamente: `square_hd`, `square`, `portrait_4_3`, `portrait_16_9`, `landscape_4_3`, `landscape_16_9`. También se admiten tamaños personalizados de hasta 2048x2048.
:::

## Ampliación Automática

Cada imagen generada se amplia automáticamente 2x usando Clarity Upscaler de FAL.ai con estas configuraciones:

| Configuración | Valor |
|---------|-------|
| Factor de Ampliación | 2x |
| Creatividad | 0.35 |
| Semejanza | 0.6 |
| Escala de Guía | 4 |
| Pasos de Inferencia | 18 |
| Indicación Positiva | `"masterpiece, best quality, highres"` + tu indicación original |
| Indicación Negativa | `"(worst quality, low quality, normal quality:2)"` |

El ampliador mejora el detalle y la resolución mientras preserva la composición original. Si el ampliador falla (problema de red, límite de velocidad), la imagen en resolución original se devuelve automáticamente.

## Ejemplos de Indicaciones

Aquí hay algunas indicaciones efectivas para probar:

```
A candid street photo of a woman with a pink bob and bold eyeliner
```

```
Modern architecture building with glass facade, sunset lighting
```

```
Abstract art with vibrant colors and geometric patterns
```

```
Portrait of a wise old owl perched on ancient tree branch
```

```
Futuristic cityscape with flying cars and neon lights
```

## Depuración

Habilita registro de depuración para generación de imágenes:

```bash
export IMAGE_TOOLS_DEBUG=true
```

Los registros de depuración se guardan en `./logs/image_tools_debug_<session_id>.json` con detalles sobre cada solicitud de generación, parámetros, tiempo y cualquier error.

## Configuración de Seguridad

La herramienta de generación de imágenes se ejecuta con comprobaciones de seguridad deshabilitadas por defecto (`safety_tolerance: 5`, la configuración más permisiva). Esto se configura a nivel de código y no se puede ajustar por el usuario.

## Limitaciones

- **Requiere clave FAL API** — la generación de imágenes incurre en costos de API en tu cuenta FAL.ai
- **Sin edición de imagen** — esto es solo texto a imagen, sin inpainting o img2img
- **Entrega basada en URL** — las imágenes se devuelven como URLs temporales de FAL.ai, no se guardan localmente
- **Ampliación agrega latencia** — el paso de ampliación automática 2x agrega tiempo de procesamiento
- **Máximo 4 imágenes por solicitud** — `num_images` está limitado a 4
