# anyka

Minimal Home Assistant + AppDaemon project for Anyka two-way audio.

## Architecture

### Home Assistant Custom Integration
- **Domain**: `anyka_talk`
- **Services**:
  - `anyka_talk.start` - Start audio streaming to camera
  - `anyka_talk.stop` - Stop audio streaming

### AppDaemon Worker
- **HTTP API**:
  - `POST /start` - Start ffmpeg audio stream
  - `POST /stop` - Stop ffmpeg audio stream
  - `GET /status` - Get stream status

### Worker Behaviour
Launches ffmpeg to:
1. Capture audio from microphone
2. Encode as PCM A-law, 8000Hz, mono
3. Send raw stream via TCP to camera IP on port 10000

## Installation

### Home Assistant Integration
1. Copy `custom_components/anyka_talk/` to your Home Assistant `custom_components/` directory
2. Restart Home Assistant
3. The `anyka_talk` integration will be available

### AppDaemon App
1. Copy `appdaemon/apps/anyka_talk.py` and `appdaemon/apps/apps.yaml` to your AppDaemon `apps/` directory
2. Restart AppDaemon
3. The HTTP API will be available at `http://localhost:5050`

## Usage

Call the service from Home Assistant:

```yaml
service: anyka_talk.start
data:
  camera_ip: "192.168.1.100"
```

To stop:

```yaml
service: anyka_talk.stop
```

## Requirements

- Home Assistant with AppDaemon
- ffmpeg installed on the system
- ALSA audio input device (Linux)