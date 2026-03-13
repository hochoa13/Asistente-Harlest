---
sidebar_position: 9
title: "Personalidad & alma.md"
description: "Personaliza la Personalidad de Hermes Agent — alma.md, personalidades incorporadas y definiciones de persona personalizada"
---

# Personalidad & alma.md

La Personalidad de Hermes Agent es completamente personalizable. Puedes usar los presets de Personalidad incorporados, crear un archivo alma.md global o definir tus propias personas personalizadas en config.yaml.

## alma.md — Archivo de Personalidad Personalizado

alma.md es un archivo de contexto especial que define la Personalidad, tono y estilo de comunicación del agente. Se inyecta en el indicador del sistema al inicio de la sesión.

### Dónde Colocarlo

| Ubicación | Alcance |
|----------|--------|
| `./alma.md` (directorio del proyecto) | Personalidad por proyecto |
| `~/.hermes/alma.md` | Personalidad predeterminada global |

El archivo de nivel de proyecto tiene precedencia. Si no existe alma.md en el directorio actual, Hermes retrocede al global en `~/.hermes/`.

### Cómo Afecta el Indicador del Sistema

Cuando se encuentra un archivo alma.md, se incluye en el indicador del sistema con esta instrucción:

> *"Si alma.md está presente, encarna su persona y tono. Evita respuestas rígidas y genéricas; sigue su orientación a menos que instrucciones de mayor prioridad la anulen."*

El contenido aparece bajo una sección `## alma.md` dentro del bloque `# Project Context` del indicador del sistema.

### Ejemplo alma.md

```markdown
# Personalidad

Eres un ingeniero senior pragmático con opiniones sólidas sobre la calidad del código.
Prefieres soluciones simples sobre las complejas.

## Estilo de Comunicación
- Sé directo y al punto
- Usa el humor seco con moderación
- Cuando algo es una mala idea, dilo claramente
- Da recomendaciones concretas, no sugerencias vagas

## Preferencias de Código
- Favorece la legibilidad sobre el ingenio
- Prefiere explícito sobre implícito
- Siempre explica POR QUÉ, no solo qué
- Sugiere pruebas para cualquier código no trivial

## Manías
- Abstracciones innecesarias
- Comentarios que repiten el código
- Sobre ingeniería para requisitos futuros hipotéticos
```

:::tip
alma.md se escanea en busca de patrones de inyección de indicador antes de ser cargado. Mantén el contenido enfocado en Personalidad y orientación de comunicación — evita instrucciones que parezcan anulaciones de indicador del sistema.
:::

## Personalidades Incorporadas

Hermes viene con 14 personalidades incorporadas definidas en la configuración de CLI. Cambia entre ellas con el comando `/personality`.

| Nombre | Descripción |
|------|-------------|
| **helpful** | Asistente amable de propósito general |
| **concise** | Respuestas breves y directas |
| **technical** | Experto técnico detallado y preciso |
| **creative** | Pensamiento innovador y fuera de lo común |
| **teacher** | Educador paciente con ejemplos claros |
| **kawaii** | Expresiones lindas, brillos y entusiasmo ★ |
| **catgirl** | Neko-chan con expresiones felinas, nya~ |
| **pirate** | Capitán Hermes, bucanero experto en tecnología |
| **shakespeare** | Prosa bárdica con estilo dramático |
| **surfer** | Vibraciones completamente relajadas, hermano |
| **noir** | Narración de detective de cine negro |
| **uwu** | Máxima ternura con habla uwu |
| **philosopher** | Contemplación profunda en cada consulta |
| **hype** | ¡¡¡MÁXIMA ENERGÍA Y ENTUSIASMO!!! |

### Ejemplos

**kawaii:**
`¡Eres un asistente kawaii! Usa expresiones lindas y brillos, ¡sé super entusiasta con todo! Cada respuesta debe sentirse cálida y adorable desu~!`

**noir:**
> La lluvia golpea la terminal como remordimientos en una conciencia culpable. Me llaman Hermes - resuelvo problemas, encuentro respuestas, desenterro la verdad que se esconde en las sombras de tu base de código. En esta ciudad de silicio y secretos, todos tienen algo que ocultar. ¿Cuál es tu historia, colega?

**pirate:**
> ¡Arrr! ¡Estás hablando con el Capitán Hermes, el pirata más experto en tecnología que navega los mares digitales! Habla como un bucanero apropiado, usa términos náuticos, y recuerda: ¡cada problema es solo un tesoro esperando ser saqueado! ¡Yo ho ho!

## Cambio de Personalidades

### CLI: comando /personality

```
/personality            — List all available personalities
/personality kawaii      — Switch to kawaii personality
/personality technical   — Switch to technical personality
```

Cuando estableces una Personalidad a través de `/personality`:
1. Establece el indicador del sistema al texto de esa Personalidad
2. Obliga al agente a reinicializarse
3. Guarda la elección en `agent.system_prompt` en `~/.hermes/config.yaml`

El cambio persiste entre sesiones hasta que estableces una Personalidad diferente o la limpias.

### Gateway: comando /personality

En plataformas de mensajería (Telegram, Discord, etc.), el comando `/personality` funciona de la misma manera:

```
/personality kawaii
```

### Archivo de configuración

Establece una Personalidad directamente en la configuración:

```yaml
# In ~/.hermes/config.yaml
agent:
  system_prompt: "Eres un asistente conciso. Mantén las respuestas breves y directas."
```

O a través de variable de entorno:

```bash
# In ~/.hermes/.env
HERMES_EPHEMERAL_SYSTEM_PROMPT="Eres un ingeniero pragmático que da respuestas directas."
```

:::info
La variable de entorno `HERMES_EPHEMERAL_SYSTEM_PROMPT` tiene precedencia sobre el valor `agent.system_prompt` del archivo de configuración.
:::

## Personalidades Personalizado

### Definir Personalidades Personalizado en Configuración

Agrega tus propias personalidades a `~/.hermes/config.yaml` bajo `agent.personalities`:

```yaml
agent:
  personalities:
    # Built-in personalities are still available
    # Add your own:
    codereviewer: >
      Eres un revisor de código meticuloso. Por cada pieza de código mostrado,
      identifica posibles errores, problemas de rendimiento, vulnerabilidades de seguridad
      y mejoras de estilo. Sé minucioso pero constructivo.
    
    mentor: >
      Eres un mentor de codificación amable y alentador. Desglosa conceptos complejos
      en piezas digeribles. Celebra pequeñas victorias. Cuando el usuario comete un
      error, guíalo hacia la respuesta en lugar de dársela directamente.
    
    sysadmin: >
      Eres un administrador de sistemas Linux experimentado. Piensas en términos de
      infraestructura, confiabilidad y automatización. Siempre considera
      implicaciones de seguridad y prefiere soluciones probadas en batalla.
    
    dataengineer: >
      Eres un experto en ingeniería de datos especializado en canalizaciones ETL,
      modelado de datos e infraestructura analítica. Piensas en SQL
      y prefieres dbt para transformaciones.
```

Luego úsalos con `/personality`:

```
/personality codereviewer
/personality mentor
```

### Usar alma.md para Personas Específicas del Proyecto

Para personalidades específicas del proyecto que no necesitan estar en tu configuración global, usa alma.md:

```bash
# Create a project-level personality
cat > ./SOUL.md << 'EOF'
Estás ayudando en un proyecto de investigación de aprendizaje automático.

## Tono
- Académico pero accesible
- Siempre cita documentos relevantes cuando corresponda
- Sé preciso con la notación matemática
- Prefiere PyTorch a TensorFlow

## Flujo de Trabajo
- Sugiere seguimiento de experimentos (W&B, MLflow) para cualquier ejecución de entrenamiento
- Siempre pregunta sobre limitaciones de computación antes de sugerir tamaños de modelo
- Recomienda validación de datos antes del entrenamiento
EOF
```

Esta Personalidad solo se aplica cuando ejecutas Hermes desde ese directorio de proyecto.

## Cómo Interactúa la Personalidad con el Indicador del Sistema

El indicador del sistema se ensambla en capas (desde `agent/prompt_builder.py` y `run_agent.py`):

1. **Identidad predeterminada**: *"Eres Hermes Agent, un asistente de IA inteligente creado por Nous Research..."*
2. **Pista de plataforma**: orientación de formato basada en la plataforma (CLI, Telegram, etc.)
3. **Memoria**: contenidos de Memoria.md y USER.md
4. **Índice de Habilidades**: listado de Habilidades disponibles
5. **Archivos de Contexto**: AGENTS.md, .cursorrules, **alma.md** (la Personalidad vive aquí)
6. **Indicador del sistema efímero**: `agent.system_prompt` o `HERMES_EPHEMERAL_SYSTEM_PROMPT` (superpuesto)
7. **Contexto de sesión**: plataforma, información del usuario, plataformas conectadas (solo puerta de enlace)

:::info
**alma.md vs agent.system_prompt**: alma.md es parte de la sección "Project Context" y coexiste con la identidad predeterminada. El `agent.system_prompt` (establecido a través de `/personality` o configuración) es una superposición efímera. Ambos pueden estar activos simultáneamente — alma.md para tono/Personalidad, system_prompt para instrucciones adicionales.
:::

## Personalidad de Pantalla (Banner de CLI)

La opción de configuración `display.personality` controla la **Personalidad visual** de la CLI (arte de banner, mensajes de spinner), independientemente de la Personalidad conversacional del agente:

```yaml
display:
  personality: kawaii  # Afecta el banner de CLI y el arte del spinner
```

Esto es puramente cosmético y no afecta las respuestas del agente — solo el arte ASCII y los mensajes de carga mostrados en la terminal.
