<p align="center">
  <img src="assets/banner.png" alt="Hermes Agent" width="100%">
</p>

# Hermes Agent ⚕

<p align="center">
  <a href="https://hermes-agent.nousres__earch.com/docs/"><img src="https://img.shields.io/badge/Docs-hermes--agent.nousresearch.com-FFD700?style=for-the-badge" alt="Documentación"></a>
  <a href="https://discord.gg/NousResearch"><img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
  <a href="https://github.com/NousResearch/hermes-agent/blob/main/LICENSE"><img src="https://img.shields.io/badge/Licencia-MIT-green?style=for-the-badge" alt="Licencia: MIT"></a>
  <a href="https://nousresearch.com"><img src="https://img.shields.io/badge/Creado%20por-Nous%20Research-blueviolet?style=for-the-badge" alt="Creado por Nous Research"></a>
</p>

**El agente de IA auto-mejorable creado por [Nous Research](https://nousresearch.com).** Es el único agente con un ciclo de aprendizaje integrado — crea habilidades a partir de la experiencia, las mejora durante el uso, se impulsa a sí mismo a persistir conocimiento, busca en sus propias conversaciones anteriores, y construye un modelo cada vez más profundo de quién eres entre sesiones. Ejecútalo en una VPS de $5, un clúster de GPU, o infraestructura sin servidor que cuesta casi nada cuando está inactiva. No está vinculado a tu laptop — habla con él desde Telegram mientras funciona en una máquina virtual en la nube.

Usa cualquier modelo que desees — [Nous Portal](https://portal.nousresearch.com), [OpenRouter](https://openrouter.ai) (200+ modelos), [z.ai/GLM](https://z.ai), [Kimi/Moonshot](https://platform.moonshot.ai), [MiniMax](https://www.minimax.io), OpenAI, o tu propio endpoint. Cambia con `hermes model` — sin cambios de código, sin bloqueo de proveedor.

<table>
<tr><td><b>Una interfaz de terminal real</b></td><td>TUI completa con edición multilínea, autocompletar de comandos slash, historial de conversaciones, interrupción y redirección, y salida de herramientas en streaming.</td></tr>
<tr><td><b>Vive donde vives tú</b></td><td>Telegram, Discord, Slack, WhatsApp, Signal y CLI — todo desde un único proceso de puerta de enlace. Transcripción de memos de voz, continuidad de conversación multiplataforma.</td></tr>
<tr><td><b>Un ciclo de aprendizaje cerrado</b></td><td>Memoria curada por agente con nudges periódicos. Creación autónoma de habilidades después de tareas complejas. Las habilidades se auto-mejoran durante el uso. Búsqueda de sesiones FTS5 con resumida por LLM para recuerdo entre sesiones. Modelado de usuario dialéctico de <a href="https://github.com/plastic-labs/honcho">Honcho</a>. Compatible con el estándar abierto <a href="https://agentskills.io">agentskills.io</a>.</td></tr>
<tr><td><b>Automatizaciones programadas</b></td><td>Programador cron integrado con entrega a cualquier plataforma. Reportes diarios, copias de seguridad nocturnas, auditorías semanales — todo en lenguaje natural, ejecutándose desatendido.</td></tr>
<tr><td><b>Delega y paraleliza</b></td><td>Genera suagentes aislados para flujos de trabajo paralelos. Escribe scripts de Python que llamen herramientas a través de RPC, colapsando pipelines de varios pasos en turnos sin costo de contexto.</td></tr>
<tr><td><b>Funciona en cualquier lugar, no solo en tu laptop</b></td><td>Seis backends de terminal — local, Docker, SSH, Daytona, Singularity y Modal. Daytona y Modal ofrecen persistencia sin servidor — el entorno de tu agente hiberna cuando está inactivo y se activa bajo demanda, costando casi nada entre sesiones. Ejecútalo en una VPS de $5 o un clúster de GPU.</td></tr>
<tr><td><b>Listo para investigación</b></td><td>Generación de trayectorias en lote, entornos RL de Atropos, compresión de trayectorias para entrenar la próxima generación de modelos con capacidad de llamada de herramientas.</td></tr>
</table>

---

## Instalación Rápida

```bash
curl -fsSL https://raw.githubusercontent.com/hochoa13/Asistente-Harlest/main/scripts/install.sh | bash
```

Funciona en Linux, macOS y WSL2. El instalador se encarga de todo — Python, Node.js, dependencias y el comando `hermes`. Sin prerrequisitos excepto git.

> **Windows:** No se admite Windows nativo. Por favor instala [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install) y ejecuta el comando anterior.

Después de la instalación:

```bash
source ~/.bashrc    # recarga el shell (o: source ~/.zshrc)
hermes              # ¡empieza a chatear!
```

---

## Primeros Pasos

```bash
hermes              # CLI interactivo — inicia una conversación
hermes model        # Elige tu proveedor de LLM y modelo
hermes tools        # Configura qué herramientas están habilitadas
hermes config set   # Establece valores de configuración individuales
hermes gateway      # Inicia la puerta de enlace de mensajería (Telegram, Discord, etc.)
hermes setup        # Ejecuta el asistente de configuración completo (configura todo de una vez)
hermes claw migrate # Migra desde OpenClaw (si vienes de OpenClaw)
hermes update       # Actualiza a la última versión
hermes doctor       # Diagnostica cualquier problema
```

📖 **[Documentación completa →](https://hermes-agent.nousresearch.com/docs/)**

---

## Documentación

Toda la documentación se encuentra en **[hermes-agent.nousresearch.com/docs](https://hermes-agent.nousresearch.com/docs/)**:

| Sección | Qué se Cubre |
|---------|-------------|
| [Inicio Rápido](https://hermes-agent.nousresearch.com/docs/getting-started/quickstart) | Instalar → configurar → primera conversación en 2 minutos |
| [Uso de CLI](https://hermes-agent.nousresearch.com/docs/user-guide/cli) | Comandos, atajos de teclado, personalidades, sesiones |
| [Configuración](https://hermes-agent.nousresearch.com/docs/user-guide/configuration) | Archivo de configuración, proveedores, modelos, todas las opciones |
| [Puerta de Enlace de Mensajería](https://hermes-agent.nousresearch.com/docs/user-guide/messaging) | Telegram, Discord, Slack, WhatsApp, Signal, Home Assistant |
| [Seguridad](https://hermes-agent.nousresearch.com/docs/user-guide/security) | Aprobación de comandos, emparejamiento de DM, aislamiento de contenedor |
| [Herramientas y Conjuntos de Herramientas](https://hermes-agent.nousresearch.com/docs/user-guide/features/tools) | 40+ herramientas, sistema de conjuntos de herramientas, backends de terminal |
| [Sistema de Habilidades](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills) | Memoria procedimental, Centro de Habilidades, creación de habilidades |
| [Memoria](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory) | Memoria persistente, perfiles de usuario, mejores prácticas |
| [Integración MCP](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp) | Conecta cualquier servidor MCP para capacidades extendidas |
| [Programación Cron](https://hermes-agent.nousresearch.com/docs/user-guide/features/cron) | Tareas programadas con entrega de plataforma |
| [Archivos de Contexto](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files) | Contexto del proyecto que moldea cada conversación |
| [Arquitectura](https://hermes-agent.nousresearch.com/docs/developer-guide/architecture) | Estructura del proyecto, ciclo del agente, clases clave |
| [Contribuyendo](https://hermes-agent.nousresearch.com/docs/developer-guide/contributing) | Configuración de desarrollo, proceso de PR, estilo de código |
| [Referencia CLI](https://hermes-agent.nousresearch.com/docs/reference/cli-commands) | Todos los comandos y banderas |
| [Variables de Entorno](https://hermes-agent.nousresearch.com/docs/reference/environment-variables) | Referencia completa de variables de entorno |

---

## Migración desde OpenClaw

Si vienes de OpenClaw, Hermes puede importar automáticamente tu configuración, memorias, habilidades y claves de API.

**Durante la configuración inicial:** El asistente de configuración (`hermes setup`) detecta automáticamente `~/.openclaw` y ofrece migrar antes de que comience la configuración.

**En cualquier momento después de instalar:**

```bash
hermes claw migrate              # Migración interactiva (preajuste completo)
hermes claw migrate --dry-run    # Previsualizar qué se migrarían
hermes claw migrate --preset user-data   # Migrar sin secretos
hermes claw migrate --overwrite  # Sobrescribir conflictos existentes
```

Qué se importa:
- **SOUL.md** — archivo de persona
- **Memorias** — entradas MEMORY.md y USER.md
- **Habilidades** — habilidades creadas por el usuario → `~/.hermes/skills/openclaw-imports/`
- **Lista de permitidos de comandos** — patrones de aprobación
- **Configuración de mensajería** — configuraciones de plataforma, usuarios permitidos, directorio de trabajo
- **Claves de API** — secretos en lista blanca (Telegram, OpenRouter, OpenAI, Anthropic, ElevenLabs)
- **Activos de TTS** — archivos de audio del espacio de trabajo
- **Instrucciones del espacio de trabajo** — AGENTS.md (con `--workspace-target`)

Ver `hermes claw migrate --help` para todas las opciones, o usa la habilidad `openclaw-migration` para una migración guiada por agente interactivo con vistas previas de ejecución en seco.

---

## Contribuyendo

¡Aceptamos contribuciones! Ver la [Guía de Contribución](https://hermes-agent.nousresearch.com/docs/developer-guide/contributing) para configuración de desarrollo, estilo de código y proceso de PR.

Inicio rápido para contribuyentes:

```bash
git clone --recurse-submodules https://github.com/hochoa13/Asistente-Harlest.git
cd Asistente-Harlest
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[all,dev]"
uv pip install -e "./mini-swe-agent"
python -m pytest tests/ -q
```

---

## Comunidad

- 💬 [Discord](https://discord.gg/NousResearch)
- 📚 [Centro de Habilidades](https://agentskills.io)
- 🐛 [Problemas](https://github.com/hochoa13/Asistente-Harlest/issues)
- 💡 [Discusiones](https://github.com/hochoa13/Asistente-Harlest/discussions)

---

## Licencia

MIT — ver [LICENSE](LICENSE).

Creado por [Nous Research](https://nousresearch.com).
