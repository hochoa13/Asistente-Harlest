---
title: Home Assistant
description: Controla tu hogar inteligente con Hermes Agent a través de la integración de Home Assistant.
sidebar_label: Home Assistant
sidebar_position: 5
---

# Integración de Home Assistant

Hermes Agent se integra con [Home Assistant](https://www.home-assistant.io/) de dos formas:

1. **Plataforma de puerta de enlace** — Se suscribe a cambios de estado en tiempo real a través de WebSocket y responde a eventos
2. **Herramientas de hogar inteligente** — Cuatro herramientas invocables por LLM para consultar y controlar dispositivos a través de la API REST

## Configuración

### 1. Crear un Token de Acceso de Larga Duración

1. Abre tu instancia de Home Assistant
2. Ve a tu **Perfil** (haz clic en tu nombre en la barra lateral)
3. Desplázate hasta **Tokens de Acceso de Larga Duración**
4. Haz clic en **Crear Token**, dale un nombre como "Agente Hermes"
5. Copia el token

### 2. Configurar Variables de Entorno

```bash
# Añade a ~/.hermes/.env

# Requerido: tu Token de Acceso de Larga Duración
HASS_TOKEN=your-long-lived-access-token

# Opcional: URL de HA (default: http://homeassistant.local:8123)
HASS_URL=http://192.168.1.100:8123
```

:::info
El conjunto de herramientas `homeassistant` se habilita automáticamente cuando se establece `HASS_TOKEN`. Tanto la plataforma de puerta de enlace como las herramientas de control de dispositivos se activan desde este único token.
:::

### 3. Iniciar la Puerta de Enlace

```bash
hermes gateway
```

Home Assistant aparecerá como una plataforma conectada junto con cualquier otra plataforma de mensajería (Telegram, Discord, etc.).

## Herramientas Disponibles

Hermes Agent registra cuatro herramientas para el control del hogar inteligente:

### `ha_list_entities`

Lista entidades de Home Assistant, opcionalmente filtradas por dominio o área.

**Parámetros:**
- `domain` *(opcional)* — Filtrar por dominio de entidad: `light`, `switch`, `climate`, `sensor`, `binary_sensor`, `cover`, `fan`, `media_player`, etc.
- `area` *(opcional)* — Filtrar por nombre de área/sala (coincide con nombres amigables): `living room`, `kitchen`, `bedroom`, etc.

**Ejemplo:**
```
Listar todas las luces en la sala de estar
```

Devuelve: IDs de entidad, estados y nombres amigables.

### `ha_get_state`

Obtiene el estado detallado de una entidad única, incluidos todos los atributos (brillo, color, punto de ajuste de temperatura, lecturas de sensores, etc.).

**Parámetros:**
- `entity_id` *(requerido)* — La entidad a consultar, ej. `light.living_room`, `climate.thermostat`, `sensor.temperature`

**Ejemplo:**
```
¿Cuál es el estado actual del climate.thermostat?
```

Devuelve: estado, todos los atributos, timestamps de último cambio/actualización.

### `ha_list_services`

Lista servicios disponibles (acciones) para el control de dispositivos. Muestra qué acciones se pueden realizar en cada tipo de dispositivo y qué parámetros aceptan.

**Parámetros:**
- `domain` *(opcional)* — Filtrar por dominio, ej. `light`, `climate`, `switch`

**Ejemplo:**
```
¿Qué servicios están disponibles para dispositivos de clima?
```

### `ha_call_service`

Llamar a un servicio de Home Assistant para controlar un dispositivo.

**Parámetros:**
- `domain` *(requerido)* — Dominio del servicio: `light`, `switch`, `climate`, `cover`, `media_player`, `fan`, `scene`, `script`
- `service` *(requerido)* — Nombre del servicio: `turn_on`, `turn_off`, `toggle`, `set_temperature`, `set_hvac_mode`, `open_cover`, `close_cover`, `set_volume_level`
- `entity_id` *(opcional)* — Entidad objetivo, ej. `light.living_room`
- `data` *(opcional)* — Parámetros adicionales como objeto JSON

**Ejemplos:**

```
Encender las luces de la sala de estar
→ ha_call_service(domain="light", service="turn_on", entity_id="light.living_room")
```

```
Establecer el termostato a 22 grados en modo calefacción
→ ha_call_service(domain="climate", service="set_temperature",
    entity_id="climate.thermostat", data={"temperature": 22, "hvac_mode": "heat"})
```

```
Establecer las luces de la sala de estar en azul al 50% de brillo
→ ha_call_service(domain="light", service="turn_on",
    entity_id="light.living_room", data={"brightness": 128, "color_name": "blue"})
```

## Plataforma de Puerta de Enlace: Eventos en Tiempo Real

El adaptador de puerta de enlace de Home Assistant se conecta a través de WebSocket y se suscribe a eventos `state_changed`. Cuando cambia el estado de un dispositivo, se reenvía al agente como un mensaje.

### Filtrado de Eventos

Configura qué eventos ve el agente a través de la configuración de plataforma en la puerta de enlace:

```python
# En configuración extra de plataforma
{
    "watch_domains": ["climate", "binary_sensor", "alarm_control_panel"],
    "watch_entities": ["sensor.front_door"],
    "ignore_entities": ["sensor.uptime", "sensor.cpu_usage"],
    "cooldown_seconds": 30
}
```

| Configuración | Default | Descripción |
|---------|---------|-------------|
| `watch_domains` | *(todas)* | Solo monitorea estos dominios de entidad |
| `watch_entities` | *(todas)* | Solo monitorea estas entidades específicas |
| `ignore_entities` | *(ninguna)* | Siempre ignora estas entidades |
| `cooldown_seconds` | `30` | Segundos mínimos entre eventos para la misma entidad |

:::tip
Sin ningún filtro, el agente recibe **todos** los cambios de estado, que pueden ser ruidosos. Para uso práctico, establece `watch_domains` en los dominios que te importan (ej. `climate`, `binary_sensor`, `alarm_control_panel`).
:::

### Formato de Eventos

Los cambios de estado se formatean como mensajes legibles para humanos basados en dominio:

| Dominio | Formato |
|--------|--------|
| `climate` | "HVAC mode changed from 'off' to 'heat' (current: 21, target: 23)" |
| `sensor` | "Cambió de 21°C a 22°C" |
| `binary_sensor` | "desencadenado" / "borrado" |
| `light`, `switch`, `fan` | "encendido" / "apagado" |
| `alarm_control_panel` | "Estado de alarma cambió de 'armed_away' a 'triggered'" |
| *(otro)* | "Cambió de 'viejo' a 'nuevo'" |

### Respuestas del Agente

Los mensajes salientes del agente se entregan como **notificaciones persistentes de Home Assistant** (a través de `persistent_notification.create`). Estos aparecen en el panel de notificaciones de HA con el título "Hermes Agent".

### Gestión de Conexión

- **WebSocket** con latido de 30 segundos para eventos en tiempo real
- **Reconexión automática** con backoff: 5s → 10s → 30s → 60s
- **API REST** para notificaciones salientes (sesión separada para evitar conflictos de WebSocket)
- **Autorización** — Los eventos de HA siempre están autorizados (no se necesita allowlist de usuario, ya que `HASS_TOKEN` autentica la conexión)

## Seguridad

Las herramientas de Home Assistant aplican restricciones de seguridad:

:::warning Dominios Bloqueados
Los siguientes dominios de servicio están **bloqueados** para prevenir ejecución de código arbitrario en el host de HA:

- `shell_command` — Comandos shell arbitrarios
- `command_line` — Sensores/switches que ejecutan comandos
- `python_script` — Ejecución de Python con script
- `pyscript` — Integración de scripting más amplia
- `hassio` — Control de addon, apagado/reinicio del host
- `rest_command` — Solicitudes HTTP desde servidor HA (vector SSRF)

Intentar llamar a servicios en estos dominios devuelve un error.
:::

Los IDs de entidad se validan contra el patrón `^[a-z_][a-z0-9_]*\.[a-z0-9_]+$` para prevenir ataques de inyección.

## Automaciones Ejemplos

### Rutina Matutina

```
Usuario: Inicia mi rutina matutina

Agente:
1. ha_call_service(domain="light", service="turn_on",
     entity_id="light.bedroom", data={"brightness": 128})
2. ha_call_service(domain="climate", service="set_temperature",
     entity_id="climate.thermostat", data={"temperature": 22})
3. ha_call_service(domain="media_player", service="turn_on",
     entity_id="media_player.kitchen_speaker")
```

### Verificación de Seguridad

```
Usuario: ¿Está la casa segura?

Agente:
1. ha_list_entities(domain="binary_sensor")
     → comprueba sensores de puerta/ventana
2. ha_get_state(entity_id="alarm_control_panel.home")
     → comprueba estado de alarma
3. ha_list_entities(domain="lock")
     → comprueba estados de cerraduras
4. Reporta: "Todas las puertas cerradas, alarma armed_away, todas las cerraduras activadas."
```

### Automatización Reactiva (a través de Eventos de Puerta de Enlace)

Cuando está conectado como plataforma de puerta de enlace, el agente puede reaccionar a eventos:

```
[Home Assistant] Puerta Principal: desencadenada (fue borrada)

Agente automáticamente:
1. ha_get_state(entity_id="binary_sensor.front_door")
2. ha_call_service(domain="light", service="turn_on",
     entity_id="light.hallway")
3. Envía notificación: "Puerta principal abierta. Luces del pasillo encendidas."
```
