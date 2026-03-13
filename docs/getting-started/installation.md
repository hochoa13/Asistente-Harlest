---
sidebar_position: 2
title: "Instalación"
description: "Instala Hermes Agent en Linux, macOS o WSL2"
---

# Instalación

Obtén Hermes Agent funcionando en menos de dos minutos con el instalador de una línea, o sigue los pasos manuales para tener control total.

## Instalación Rápida

### Linux / macOS / WSL2

```bash
curl -fsSL https://raw.githubusercontent.com/hochoa13/Asistente-Harlest/main/scripts/install.sh | bash
```

:::warning Windows
Windows nativo **no es compatible**. Por favor instala [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install) y ejecuta Hermes Agent desde allí. El comando de instalación anterior funciona dentro de WSL2.
:::

### Qué hace el instalador

El instalador maneja todo automáticamente — todas las dependencias (Python, Node.js, ripgrep, ffmpeg), la clonación del repositorio, el ambiente virtual, la configuración del comando global `hermes`, y la configuración del proveedor LLM. Al final, estará listo para chatear.

### Después de la instalación

Recarga tu shell e inicia a chatear:

```bash
source ~/.bashrc   # o: source ~/.zshrc
hermes             # ¡Comienza a chatear!
```

Para reconfigurar configuraciones individuales más tarde, usa los comandos dedicados:

```bash
hermes model          # Elige tu proveedor LLM y modelo
hermes tools          # Configura qué herramientas están habilitadas
hermes gateway setup  # Configura plataformas de mensajería
hermes config set     # Define valores de configuración individuales
hermes setup          # O ejecuta el asistente de configuración completo para configurar todo de una vez
```

---

## Requisitos previos

El único requisito previo es **Git**. El instalador maneja automáticamente todo lo demás:

- **uv** (gestor de paquetes Python rápido)
- **Python 3.11** (vía uv, sin necesidad de sudo)
- **Node.js v22** (para automatización de navegador y puente de WhatsApp)
- **ripgrep** (búsqueda rápida de archivos)
- **ffmpeg** (conversión de formato de audio para TTS)

:::info
No necesitas instalar Python, Node.js, ripgrep o ffmpeg manualmente. El instalador detecta qué falta e instala por ti. Solo asegúrate de que `git` esté disponible (`git --version`).
:::

---

## Instalación manual

Si prefieres tener control total sobre el proceso de instalación, sigue estos pasos.

### Paso 1: Clonar el repositorio

Clona con `--recurse-submodules` para obtener los submódulos requeridos:

```bash
git clone --recurse-submodules https://github.com/hochoa13/Asistente-Harlest.git
cd hermes-agent
```

Si ya clonaste sin `--recurse-submodules`:
```bash
git submodule update --init --recursive
```

### Paso 2: Instalar uv y crear el ambiente virtual

```bash
# Instala uv (si no está instalado)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Crea venv con Python 3.11 (uv lo descarga si no está presente — sin sudo)
uv venv venv --python 3.11
```

:::tip
No necesitas activar el venv para usar `hermes`. El punto de entrada tiene un shebang hardcodeado que apunta al Python del venv, así que funciona globalmente una vez vinculado simbólicamente.
:::

### Paso 3: Instalar dependencias de Python

```bash
# Dile a uv cuál venv usar
export VIRTUAL_ENV="$(pwd)/venv"

# Instala con todos los extras
uv pip install -e ".[all]"
```

Si solo quieres el agente principal (sin soporte para Telegram/Discord/cron):
```bash
uv pip install -e "."
```

<details>
<summary><strong>Desglose de extras opcionales</strong></summary>

| Extra | Qué agrega | Comando de instalación |
|-------|-----------|------------------------|
| `all` | Todo lo siguiente | `uv pip install -e ".[all]"` |
| `messaging` | Gateway de Telegram y Discord | `uv pip install -e ".[messaging]"` |
| `cron` | Análisis de expresiones cron para tareas programadas | `uv pip install -e ".[cron]"` |
| `cli` | Interfaz de menú de terminal para asistente de configuración | `uv pip install -e ".[cli]"` |
| `modal` | Backend de ejecución en nube Modal | `uv pip install -e ".[modal]"` |
| `tts-premium` | Voces premium de ElevenLabs | `uv pip install -e ".[tts-premium]"` |
| `pty` | Soporte de terminal PTY | `uv pip install -e ".[pty]"` |
| `honcho` | Memoria nativa de IA (integración Honcho) | `uv pip install -e ".[honcho]"` |
| `mcp` | Soporte del Protocolo de Contexto de Modelo | `uv pip install -e ".[mcp]"` |
| `homeassistant` | Integración de Home Assistant | `uv pip install -e ".[homeassistant]"` |
| `slack` | Mensajería de Slack | `uv pip install -e ".[slack]"` |
| `dev` | pytest y utilidades de prueba | `uv pip install -e ".[dev]"` |

Puedes combinar extras: `uv pip install -e ".[messaging,cron]"`

</details>

### Paso 4: Instalar paquetes del submódulo

```bash
# Backend de herramienta de terminal (requerido para ejecución de terminal/comandos)
uv pip install -e "./mini-swe-agent"

# Backend de entrenamiento RL
uv pip install -e "./tinker-atropos"
```

Ambos son opcionales — si los omites, los conjuntos de herramientas correspondientes simplemente no estarán disponibles.

### Paso 5: Instalar dependencias de Node.js (opcional)

Solo necesaria para **automatización de navegador** (impulsada por Browserbase) y **puente de WhatsApp**:

```bash
npm install
```

### Paso 6: Crear el directorio de configuración

```bash
# Crea la estructura de directorios
mkdir -p ~/.hermes/{cron,sessions,logs,memories,skills,pairing,hooks,image_cache,audio_cache,whatsapp/session}

# Copia el archivo de configuración de ejemplo
cp cli-config.yaml.example ~/.hermes/config.yaml

# Crea un archivo .env vacío para las claves API
touch ~/.hermes/.env
```

### Paso 7: Añade tus claves API

Abre `~/.hermes/.env` y añade al menos una clave de proveedor LLM:

```bash
# Requerido — al menos un proveedor LLM:
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Opcional — habilita herramientas adicionales:
FIRECRAWL_API_KEY=fc-your-key          # Búsqueda web y scraping (o auto-hosting, ver docs)
FAL_KEY=your-fal-key                   # Generación de imágenes (FLUX)
```

O configúralas vía CLI:
```bash
hermes config set OPENROUTER_API_KEY sk-or-v1-your-key-here
```

### Paso 8: Añade `hermes` a tu PATH

```bash
mkdir -p ~/.local/bin
ln -sf "$(pwd)/venv/bin/hermes" ~/.local/bin/hermes
```

Si `~/.local/bin` no está en tu PATH, añádelo a tu configuración de shell:

```bash
# Bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc

# Zsh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc

# Fish
fish_add_path $HOME/.local/bin
```

### Paso 9: Configura tu proveedor

```bash
hermes model       # Selecciona tu proveedor LLM y modelo
```

### Paso 10: Verifica la instalación

```bash
hermes version    # Comprueba que el comando está disponible
hermes doctor     # Ejecuta diagnósticos para verificar que todo funciona
hermes status     # Comprueba tu configuración
hermes chat -q "¡Hola! ¿Qué herramientas tienes disponibles?"
```

---

## Referencia rápida: Instalación manual (Condensada)

Para quienes solo quieren los comandos:

```bash
# Instala uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clona y entra
git clone --recurse-submodules https://github.com/hochoa13/Asistente-Harlest.git
cd hermes-agent

# Crea venv con Python 3.11
uv venv venv --python 3.11
export VIRTUAL_ENV="$(pwd)/venv"

# Instala todo
uv pip install -e ".[all]"
uv pip install -e "./mini-swe-agent"
uv pip install -e "./tinker-atropos"
npm install  # opcional, para herramientas de navegador y WhatsApp

# Configura
mkdir -p ~/.hermes/{cron,sessions,logs,memories,skills,pairing,hooks,image_cache,audio_cache,whatsapp/session}
cp cli-config.yaml.example ~/.hermes/config.yaml
touch ~/.hermes/.env
echo 'OPENROUTER_API_KEY=sk-or-v1-your-key' >> ~/.hermes/.env

# Haz hermes disponible globalmente
mkdir -p ~/.local/bin
ln -sf "$(pwd)/venv/bin/hermes" ~/.local/bin/hermes

# Verifica
hermes doctor
hermes
```

---

## Solución de problemas

| Problema | Solución |
|----------|----------|
| `hermes: command not found` | Recarga tu shell (`source ~/.bashrc`) o comprueba PATH |
| `API key not set` | Ejecuta `hermes model` para configurar tu proveedor, o `hermes config set OPENROUTER_API_KEY your_key` |
| Configuración faltante después de actualizar | Ejecuta `hermes config check` después `hermes config migrate` |

Para más diagnósticos, ejecuta `hermes doctor` — te dirá exactamente qué falta y cómo arreglarlo.
