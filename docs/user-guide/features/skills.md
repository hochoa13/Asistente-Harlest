---
sidebar_position: 2
title: "Sistema de Habilidades"
description: "Documentos de conocimiento bajo demanda — divulgación progresiva, habilidades gestionadas por agente y el Centro de Habilidades"
---

# Sistema de Habilidades

Las Habilidades son documentos de conocimiento bajo demanda que el agente puede cargar cuando lo necesita. Siguen un patrón de **divulgación progresiva** para minimizar el uso de tokens y son compatibles con el estándar abierto [agentskills.io](https://agentskills.io/specification).

Todas las Habilidades viven en **`~/.hermes/Habilidades/`** — un directorio único que sirve como fuente de verdad. En una instalación nueva, las Habilidades incluidas se copian del repositorio. Las Habilidades instaladas desde el Centro y las creadas por el agente también van aquí. El agente puede modificar o eliminar cualquier habilidad.

## Usar Habilidades

Cada habilidad instalada está automáticamente disponible como un comando slash:

```bash
# En la CLI o cualquier plataforma de mensajería:
/gif-search funny cats
/axolotl help me fine-tune Llama 3 on my dataset
/github-pr-workflow create a PR for the auth refactor

# Solo el nombre de la habilidad la carga y permite que el agente pregunte qué necesitas:
/excalidraw
```

También puedes interactuar con las Habilidades a través de conversación natural:

```bash
hermes chat --toolsets skills -q "What skills do you have?"
hermes chat --toolsets skills -q "Show me the axolotl skill"
```

## Divulgación Progresiva

Las Habilidades utilizan un patrón de carga eficiente en tokens:

```
Nivel 0: skills_list()           → [{name, description, category}, ...]   (~3k tokens)
Nivel 1: skill_view(name)        → Contenido completo + metadatos       (varía)
Nivel 2: skill_view(name, path)  → Archivo de referencia específico       (varía)
```

El agente solo carga el contenido completo de la habilidad cuando realmente lo necesita.

## Formato Habilidad.md

```markdown
---
name: my-skill
description: Breve descripción de lo que hace esta habilidad
version: 1.0.0
platforms: [macos, linux]     # Opcional — restringir a plataformas OS específicas
metadata:
  hermes:
    tags: [python, automation]
    category: devops
    fallback_for_toolsets: [web]    # Opcional — activación condicional (ver abajo)
    requires_toolsets: [terminal]   # Opcional — activación condicional (ver abajo)
---

# Título de Habilidad

## Cuándo Usar
Condiciones de activación para esta habilidad.

## Procedimiento
1. Paso uno
2. Paso dos

## Trampas
- Modos de fallo conocidos y soluciones

## Verificación
Cómo confirmar que funcionaba.
```

### Habilidades Específicas de Plataforma

Las Habilidades pueden limitarse a sistemas operativos específicos utilizando el campo `platforms`:

| Valor | Coincide |
|-------|---------|
| `macos` | macOS (Darwin) |
| `linux` | Linux |
| `windows` | Windows |

```yaml
platforms: [macos]            # Solo macOS (ej., iMessage, Apple Reminders, FindMy)
platforms: [macos, linux]     # macOS y Linux
```

Cuando se establece, la habilidad se oculta automáticamente del indicador del sistema, `skills_list()` y comandos slash en plataformas incompatibles. Si se omite, la habilidad se carga en todas las plataformas.

### Activación Condicional (Habilidades Alternativas)

Las Habilidades pueden mostrarse u ocultarse automáticamente según qué Herramientas estén disponibles en la sesión actual. Esto es más útil para **Habilidades alternativas** — alternativas gratuitas o locales que solo deben aparecer cuando una herramienta premium no está disponible.

```yaml
metadata:
  hermes:
    fallback_for_toolsets: [web]      # Mostrar SOLO cuando estos conjuntos de herramientas no estén disponibles
    requires_toolsets: [terminal]     # Mostrar SOLO cuando estos conjuntos de herramientas estén disponibles
    fallback_for_tools: [web_search]  # Mostrar SOLO cuando estas herramientas específicas no estén disponibles
    requires_tools: [terminal]        # Mostrar SOLO cuando estas herramientas específicas estén disponibles
```

| Campo | Comportamiento |
|-------|----------|
| `fallback_for_toolsets` | La habilidad está **oculta** cuando los Conjuntos de herramientas enumerados están disponibles. Se muestra cuando faltan. |
| `fallback_for_tools` | Lo mismo, pero verifica herramientas individuales en lugar de Conjuntos de herramientas. |
| `requires_toolsets` | La habilidad está **oculta** cuando los Conjuntos de herramientas enumerados no están disponibles. Se muestra cuando están presentes. |
| `requires_tools` | Lo mismo, pero verifica herramientas individuales. |

**Ejemplo:** La habilidad de `duckduckgo-search` incorporada utiliza `fallback_for_toolsets: [web]`. Cuando tienes `FIRECRAWL_API_KEY` establecido, el conjunto de herramientas web está disponible y el agente usa `web_search` — la habilidad DuckDuckGo permanece oculta. Si la clave API no está disponible, el conjunto de herramientas web no está disponible y la habilidad DuckDuckGo aparece automáticamente como alternativa.

Las Habilidades sin campos condicionales se comportan exactamente como antes — siempre se muestran.

## Estructura de Directorio de Habilidad

```
~/.hermes/skills/                  # Fuente única de verdad
├── mlops/                         # Directorio de categoría
│   ├── axolotl/
│   │   ├── SKILL.md               # Instrucciones principales (requerido)
│   │   ├── references/            # Documentación adicional
│   │   ├── templates/             # Formatos de salida
│   │   └── assets/                # Archivos complementarios
│   └── vllm/
│       └── SKILL.md
├── devops/
│   └── deploy-k8s/                # Habilidad creada por agente
│       ├── SKILL.md
│       └── references/
├── .hub/                          # Estado del Centro de Habilidades
│   ├── lock.json
│   ├── quarantine/
│   └── audit.log
└── .bundled_manifest              # Rastrea habilidades incluidas sembradas
```

## Habilidades Gestionadas por Agente (herramienta skill_manage)

El agente puede crear, actualizar y eliminar sus propias Habilidades a través de la herramienta `skill_manage`. Esta es la **Memoria procesal** del agente — cuando descubre un flujo de trabajo no trivial, guarda el enfoque como una habilidad para reutilización futura.

### Cuándo el Agente Crea Habilidades

- Después de completar una tarea compleja (5+ Llamadas de Herramientas) exitosamente
- Cuando golpeó errores o callejones sin salida y encontró la ruta que funciona
- Cuando el usuario corrigió su enfoque
- Cuando descubrió un flujo de trabajo no trivial

### Acciones

| Acción | Usar para | Parámetros clave |
|--------|----------|----------|
| `Create` | Nueva habilidad desde cero | `name`, `content` (habilidad.md completo), `category` opcional |
| `patch` | Correcciones dirigidas (preferido) | `name`, `old_string`, `new_string` |
| `edit` | Reescritos estructurales mayores | `name`, `content` (reemplazo completo de habilidad.md) |
| `delete` | Eliminar una habilidad por completo | `name` |
| `write_file` | Añadir/actualizar archivos de soporte | `name`, `file_path`, `file_content` |
| `remove_file` | Eliminar un archivo de soporte | `name`, `file_path` |

:::tip
La acción `patch` es preferida para actualizaciones — es más eficiente en tokens que `edit` porque solo el texto cambiado aparece en la llamada de herramienta.
:::

## Centro de Habilidades

Examina, busca, instala y gestiona Habilidades desde registros en línea y Habilidades opcionales oficiales:

```bash
hermes skills browse                     # Examina todas las habilidades del hub (oficiales primero)
hermes skills browse --source official   # Examina solo habilidades opcionales oficiales
hermes skills search kubernetes          # Busca en todas las fuentes
hermes skills install openai/skills/k8s  # Instalar con escaneo de seguridad
hermes skills inspect openai/skills/k8s  # Obtener vista previa antes de instalar
hermes skills list --source hub          # Listar habilidades instaladas del hub
hermes skills audit                      # Re-escanear todas las habilidades del hub
hermes skills uninstall k8s              # Eliminar una habilidad del hub
hermes skills publish skills/my-skill --to github --repo owner/repo
hermes skills snapshot export setup.json # Exportar configuración de habilidad
hermes skills tap add myorg/skills-repo  # Añadir una fuente personalizada
```

Todas las Habilidades instaladas del Centro pasan por un **escáner de seguridad** que verifica exfiltración de datos, inyección de indicador, comandos destructivos y otras amenazas.

### Niveles de Confianza

| Nivel | Fuente | Política |
|-------|--------|---------||
| `builtin` | Incluido con Hermes | Siempre confiable |
| `official` | `optional-Habilidades/` en el repositorio | Confianza incorporada, sin advertencia de terceros |
| `trusted` | openai/Habilidades, anthropics/Habilidades | Fuentes confiables |
| `community` | Todo lo demás | Cualquier hallazgo = bloqueado a menos que `--force` |

### Comandos Slash (Dentro del Chat)

Todos los mismos comandos funcionan con el prefijo `/skills`:

```
/skills browse
/skills search kubernetes
/skills install openai/skills/skill-creator
/skills list
```
