# Installation Guide - Anyka Two-Way Audio

This guide provides detailed step-by-step instructions for installing the Anyka Two-Way Audio integration in Home Assistant.

**🇪🇸 Para la versión en español, consulte [INSTALL_ES.md](INSTALL_ES.md)**

## Prerequisites

Before installing, ensure you have:

1. **Home Assistant** (version 2021.12 or newer recommended)
2. **AppDaemon** installed and configured in Home Assistant
3. **ffmpeg** installed on your system
4. **Audio input device** (microphone) configured on your Home Assistant host
5. **Anyka camera** accessible on your local network

## Installation Methods

### Method 1: Manual Installation (Recommended)

#### Step 1: Install the Home Assistant Custom Integration

1. **Access your Home Assistant configuration directory**
   - If using Home Assistant OS: `/config/`
   - If using Docker: Your mapped config volume
   - If using Core installation: Usually `~/.homeassistant/` or `/home/homeassistant/.homeassistant/`

2. **Create the custom_components directory** (if it doesn't exist):
   ```bash
   cd /config
   mkdir -p custom_components
   ```

3. **Copy the integration files**:
   ```bash
   cd custom_components
   mkdir -p anyka_talk
   ```
   
   Copy these files to `custom_components/anyka_talk/`:
   - `__init__.py`
   - `manifest.json`
   - `services.yaml`

4. **Verify the structure**:
   ```
   /config/
   └── custom_components/
       └── anyka_talk/
           ├── __init__.py
           ├── manifest.json
           └── services.yaml
   ```

5. **Restart Home Assistant**
   - Go to **Settings** → **System** → **Restart**
   - Or use the service: `homeassistant.restart`

#### Step 2: Install the AppDaemon App

1. **Access your AppDaemon apps directory**
   - Default location: `/config/appdaemon/apps/`
   - Or check your AppDaemon configuration for the apps directory

2. **Copy the AppDaemon files**:
   ```bash
   cd /config/appdaemon/apps
   ```
   
   Copy these files:
   - `anyka_talk.py`
   - `apps.yaml` (merge with existing if you have one)

3. **Configure apps.yaml**:
   
   If you already have an `apps.yaml`, add this configuration:
   ```yaml
   anyka_talk:
     module: anyka_talk
     class: AnykaTalk
   ```
   
   If you don't have an `apps.yaml`, use the provided one as-is.

4. **Verify the structure**:
   ```
   /config/appdaemon/apps/
   ├── anyka_talk.py
   └── apps.yaml
   ```

5. **Restart AppDaemon**
   - Go to **Settings** → **Add-ons** → **AppDaemon** → **Restart**
   - Or restart the AppDaemon container/process

6. **Verify AppDaemon is running**:
   - Check AppDaemon logs for: `"Initializing Anyka Talk worker"`
   - Check that HTTP API is available at `http://localhost:5050`

### Method 2: Using HACS (Future)

*HACS installation will be available once the repository is added to HACS.*

## Configuration

### AppDaemon HTTP API Port

By default, the integration expects AppDaemon's HTTP API on port 5050. If your AppDaemon uses a different port:

1. Check your AppDaemon configuration (`appdaemon.yaml`):
   ```yaml
   appdaemon:
     plugins:
       HASS:
         type: hass
   http:
     url: http://127.0.0.1:5050
   ```

2. If using a different port, you'll need to modify the `APPDAEMON_URL` in `custom_components/anyka_talk/__init__.py`.

### Audio Device Configuration

The default configuration uses ALSA's `default` audio input device. To use a different device:

1. List available audio devices:
   ```bash
   arecord -L
   ```

2. Modify the audio input in `appdaemon/apps/anyka_talk.py` (line 84):
   ```python
   "-i", "hw:0,0",  # Change from "default" to your device
   ```

### Camera Port Configuration

The default camera port is 10000 (TCP). If your Anyka camera uses a different port, modify line 89 in `appdaemon/apps/anyka_talk.py`:
```python
f"tcp://{camera_ip}:YOUR_PORT_HERE"
```

## Verification

### 1. Check Integration Load

1. Go to **Developer Tools** → **Services**
2. Look for these services:
   - `anyka_talk.start`
   - `anyka_talk.stop`

If you see these services, the integration is loaded successfully!

### 2. Check AppDaemon Worker

1. Go to **AppDaemon logs** (Settings → Add-ons → AppDaemon → Log)
2. Look for: `"Anyka Talk worker initialized"`

### 3. Test the Installation

1. Find your camera's IP address (e.g., `192.168.1.100`)

2. In Home Assistant, go to **Developer Tools** → **Services**

3. Select service: `anyka_talk.start`

4. Add service data:
   ```yaml
   camera_ip: "192.168.1.100"
   ```

5. Click **Call Service**

6. Check AppDaemon logs for:
   - `"Starting audio stream to 192.168.1.100"`
   - `"ffmpeg process started with PID..."`

7. To stop the stream:
   - Select service: `anyka_talk.stop`
   - Click **Call Service**

## Troubleshooting

### Integration Not Loading

**Symptom**: Services `anyka_talk.start` and `anyka_talk.stop` don't appear

**Solutions**:
1. Check Home Assistant logs: **Settings** → **System** → **Logs**
2. Look for errors mentioning `anyka_talk`
3. Verify file permissions (files should be readable by Home Assistant)
4. Ensure all three files are in the correct location
5. Try a full restart instead of a quick reload

### AppDaemon Not Starting

**Symptom**: AppDaemon logs show errors about `anyka_talk`

**Solutions**:
1. Check Python syntax: `python3 -m py_compile anyka_talk.py`
2. Verify `apps.yaml` syntax
3. Ensure AppDaemon can import required modules
4. Check AppDaemon version (4.0.0 or newer recommended)

### FFmpeg Not Found

**Symptom**: AppDaemon logs show `"Failed to start ffmpeg"` or `"ffmpeg: command not found"`

**Solutions**:

For Home Assistant OS:
```bash
# SSH into your system
apk add ffmpeg
```

For Docker:
```dockerfile
# Add to your Dockerfile or use a container with ffmpeg pre-installed
RUN apt-get update && apt-get install -y ffmpeg
```

For Home Assistant Core:
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# CentOS/RHEL
sudo yum install ffmpeg
```

### No Audio Device

**Symptom**: FFmpeg errors about ALSA or audio input

**Solutions**:
1. Check available devices: `arecord -L`
2. Test microphone: `arecord -d 5 test.wav && aplay test.wav`
3. Ensure Home Assistant has permission to access audio devices
4. For Docker, ensure audio devices are mapped:
   ```yaml
   devices:
     - /dev/snd:/dev/snd
   ```

### Cannot Connect to Camera

**Symptom**: Stream starts but no audio on camera

**Solutions**:
1. Verify camera IP address is correct
2. Ensure camera port 10000 is open (try: `nc -zv CAMERA_IP 10000`)
3. Check firewall rules
4. Verify camera supports PCM A-law audio format
5. Try testing with netcat:
   ```bash
   ffmpeg -f alsa -i default -ar 8000 -ac 1 -acodec pcm_alaw -f alaw tcp://CAMERA_IP:10000
   ```

### Connection Refused to AppDaemon

**Symptom**: Home Assistant logs show "Connection refused" to port 5050

**Solutions**:
1. Verify AppDaemon HTTP API is enabled
2. Check AppDaemon is running
3. Verify port 5050 is not blocked by firewall
4. Test connection: `curl http://localhost:5050/status`
5. Check if AppDaemon is listening: `netstat -tlnp | grep 5050`

## Advanced Configuration

### Using in Automations

Create an automation to start audio when a button is pressed:

```yaml
automation:
  - alias: "Start Anyka Audio on Button Press"
    trigger:
      - platform: state
        entity_id: input_boolean.camera_talk
        to: "on"
    action:
      - service: anyka_talk.start
        data:
          camera_ip: "192.168.1.100"

  - alias: "Stop Anyka Audio on Button Release"
    trigger:
      - platform: state
        entity_id: input_boolean.camera_talk
        to: "off"
    action:
      - service: anyka_talk.stop
```

### Dashboard Integration

Add a button to your dashboard:

```yaml
type: button
name: Talk to Camera
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

### Multiple Cameras

To support multiple cameras, call the service with different IPs:

```yaml
# Camera 1
service: anyka_talk.start
data:
  camera_ip: "192.168.1.100"

# Camera 2
service: anyka_talk.start
data:
  camera_ip: "192.168.1.101"
```

**Note**: Only one stream can be active at a time with the current implementation.

## Uninstallation

### Remove Home Assistant Integration

1. Delete the directory:
   ```bash
   rm -rf /config/custom_components/anyka_talk
   ```

2. Restart Home Assistant

### Remove AppDaemon App

1. Delete the files:
   ```bash
   rm /config/appdaemon/apps/anyka_talk.py
   ```

2. Remove from `apps.yaml`:
   ```yaml
   # Remove or comment out:
   # anyka_talk:
   #   module: anyka_talk
   #   class: AnykaTalk
   ```

3. Restart AppDaemon

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/dani811/anyka/issues
- Discussions: https://github.com/dani811/anyka/discussions

## System Requirements Summary

| Component | Requirement |
|-----------|-------------|
| Home Assistant | 2021.12+ |
| AppDaemon | 4.0.0+ |
| Python | 3.8+ |
| FFmpeg | Any recent version |
| Audio Device | ALSA-compatible input |
| Network | Local network access to camera |
| Camera Port | TCP port 10000 (default) |

## Next Steps

After successful installation:
1. Test the basic functionality
2. Create automations for common use cases
3. Add dashboard controls for easy access
4. Consider creating scenes that include audio notifications
5. Check the main README.md for usage examples
