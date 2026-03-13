# Migración desde OpenClaw a Hermes Agent

Esta guía cubre cómo importar su configuración de OpenClaw, memorias, habilidades y claves API en Hermes Agent.

## Tres formas de migrar

### 1. Automático (durante la configuración inicial)

Cuando ejecuta `hermes setup` por primera vez y Hermes detecta `~/.openclaw`, automáticamente ofrece importar sus datos de OpenClaw antes de que comience la configuración. Solo acepte el mensaje y todo se maneja para usted.

### 2. Comando CLI (rápido, programable)

```bash
hermes claw migrate                      # Migración completa con aviso de confirmación
hermes claw migrate --dry-run            # Vista previa de lo que sucedería
hermes claw migrate --preset user-data   # Migrar sin claves API/secretos
hermes claw migrate --yes                # Omitir avisos de confirmación
```

**Todas las opciones:**

| Bandera | Descripción |
|------|-------------|
| `--source PATH` | Ruta al directorio OpenClaw (predeterminado: `~/.openclaw`) |
| `--dry-run` | Solo vista previa — no se modifican archivos |
| `--preset {user-data,full}` | Preset de migración (predeterminado: `full`). `user-data` excluye secretos |
| `--overwrite` | Sobrescribir archivos existentes (predeterminado: omitir conflictos) |
| `--migrate-secrets` | Incluir secretos permitidos (habilitado automáticamente con preset `full`) |
| `--workspace-target PATH` | Copiar instrucciones de espacio de trabajo (AGENTS.md) a esta ruta absoluta |
| `--skill-conflict {skip,overwrite,rename}` | Cómo manejar conflictos de nombre de habilidad (predeterminado: `skip`) |
| `--yes`, `-y` | Omitir avisos de confirmación |

### 3. Guía del Agente (interactivo, con vistas previas)

Pida al agente que ejecute la migración por usted:

```
> Migra mi configuración de OpenClaw a Hermes
```

El agente utilizará la habilidad `openclaw-migration` para:
1. Ejecutar una ejecución en seco primero para vista previa de cambios
2. Preguntar sobre resolución de conflictos (SOUL.md, habilidades, etc.)
3. Dejar que elija entre presets `user-data` y `full`
4. Ejecutar la migración con tus elecciones
5. Imprimir un resumen detallado de lo que se migró

## Qué se migra

### Preset `user-data`
| Elemento | Origen | Destino |
|------|--------|-------------|
| SOUL.md | `~/.openclaw/workspace/SOUL.md` | `~/.hermes/SOUL.md` |
| Entradas de memoria | `~/.openclaw/workspace/MEMORY.md` | `~/.hermes/memories/MEMORY.md` |
| Perfil de usuario | `~/.openclaw/workspace/USER.md` | `~/.hermes/memories/USER.md` |
| Habilidades | `~/.openclaw/workspace/skills/` | `~/.hermes/skills/openclaw-imports/` |
| Lista de permitidos de comando | `~/.openclaw/workspace/exec_approval_patterns.yaml` | Fusionado en `~/.hermes/config.yaml` |
| Configuración de mensajería | `~/.openclaw/config.yaml` (TELEGRAM_ALLOWED_USERS, MESSAGING_CWD) | `~/.hermes/.env` |
| Activos de TTS | `~/.openclaw/workspace/tts/` | `~/.hermes/tts/` |

### Preset `full` (agrega a `user-data`)
| Elemento | Origen | Destino |
|------|--------|-------------|
| Token de bot Telegram | `~/.openclaw/config.yaml` | `~/.hermes/.env` |
| Clave API de OpenRouter | `~/.openclaw/.env` o config | `~/.hermes/.env` |
| Clave API de OpenAI | `~/.openclaw/.env` o config | `~/.hermes/.env` |
| Clave API de Anthropic | `~/.openclaw/.env` o config | `~/.hermes/.env` |
| Clave API de ElevenLabs | `~/.openclaw/.env` o config | `~/.hermes/.env` |

Solo estos 6 secretos permitidos se importan. Otras credenciales se omiten y se reportan.

## Manejo de conflictos

De forma predeterminada, la migración **no sobrescribirá** datos existentes de Hermes:

- **SOUL.md** — omitido si uno ya existe en `~/.hermes/`
- **Entradas de memoria** — omitidas si ya existen memorias (para evitar duplicados)
- **Habilidades** — omitidas si ya existe una habilidad con el mismo nombre
- **Claves API** — omitidas si la clave ya está configurada en `~/.hermes/.env`

Para sobrescribir conflictos, use `--overwrite`. La migración crea copias de seguridad antes de sobrescribir.

Para habilidades, también puede usar `--skill-conflict rename` para importar habilidades conflictivas bajo un nuevo nombre (p. ej., `skill-name-imported`).

## Reporte de migración

Cada migración (incluidas las ejecuciones en seco) produce un reporte mostrando:
- **Elementos migrados** — lo que se importó exitosamente
- **Conflictos** — elementos omitidos porque ya existen
- **Elementos omitidos** — elementos no encontrados en la fuente
- **Errores** — elementos que no se pudieron importar

Para ejecuciones completadas, el reporte completo se guarda en `~/.hermes/migration/openclaw/<timestamp>/`.

## Solución de Problemas

### "Directorio de OpenClaw no encontrado"
La migración busca `~/.openclaw` de forma predeterminada. Si su OpenClaw está instalado en otro lugar, use `--source`:
```bash
hermes claw migrate --source /path/to/.openclaw
```

### "Script de migración no encontrado"
El script de migración se envía con Hermes Agent. Si instaló vía pip (no git clone), el directorio `optional-skills/` puede no estar presente. Instale la habilidad desde el Centro de Habilidades:
```bash
hermes skills install openclaw-migration
```

### Desbordamiento de memoria
Si su MEMORY.md o USER.md de OpenClaw excede los límites de caracteres de Hermes, las entradas excedentes se exportan a un archivo de desbordamiento en el directorio de reporte de migración. Puede revisar manualmente y agregar las más importantes.
