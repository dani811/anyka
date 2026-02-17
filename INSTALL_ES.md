# Guía de Instalación - Anyka Audio Bidireccional

Esta guía proporciona instrucciones detalladas paso a paso para instalar la integración de Audio Bidireccional Anyka en Home Assistant.

## Requisitos Previos

Antes de instalar, asegúrese de tener:

1. **Home Assistant** (versión 2021.12 o más reciente recomendada)
2. **AppDaemon** instalado y configurado en Home Assistant
3. **ffmpeg** instalado en su sistema
4. **Dispositivo de entrada de audio** (micrófono) configurado en su host de Home Assistant
5. **Cámara Anyka** accesible en su red local

## Métodos de Instalación

### Método 1: Instalación Manual (Recomendado)

#### Paso 1: Instalar la Integración Personalizada de Home Assistant

1. **Acceda a su directorio de configuración de Home Assistant**
   - Si usa Home Assistant OS: `/config/`
   - Si usa Docker: Su volumen de configuración mapeado
   - Si usa instalación Core: Usualmente `~/.homeassistant/` o `/home/homeassistant/.homeassistant/`

2. **Cree el directorio custom_components** (si no existe):
   ```bash
   cd /config
   mkdir -p custom_components
   ```

3. **Copie los archivos de la integración**:
   ```bash
   cd custom_components
   mkdir -p anyka_talk
   ```
   
   Copie estos archivos a `custom_components/anyka_talk/`:
   - `__init__.py`
   - `manifest.json`
   - `services.yaml`

4. **Verifique la estructura**:
   ```
   /config/
   └── custom_components/
       └── anyka_talk/
           ├── __init__.py
           ├── manifest.json
           └── services.yaml
   ```

5. **Reinicie Home Assistant**
   - Vaya a **Ajustes** → **Sistema** → **Reiniciar**
   - O use el servicio: `homeassistant.restart`

#### Paso 2: Instalar la Aplicación AppDaemon

1. **Acceda a su directorio de aplicaciones de AppDaemon**
   - Ubicación predeterminada: `/config/appdaemon/apps/`
   - O verifique su configuración de AppDaemon para el directorio de apps

2. **Copie los archivos de AppDaemon**:
   ```bash
   cd /config/appdaemon/apps
   ```
   
   Copie estos archivos:
   - `anyka_talk.py`
   - `apps.yaml` (combine con el existente si ya tiene uno)

3. **Configure apps.yaml**:
   
   Si ya tiene un `apps.yaml`, agregue esta configuración:
   ```yaml
   anyka_talk:
     module: anyka_talk
     class: AnykaTalk
   ```
   
   Si no tiene un `apps.yaml`, use el proporcionado tal como está.

4. **Verifique la estructura**:
   ```
   /config/appdaemon/apps/
   ├── anyka_talk.py
   └── apps.yaml
   ```

5. **Reinicie AppDaemon**
   - Vaya a **Ajustes** → **Complementos** → **AppDaemon** → **Reiniciar**
   - O reinicie el contenedor/proceso de AppDaemon

6. **Verifique que AppDaemon esté funcionando**:
   - Revise los registros de AppDaemon para: `"Initializing Anyka Talk worker"`
   - Verifique que la API HTTP esté disponible en `http://localhost:5050`

### Método 2: Usando HACS (Futuro)

*La instalación mediante HACS estará disponible una vez que el repositorio sea agregado a HACS.*

## Configuración

### Puerto de la API HTTP de AppDaemon

Por defecto, la integración espera que la API HTTP de AppDaemon esté en el puerto 5050. Si su AppDaemon usa un puerto diferente:

1. Verifique su configuración de AppDaemon (`appdaemon.yaml`):
   ```yaml
   appdaemon:
     plugins:
       HASS:
         type: hass
   http:
     url: http://127.0.0.1:5050
   ```

2. Si usa un puerto diferente, deberá modificar `APPDAEMON_URL` en `custom_components/anyka_talk/__init__.py`.

### Configuración del Dispositivo de Audio

La configuración predeterminada usa el dispositivo de entrada de audio `default` de ALSA. Para usar un dispositivo diferente:

1. Liste los dispositivos de audio disponibles:
   ```bash
   arecord -L
   ```

2. Modifique la entrada de audio en `appdaemon/apps/anyka_talk.py` (línea 84):
   ```python
   "-i", "hw:0,0",  # Cambie de "default" a su dispositivo
   ```

### Configuración del Puerto de la Cámara

El puerto predeterminado de la cámara es 10000 (TCP). Si su cámara Anyka usa un puerto diferente, modifique la línea 89 en `appdaemon/apps/anyka_talk.py`:
```python
f"tcp://{camera_ip}:SU_PUERTO_AQUI"
```

## Verificación

### 1. Verificar Carga de la Integración

1. Vaya a **Herramientas de Desarrollador** → **Servicios**
2. Busque estos servicios:
   - `anyka_talk.start`
   - `anyka_talk.stop`

¡Si ve estos servicios, la integración se cargó correctamente!

### 2. Verificar el Worker de AppDaemon

1. Vaya a **Registros de AppDaemon** (Ajustes → Complementos → AppDaemon → Registro)
2. Busque: `"Anyka Talk worker initialized"`

### 3. Probar la Instalación

1. Encuentre la dirección IP de su cámara (ej., `192.168.1.100`)

2. En Home Assistant, vaya a **Herramientas de Desarrollador** → **Servicios**

3. Seleccione el servicio: `anyka_talk.start`

4. Agregue los datos del servicio:
   ```yaml
   camera_ip: "192.168.1.100"
   ```

5. Haga clic en **Llamar Servicio**

6. Verifique los registros de AppDaemon para:
   - `"Starting audio stream to 192.168.1.100"`
   - `"ffmpeg process started with PID..."`

7. Para detener la transmisión:
   - Seleccione el servicio: `anyka_talk.stop`
   - Haga clic en **Llamar Servicio**

## Solución de Problemas

### La Integración No Carga

**Síntoma**: Los servicios `anyka_talk.start` y `anyka_talk.stop` no aparecen

**Soluciones**:
1. Revise los registros de Home Assistant: **Ajustes** → **Sistema** → **Registros**
2. Busque errores que mencionen `anyka_talk`
3. Verifique los permisos de los archivos (deben ser legibles por Home Assistant)
4. Asegúrese de que los tres archivos estén en la ubicación correcta
5. Intente un reinicio completo en lugar de una recarga rápida

### AppDaemon No Inicia

**Síntoma**: Los registros de AppDaemon muestran errores sobre `anyka_talk`

**Soluciones**:
1. Verifique la sintaxis de Python: `python3 -m py_compile anyka_talk.py`
2. Verifique la sintaxis de `apps.yaml`
3. Asegúrese de que AppDaemon pueda importar los módulos requeridos
4. Verifique la versión de AppDaemon (se recomienda 4.0.0 o más reciente)

### FFmpeg No Encontrado

**Síntoma**: Los registros de AppDaemon muestran `"Failed to start ffmpeg"` o `"ffmpeg: command not found"`

**Soluciones**:

Para Home Assistant OS:
```bash
# SSH a su sistema
apk add ffmpeg
```

Para Docker:
```dockerfile
# Agregue a su Dockerfile o use un contenedor con ffmpeg preinstalado
RUN apt-get update && apt-get install -y ffmpeg
```

Para Home Assistant Core:
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# CentOS/RHEL
sudo yum install ffmpeg
```

### No Hay Dispositivo de Audio

**Síntoma**: Errores de FFmpeg sobre ALSA o entrada de audio

**Soluciones**:
1. Verifique los dispositivos disponibles: `arecord -L`
2. Pruebe el micrófono: `arecord -d 5 test.wav && aplay test.wav`
3. Asegúrese de que Home Assistant tenga permiso para acceder a dispositivos de audio
4. Para Docker, asegúrese de que los dispositivos de audio estén mapeados:
   ```yaml
   devices:
     - /dev/snd:/dev/snd
   ```

### No Se Puede Conectar a la Cámara

**Síntoma**: La transmisión inicia pero no hay audio en la cámara

**Soluciones**:
1. Verifique que la dirección IP de la cámara sea correcta
2. Asegúrese de que el puerto 10000 de la cámara esté abierto (pruebe: `nc -zv IP_CAMARA 10000`)
3. Verifique las reglas del firewall
4. Verifique que la cámara soporte el formato de audio PCM A-law
5. Intente probar con netcat:
   ```bash
   ffmpeg -f alsa -i default -ar 8000 -ac 1 -acodec pcm_alaw -f alaw tcp://IP_CAMARA:10000
   ```

### Conexión Rechazada a AppDaemon

**Síntoma**: Los registros de Home Assistant muestran "Connection refused" al puerto 5050

**Soluciones**:
1. Verifique que la API HTTP de AppDaemon esté habilitada
2. Verifique que AppDaemon esté funcionando
3. Verifique que el puerto 5050 no esté bloqueado por el firewall
4. Pruebe la conexión: `curl http://localhost:5050/status`
5. Verifique si AppDaemon está escuchando: `netstat -tlnp | grep 5050`

## Configuración Avanzada

### Uso en Automatizaciones

Cree una automatización para iniciar el audio cuando se presiona un botón:

```yaml
automation:
  - alias: "Iniciar Audio Anyka al Presionar Botón"
    trigger:
      - platform: state
        entity_id: input_boolean.camera_talk
        to: "on"
    action:
      - service: anyka_talk.start
        data:
          camera_ip: "192.168.1.100"

  - alias: "Detener Audio Anyka al Soltar Botón"
    trigger:
      - platform: state
        entity_id: input_boolean.camera_talk
        to: "off"
    action:
      - service: anyka_talk.stop
```

### Integración en el Panel de Control

Agregue un botón a su panel de control:

```yaml
type: button
name: Hablar a la Cámara
tap_action:
  action: call-service
  service: anyka_talk.start
  data:
    camera_ip: "192.168.1.100"
hold_action:
  action: call-service
  service: anyka_talk.stop
icon: mdi:microphone
```

### Múltiples Cámaras

Para soportar múltiples cámaras, llame al servicio con diferentes IPs:

```yaml
# Cámara 1
service: anyka_talk.start
data:
  camera_ip: "192.168.1.100"

# Cámara 2
service: anyka_talk.start
data:
  camera_ip: "192.168.1.101"
```

**Nota**: Solo una transmisión puede estar activa a la vez con la implementación actual.

## Desinstalación

### Remover la Integración de Home Assistant

1. Elimine el directorio:
   ```bash
   rm -rf /config/custom_components/anyka_talk
   ```

2. Reinicie Home Assistant

### Remover la Aplicación AppDaemon

1. Elimine los archivos:
   ```bash
   rm /config/appdaemon/apps/anyka_talk.py
   ```

2. Elimine de `apps.yaml`:
   ```yaml
   # Elimine o comente:
   # anyka_talk:
   #   module: anyka_talk
   #   class: AnykaTalk
   ```

3. Reinicie AppDaemon

## Soporte

Para problemas, preguntas o contribuciones:
- Issues de GitHub: https://github.com/dani811/anyka/issues
- Discusiones: https://github.com/dani811/anyka/discussions

## Resumen de Requisitos del Sistema

| Componente | Requisito |
|-----------|-----------|
| Home Assistant | 2021.12+ |
| AppDaemon | 4.0.0+ |
| Python | 3.8+ |
| FFmpeg | Cualquier versión reciente |
| Dispositivo de Audio | Entrada compatible con ALSA |
| Red | Acceso de red local a la cámara |
| Puerto de Cámara | Puerto TCP 10000 (predeterminado) |

## Próximos Pasos

Después de una instalación exitosa:
1. Pruebe la funcionalidad básica
2. Cree automatizaciones para casos de uso comunes
3. Agregue controles de panel de control para fácil acceso
4. Considere crear escenas que incluyan notificaciones de audio
5. Consulte el README.md principal para ejemplos de uso

## Versión en Inglés

Para la versión en inglés de esta guía, consulte [INSTALL.md](INSTALL.md).
