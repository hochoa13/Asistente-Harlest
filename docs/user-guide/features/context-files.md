---
sidebar_position: 8
title: "Archivos de Contexto"
description: "Archivos de contexto del proyecto — AGENTS.md, alma.md y .cursorrules — inyectados automáticamente en cada conversación"
---

# Archivos de Contexto

Hermes Agent descubre y carga automáticamente archivos de contexto del proyecto desde tu directorio de trabajo. Estos archivos se inyectan en el indicador del sistema al inicio de cada sesión, dando al agente conocimiento persistente sobre las convenciones, arquitectura y preferencias de tu proyecto.

## Archivos de Contexto Soportados

| Archivo | Propósito | Descubrimiento |
|------|---------|-----------|
| **AGENTS.md** | Instrucciones del proyecto, convenciones, arquitectura | Recursivo (camina subdirectorios) |
| **alma.md** | Personalización de personalidad y tono | CWD → `~/.hermes/alma.md` respaldo |
| **.cursorrules** | Convenciones de codificación de IDE Cursor | Solo CWD |
| **.cursor/rules/*.mdc** | Módulos de reglas de IDE Cursor | Solo CWD |

## AGENTS.md

`AGENTS.md` es el archivo de contexto del proyecto primario. Le dice al agente cómo se estructura tu proyecto, qué convenciones seguir y cualquier instrucción especial.

### Descubrimiento Jerárquico

Hermes camina el árbol de directorios comenzando desde el directorio de trabajo y carga **todos** los archivos `AGENTS.md` encontrados, ordenados por profundidad. Esto soporta configuraciones de estilo monorepo:

```
my-project/
├── AGENTS.md              ← Contexto del proyecto de nivel superior
├── frontend/
│   └── AGENTS.md          ← Instrucciones específicas del frontend
├── backend/
│   └── AGENTS.md          ← Instrucciones específicas del backend
└── shared/
    └── AGENTS.md          ← Convenciones de biblioteca compartida
```

Los cuatro archivos se concatenan en un bloque de contexto único con encabezados de ruta relativa.

:::información
Los directorios que se omiten durante la caminata: directorios con prefijo `.`, `node_modules`, `__pycache__`, `venv`, `.venv`.
:::

### Ejemplo de AGENTS.md

```markdown
# Contexto del Proyecto

Esta es una aplicación web Next.js 14 con un backend FastAPI de Python.

## Arquitectura
- Frontend: Next.js 14 con App Router en `/frontend`
- Backend: FastAPI en `/backend`, usa ORM SQLAlchemy
- Base de datos: PostgreSQL 16
- Implementación: Docker Compose en un VPS de Hetzner

## Convenciones
- Usa modo strict de TypeScript para todo el código frontend
- Código Python sigue PEP 8, usa type hints en todas partes
- Todos los endpoints de API devuelven JSON con forma `{data, error, meta}`
- Las pruebas van en directorios `__tests__/` (frontend) o `tests/` (backend)

## Notas Importantes
- Nunca modifiques archivos de migración directamente — usa comandos de Alembic
- El archivo `.env.local` tiene claves API reales, no lo hagas commit
- Puerto frontend es 3000, backend es 8000, BD es 5432
```

## alma.md

`alma.md` controla la personalidad, tono y estilo de comunicación del agente. Ve la página [Personalidad](/docs/user-guide/features/Personalidad) para detalles completos.

**Orden de descubrimiento:**

1. `alma.md` o `alma.md` en el directorio de trabajo actual
2. `~/.hermes/alma.md` (respaldo global)

Cuando se encuentra un alma.md, se instruye al agente:

> *"Si alma.md está presente, encarna su persona y tono. Evita respuestas rígidas y genéricas; sigue su orientación a menos que instrucciones de mayor prioridad la anulen."

## .cursorrules

Hermes es compatible con el archivo `.cursorrules` de Cursor IDE y módulos de reglas `.cursor/rules/*.mdc`. Si estos archivos existen en la raíz de tu proyecto, se cargan junto con AGENTS.md.

Esto significa que tus convenciones de Cursor existentes se aplican automáticamente cuando usas Hermes.

## Cómo se Cargan los Archivos de Contexto

Los archivos de contexto se cargan a través de `build_context_files_prompt()` en `agent/prompt_builder.py`:

1. **Al inicio de sesión** — la función escanea el directorio de trabajo
2. **Se lee el contenido** — cada archivo se lee como texto UTF-8
3. **Escaneo de seguridad** — el contenido se verifica para patrones de inyección de indicador
4. **Truncamiento** — los archivos que exceden 20.000 caracteres se truncan cabeza/cola (70% cabeza, 20% cola, con un marcador en el medio)
5. **Asamblea** — todas las secciones se combinan bajo un encabezado `# Contexto del Proyecto`
6. **Inyección** — el contenido montado se agrega al indicador del sistema

La sección de indicador final se ve así:

```
# Contexto del Proyecto

Los siguientes archivos de contexto del proyecto se han cargado y deben seguirse:

## AGENTS.md

[Tu contenido de AGENTS.md aquí]

## .cursorrules

[Tu contenido de .cursorrules aquí]

## SOUL.md

Si SOUL.md está presente, encarna su persona y tono...

[Tu contenido de SOUL.md aquí]
```

## Seguridad: Protección Contra Inyección de Indicador

Todos los archivos de contexto se escanean en busca de inyección de indicador potencial antes de ser incluidos. El escáner verifica:

- **Intentos de anulación de instrucción**: "ignorar instrucciones anteriores", "descuidar tus reglas"
- **Patrones de engaño**: "no le digas al usuario"
- **Anulaciones de indicador del sistema**: "anular indicador del sistema"
- **Comentarios HTML ocultos**: `<!-- ignorar instrucciones -->`
- **Elementos div ocultos**: `<div style="display:none">`
- **Exfiltración de credenciales**: `curl ... $API_KEY`
- **Acceso a archivo secreto**: `cat .env`, `cat credentials`
- **Caracteres invisibles**: espacios de ancho cero, anulaciones bidireccionales, unidos de palabras

Si se detecta algún patrón de amenaza, el archivo se bloquea:

```
[BLOQUEADO: AGENTS.md contenía inyección de indicador potencial (prompt_injection). Contenido no cargado.]
```

:::advertencia
Este escáner protege contra patrones comunes de inyección, pero no es un sustituto para revisar el contenido de Archivos de Contexto en repositorios compartidos. Siempre valida el contenido de AGENTS.md en proyectos que no escribiste.
:::

## Límites de Tamaño

| Límite | Valor |
|-------|-------|
| Máx caracteres por archivo | 20.000 (~7.000 tokens) |
| Relación de truncamiento de cabeza | 70% |
| Relación de truncamiento de cola | 20% |
| Marcador de truncamiento | 10% (muestra recuentos de caracteres y sugiere usar herramientas de archivo) |

Cuando un archivo excede 20.000 caracteres, el mensaje de truncamiento se lee:

```
[...truncado AGENTS.md: mantenido 14000+4000 de 25000 caracteres. Usa herramientas de archivo para leer el archivo completo.]
```

## Consejos para Archivos de Contexto Efectivos

:::consejo Mejores prácticas para AGENTS.md
1. **Manténlo conciso** — mantén bien por debajo de 20K caracteres; el agente lo lee cada turno
2. **Estructura con encabezados** — usa secciones `##` para arquitectura, convenciones, notas importantes
3. **Incluye ejemplos concretos** — muestra patrones de código preferidos, formas de API, convenciones de nombres
4. **Menciona qué NO hacer** — "nunca modifiques archivos de migración directamente"
5. **Lista rutas clave y puertos** — el agente los usa para comandos de terminal
6. **Actualiza conforme el proyecto evoluciona** — el contexto antiguo es peor que ningún contexto
:::

### Contexto Por Subdirectorio

Para monorepos, put instrucciones específicas de subdirectorio en archivos AGENTS.md anidados:

```markdown
<!-- frontend/AGENTS.md -->
# Contexto del Frontend

- Usa `pnpm` no `npm` para gestión de paquetes
- Los componentes van en `src/components/`, páginas en `src/app/`
- Usa Tailwind CSS, nunca estilos en línea
- Ejecuta pruebas con `pnpm test`
```

```markdown
<!-- backend/AGENTS.md -->
# Contexto del Backend

- Usa `poetry` para gestión de dependencias
- Ejecuta el servidor de desarrollo con `poetry run uvicorn main:app --reload`
- Todos los endpoints necesitan docstrings OpenAPI
- Los modelos de base de datos están en `models/`, esquemas en `schemas/`
```
