# Puntos de Control del Sistema de Archivos

Hermes puede crear automáticamente una instantánea de tu directorio de trabajo antes de realizar cambios en archivos, dándote una red de seguridad para deshacer si algo sale mal.

## Cómo Funciona

Cuando está habilitado, Hermes toma una **instantánea única** al inicio de cada turno de conversación antes de la primera operación que modifica archivos (`write_file` o `patch`). Esto crea una copia de seguridad puntual que puedes restaurar en cualquier momento.

Bajo el capó, los puntos de control usan un **repositorio git sombra** almacenado en `~/.hermes/checkpoints/`. Esto está completamente separado del git de tu proyecto — no se crea directorio `.git` en tu proyecto, y tu propio historial de git nunca se toca.

## Habilitando Puntos de Control

### Por sesión (bandera CLI)

```bash
hermes --checkpoints
```

### De Forma Permanente (config.yaml)

```yaml
# ~/.hermes/config.yaml
checkpoints:
  enabled: true
  max_snapshots: 50  # máximo de puntos de control por directorio (predeterminado: 50)
```

## Deshacer

Usa el comando slash `/rollback`:

```
/rollback          # List all available checkpoints
/rollback 1        # Restore to checkpoint #1 (most recent)
/rollback 3        # Restore to checkpoint #3 (further back)
/rollback abc1234  # Restore by git commit hash
```

Ejemplo output:

```
📸 Puntos de Control for /home/user/project:

  1. abc1234  2026-03-10 14:22  before write_file
  2. def5678  2026-03-10 14:15  before patch
  3. ghi9012  2026-03-10 14:08  before write_file

Use /rollback <number> to restore, e.g. /rollback 1
```

When you restore, Hermes automatically takes a **pre-Deshacer snapshot** first — so you can always undo your undo.

## What Gets Checkpointed

Puntos de control capture the entire working directorio (the project root), excluding common large/sensitive patterns:

- `node_modules/`, `dist/`, `build/`
- `.env`, `.env.*`
- `__pycache__/`, `*.pyc`
- `.venv/`, `venv/`
- `.git/`
- `.DS_Store`, `*.log`

## Rendimiento

Los puntos de control están diseñados para ser ligeros:

- **Una vez por turno** — solo la primera operación de archivo desencadena una instantánea, no cada escritura
- **Omite directorios grandes** — los directorios con más de 50.000 archivos se omiten automáticamente
- **Omite cuando nada cambió** — si no se modificaron archivos desde el último punto de control, no se crea commit
- **No bloqueante** — si un punto de control falla por cualquier motivo, la operación de archivo procede normalmente

## Cómo Se Determina la Raíz del Proyecto

Cuando escribes en un archivo como `src/components/Button.tsx`, Hermes camina hacia arriba en el árbol de directorios buscando marcadores de proyecto (`.git`, `pyproject.toml`, `package.json`, `Cargo.toml`, etc.) para encontrar la raíz del proyecto. Esto asegura que se haga punto de control de todo el proyecto, no solo del directorio padre del archivo.

## Plataformas

Los puntos de control funcionan en ambos:
- **CLI** — usa tu directorio de trabajo actual
- **Gateway** (Telegram, Discord, etc.) — usa `MESSAGING_CWD`

El comando `/rollback` está disponible en todas las plataformas.

## Preguntas Frecuentes

**¿Esto entra en conflicto con el git de mi proyecto?**
No. Los puntos de control usan un repositorio git sombra completamente separado a través de variables de entorno `GIT_DIR`. El `.git/` de tu proyecto nunca se toca.

**¿Cuánto espacio en disco usan los puntos de control?**
Git es muy eficiente al almacenar diffs. Para la mayoría de proyectos, los datos de punto de control son insignificantes. Los viejos puntos de control se podan cuando se excede `max_snapshots`.

**¿Puedo hacer punto de control sin git instalado?**
No — git debe estar disponible en tu ruta. Si no está instalado, los puntos de control se deshabilitan silenciosamente.

**¿Puedo deshacer entre sesiones?**
Sí. Los puntos de control persisten en `~/.hermes/checkpoints/` y sobreviven entre sesiones. Puedes deshacer a un punto de control de ayer.
