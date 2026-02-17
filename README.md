# anyka

**Home Assistant addon for bidirectional audio with Anyka IP cameras**

**🎯 NOW OPERATIONAL: Talk AND Listen to your Anyka cameras!**

## Features

- 🎤 **Uplink (Talk)**: Stream audio from microphone to camera via TCP
- 🔊 **Downlink (Listen)**: Receive audio from camera via RTSP to speaker
- 🔄 **Bidirectional**: Use both simultaneously for true two-way communication
- 🏠 **HAOS Native**: Runs as a Home Assistant addon (no AppDaemon needed)
- 🚀 **Simple API**: Easy integration with automations and dashboards
- 🔧 **Self-contained**: Includes ffmpeg and all dependencies

## Quick Start

### Prerequisites

- Home Assistant OS (Supervisor)
- Anyka-based IP camera with:
  - TCP audio input (port 10000)
  - RTSP audio output

### Installation (HAOS Addon)

1. **Add this repository** to Home Assistant:
   - Go to **Supervisor** → **Add-on Store** → **⋮** → **Repositories**
   - Add: `https://github.com/dani811/anyka`

2. **Install the addon**:
   - Find "Anyka Bidirectional Audio"
   - Click **INSTALL**

3. **Configure** (optional):
   ```yaml
   camera_ip: "192.168.1.100"
   rtsp_url: "rtsp://192.168.1.100:554/audio"
   ```

4. **Start** the addon

5. **Install integration from HACS**:
   - Add this repo as a custom repository in HACS (category: Integration)
   - Install **Anyka Talk**
   - Restart Home Assistant

6. **Add integration** to `configuration.yaml`:
   ```yaml
   anyka_talk:
     host: localhost
     port: 8099
   ```

7. **Restart** Home Assistant

**📖 Detailed: [anyka_audio/README.md](anyka_audio/README.md)**

### Basic Usage

**Talk to camera** (uplink):

```yaml
service: anyka_talk.start_talk
data:
  camera_ip: "192.168.1.100"
```

**Talk to camera by UPLOAD** (uplink bytes, no URL/TTS dependency):

```yaml
service: anyka_talk.upload_talk
data:
  camera_ip: "192.168.1.100"
  audio_file: "/config/www/talk.wav"
  input_format: "wav"
```

**Listen from camera** (downlink):

```yaml
service: anyka_talk.start_listen
data:
  rtsp_url: "rtsp://192.168.1.100:554/audio"
```

**Stop**:

```yaml
service: anyka_talk.stop_talk
service: anyka_talk.stop_listen
```

## How It Works

### Architecture

```
┌─────────────────┐                  ┌────────────────────┐                  ┌─────────┐
│ Home Assistant  │   HTTP API       │  HAOS Addon        │   Bidirectional  │  Camera │
│   Integration   │ ───────────────> │  (anyka_audio)     │ <──────────────> │ (Anyka) │
│                 │   (port 8099)    │                    │                  │         │
└─────────────────┘                  └────────────────────┘                  └─────────┘
        │                                       │                                  │
        │ Actions/Services:                     │ Uplink (Talk):                   │
        │ - start_talk                          │ • FFmpeg: Mic → PCM A-law       │
        │ - stop_talk                           │ • TCP → Camera:10000 ────────> │
        │ - upload_talk (UPLOAD)                │                                  │
        │ - start_listen                        │                                  │
        │ - stop_listen                         │ Downlink (Listen):               │
        │                                       │ • RTSP ← Camera:554  <────────── │
        │                                       │ • FFmpeg: RTSP → Speaker         │
        └───────────────────────────────────────┘                                  
```

### Components

1. **HAOS Addon** (`anyka_audio/`)
   - Self-contained Docker container
   - Includes ffmpeg and Python server
   - Manages bidirectional audio streams
   - Exposes REST API on port 8099

2. **Home Assistant Integration** (`custom_components/anyka_talk`)
   - Registers services (shown as **Actions** in HA 2026 UI) under `anyka_talk`: `start_talk`, `stop_talk`, `upload_talk`, `start_listen`, `stop_listen`
   - Includes Device Actions backed by those same services
   - Communicates with addon via HTTP API
   - Enables automation and dashboard integration

3. **Anyka SD Overlay Package** (`camera_sd_overlay/`)
   - Startup hook for camera firmware
   - Keeps talk TCP port 10000 enabled persistently

## Documentation

- **[anyka_audio/README.md](anyka_audio/README.md)** - Complete addon documentation
- **[INSTALL.md](INSTALL.md)** - Legacy installation guide (v1.0, deprecated)
- **[INSTALL_ES.md](INSTALL_ES.md)** - Guía de instalación (v1.0, obsoleta)
- **Legacy files** - See `custom_components/` and `appdaemon/` for v1.0 code

## Examples

### Bidirectional Communication

Talk AND listen simultaneously:

```yaml
automation:
  - alias: "Two-Way Intercom"
    trigger:
      platform: state
      entity_id: input_boolean.intercom
      to: "on"
    action:
      # Start talk
      - service: anyka_talk.start_talk
        data:
          camera_ip: "192.168.1.100"
      # Start listen
      - service: anyka_talk.start_listen
        data:
          rtsp_url: "rtsp://192.168.1.100:554/audio"

  - alias: "Stop Intercom"
    trigger:
      platform: state
      entity_id: input_boolean.intercom
      to: "off"
    action:
      - service: anyka_talk.stop_talk
      - service: anyka_talk.stop_listen
```

## Requirements

| Component | Version | Notes |
|-----------|---------|-------|
| Home Assistant | 2026.1+ | OS/Supervised required for addon |
| Anyka Camera | Any | Must support TCP audio + RTSP |
| FFmpeg | Included | Built into addon |

## Troubleshooting

Common issues and solutions:

- **Services not appearing**: Check addon is running, restart HA
- **No audio output**: Verify RTSP URL, check addon logs
- **No audio input**: Verify camera IP and port 10000
- **Connection failed**: Check network connectivity to camera

For detailed troubleshooting, see [anyka_audio/README.md](anyka_audio/README.md#troubleshooting).

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is open source and available for use in accordance with the repository license.

## Credits

Created for the Home Assistant community to enable two-way audio communication with Anyka-based IP cameras.

## Support

- 🐛 Report bugs: [GitHub Issues](https://github.com/dani811/anyka/issues)
- 💬 Ask questions: [GitHub Discussions](https://github.com/dani811/anyka/discussions)
- 📖 Documentation: [INSTALL.md](INSTALL.md)
