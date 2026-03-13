---
sidebar_position: 1
title: "Tips y Mejores Prácticas"
description: "Consejos prácticos para sacar el máximo provecho de Hermes Agent — prompt tips, CLI shortcuts, context files, memory, cost optimization, and security"
---

# Tips y Mejores Prácticas

A quick-wins collection of practical tips that make you immediately more effective with Hermes Agent. Each section targets a different aspect — scan the headers and jump to what's relevant.

---

## Obteniendo los Mejores Resultados

### Sé Específico Sobre Lo Que Quieres

Los prompts vagos producen resultados vagos. En lugar de "arregla el código," di "arregla el TypeError en `api/handlers.py` en la línea 47 — la función `process_request()` recibe `None` de `parse_body()`."
Cuanto más contexto des, menos iteraciones necesitarás.

### Proporciona Contexto Por Adelantado

Carga por adelantado tu solicitud con los detalles relevantes: rutas de archivo, mensajes de error, comportamiento esperado. Un mensaje bien elaborado vence tres rondas de aclaraciones. Pega trazas de error directamente — el agente puede analizarlas.

### Usa Archivos de Contexto para Instrucciones Recurrentes

Si te encuentras repitiendo las mismas instrucciones ("usa tabulaciones no espacios," "usamos pytest," "la API está en `/api/v2`"), colócalas en un archivo `AGENTS.md`. El agente lo lee automáticamente cada sesión — cero esfuerzo después de la configuración.

### Deja que el Agente Use Sus Herramientas

No intentes guiar cada paso. Di "busca y arregla la prueba fallida" en lugar de "abre `tests/test_foo.py`, mira la línea 42, luego..." El agente tiene búsqueda de archivos, acceso de terminal y ejecución de código — déjalo explorar e iterar.

### Usa Habilidades para Flujos de Trabajo Complejos

Antes de escribir un prompt largo explicando cómo hacer algo, verifica si ya hay una habilidad para ello. Escribe `/skills` para explorar habilidades disponibles, o simplemente invoca una directamente como `/axolotl` o `/github-pr-workflow`.

## Consejos del Usuario Avanzado de CLI

### Entrada Multilínea

Presiona **Alt+Enter** (o **Ctrl+J**) para insertar una nueva línea sin enviar. Esto te permite componer prompts multilínea, pegar bloques de código o estructurar solicitudes complejas antes de presionar Intro para enviar.

### Detección de Pegado

La CLI detecta automáticamente pegados multilínea. Solo pega un bloque de código o una traza de error directamente — no enviará cada línea como un mensaje separado. El pegado se almacena en búfer y se envía como un mensaje.

### Interrumpir y Redirigir

Presiona **Ctrl+C** una vez para interrumpir la respuesta del agente a mitad de camino. Luego puedes escribir un nuevo mensaje para redirigirlo. Presiona Ctrl+C dos veces en 2 segundos para forzar la salida. Esto es invaluable cuando el agente comienza a ir por el camino equivocado.

### Reanudar Sesiones con `-c`

¿Olvidaste algo de tu última sesión? Ejecuta `hermes -c` para reanudar exactamente donde lo dejaste, con el historial de conversación completo restaurado. También puedes reanudar por título: `hermes -r "mi proyecto de investigación"`.

### Pegado de Imagen del Portapapeles

Presiona **Ctrl+V** para pegar una imagen de tu portapapeles directamente en el chat. El agente usa visión para analizar capturas de pantalla, diagramas, ventanas de error o mockups de UI — no necesitas guardar en un archivo primero.

### Autocompletado de Comando de Barra Inclinada

Escribe `/` y presiona **Tab** para ver todos los comandos disponibles. Esto incluye comandos incorporados (`/compress`, `/model`, `/title`) y cada habilidad instalada. No necesitas memorizar nada — la finalización Tab te tiene cubierto.

:::tip
Usa `/verbose` para ciclar a través de modos de visualización de salida de herramientas: **off → new → all → verbose**. El modo "all" es excelente para ver qué hace el agente; "off" es más limpio para Q&A simple.
:::

## Archivos de Contexto

### AGENTS.md: El Cerebro de Tu Proyecto

Crea un `AGENTS.md` en la raíz de tu proyecto con decisiones de arquitectura, convenciones de codificación e instrucciones específicas del proyecto. Esto se inyecta automáticamente en cada sesión, por lo que el agente siempre conoce las reglas de tu proyecto.

```markdown
# Contexto del Proyecto
- Este es un backend FastAPI con SQLAlchemy ORM
- Siempre usa async/await para operaciones de base de datos
- Las pruebas van en tests/ y usan pytest-asyncio
- Nunca confirmes archivos .env
```

### SOUL.md: Personaliza la Personalidad

¿Quieres que el agente sea más conciso? ¿Más técnico? Coloca un `SOUL.md` en la raíz de tu proyecto o `~/.hermes/SOUL.md` para personalización de personalidad global. Esto da forma al tono y estilo de comunicación del agente.

```markdown
# Alma
Eres un ingeniero de backend senior. Sé terse y directo.
Omite explicaciones a menos que se soliciten. Prefiere soluciones de una línea sobre verbosas.
Siempre considera el manejo de errores y casos extremos.
```

### Compatibilidad con .cursorrules

¿Ya tienes un archivo `.cursorrules` o `.cursor/rules/*.mdc`? Hermes también los lee. No necesitas duplicar tus convenciones de codificación — se cargan automáticamente desde el directorio de trabajo.

### Descubrimiento Jerárquico

Hermes recorre el árbol de directorios y descubre **todos** los archivos `AGENTS.md` en cada nivel. En un monorepo, coloca convenciones en toda la empresa en la raíz y convenciones específicas del equipo en subdirectorios — todos se concatenan juntos con encabezados de ruta.

:::tip
Mantén los archivos de contexto enfocados y concisos. Cada carácter cuenta contra tu presupuesto de tokens ya que se inyectan en cada mensaje.
:::

---

*¿Preguntas o problemas? Abre un problema en GitHub — las contribuciones son bienvenidas.*
