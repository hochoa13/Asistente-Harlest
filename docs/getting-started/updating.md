---
sidebar_position: 3
title: "Actualizando y Desinstalando"
description: "Cómo actualizar Hermes Agent a la última versión o desinstalarlo"
---

# Actualizando y Desinstalando

## Actualizando

Actualiza a la última versión con un único comando:

```bash
hermes update
```

Esto extrae el código más reciente, actualiza las dependencias, y te pide que configures cualquier opción nueva que se haya añadido desde tu última actualización.

:::tip
`hermes update` detecta automáticamente nuevas opciones de configuración y te pide que las añadas. Si saltaste esa solicitud, puedes ejecutar manualmente `hermes config check` para ver opciones faltantes, luego `hermes config migrate` para añadirlas interactivamente.
:::

### Actualizando desde Plataformas de Mensajería

También puedes actualizar directamente desde Telegram, Discord, Slack o WhatsApp enviando:

```
/update
```

Esto extrae el código más reciente, actualiza las dependencias, y reinicia la puerta de enlace.

### Actualización Manual

Si instalaste manualmente (no vía el instalador rápido):

```bash
cd /ruta/a/hermes-agent
export VIRTUAL_ENV="$(pwd)/venv"

# Extrae el código más reciente y submódulos
git pull origin main
git submodule update --init --recursive

# Reinstala (recoge nuevas dependencias)
uv pip install -e ".[all]"
uv pip install -e "./mini-swe-agent"
uv pip install -e "./tinker-atropos"

# Verifica opciones de configuración nuevas
hermes config check
hermes config migrate   # Añade interactivamente cualquier opción faltante
```

---

## Desinstalando

```bash
hermes uninstall
```

El desinstalador te da la opción de mantener tus archivos de configuración (`~/.hermes/`) para una reinstalación futura.

### Desinstalación Manual

```bash
rm -f ~/.local/bin/hermes
rm -rf /ruta/a/hermes-agent
rm -rf ~/.hermes            # Opcional — mantén si planeas reinstalar
```

:::info
Si instalaste la puerta de enlace como un servicio de sistema, deténlo y desactívalo primero:
```bash
hermes gateway stop
# Linux: systemctl --user disable hermes-gateway
# macOS: launchctl remove ai.hermes.gateway
```
:::
