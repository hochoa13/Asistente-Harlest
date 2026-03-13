---
title: Generación de Imágenes
description: Generate high-quality images using FLUX 2 Pro with automatic Aumento de escala via FAL.ai.
sidebar_label: Generación de Imágenes
sidebar_position: 6
---

# Generación de Imágenes

Hermes Agent can generate images from text prompts using FAL.ai's **FLUX 2 Pro** model with automatic 2x Aumento de escala via the **Clarity Upscaler** for enhanced quality.

## Configuración

### Obtener a API FAL Key

1. Sign up at [fal.ai](https://fal.ai/)
2. Generate an clave API from your dashboard

### Configurar the Key

```bash
# Add to ~/.hermes/.env
FAL_KEY=your-fal-api-key-here
```

### Instalar the Client Library

```bash
pip install fal-client
```

:::Información
The Generación de Imágenes herramienta is automatically available when `FAL_KEY` is Establecer. No additional conjunto de herramientas Configuración is needed.
:::

## How It Works

When you ask Hermes to generate an image:

1. **Generation** — Your prompt is sent to the FLUX 2 Pro model (`fal-ai/FLUX-2-pro`)
2. **Aumento de escala** — The generated image is automatically upscaled 2x using the Clarity Upscaler (`fal-ai/clarity-upscaler`)
3. **Delivery** — The upscaled image URL is returned

If Aumento de escala fails for any reason, the original image is returned as a fallback.

## Uso

Simply ask Hermes to Crear an image:

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

The `image_generate_tool` accepts these Parámetros:

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `prompt` | *(required)* | — | Text description of the desired image |
| `aspect_ratio` | `"landscape"` | `landscape`, `square`, `portrait` | Image aspect ratio |
| `num_inference_steps` | `50` | 1–100 | Number of denoising steps (more = higher quality, slower) |
| `guidance_scale` | `4.5` | 0.1–20.0 | How closely to follow the prompt |
| `num_images` | `1` | 1–4 | Number of images to generate |
| `output_format` | `"png"` | `png`, `jpeg` | Image archivo format |
| `seed` | *(random)* | any integer | Random seed for reproducible results |

## relaciones de aspecto

The herramienta uses simplified aspect ratio names that map to FLUX 2 Pro image sizes:

| Aspect Ratio | Maps To | Best For |
|-------------|---------|----------|
| `landscape` | `landscape_16_9` | Wallpapers, banners, scenes |
| `square` | `square_hd` | Profile pictures, social media posts |
| `portrait` | `portrait_16_9` | Character art, phone wallpapers |

:::Consejo
You can also Usar the raw FLUX 2 Pro size presets directly: `square_hd`, `square`, `portrait_4_3`, `portrait_16_9`, `landscape_4_3`, `landscape_16_9`. Custom sizes up to 2048x2048 are also supported.
:::

## Automatic Aumento de escala

Every generated image is automatically upscaled 2x using FAL.ai's Clarity Upscaler with these settings:

| Setting | Value |
|---------|-------|
| Upscale Factor | 2x |
| Creativity | 0.35 |
| Resemblance | 0.6 |
| Guidance Scale | 4 |
| Inference Steps | 18 |
| Positive Prompt | `"masterpiece, best quality, highres"` + your original prompt |
| Negative Prompt | `"(worst quality, low quality, normal quality:2)"` |

The upscaler enhances detail and resolution while preserving the original composition. If the upscaler fails (network issue, rate limit), the original resolution image is returned automatically.

## ejemplos de indicaciones

Aquí hay some effective prompts to try:

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

## Debugging

Habilitar Depurar logging for Generación de Imágenes:

```bash
export IMAGE_TOOLS_DEBUG=true
```

Depurar logs are saved to `./logs/image_tools_debug_<session_id>.json` with details about each generation request, Parámetros, timing, and any errors.

## Safety Settings

The Generación de Imágenes herramienta runs with safety checks disabled by default (`safety_tolerance: 5`, the most permissive setting). This is configured at the code level and is not user-adjustable.

## Limitations

- **Requires API FAL key** — Generación de Imágenes incurs API costs on your FAL.ai account
- **No image editing** — this is text-to-image only, no inpainting or img2img
- **URL-based delivery** — images are returned as temporary FAL.ai URLs, not saved locally
- **Aumento de escala adds latency** — the automatic 2x upscale step adds processing time
- **Max 4 images per request** — `num_images` is capped at 4
