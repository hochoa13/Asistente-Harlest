---
sidebar_position: 3
title: "Ruta de aprendizaje"
description: "Elige tu ruta de aprendizaje a través de la documentación de Hermes Agent según tu nivel de experiencia y objetivos"
---

# Ruta de aprendizaje

Hermes Agent puede hacer mucho — asistente CLI, bot de Telegram/Discord, automatización de tareas, entrenamiento RL, y más. Esta página te ayuda a determinar por dónde empezar y qué leer según tu nivel de experiencia y lo que estés intentando lograr.

:::tip Comienza aquí
Si aún no has instalado Hermes Agent, comienza con la guía de [Instalación](/docs/getting-started/installation) y después ejecuta el [Inicio rápido](/docs/getting-started/quickstart). Todo lo siguiente asume que tienes una instalación funcional.
:::

## Cómo usar esta página

- **¿Sabes tu nivel?** Ve a la [tabla de nivel de experiencia](#por-nivel-de-experiencia) y sigue el orden de lectura para tu nivel.
- **¿Tienes un objetivo específico?** Ve a [Por caso de uso](#por-caso-de-uso) y encuentra el escenario que coincida.
- **¿Solo navegando?** Consulta la tabla de [Características clave](#características-clave-de-un-vistazo) para una descripción general rápida de todo lo que Hermes Agent puede hacer.

## Por nivel de experiencia

| Nivel | Objetivo | Lectura recomendada | Estimación de tiempo |
|---|---|---|---|
| **Principiante** | Levántate y anda, ten conversaciones básicas, usa herramientas integradas | [Instalación](/docs/getting-started/installation) → [Inicio rápido](/docs/getting-started/quickstart) → [Uso de CLI](/docs/user-guide/cli) → [Configuración](/docs/user-guide/configuration) | ~1 hora |
| **Intermedio** | Configura bots de mensajería, usa características avanzadas como memoria, trabajos cron, y habilidades | [Sesiones](/docs/user-guide/sessions) → [Mensajería](/docs/user-guide/messaging) → [Herramientas](/docs/user-guide/features/tools) → [Habilidades](/docs/user-guide/features/skills) → [Memoria](/docs/user-guide/features/memory) → [Cron](/docs/user-guide/features/cron) | ~2–3 horas |
| **Avanzado** | Construye herramientas personalizadas, crea habilidades, entrena modelos con RL, contribuye al proyecto | [Arquitectura](/docs/developer-guide/architecture) → [Agregando herramientas](/docs/developer-guide/adding-tools) → [Creando habilidades](/docs/developer-guide/creating-skills) → [Entrenamiento RL](/docs/user-guide/features/rl-training) → [Contribuyendo](/docs/developer-guide/contributing) | ~4–6 horas |

## Por caso de uso

Elige el escenario que coincida con lo que quieres hacer. Cada uno te vincula a la documentación relevante en el orden que deberías leerla.

### "Quiero un asistente de codificación de CLI"

Usa Hermes Agent como asistente interactivo de terminal para escribir, revisar y ejecutar código.

1. [Instalación](/docs/getting-started/installation)
2. [Inicio rápido](/docs/getting-started/quickstart)
3. [Uso de CLI](/docs/user-guide/cli)
4. [Ejecución de código](/docs/user-guide/features/code-execution)
5. [Archivos de contexto](/docs/user-guide/features/context-files)
6. [Tips y mejores prácticas](/docs/guides/tips)

:::tip
Pasa archivos directamente a tu conversación con archivos de contexto. Hermes Agent puede leer, editar y ejecutar código en tus proyectos.
:::

### "Quiero un bot de Telegram/Discord"

Implementa Hermes Agent como bot en tu plataforma de mensajería favorita.

1. [Instalación](/docs/getting-started/installation)
2. [Configuración](/docs/user-guide/configuration)
3. [Descripción general de mensajería](/docs/user-guide/messaging)
4. [Configuración de Telegram](/docs/user-guide/messaging/telegram)
5. [Configuración de Discord](/docs/user-guide/messaging/discord)
6. [Seguridad](/docs/user-guide/security)

Para ejemplos de proyectos completos, consulta:
- [Bot de resumen diario](/docs/guides/daily-briefing-bot)
- [Asistente de equipo de Telegram](/docs/guides/team-telegram-assistant)

### "Quiero automatizar tareas"

Programa tareas recurrentes, ejecuta trabajos por lotes, o encadena acciones de agente juntas.

1. [Inicio rápido](/docs/getting-started/quickstart)
2. [Programación de cron](/docs/user-guide/features/cron)
3. [Procesamiento por lotes](/docs/user-guide/features/batch-processing)
4. [Delegación](/docs/user-guide/features/delegation)
5. [Hooks](/docs/user-guide/features/hooks)

:::tip
Los trabajos cron permiten que Hermes Agent ejecute tareas en un horario — resúmenes diarios, comprobaciones periódicas, informes automatizados — sin que estés presente.
:::

### "Quiero construir herramientas/habilidades personalizadas"

Extiende Hermes Agent con tus propias herramientas y paquetes de habilidades reutilizables.

1. [Descripción general de herramientas](/docs/user-guide/features/tools)
2. [Descripción general de habilidades](/docs/user-guide/features/skills)
3. [MCP (Protocolo de contexto de modelo)](/docs/user-guide/features/mcp)
4. [Arquitectura](/docs/developer-guide/architecture)
5. [Agregando herramientas](/docs/developer-guide/adding-tools)
6. [Creando habilidades](/docs/developer-guide/creating-skills)

:::tip
Las herramientas son funciones individuales que el agente puede llamar. Las habilidades son paquetes de herramientas, prompts y configuración empaquetadas juntas. Comienza con herramientas, progresa a habilidades.
:::

### "Quiero entrenar modelos"

Usa aprendizaje por refuerzo para ajustar el comportamiento del modelo con el pipeline de entrenamiento RL integrado de Hermes Agent.

1. [Inicio rápido](/docs/getting-started/quickstart)
2. [Configuración](/docs/user-guide/configuration)
3. [Entrenamiento RL](/docs/user-guide/features/rl-training)
4. [Enrutamiento de proveedores](/docs/user-guide/features/provider-routing)
5. [Arquitectura](/docs/developer-guide/architecture)

:::tip
El entrenamiento RL funciona mejor cuando ya entiendes los conceptos básicos de cómo Hermes Agent maneja conversaciones y llamadas de herramientas. Si eres nuevo, primero ejecuta la ruta para principiantes.
:::

### "Quiero usarlo como librería de Python"

Integra Hermes Agent en tus propias aplicaciones de Python programáticamente.

1. [Instalación](/docs/getting-started/installation)
2. [Inicio rápido](/docs/getting-started/quickstart)
3. [Guía de librería Python](/docs/guides/python-library)
4. [Arquitectura](/docs/developer-guide/architecture)
5. [Herramientas](/docs/user-guide/features/tools)
6. [Sesiones](/docs/user-guide/sessions)

## Características clave de un vistazo

¿No estás seguro de qué está disponible? Aquí hay un directorio rápido de características principales:

| Característica | Qué hace | Enlace |
|---|---|---|
| **Herramientas** | Herramientas integradas que el agente puede llamar (E/S de archivo, búsqueda, shell, etc.) | [Herramientas](/docs/user-guide/features/tools) |
| **Habilidades** | Paquetes de extensiones instalables que añaden nuevas capacidades | [Habilidades](/docs/user-guide/features/skills) |
| **Memoria** | Memoria persistente entre sesiones | [Memoria](/docs/user-guide/features/memory) |
| **Archivos de contexto** | Alimenta archivos y directorios a conversaciones | [Archivos de contexto](/docs/user-guide/features/context-files) |
| **MCP** | Conecta a servidores de herramientas externos vía Protocolo de contexto de modelo | [MCP](/docs/user-guide/features/mcp) |
| **Cron** | Programa tareas recurrentes de agente | [Cron](/docs/user-guide/features/cron) |
| **Delegación** | Genera sub-agentes para trabajo paralelo | [Delegación](/docs/user-guide/features/delegation) |
| **Ejecución de código** | Ejecuta código en ambientes aislados | [Ejecución de código](/docs/user-guide/features/code-execution) |
| **Navegador** | Navegación web y scraping | [Navegador](/docs/user-guide/features/browser) |
| **Hooks** | Callbacks y middleware impulsados por eventos | [Hooks](/docs/user-guide/features/hooks) |
| **Procesamiento por lotes** | Procesa múltiples entradas en lote | [Procesamiento por lotes](/docs/user-guide/features/batch-processing) |
| **Entrenamiento RL** | Ajusta modelos con aprendizaje por refuerzo | [Entrenamiento RL](/docs/user-guide/features/rl-training) |
| **Enrutamiento de proveedores** | Enruta solicitudes a través de múltiples proveedores LLM | [Enrutamiento de proveedores](/docs/user-guide/features/provider-routing) |

## Qué leer a continuación

Basándose en dónde estés ahora:

- **¿Acabas de terminar la instalación?** → Ve al [Inicio rápido](/docs/getting-started/quickstart) para ejecutar tu primera conversación.
- **¿Completaste el inicio rápido?** → Lee [Uso de CLI](/docs/user-guide/cli) y [Configuración](/docs/user-guide/configuration) para personalizar tu configuración.
- **¿Cómodo con los conceptos básicos?** → Explora [Herramientas](/docs/user-guide/features/tools), [Habilidades](/docs/user-guide/features/skills), y [Memoria](/docs/user-guide/features/memory) para desbloquear el poder completo del agente.
- **¿Configurando para un equipo?** → Lee [Seguridad](/docs/user-guide/security) y [Sesiones](/docs/user-guide/sessions) para entender el control de acceso y la gestión de conversaciones.
- **¿Listo para construir?** → Salta a la [Guía de desarrollador](/docs/developer-guide/architecture) para entender lo interno y comenzar a contribuir.
- **¿Quieres ejemplos prácticos?** → Consulta la sección [Guías](/docs/guides/tips) para proyectos de mundo real y consejos.

:::tip
No necesitas leerlo todo. Elige la ruta que coincida con tu objetivo, sigue los enlaces en orden, y serás productivo rápidamente. Siempre puedes volver a esta página para encontrar tu próximo paso.
:::
