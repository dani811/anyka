# Anyka Bidirectional Audio - Home Assistant Addon

This addon enables **bidirectional audio** with Anyka-based IP cameras:

- **🎤 Uplink (Talk)**: Send audio from microphone to camera via TCP
- **🔊 Downlink (Listen)**: Receive audio from camera via RTSP to speaker

## Features

- ✅ **Bidirectional audio** - Talk AND listen simultaneously
- ✅ **HAOS native** - Runs as a Home Assistant addon
- ✅ **Ingress UI** - Open the mic web interface directly from the addon panel
- ✅ **No external dependencies** - Self-contained with ffmpeg
- ✅ **Simple API** - Easy integration with automations
- ✅ **Real-time** - Low latency audio streaming

## Installation

### 1. Add Repository

Add this repository to your Home Assistant:

1. Go to **Supervisor** → **Add-on Store** → **⋮** (three dots) → **Repositories**
2. Add: `https://github.com/dani811/anyka`
3. Refresh the page

### 2. Install Addon

1. Find "Anyka Bidirectional Audio" in the add-on store
2. Click **INSTALL**
3. Wait for installation to complete

### 3. Configure

Configure the addon in the **Configuration** tab:

```yaml
cameras:
  - id: "front"
    ip: "192.168.1.100"
    talk_port: 10000
    talk_mode: ptt
log_level: info
```

- `cameras`: Camera list (use 1 item for single camera, multiple items for multi-camera) (`id`, `ip`, `talk_port`, `talk_mode`)
- `log_level`: Logging level (trace, debug, info, warning, error)

If `talk_mode` is omitted in a camera, it defaults to `ptt`.

`camera_ip`, `rtsp_url` and `audio_port` remain available per API/service call when needed, but are no longer required as addon-level options.

### 4. Start Addon

1. Go to the **Info** tab
2. Enable **Start on boot** (optional)
3. Click **START**
4. Click **OPEN WEB UI** (Ingress) to use the embedded talk interface

### 5. Install Integration

The custom integration is automatically included. Add to your `configuration.yaml`:

```yaml
anyka_audio:
  host: localhost  # or addon_<slug> for Supervisor
  port: 8099
```

Then restart Home Assistant.

## Usage

### Talk (Uplink)

Send audio from your microphone to the camera:

```yaml
service: anyka_audio.start_talk
data:
  camera_ip: "192.168.1.100"
  audio_port: 10000  # optional
```

Or upload audio bytes (recommended for stable uplink without URL/TTS dependencies):

```yaml
service: anyka_talk.upload_talk
data:
  camera_ip: "192.168.1.100"
  audio_file: "/config/www/talk.wav"
  input_format: "wav"
```

To stop:

```yaml
service: anyka_audio.stop_talk
```

### Listen (Downlink)

Receive audio from the camera to your speaker:

```yaml
service: anyka_audio.start_listen
data:
  rtsp_url: "rtsp://192.168.1.100:554/audio"
```

To stop:

```yaml
service: anyka_audio.stop_listen
```

### Bidirectional (Both)

Talk and listen at the same time:

```yaml
# Start talk
service: anyka_audio.start_talk
data:
  camera_ip: "192.168.1.100"

# Start listen (in same automation)
service: anyka_audio.start_listen
data:
  rtsp_url: "rtsp://192.168.1.100:554/audio"
```

## Automations

### Push-to-Talk Button

```yaml
automation:
  - alias: "Camera Talk Button"
    trigger:
      - platform: state
        entity_id: input_boolean.camera_talk
        to: "on"
    action:
      - service: anyka_audio.start_talk
        data:
          camera_ip: "192.168.1.100"
      - service: anyka_audio.start_listen
        data:
          rtsp_url: "rtsp://192.168.1.100:554/audio"

  - alias: "Camera Talk Button Release"
    trigger:
      - platform: state
        entity_id: input_boolean.camera_talk
        to: "off"
    action:
      - service: anyka_audio.stop_talk
      - service: anyka_audio.stop_listen
```

### Dashboard Card

```yaml
type: button
name: Talk to Camera
tap_action:
  action: call-service
  service: anyka_audio.start_talk
  data:
    camera_ip: "192.168.1.100"
hold_action:
  action: call-service
  service: anyka_audio.stop_talk
icon: mdi:microphone
```

## API Endpoints

The addon exposes a REST API on port 8099:

- `POST /api/uplink/start` - Start talk (mic → camera)
- `POST /api/uplink/chunk` - Send real-time browser chunk to running talk stream
- `POST /api/uplink/upload` - Upload audio bytes and stream to camera
- `POST /api/uplink/stop` - Stop talk
- `GET /api/uplink/webview` - Embeddable mic webview for dashboard cards
- `POST /api/downlink/start` - Start listen (camera → speaker)
- `POST /api/downlink/stop` - Stop listen
- `GET /api/status` - Get stream status
- `GET /health` - Health check

For multi-camera setups, select target camera with query param `?cam=<id>` (for example `/?cam=front` in web UI or `/api/uplink/start?cam=front`).

### Embedded dashboard card (no navigation out of card)

Use an iframe/webpage card pointing to:

`/api/uplink/webview?cam=front&parent_origin=http://homeassistant.local:8123`

This keeps microphone controls inside the card. The embedded page also accepts `postMessage` commands:

```js
const addonOrigin = "http://homeassistant.local:8099"; // iframe src origin
iframe.contentWindow.postMessage({ type: "anyka_talk", action: "start", cam: "front" }, addonOrigin);
iframe.contentWindow.postMessage({ type: "anyka_talk", action: "stop" }, addonOrigin);
iframe.contentWindow.postMessage({ type: "anyka_talk", action: "toggle" }, addonOrigin);
```

## Troubleshooting

### No Audio Output

1. Check Home Assistant audio output settings
2. Verify RTSP URL is correct
3. Check addon logs for errors

### No Audio Input

1. Browser/mobile microphone is required for talk (no ALSA dependency inside HAOS container)
2. Verify camera IP and port
3. Check firewall allows TCP to camera port 10000

### RTSP Connection Failed

1. Verify RTSP URL format: `rtsp://IP:PORT/path`
2. Test RTSP stream: `ffplay rtsp://192.168.1.100:554/audio`
3. Check camera supports RTSP audio

### View Logs

Go to **Addon** → **Log** tab to view detailed logs.

## Technical Details

### Audio Formats

- **Uplink**: PCM A-law, 8000 Hz, mono, TCP
- **Downlink**: Auto-detected from RTSP stream

### Requirements

- Home Assistant OS
- Anyka-based IP camera
- Camera must support:
  - TCP audio input on port 10000 (for talk)
  - RTSP audio output (for listen)

## Support

- GitHub Issues: https://github.com/dani811/anyka/issues
- Discussions: https://github.com/dani811/anyka/discussions

## Version History

### 2.0.2
- Multi-camera config no longer requires root `audio_port`

### 2.0.1
- Enabled Ingress panel UI metadata
- Embedded webview and command-driven browser talk improvements

### 2.0.0
- Complete refactor to HAOS addon
- Added bidirectional audio support
- Added RTSP downlink (listen)
- Removed AppDaemon dependency
- Integrated custom component

### 1.0.0
- Initial release (uplink only)

## Maintainer: How Home Assistant detects a new version

To make Home Assistant show an update, publish a **new version number**:

1. Bump addon version in `anyka_audio/config.yaml` (`version` field).
2. If integration code changed, bump `version` in `anyka_audio/rootfs/app/custom_components/anyka_audio/manifest.json`.
3. Push the change to the repository branch used by your Add-on repository.
4. In Home Assistant, refresh Add-on Store / check updates.

Without version bump, Home Assistant treats it as the same release and won't show update availability.
