---
slug: /
sidebar_position: 0
title: "Documentación Hermes Agent"
description: "El agente de IA auto-mejorable creado por Harlest. Un ciclo de aprendizaje integrado que crea habilidades a partir de la experiencia, las mejora durante el uso, y recuerda entre sesiones."
hide_table_of_contents: true
---

# Hermes Agent

El agente de IA auto-mejorable creado por [Harlest](https://www.facebook.com/haroldandres.hernandezochoa/). El único agente con un ciclo de aprendizaje integrado — crea habilidades a partir de la experiencia, las mejora durante el uso, se impulsa a sí mismo a persistir conocimiento, y construye un modelo cada vez más profundo de quién eres entre sesiones.

<div style={{display: 'flex', gap: '1rem', marginBottom: '2rem', flexWrap: 'wrap'}}>
  <a href="/docs/getting-started/installation" style={{display: 'inline-block', padding: '0.6rem 1.2rem', backgroundColor: '#FFD700', color: '#07070d', borderRadius: '8px', fontWeight: 600, textDecoration: 'none'}}>Comenzar →</a>
  <a href="https://github.com/hochoa13/Asistente-Harlest" style={{display: 'inline-block', padding: '0.6rem 1.2rem', border: '1px solid rgba(255,215,0,0.2)', borderRadius: '8px', textDecoration: 'none'}}>Ver en GitHub</a>
</div>

## ¿Qué es Hermes Agent?

No es un copiloto de codificación atado a un IDE ni un envoltorio de chatbot alrededor de una sola API. Es un **agente autónomo** que se vuelve más capaz cuanto más tiempo se ejecuta. Vive donde lo coloques — una VPS de $5, un clúster de GPU, o infraestructura sin servidor (Daytona, Modal) que cuesta casi nada cuando está inactiva. Hablo con él desde Telegram mientras funciona en una VM en la nube que nunca necesitas acceder por SSH. No está atado a tu laptop.

## Enlaces Rápidos

| | |
|---|---|
| 🚀 **[Instalación](/docs/getting-started/installation)** | Instala en 60 segundos en Linux, macOS, o WSL2 |
| 📖 **[Tutorial Rápido](/docs/getting-started/quickstart)** | Tu primera conversación y características clave a probar |
| 🗺️ **[Ruta de Aprendizaje](/docs/getting-started/learning-path)** | Encuentra los docs correctos para tu nivel de experiencia |
| ⚙️ **[Configuración](/docs/user-guide/configuration)** | Archivo de configuración, proveedores, modelos y opciones |
| 💬 **[Puerta de Enlace de Mensajería](/docs/user-guide/messaging)** | Configura Telegram, Discord, Slack o WhatsApp |
| 🔧 **[Herramientas y Conjuntos](/docs/user-guide/features/tools)** | 40+ herramientas integradas y cómo configurarlas |
| 🧠 **[Sistema de Memoria](/docs/user-guide/features/memory)** | Memoria persistente que crece entre sesiones |
| 📚 **[Sistema de Habilidades](/docs/user-guide/features/skills)** | Memoria procedimental que el agente crea y reutiliza |
| 🔌 **[Integración MCP](/docs/user-guide/features/mcp)** | Conecta a cualquier servidor MCP para capacidades extendidas |
| 📄 **[Archivos de Contexto](/docs/user-guide/features/context-files)** | Archivos de contexto que moldean cada conversación |
| 🔒 **[Seguridad](/docs/user-guide/security)** | Aprobación de comandos, autorización, aislamiento de contenedor |
| 💡 **[Tips y Mejores Prácticas](/docs/guides/tips)** | Ganancias rápidas para sacar el máximo de Hermes |
| 🏗️ **[Arquitectura](/docs/developer-guide/architecture)** | Cómo funciona bajo el capó |
| ❓ **[Preguntas Frecuentes](/docs/reference/faq)** | Preguntas comunes y soluciones |

## Características Clave

- **Un ciclo de aprendizaje cerrado** — Memoria curada por agente con nudges periódicos, creación autónoma de habilidades, auto-mejora de habilidades durante el uso, recuperación entre sesiones FTS5 con resumen por LLM, y modelado de usuario dialéctico de [Honcho](https://github.com/plastic-labs/honcho)
- **Funciona en cualquier lugar, no solo tu laptop** — 6 backends de terminal: local, Docker, SSH, Daytona, Singularity, Modal. Daytona y Modal ofrecen persistencia sin servidor — tu entorno hiberna cuando está inactivo, costando casi nada
- **Vive donde vives tú** — CLI, Telegram, Discord, Slack, WhatsApp, todo desde una puerta de enlace
- **Creado por expertos en IA** — Creado por [Harlest](https://www.facebook.com/haroldandres.hernandezochoa/). Funciona con [Nous Portal](https://portal.nousresearch.com), [OpenRouter](https://openrouter.ai), OpenAI, o cualquier endpoint
- **Automatizaciones programadas** — Cron integrado con entrega a cualquier plataforma
- **Delega y paraleliza** — Genera suagentes aislados para flujos de trabajo paralelos. Llamada programática de herramientas via `execute_code` colapsa pipelines de múltiples pasos en llamadas de inferencia única
- **Habilidades de estándar abierto** — Compatible con [agentskills.io](https://agentskills.io). Las habilidades son portátiles, compartibles, y contribuidas por la comunidad via el Skills Hub
- **Control web completo** — Búsqueda, extracción, navegación, visión, generación de imágenes, TTS
- **MCP support** — Connect to any MCP server for extended tool capabilities
- **Research-ready** — Batch processing, trajectory export, RL training with Atropos. Built by [Harlest](https://www.facebook.com/haroldandres.hernandezochoa/) — the lab behind Hermes, Nomos, and Psyche models
